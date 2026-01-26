#!/usr/bin/env python3
import json
import re
from collections import Counter
import sys
import os

p = 'pylint_report4.json'
if not os.path.exists(p):
    print('ERROR: file not found', p)
    sys.exit(1)
try:
    s = open(p, 'r', encoding='utf-8').read()
except Exception as e:
    print('ERROR loading', p, e)
    sys.exit(1)

names = re.findall(r"Unable to import '([^']+)'", s, flags=re.I)
print('Top missing import names:')
for name, count in Counter(names).most_common(30):
    print(f"{count:4d}  {name}")

modules = [m.group(1) for m in re.finditer(r'"module":\s*"([^"]+)"[\s\S]*?"symbol":\s*"import-error"', s)]
print('\nTop modules with import-error:')
for mod, count in Counter(modules).most_common(30):
    print(f"{count:4d}  {mod}")
