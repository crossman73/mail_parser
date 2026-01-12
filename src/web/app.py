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

    # ========================================================================
    # 설정 관리자 초기화 (DB 불가 시 메모리 폴백)
    # ========================================================================
    try:
        from src.core.settings_manager import get_settings_manager
        settings = get_settings_manager()
        app.config['SETTINGS_MANAGER'] = settings
        if settings.is_db_available():
            print("✅ 설정 DB 연결 성공")
        else:
            print("⚠️ 설정 DB 연결 실패 - 메모리 폴백 사용")
    except Exception as e:
        print(f"⚠️ 설정 관리자 초기화 실패 (계속 진행): {e}")
        app.config['SETTINGS_MANAGER'] = None

    # ========================================================================
    # 통합 로거 설정 (DB 기반 - 실패해도 계속)
    # ========================================================================
    try:
        from src.utils.db_logger import setup_db_logging
        setup_db_logging(app.logger, "data/db/email_parser.db")
        app.logger.info("Flask 앱 로거 초기화 완료 - DB 로깅 활성화")
    except Exception as e:
        print(f"⚠️ 로거 초기화 실패 (무시됨): {e}")

    # 라우트 등록
    print("📍 라우트 등록 시작...")
    try:
        from .routes import register_routes
        register_routes(app)
        print("✅ 라우트 등록 완료")
    except Exception as e:
        print(f"❌ 라우트 등록 실패: {e}")
        import traceback
        traceback.print_exc()
        raise

    # Main Blueprint 등록
    try:
        from .blueprints.main_routes import main_bp
        app.register_blueprint(main_bp)
        app.logger.info('✅ Main blueprint registered (/, /search, /settings, /download)')
    except Exception as e:
        app.logger.warning(f'⚠️ Main blueprint 등록 실패 (계속 진행): {e}')

    # Email Blueprint 등록
    try:
        from .blueprints.email_routes import email_bp
        app.register_blueprint(email_bp)
        app.logger.info('✅ Email blueprint registered (/emails, /email, /generate_evidence, /process_selected)')
    except Exception as e:
        app.logger.warning(f'⚠️ Email blueprint 등록 실패 (계속 진행): {e}')

    # Evidence Blueprint는 routes.py의 register_routes 내부에서 등록됨
    # (evidence_service가 필요하므로)

    # API 라우트 등록
    from .api import register_api_routes
    register_api_routes(app)

    # Admin blueprint: register if available, log errors to file for debugging
    try:
        from .admin_routes import admin as admin_bp

        # Always register admin blueprint - it contains multiple routes like /admin, /admin/settings, etc.
        # The blueprint itself has url_prefix='' so routes are registered as-is
        app.register_blueprint(admin_bp)
        app.logger.info('Admin blueprint registered successfully')
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

        # 임시 파일 자동 정리 스케줄러 시작
        import threading
        import time

        from src.utils.temp_manager import temp_manager

        def cleanup_scheduler():
            """백그라운드에서 주기적으로 오래된 임시 파일 정리"""
            while True:
                try:
                    # 6시간마다 실행
                    time.sleep(6 * 60 * 60)

                    # 오래된 세션 정리
                    stats = temp_manager.cleanup_old_sessions(
                        days_old=7,           # 일반 세션 7일
                        evidence_days_old=30  # 증거 세션 30일
                    )

                    app.logger.info(
                        f"🗑️ 임시 파일 자동 정리 완료: "
                        f"일반 {stats['normal']}개, "
                        f"증거 {stats['evidence']}개, "
                        f"에러 {stats['error']}개, "
                        f"총 {stats['total']}개"
                    )
                except Exception as e:
                    app.logger.error(f"임시 파일 정리 스케줄러 오류: {e}")

        # 데몬 스레드로 시작 (앱 종료 시 자동 종료)
        cleanup_thread = threading.Thread(
            target=cleanup_scheduler, daemon=True)
        cleanup_thread.start()
        app.logger.info("✅ 임시 파일 자동 정리 스케줄러 시작 (6시간 간격)")

        # API 문서 자동 수집
        try:
            print("🔍 API 문서 수집 시작...")
            from src.api.api_collector import collect_api_docs
            from src.database.connection import db_connection

            # DB가 초기화되었는지 확인
            print(f"  - DB 경로: {db_connection.db_path}")
            if db_connection.db_path:
                count = collect_api_docs(app, db_connection)
                print(f"✅ API 문서 자동 수집 완료: {count}개 엔드포인트")
                app.logger.info(f"✅ API 문서 자동 수집 완료: {count}개 엔드포인트")
            else:
                print("⚠️ DB 미초기화로 API 문서 수집 스킵")
                app.logger.warning("⚠️ DB 미초기화로 API 문서 수집 스킵")
        except Exception as e:
            print(f"⚠️ API 문서 수집 실패: {e}")
            app.logger.warning(f"⚠️ API 문서 수집 실패 (계속 진행): {e}")
            import traceback
            traceback.print_exc()    # 템플릿 헬퍼 함수 등록
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

            # CPU 사용률 (첫 호출은 짧은 interval로 정확한 측정)
            cpu_percent = psutil.cpu_percent(interval=0.1)
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

            # 데이터베이스 헬스체크
            try:
                from src.database.connection import db_connection
                db_health = db_connection.health_check()
                db_info = db_connection.get_database_info()

                services_status.append({
                    'name': 'Database',
                    'status': db_health['status'],
                    'info': f"{db_health.get('table_count', 0)}개 테이블, "
                           f"{db_health.get('size_mb', 0):.1f}MB, "
                           f"{db_info.get('total_records', 0):,}건 레코드",
                    'healthy': db_health['status'] == 'healthy',
                    'details': {
                        'path': db_health.get('db_path'),
                        'response_time_ms': db_health.get('response_time_ms', 0),
                        'writable': db_health.get('writable', False),
                        'sqlite_version': db_info.get('sqlite_version'),
                        'tables': db_info.get('tables', []),
                        'table_counts': db_info.get('table_counts', {})
                    }
                })
            except Exception as db_error:
                services_status.append({
                    'name': 'Database',
                    'status': 'error',
                    'info': f'연결 실패: {str(db_error)}',
                    'healthy': False
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
                    'methods': ', '.join(sorted(rule.methods - {'HEAD', 'OPTIONS'})) if rule.methods else '',
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
