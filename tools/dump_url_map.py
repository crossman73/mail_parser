from src.web.app_factory import create_app
import json
import sys
from pathlib import Path

# Ensure project root (repository) is on sys.path so imports like 'src.*' work
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def main():
    app = create_app()
    with app.app_context():
        rules = sorted([(r.rule, r.endpoint)
                        for r in app.url_map.iter_rules()])
        print(json.dumps(rules, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
