import json
from collections import Counter

def summarize(path):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    total = len(data)
    typecnt = Counter(item.get('type') for item in data)
    symcnt = Counter(item.get('symbol') for item in data)
    filecnt = Counter(item.get('path') for item in data)

    print(f"Pylint total issues: {total}")
    print('Counts by type:')
    for t,c in typecnt.most_common():
        print(f" - {t}: {c}")

    print('\nTop symbols:')
    for s,c in symcnt.most_common(20):
        print(f" - {s}: {c}")

    print('\nTop files:')
    for f,c in filecnt.most_common(20):
        print(f" - {f}: {c}")

if __name__ == '__main__':
    import sys
    p = sys.argv[1] if len(sys.argv) > 1 else 'pylint_report_after_inithook.json'
    summarize(p)
