"""Inspect installed mcp packages and print useful info for debugging.
Run from PowerShell: python .\scripts\inspect_mcp.py
"""
import importlib
import inspect
import sys

mods = [
    'mcp_server_fetch', 'mcp', 'mcp.server.lowlevel', 'mcp.server', 'mcp.shared',
    'mcp.client'
]
for mod in mods:
    try:
        m = importlib.import_module(mod)
        print('MODULE:', mod)
        print('  file:', getattr(m, '__file__', None))
        names = [n for n in dir(m) if not n.startswith('_')]
        sample = ', '.join(names[:80])
        print('  members sample:', sample)
        # try to print serve signature if present
        for candidate in ('serve', 'main', 'run', 'create_task_group'):
            if candidate in names:
                try:
                    obj = getattr(m, candidate)
                    print(f'  signature for {candidate}:',
                          inspect.signature(obj))
                except Exception:
                    print(f'  could not inspect signature for {candidate}')
        print()
    except Exception as e:
        print('MODULE FAIL:', mod, '->', repr(e))
        print()

# quick note for user
print('Done. If a module file is None or "MODULE FAIL" appears, ensure the module is installed in the active Python environment.')
