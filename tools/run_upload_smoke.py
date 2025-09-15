"""Run a smoke test that posts README.md as upload and prints job id and status."""
from src.web.app_factory import create_app
import os
import sys
import time
from pathlib import Path

# Ensure project root on sys.path when run from tools/
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


app = create_app()
client = app.test_client()

readme_path = project_root / 'README.md'
if not readme_path.exists():
    raise FileNotFoundError(
        f"README.md not found at expected location: {readme_path}")

with open(str(readme_path), 'rb') as f:
    # use canonical API upload endpoint; UI uses /upload but API is under /api/
    resp = client.post('/api/upload/stream', data={'file': (f, 'README.md')})
    try:
        json_body = resp.get_json()
    except Exception:
        json_body = None
    print('upload response:', resp.status_code, json_body)
    job = (json_body or {}).get('job_id') if isinstance(
        json_body, dict) else None
    if job:
        time.sleep(1)
        s = client.get(f'/api/upload/job/{job}')
        print('job status:', s.status_code, s.get_json())
