import importlib
import inspect
import json

try:
    m = importlib.import_module('mcp_server_fetch')
    info = {'file': getattr(m, '__file__', None), 'members': [
        n for n in dir(m) if not n.startswith('_')]}
    for candidate in ('serve', 'main'):
        if candidate in info['members']:
            try:
                info[f'{candidate}_sig'] = str(
                    inspect.signature(getattr(m, candidate)))
            except Exception:
                info[f'{candidate}_sig'] = 'unable to inspect'
    print(json.dumps(info, ensure_ascii=False, indent=2))
except Exception as e:
    print('IMPORT FAIL:', repr(e))
