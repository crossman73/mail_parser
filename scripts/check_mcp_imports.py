import importlib
import inspect
from pathlib import Path

mods = [
    'mcp_server_fetch', 'mcp', 'mcp.server.lowlevel', 'mcp.server', 'mcp.shared',
    'mcp.client'
]

out_path = Path(__file__).with_suffix('.log')
with out_path.open('w', encoding='utf-8') as log:
    for mod in mods:
        try:
            m = importlib.import_module(mod)
            log.write(f"MODULE: {mod}\n")
            log.write(f"  file: {getattr(m, '__file__', None)}\n")
            names = [n for n in dir(m) if not n.startswith('_')]
            sample = ', '.join(names[:40])
            log.write(f"  members sample: {sample}\n")
            for candidate in ('serve', 'main', 'run', 'create_task_group'):
                if candidate in names:
                    try:
                        obj = getattr(m, candidate)
                        log.write(
                            f'  signature for {candidate}: {inspect.signature(obj)}\n')
                    except Exception:
                        log.write(
                            f'  could not inspect signature for {candidate}\n')
        except Exception as e:
            log.write(f"MODULE FAIL: {mod} -> {repr(e)}\n")
        log.write('\n')

        # final marker while file still open
        log.write('Done.\n')

    print(f"Wrote MCP import log to: {out_path}")
