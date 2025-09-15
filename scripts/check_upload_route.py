"""Check whether the legacy full UI app exposes /upload without starting the server.

This script is intentionally light-weight and safe to run in CI or locally. It prints
one-line status output suitable for background runs.
"""
import os
import sys
import traceback


# Find the project root robustly: walk up until we find run_server.py or .git
def find_project_root(start_path: str):
    cur = os.path.abspath(start_path)
    last = None
    while cur and cur != last:
        if os.path.exists(os.path.join(cur, 'run_server.py')) or os.path.exists(os.path.join(cur, '.git')):
            return cur
        last = cur
        cur = os.path.dirname(cur)
    # fallback to script dir's parent
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


ROOT = find_project_root(os.getcwd())
print(f'INFO: using project root: {ROOT}')
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def main():
    try:
        # Import legacy app factory explicitly to check the full UI
        from src.web.app import create_app

        app = create_app()

        routes = {r.rule: r.endpoint for r in app.url_map.iter_rules()}

        if '/upload' in routes:
            print('OK: /upload registered ->', routes['/upload'])
            sys.exit(0)
        else:
            print('MISSING: /upload not found; registered routes:')
            for k in sorted(routes):
                print('  ', k, '->', routes[k])
            sys.exit(2)

    except Exception:
        print('ERROR: Exception while checking app routes')
        traceback.print_exc()
        sys.exit(3)


if __name__ == '__main__':
    main()
