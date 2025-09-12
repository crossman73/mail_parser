from src.core import db_manager, evidence_store
import os
import sys
from pathlib import Path

import pytest

# Ensure project root is on sys.path so tests can import `src` package when
# pytest is executed from the repo root or CI.
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_save_evidence_integration(tmp_path):
    """Integration test: save_evidence writes chain entries and sets integrity_hash.

    Uses separate test DB files under data/ to avoid polluting main DBs.
    If environment variable KEEP_TEST_ARTIFACTS is set to a truthy value, test DB files are kept for inspection.
    """
    # prepare test DB paths
    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)
    test_evidence_db = data_dir / 'evidence_test.db'
    test_job_db = data_dir / 'job_store_test.db'

    # ensure clean start
    for p in (test_evidence_db, test_job_db):
        if p.exists():
            p.unlink()

    # init DBs pointing to test files
    db_manager.init_all(evidence_path=test_evidence_db,
                        job_store_path=test_job_db)

    # create a temp file to act as evidence
    tmp_file = tmp_path / 'sample.txt'
    tmp_file.write_text('integration test content', encoding='utf-8')

    metadata = {
        'evidence_number': 'TEST-001',
        'subject': 'integration test'
    }

    eid, entries = db_manager.save_evidence(metadata, [str(tmp_file)])

    # basic assertions about returned values
    assert eid is not None
    assert isinstance(entries, list)
    assert len(entries) == 1
    assert 'chain_hash' in entries[0]

    # fetch evidence record from the test DB and verify integrity_hash was set
    rec = evidence_store.get_evidence(eid)
    assert rec is not None
    assert rec.get('integrity_hash') is not None

    # verify chain entries exist for this evidence id
    chain = evidence_store.list_chain_entries(eid)
    assert len(chain) == 1
    assert chain[0]['chain_hash'] == entries[0]['chain_hash']

    # cleanup test DBs unless the environment requests they be kept
    keep = os.environ.get('KEEP_TEST_ARTIFACTS')
    if not keep:
        try:
            test_evidence_db.unlink()
        except Exception:
            pass
        try:
            test_job_db.unlink()
        except Exception:
            pass


if __name__ == '__main__':
    pytest.main([__file__])
