import secrets
from pathlib import Path

from flask import (Blueprint, abort, current_app, render_template, request,
                   send_file, session)

from src.core import evidence_store

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
