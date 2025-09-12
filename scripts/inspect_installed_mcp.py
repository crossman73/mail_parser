installed mcp and mcp_server_fetch modules and dump key sources into workspace files.

Writes:
 - logs/mcp_server_fetch_source.txt
 - logs/mcp_source.txt

Run this from the project virtualenv so it inspects the same environment you use.
"""
import importlib
import inspect
import sys
from pathlib import Path

out_dir = Path(__file__).resolve().parent.parent / 'logs'
out_dir.mkdir(parents=True, exist_ok=True)


def dump_module(name, outname):
    try:
        mod = importlib.import_module(name)
    except Exception as e:
        print(f"IMPORT FAIL {name}: {e}")
        Path(out_dir / outname).write_text(f"IMPORT FAIL: {e}\n")
        return
    info = []
    info.append(f"MODULE: {name}\nfile: {getattr(mod, '__file__', None)}\n")
    try:
        src = inspect.getsource(mod)
        info.append('\n-- BEGIN SOURCE --\n')
        info.append(src)
        info.append('\n-- END SOURCE --\n')
    except Exception as e:
        info.append(f"(could not getsource: {e})\n")
    Path(out_dir / outname).write_text('\n'.join(info))
    print(f"WROTE {outname}")


if __name__ == '__main__':
    dump_module('mcp_server_fetch', 'mcp_server_fetch_source.txt')
    dump_module('mcp', 'mcp_source.txt')
    # also try to print available attributes for quick inspection
    try:
        import mcp
        attrs = ', '.join(
            sorted([a for a in dir(mcp) if not a.startswith('_')]))
        Path(out_dir / 'mcp_attrs.txt').write_text(attrs)
        print('WROTE mcp_attrs.txt')
    except Exception:
        pass
