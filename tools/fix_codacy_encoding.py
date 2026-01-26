#!/usr/bin/env python3
import re
from pathlib import Path
import sys

LOG_PATH = Path('/mnt/c/dev/python-email/codacy_run.log')
ENCODINGS = ['utf-8', 'utf-16', 'utf-16-le', 'utf-16-be', 'utf-32', 'latin-1', 'cp1252']

def find_malformed_files(log_path):
    if not log_path.exists():
        print(f'Log not found: {log_path}')
        return []
    text = log_path.read_text(errors='ignore')
    pattern = re.compile(r'Failed to read file (.+)\s')
    matches = pattern.findall(text)
    # normalize and dedupe
    files = []
    for m in matches:
        p = Path(m.strip())
        if p.exists() and p not in files:
            files.append(p)
    return files


def try_fix_file(path: Path):
    print(f'Processing: {path}')
    b = path.read_bytes()
    for enc in ENCODINGS:
        try:
            s = b.decode(enc)
        except Exception:
            continue
        # if decoded with utf-8 already, skip
        if enc == 'utf-8':
            print(f' - already utf-8: {enc}')
            return True, enc
        # backup
        bak = path.with_suffix(path.suffix + '.bak')
        if not bak.exists():
            path.rename(bak)
            bak.write_bytes(b)
            # write utf-8
            path.write_text(s, encoding='utf-8')
            print(f' - converted from {enc} -> utf-8, backup: {bak}')
            return True, enc
        else:
            print(f' - backup exists ({bak}), skipping rename; will overwrite file in-place')
            path.write_text(s, encoding='utf-8')
            print(f' - converted from {enc} -> utf-8 (in-place)')
            return True, enc
    print(' - failed to decode with common encodings')
    return False, None


def main():
    files = find_malformed_files(LOG_PATH)
    if not files:
        print('No malformed-file entries found in log.')
        return 0
    report = []
    for p in files:
        ok, enc = try_fix_file(p)
        report.append((str(p), ok, enc))
    print('\nSummary:')
    for p, ok, enc in report:
        print(f'{p}: fixed={ok}, detected_encoding={enc}')
    # write report file
    out = Path('/mnt/c/dev/python-email/codacy_encoding_fix_report.txt')
    with out.open('w', encoding='utf-8') as f:
        for p, ok, enc in report:
            f.write(f'{p}\tfixed={ok}\tdetected={enc}\n')
    print(f'Wrote report to: {out}')
    return 0

if __name__ == '__main__':
    sys.exit(main())
