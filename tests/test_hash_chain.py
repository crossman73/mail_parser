import os
import tempfile

from src.core import hash_chain


def test_hash_chain_basic(tmp_path):
    # create 3 small files
    files = []
    for i in range(3):
        p = tmp_path / f"file_{i}.txt"
        p.write_text(f"sample content {i}")
        files.append(str(p))

    entries = hash_chain.build_hash_chain(files)
    assert len(entries) == 3

    # verify chain structure
    for e in entries:
        assert 'file_hash' in e and 'chain_hash' in e and 'path' in e

    assert hash_chain.verify_hash_chain(entries, verify_files=True) is True

    # tamper a file
    with open(files[1], 'w') as f:
        f.write('tampered')

    assert hash_chain.verify_hash_chain(entries, verify_files=True) is False
