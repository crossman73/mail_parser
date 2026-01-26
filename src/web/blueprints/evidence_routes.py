"""
Evidence routes blueprint
증거 관리, 추가 증거, 증거 목록 관련 라우트
"""

import tempfile
from datetime import datetime
from pathlib import Path

from flask import (Blueprint, current_app, flash, jsonify, redirect,
                   render_template, request, send_file, url_for)
from werkzeug.utils import secure_filename

from ...evidence.additional_evidence_manager import AdditionalEvidenceManager

# Blueprint 정의
evidence_bp = Blueprint('evidence', __name__)

# 전역 서비스 (routes.py에서 초기화)
evidence_service = None
USE_DATABASE = False
email_db = None


def init_evidence_services(ev_service, use_db, db):
    """Evidence 서비스 초기화"""
    global evidence_service, USE_DATABASE, email_db
    evidence_service = ev_service
    USE_DATABASE = use_db
    email_db = db


@evidence_bp.route('/evidence')
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

        evidence_list_data = evidence_service.get_evidence_list()
        stats = evidence_service.get_evidence_statistics()

        # 증거가 없는 경우
        if not evidence_list_data or len(evidence_list_data) == 0:
            flash('증거 목록이 비어있습니다.', 'info')
            return render_template('evidence_list.html',
                                   evidence_list=[],
                                   stats=stats,
                                   no_data=True,
                                   page_title='증거 목록')

        return render_template('evidence_list.html',
                               evidence_list=evidence_list_data,
                               stats=stats,
                               no_data=False,
                               page_title='증거 목록')

    except Exception as e:
        flash(f'증거 목록 로드 오류: {str(e)}', 'error')
        return redirect(url_for('main.index'))


@evidence_bp.route('/evidence/<folder_name>')
def evidence_detail(folder_name):
    """증거 상세 페이지"""
    try:
        result = evidence_service.get_evidence_details(folder_name)
        if not result['success']:
            flash(result['message'], 'error')
            return redirect(url_for('evidence.evidence_list'))

        return render_template('evidence_detail.html',
                               evidence=result['details'],
                               folder_name=folder_name,
                               page_title=f'증거 상세 - {folder_name}')

    except Exception as e:
        flash(f'증거 상세 로드 오류: {str(e)}', 'error')
        return redirect(url_for('evidence.evidence_list'))


@evidence_bp.route('/evidence_management')
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
                current_app.logger.warning(
                    f"⚠️ DB 파일 조회 실패 (폴백): {db_err}")
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
        return redirect(url_for('main.index'))


