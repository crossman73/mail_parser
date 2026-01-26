"""
Attempt conservative automatic fixes for import-error issues reported by pylint.

Strategy:
- Parse `pylint_report_after_inithook.json` for items with symbol 'import-error'.
- For each file, replace occurrences of:
  - "from src." -> "from <dots>" where <dots> is computed per file depth
  - "import src." -> convert to "from <dots>... import ..." when possible

This is a heuristic and should be reviewed before committing.
"""
import json
from pathlib import Path
import re

REPORT = Path('pylint_report_after_inithook.json')

def compute_dots(path: Path) -> str:
    # path is like src/dir1/dir2/file.py
    rel = path.parts
    try:
        idx = rel.index('src')
    except ValueError:
        # not under src
        return ''
    # parts after 'src', excluding the file name
    after = rel[idx+1:-1]
    package_depth = len(after)
    dot_count = package_depth + 1
    return '.' * dot_count

def fix_file(path: Path):
    text = path.read_text(encoding='utf-8')
    dots = compute_dots(path)
    if not dots:
        return False

    orig = text
    # from src.xxx import yyy  -> from <dots>xxx import yyy
    text = re.sub(r'from\s+src\.', f'from {dots}', text)

    # import src.xxx.sub -> from <dots>xxx import sub
    def repl_import(m):
        full = m.group(1)
        parts = full.split('.')
        if len(parts) >= 2:
            pkg = parts[1]
            rest = '.'.join(parts[2:])
            if rest:
                return f'from {dots}{pkg} import {rest}'
            else:
                return f'from {dots}{pkg} import {pkg}'
        return m.group(0)

    text = re.sub(r'import\s+src\.([\w\.]+)', repl_import, text)

    if text != orig:
        backup = path.with_suffix(path.suffix + '.bak')
        backup.write_text(orig, encoding='utf-8')
        path.write_text(text, encoding='utf-8')
        return True
    return False

def main():
    if not REPORT.exists():
        print('Report not found:', REPORT)
        return
    data = json.loads(REPORT.read_text(encoding='utf-8'))
    files = sorted({item['path'] for item in data if item.get('symbol') == 'import-error'})
    print('Files to process:', len(files))
    changed = []
    for f in files:
        p = Path(f)
        if p.exists():
            ok = fix_file(p)
            if ok:
                changed.append(f)
                print('Fixed:', f)
            else:
                print('No change needed:', f)
        else:
            print('File missing:', f)
    print('Total changed:', len(changed))

if __name__ == '__main__':
    main()
