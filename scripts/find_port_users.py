import psutil

for conn in psutil.net_connections(kind='inet'):
    if conn.laddr and conn.laddr.port == 5000:
        try:
            p = psutil.Process(conn.pid)
            print('PID', p.pid, 'name', p.name(), 'cmd', p.cmdline())
        except Exception as e:
            print('err', e)