@evidence_bp.route('/api/delete_files', methods=['POST'])
def delete_files():
    """파일 삭제 API (소프트 삭제 + 물리적 삭제)"""
    try:
        data = request.json
        file_ids = data.get('file_ids', []) if data else []
        confirm = data.get('confirm', False) if data else False
        reason = data.get('reason', '사용자 요청') if data else '사용자 요청'

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

        from ...utils.file_deleter import delete_physical_files

        for file_id in file_ids:
            try:
                # 1. 소프트 삭제 (DB에 deleted 마킹)
                if USE_DATABASE and email_db:
                    try:
                        soft_delete_result = email_db.soft_delete_file(
                            file_id, reason)
                        if not soft_delete_result:
                            current_app.logger.warning(
                                f"⚠️ DB 소프트 삭제 실패 (무시): {file_id}")
                    except Exception as db_err:
                        current_app.logger.warning(
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


@evidence_bp.route('/evidence_file/<file_id>')
def evidence_file_detail(file_id):
    """증거 파일 상세 뷰어"""
    try:
        # 파일 경로 찾기
        processed_dir = Path('processed_emails')
        file_path = None

        for folder in processed_dir.iterdir():
            if folder.is_dir() and file_id in folder.name:
                for file in folder.iterdir():
                    if file.is_file() and file.suffix in ['.html', '.pdf']:
                        file_path = file
                        break
                if file_path:
                    break

        if not file_path or not file_path.exists():
            flash('요청한 증거 파일을 찾을 수 없습니다.', 'error')
            return redirect(url_for('evidence.evidence_list'))

        # HTML 파일인 경우 내용 읽어서 렌더링
        if file_path.suffix == '.html':
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            return render_template('evidence_viewer.html',
                                   html_content=html_content,
                                   filename=file_path.name)

        # PDF 파일인 경우 다운로드
        elif file_path.suffix == '.pdf':
            return send_file(file_path, as_attachment=True)

    except Exception as e:
        flash(f'파일 뷰어 오류: {str(e)}', 'error')
        return redirect(url_for('evidence.evidence_list'))


@evidence_bp.route('/additional_evidence')
def additional_evidence():
    """추가 증거 관리 페이지"""
    try:
        manager = AdditionalEvidenceManager()
        evidence_list_data = manager.get_evidence_list()
        statistics = manager.get_statistics()

        return render_template('additional_evidence.html',
                               evidence_list=evidence_list_data,
                               statistics=statistics)
    except Exception as e:
        flash(f'추가 증거 관리 오류: {str(e)}', 'error')
        return redirect(url_for('main.index'))


@evidence_bp.route('/add_evidence', methods=['GET', 'POST'])
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
        if file.filename == '' or file.filename is None:
            flash('파일이 선택되지 않았습니다.', 'error')
            return redirect(request.url)

        # 임시 파일 저장
        temp_dir = Path(tempfile.gettempdir()) / "evidence_upload"
        temp_dir.mkdir(exist_ok=True)

        filename = secure_filename(file.filename or 'unnamed')
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
        return redirect(url_for('evidence.additional_evidence'))

    except Exception as e:
        flash(f'추가 증거 등록 실패: {str(e)}', 'error')
        return redirect(request.url)


@evidence_bp.route('/api/evidence_categories')
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


@evidence_bp.route('/edit_evidence/<file_id>', methods=['GET', 'POST'])
def edit_evidence(file_id):
    """추가 증거 편집"""
    manager = AdditionalEvidenceManager()
    evidence = manager.get_evidence_by_id(file_id)

    if not evidence:
        flash('해당 증거를 찾을 수 없습니다.', 'error')
        return redirect(url_for('evidence.additional_evidence'))

    if request.method == 'GET':
        return render_template('edit_evidence.html', evidence=evidence)

    try:
        # 업데이트할 데이터 수집
        updates = {}

        title = request.form.get('title')
        if title:
            updates['title'] = title.strip()

        description = request.form.get('description')
        if description:
            updates['description'] = description.strip()

        evidence_date = request.form.get('evidence_date')
        if evidence_date:
            updates['evidence_date'] = evidence_date

        related_emails = request.form.get('related_emails')
        if related_emails:
            related_emails_stripped = related_emails.strip()
            updates['related_email_ids'] = [email.strip()
                                            for email in related_emails_stripped.split(',') if email.strip()]

        # 메타데이터 업데이트
        if manager.update_evidence_metadata(file_id, updates):
            flash('증거 정보가 성공적으로 업데이트되었습니다.', 'success')
        else:
            flash('증거 정보 업데이트에 실패했습니다.', 'error')

        return redirect(url_for('evidence.additional_evidence'))

    except Exception as e:
        flash(f'증거 편집 실패: {str(e)}', 'error')
        return redirect(url_for('evidence.additional_evidence'))


@evidence_bp.route('/delete_evidence/<file_id>', methods=['POST'])
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

    return redirect(url_for('evidence.additional_evidence'))


@evidence_bp.route('/download_evidence_index')
def download_evidence_index():
    """증거 목록 Excel 다운로드"""
    try:
        manager = AdditionalEvidenceManager()
        excel_path = manager.export_to_excel()

        if excel_path and Path(excel_path).exists():
            return send_file(excel_path,
                             as_attachment=True,
                             download_name='증거목록.xlsx',
                             mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        else:
            flash('Excel 파일 생성에 실패했습니다.', 'error')
            return redirect(url_for('evidence.additional_evidence'))

    except Exception as e:
        flash(f'Excel 다운로드 실패: {str(e)}', 'error')
        return redirect(url_for('evidence.additional_evidence'))


@evidence_bp.route('/export_additional_evidence')
def export_additional_evidence():
    """추가 증거 전체 패키지 다운로드"""
    try:
        manager = AdditionalEvidenceManager()
        zip_path = manager.export_all_evidence()

        if zip_path and Path(zip_path).exists():
            return send_file(zip_path,
                             as_attachment=True,
                             download_name='추가증거_전체.zip',
                             mimetype='application/zip')
        else:
            flash('ZIP 파일 생성에 실패했습니다.', 'error')
            return redirect(url_for('evidence.additional_evidence'))

    except Exception as e:
        flash(f'패키지 다운로드 실패: {str(e)}', 'error')
        return redirect(url_for('evidence.additional_evidence'))
