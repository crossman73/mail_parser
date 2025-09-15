from src.web.app_factory import create_app
import json
import sys
from pathlib import Path

# Ensure project root is on sys.path so local `src` package can be imported
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def fetch(path, headers=None):
    app = create_app()
    with app.test_client() as client:
        resp = client.get(path, headers=headers or {})
        print('--- REQUEST:', path, 'headers=', headers)
        print('status:', resp.status_code)
        print('content-type:', resp.content_type)
        print('body:')
        try:
            print(resp.get_data(as_text=True))
        except Exception:
            print(repr(resp.data))


def main():
    print('Dumping url_map for reference:')
    app = create_app()
    with app.app_context():
        rules = sorted([(r.rule, r.endpoint)
                       for r in app.url_map.iter_rules()])
        print(json.dumps(rules, ensure_ascii=False, indent=2))

    fetch('/system/status', headers={'Accept': 'text/html'})
    fetch('/system/status', headers={'Accept': 'application/json'})
    fetch('/system/status', headers={})


if __name__ == '__main__':
    main()
