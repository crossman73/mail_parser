"""
Flask 애플리케이션 팩토리 - 통합 아키텍처 기반
"""
import os
from pathlib import Path

from flask import (Flask, jsonify, redirect, render_template,
                   render_template_string, request, url_for)


def create_app(unified_arch=None):
    """통합 아키텍처 기반 Flask 앱 생성"""

    # Flask 앱 생성 - 템플릿 경로 수정
    app_root = Path(__file__).parent.parent.parent
    template_dir = app_root / "templates"
    static_dir = app_root / "static"

    app = Flask(__name__,
                template_folder=str(template_dir),
                static_folder=str(static_dir))

    # 기본 설정
    app.config.update({
        'SECRET_KEY': os.environ.get('SECRET_KEY', 'unified-architecture-key-2024'),
        'MAX_CONTENT_LENGTH': 2 * 1024 * 1024 * 1024,  # 2GB
        'JSON_AS_ASCII': False,  # 한글 지원
        'SEND_FILE_MAX_AGE_DEFAULT': 0,  # 캐시 비활성화 (개발용)
    })

    # File upload default directory (can be overridden in config.json)
    app_root = Path(__file__).parent.parent.parent
    # Normalize configured upload folder to an absolute path under project root
    configured_upload = os.environ.get('UPLOAD_FOLDER') or app.config.get(
        'UPLOAD_FOLDER') or str(app_root / 'uploads')
    upload_path = Path(configured_upload)
    if not upload_path.is_absolute():
        upload_path = app_root / upload_path
    try:
        upload_path = upload_path.resolve()
    except Exception:
        # fallback to the joined path if resolve fails (e.g., permissions)
        upload_path = app_root / upload_path
    app.config['UPLOAD_FOLDER'] = str(upload_path)

    # Ensure common runtime directories exist and have best-effort restrictive perms
    try:
        upload_path.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(str(upload_path), 0o700)
        except Exception:
            # Non-fatal on Windows or filesystems that don't support POSIX perms
            pass
    except Exception as e:
        print(f"⚠️ 업로드 폴더 생성 실패: {e}")

    # Create other expected runtime directories (logs, temp, processed_emails)
    for d in ('logs', 'temp', 'processed_emails'):
        try:
            p = app_root / d
            p.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

    # Default allowed upload extensions (operators can override in config.json)
    app.config.setdefault('ALLOWED_UPLOAD_EXTENSIONS', [
        'mbox', 'eml', 'txt', 'pdf', 'zip', '7z', 'tar', 'gz', 'csv', 'xlsx', 'xls', 'msg'
    ])

    # 통합 아키텍처 연결
    # If an instance was provided, use it. Otherwise try to create a
    # lightweight default UnifiedArchitecture so endpoints like /system
    # and /health can provide real status in dev and integration runs.
    if unified_arch:
        app.unified_arch = unified_arch
        app.logger = unified_arch.logger
    else:
        # Allow opt-out via env var for very lightweight runs
        if os.environ.get('DISABLE_AUTO_UNIFIED_ARCH', '').lower() in ('1', 'true', 'yes', 'on'):
            app.logger.debug(
                '자동 UnifiedArchitecture 초기화를 건너뜁니다 (DISABLE_AUTO_UNIFIED_ARCH).')
        else:
            try:
                # Create a SystemConfig using the application root so paths
                # (uploads, logs, etc.) resolve to the project tree.
                from src.core.unified_architecture import (SystemConfig,
                                                           UnifiedArchitecture)

                config = SystemConfig(project_root=app_root)
                _ua = UnifiedArchitecture(config)
                _ua.initialize()
                app.unified_arch = _ua
                # prefer unified logger if available
                try:
                    app.logger = _ua.logger
                except Exception:
                    pass
                print('🔧 기본 UnifiedArchitecture 인스턴스가 앱에 연결되었습니다')
            except Exception as e:
                # Non-fatal: leave app without unified_arch but log for debugging
                try:
                    app.logger.warning(f"UnifiedArchitecture 자동 초기화 실패: {e}")
                except Exception:
                    print(f"UnifiedArchitecture 자동 초기화 실패: {e}")

    # 라우트 등록
    register_core_routes(app)
    # Prefer external API module (src.web.api) if available. Fall back to
    # the in-file `register_api_routes` if import fails.
    try:
        from src.web import api as external_api
        external_api.register_api_routes(app)
    except Exception:
        # fallback to local registration
        register_api_routes(app)
    # Compatibility: ensure light-weight /docs and /upload routes exist for
    # older clients or test scripts. Register only if not already present.

    def register_compat_routes(app):
        try:
            # /docs endpoint (endpoint name: 'api_docs')
            if 'api_docs' not in app.view_functions:
                @app.route('/docs')
                def api_docs():
                    try:
                        return render_template('api_docs.html', title='API 문서')
                    except Exception:
                        return """
                        <html>
                        <head><title>API 문서</title></head>
                        <body>
                            <h1>📧 이메일 증거 처리 시스템 API v2.0</h1>
                            <h2>주요 엔드포인트</h2>
                            <ul>
                                <li><a href="/">/</a> - 메인 페이지</li>
                                <li><a href="/health">/health</a> - 헬스체크</li>
                                <li><a href="/system/status">/system/status</a> - 시스템 상태</li>
                                <li><a href="/api">/api</a> - API 정보</li>
                                <li><a href="/upload">/upload</a> - 파일 업로드 (구현 예정)</li>
                            </ul>
                        </body>
                        </html>
                        """

            # NOTE: /upload compatibility route intentionally removed here to avoid
            # duplicate route registrations. The canonical upload implementation
            # lives in `src.web.routes` (full UI) and the API upload is provided
            # as `/api/upload` in `src.web.api`. Keeping one implementation avoids
            # unpredictable inline HTML fallbacks or conflicting handlers.
        except Exception:
            # Don't let compatibility helpers break app startup
            try:
                app.logger.debug('Compatibility route registration failed.')
            except Exception:
                pass

    register_compat_routes(app)
    # Provide a lightweight /api root and /api/docs compatibility routes
    try:
        if '/api' not in [r.rule for r in app.url_map.iter_rules()]:
            @app.route('/api')
            def api_info_compat():
                return jsonify({
                    'name': 'Email Evidence Processing API',
                    'version': '2.0',
                    'description': 'Compatibility root for legacy /api requests',
                    'endpoints': {
                        'health': '/health',
                        'system_status': '/system/status',
                        'upload': '/upload',
                        'docs': '/docs',
                    }
                })

            if '/api/docs' not in [r.rule for r in app.url_map.iter_rules()]:
                @app.route('/api/docs')
                def api_docs_redirect_compat():
                    # Prefer serving the API docs dashboard directly if available
                    try:
                        # If Swagger UI registered an API docs dashboard endpoint, call it
                        if 'api_docs_dashboard' in app.view_functions:
                            return app.view_functions['api_docs_dashboard']()
                        if 'api_docs' in app.view_functions:
                            return app.view_functions['api_docs']()
                    except Exception:
                        pass
                    # Fallback: simple HTML
                    try:
                        return render_template('api_docs.html', title='API 문서')
                    except Exception:
                        return """
                        <html><body><h1>API 문서</h1><p>문서를 사용할 수 없습니다.</p></body></html>
                        """
    except Exception:
        try:
            app.logger.debug(
                'API compatibility route registration skipped/failed')
        except Exception:
            pass
    # UI wireframe routes (minimal)
    try:
        from src.web.ui_routes import ui as ui_bp
        app.register_blueprint(ui_bp)
    except Exception:
        pass
    # Upload streaming skeleton
    try:
        from src.web.upload_stream import upload_bp
        app.register_blueprint(upload_bp)
    except Exception:
        pass
    # Admin dashboard
    try:
        from src.web.admin_routes import admin as admin_bp
        app.register_blueprint(admin_bp)
    except Exception:
        pass

    # 에러 핸들러 등록
    register_error_handlers(app)

    # Feature flags: 환경변수로 간단히 제어
    app.config['FEATURE_FLAGS'] = {
        'enable_redis': os.environ.get('ENABLE_REDIS', 'false').lower() in ('1', 'true', 'yes', 'on'),
        'enable_swagger': os.environ.get('ENABLE_SWAGGER', 'false').lower() in ('1', 'true', 'yes', 'on'),
        'enable_upload': os.environ.get('ENABLE_UPLOAD', 'true').lower() in ('1', 'true', 'yes', 'on'),
    }

    @app.context_processor
    def inject_feature_flags():
        return {'FEATURE_FLAGS': app.config.get('FEATURE_FLAGS', {})}

    @app.context_processor
    def inject_template_helpers():
        """템플릿 헬퍼 함수 등록: 엔드포인트 확인 및 안전한 URL 생성"""
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

    # Phase 2.3: Swagger UI 통합
    try:
        from src.docs import init_swagger_ui

        # Initialize swagger UI (assignment not needed)
        init_swagger_ui(app, "docs/openapi.json")
        print("🔌 Swagger UI 서비스 통합 완료")

        # 문서 API 등록
        from src.docs.api_endpoints import register_docs_api
        register_docs_api(app)

    except ImportError as e:
        print(f"⚠️ Swagger UI 통합 실패 (선택사항): {e}")
    except Exception as e:
        print(f"⚠️ Swagger UI 초기화 오류: {e}")
    # Run startup checks (DBs, templates, logging, optional services)
    try:
        from src.core import startup

        # Register a lightweight compatibility route for legacy templates
        # that call url_for('additional_evidence'). The full implementation
        # lives in src.web.routes.register_routes which may be skipped in
        # some configurations; this ensures url_for works during startup.
        try:
            @app.route('/additional_evidence', endpoint='additional_evidence')
            def _compat_additional_evidence():
                # minimal placeholder page
                return render_template('additional_evidence.html', evidence_list=[], statistics={})
        except Exception:
            # if route already exists or template missing, ignore
            pass

        errors = startup.check_and_init(app)
        app.config['STARTUP_ERRORS'] = errors
        if errors:
            print(f"⚠️ Startup checks found issues: {errors}")
    except Exception as e:
        print(f"⚠️ Startup checks failed: {e}")

    return app


