import sys, json, urllib.request, urllib.error
sys.path.insert(0, r'C:\dev\python-email')
from src.core import db_manager

token = None
try:
    token = db_manager.get_setting('DEV_RELOAD_TOKEN')
except Exception:
    token = None

url = 'http://127.0.0.1:5000/admin/reload'
headers = {'Content-Type': 'application/json'}
if token:
    headers['X-DEV-RELOAD-TOKEN'] = token

data = json.dumps({'modules': ['src.web.admin_routes']}).encode('utf-8')
req = urllib.request.Request(url, data=data, headers=headers, method='POST')
result = {'attempt': url}
try:
    with urllib.request.urlopen(req, timeout=5) as r:
        result['status'] = r.getcode()
        result['body'] = r.read().decode('utf-8')
except urllib.error.HTTPError as e:
    try:
        b = e.read().decode('utf-8')
    except Exception:
        b = ''
    result['status'] = e.code
    result['body'] = b
except Exception as e:
    result['error'] = str(e)

# attach recent logs
try:
    logs = db_manager.list_logs(10)
    result['logs'] = logs
except Exception as e:
    result['logs_error'] = str(e)

open('temp/real_reload_call.json', 'w', encoding='utf-8').write(json.dumps(result, ensure_ascii=False, indent=2))
print('done')
