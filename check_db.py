import sqlite3

conn = sqlite3.connect('data/db/court_evidence.db')
cursor = conn.cursor()

# API 관련 테이블 확인
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'api%' ORDER BY name")
tables = cursor.fetchall()
print("API 관련 테이블:")
for t in tables:
    print(f"  - {t[0]}")

# 스키마 버전 확인
cursor.execute("SELECT * FROM schema_version ORDER BY version DESC LIMIT 1")
ver = cursor.fetchone()
print(f"\n현재 스키마 버전: {ver[0]}")
print(f"설명: {ver[2]}")

# api_test_executions 테이블 구조 확인
print("\napi_test_executions 테이블 구조:")
cursor.execute("PRAGMA table_info(api_test_executions)")
columns = cursor.fetchall()
for col in columns:
    print(f"  - {col[1]} ({col[2]})")

conn.close()
