import json
import secrets
from pathlib import Path

from flask import (Blueprint, abort, current_app, render_template, request,
                   send_file, session)

from src.core import evidence_store

# [2025-12-30] Admin Blueprint
# url_prefix='': 주요 경로 ('/admin', '/admin/settings' 등)
# Phase 2에서 url_prefix='/admin'으로 변경 예정
# Blueprint name must match template expectations (templates call url_for('admin.evidence_detail'))
admin = Blueprint('admin', __name__, url_prefix='')


@admin.route('/admin')
def admin_index():
    # paging support
    try:
        page = int(request.args.get('page', '1'))
        if page < 1:
            page = 1
    except Exception:
        page = 1
    per_page = 20
    offset = (page - 1) * per_page

    try:
        conn = evidence_store._get_conn()
        cur = conn.cursor()
        cur.execute('SELECT COUNT(1) FROM evidence')
        total = cur.fetchone()[0]

        cur.execute('SELECT id, evidence_number, subject, generated_at, integrity_hash FROM evidence ORDER BY id DESC LIMIT ? OFFSET ?', (per_page, offset))
        rows = cur.fetchall()
        evidences = [dict(r) for r in rows]
    except Exception as e:
        current_app.logger.exception(f'admin_index db error: {e}')
        evidences = []
        total = 0

    total_pages = (total + per_page - 1) // per_page
    # Ensure CSRF token for admin actions
    if 'admin_csrf' not in session:
        session['admin_csrf'] = secrets.token_urlsafe(24)
    return render_template('admin_dashboard.html', evidences=evidences, page=page, total_pages=total_pages, admin_csrf=session['admin_csrf'])


@admin.route('/admin/evidence/<int:evidence_id>')
def evidence_detail(evidence_id: int):
    try:
        ev = evidence_store.get_evidence(evidence_id)
        if not ev:
            abort(404)
        chain = evidence_store.list_chain_entries(evidence_id)
    except Exception as e:
        current_app.logger.exception(f'evidence_detail error: {e}')
        abort(500)
    return render_template('admin_evidence_detail.html', evidence=ev, chain=chain)


# NOTE: avoid using a dotted endpoint name on the blueprint level
# (Flask raises ValueError if endpoint contains a dot). The primary
# `evidence_detail` view above is registered on this blueprint and will
# already expose the endpoint `admin.evidence_detail` when the blueprint
# is registered as `admin`. If compatibility wiring is needed at the
# application level it should be done in the app factory instead.


@admin.route('/admin/jobs')
def admin_jobs():
    try:
        from src.core import job_store
        jobs = job_store.list_jobs(200)
    except Exception as e:
        current_app.logger.exception(f'admin_jobs db error: {e}')
        jobs = []
    return render_template('admin_jobs.html', jobs=jobs)


