#!/usr/bin/env python3
"""테이블 차이 확인"""
import sqlite3

# court_evidence.db 테이블
conn1 = sqlite3.connect('data/db/court_evidence.db')
cur1 = conn1.cursor()
cur1.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables1 = set([r[0] for r in cur1.fetchall()])
conn1.close()

# email_parser.db 테이블
conn2 = sqlite3.connect('data/db/email_parser.db')
cur2 = conn2.cursor()
cur2.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables2 = set([r[0] for r in cur2.fetchall()])
conn2.close()

only_court = tables1 - tables2
only_email = tables2 - tables1
both = tables1 & tables2

print(f'court_evidence.db에만 있는 테이블: {only_court}')
print(f'email_parser.db에만 있는 테이블: {only_email}')
print(f'공통 테이블: {both}')
