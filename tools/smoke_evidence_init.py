from src.mail_parser.evidence_generator import EvidenceGenerator
import logging
import os
import sqlite3
import sys
from pathlib import Path

# Ensure project root is on sys.path when running from tools/
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


class Dummy:
    def __init__(self):
        self.mbox = None
        self.logger = logging.getLogger('dummy')


if __name__ == '__main__':
    d = Dummy()
    eg = EvidenceGenerator(d)
    print('EvidenceGenerator initialized ok')
    print('DB exists:', os.path.exists('data/evidence.db'))
    conn = sqlite3.connect('data/evidence.db')
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    print('tables:', cur.fetchall())
    conn.close()
