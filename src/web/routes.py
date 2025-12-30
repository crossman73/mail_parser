"""
Web routes for the email evidence system
웹 라우트 정의 - EmailEvidenceProcessor 통합
"""

import os
import sys
import tempfile
import threading
import uuid
from datetime import datetime
from pathlib import Path

from flask import (flash, jsonify, redirect, render_template, request,
                   send_file, session, url_for)
from werkzeug.utils import secure_filename

from src.evidence.additional_evidence_manager import AdditionalEvidenceManager
# Heavy imports (openpyxl/numpy) moved into functions to avoid import-time cost
# from src.legal_compliance.court_evidence_verifier import \
#     CourtEvidenceIntegrityVerifier
from src.mail_parser.processor import EmailEvidenceProcessor
from src.mail_parser.progress import EmailProcessingProgress
from src.timeline.integrated_timeline_generator import \
    IntegratedTimelineGenerator
from src.utils.temp_manager import temp_manager

from .progress_tracker import progress_tracker

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


# 메모리에서 임시 데이터 저장 (실제 환경에서는 데이터베이스 사용)
uploaded_files = {}
processed_emails = {}
email_processors = {}  # 세션별 프로세서 인스턴스

# DB 통합
try:
    from src.database.email_db import db as email_db
    USE_DATABASE = True
    print("✅ 데이터베이스 연결 성공")
except ImportError as e:
    print(f"⚠️ 데이터베이스 모듈 로드 실패, 메모리 모드 사용: {e}")
    email_db = None
    USE_DATABASE = False


