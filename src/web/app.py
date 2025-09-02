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

    # 앱 시작 시 비정상 종료된 작업들 정리
    with app.app_context():
        from .progress_tracker import progress_tracker
        progress_tracker.reset_stuck_tasks(
            max_stuck_minutes=1)  # 1분 이상 된 작업들 정리
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

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
