from src.web.app import create_app
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


app = create_app()
for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
    if '/admin' in rule.rule or 'admin' in rule.endpoint:
        print(rule.rule, '->', rule.endpoint)