def register_core_routes(app):
    """핵심 웹 라우트 등록"""

    @app.route('/')
    def index():
        """메인 대시보드"""
        try:
            system_status = None
            if hasattr(app, 'unified_arch'):
                system_status = app.unified_arch.get_system_status()

            return render_template('index.html',
                                   title='이메일 증거 처리 시스템 v2.0',
                                   system_status=system_status)
        except Exception as e:
            if hasattr(app, 'logger'):
                app.logger.error(f"메인 페이지 로드 실패: {e}")
            return f"<h1>시스템 초기화 중입니다...</h1><p>오류: {str(e)}</p>", 503

    @app.route('/health')
    def health_check():
        """헬스체크 (Docker/로드밸런서용)"""
        try:
            # If the unified architecture is available, derive health from its
            # startup errors and basic metrics. Otherwise return a lightweight
            # healthy response for container health-checks.
            if hasattr(app, 'unified_arch'):
                status = app.unified_arch.get_system_status()
                startup_errors = app.config.get('STARTUP_ERRORS') or []
                healthy = (not startup_errors)
                payload = {
                    'status': 'healthy' if healthy else 'unhealthy',
                    'version': status.get('version'),
                    'services': len(status.get('registered_services', [])),
                    'timestamp': status.get('timestamp'),
                    'uptime_seconds': status.get('uptime_seconds')
                }
                if startup_errors:
                    payload['startup_errors'] = startup_errors

                return (jsonify(payload), 200) if healthy else (jsonify(payload), 503)
            else:
                # Minimal response for probes when unified architecture is not
                # initialized (development). Return 200 to avoid orchestration
                # restarts during dev runs.
                return jsonify({
                    'status': 'healthy',
                    'version': '2.0.0',
                    'services': 0,
                    'timestamp': 'unknown'
                }), 200
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'error': str(e)
            }), 500

    @app.route('/system')
    def system_overview():
        """시스템 대시보드(간단한 JSON 또는 HTML)"""
        try:
            if hasattr(app, 'unified_arch'):
                status = app.unified_arch.get_system_status()
                # If templates available, render a human-friendly page
                try:
                    return render_template('system_overview.html', status=status)
                except Exception:
                    return jsonify(status)
            else:
                return jsonify({
                    'error': 'Unified architecture not initialized',
                    'app_name': '이메일 증거 처리 시스템',
                    'version': '2.0.0'
                })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/system/status')
    def system_status():
        """시스템 상태 페이지"""
        try:
            # If a browser (Accept: text/html) requests this endpoint, render
            # a human-friendly HTML page. Otherwise return JSON for API clients.
            accepts_html = request.accept_mimetypes['text/html'] >= request.accept_mimetypes['application/json']

            if hasattr(app, 'unified_arch'):
                status = app.unified_arch.get_system_status()
                # Prepare optional admin links for services if admin blueprint
                # exposes a 'service' endpoint. This is done defensively so
                # templates can render links only when available.
                service_admin_links = {}
                try:
                    for s in status.get('registered_services', []) or []:
                        name = None
                        if isinstance(s, dict):
                            name = s.get('name')
                        elif isinstance(s, str):
                            name = s
                        if not name:
                            continue
                        try:
                            admin_url = url_for('admin.service', name=name)
                            service_admin_links[name] = admin_url
                        except Exception:
                            try:
                                admin_url = url_for(
                                    'admin.service', service=name)
                                service_admin_links[name] = admin_url
                            except Exception:
                                # no admin link available for this service
                                pass
                except Exception:
                    # Be resilient if status shape changes
                    service_admin_links = {}

                if accepts_html:
                    try:
                        return render_template('system_status.html', status=status, service_admin_links=service_admin_links)
                    except Exception:
                        # If template missing or rendering fails, fall back to JSON
                        return jsonify(status)
                return jsonify(status)
            else:
                payload = {
                    'error': 'Unified architecture not initialized',
                    'app_name': '이메일 증거 처리 시스템',
                    'version': '2.0.0'
                }
                if accepts_html:
                    try:
                        return render_template('system_status.html', status=payload)
                    except Exception:
                        return jsonify(payload)
                return jsonify(payload)
        except Exception as e:
            return jsonify({'error': str(e)}), 500


