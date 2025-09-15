"""Ensure all tools/*.py scripts insert project root into sys.path before importing local 'src' packages.

Usage:
    python tools/fix_tools_headers.py --apply   # apply fixes
    python tools/fix_tools_headers.py          # dry-run

This script is idempotent and safe to run repeatedly.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = list((ROOT / 'tools').glob('*.py'))

HEADER = (
    "from pathlib import Path\n"
    "import sys\n\n"
    "# Ensure project root is on sys.path so local `src` package can be imported\n"
    "project_root = Path(__file__).resolve().parents[1]\n"
    "if str(project_root) not in sys.path:\n"
    "    sys.path.insert(0, str(project_root))\n\n"
)

SRC_IMPORT_RE = re.compile(r"^\s*(from|import)\s+src[\.|\s]", re.M)

changes = []
for p in TOOLS:
    text = p.read_text(encoding='utf-8')
    # if header already present at top, skip
    if text.startswith(HEADER):
        continue
    # find first occurrence of import from src
    m = SRC_IMPORT_RE.search(text)
    if not m:
        # nothing to do
        continue
    # if there's already a project_root insertion anywhere, skip
    if 'project_root = Path(__file__).resolve().parents[1]' in text:
        # ensure it's before the first src import
        idx_header = text.find(
            'project_root = Path(__file__).resolve().parents[1]')
        if idx_header < m.start():
            continue
    changes.append(p)

if not changes:
    print('No files to fix.')
    sys.exit(0)

print('Files to fix:')
for p in changes:
    print(' -', p)

if '--apply' not in sys.argv:
    print('\nRun with --apply to modify these files.')
    sys.exit(0)

for p in changes:
    text = p.read_text(encoding='utf-8')
    # remove an existing header if present later in file
    text = text.replace(HEADER, '')
    # insert HEADER before first src import
    m = SRC_IMPORT_RE.search(text)
    new_text = text[:m.start()] + HEADER + text[m.start():]
    p.write_text(new_text, encoding='utf-8')
    print('Patched', p)

print('Done.')