def register_routes(app):
    """웹 라우트 등록"""

    # 서비스 인스턴스 초기화
    from src.services.evidence_service import EvidenceService
    from src.services.timeline_service import TimelineService

    evidence_service = EvidenceService()
    timeline_service = TimelineService()

    # Avoid duplicating routes when multiple app factories or blueprints
    # attempt to register the same handlers. If an endpoint named 'index'
    # already exists, skip registering the legacy routes to prevent
    # "View function mapping is overwriting an existing endpoint function" errors.
    existing_endpoints = {r.endpoint for r in app.url_map.iter_rules()}
    if 'index' in existing_endpoints:
        app.logger.info(
            'Skipping register_routes: index endpoint already registered')
        return

    def allowed_file(filename):
        """허용된 파일 확장자 확인"""
        ALLOWED_EXTENSIONS = {'mbox', 'eml', 'msg'}
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    @app.route('/', endpoint='index')
    def index():
        """메인 페이지"""
        try:
            # 데이터 상태 확인
            processed_dir = Path('processed_emails')
            has_data = processed_dir.exists() and any(processed_dir.iterdir())

            # 기본 통계 정보 계산
            total_files = len(uploaded_files)
            processed_files = len(
                [f for f in uploaded_files.values() if f.get('processed', False)])
            total_emails = sum(len(data.get('emails', []))
                               for data in processed_emails.values())

            # 증거 개수 계산 (폴더 개수)
            evidence_count = len(
                [d for d in processed_dir.iterdir() if d.is_dir()]) if has_data else 0

            stats = {
                'total_files': total_files,
                'processed_files': processed_files,
                'total_emails': total_emails,
                'evidence_count': evidence_count,
                'has_data': has_data
            }

            # 기능 활성화 상태
            features_status = {
                'timeline_available': has_data and evidence_count > 0,
                'evidence_available': has_data and evidence_count > 0,
                'integrity_available': has_data and evidence_count > 0,
                'upload_available': True  # 항상 사용 가능
            }

            return render_template('index.html',
                                   stats=stats,
                                   features_status=features_status)
        except Exception as e:
            app.logger.error(f"메인 페이지 로드 실패: {str(e)}")
            stats = {'total_files': 0, 'processed_files': 0,
                     'total_emails': 0, 'evidence_count': 0, 'has_data': False}
            features_status = {'timeline_available': False, 'evidence_available': False,
                               'integrity_available': False, 'upload_available': True}
            return render_template('index.html',
                                   stats=stats,
                                   features_status=features_status)

    def process_file_background(task_id: str, temp_path: str, filename: str, options: dict):
        """백그라운드에서 파일 파싱 (증거 생성 제외)"""
        session_dir = None
        try:
            progress_tracker.start_processing(task_id, f"{filename} 처리", 100)

            # 0단계: 임시 세션 디렉토리 생성
            progress_tracker.update_progress(task_id, 5, "임시 작업 디렉토리 생성 중...")
            session_dir = temp_manager.create_session_directory(task_id)

            # 1단계: 파일 검증
            progress_tracker.update_progress(
                task_id, 10, "파일 검증 및 무결성 확인 중...")

            # 2단계: EmailEvidenceProcessor 초기화
            progress_tracker.update_progress(task_id, 20, "이메일 파싱 엔진 초기화 중...")
            config_path = os.path.join(os.path.dirname(
                __file__), '..', '..', 'config.json')
            processor = EmailEvidenceProcessor(config_path)

            # 3단계: mbox 파일 로드
            progress_tracker.update_progress(
                task_id, 40, "이메일 파일 로드 및 파싱 중...")
            processor.load_mbox(temp_path)

            # 4단계: 메일 메타데이터 추출
            progress_tracker.update_progress(
                task_id, 70, "이메일 메타데이터 추출 및 분석 중...")
            all_messages = processor.get_all_message_metadata()

            if not all_messages:
                progress_tracker.set_error(task_id, "처리할 메일이 없습니다.")
                return

            # 5단계: 파싱된 데이터 임시 저장
            progress_tracker.update_progress(task_id, 80, "파싱 데이터 임시 저장 중...")

            # 파싱된 이메일 데이터 저장
            parsed_data = {
                'emails': [msg.to_dict() if hasattr(msg, 'to_dict') else msg for msg in all_messages],
                'filename': filename,
                'parsed_at': str(datetime.now()),
                'total_count': len(all_messages),
                'task_id': task_id
            }
            temp_manager.save_parsed_emails(
                parsed_data, f"parsed_{task_id}.json")

            # 메타데이터 저장
            metadata = {
                'session_id': task_id,
                'filename': filename,
                'temp_path': temp_path,
                'session_dir': session_dir,
                'parsing_options': options,
                'parsed_at': str(datetime.now()),
                'total_emails': len(all_messages),
                'status': 'parsing_complete'
            }
            temp_manager.save_metadata(metadata, f"metadata_{task_id}.json")

            # 6단계: 메모리에 데이터 저장 (기존 호환성 유지)
            progress_tracker.update_progress(task_id, 90, "파싱 완료 처리 중...")

            uploaded_files[task_id] = {
                'filename': filename,
                'temp_path': temp_path,
                'session_dir': session_dir,
                'uploaded_at': str(datetime.now()),
                'processed': True,
                'total_emails': len(all_messages),
                'options': options,
                'parsing_complete': True,
                'evidence_generated': False
            }

            processed_emails[task_id] = {
                'emails': all_messages,
                'filename': filename,
                'session_dir': session_dir,
                'parsing_complete': True,
                'evidence_generated': False
            }

            email_processors[task_id] = processor

            # 데이터베이스에 파싱된 이메일 데이터 저장 (선택적 - 실패해도 계속)
            if USE_DATABASE and email_db:
                try:
                    emails_json_data = [
                        msg.to_dict() if hasattr(msg, 'to_dict') else msg
                        for msg in all_messages
                    ]
                    email_db.save_processed_emails(
                        file_id=task_id,
                        filename=filename,
                        emails_data=emails_json_data
                    )
                    app.logger.info(
                        f"✅ DB에 파싱 데이터 저장: {task_id} ({len(all_messages)}개 이메일)")
                except Exception as db_err:
                    app.logger.warning(f"⚠️ 파싱 데이터 DB 저장 실패 (무시됨): {db_err}")

            # 완료 메시지
            completion_msg = f"파싱 완료! {len(all_messages)}개의 이메일을 발견했습니다. 증거 생성할 이메일을 선택하세요."
            progress_tracker.complete_processing(task_id, completion_msg)

            # 시스템 임시 파일 삭제 (uploads에 복사되었으므로)
            temp_manager.cleanup_system_temp_file(temp_path)

        except Exception as e:
            app.logger.error(f"파싱 처리 실패: {str(e)}")
            progress_tracker.set_error(task_id, str(e))

            # 오류 시 임시 세션 정리
            if session_dir:
                temp_manager.cleanup_session(session_dir)

            # 시스템 임시 파일 정리
            temp_manager.cleanup_system_temp_file(temp_path)

    def generate_evidence_background(task_id: str, selected_email_indices: list, options: dict):
        """선택된 이메일들에 대해 백그라운드에서 증거 생성"""
        try:
            if task_id not in processed_emails or task_id not in email_processors:
                progress_tracker.set_error(task_id, "파싱 데이터를 찾을 수 없습니다.")
                return

            email_data = processed_emails[task_id]
            processor = email_processors[task_id]
            all_messages = email_data['emails']
            session_dir = email_data.get('session_dir')

            # 선택된 이메일만 추출
            selected_messages = [all_messages[i]
                                 for i in selected_email_indices if i < len(all_messages)]

            if not selected_messages:
                progress_tracker.set_error(task_id, "선택된 이메일이 없습니다.")
                return

            progress_tracker.start_processing(
                task_id + "_evidence",
                f"선택된 {len(selected_messages)}개 이메일 증거 생성",
                100
            )

            # 증거 생성 준비
            progress_tracker.update_progress(
                task_id + "_evidence", 5, "증거 생성 디렉토리 준비 중...")

            # 임시 관리자에서 현재 세션 설정
            if session_dir and temp_manager.current_session_dir is None:
                temp_manager.current_session_dir = Path(session_dir)

            # 증거 생성 시작
            progress_tracker.update_progress(
                task_id + "_evidence", 10, "증거 생성 준비 중...")
            evidence_prefix = options.get('evidence_prefix', '갑')
            generated_evidence = []

            # 증거 생성 디렉토리 준비
            evidence_dir = temp_manager.get_subdir("generated_evidence")

            total_selected = len(selected_messages)
            for i, email_data in enumerate(selected_messages):
                current_progress = 20 + (i / total_selected) * 60  # 20-80% 범위
                progress_tracker.update_progress(
                    task_id + "_evidence",
                    current_progress,
                    f"증거 생성 중... ({i+1}/{total_selected}) - {email_data.get('subject', '제목 없음')[:30]}"
                )

                # 실제 증거 번호 생성 및 처리
                evidence_number = processor.get_evidence_number(
                    evidence_prefix)

                # 이메일 상세 내용 가져오기
                full_email = processor.get_full_message_by_id(
                    email_data.get('message_id'))

                if full_email:
                    # 증거 폴더 생성 및 파일 저장 (임시 디렉토리 내에)
                    evidence_info = processor.process_email_to_evidence(
                        full_email,
                        evidence_number,
                        base_dir=evidence_dir,
                        extract_attachments=options.get(
                            'extract_attachments', True)
                    )
                    generated_evidence.append(evidence_info)

            # 첨부파일 임시 복사
            if options.get('extract_attachments', True) and generated_evidence:
                progress_tracker.update_progress(
                    task_id + "_evidence", 82, "첨부파일 정리 중...")
                attachment_files = []
                for evidence in generated_evidence:
                    if evidence.get('attachments'):
                        attachment_files.extend(evidence['attachments'])

                if attachment_files:
                    temp_manager.copy_attachments(attachment_files)

            # 타임라인 생성 (선택된 이메일만)
            timeline_data = None
            if options.get('generate_timeline', True):
                progress_tracker.update_progress(
                    task_id + "_evidence", 85, "선택된 이메일 타임라인 생성 중...")
                timeline_generator = IntegratedTimelineGenerator()
                timeline_data = timeline_generator.generate_timeline_from_emails(
                    selected_messages)

                # 타임라인 데이터 임시 저장
                if timeline_data:
                    temp_manager.save_metadata(
                        timeline_data, f"timeline_{task_id}.json")

            # 무결성 검증 (heavy module import delayed)
            integrity_report = None
            if options.get('verify_integrity', True):
                try:
                    from src.legal_compliance.court_evidence_verifier import \
                        CourtEvidenceIntegrityVerifier
                except Exception as e:
                    app.logger.error(f"무결성 검증 모듈 로드 실패: {e}")
                    verifier = None
                else:
                    progress_tracker.update_progress(
                        task_id + "_evidence", 90, "증거 무결성 검증 수행 중...")
                    verifier = CourtEvidenceIntegrityVerifier()
                    integrity_report = verifier.verify_all_evidence()

                    # 무결성 보고서 임시 저장
                    if integrity_report:
                        temp_manager.save_metadata(
                            integrity_report, f"integrity_{task_id}.json")

            # 데이터 업데이트
            progress_tracker.update_progress(
                task_id + "_evidence", 95, "결과 데이터 저장 중...")

            # 증거 생성 결과 임시 저장
            evidence_result = {
                'task_id': task_id,
                'generated_at': str(datetime.now()),
                'evidence_prefix': evidence_prefix,
                'selected_email_indices': selected_email_indices,
                'generated_evidence': generated_evidence,
                'timeline_data': timeline_data,
                'integrity_report': integrity_report,
                'options': options,
                'total_generated': len(generated_evidence),
                'total_selected': len(selected_messages)
            }
            temp_manager.save_metadata(
                evidence_result, f"evidence_result_{task_id}.json")

            # 기존 데이터 업데이트 (호환성 유지)
            uploaded_files[task_id].update({
                'generated_evidence_count': len(generated_evidence),
                'evidence_prefix': evidence_prefix,
                'evidence_generated': True,
                'selected_email_count': len(selected_messages),
                'evidence_result_saved': True
            })

            processed_emails[task_id].update({
                'generated_evidence': generated_evidence,
                'timeline_data': timeline_data,
                'integrity_report': integrity_report,
                'selected_messages': selected_messages,
                'evidence_generated': True,
                'evidence_result_path': temp_manager.get_subdir("metadata")
            })

            # 데이터베이스에 증거 생성 정보 업데이트 (선택적 - 실패해도 계속)
            if USE_DATABASE and email_db:
                try:
                    email_db.update_evidence_generated(
                        file_id=task_id,
                        evidence_data=evidence_result
                    )
                    app.logger.info(
                        f"✅ DB에 증거 생성 정보 업데이트: {task_id} ({len(generated_evidence)}개 증거)")
                except Exception as db_err:
                    app.logger.warning(
                        f"⚠️ 증거 생성 정보 DB 업데이트 실패 (무시됨): {db_err}")

            # 완료 메시지
            completion_msg = (
                f"증거 생성 완료! "
                f"선택된 {len(selected_messages)}개 이메일에 대해 "
                f"{len(generated_evidence)}개 증거 생성"
            )

            if timeline_data:
                completion_msg += f", 타임라인 생성됨"
            if integrity_report:
                completion_msg += f", 무결성 검증 완료"

            completion_msg += f" (세션 디렉토리: {temp_manager.get_session_dir()})"

            progress_tracker.complete_processing(
                task_id + "_evidence", completion_msg)

            # 세션 최종 정리: 증거 파일은 보관, 임시 파일만 삭제
            temp_manager.finalize_session(task_id, keep_evidence_files=True)
            app.logger.info(f"✅ 세션 정리 완료: {task_id}")

        except Exception as e:
            app.logger.error(f"증거 생성 실패: {str(e)}")
            progress_tracker.set_error(task_id + "_evidence", str(e))

    @app.route('/upload', methods=['GET', 'POST'])
    def upload_file():
        """파일 업로드 및 처리"""
        if request.method == 'GET':
            return render_template('upload.html')

        try:
            if 'mbox_file' not in request.files:
                flash('파일이 선택되지 않았습니다.', 'error')
                return redirect(request.url)

            file = request.files['mbox_file']
            if file.filename == '':
                flash('파일이 선택되지 않았습니다.', 'error')
                return redirect(request.url)

            if file and allowed_file(file.filename):
                # 안전한 파일명 생성
                filename = secure_filename(file.filename)
                task_id = str(uuid.uuid4())

                # 임시 파일로 저장
                temp_dir = tempfile.gettempdir()
                temp_path = os.path.join(temp_dir, f"{task_id}_{filename}")
                file.save(temp_path)

                # uploads 디렉토리에도 복사 (영구 보관용)
                uploads_dir = Path('uploads')
                uploads_dir.mkdir(exist_ok=True)
                permanent_path = uploads_dir / f"{task_id}_{filename}"
                import shutil
                shutil.copy2(temp_path, permanent_path)

                # 파일 크기 확인
                file_size = permanent_path.stat().st_size

                # 데이터베이스에 업로드 파일 정보 저장 (선택적 - 실패해도 계속)
                if USE_DATABASE and email_db:
                    try:
                        email_db.save_uploaded_file(
                            file_id=task_id,
                            filename=f"{task_id}_{filename}",
                            original_filename=file.filename,
                            file_size=file_size,
                            file_path=str(permanent_path)
                        )
                        app.logger.info(f"✅ DB에 업로드 파일 정보 저장: {task_id}")
                    except Exception as db_err:
                        app.logger.warning(f"⚠️ DB 저장 실패 (무시됨): {db_err}")

                # 업로드 옵션 수집
                options = {
                    'evidence_prefix': request.form.get('evidence_prefix', '갑'),
                    'generate_timeline': request.form.get('generate_timeline') == 'true',
                    'extract_attachments': request.form.get('extract_attachments') == 'true',
                    'verify_integrity': request.form.get('verify_integrity') == 'true',
                    'commit_to_github': request.form.get('commit_to_github', 'false') == 'true'
                }

                # 백그라운드에서 처리 시작
                thread = threading.Thread(
                    target=process_file_background,
                    args=(task_id, temp_path, filename, options)
                )
                thread.daemon = True
                thread.start()

                # 처리 진행 상황 페이지로 리다이렉트
                return redirect(url_for('processing_status', task_id=task_id))

            else:
                flash('허용되지 않는 파일 형식입니다. .mbox, .eml, .msg 파일만 업로드할 수 있습니다.', 'error')
                return redirect(request.url)

        except Exception as e:
            app.logger.error(f"업로드 처리 실패: {str(e)}")
            flash('파일 업로드 중 오류가 발생했습니다.', 'error')
            return redirect(request.url)

    @app.route('/processing/<task_id>')
    def processing_status(task_id):
        """처리 진행 상황 페이지"""
        progress_data = progress_tracker.get_progress(task_id)
        if not progress_data:
            flash('처리 작업을 찾을 수 없습니다.', 'error')
            return redirect(url_for('index'))

        return render_template('processing.html', task_id=task_id, progress=progress_data)

    @app.route('/api/progress/<task_id>')
    def get_progress(task_id):
        """진행 상황 API"""
        progress_data = progress_tracker.get_progress(task_id)
        if not progress_data:
            return jsonify({'error': 'Task not found'}), 404

        return jsonify(progress_data)

    @app.route('/api/admin/tasks')
    def get_all_tasks():
        """모든 진행 중인 작업 확인 (관리용)"""
        all_tasks = progress_tracker.get_all_progress()
        return jsonify({
            'total_tasks': len(all_tasks),
            'tasks': all_tasks,
            'active_tasks': [task for task in all_tasks.values() if task.get('status') == 'processing']
        })

    @app.route('/api/admin/cleanup', methods=['POST'])
    def cleanup_tasks():
        """비정상 종료된 작업들 정리"""
        # 멈춘 작업들을 오류 상태로 변경
        progress_tracker.reset_stuck_tasks(max_stuck_minutes=5)

        # 오류 상태의 작업들 정리
        progress_tracker.cleanup_error_tasks()

        # 메모리에 저장된 업로드 파일 정보도 정리
        global uploaded_files, processed_emails, email_processors

        # 완료되지 않은 업로드 파일들 정리
        to_remove = []
        for task_id, file_info in uploaded_files.items():
            if not file_info.get('processed', False) or file_info.get('status') == 'error':
                to_remove.append(task_id)

        for task_id in to_remove:
            uploaded_files.pop(task_id, None)
            processed_emails.pop(task_id, None)
            email_processors.pop(task_id, None)

        return jsonify({
            'success': True,
            'message': f'정리 완료: {len(to_remove)}개 비정상 작업 제거됨'
        })

    @app.route('/api/admin/task/<task_id>', methods=['DELETE'])
    def delete_task(task_id):
        """특정 작업 삭제"""
        try:
            # progress_tracker에서 작업 제거
            all_tasks = progress_tracker.get_all_progress()
            if task_id in all_tasks:
                progress_tracker.tasks.pop(task_id, None)

                # 관련 파일 정보도 제거
                global uploaded_files, processed_emails, email_processors
                uploaded_files.pop(task_id, None)
                processed_emails.pop(task_id, None)
                email_processors.pop(task_id, None)

                return jsonify({
                    'status': 'success',
                    'message': f'작업 {task_id[:8]}... 삭제 완료'
                })
            else:
                return jsonify({
                    'status': 'error',
                    'error': '작업을 찾을 수 없습니다'
                }), 404
        except Exception as e:
            return jsonify({
                'status': 'error',
                'error': str(e)
            }), 500

    @app.route('/api/admin/system-info')
    def get_system_info():
        """시스템 정보 조회 (관리 페이지용)"""
        try:
            from pathlib import Path

            import psutil

            # 메모리 사용량
            memory = psutil.virtual_memory()
            memory_usage = f"{memory.percent}% ({memory.used / 1024 / 1024 / 1024:.1f}GB / {memory.total / 1024 / 1024 / 1024:.1f}GB)"

            # 업로드된 파일 수
            upload_folder = Path('uploads')
            uploaded_count = len(list(upload_folder.glob('*'))
                                 ) if upload_folder.exists() else 0

            # 처리된 이메일 수
            processed_folder = Path('processed_emails')
            processed_count = len(list(processed_folder.glob(
                '*'))) if processed_folder.exists() else 0

            # 임시 저장소 통계
            storage_stats = temp_manager.get_storage_stats()

            return jsonify({
                'memory_usage': memory_usage,
                'uploaded_files': uploaded_count,
                'processed_emails': processed_count,
                'server_status': 'running',
                'temp_storage': {
                    'total_size_mb': round(storage_stats['total_size_mb'], 2),
                    'total_sessions': storage_stats['total_sessions'],
                    'sessions_with_evidence': storage_stats['sessions_with_evidence'],
                    'old_sessions': storage_stats['old_sessions_count'],
                    'very_old_sessions': storage_stats['very_old_sessions_count']
                }
            })
        except Exception as e:
            return jsonify({
                'memory_usage': 'N/A',
                'uploaded_files': 0,
                'processed_emails': 0,
                'server_status': 'error',
                'error': str(e)
            }), 500

    @app.route('/api/admin/cleanup-temp', methods=['POST'])
    def cleanup_temp_files():
        """임시 파일 수동 정리 API"""
        try:
            # 요청에서 파라미터 가져오기
            data = request.get_json() or {}
            days_old = data.get('days_old', 7)
            evidence_days_old = data.get('evidence_days_old', 30)

            # 정리 실행
            stats = temp_manager.cleanup_old_sessions(
                days_old=days_old,
                evidence_days_old=evidence_days_old
            )

            return jsonify({
                'success': True,
                'message': f"임시 파일 정리 완료",
                'stats': stats
            })
        except Exception as e:
            app.logger.error(f"임시 파일 정리 실패: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/admin/temp-sessions')
    def get_temp_sessions():
        """임시 세션 목록 조회 API"""
        try:
            sessions = temp_manager.list_sessions()
            return jsonify({
                'success': True,
                'total': len(sessions),
                'sessions': sessions[:100]  # 최대 100개만 반환
            })
        except Exception as e:
            app.logger.error(f"세션 목록 조회 실패: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/admin')
    def admin_page():
        """관리자 페이지 - 블루프린트로 위임(존재하면 리다이렉트), 없으면 기존 템플릿 렌더링"""
        try:
            # prefer blueprint-provided admin index if available
            return redirect(url_for('admin_bp.admin_index'))
        except Exception:
            return render_template('admin.html')

    @app.route('/emails/<file_id>')
    def email_list(file_id):
        """이메일 목록 페이지 - 선택적 증거 생성 기능 포함"""
        if file_id not in processed_emails:
            flash('파일을 찾을 수 없습니다.', 'error')
            return redirect(url_for('index'))

        data = processed_emails[file_id]
        file_info = uploaded_files.get(file_id, {})

        return render_template('email_list.html',
                               emails=data['emails'],
                               filename=data['filename'],
                               file_id=file_id,
                               file_info=file_info,
                               evidence_generated=data.get(
                                   'evidence_generated', False),
                               generated_evidence=data.get('generated_evidence', []))

    @app.route('/generate_evidence/<file_id>', methods=['POST'])
    def generate_evidence(file_id):
        """선택된 이메일들에 대해 증거 생성"""
        if file_id not in processed_emails:
            return jsonify({'error': '파일을 찾을 수 없습니다.'}), 404

        try:
            selected_indices = request.json.get('selected_indices', [])
            if not selected_indices:
                return jsonify({'error': '선택된 이메일이 없습니다.'}), 400

            # 옵션 가져오기
            evidence_prefix = request.json.get('evidence_prefix', '갑')
            options = {
                'evidence_prefix': evidence_prefix,
                'generate_timeline': request.json.get('generate_timeline', True),
                'extract_attachments': request.json.get('extract_attachments', True),
                'verify_integrity': request.json.get('verify_integrity', True)
            }

            # 백그라운드에서 증거 생성 시작
            thread = threading.Thread(
                target=generate_evidence_background,
                args=(file_id, selected_indices, options)
            )
            thread.daemon = True
            thread.start()

            return jsonify({
                'success': True,
                'message': f'선택된 {len(selected_indices)}개 이메일에 대한 증거 생성을 시작했습니다.',
                'evidence_task_id': file_id + "_evidence"
            })

        except Exception as e:
            app.logger.error(f"증거 생성 요청 실패: {str(e)}")
            return jsonify({'error': '증거 생성 요청 처리 중 오류가 발생했습니다.'}), 500

    @app.route('/api/evidence_progress/<task_id>')
    def get_evidence_progress(task_id):
        """증거 생성 진행 상황 API"""
        progress_data = progress_tracker.get_progress(task_id)
        if not progress_data:
            return jsonify({'error': 'Task not found'}), 404

        return jsonify(progress_data)

    @app.route('/email/<file_id>/<int:email_index>')
    def email_detail(file_id, email_index):
        """이메일 상세 페이지"""
        if file_id not in processed_emails:
            flash('파일을 찾을 수 없습니다.', 'error')
            return redirect(url_for('index'))

        emails = processed_emails[file_id]['emails']
        if email_index >= len(emails):
            flash('존재하지 않는 이메일입니다.', 'error')
            return redirect(url_for('email_list', file_id=file_id))

        email = emails[email_index]
        processor = email_processors.get(file_id)

        # 상세 이메일 내용 가져오기
        if processor:
            try:
                # 메시지 ID로 전체 메시지 내용 가져오기
                message_content = processor.get_message_content(email['id'])
                email['full_content'] = message_content
            except Exception as e:
                app.logger.error(f"이메일 내용 로드 실패: {str(e)}")
                email['full_content'] = None

        return render_template('email_detail.html', email=email, file_id=file_id, email_index=email_index)

    @app.route('/process_selected', methods=['POST'])
    def process_selected_emails():
        """선택된 이메일들을 HTML/PDF로 처리"""
        try:
            data = request.get_json()
            file_id = data.get('file_id')
            selected_indices = data.get('selected_emails', [])
            party = data.get('party', '갑')  # 갑 또는 을
            convert_to_pdf = data.get('convert_to_pdf', False)

            if file_id not in email_processors:
                return jsonify({'error': '프로세서를 찾을 수 없습니다.'}), 400

            processor = email_processors[file_id]
            emails = processed_emails[file_id]['emails']

            # 선택된 메일 ID 목록
            selected_msg_ids = [emails[idx]['id']
                                for idx in selected_indices if idx < len(emails)]

            if not selected_msg_ids:
                return jsonify({'error': '선택된 이메일이 없습니다.'}), 400

            # 출력 디렉토리 생성
            output_dir = 'processed_emails'
            os.makedirs(output_dir, exist_ok=True)

            processed_files = []

            # HTML 파일 생성
            for i, msg_id in enumerate(selected_msg_ids):
                try:
                    html_filepath = processor.process_single_message(
                        msg_id, output_dir)
                    if html_filepath:
                        processed_files.append(html_filepath)
                except Exception as e:
                    app.logger.error(f"메시지 처리 실패 (ID: {msg_id}): {str(e)}")

            result = {
                'processed_count': len(processed_files),
                'html_files': processed_files
            }

            # PDF 변환 요청 시
            if convert_to_pdf and processed_files:
                try:
                    evidence_number_counter = {party: 0}
                    pdf_files = []

                    for html_file in processed_files:
                        success = processor.convert_html_to_pdf(
                            html_file, party, evidence_number_counter)
                        if success:
                            # PDF 파일 경로 추정 (실제 파일명은 processor 내부 로직에 따라 다름)
                            pdf_path = html_file.replace('.html', '.pdf')
                            if os.path.exists(pdf_path):
                                pdf_files.append(pdf_path)

                    result['pdf_files'] = pdf_files
                    result['pdf_count'] = len(pdf_files)

                except Exception as e:
                    app.logger.error(f"PDF 변환 실패: {str(e)}")
                    result['pdf_error'] = str(e)

            return jsonify(result)

        except Exception as e:
            app.logger.error(f"이메일 처리 실패: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/docs')
    def api_docs():
        """API 문서 페이지"""
        return render_template('api.html')

    @app.route('/integrity')
    def integrity():
        """무결성 검증 페이지"""
        return render_template('integrity.html')

    @app.route('/api/upload', methods=['POST'])
    def api_upload():
        """API: 파일 업로드"""
        try:
            if 'file' not in request.files:
                return jsonify({'error': '파일이 제공되지 않았습니다.'}), 400

            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': '파일이 선택되지 않았습니다.'}), 400

            if not allowed_file(file.filename):
                return jsonify({'error': '허용되지 않는 파일 형식입니다.'}), 400

            # 파일 처리 로직 (upload_file과 동일)
            filename = secure_filename(file.filename)
            file_id = str(uuid.uuid4())

            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, f"{file_id}_{filename}")
            file.save(temp_path)

            config_path = os.path.join(os.path.dirname(
                __file__), '..', '..', 'config.json')
            processor = EmailEvidenceProcessor(config_path)
            processor.load_mbox(temp_path)

            all_messages = processor.get_all_message_metadata()

            uploaded_files[file_id] = {
                'filename': filename,
                'temp_path': temp_path,
                'processed': True,
                'total_emails': len(all_messages)
            }

            processed_emails[file_id] = {
                'emails': all_messages,
                'filename': filename
            }

            email_processors[file_id] = processor

            return jsonify({
                'file_id': file_id,
                'filename': filename,
                'total_emails': len(all_messages),
                'message': '파일이 성공적으로 처리되었습니다.'
            })

        except Exception as e:
            app.logger.error(f"API 업로드 실패: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/emails/<file_id>')
    def api_email_list(file_id):
        """API: 이메일 목록 조회"""
        if file_id not in processed_emails:
            return jsonify({'error': '파일을 찾을 수 없습니다.'}), 404

        data = processed_emails[file_id]
        return jsonify({
            'filename': data['filename'],
            'emails': data['emails']
        })

    @app.route('/api/files')
    def api_file_list():
        """API: 업로드된 파일 목록"""
        return jsonify(uploaded_files)

    @app.route('/api/evidence/check')
    def api_evidence_check():
        """API: processed_emails 디렉터리 존재 및 파일 수 체크"""
        try:
            processed_dir = Path('processed_emails')
            if not processed_dir.exists():
                return jsonify({'has_evidence': False, 'count': 0})

            # 디렉터리 내 파일/폴더 수 카운트
            count = sum(1 for _ in processed_dir.iterdir())
            return jsonify({'has_evidence': count > 0, 'count': count})
        except Exception as e:
            current_app.logger.exception(f'api_evidence_check error: {e}')
            return jsonify({'has_evidence': False, 'count': 0, 'error': str(e)})

    @app.context_processor
    def inject_template_vars():
        """템플릿 전역 변수 주입"""
        return {
            'app_name': '이메일 증거 처리 시스템',
            'app_version': '2.0.0'
        }

    def upload_page():
        """파일 업로드 페이지"""
        return render_template('upload.html', page_title='mbox 파일 업로드')

    # 중복 라우트 제거됨 - upload_file 함수는 위에 정의되어 있음
    # 중복된 구현은 완전히 제거됨 (2025-01-15)
    #             return redirect(url_for('upload_page'))
    #
    #         # 통계 정보
    #         stats = email_service.get_email_statistics()
    #
    #         return render_template('email_list.html',
    #                                emails=result['emails'],
    #                                stats=stats,
    #                                filename=filename,
    #                                page_title=f'이메일 목록 - {filename}')
    #
    #     except Exception as e:
    #         flash(f'이메일 목록 로드 오류: {str(e)}', 'error')
    #         return redirect(url_for('upload_page'))

    @app.route('/evidence')
    def evidence_list():
        """증거 목록 페이지"""
        try:
            # 처리된 이메일 폴더 확인
            processed_dir = Path('processed_emails')
            if not processed_dir.exists() or not any(processed_dir.iterdir()):
                flash('처리된 이메일 증거가 없습니다. 먼저 mbox 파일을 업로드하고 처리해주세요.', 'warning')
                return render_template('evidence_list.html',
                                       evidence_list=[],
                                       stats={'total': 0, 'processed': 0},
                                       no_data=True,
                                       page_title='증거 목록')

            evidence_list = evidence_service.get_evidence_list()
            stats = evidence_service.get_evidence_statistics()

            # 증거가 없는 경우
            if not evidence_list or len(evidence_list) == 0:
                flash('증거 목록이 비어있습니다.', 'info')
                return render_template('evidence_list.html',
                                       evidence_list=[],
                                       stats=stats,
                                       no_data=True,
                                       page_title='증거 목록')

            return render_template('evidence_list.html',
                                   evidence_list=evidence_list,
                                   stats=stats,
                                   no_data=False,
                                   page_title='증거 목록')

        except Exception as e:
            flash(f'증거 목록 로드 오류: {str(e)}', 'error')
            return redirect(url_for('index'))

    @app.route('/evidence/<folder_name>')
    def evidence_detail(folder_name):
        """증거 상세 페이지"""
        try:
            result = evidence_service.get_evidence_details(folder_name)
            if not result['success']:
                flash(result['message'], 'error')
                return redirect(url_for('evidence_list'))

            return render_template('evidence_detail.html',
                                   evidence=result['details'],
                                   folder_name=folder_name,
                                   page_title=f'증거 상세 - {folder_name}')

        except Exception as e:
            flash(f'증거 상세 로드 오류: {str(e)}', 'error')
            return redirect(url_for('evidence_list'))

    @app.route('/timeline')
    def timeline_page():
        """타임라인 페이지"""
        try:
            # 증거 목록으로부터 타임라인 생성
            evidence_list = evidence_service.get_evidence_list()
            timeline_result = timeline_service.generate_timeline_from_evidence(
                evidence_list)

            if not timeline_result['success']:
                flash(timeline_result['message'], 'error')
                return redirect(url_for('index'))

            # 웹용 타임라인 데이터 생성
            timeline_data = timeline_result['timeline']
            summary = timeline_service.get_timeline_summary(timeline_data)

            return render_template('timeline.html',
                                   timeline_data=timeline_data,
                                   summary=summary,
                                   page_title='이메일 타임라인')

        except Exception as e:
            flash(f'타임라인 로드 오류: {str(e)}', 'error')
            return redirect(url_for('index'))

    # [2025-12-30] 아래 라우트들은 main_routes.py Blueprint로 이동됨
    # - /search (검색 페이지)
    # - /settings (설정 페이지)
    # - /download/<path:filename> (파일 다운로드)

    @app.route('/evidence_management')
    def evidence_management():
        """증거 관리 - 업로드된 파일 목록"""
        try:
            # show_deleted 파라미터 확인 (관리자 기능)
            show_deleted = request.args.get(
                'show_deleted', 'false').lower() == 'true'

            # 데이터베이스에서 업로드된 파일 조회 (실패 시 폴백)
            if USE_DATABASE and email_db:
                try:
                    # get_all_uploaded_files 메서드 사용
                    upload_files = email_db.get_all_uploaded_files(
                        include_deleted=show_deleted)

                    # 데이터 포맷팅
                    for file_info in upload_files:
                        if file_info.get('file_size'):
                            file_info['size_mb'] = f"{file_info['file_size'] / (1024 * 1024):.2f}"
                        else:
                            file_info['size_mb'] = "0.00"
                except Exception as db_err:
                    app.logger.warning(f"⚠️ DB 파일 조회 실패 (폴백): {db_err}")
                    # 폴백: uploads 디렉토리에서 파일 스캔
                    upload_files = []
            else:
                # 폴백: uploads 디렉토리에서 파일 스캔
                uploads_dir = Path('uploads')
                processed_dir = Path('processed_emails')

                upload_files = []
                if uploads_dir.exists():
                    for file_path in sorted(uploads_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
                        if file_path.is_file() and file_path.suffix.lower() in ['.mbox', '.eml', '.msg']:
                            file_stat = file_path.stat()
                            file_size_mb = file_stat.st_size / (1024 * 1024)
                            upload_time = datetime.fromtimestamp(
                                file_stat.st_mtime)

                            # 처리된 이메일 개수 확인
                            processed_count = 0
                            if processed_dir.exists():
                                base_name = file_path.stem
                                for folder in processed_dir.iterdir():
                                    if folder.is_dir() and base_name in folder.name:
                                        processed_count += 1

                            upload_files.append({
                                'filename': file_path.name,
                                'upload_time': upload_time.strftime('%Y-%m-%d %H:%M:%S'),
                                'size_mb': f"{file_size_mb:.2f}",
                                'processed_count': processed_count,
                                'file_id': file_path.stem,
                                'deleted': False
                            })

            return render_template('evidence_management.html',
                                   upload_files=upload_files,
                                   total_count=len(upload_files),
                                   show_deleted=show_deleted)
        except Exception as e:
            flash(f'증거 관리 페이지 로드 오류: {str(e)}', 'error')
            return redirect(url_for('index'))

    @app.route('/api/delete_files', methods=['POST'])
    def delete_files():
        """파일 삭제 API (소프트 삭제 + 물리적 삭제)"""
        try:
            data = request.json
            file_ids = data.get('file_ids', [])
            confirm = data.get('confirm', False)
            reason = data.get('reason', '사용자 요청')

            if not confirm:
                return jsonify({
                    'success': False,
                    'message': '삭제 확인이 필요합니다.'
                }), 400

            if not file_ids or not isinstance(file_ids, list):
                return jsonify({
                    'success': False,
                    'message': '삭제할 파일 ID를 지정해야 합니다.'
                }), 400

            deleted_count = 0
            errors = []
            deleted_files = []

            from src.utils.file_deleter import delete_physical_files

            for file_id in file_ids:
                try:
                    # 1. 소프트 삭제 (DB에 deleted 마킹 - 실패해도 물리적 삭제는 진행)
                    if USE_DATABASE and email_db:
                        try:
                            soft_delete_result = email_db.soft_delete_file(
                                file_id, reason)
                            if not soft_delete_result:
                                app.logger.warning(
                                    f"⚠️ DB 소프트 삭제 실패 (무시): {file_id}")
                        except Exception as db_err:
                            app.logger.warning(
                                f"⚠️ DB 소프트 삭제 실패 (무시): {file_id} - {db_err}")

                    # 2. 물리적 파일 삭제
                    delete_result = delete_physical_files(file_id)

                    if delete_result['errors']:
                        errors.extend(delete_result['errors'])

                    deleted_files.append({
                        'file_id': file_id,
                        'uploads_deleted': delete_result['uploads_deleted'],
                        'evidence_deleted': delete_result['evidence_deleted'],
                        'evidence_folders': delete_result['evidence_folders']
                    })

                    deleted_count += 1

                except Exception as e:
                    errors.append(f"{file_id}: {str(e)}")

            return jsonify({
                'success': True,
                'message': f'{deleted_count}개의 파일이 삭제되었습니다.',
                'deleted_count': deleted_count,
                'deleted_files': deleted_files,
                'errors': errors
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'파일 삭제 중 오류: {str(e)}'
            }), 500

    @app.route('/evidence_file/<file_id>')
    def evidence_file_detail(file_id):
        """특정 업로드 파일의 처리된 이메일 상세 목록"""
        try:
            processed_dir = Path('processed_emails')

            # 해당 파일로 처리된 이메일 폴더 리스트 수집
            evidence_folders = []
            if processed_dir.exists():
                for folder in sorted(processed_dir.iterdir()):
                    if folder.is_dir() and file_id in folder.name and not folder.name.startswith('0'):
                        # 폴더 정보 추출
                        folder_name = folder.name

                        # 날짜 추출 (예: [2021-01-13])
                        date_match = folder_name.split('_')[0].strip('[]')

                        # 제목 추출
                        title = '_'.join(folder_name.split(
                            '_')[1:]) if '_' in folder_name else folder_name

                        # 파일 개수 확인
                        file_count = len(
                            [f for f in folder.iterdir() if f.is_file()])

                        # 폴더 크기 계산
                        total_size = sum(
                            f.stat().st_size for f in folder.rglob('*') if f.is_file())
                        size_mb = total_size / (1024 * 1024)

                        evidence_folders.append({
                            'folder_name': folder_name,
                            'date': date_match,
                            'title': title,
                            'file_count': file_count,
                            'size_mb': f"{size_mb:.2f}",
                            'path': str(folder)
                        })

            return render_template('evidence_detail.html',
                                   file_id=file_id,
                                   evidence_folders=evidence_folders,
                                   total_count=len(evidence_folders))
        except Exception as e:
            flash(f'증거 상세 페이지 로드 오류: {str(e)}', 'error')
            return redirect(url_for('evidence_management'))

    @app.route('/additional_evidence')
    def additional_evidence():
        """추가 증거 관리 페이지"""
        try:
            manager = AdditionalEvidenceManager()
            evidence_list = manager.get_evidence_list()
            statistics = manager.get_statistics()

            return render_template('additional_evidence.html',
                                   evidence_list=evidence_list,
                                   statistics=statistics)
        except Exception as e:
            flash(f'추가 증거 관리 오류: {str(e)}', 'error')
            return redirect(url_for('index'))

    @app.route('/add_evidence', methods=['GET', 'POST'])
    def add_evidence():
        """추가 증거 파일 등록"""
        if request.method == 'GET':
            return render_template('add_evidence.html')

        try:
            # 파일 업로드 처리
            if 'evidence_file' not in request.files:
                flash('파일이 선택되지 않았습니다.', 'error')
                return redirect(request.url)

            file = request.files['evidence_file']
            if file.filename == '':
                flash('파일이 선택되지 않았습니다.', 'error')
                return redirect(request.url)

            # 임시 파일 저장
            temp_dir = Path(tempfile.gettempdir()) / "evidence_upload"
            temp_dir.mkdir(exist_ok=True)

            filename = secure_filename(file.filename)
            temp_path = temp_dir / filename
            file.save(str(temp_path))

            # 폼 데이터 수집
            title = request.form.get('title', '').strip()
            description = request.form.get('description', '').strip()
            party = request.form.get('party', '갑')
            evidence_date = request.form.get('evidence_date', '')
            related_emails = request.form.get('related_emails', '').strip()

            if not title:
                flash('증거 제목을 입력해주세요.', 'error')
                temp_path.unlink()
                return redirect(request.url)

            # 관련 이메일 ID 처리
            related_email_ids = []
            if related_emails:
                related_email_ids = [email.strip()
                                     for email in related_emails.split(',')]

            # 추가 증거 등록
            manager = AdditionalEvidenceManager()
            evidence_info = manager.add_evidence_file(
                file_path=str(temp_path),
                title=title,
                description=description,
                party=party,
                evidence_date=evidence_date,
                related_email_ids=related_email_ids
            )

            # 임시 파일 삭제
            temp_path.unlink()

            flash(
                f'추가 증거가 성공적으로 등록되었습니다: {evidence_info["evidence_number"]}', 'success')
            return redirect(url_for('additional_evidence'))

        except Exception as e:
            flash(f'추가 증거 등록 실패: {str(e)}', 'error')
            return redirect(request.url)

    @app.route('/api/evidence_categories')
    def api_evidence_categories():
        """증거 카테고리 정보 API"""
        try:
            manager = AdditionalEvidenceManager()
            return jsonify({
                'success': True,
                'categories': manager.category_names,
                'allowed_formats': manager.allowed_formats
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/edit_evidence/<file_id>', methods=['GET', 'POST'])
    def edit_evidence(file_id):
        """추가 증거 편집"""
        manager = AdditionalEvidenceManager()
        evidence = manager.get_evidence_by_id(file_id)

        if not evidence:
            flash('해당 증거를 찾을 수 없습니다.', 'error')
            return redirect(url_for('additional_evidence'))

        if request.method == 'GET':
            return render_template('edit_evidence.html', evidence=evidence)

        try:
            # 업데이트할 데이터 수집
            updates = {}

            if request.form.get('title'):
                updates['title'] = request.form.get('title').strip()

            if request.form.get('description'):
                updates['description'] = request.form.get(
                    'description').strip()

            if request.form.get('evidence_date'):
                updates['evidence_date'] = request.form.get('evidence_date')

            if request.form.get('related_emails'):
                related_emails = request.form.get('related_emails').strip()
                updates['related_email_ids'] = [email.strip()
                                                for email in related_emails.split(',') if email.strip()]

            # 메타데이터 업데이트
            if manager.update_evidence_metadata(file_id, updates):
                flash('증거 정보가 성공적으로 업데이트되었습니다.', 'success')
            else:
                flash('증거 정보 업데이트에 실패했습니다.', 'error')

            return redirect(url_for('additional_evidence'))

        except Exception as e:
            flash(f'증거 편집 실패: {str(e)}', 'error')
            return redirect(url_for('additional_evidence'))

    @app.route('/delete_evidence/<file_id>', methods=['POST'])
    def delete_evidence(file_id):
        """추가 증거 삭제"""
        try:
            manager = AdditionalEvidenceManager()
            if manager.remove_evidence(file_id):
                flash('증거가 성공적으로 삭제되었습니다.', 'success')
            else:
                flash('증거 삭제에 실패했습니다.', 'error')
        except Exception as e:
            flash(f'증거 삭제 실패: {str(e)}', 'error')

        return redirect(url_for('additional_evidence'))

    @app.route('/download_evidence_index')
    def download_evidence_index():
        """추가 증거 목록서 다운로드"""
        try:
            manager = AdditionalEvidenceManager()
            index_file = manager.generate_evidence_index()

            return send_file(index_file, as_attachment=True)

        except Exception as e:
            flash(f'증거목록서 다운로드 실패: {str(e)}', 'error')
            return redirect(url_for('additional_evidence'))

    @app.route('/export_additional_evidence')
    def export_additional_evidence():
        """추가 증거 법원 제출용 패키징"""
        try:
            manager = AdditionalEvidenceManager()
            export_dir = manager.export_for_court_submission()

            # ZIP 파일로 압축
            import zipfile
            zip_path = f"{export_dir}.zip"

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                export_path = Path(export_dir)
                for file_path in export_path.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(export_path.parent)
                        zipf.write(file_path, arcname)

            return send_file(zip_path, as_attachment=True,
                             download_name=f"법원제출용_추가증거_{datetime.now().strftime('%Y%m%d')}.zip")

        except Exception as e:
            flash(f'추가 증거 패키징 실패: {str(e)}', 'error')
            return redirect(url_for('additional_evidence'))

    @app.route('/integrated_timeline')
    def integrated_timeline():
        """통합 타임라인 페이지"""
        try:
            # 처리된 이메일 폴더 확인
            processed_dir = Path('processed_emails')
            if not processed_dir.exists() or not any(processed_dir.iterdir()):
                flash('처리된 이메일 데이터가 없습니다. 먼저 mbox 파일을 업로드하고 처리해주세요.', 'warning')
                return render_template('integrated_timeline.html',
                                       timeline_result=None,
                                       no_data=True)

            from src.timeline.integrated_timeline_generator import \
                IntegratedTimelineGenerator

            generator = IntegratedTimelineGenerator()
            result = generator.generate_integrated_timeline()

            # 타임라인 항목이 없는 경우
            if not result or not hasattr(result, 'timeline_items') or len(result.timeline_items) == 0:
                flash('타임라인에 표시할 데이터가 없습니다.', 'info')
                return render_template('integrated_timeline.html',
                                       timeline_result=None,
                                       no_data=True)

            return render_template('integrated_timeline.html',
                                   timeline_result=result,
                                   no_data=False)
        except Exception as e:
            flash(f'통합 타임라인 생성 오류: {str(e)}', 'error')
            app.logger.error(
                f'Integrated timeline error: {str(e)}', exc_info=True)
            return redirect(url_for('index'))

    @app.route('/generate_timeline_package')
    def generate_timeline_package():
        """법원 제출용 타임라인 패키지 생성"""
        try:
            from src.timeline.integrated_timeline_generator import \
                IntegratedTimelineGenerator

            generator = IntegratedTimelineGenerator()
            result = generator.generate_integrated_timeline()

            # 가장 최근 패키지 디렉토리 찾기
            timeline_dir = Path("processed_emails") / "06_통합타임라인"
            package_dirs = list(timeline_dir.glob("법원제출용_통합증거_*"))

            if not package_dirs:
                flash('생성된 패키지가 없습니다.', 'error')
                return redirect(url_for('integrated_timeline'))

            # 가장 최근 패키지를 ZIP으로 압축
            latest_package = max(package_dirs, key=lambda p: p.stat().st_mtime)

            import zipfile
            zip_path = f"{latest_package}.zip"

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in latest_package.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(latest_package.parent)
                        zipf.write(file_path, arcname)

            return send_file(zip_path, as_attachment=True,
                             download_name=f"법원제출용_통합증거_{datetime.now().strftime('%Y%m%d')}.zip")

        except Exception as e:
            flash(f'타임라인 패키지 생성 실패: {str(e)}', 'error')
            return redirect(url_for('integrated_timeline'))

    @app.route('/download_timeline_excel')
    def download_timeline_excel():
        """통합 타임라인 Excel 다운로드"""
        try:
            timeline_dir = Path("processed_emails") / "06_통합타임라인"
            excel_files = list(timeline_dir.glob("통합타임라인_*.xlsx"))

            if not excel_files:
                flash('생성된 Excel 파일이 없습니다. 먼저 통합 타임라인을 생성하세요.', 'error')
                return redirect(url_for('integrated_timeline'))

            # 가장 최근 Excel 파일
            latest_excel = max(excel_files, key=lambda p: p.stat().st_mtime)

            return send_file(str(latest_excel.absolute()),
                             as_attachment=True,
                             download_name=f"통합타임라인_{datetime.now().strftime('%Y%m%d')}.xlsx")

        except Exception as e:
            flash(f'Excel 다운로드 실패: {str(e)}', 'error')
            return redirect(url_for('integrated_timeline'))

    @app.route('/verify_integrity')
    def verify_integrity():
        """법원 제출용 무결성 검증 페이지"""
        try:
            # Lazy import to avoid loading heavy dependencies at startup
            from src.legal_compliance.court_evidence_verifier import \
                CourtEvidenceIntegrityVerifier

            # 처리된 이메일 폴더 확인
            processed_dir = Path('processed_emails')
            if not processed_dir.exists() or not any(processed_dir.iterdir()):
                flash('검증할 증거 데이터가 없습니다. 먼저 mbox 파일을 업로드하고 처리해주세요.', 'warning')
                return render_template('verify_integrity.html',
                                       verification_report=None,
                                       no_data=True)

            # 기본 프로젝트 디렉토리에서 검증
            verifier = CourtEvidenceIntegrityVerifier("processed_emails")
            verification_report = verifier.verify_all_evidence()

            # 검증할 파일이 없는 경우
            if not verification_report or not hasattr(verification_report, 'verified_files') or len(verification_report.verified_files) == 0:
                flash('검증할 파일이 없습니다.', 'info')
                return render_template('verify_integrity.html',
                                       verification_report=None,
                                       no_data=True)

            return render_template('verify_integrity.html',
                                   verification_report=verification_report,
                                   no_data=False)
        except Exception as e:
            flash(f'무결성 검증 오류: {str(e)}', 'error')
            app.logger.error(
                f'Verify integrity error: {str(e)}', exc_info=True)
            return redirect(url_for('index'))

    @app.route('/api/verify_integrity')
    def api_verify_integrity():
        """법원 제출용 무결성 검증 API"""
        try:
            # Lazy import to avoid loading heavy dependencies at startup
            from src.legal_compliance.court_evidence_verifier import \
                CourtEvidenceIntegrityVerifier

            verifier = CourtEvidenceIntegrityVerifier("processed_emails")
            verification_report = verifier.verify_all_evidence()

            return jsonify({
                'success': True,
                'verification_report': verification_report
            })
        except Exception as e:
            app.logger.error(
                f'API verify integrity error: {str(e)}', exc_info=True)
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/check_processed_emails')
    def api_check_processed_emails():
        """처리된 이메일 존재 여부 확인 API"""
        try:
            processed_dir = Path("processed_emails")
            has_processed = processed_dir.exists() and any(processed_dir.iterdir())

            return jsonify({
                'success': True,
                'has_processed_emails': has_processed,
                'processed_count': len(list(processed_dir.iterdir())) if has_processed else 0
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e),
                'has_processed_emails': False
            })

    @app.route('/download_verification_report')
    def download_verification_report():
        """무결성 검증 보고서 다운로드"""
        try:
            # 가장 최근 검증 보고서 찾기
            verification_dir = Path("processed_emails") / "04_검증자료"
            if not verification_dir.exists():
                flash('검증 보고서가 없습니다. 먼저 무결성 검증을 실행하세요.', 'error')
                return redirect(url_for('verify_integrity'))

            # JSON 보고서 파일 찾기
            json_reports = list(verification_dir.glob("무결성검증보고서_*.json"))
            if not json_reports:
                flash('검증 보고서 파일을 찾을 수 없습니다.', 'error')
                return redirect(url_for('verify_integrity'))

            # 가장 최근 파일
            latest_report = max(json_reports, key=lambda p: p.stat().st_mtime)

            return send_file(str(latest_report.absolute()),
                             as_attachment=True,
                             download_name=f"무결성검증보고서_{latest_report.stem.split('_')[-1]}.json")

        except Exception as e:
            flash(f'보고서 다운로드 오류: {str(e)}', 'error')
            return redirect(url_for('verify_integrity'))

    @app.route('/download_court_certificate')
    def download_court_certificate():
        """법원 제출용 무결성 증명서 다운로드"""
        try:
            # 법원 제출용 증명서 찾기
            verification_dir = Path("processed_emails") / "04_검증자료"
            if not verification_dir.exists():
                flash('검증 증명서가 없습니다. 먼저 무결성 검증을 실행하세요.', 'error')
                return redirect(url_for('verify_integrity'))

            # 법원 제출용 증명서 파일 찾기
            cert_files = list(verification_dir.glob("법원제출용_무결성증명서_*.txt"))
            if not cert_files:
                flash('법원 제출용 증명서 파일을 찾을 수 없습니다.', 'error')
                return redirect(url_for('verify_integrity'))

            # 가장 최근 파일
            latest_cert = max(cert_files, key=lambda p: p.stat().st_mtime)

            return send_file(str(latest_cert.absolute()),
                             as_attachment=True,
                             download_name=f"법원제출용_무결성증명서_{latest_cert.stem.split('_')[-1]}.txt")

        except Exception as e:
            flash(f'증명서 다운로드 오류: {str(e)}', 'error')
            return redirect(url_for('verify_integrity'))

    @app.context_processor
    def inject_template_vars():
        """템플릿 전역 변수 주입"""
        return {
            'app_name': '이메일 증거 처리 시스템',
            'app_version': '2.0.0'
        }

    # [2025-12-30] 중복 라우트 제거: integrated_timeline, generate_timeline_package, download_timeline_excel

    # ========================================================================
    # 로그 뷰어 라우트 (DB 기반)
    # ========================================================================

    @app.route('/logs')
    def logs_viewer():
        """로그 뷰어 페이지"""
        try:
            return render_template('log_viewer.html')
        except Exception as e:
            app.logger.error(f"로그 뷰어 페이지 로드 실패: {str(e)}", exc_info=True)
            return f"로그 뷰어 로드 실패: {str(e)}", 500

    @app.route('/api/logs')
    def api_logs():
        """최근 로그 조회 API (DB 기반 - 실패 시 메모리 폴백)"""
        try:
            from src.database.email_db import db

            level = request.args.get('level', None)
            limit = request.args.get('limit', 1000, type=int)
            offset = request.args.get('offset', 0, type=int)

            try:
                logs = db.get_logs(limit=limit, offset=offset, level=level)
                total_count = db.get_log_count(level=level)
            except Exception as db_err:
                app.logger.warning(f"⚠️ DB 로그 조회 실패 (빈 결과 반환): {db_err}")
                logs = []
                total_count = 0

            # 통계 계산
            stats = {}
            for log in logs:
                log_level = log.get('level', 'INFO')
                stats[log_level] = stats.get(log_level, 0) + 1

            return jsonify({
                'success': True,
                'logs': logs,
                'stats': stats,
                'count': len(logs),
                'total': total_count,
                'offset': offset,
                'limit': limit
            })
        except Exception as e:
            app.logger.error(f"로그 조회 API 실패: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/logs/download')
    def api_logs_download():
        """로그 다운로드 (JSON) - DB 실패 시 빈 파일"""
        try:
            import json

            from src.database.email_db import db

            level = request.args.get('level', None)
            limit = request.args.get('limit', 5000, type=int)

            try:
                logs = db.get_logs(limit=limit, level=level)
            except Exception as db_err:
                app.logger.warning(f"⚠️ DB 로그 조회 실패 (빈 파일 생성): {db_err}")
                logs = []

            # JSON 파일로 생성
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"logs_{timestamp}.json"
            temp_file = temp_manager.create_temp_file(filename, cleanup=False)

            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)

            return send_file(
                temp_file,
                as_attachment=True,
                download_name=filename,
                mimetype='application/json'
            )
        except Exception as e:
            app.logger.error(f"로그 다운로드 실패: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/logs/clear', methods=['POST'])
    def api_logs_clear():
        """DB 로그 초기화 API - DB 실패 시 안내"""
        try:
            # 7일 이전 로그만 삭제 (안전장치)
            from datetime import timedelta

            from src.database.email_db import db
            cutoff = (datetime.now() - timedelta(days=7)).isoformat()

            try:
                deleted = db.clear_logs(before_time=cutoff)
            except Exception as db_err:
                app.logger.warning(f"⚠️ DB 로그 삭제 실패: {db_err}")
                return jsonify({
                    'success': False,
                    'error': 'DB 연결 실패 - 로그를 삭제할 수 없습니다.',
                    'db_available': False
                }), 503

            return jsonify({
                'success': True,
                'message': f'{deleted}개의 로그가 삭제되었습니다.'
            })
        except Exception as e:
            app.logger.error(f"로그 초기화 실패: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/logs/files')
    def api_log_files():
        """로그 파일 목록 조회 API"""
        try:
            log_dir = Path('logs')
            if not log_dir.exists():
                return jsonify({
                    'success': True,
                    'files': [],
                    'count': 0
                })

            files = []
            for log_file in sorted(log_dir.glob('*.log'), reverse=True)[:50]:
                stat = log_file.stat()
                files.append({
                    'name': log_file.name,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })

            return jsonify({
                'success': True,
                'files': files,
                'count': len(files)
            })
        except Exception as e:
            app.logger.error(f"로그 파일 목록 조회 실패: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/logs/file/<filename>')
    def api_log_file_view(filename):
        """특정 로그 파일 내용 보기 (HTML)"""
        try:
            log_dir = Path('logs')
            file_path = log_dir / filename

            if not file_path.exists() or not file_path.is_file():
                return "로그 파일을 찾을 수 없습니다.", 404

            # 경로 탐색 공격 방지
            if not str(file_path.resolve()).startswith(str(log_dir.resolve())):
                return "잘못된 파일 경로입니다.", 403

            lines = request.args.get('lines', 500, type=int)

            # 파일 읽기 (마지막 N줄)
            with open(file_path, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                content_lines = all_lines[-lines:] if len(
                    all_lines) > lines else all_lines
                content = ''.join(content_lines)

            # HTML로 렌더링
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>{filename}</title>
                <style>
                    body {{
                        font-family: 'Consolas', 'Monaco', monospace;
                        background: #1e1e1e;
                        color: #d4d4d4;
                        padding: 2rem;
                        margin: 0;
                    }}
                    pre {{
                        background: #252526;
                        padding: 1rem;
                        border-radius: 8px;
                        overflow-x: auto;
                        font-size: 0.9rem;
                        line-height: 1.5;
                    }}
                    h1 {{
                        color: #fff;
                    }}
                </style>
            </head>
            <body>
                <h1>{filename}</h1>
                <pre>{content}</pre>
            </body>
            </html>
            """
            return html_content
        except Exception as e:
            app.logger.error(f"로그 파일 보기 실패: {str(e)}", exc_info=True)
            return f"로그 파일 보기 실패: {str(e)}", 500

    @app.route('/api/logs/file/<filename>/download')
    def api_log_file_download(filename):
        """특정 로그 파일 다운로드"""
        try:
            log_dir = Path('logs')
            file_path = log_dir / filename

            if not file_path.exists() or not file_path.is_file():
                return "로그 파일을 찾을 수 없습니다.", 404

            # 경로 탐색 공격 방지
            if not str(file_path.resolve()).startswith(str(log_dir.resolve())):
                return "잘못된 파일 경로입니다.", 403

            return send_file(
                file_path,
                as_attachment=True,
                download_name=filename,
                mimetype='text/plain'
            )
        except Exception as e:
            app.logger.error(f"로그 파일 다운로드 실패: {str(e)}", exc_info=True)
            return f"로그 파일 다운로드 실패: {str(e)}", 500
