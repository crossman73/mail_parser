"""Start mcp_server_fetch as a subprocess, wait, verify it's alive, then cleanup.
Run: python .\scripts\test_fetch_smoke.py
"""
import os
import subprocess
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'temp_fetch_out.txt')
ERR = os.path.join(ROOT, 'temp_fetch_err.txt')
print('Using python:', sys.executable)
cmd = [sys.executable, '-u', '-m', 'mcp_server_fetch', '--ignore-robots-txt']
print('Command:', ' '.join(cmd))
with open(OUT, 'wb') as outf, open(ERR, 'wb') as errf:
    p = subprocess.Popen(cmd, stdout=outf, stderr=errf)
    print('Started PID', p.pid)
    try:
        time.sleep(3)
        alive = (p.poll() is None)
        print('Alive after 3s:', alive)
        if not alive:
            print('Process exited early with returncode', p.returncode)
        else:
            print('Terminating process...')
            p.terminate()
            try:
                p.wait(timeout=5)
            except Exception:
                p.kill()
        # print tails
        print('\n---- STDOUT tail ----')
        try:
            with open(OUT, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()[-200:]
                print(''.join(lines))
        except Exception as e:
            print('Could not read stdout file:', e)
        print('\n---- STDERR tail ----')
        try:
            with open(ERR, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()[-200:]
                print(''.join(lines))
        except Exception as e:
            print('Could not read stderr file:', e)
    finally:
        if p.poll() is None:
            p.kill()
        print('Done')
