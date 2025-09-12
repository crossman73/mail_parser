#!/usr/bin/env python3
"""Check server and attempt admin reload in a way that's safe for PowerShell.

Writes results to temp/*.txt and temp/*.json so the calling shell/agent can read them
without needing complex quoting.
"""
import json
import socket
import sys
import traceback
from importlib import import_module
from pathlib import Path

out_dir = Path('temp')
out_dir.mkdir(exist_ok=True)

# Ensure repo root is on sys.path so 'src' package can be imported when
# this script is executed from anywhere (e.g., .venv python).
repo_root = Path(__file__).resolve().parents[1]
repo_root_str = str(repo_root)
if repo_root_str not in sys.path:
    sys.path.insert(0, repo_root_str)


def write(path, data, mode='w', encoding='utf-8'):
    p = out_dir / path
    with open(p, mode, encoding=encoding) as f:
        f.write(data)


def read_token():
    try:
        dbm = import_module('src.core.db_manager')
        token = dbm.get_setting('DEV_RELOAD_TOKEN')
        write('dev_reload_token.txt', repr(token) + '\n')
        return token
    except Exception as e:
        tb = traceback.format_exc()
        write('dev_reload_token.txt', 'ERROR: ' + str(e) + '\n' + tb)
        return None


def tail_server_log():
    try:
        p = Path('server.log')
        if not p.exists():
            write('server_log_tail.txt', 'server.log not found\n')
            return
        lines = p.read_text(encoding='utf-8', errors='replace').splitlines()
        tail = '\n'.join(lines[-50:])
        write('server_log_tail.txt', tail + '\n')
    except Exception as e:
        write('server_log_tail.txt', 'ERROR: ' +
              str(e) + '\n' + traceback.format_exc())


def check_port(host='127.0.0.1', port=5000, timeout=2.0):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            write('netstat_5000.txt', f'{host}:{port} open\n')
            return True
    except Exception as e:
        write('netstat_5000.txt',
              f'{host}:{port} closed or unreachable: {e}\n')
        return False


def post_reload(token):
    try:
        # Use stdlib to avoid external deps
        import urllib.error as error
        import urllib.request as request

        url = 'http://127.0.0.1:5000/admin/reload'
        body = json.dumps(
            {'modules': ['src.web.admin_routes']}).encode('utf-8')
        headers = {'Content-Type': 'application/json',
                   'X-DEV-RELOAD-TOKEN': token or ''}
        req = request.Request(url, data=body, headers=headers, method='POST')
        with request.urlopen(req, timeout=10) as resp:
            data = resp.read().decode('utf-8', errors='replace')
            # try to pretty-print JSON if possible
            try:
                j = json.loads(data)
                write('real_reload_response.json', json.dumps(
                    j, ensure_ascii=False, indent=2) + '\n')
            except Exception:
                write('real_reload_response.json', data + '\n')
            return True
    except Exception as e:
        tb = traceback.format_exc()
        write('real_reload_error.txt', 'ERROR: ' + str(e) + '\n' + tb)
        return False


def dump_settings():
    try:
        dbm = import_module('src.core.db_manager')
        keys = ['ENABLE_DEV_RELOAD', 'DEV_RELOAD_TOKEN',
                'ALLOW_REMOTE_RELOAD', 'ALLOW_REMOTE_RELOAD_IPS']
        out = {}
        for k in keys:
            try:
                out[k] = dbm.get_setting(k)
            except Exception as e:
                out[k] = f'ERROR: {e}'
        write('settings_dump.json', json.dumps(
            out, ensure_ascii=False, indent=2) + '\n')
    except Exception as e:
        write('settings_dump.json', 'ERROR: ' +
              str(e) + '\n' + traceback.format_exc())


def main():
    token = read_token()
    tail_server_log()
    open_port = check_port()
    dump_settings()
    post_ok = post_reload(token)
    summary = {
        'token_present': bool(token),
        'port_open': open_port,
        'post_attempted': post_ok,
    }
    write('check_reload_summary.json', json.dumps(
        summary, ensure_ascii=False, indent=2) + '\n')
    print('DONE')


if __name__ == '__main__':
    main()
