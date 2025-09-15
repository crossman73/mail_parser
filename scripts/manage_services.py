"""
Light-weight service manager for the development environment.

Usage:
  python scripts/manage_services.py list
  python scripts/manage_services.py stop <service_name>
  python scripts/manage_services.py start <service_name>
  python scripts/manage_services.py restart <service_name>
  python scripts/manage_services.py stop-all
  python scripts/manage_services.py restart-all

This script uses the UnifiedArchitecture singleton (src.core.unified_architecture)
and calls common lifecycle methods on registered services when available.
This is a best-effort helper to stop/start specific services without bringing
down the whole application process.

Note: In production, prefer process manager (systemd, supervisor) or container
orchestration (k8s) for per-process control. This script is for local/dev use.
"""
from src.core.unified_architecture import get_unified_architecture
import sys
from pathlib import Path

# Ensure project root is on sys.path so 'src' package imports work when
# running this script from the scripts/ directory.
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))


def call_method_if_exists(obj, methods):
    for name in methods:
        if hasattr(obj, name):
            try:
                method = getattr(obj, name)
                method()
                return True, name
            except Exception as e:
                return False, f"{name} error: {e}"
    return False, None


def list_services(ua):
    services = ua.services
    if not services:
        print('No registered services found')
        return
    print('Registered services:')
    for name, inst in services.items():
        print(f' - {name} ({type(inst).__name__})')


def stop_service(ua, name):
    svc = ua.get_service(name)
    if not svc:
        print(f'Service not found: {name}')
        return
    ok, info = call_method_if_exists(svc, ['stop', 'shutdown', 'cleanup'])
    if ok:
        print(f'Stopped {name} via {info}')
    else:
        print(f'Could not stop {name}. Tried methods, last result: {info}')


def start_service(ua, name):
    svc = ua.get_service(name)
    if not svc:
        print(f'Service not found: {name}')
        return
    ok, info = call_method_if_exists(svc, ['start', 'initialize', 'run'])
    if ok:
        print(f'Started {name} via {info}')
    else:
        print(f'Could not start {name}. Tried methods, last result: {info}')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: scripts/manage_services.py <command> [service_name]')
        sys.exit(1)

    cmd = sys.argv[1]
    ua = get_unified_architecture()

    if cmd == 'list':
        list_services(ua)
    elif cmd == 'stop-all':
        for name in list(ua.services.keys()):
            stop_service(ua, name)
    elif cmd == 'restart-all':
        for name in list(ua.services.keys()):
            stop_service(ua, name)
            start_service(ua, name)
    elif cmd in ('stop', 'start', 'restart'):
        if len(sys.argv) < 3:
            print(f'Usage: scripts/manage_services.py {cmd} <service_name>')
            sys.exit(1)
        name = sys.argv[2]
        if cmd == 'stop':
            stop_service(ua, name)
        elif cmd == 'start':
            start_service(ua, name)
        else:
            stop_service(ua, name)
            start_service(ua, name)
    else:
        print('Unknown command:', cmd)
        sys.exit(2)
