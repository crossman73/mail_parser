"""
Main Flask application factory
메인 Flask 애플리케이션
"""

import os
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, url_for


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

    # 템플릿 헬퍼 함수 등록
    @app.context_processor
    def inject_template_helpers():
        """템플릿 헬퍼 함수 등록: 엔드포인트 확인 및 안전한 URL 생성"""
        from flask import url_for

        def has_endpoint(name):
            """엔드포인트가 등록되어 있는지 확인"""
            try:
                return name in app.view_functions
            except Exception:
                return False

        def safe_url_for(endpoint, **kwargs):
            """안전한 url_for: 엔드포인트가 없으면 폴백 경로 반환"""
            try:
                return url_for(endpoint, **kwargs)
            except Exception:
                # 엔드포인트가 없으면 루트로 폴백하여 템플릿 크래시 방지
                return '/'

        return {
            'has_endpoint': has_endpoint,
            'safe_url_for': safe_url_for
        }

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

    # 헬스체크 엔드포인트 - JSON과 HTML 모두 지원
    @app.route('/health')
    def health_check():
        """시스템 상태 확인 - Accept 헤더에 따라 JSON 또는 HTML 반환"""
        from datetime import datetime
        from pathlib import Path

        import psutil
        from flask import render_template, request

        try:
            # 메모리 사용률 확인
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            cpu_percent = psutil.cpu_percent(interval=0.5)

            # 서비스 상태 체크
            processed_count = len(list(Path('processed_emails').glob(
                '*'))) if Path('processed_emails').exists() else 0
            upload_count = len(list(Path('uploads').glob('*'))
                               ) if Path('uploads').exists() else 0

            health_status = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'version': '2.0.0',
                'system': {
                    'memory_usage_percent': memory.percent,
                    'disk_usage_percent': disk.percent,
                    'cpu_usage_percent': cpu_percent,
                    'available_memory_mb': memory.available / 1024 / 1024,
                    'total_memory_gb': memory.total / 1024 / 1024 / 1024,
                    'disk_free_gb': disk.free / 1024 / 1024 / 1024
                },
                'services': {
                    'flask_app': 'running',
                    'file_system': 'accessible' if os.path.exists('config/config.json') or os.path.exists('config.json') else 'error',
                    'processed_emails': processed_count,
                    'pending_uploads': upload_count,
                    'database': 'connected' if Path('data/db').exists() else 'not_configured'
                }
            }

            # 시스템 상태가 정상인지 확인
            warnings = []
            if memory.percent > 90:
                warnings.append('High memory usage')
            if disk.percent > 95:
                warnings.append('Low disk space')
            if cpu_percent > 90:
                warnings.append('High CPU usage')

            if warnings:
                health_status['status'] = 'warning'
                health_status['warnings'] = warnings

            status_code = 200 if health_status['status'] in [
                'healthy', 'warning'] else 503

            # HTML 요청인 경우 시각적 페이지 반환
            if 'text/html' in request.headers.get('Accept', ''):
                return render_template('health_check.html', health=health_status), status_code

            return health_status, status_code

        except Exception as e:
            return {
                'status': 'unhealthy',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }, 503

    # 시스템 상태 API - JSON 응답 (비동기 처리용)
    @app.route('/api/system/status')
    def system_status_json():
        """시스템 상태 API (JSON) - 프론트엔드 비동기 로딩용"""
        import os
        from datetime import datetime
        from pathlib import Path

        import psutil

        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # 처리된 이메일 통계 (비동기 처리)
            processed_dir = Path('processed_emails')
            processed_count = len([d for d in processed_dir.iterdir(
            ) if d.is_dir()]) if processed_dir.exists() else 0

            # 최근 처리된 이메일 목록
            recent_emails = []
            if processed_dir.exists():
                recent_dirs = sorted(processed_dir.iterdir(
                ), key=lambda x: x.stat().st_mtime, reverse=True)[:5]
                recent_emails = [d.name for d in recent_dirs if d.is_dir()]

            # 업로드 파일 통계
            upload_dir = Path('uploads')
            upload_count = len(list(upload_dir.glob('*'))
                               ) if upload_dir.exists() else 0

            # 최근 업로드 파일
            recent_uploads = []
            if upload_dir.exists():
                recent_files = sorted(upload_dir.iterdir(
                ), key=lambda x: x.stat().st_mtime, reverse=True)[:5]
                recent_uploads = [{
                    'name': f.name,
                    'size': f'{f.stat().st_size / 1024:.1f} KB',
                    'time': datetime.fromtimestamp(f.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
                } for f in recent_files if f.is_file()]

            # 로그 파일 크기 및 최근 로그
            log_dir = Path('logs')
            log_size = sum(f.stat().st_size for f in log_dir.glob(
                '*') if f.is_file()) if log_dir.exists() else 0

            recent_logs = []
            if log_dir.exists():
                log_files = sorted(log_dir.glob(
                    '*.log'), key=lambda x: x.stat().st_mtime, reverse=True)[:5]
                recent_logs = [f.name for f in log_files]

            # 등록된 라우트 수
            route_count = len(list(app.url_map.iter_rules()))

            # CPU 사용률 (non-blocking)
            cpu_percent = psutil.cpu_percent(interval=0)
            cpu_count = psutil.cpu_count()

            # 프로세스 정보
            process = psutil.Process(os.getpid())
            process_info = {
                'pid': process.pid,
                'memory_mb': f'{process.memory_info().rss / 1024 / 1024:.1f}',
                'threads': process.num_threads(),
                'cpu_percent': process.cpu_percent()
            }

            # 서비스 상태 체크 - 실제 상태 반영
            services_status = []

            services_status.append({
                'name': 'Flask Web Server',
                'status': 'running',
                'info': f'PID: {process.pid}, Threads: {process.num_threads()}',
                'healthy': True
            })

            services_status.append({
                'name': 'Email Parser',
                'status': 'online' if processed_dir.exists() else 'offline',
                'info': f'{processed_count}개 처리됨',
                'healthy': processed_dir.exists()
            })

            services_status.append({
                'name': 'Evidence Generator',
                'status': 'ok' if processed_count > 0 else 'idle',
                'info': f'{processed_count}개 증거 생성',
                'healthy': True
            })

            services_status.append({
                'name': 'Timeline Builder',
                'status': 'online',
                'info': '타임라인 생성 준비',
                'healthy': True
            })

            services_status.append({
                'name': 'File Upload Handler',
                'status': 'online' if upload_dir.exists() else 'offline',
                'info': f'{upload_count}개 파일 대기',
                'healthy': upload_dir.exists()
            })

            services_status.append({
                'name': 'API Endpoints',
                'status': 'running',
                'info': f'{route_count}개 라우트 등록됨',
                'healthy': True
            })

            return {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'version': '2.0.0',
                'status': 'healthy' if memory.percent < 90 and disk.percent < 95 else 'warning',
                'system': {
                    'cpu': {
                        'percent': cpu_percent,
                        'count': cpu_count,
                        'status': 'normal' if cpu_percent < 80 else 'high'
                    },
                    'memory': {
                        'total_gb': f'{memory.total / 1024 / 1024 / 1024:.1f}',
                        'used_gb': f'{memory.used / 1024 / 1024 / 1024:.1f}',
                        'available_gb': f'{memory.available / 1024 / 1024 / 1024:.1f}',
                        'percent': memory.percent
                    },
                    'disk': {
                        'total_gb': f'{disk.total / 1024 / 1024 / 1024:.1f}',
                        'used_gb': f'{disk.used / 1024 / 1024 / 1024:.1f}',
                        'free_gb': f'{disk.free / 1024 / 1024 / 1024:.1f}',
                        'percent': disk.percent
                    }
                },
                'services': services_status,
                'statistics': {
                    'processed_emails': processed_count,
                    'upload_files': upload_count,
                    'log_size_mb': f'{log_size / 1024 / 1024:.1f}',
                    'registered_routes': route_count
                },
                'recent_activity': {
                    'emails': recent_emails,
                    'uploads': recent_uploads,
                    'logs': recent_logs
                },
                'process': process_info
            }
        except Exception as e:
            import traceback
            return {
                'status': 'error',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'error': str(e),
                'traceback': traceback.format_exc()
            }, 500

    # 시스템 상태 페이지 - 비동기 로딩 (빠른 초기 렌더링)
    @app.route('/system/status')
    def system_status_page():
        """시스템 상태 페이지 (HTML) - 비동기 데이터 로딩"""
        from datetime import datetime

        # 초기 페이지는 빠르게 렌더링 (스켈레톤 UI)
        initial_data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'version': '2.0.0',
            'app_name': '이메일 증거 처리 시스템',
            'status': 'loading'
        }

        return render_template('system_status.html', status=initial_data)

    # 구형 /system 엔드포인트 호환성 유지
    @app.route('/system')
    def system_redirect():
        """구형 /system 엔드포인트 리다이렉트"""
        from flask import redirect, url_for
        return redirect(url_for('system_status_json'))

    # ===== 이하 기존 코드 삭제 (중복 제거) =====
    # 아래 코드는 위의 /api/system/status로 대체됨
    """
    OLD CODE REMOVED - 중복 제거됨
    if False:  # 코드 보존을 위한 블록
        status_info = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    """

    # API 문서 페이지
    @app.route('/docs')
    def docs_page():
        """API 문서 페이지 - 실제 사용 가능한 API 엔드포인트 목록"""
        from flask import render_template

        # 등록된 모든 라우트 수집
        routes = []
        for rule in app.url_map.iter_rules():
            if rule.endpoint != 'static':
                routes.append({
                    'endpoint': rule.endpoint,
                    'methods': ', '.join(sorted(rule.methods - {'HEAD', 'OPTIONS'})),
                    'path': str(rule),
                    'description': app.view_functions[rule.endpoint].__doc__ or '설명 없음'
                })

        # API 라우트만 필터링
        api_routes = [r for r in routes if r['path'].startswith('/api/')]
        web_routes = [r for r in routes if not r['path'].startswith(
            '/api/') and not r['path'].startswith('/static')]

        return render_template('api_docs.html',
                               api_routes=sorted(
                                   api_routes, key=lambda x: x['path']),
                               web_routes=sorted(
                                   web_routes, key=lambda x: x['path']),
                               total_routes=len(routes))

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
