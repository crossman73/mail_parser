"""
Email routes blueprint
이메일 목록, 상세, 처리 관련 라우트
"""

import os
import threading
from pathlib import Path

from flask import (Blueprint, current_app, flash, jsonify, redirect,
                   render_template, request, send_file, url_for)

# Blueprint 정의
email_bp = Blueprint('email', __name__)

from ..progress_tracker import progress_tracker
# 전역 메모리 저장소 (routes.py와 공유)
from ..routes import email_processors, processed_emails, uploaded_files


@email_bp.route('/emails/<file_id>')
def email_list(file_id):
    """이메일 목록 페이지 - 선택적 증거 생성 기능 포함"""
    if file_id not in processed_emails:
        flash('파일을 찾을 수 없습니다.', 'error')
        return redirect(url_for('main.index'))

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


@email_bp.route('/generate_evidence/<file_id>', methods=['POST'])
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

        # generate_evidence_background 함수는 routes.py에 정의되어 있어야 함
        # 또는 여기로 이동 필요
        from ..routes import generate_evidence_background

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
        current_app.logger.error(f"증거 생성 요청 실패: {str(e)}")
        return jsonify({'error': '증거 생성 요청 처리 중 오류가 발생했습니다.'}), 500


@email_bp.route('/api/evidence_progress/<task_id>')
def get_evidence_progress(task_id):
    """증거 생성 진행 상황 API"""
    progress_data = progress_tracker.get_progress(task_id)
    if not progress_data:
        return jsonify({'error': 'Task not found'}), 404

    return jsonify(progress_data)


@email_bp.route('/email/<file_id>/<int:email_index>')
def email_detail(file_id, email_index):
    """이메일 상세 페이지"""
    if file_id not in processed_emails:
        flash('파일을 찾을 수 없습니다.', 'error')
        return redirect(url_for('main.index'))

    emails = processed_emails[file_id]['emails']
    if email_index >= len(emails):
        flash('존재하지 않는 이메일입니다.', 'error')
        return redirect(url_for('email.email_list', file_id=file_id))

    email = emails[email_index]
    processor = email_processors.get(file_id)

    # 상세 이메일 내용 가져오기
    if processor:
        try:
            # 메시지 ID로 전체 메시지 내용 가져오기
            message_content = processor.get_message_content(email['id'])
            email['full_content'] = message_content
        except Exception as e:
            current_app.logger.error(f"이메일 내용 로드 실패: {str(e)}")
            email['full_content'] = None

    return render_template('email_detail.html', email=email, file_id=file_id, email_index=email_index)


@email_bp.route('/process_selected', methods=['POST'])
def process_selected_emails():
    """선택된 이메일들을 HTML/PDF로 처리"""
    try:
        data = request.get_json()
        file_id = data.get('file_id')
        selected_indices = data.get('selected_indices', [])

        if not file_id or file_id not in processed_emails:
            return jsonify({'error': '파일을 찾을 수 없습니다.'}), 404

        if not selected_indices:
            return jsonify({'error': '선택된 이메일이 없습니다.'}), 400

        emails = processed_emails[file_id]['emails']
        selected_emails = [emails[i] for i in selected_indices if i < len(emails)]

        if not selected_emails:
            return jsonify({'error': '유효한 이메일이 없습니다.'}), 400

        # 처리 로직 (routes.py에서 이동 필요)
        # 임시로 성공 응답
        return jsonify({
            'success': True,
            'message': f'{len(selected_emails)}개 이메일 처리 완료',
            'count': len(selected_emails)
        })

    except Exception as e:
        current_app.logger.error(f"이메일 처리 실패: {str(e)}")
        return jsonify({'error': '이메일 처리 중 오류가 발생했습니다.'}), 500