def register_api_routes(app):
    """API 라우트 등록 - 통합 아키텍처 전용"""

    # Phase 1에서는 기존 routes.py를 사용하지 않고 새로운 라우트만 사용
    # Phase 2에서 기존 routes.py와 통합 예정

    # API 문서 라우트
    @app.route('/docs')
    def api_docs():
        """API 문서 페이지"""
        try:
            return render_template('api_docs.html', title='API 문서')
        except Exception:
            # 템플릿이 없으면 간단한 HTML 반환
            return """
            <html>
            <head><title>API 문서</title></head>
            <body>
                <h1>📧 이메일 증거 처리 시스템 API v2.0</h1>
                <h2>주요 엔드포인트</h2>
                <ul>
                    <li><a href="/">/</a> - 메인 페이지</li>
                    <li><a href="/health">/health</a> - 헬스체크</li>
                    <li><a href="/system/status">/system/status</a> - 시스템 상태</li>
                    <li><a href="/api">/api</a> - API 정보</li>
                    <li><a href="/upload">/upload</a> - 파일 업로드 (구현 예정)</li>
                </ul>
            </body>
            </html>
            """

    @app.route('/api')
    def api_info():
        """API 정보 엔드포인트"""
        return jsonify({
            'name': 'Email Evidence Processing API',
            'version': '2.0',
            'description': '이메일 증거 처리 시스템 통합 API',
            'endpoints': {
                'health': '/health',
                'system_status': '/system/status',
                'upload': '/upload (구현 예정)',
                'process': '/api/process (구현 예정)',
                'evidence': '/api/evidence (구현 예정)',
                'timeline': '/api/timeline (구현 예정)',
                'docs': '/docs'
            }
        })

    # 호환성 라우트: 기존/테스트에서 기대하는 경로를 실제 등록된 경로로 리다이렉트
    @app.route('/swagger')
    def legacy_swagger_redirect():
        """과거/테스트에서 /swagger 경로를 요청하면 실제 Swagger UI로 이동시킵니다."""
        try:
            return redirect(url_for('swagger_ui'))
        except Exception:
            # 안전하게 절대 경로로 리다이렉트
            return redirect('/api/swagger-ui')

    @app.route('/api/docs')
    def legacy_api_docs_redirect():
        """/api/docs 요청을 문서 대시보드로 리다이렉트합니다."""
        try:
            return redirect(url_for('api_docs_dashboard'))
        except Exception:
            return redirect('/api/docs-dashboard')

    # NOTE: The in-file compatibility /upload route has been intentionally
    # removed from this factory to avoid conflicting handlers. The canonical
    # UI upload implementation is provided by `src.web.routes.upload_file` and
    # the API upload endpoint is `src.web.api.api_upload_file` (located at
    # `/api/upload`). Keeping a single implementation prevents unpredictable
    # inline HTML fallbacks and makes behavior consistent across factory modes.


