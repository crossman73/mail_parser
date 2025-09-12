import ast
import os

HEAVY_MODULES = {'numpy', 'openpyxl', 'pandas', 'scipy', 'matplotlib'}

report = []
for root, dirs, files in os.walk('src'):
    for fn in files:
        if not fn.endswith('.py'):
            continue
        path = os.path.join(root, fn)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                src = f.read()
            tree = ast.parse(src)
            for node in tree.body:
                if isinstance(node, ast.Import):
                    for n in node.names:
                        if n.name.split('.')[0] in HEAVY_MODULES:
                            report.append(f"{path}: top-level import {n.name}")
                elif isinstance(node, ast.ImportFrom):
                    mod = (node.module or '')
                    if mod.split('.')[0] in HEAVY_MODULES:
                        report.append(
                            f"{path}: top-level from {mod} import ...")
        except Exception as e:
            report.append(f"{path}: parse error: {e}")

with open('import_issues_report.txt', 'w', encoding='utf-8') as f:
    if report:
        f.write('\n'.join(report))
    else:
        f.write('no heavy top-level imports found')

print('wrote import_issues_report.txt')
