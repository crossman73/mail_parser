import sys

import psutil

pid = int(sys.argv[1])
try:
    p = psutil.Process(pid)
    print('killing', p.pid, p.cmdline())
    p.terminate()
    p.wait(3)
    print('terminated')
except Exception as e:
    print('error', e)
