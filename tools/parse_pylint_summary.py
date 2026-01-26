#!/usr/bin/env python3
import json
import collections

P='pylint_report_after_deps.json'
OUT='pylint_summary.txt'
with open(P,'r',encoding='utf-8') as f:
    data=json.load(f)
order={'error':0,'warning':1,'refactor':2,'convention':3,'info':4}
by_type=collections.Counter()
by_symbol=collections.Counter()
by_path=collections.Counter()
for e in data:
    t=e.get('type','')
    by_type[t]+=1
    by_symbol[e.get('symbol','')]+=1
    by_path[e.get('path','')]+=1

def keyfn(e):
    t=e.get('type','')
    return (order.get(t,9), e.get('path',''), e.get('line',0))

items=sorted(data, key=keyfn)
summary_lines=[]
summary_lines.append(f"Pylint total issues: {len(data)}")
summary_lines.append('Counts by type:')
for k,v in by_type.most_common():
    summary_lines.append(f" - {k}: {v}")
summary_lines.append('Top symbols:')
for k,v in by_symbol.most_common(20):
    summary_lines.append(f" - {k}: {v}")
summary_lines.append('Top files:')
for p,v in by_path.most_common(20):
    summary_lines.append(f" - {p}: {v}")
summary_lines.append('\nTop 50 individual issues:')
for i,e in enumerate(items[:50],1):
    summary_lines.append(f"{i:2d}. {e.get('type')}: {e.get('path')}:{e.get('line')} - {e.get('symbol')} - {e.get('message')}")

with open(OUT,'w',encoding='utf-8') as f:
    f.write('\n'.join(summary_lines))

print('\n'.join(summary_lines[:40]))
print('\nSaved summary to', OUT)
