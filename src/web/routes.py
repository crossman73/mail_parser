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

    # Evidence Blueprint 등록 (evidence_service 필요)
    try:
        from src.web.blueprints.evidence_routes import (evidence_bp,
                                                        init_evidence_services)

        # USE_DATABASE와 email_db는 여기서 가져옴
        USE_DATABASE = app.config.get('USE_DATABASE', False)
        email_db = getattr(app, 'email_db', None)
        init_evidence_services(evidence_service, USE_DATABASE, email_db)
        app.register_blueprint(evidence_bp)
        app.logger.info('✅ Evidence blueprint registered (/evidence, /evidence_management, /add_evidence, etc.)')
    except Exception as e:
        app.logger.warning(f'⚠️ Evidence blueprint 등록 실패 (계속 진행): {e}')

    # Timeline Blueprint 등록 (timeline_service, evidence_service 필요)
    try:
        from src.web.blueprints.timeline_routes import (init_timeline_services,
                                                        timeline_bp)
        init_timeline_services(timeline_service, evidence_service)
        app.register_blueprint(timeline_bp)
        app.logger.info('✅ Timeline blueprint registered (/timeline, /integrated_timeline, /generate_timeline_package, etc.)')
    except Exception as e:
        app.logger.warning(f'⚠️ Timeline blueprint 등록 실패 (계속 진행): {e}')

    # Integrity Blueprint 등록
    try:
        from src.web.blueprints.integrity_routes import integrity_bp
        app.register_blueprint(integrity_bp)
        app.logger.info('✅ Integrity blueprint registered (/integrity, /verify_integrity, /download_verification_report, etc.)')
    except Exception as e:
        app.logger.warning(f'⚠️ Integrity blueprint 등록 실패 (계속 진행): {e}')

    # Logs Blueprint 등록
    try:
        from src.web.blueprints.logs_routes import logs_bp
        app.register_blueprint(logs_bp)
        app.logger.info('✅ Logs blueprint registered (/logs, /api/logs, /api/logs/download, etc.)')
    except Exception as e:
        app.logger.warning(f'⚠️ Logs blueprint 등록 실패 (계속 진행): {e}')

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
                return redirect(url_for('upload_file'))

            file = request.files['mbox_file']
            if file.filename == '':
                flash('파일이 선택되지 않았습니다.', 'error')
                return redirect(url_for('upload_file'))

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
                return redirect(url_for('upload_file'))

        except Exception as e:
            app.logger.error(f"업로드 처리 실패: {str(e)}")
            flash('파일 업로드 중 오류가 발생했습니다.', 'error')
            return redirect(url_for('upload_file'))

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

    # [2025-12-30] 아래 라우트들은 email_routes.py Blueprint로 이동됨
    # - /emails/<file_id> (이메일 목록)
    # - /email/<file_id>/<int:email_index> (이메일 상세)
    # - /generate_evidence/<file_id> (증거 생성) - ⚠️ 중복 제거됨
    # - /api/evidence_progress/<task_id> (진행 상황)
    # - /process_selected (선택 이메일 처리)

    # [2025-12-30] /generate_evidence/<file_id>는 email_routes.py에 이미 존재하므로 제거됨
    # @app.route('/generate_evidence/<file_id>', methods=['POST'])
    # def generate_evidence(file_id):
    #     """선택된 이메일들에 대해 증거 생성"""
    #     ...
    #
    # generate_evidence_background 함수는 여기 유지 (Blueprint에서 호출)


    @app.route('/api/docs')
    def api_docs():
        """API 문서 페이지 (DB 기반 동적 생성)"""
        from src.database.connection import db_connection

        try:
            with db_connection.get_connection() as conn:
                cursor = conn.cursor()

                # 카테고리별 통계 조회
                cursor.execute('''
                    SELECT category, COUNT(*) as count
                    FROM api_endpoints
                    WHERE deprecated = 0
                    GROUP BY category
                    ORDER BY category
                ''')
                categories = cursor.fetchall()

                # 전체 엔드포인트 조회
                cursor.execute('''
                    SELECT id, path, method, summary, description, category, auth_required
                    FROM api_endpoints
                    WHERE deprecated = 0
                    ORDER BY category, path, method
                ''')
                endpoints_raw = cursor.fetchall()

                # 엔드포인트를 딕셔너리 리스트로 변환
                endpoints = []
                for ep in endpoints_raw:
                    endpoint_id, path, method, summary, description, category, auth_required = ep
                    endpoints.append({
                        'id': endpoint_id,
                        'path': path,
                        'method': method,
                        'summary': summary or f"{path} {method}",
                        'description': description or '',
                        'category': category,
                        'auth_required': bool(auth_required)
                    })

                return render_template('api.html',
                                     categories=categories,
                                     endpoints=endpoints)
        except Exception as e:
            app.logger.error(f"API 문서 조회 오류: {e}")
            # 폴백: 정적 템플릿 렌더링
            return render_template('api.html', categories=[], endpoints=[])

    @app.route('/api/test-result', methods=['POST'])
    def api_test_result():
        """API 테스트 결과 저장"""
        from src.database.connection import db_connection

        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400

            # endpoint_id 조회
            endpoint_path = data.get('endpoint')
            method = data.get('method')

            if not endpoint_path or not method:
                return jsonify({'error': 'endpoint and method are required'}), 400

            with db_connection.get_connection() as conn:
                cursor = conn.cursor()

                # endpoint_id 찾기
                cursor.execute(
                    "SELECT id FROM api_endpoints WHERE path = ? AND method = ?",
                    (endpoint_path, method)
                )
                result = cursor.fetchone()

                if not result:
                    return jsonify({'error': 'Endpoint not found'}), 404

                endpoint_id = result[0]

                # 테스트 결과 저장
                cursor.execute("""
                    INSERT INTO api_test_executions
                    (endpoint_id, method, status_code, response_time_ms, success,
                     error_message, request_data, response_data, user_agent)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    endpoint_id,
                    method,
                    data.get('status_code'),
                    data.get('response_time_ms'),
                    1 if data.get('success') else 0,
                    data.get('error_message'),
                    data.get('request_data'),
                    data.get('response_data', '')[:1000],  # 1KB로 제한
                    request.headers.get('User-Agent')
                ))

                conn.commit()

                return jsonify({
                    'success': True,
                    'message': 'Test result saved',
                    'id': cursor.lastrowid
                }), 201

        except Exception as e:
            app.logger.error(f"API 테스트 결과 저장 오류: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/docs/history')
    def api_docs_history():
        """API 테스트 이력 조회"""
        from src.database.connection import db_connection

        try:
            with db_connection.get_connection() as conn:
                cursor = conn.cursor()

                # 최근 100개 테스트 이력
                cursor.execute("""
                    SELECT
                        e.path, e.method, e.category,
                        t.status_code, t.response_time_ms, t.success,
                        t.executed_at, t.error_message, t.id
                    FROM api_test_executions t
                    JOIN api_endpoints e ON t.endpoint_id = e.id
                    ORDER BY t.executed_at DESC
                    LIMIT 100
                """)
                history_raw = cursor.fetchall()

                # 통계
                cursor.execute("""
                    SELECT
                        COUNT(*) as total,
                        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_count,
                        AVG(response_time_ms) as avg_response_time
                    FROM api_test_executions
                    WHERE executed_at >= datetime('now', '-7 days')
                """)
                stats = cursor.fetchone()

                # 이력 데이터 변환
                history = []
                for h in history_raw:
                    path, method, category, status_code, response_time_ms, success, executed_at, error_message, test_id = h
                    history.append({
                        'id': test_id,
                        'path': path,
                        'method': method,
                        'category': category,
                        'status_code': status_code if status_code else 'Error',
                        'response_time_ms': response_time_ms if response_time_ms else 0,
                        'success': bool(success),
                        'executed_at': executed_at,
                        'error_message': error_message
                    })

                return render_template('api_test_history.html',
                                     history=history,
                                     total=stats[0] if stats else 0,
                                     success_count=stats[1] if stats else 0,
                                     avg_response_time=round(stats[2]) if stats and stats[2] else 0)
        except Exception as e:
            app.logger.error(f"API 테스트 이력 조회 오류: {e}")
            return render_template('api_test_history.html',
                                 history=[],
                                 total=0,
                                 success_count=0,
                                 avg_response_time=0)

    @app.route('/test-api-tracking')
    def test_api_tracking():
        """API 테스트 결과 저장 검증 페이지"""
        return render_template('test_api_tracking.html')

    # [2025-12-30] Integrity 관련 라우트들은 blueprints/integrity_routes.py로 이동됨
    # /integrity, /verify_integrity, /api/verify_integrity,
    # /download_verification_report, /download_court_certificate

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

    # [2025-12-30] Evidence 라우트들은 blueprints/evidence_routes.py로 이동됨
    # /evidence, /evidence/<folder_name>, /evidence_management, /api/delete_files,
    # /evidence_file/<file_id>, /additional_evidence, /add_evidence,
    # /edit_evidence/<file_id>, /delete_evidence/<file_id>

    # [2025-12-30] 아래 라우트들은 main_routes.py Blueprint로 이동됨
    # - /search (검색 페이지)
    # - /settings (설정 페이지)
    # - /download/<path:filename> (파일 다운로드)

    # [2025-12-30] Evidence 관리 관련 라우트들은 blueprints/evidence_routes.py로 이동됨
    # /evidence_management, /api/delete_files, /evidence_file/<file_id>

    # [2025-12-30] additional_evidence 관련 라우트들은 blueprints/evidence_routes.py로 이동됨
    # /additional_evidence, /add_evidence, /api/evidence_categories,
    # /edit_evidence/<file_id>, /delete_evidence/<file_id>,
    # /download_evidence_index, /export_additional_evidence

    # [2025-12-30] Timeline 관련 라우트들은 blueprints/timeline_routes.py로 이동됨
    # /timeline, /integrated_timeline, /generate_timeline_package, /download_timeline_excel

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

    @app.context_processor
    def inject_template_vars():
        """템플릿 전역 변수 주입"""
        return {
            'app_name': '이메일 증거 처리 시스템',
            'app_version': '2.0.0'
        }

    # [2025-12-30] 중복 라우트 제거: integrated_timeline, generate_timeline_package, download_timeline_excel

    # ========================================================================
    # [2025-12-30] Logs 관련 라우트들은 blueprints/logs_routes.py로 이동됨
    # ========================================================================
    # /logs, /api/logs, /api/logs/download, /api/logs/clear,
    # /api/logs/files, /api/logs/file/<filename>, /api/logs/file/<filename>/download

