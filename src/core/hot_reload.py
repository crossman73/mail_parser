"""Dev helper: reload selected python modules in-place using importlib.reload.

Note: this is a development aid only. Re-loading modules at runtime can leave
stateful objects inconsistent. Use only with FEATURE_FLAGS['enable_dev_reload']
enabled and in development environments.
"""
from importlib import import_module, reload
from types import ModuleType
from typing import Any, Dict, List


def reload_modules(module_names: List[str]) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for name in module_names:
        try:
            mod = import_module(name)
            reloaded = reload(mod)
            results.append({'module': name, 'status': 'reloaded'})
        except Exception as e:
            results.append(
                {'module': name, 'status': 'error', 'error': str(e)})
    return results
