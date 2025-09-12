"""Run a smoke test that posts README.md as upload and prints job id and status."""
import os
import sys
import time

# Ensure project root on sys.path when run from scripts/
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.web.app_factory import create_app


app = create_app()
client = app.test_client()

with open('README.md', 'rb') as f:
    resp = client.post('/api/upload/stream', data={'file': (f, 'README.md')})
    print('upload response:', resp.status_code, resp.get_json())
    job = resp.get_json().get('job_id')
    if job:
        time.sleep(1)
        s = client.get(f'/api/upload/job/{job}')
        print('job status:', s.status_code, s.get_json())
