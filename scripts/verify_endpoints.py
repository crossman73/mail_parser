from src.web.app_factory import create_app
import json
import sys
from pathlib import Path

# ensure project root on path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))


app = create_app()
client = app.test_client()

print('Requesting /health')
resp = client.get('/health')
print('status_code:', resp.status_code)
try:
    print(json.dumps(resp.get_json(), ensure_ascii=False, indent=2))
except Exception:
    print(resp.data.decode('utf-8'))

print('\nRequesting /system/status')
resp2 = client.get('/system/status')
print('status_code:', resp2.status_code)
try:
    print(json.dumps(resp2.get_json(), ensure_ascii=False, indent=2))
except Exception:
    print(resp2.data.decode('utf-8'))