@admin.route('/api/admin/job/<job_id>', methods=['DELETE'])
def delete_job(job_id: str):
    """Job 삭제 API"""
    from flask import jsonify
    try:
        from src.core import job_store
        success = job_store.delete_job(job_id)
        if success:
            return jsonify({'status': 'ok', 'message': 'Job deleted'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Job not found'}), 404
    except Exception as e:
        current_app.logger.exception(f'delete_job error: {e}')
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin.route('/admin/settings')
def admin_settings():
    """시스템 설정 관리 페이지"""
    try:
        from src.core.settings_manager import get_settings_manager
        settings_manager = get_settings_manager()

        # DB 연결 상태 확인
        db_available = settings_manager.is_db_available()

        # 전체 설정 조회 (카테고리별)
        categories = ['general', 'database',
                      'email', 'security', 'performance', 'route']
        settings_by_category = {}

        for category in categories:
            try:
                from src.database.email_db import db
                settings = db.get_settings_metadata(category=category)
                settings_by_category[category] = settings
            except Exception as e:
                current_app.logger.warning(f'설정 조회 실패 ({category}): {e}')
                settings_by_category[category] = []

        # CSRF 토큰 생성
        if 'admin_csrf' not in session:
            session['admin_csrf'] = secrets.token_urlsafe(24)

        return render_template('admin_settings.html',
                               settings_by_category=settings_by_category,
                               categories=categories,
                               db_available=db_available,
                               admin_csrf=session['admin_csrf'])
    except Exception as e:
        current_app.logger.exception(f'admin_settings error: {e}')
        return render_template('admin_settings.html',
                               settings_by_category={},
                               categories=[],
                               db_available=False,
                               error=str(e))


@admin.route('/admin/logs')
def admin_logs():
    try:
        from src.core import db_manager
        page = int(request.args.get('page', '1'))
        if page < 1:
            page = 1
        per_page = 50
        logs = db_manager.list_logs(per_page)
    except Exception as e:
        current_app.logger.exception(f'admin_logs db error: {e}')
        logs = []
    return render_template('admin_logs.html', logs=logs)


@admin.route('/api/admin/logs')
def api_admin_logs():
    try:
        from src.core import db_manager
        limit = int(request.args.get('limit', '100'))
        if limit < 1:
            limit = 100
        logs = db_manager.list_logs(limit)
        return {'logs': logs}
    except Exception as e:
        current_app.logger.exception(f'api_admin_logs error: {e}')
        return {'logs': []}


@admin.route('/api/admin/settings/init', methods=['POST'])
def api_init_settings():
    """기본 설정 초기화"""
    from flask import jsonify
    try:
        from src.database.email_db import db

        # 기본 설정 정의
        default_settings = [
            # General 설정
            {'key': 'app_name', 'value': 'Email Evidence System',
                'type': 'string', 'category': 'general', 'description': '애플리케이션 이름'},
            {'key': 'debug_mode', 'value': False, 'type': 'bool',
                'category': 'general', 'description': '디버그 모드 활성화'},
            {'key': 'max_upload_size', 'value': 100, 'type': 'int',
                'category': 'general', 'description': '최대 업로드 파일 크기 (MB)'},

            # Database 설정
            {'key': 'db_connection_pool', 'value': 10, 'type': 'int',
                'category': 'database', 'description': 'DB 연결 풀 크기'},
            {'key': 'db_timeout', 'value': 30, 'type': 'int',
                'category': 'database', 'description': 'DB 연결 타임아웃 (초)'},
            {'key': 'db_backup_enabled', 'value': True, 'type': 'bool',
                'category': 'database', 'description': '자동 백업 활성화'},

            # Email 설정
            {'key': 'smtp_server', 'value': '', 'type': 'string',
                'category': 'email', 'description': 'SMTP 서버 주소', 'is_sensitive': True},
            {'key': 'smtp_port', 'value': 587, 'type': 'int',
                'category': 'email', 'description': 'SMTP 포트'},
            {'key': 'email_enabled', 'value': False, 'type': 'bool',
                'category': 'email', 'description': '이메일 알림 활성화'},

            # Security 설정
            {'key': 'session_timeout', 'value': 3600, 'type': 'int',
                'category': 'security', 'description': '세션 타임아웃 (초)'},
            {'key': 'password_min_length', 'value': 8, 'type': 'int',
                'category': 'security', 'description': '최소 비밀번호 길이'},
            {'key': 'enable_2fa', 'value': False, 'type': 'bool',
                'category': 'security', 'description': '2단계 인증 활성화'},

            # Performance 설정
            {'key': 'log_retention_days', 'value': 30, 'type': 'int',
                'category': 'performance', 'description': '로그 보관 기간 (일)'},
            {'key': 'cache_enabled', 'value': True, 'type': 'bool',
                'category': 'performance', 'description': '캐시 활성화'},
            {'key': 'max_concurrent_tasks', 'value': 5, 'type': 'int',
                'category': 'performance', 'description': '최대 동시 처리 작업 수'},

            # Route 설정 (페이지별 라우트 경로)
            {'key': 'route_home', 'value': '/', 'type': 'string',
                'category': 'route', 'description': '홈페이지 라우트 경로'},
            {'key': 'route_upload', 'value': '/upload', 'type': 'string',
                'category': 'route', 'description': '파일 업로드 페이지 경로'},
            {'key': 'route_admin', 'value': '/admin', 'type': 'string',
                'category': 'route', 'description': '관리자 대시보드 경로'},
            {'key': 'route_admin_settings', 'value': '/admin/settings', 'type': 'string',
                'category': 'route', 'description': '시스템 설정 페이지 경로'},
            {'key': 'route_admin_logs', 'value': '/admin/logs', 'type': 'string',
                'category': 'route', 'description': '로그 조회 페이지 경로'},
            {'key': 'route_admin_jobs', 'value': '/admin/jobs', 'type': 'string',
                'category': 'route', 'description': '작업 관리 페이지 경로'},
            {'key': 'route_api_prefix', 'value': '/api', 'type': 'string',
                'category': 'route', 'description': 'API 엔드포인트 접두사'},
            {'key': 'route_health', 'value': '/health', 'type': 'string',
                'category': 'route', 'description': '헬스체크 엔드포인트 경로'},
            {'key': 'route_system_status', 'value': '/system/status', 'type': 'string',
                'category': 'route', 'description': '시스템 상태 페이지 경로'},
        ]

        added = 0
        for setting in default_settings:
            try:
                is_sensitive = setting.get('is_sensitive', False)
                db.set_setting(
                    key=setting['key'],
                    value=setting['value'],
                    description=setting['description'],
                    category=setting['category'],
                    is_sensitive=is_sensitive,
                    changed_by='system',
                    reason='초기 설정'
                )
                added += 1
            except Exception as e:
                current_app.logger.warning(f"설정 추가 실패 ({setting['key']}): {e}")

        return jsonify({
            'success': True,
            'message': f'{added}개의 기본 설정이 추가되었습니다.'
        })
    except Exception as e:
        current_app.logger.exception(f'api_init_settings error: {e}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin.route('/api/admin/settings', methods=['GET', 'POST'])
def api_settings():
    """설정 조회/추가 API"""
    from flask import jsonify

    if request.method == 'GET':
        try:
            from src.database.email_db import db
            category = request.args.get('category', None)
            include_sensitive = request.args.get(
                'show_sensitive', 'false').lower() == 'true'

            settings = db.get_all_settings(
                category=category, include_sensitive=include_sensitive)
            metadata = db.get_settings_metadata(category=category)

            return jsonify({
                'success': True,
                'settings': settings,
                'metadata': metadata
            })
        except Exception as e:
            current_app.logger.exception(f'api_get_settings error: {e}')
            return jsonify({
                'success': False,
                'error': str(e),
                'db_available': False
            }), 500

    elif request.method == 'POST':
        try:
            data = request.get_json() or {}
            key = data.get('key')
            value = data.get('value')
            description = data.get('description', '')
            category = data.get('category', 'general')
            value_type = data.get('type', 'string')
            is_sensitive = data.get('is_sensitive', False)
            changed_by = data.get('changed_by', 'admin')

            if not key or value is None:
                return jsonify({
                    'success': False,
                    'error': '키와 값은 필수입니다.'
                }), 400

            # 타입 변환
            if value_type == 'int':
                value = int(value)
            elif value_type == 'float':
                value = float(value)
            elif value_type == 'bool':
                value = value.lower() in ('true', '1', 'yes') if isinstance(
                    value, str) else bool(value)
            elif value_type == 'json':
                value = json.loads(value) if isinstance(value, str) else value

            from src.database.email_db import db
            db.set_setting(
                key=key,
                value=value,
                description=description,
                category=category,
                is_sensitive=is_sensitive,
                changed_by=changed_by,
                reason='새 설정 추가'
            )

            return jsonify({
                'success': True,
                'message': f'설정 "{key}"이(가) 추가되었습니다.'
            })
        except Exception as e:
            current_app.logger.exception(f'api_add_setting error: {e}')
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500


@admin.route('/api/admin/settings/<key>', methods=['PUT'])
def api_update_setting(key: str):
    """설정 수정 API"""
    from flask import jsonify
    try:
        data = request.get_json() or {}
        value = data.get('value')
        description = data.get('description')
        category = data.get('category', 'general')
        is_sensitive = data.get('is_sensitive', False)
        changed_by = data.get('changed_by', 'admin')
        reason = data.get('reason', '관리자 수정')

        from src.database.email_db import db
        db.set_setting(
            key=key,
            value=value,
            description=description,
            category=category,
            is_sensitive=is_sensitive,
            changed_by=changed_by,
            reason=reason
        )

        return jsonify({
            'success': True,
            'message': f'설정 "{key}"이(가) 업데이트되었습니다.'
        })
    except Exception as e:
        current_app.logger.exception(f'api_update_setting error: {e}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin.route('/api/admin/settings/<key>', methods=['DELETE'])
def api_delete_setting(key: str):
    """설정 삭제 API"""
    from flask import jsonify
    try:
        data = request.get_json() or {}
        changed_by = data.get('changed_by', 'admin')
        reason = data.get('reason', '관리자 삭제')

        from src.database.email_db import db
        db.delete_setting(key=key, changed_by=changed_by, reason=reason)

        return jsonify({
            'success': True,
            'message': f'설정 "{key}"이(가) 삭제되었습니다.'
        })
    except Exception as e:
        current_app.logger.exception(f'api_delete_setting error: {e}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin.route('/api/admin/settings/history', methods=['GET'])
def api_get_all_history():
    """전체 설정 변경 이력 조회 API"""
    from flask import jsonify
    try:
        key = request.args.get('key', None)
        limit = int(request.args.get('limit', '100'))
        from src.database.email_db import db
        history = db.get_settings_history(key=key, limit=limit)

        return jsonify({
            'success': True,
            'history': history,
            'count': len(history)
        })
    except Exception as e:
        current_app.logger.exception(f'api_get_all_history error: {e}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin.route('/api/admin/settings/<key>/history', methods=['GET'])
def api_get_setting_history(key: str):
    """특정 설정 변경 이력 조회 API"""
    from flask import jsonify
    try:
        limit = int(request.args.get('limit', '50'))
        from src.database.email_db import db
        history = db.get_settings_history(key=key, limit=limit)

        return jsonify({
            'success': True,
            'history': history
        })
    except Exception as e:
        current_app.logger.exception(f'api_get_setting_history error: {e}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin.route('/admin/reload', methods=['POST'])
def admin_reload():
    """Dev-only endpoint to reload selected modules at runtime.

    Enable by setting app.config['ENABLE_DEV_RELOAD'] = True and optionally
    app.config['DEV_RELOAD_MODULES'] = ['src.core.evidence_store', ...]
    """
    enabled = current_app.config.get('ENABLE_DEV_RELOAD', False)
    if not enabled:
        current_app.logger.warning(
            'admin_reload blocked: ENABLE_DEV_RELOAD is False')
        return {'error': 'disabled', 'reason': 'ENABLE_DEV_RELOAD is False'}, 403

    # Allow only local requests unless explicitly permitted
    allow_remote = current_app.config.get('ALLOW_REMOTE_RELOAD', False)
    remote = request.headers.get('X-Forwarded-For', request.remote_addr)
    if not allow_remote:
        if remote is None:
            current_app.logger.warning(
                'admin_reload blocked: remote address missing')
            return {'error': 'forbidden', 'reason': 'remote address missing'}, 403
        if isinstance(remote, str):
            remote_ip = remote.split(',')[0].strip()
        else:
            remote_ip = str(remote)
        # Accept local addresses first
        if remote_ip not in ('127.0.0.1', '::1', 'localhost'):
            # check whitelist
            ip_whitelist = current_app.config.get('DEV_RELOAD_IP_WHITELIST')
            if ip_whitelist:
                # allow if remote_ip in whitelist
                if remote_ip not in ip_whitelist:
                    current_app.logger.warning(
                        f'admin_reload blocked: {remote_ip} not in DEV_RELOAD_IP_WHITELIST')
                    return {'error': 'forbidden', 'reason': f'{remote_ip} not in DEV_RELOAD_IP_WHITELIST'}, 403
            else:
                current_app.logger.warning(
                    f'admin_reload blocked: {remote_ip} is not local and no whitelist configured')
                return {'error': 'forbidden', 'reason': f'{remote_ip} not allowed'}, 403

    # Token check: header X-DEV-RELOAD-TOKEN or json/form 'token'
    # Token precedence: 1) DB setting 2) app config
    expected = None
    try:
        from src.core import db_manager
        expected = db_manager.get_setting('DEV_RELOAD_TOKEN')
    except Exception:
        expected = None
    if not expected:
        expected = current_app.config.get('DEV_RELOAD_TOKEN')
    if expected:
        token = None
        if request.is_json:
            token = (request.get_json(silent=True) or {}).get('token')
        if not token:
            token = request.form.get('token')
        if not token:
            token = request.headers.get('X-DEV-RELOAD-TOKEN')
        if token != expected:
            current_app.logger.warning('admin_reload blocked: token mismatch')
            return {'error': 'forbidden', 'reason': 'token mismatch'}, 403

    # CSRF check for form-based admin actions
    form_csrf = request.form.get('admin_csrf') or ((request.get_json(
        silent=True) or {}).get('admin_csrf') if request.is_json else None)
    if form_csrf and session.get('admin_csrf') != form_csrf:
        current_app.logger.warning('admin_reload blocked: csrf mismatch')
        return {'error': 'forbidden', 'reason': 'csrf mismatch'}, 403

    # Accept JSON body {"modules": ["mod.name", ...]} or form 'modules' CSV
    modules = None
    if request.is_json:
        body = request.get_json(silent=True) or {}
        modules = body.get('modules')

    if not modules:
        modules_csv = request.form.get('modules')
        if modules_csv:
            modules = [m.strip() for m in modules_csv.split(',') if m.strip()]

    if not modules:
        modules = current_app.config.get('DEV_RELOAD_MODULES', [
            'src.core.evidence_store',
            'src.core.db_manager',
            'src.core.hot_reload',
            'src.web.admin_routes',
            'src.web.app_factory',
            'src.core.log_store',
            'src.core.logging_utils',
        ])

    try:
        from src.core import hot_reload
        results = hot_reload.reload_modules(modules)
    except Exception as e:
        current_app.logger.exception(f'admin_reload error: {e}')
        return {'results': [{'module': 'internal', 'status': 'error', 'error': str(e)}]}, 500

    # log the reload attempt
    try:
        from src.core import db_manager
        db_manager.write_log('INFO', 'dev_reload executed', extra={
                             'modules': modules, 'results': results})
    except Exception:
        current_app.logger.exception('failed to write reload log')

    return {'results': results}


@admin.route('/api/evidence/<int:evidence_id>/download/<kind>')
def evidence_download(evidence_id: int, kind: str):
    # kind: 'html' | 'pdf'
    ev = evidence_store.get_evidence(evidence_id)
    if not ev:
        abort(404)
    if kind == 'html':
        path = ev.get('html_file')
    elif kind == 'pdf':
        path = ev.get('pdf_file')
    else:
        abort(400)

    if not path:
        abort(404)
    p = Path(path)
    if not p.exists():
        abort(404)
    return send_file(str(p), as_attachment=True, download_name=p.name)


@admin.route('/api/evidence/attachment/<int:entry_id>/download')
def attachment_download(entry_id: int):
    conn = evidence_store._get_conn()
    cur = conn.cursor()
    cur.execute('SELECT file_path FROM chain_entry WHERE id=?', (entry_id,))
    row = cur.fetchone()
    if not row:
        abort(404)
    p = Path(row['file_path'])
    if not p.exists():
        abort(404)
    return send_file(str(p), as_attachment=True, download_name=p.name)


@admin.route('/api/admin/task/<task_id>', methods=['DELETE'])
def remove_task(task_id: str):
    """개별 작업 제거 API 엔드포인트"""
    try:
        # CSRF 토큰 검증 (선택적)
        # csrf_token = request.headers.get('X-CSRF-Token')
        # if csrf_token != session.get('admin_csrf'):
        #     return {'error': 'CSRF token validation failed'}, 403

        from src.web.progress_tracker import ProgressTracker
        tracker = ProgressTracker()
        tracker.remove_task(task_id)

        current_app.logger.info(f'작업 제거됨: {task_id}')
        return {'status': 'success', 'message': f'작업 {task_id}이(가) 제거되었습니다.', 'task_id': task_id}, 200
    except Exception as e:
        current_app.logger.exception(f'작업 제거 오류: {e}')
        return {'error': str(e)}, 500
