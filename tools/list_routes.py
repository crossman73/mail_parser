"""List Flask routes in a way that's safe to run from PowerShell.

Usage:
    python tools/list_routes.py
"""
from src.web.app_factory import create_app
import os
import sys
from pathlib import Path

# Ensure project root is on sys.path BEFORE importing application code so
# the script can be run from PowerShell without installing the package.
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def main():
    app = create_app()
    for r in app.url_map.iter_rules():
        print(f"{r.rule} -> {r.endpoint}")


if __name__ == '__main__':
    main()
