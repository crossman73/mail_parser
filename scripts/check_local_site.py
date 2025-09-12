import time
import urllib.request

url = 'http://127.0.0.1:5000/'

# 짧게 대기하여 서버가 시작할 시간을 줌
time.sleep(2)
try:
    with urllib.request.urlopen(url, timeout=5) as r:
        print('status', r.status)
        body = r.read(1024).decode('utf-8', errors='replace')
        print('body_preview:\n', body[:500])
except Exception as e:
    print('error', e)
