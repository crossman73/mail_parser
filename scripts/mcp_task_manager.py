#!/usr/bin/env python3
"""Small task manager: create local task files and record MCP availability.
Usage:
  python scripts/mcp_task_manager.py add "Title" "Description"
  python scripts/mcp_task_manager.py list

This writes tasks to tasks/mcp_tasks/*.json and, if `mcp` is importable,
writes `tasks/mcp_tasks/mcp_capabilities.json` with detected members.
"""
import importlib
import json
import sys
import uuid
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS_DIR = ROOT / 'tasks' / 'mcp_tasks'
TASKS_DIR.mkdir(parents=True, exist_ok=True)


def detect_mcp_capabilities():
    try:
        m = importlib.import_module('mcp')
        names = [n for n in dir(m) if not n.startswith('_')]
        return {'module': 'mcp', 'file': getattr(m, '__file__', None), 'members': names}
    except Exception as e:
        return {'module': 'mcp', 'error': repr(e)}


def add_task(title, description):
    task = {
        'id': str(uuid.uuid4()),
        'title': title,
        'description': description,
        'status': 'pending',
        'created_at': datetime.utcnow().isoformat() + 'Z'
    }
    path = TASKS_DIR / f"{task['id']}.json"
    with path.open('w', encoding='utf-8') as f:
        json.dump(task, f, ensure_ascii=False, indent=2)
    print('Wrote task:', path)
    return path


def list_tasks():
    entries = sorted(TASKS_DIR.glob('*.json'))
    for p in entries:
        try:
            t = json.loads(p.read_text(encoding='utf-8'))
            print(p.name, t.get('status'), '-', t.get('title'))
        except Exception:
            print(p.name, ' <invalid>')


def main(argv):
    if len(argv) < 2:
        print('Usage: add "Title" "Description" | list')
        return 1

    cmd = argv[1]
    if cmd == 'add':
        if len(argv) < 4:
            print('Usage: add "Title" "Description"')
            return 1
        title = argv[2]
        desc = argv[3]
        task_path = add_task(title, desc)
        cap = detect_mcp_capabilities()
        cap_path = TASKS_DIR / 'mcp_capabilities.json'
        with cap_path.open('w', encoding='utf-8') as f:
            json.dump(cap, f, ensure_ascii=False, indent=2)
        print('Wrote MCP capabilities to:', cap_path)
        return 0
    elif cmd == 'list':
        list_tasks()
        return 0
    else:
        print('Unknown command:', cmd)
        return 2


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
