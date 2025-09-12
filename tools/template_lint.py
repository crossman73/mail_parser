"""Simple Jinja2 template linter.

Usage:
  python tools/template_lint.py [templates_dir]

Exits with code 0 when no syntax errors found, otherwise prints errors and exits 1.
"""
import os
import sys

from jinja2 import Environment, FileSystemLoader, TemplateSyntaxError


def lint_templates(templates_dir: str) -> int:
    env = Environment(loader=FileSystemLoader(templates_dir))
    errors = []
    for root, dirs, files in os.walk(templates_dir):
        for f in files:
            if not f.endswith('.html') and not f.endswith('.jinja'):
                continue
            path = os.path.join(root, f)
            rel = os.path.relpath(path, templates_dir)
            try:
                with open(path, 'r', encoding='utf-8') as fh:
                    src = fh.read()
                # parse will raise TemplateSyntaxError for syntax problems
                env.parse(src)
            except TemplateSyntaxError as e:
                errors.append((rel, e.lineno, str(e)))
            except Exception as e:
                errors.append((rel, None, f'Unexpected error: {e}'))

    if not errors:
        print('✅ No template syntax errors found.')
        return 0

    print('❌ Template syntax errors:')
    for rel, lineno, msg in errors:
        loc = f':{lineno}' if lineno else ''
        print(f' - {rel}{loc} -> {msg}')
    return 1


if __name__ == '__main__':
    templates_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(__file__), '..', 'templates')
    templates_dir = os.path.abspath(templates_dir)
    if not os.path.isdir(templates_dir):
        print(f'Templates directory not found: {templates_dir}')
        sys.exit(2)
    rc = lint_templates(templates_dir)
    sys.exit(rc)
