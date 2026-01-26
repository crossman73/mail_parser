#!/usr/bin/env python3
"""두 DB 파일 비교"""

import sqlite3
from pathlib import Path


def check_db(db_path):
    print(f"\n{'='*60}")
    print(f"DB: {db_path}")
    print(f"{'='*60}")

    if not Path(db_path).exists():
        print("  ❌ 파일 없음")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 테이블 목록
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"\n📋 테이블 목록 ({len(tables)}개):")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  - {table}: {count}개 행")

        # 주요 테이블 샘플 데이터
        if 'test_executions' in tables:
            print(f"\n🔍 test_executions 샘플:")
            cursor.execute("SELECT id, test_id, execution_time, status FROM test_executions LIMIT 3")
            rows = cursor.fetchall()
            for row in rows:
                print(f"  {row}")

        if 'system_tests' in tables:
            print(f"\n🔍 system_tests 샘플:")
            cursor.execute("SELECT id, test_key, test_name FROM system_tests LIMIT 3")
            rows = cursor.fetchall()
            for row in rows:
                print(f"  {row}")

        if 'api_endpoints' in tables:
            print(f"\n🔍 api_endpoints 샘플:")
            cursor.execute("SELECT id, endpoint, method FROM api_endpoints LIMIT 3")
            rows = cursor.fetchall()
            for row in rows:
                print(f"  {row}")

        conn.close()

    except Exception as e:
        print(f"  ❌ 오류: {e}")

# 두 DB 확인
check_db("data/db/court_evidence.db")
check_db("data/db/email_parser.db")

print(f"\n{'='*60}")
print("결론:")
print("='*60}")
print("두 DB 파일이 존재하며, 코드에서 혼용되고 있을 수 있습니다.")
print("통합이 필요합니다.")
