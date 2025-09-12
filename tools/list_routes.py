"""List Flask routes in a way that's safe to run from PowerShell.

Usage:
  python tools/list_routes.py
"""
from src.web.app_factory import create_app
import os
import sys

# Ensure project root is on sys.path BEFORE importing application code so
# the script can be run from PowerShell without installing the package.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def main():
    app = create_app()
    for r in app.url_map.iter_rules():
        print(f"{r.rule} -> {r.endpoint}")


if __name__ == '__main__':
    main()
