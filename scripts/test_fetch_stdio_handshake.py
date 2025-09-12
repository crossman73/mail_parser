"""Attempt a stdio handshake with mcp_server_fetch.
 - Start server as subprocess with pipes
 - Try to locate mcp.client connect helpers and use them if available
 - Otherwise send a small probe and read response
"""
import inspect
import os
import subprocess
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'temp_fetch_handshake_out.txt')
ERR = os.path.join(ROOT, 'temp_fetch_handshake_err.txt')
PY = sys.executable
cmd = [PY, '-u', '-m', 'mcp_server_fetch', '--ignore-robots-txt']
print('Running:', ' '.join(cmd))
# start process with pipes
p = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
print('Started PID', p.pid)
# give it a moment to initialize
time.sleep(0.5)
# dump a bit of stderr if present
try:
    stderr_bytes = p.stderr.read1(4096) if hasattr(
        p.stderr, 'read1') else p.stderr.read(4096)
    print('initial stderr:', stderr_bytes.decode('utf-8', errors='replace'))
except Exception as e:
    print('stderr read failed:', e)
# attempt to import mcp client helpers (robust across mcp versions)
client_used = None
try:
    import importlib
    cl = importlib.import_module('mcp.client')
    names = [n for n in dir(cl) if not n.startswith('_')]
    print('mcp.client members sample:', names[:40])
    # candidate functions that might accept stdio streams (lib authors vary)
    candidates = ['connect_stdio', 'connect', 'create_client',
                  'connect_stdio_client', 'connect_streams', 'open_stdio']
    for c in candidates:
        if c in names:
            func = getattr(cl, c)
            print('Found candidate client function:', c)
            try:
                print('Signature:', inspect.signature(func))
            except Exception:
                pass
            client_used = ('client', c)
            break
except Exception as e:
    print('mcp.client import failed or none:', repr(e))
# If we didn't find a helper, try highlevel
if not client_used:
    try:
        ch = importlib.import_module('mcp.client')
        names = [n for n in dir(ch) if not n.startswith('_')]
        print('mcp.client members sample:', names[:40])
        # look for stdio helpers
        for c in ['connect', 'create_client', 'open_stdio']:
            if c in names:
                print('Found candidate in mcp.client:', c)
                client_used = ('client', c)
                break
    except Exception as e:
        print('mcp.client import failed or none:', repr(e))
# If we found a client helper, report and do not attempt unknown calls — just show availability
if client_used:
    print('Client helper available:', client_used)
    # try quick probe: send newline and read
    try:
        p.stdin.write(b"\n")
        p.stdin.flush()
        time.sleep(0.3)
        out = p.stdout.read1(4096) if hasattr(
            p.stdout, 'read1') else p.stdout.read(4096)
        print('Probe response:', out.decode('utf-8', errors='replace'))
    except Exception as e:
        print('Probe failed:', e)
else:
    print('No client API detected; performing raw probe (send newline and read)')
    try:
        p.stdin.write(b"\n")
        p.stdin.flush()
        time.sleep(0.5)
        out = p.stdout.read1(4096) if hasattr(
            p.stdout, 'read1') else p.stdout.read(4096)
        print('Raw probe response:', out.decode('utf-8', errors='replace'))
    except Exception as e:
        print('Raw probe failed:', e)
# cleanup
try:
    p.terminate()
    p.wait(timeout=3)
except Exception:
    p.kill()
print('Done; exitcode', p.returncode)