def register_error_handlers(app):
    """에러 핸들러 등록"""

    @app.errorhandler(404)
    def not_found(error):
        return """
        <html>
        <head><title>404 - 페이지를 찾을 수 없습니다</title></head>
        <body>
            <h1>404 - 페이지를 찾을 수 없습니다</h1>
            <p>요청하신 페이지를 찾을 수 없습니다.</p>
            <a href="/">메인으로 돌아가기</a>
        </body>
        </html>
        """, 404

    @app.errorhandler(500)
    def internal_error(error):
        # Log structured error to DB for later inspection
        try:
            import traceback

            from src.core import db_manager
            tb = traceback.format_exc()
            db_manager.write_log('ERROR', 'internal_server_error', {
                                 'error': str(error), 'trace': tb})
        except Exception:
            # fallback to logger
            if hasattr(app, 'logger'):
                app.logger.error(f"내부 서버 오류(로깅 실패): {error}")
        return """
        <html>
        <head><title>500 - 서버 내부 오류</title></head>
        <body>
            <h1>500 - 서버 내부 오류</h1>
            <p>서버 내부 오류가 발생했습니다.</p>
            <a href="/">메인으로 돌아가기</a>
        </body>
        </html>
        """, 500

    @app.errorhandler(413)
    def file_too_large(error):
        return """
        <html>
        <head><title>413 - 파일이 너무 큽니다</title></head>
        <body>
            <h1>413 - 파일이 너무 큽니다</h1>
            <p>업로드 파일이 너무 큽니다. (최대 2GB)</p>
            <a href="/">메인으로 돌아가기</a>
        </body>
        </html>
        """, 413
