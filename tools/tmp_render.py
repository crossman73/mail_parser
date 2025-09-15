from src.web import app_factory
import traceback
import os
import sys
from pathlib import Path

# Ensure project root is on sys.path so local `src` package can be imported
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


# Ensure we don't accidentally initialize heavy services during app creation
os.environ['DISABLE_AUTO_UNIFIED_ARCH'] = '1'


class DummyUA:
    def __init__(self):
        # provide a minimal logger attribute to satisfy app_factory's assignment
        import logging
        self.logger = logging.getLogger('dummy')

    def get_system_status(self):
        return {
            'app_name': '테스트앱',
            'version': '0.1',
            'timestamp': 'now',
            'registered_services': [
                {'name': 'email_processor', 'status': 'ok'},
                {'name': 'forensic_service', 'status': 'degraded'}
            ],
            'directories': {'docs': '/project/docs'}
        }


def main():
    try:
        dummy_unified = DummyUA()
        app = app_factory.create_app(unified_arch=dummy_unified)
        # Render in a test request context to allow url_for and other request utilities
        from flask import render_template
        with app.test_request_context('/system/status', headers={'Accept': 'text/html'}):
            html = render_template('system_status.html',
                                   status=dummy_unified.get_system_status(),
                                   service_admin_links={'email_processor': '/admin/email'})
            print('Rendered length:', len(html))
    except Exception as e:
        traceback.print_exc()
        print('Error:', e)


if __name__ == '__main__':
    main()
