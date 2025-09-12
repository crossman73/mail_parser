"""
Main Flask application factory
메인 Flask 애플리케이션
"""

import os
from pathlib import Path

from flask import Flask


def create_app(config_path: str = None):
    """Flask 애플리케이션 생성"""

    app = Flask(__name__,
                template_folder='../../templates',
                static_folder='../../static')

    # 설정
    app.config['SECRET_KEY'] = os.environ.get(
        'SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 1GB

    if config_path:
        app.config['EMAIL_PROCESSOR_CONFIG'] = config_path
    else:
        app.config['EMAIL_PROCESSOR_CONFIG'] = 'config.json'

    # 업로드 폴더 설정
    upload_folder = Path('uploads')
    upload_folder.mkdir(exist_ok=True)
    app.config['UPLOAD_FOLDER'] = str(upload_folder)

    # 라우트 등록
    from .routes import register_routes
    register_routes(app)

    # API 라우트 등록
    from .api import register_api_routes
    register_api_routes(app)

    # Admin blueprint: register if available, log errors to file for debugging
    try:
        from .admin_routes import admin as admin_bp

        # avoid double-registration: check if any existing rule uses the same URL prefix
        existing_rules = {r.rule for r in app.url_map.iter_rules()}
        admin_prefix_conflict = any(r.startswith('/admin')
                                    for r in existing_rules)
        if admin_prefix_conflict:
            # skip registering blueprint to avoid conflicts with existing routes
            with open('blueprint_register_skip.txt', 'w', encoding='utf-8') as f:
                f.write(
                    'skipped admin blueprint registration due to existing /admin routes\n')
            app.logger.info(
                'Skipping admin blueprint registration because /admin routes already exist')
        else:
            app.register_blueprint(admin_bp)
    except Exception:
        # write debug info to file so test scripts can inspect
        import traceback
        with open('blueprint_register_error.txt', 'w', encoding='utf-8') as f:
            f.write('failed to register admin blueprint\n')
            f.write(traceback.format_exc())
        # continue without raising to allow app to start
    else:
        # If we skipped registering the admin blueprint due to existing admin endpoints,
        # ensure at least the reload endpoint is exposed so dev tooling/tests can call it.
        try:
            # if admin_reload is defined in the module, register a direct route
            from . import admin_routes as _admin_mod
            if hasattr(_admin_mod, 'admin_reload') and 'admin.admin_reload' not in {r.endpoint for r in app.url_map.iter_rules()}:
                # register POST /admin/reload to the function directly
                app.add_url_rule('/admin/reload', endpoint='admin.admin_reload',
                                 view_func=_admin_mod.admin_reload, methods=['POST'])
        except Exception:
            # don't fail app startup for this convenience wiring
            app.logger.exception('failed to register fallback admin.reload')

    # 앱 시작 시 비정상 종료된 작업들 정리
    with app.app_context():
        from .progress_tracker import progress_tracker
        progress_tracker.reset_stuck_tasks(max_stuck_minutes=1)
        progress_tracker.cleanup_error_tasks()

    # 에러 핸들러
    @app.errorhandler(404)
    def not_found_error(error):
        return {'error': 'Not found'}, 404

    @app.errorhandler(500)
    def internal_error(error):
        return {'error': 'Internal server error'}, 500

    @app.errorhandler(413)
    def too_large(error):
        return {'error': 'File too large'}, 413

    # 헬스체크 엔드포인트 추가
    @app.route('/health')
    def health_check():
        """시스템 상태 확인"""
        from datetime import datetime

        import psutil

        try:
            # 메모리 사용률 확인
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            health_status = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'version': '2.0.0',
                'system': {
                    'memory_usage_percent': memory.percent,
                    'disk_usage_percent': disk.percent,
                    'available_memory_mb': memory.available / 1024 / 1024
                },
                'services': {
                    'flask_app': 'running',
                    'file_system': 'accessible' if os.path.exists('config.json') else 'error'
                }
            }

            # 시스템 상태가 정상인지 확인
            if memory.percent > 90 or disk.percent > 95:
                health_status['status'] = 'warning'
                health_status['warnings'] = []

                if memory.percent > 90:
                    health_status['warnings'].append('High memory usage')
                if disk.percent > 95:
                    health_status['warnings'].append('Low disk space')

            status_code = 200 if health_status['status'] in [
                'healthy', 'warning'] else 503
            return health_status, status_code

        except Exception as e:
            return {
                'status': 'unhealthy',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }, 503

    # Compatibility: provide an `index` endpoint for templates/tests that rely on it.
    # Only add if an 'index' endpoint does not already exist to avoid overwriting.
    if 'index' not in app.view_functions:
        def _compat_index():
            from flask import redirect, url_for
            try:
                return redirect(url_for('legacy_index'))
            except Exception:
                return redirect('/admin')

        app.add_url_rule('/', endpoint='index', view_func=_compat_index)

    # start file watcher for hot reload if enabled
    try:
        _maybe_start_watcher(app)
    except Exception:
        pass

    return app


def _maybe_start_watcher(app):
    try:
        if app.config.get('ENABLE_FILE_WATCHER') and app.config.get('ENABLE_DEV_RELOAD'):
            modules = app.config.get('DEV_RELOAD_MODULES', [])
            paths = app.config.get('WATCH_PATHS')
            try:
                from src.core.hot_reload_watcher import start_watcher
                start_watcher(app, modules, paths)
            except Exception:
                app.logger.exception('failed to start hot reload watcher')
    except Exception:
        # ignore in create_app path
        pass


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
