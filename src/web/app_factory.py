"""
Flask 애플리케이션 팩토리 - 통합 아키텍처 기반
"""
import os
import sys
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, url_for


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

    # 통합 아키텍처 연결
    if unified_arch:
        app.unified_arch = unified_arch
        app.logger = unified_arch.logger

    # 라우트 등록
    register_core_routes(app)
    register_api_routes(app)
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

    # Phase 2.3: Swagger UI 통합
    try:
        from src.docs import init_swagger_ui
        swagger_service = init_swagger_ui(app, "docs/openapi.json")
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
            if hasattr(app, 'unified_arch'):
                status = app.unified_arch.get_system_status()
                return jsonify({
                    'status': 'healthy',
                    'version': status['version'],
                    'services': len(status['registered_services']),
                    'timestamp': status['timestamp']
                })
            else:
                return jsonify({
                    'status': 'healthy',
                    'version': '2.0.0',
                    'services': 0,
                    'timestamp': 'unknown'
                })
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'error': str(e)
            }), 500

    @app.route('/system/status')
    def system_status():
        """시스템 상태 페이지"""
        try:
            if hasattr(app, 'unified_arch'):
                status = app.unified_arch.get_system_status()
                return jsonify(status)
            else:
                return jsonify({
                    'error': 'Unified architecture not initialized',
                    'app_name': '이메일 증거 처리 시스템',
                    'version': '2.0.0'
                })
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
        except:
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

    @app.route('/upload', methods=['GET', 'POST'])
    def upload():
        """파일 업로드 페이지 (기본 구현)"""
        if request.method == 'POST':
            return jsonify({
                'status': 'success',
                'message': '업로드 기능은 다음 단계에서 구현됩니다.',
                'phase': 'Phase 2 - API 구현 예정'
            })
        else:
            return """
            <html>
            <head><title>파일 업로드</title></head>
            <body>
                <h1>📧 파일 업로드</h1>
                <p>이 기능은 Phase 2에서 구현될 예정입니다.</p>
                <a href="/">메인으로 돌아가기</a>
            </body>
            </html>
            """


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
