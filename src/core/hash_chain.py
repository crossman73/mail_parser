"""Hash chain utilities for evidence integrity.

Provides:
- file_sha256(path): compute SHA-256 of a file using streaming
- build_hash_chain(file_paths): build a chain of hashes (file_hash + chain_hash)
- verify_hash_chain(chain_entries, verify_files=True): verify chain integrity and optionally file contents

Chain algorithm (simple, deterministic):
- file_hash = sha256(file_bytes)
- chain_hash[0] = file_hash[0]
- chain_hash[i] = sha256(chain_hash[i-1].encode('utf-8') + file_hash[i].encode('utf-8'))

This is lightweight and intended as a building block for evidence-chain features.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Dict, List


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha256(path: str | Path, chunk_size: int = 8192) -> str:
    """Compute SHA-256 for a file in streaming fashion.

    Args:
        path: file path
        chunk_size: read buffer size

    Returns:
        hex digest string
    """
    h = hashlib.sha256()
    p = Path(path)
    with p.open('rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def build_hash_chain(file_paths: List[str | Path]) -> List[Dict[str, Any]]:
    """Build a hash chain from ordered list of files.

    Returns a list of entries:
      { 'path': str(path), 'file_hash': <hex>, 'chain_hash': <hex> }
    """
    entries: List[Dict[str, Any]] = []
    prev_chain: str | None = None

    for p in file_paths:
        path = Path(p)
        file_hash = file_sha256(path)
        if prev_chain is None:
            chain_hash = file_hash
        else:
            chain_hash = sha256_bytes(prev_chain.encode(
                'utf-8') + file_hash.encode('utf-8'))
        entries.append({
            'path': str(path),
            'file_hash': file_hash,
            'chain_hash': chain_hash,
        })
        prev_chain = chain_hash

    return entries


def verify_hash_chain(entries: List[Dict[str, Any]], verify_files: bool = True) -> bool:
    """Verify hash chain entries.

    If verify_files is True, recompute file hashes and compare.
    Returns True if all checks pass, False otherwise.
    """
    prev_chain: str | None = None
    for entry in entries:
        file_path = Path(entry['path'])
        expected_file_hash = entry.get('file_hash')
        expected_chain_hash = entry.get('chain_hash')

        if verify_files:
            if not file_path.exists():
                return False
            actual_file_hash = file_sha256(file_path)
            if actual_file_hash != expected_file_hash:
                return False

        if prev_chain is None:
            computed_chain = expected_file_hash
        else:
            computed_chain = sha256_bytes(prev_chain.encode(
                'utf-8') + expected_file_hash.encode('utf-8'))

        if computed_chain != expected_chain_hash:
            return False

        prev_chain = computed_chain

    return True
