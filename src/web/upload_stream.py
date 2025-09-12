import tempfile
import threading
import uuid
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request
from src.core import job_store

upload_bp = Blueprint('upload', __name__, url_prefix='/api')

# ---------------------------------------------------------------------------
# NOTE (로컬 개발자):
# 이 모듈은 RQ/Redis 큐를 이용하는 것을 전제로 구현되어 있습니다. 그러나
# 개발 로컬 환경에서 Docker/Redis를 실행할 수 없는(또는 자원이 부족한)
# 경우를 위해 'local_jobs'에 기반한 간단한 폴백을 제공합니다.
#
# 폴백 동작은 개발/테스트 용도로만 사용하세요. 프로덕션에서는 반드시
# Redis + RQ를 사용하고, 작업은 별도 워커 프로세스에서 실행해야 합니다.
#
# 배포시(스테이징/프로덕션) 반드시 수행할 작업:
#  - Redis 인스턴스 준비 및 보안 설정(TLS/ACL)
#  - RQ 워커를 별도의 프로세스로 운영하고 모니터링/재시작 정책 적용
#  - SQLite 대신 Postgres 등 프로덕션 DB로 전환
#  - 대용량 파일 처리를 위한 스트리밍/청크 처리 로직 강화
# ---------------------------------------------------------------------------

# In-memory fallback for environments without Redis/RQ
# Initialize job_store DB (safe no-op if already initialized)
job_store.init_db()


@upload_bp.route('/upload/stream', methods=['POST'])
def upload_stream():
    """Chunked upload endpoint skeleton.

    Expects chunked POST with file in request.files['file'] or raw body.
    This is a lightweight skeleton that writes to a temporary file and returns a job id placeholder.
    Integrate with background worker (RQ/Celery) in next steps.
    """
    try:
        # Prefer file field
        f = None
        if 'file' in request.files:
            f = request.files['file']
            tmp = tempfile.NamedTemporaryFile(
                delete=False, prefix='upload_', suffix='.mbox')
            f.save(tmp.name)
            tmp_path = tmp.name
        else:
            # Read raw body
            tmp = tempfile.NamedTemporaryFile(
                delete=False, prefix='upload_raw_', suffix='.mbox')
            with open(tmp.name, 'wb') as out:
                out.write(request.get_data())
            tmp_path = tmp.name

        # Try to enqueue background job using RQ; fallback to local thread if unavailable
        from src.tasks.worker_tasks import process_uploaded_mbox
        try:
            # Lazy import to avoid hard dependency at module import time
            # In production this branch should succeed and enqueue to Redis/RQ.
            from redis import Redis
            from rq import Queue

            redis_conn = Redis()
            q = Queue('default', connection=redis_conn)
            job = q.enqueue(process_uploaded_mbox, tmp_path)
            return jsonify({'status': 'accepted', 'job_id': job.get_id(), 'tmp_path': tmp_path}), 202
        except Exception as e:
            # If Redis isn't available, we fall back to a local background
            # thread. This is intentional for lightweight local development
            # environments, but it is NOT suitable for production use because:
            #  - No persistence of job state across process restarts
            #  - Single-process execution cannot scale
            #  - Potential blocking/resource exhaustion for large files
            current_app.logger.warning(
                f'RQ enqueue failed, falling back to local thread: {e}')
            # Fallback: run in a background thread and store status in local_jobs
            # Note: local_jobs is an in-memory dict and will be lost on restart.
            job_id = f"local-{uuid.uuid4().hex[:8]}"
            job_store.create_job(job_id, status='running', result=None)

            def _run_local():
                try:
                    res = process_uploaded_mbox(tmp_path)
                    job_store.update_job(job_id, status='completed', result=res)
                except Exception as ex:
                    job_store.update_job(job_id, status='failed', result={'error': str(ex)})

            t = threading.Thread(target=_run_local, daemon=True)
            t.start()
            return jsonify({'status': 'accepted', 'job_id': job_id, 'tmp_path': tmp_path, 'note': 'processed locally'}), 202
    except Exception as e:
        current_app.logger.error(f'upload_stream error: {e}')
        return jsonify({'status': 'error', 'message': str(e)}), 500


@upload_bp.route('/upload/job/<job_id>', methods=['GET'])
def job_status(job_id):
    # Check local_jobs fallback first
    # Check local SQLite-backed job store first
    jb = job_store.get_job(job_id)
    if jb:
        # result is stored as JSON string; try to parse
        try:
            import json
            res = json.loads(jb['result']) if jb['result'] else None
        except Exception:
            res = jb['result']
        return jsonify({'id': jb['id'], 'status': jb['status'], 'result': res}), 200

    # Otherwise try RQ Job fetch
    try:
        from redis import Redis
        from rq.job import Job
        redis_conn = Redis()
        job = Job.fetch(job_id, connection=redis_conn)
        return jsonify({'id': job.get_id(), 'status': job.get_status(), 'result': job.result}), 200
    except Exception as e:
        current_app.logger.error(f'job_status error: {e}')
        return jsonify({'status': 'error', 'message': str(e)}), 404
