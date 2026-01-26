"""
Main routes blueprint
메인 페이지, 업로드, 검색, 설정 등 핵심 기능
"""

import os
import shutil
import tempfile
import threading
import uuid
from datetime import datetime
from pathlib import Path

from flask import (Blueprint, current_app, flash, jsonify, redirect,
                   render_template, request, send_file, url_for)
from werkzeug.utils import secure_filename

# Blueprint 정의
main_bp = Blueprint('main', __name__)

# 메모리 저장소 (전역)
uploaded_files = {}
processed_emails = {}
email_processors = {}


def allowed_file(filename):
    """허용된 파일 확장자 확인"""
    ALLOWED_EXTENSIONS = {'mbox', 'eml', 'msg'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@main_bp.route('/', endpoint='index')
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
        current_app.logger.error(f"메인 페이지 로드 실패: {str(e)}")
        stats = {'total_files': 0, 'processed_files': 0,
                 'total_emails': 0, 'evidence_count': 0, 'has_data': False}
        features_status = {'timeline_available': False, 'evidence_available': False,
                           'integrity_available': False, 'upload_available': True}
        return render_template('index.html',
                               stats=stats,
                               features_status=features_status)


@main_bp.route('/search')
def search_page():
    """검색 페이지 (템플릿 미구현)"""
    from flask import jsonify
    return jsonify({
        'status': 'not_implemented',
        'message': '검색 기능은 추후 구현 예정입니다.',
        'available_endpoints': ['/', '/settings', '/download/<path>']
    }), 501


@main_bp.route('/settings')
def settings_page():
    """설정 페이지"""
    try:
        # 현재 설정 로드
        config_path = current_app.config.get(
            'EMAIL_PROCESSOR_CONFIG', 'config.json')

        import json
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        return render_template('settings.html',
                               config=config,
                               page_title='시스템 설정')

    except Exception as e:
        flash(f'설정 로드 오류: {str(e)}', 'error')
        return redirect(url_for('main.index'))


@main_bp.route('/download/<path:filename>')
def download_file(filename):
    """파일 다운로드"""
    try:
        # 보안을 위해 경로 검증
        safe_path = Path(filename).resolve()
        base_path = Path('processed_emails').resolve()

        if not str(safe_path).startswith(str(base_path)):
            flash('허용되지 않은 경로입니다.', 'error')
            return redirect(url_for('main.index'))

        if not safe_path.exists():
            flash('파일을 찾을 수 없습니다.', 'error')
            return redirect(url_for('main.index'))

        return send_file(safe_path, as_attachment=True)

    except Exception as e:
        current_app.logger.error(f"파일 다운로드 실패: {str(e)}")
        flash('파일 다운로드 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('main.index'))


# 템플릿 컨텍스트 프로세서
@main_bp.context_processor
def inject_template_vars():
    """템플릿 전역 변수 주입"""
    return {
        'app_name': current_app.config.get('APP_NAME', 'Email Evidence System'),
        'app_version': current_app.config.get('APP_VERSION', '2.0'),
        'current_year': datetime.now().year
    }
