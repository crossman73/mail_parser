import re
import json
import urllib.request
from urllib.error import HTTPError, URLError

BASE = 'http://localhost:5000'
endpoints = ['/', '/admin', '/additional_evidence']
results = {}

for ep in endpoints:
    url = BASE + ep
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            body = r.read(10240)
            results[ep] = {'status': r.status, 'len': len(
                body), 'snippet': body.decode('utf-8', 'replace')[:1000]}
    except HTTPError as he:
        results[ep] = {'status': he.code, 'error': str(he)}
    except URLError as ue:
        results[ep] = {'error': str(ue)}
    except Exception as e:
        results[ep] = {'error': str(e)}

# Try to get an evidence id from /admin page by simple extraction
admin_snippet = results.get('/admin', {}).get('snippet', '')

m = re.search(r'/admin/evidence/(\d+)', admin_snippet)
if m:
    eid = m.group(1)
    ep = f'/admin/evidence/{eid}'
    url = BASE + ep
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            body = r.read(10240)
            results[ep] = {'status': r.status, 'len': len(
                body), 'snippet': body.decode('utf-8', 'replace')[:1000]}
    except Exception as e:
        results[ep] = {'error': str(e)}
else:
    results['/admin/evidence/<id>'] = {
        'note': 'no id found in admin page snippet'}

with open('logs/web_checks.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print('WROTE logs/web_checks.json')
for k, v in results.items():
    print(k, v.get('status', v.get('error', v.get('note'))))
