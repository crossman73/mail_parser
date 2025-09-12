# Dump Flask app url_map rules to stdout
# 사용: python scripts\dump_routes.py

from src.web.app import create_app
import sys
from pathlib import Path

# Ensure repo root is on sys.path so `src` package is importable when running the script
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


print('DEBUG: before create_app')
app = create_app()
print('DEBUG: after create_app')
print('DEBUG: url_map size', len(list(app.url_map.iter_rules())))

print('ROUTES:')
for rule in sorted(app.url_map.iter_rules(), key=lambda r: (r.rule, r.endpoint)):
    methods_iter = rule.methods or []
    methods = ','.join(sorted(methods_iter))
    print(f"{rule.rule} -> endpoint={rule.endpoint} methods={methods}")

print('\nEND')
