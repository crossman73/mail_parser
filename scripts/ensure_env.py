"""ensure_env.py
Simple developer environment checker and helper.
- Prints current python executable, venv presence, pip packages (mcp, mcp_server_fetch), and PATH info.
- Exits non-zero if obvious misconfiguration detected.

Usage: python scripts/ensure_env.py
"""
import os
import subprocess
import sys
from pathlib import Path


def which(exe):
    from shutil import which as _which
    return _which(exe)


def main():
    repo_root = Path(__file__).resolve().parents[1]
    print('Repository root:', repo_root)
    print('Python executable:', sys.executable)
    print('Python version: ', sys.version.replace('\n', ' '))
    venv = os.environ.get('VIRTUAL_ENV') or os.environ.get('CONDA_PREFIX')
    print('Virtualenv active:', bool(venv))
    if venv:
        print('Virtualenv path:', venv)
    # check for .venv next to repo
    venv_path = repo_root / '.venv'
    print("Repository .venv exists:", venv_path.exists())

    # check for uvx
    print('\nChecking executables (uvx, python, mcp_server_fetch) on PATH:')
    print('  uvx ->', which('uvx'))
    print('  mcp-server-fetch ->', which('mcp-server-fetch'))
    print('  python ->', which('python'))

    # check for packages
    print('\nChecking python packages:')
    try:
        import importlib
        for pkg in ('mcp', 'mcp_server_fetch'):
            try:
                m = importlib.import_module(pkg)
                print(f'  {pkg} -> installed at {getattr(m, "__file__", None)}')
            except Exception as e:
                print(f'  {pkg} -> NOT importable: {e!r}')
    except Exception:
        print('  importlib not available')

    # quick pip list (top 30)
    try:
        print('\nTop installed packages (pip list -l):')
        p = subprocess.run([sys.executable, '-m', 'pip', 'list',
                           '--disable-pip-version-check'], capture_output=True, text=True, check=False)
        lines = p.stdout.splitlines()
        for l in lines[:30]:
            print('   ', l)
    except Exception as e:
        print('  pip list failed:', e)

    # guidance
    print('\nGuidance:')
    print(' - Use the project venv:')
    print('    PowerShell: & .\\.venv\\Scripts\\Activate.ps1')
    print('    cmd: .\\.venv\\Scripts\\activate.bat')
    print('    bash: source .venv/bin/activate')
    print(' - Prefer running tools via MCP (configured in settings.json) instead of ad-hoc python -m calls')
    print(' - Use scripts/mcp_task_manager.py to create/manage tasks that will be executed through MCP workflows')

    # fail if no venv and python executable not under repo
    if not venv and not str(sys.executable).startswith(str(venv_path)):
        print(
            '\nWARNING: No virtualenv active and Python executable is not repository .venv')
        return 2

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
