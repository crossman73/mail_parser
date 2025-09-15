from src.web.app_factory import create_app
import sys
from pathlib import Path

# Ensure project root is on sys.path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))


app = create_app()

for r in sorted(app.url_map.iter_rules(), key=lambda x: x.rule):
    meths = r.methods or set()
    methods = ','.join(sorted(meths - {"HEAD", "OPTIONS"}))
    print(f"{r.rule:40} -> {r.endpoint:30} [{methods}]")
