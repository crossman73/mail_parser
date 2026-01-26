#!/usr/bin/env python3
"""court_evidence.db의 데이터를 email_parser.db로 마이그레이션 후 삭제"""

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


def migrate_databases():
    source_db = "data/db/court_evidence.db"  # 소스 (삭제 예정)
    target_db = "data/db/email_parser.db"    # 타겟 (유지)
    backup_source = f"data/db/court_evidence.db.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    backup_target = f"data/db/email_parser.db.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    print(f"🔄 DB 마이그레이션 시작...")
    print(f"  Source (삭제 예정): {source_db}")
    print(f"  Target (유지): {target_db}")

    # 백업
    print(f"\n📦 백업 생성...")
    shutil.copy2(source_db, backup_source)
    print(f"  ✅ {backup_source}")
    shutil.copy2(target_db, backup_target)
    print(f"  ✅ {backup_target}")

    # 연결
    source_conn = sqlite3.connect(source_db)
    target_conn = sqlite3.connect(target_db)

    source_cursor = source_conn.cursor()
    target_cursor = target_conn.cursor()

    # system_tests 마이그레이션
    print(f"\n📋 system_tests 마이그레이션...")
    source_cursor.execute("SELECT * FROM system_tests")
    tests = source_cursor.fetchall()

    # 테이블 구조 확인
    source_cursor.execute("PRAGMA table_info(system_tests)")
    columns = [col[1] for col in source_cursor.fetchall()]
    print(f"  컬럼: {columns}")

    for test in tests:
        placeholders = ','.join(['?'] * len(test))
        target_cursor.execute(f"INSERT OR IGNORE INTO system_tests VALUES ({placeholders})", test)
    print(f"  ✅ {len(tests)}개 행 마이그레이션")

    # test_executions 마이그레이션
    print(f"\n📋 test_executions 마이그레이션...")
    source_cursor.execute("SELECT * FROM test_executions")
    executions = source_cursor.fetchall()

    source_cursor.execute("PRAGMA table_info(test_executions)")
    columns = [col[1] for col in source_cursor.fetchall()]
    print(f"  컬럼: {columns}")

    for execution in executions:
        placeholders = ','.join(['?'] * len(execution))
        target_cursor.execute(f"INSERT OR IGNORE INTO test_executions VALUES ({placeholders})", execution)
    print(f"  ✅ {len(executions)}개 행 마이그레이션")

    # system_settings 마이그레이션 (있다면)
    try:
        source_cursor.execute("SELECT * FROM system_settings")
        settings = source_cursor.fetchall()

        # target에 테이블이 없으면 생성
        source_cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='system_settings'")
        create_sql = source_cursor.fetchone()
        if create_sql:
            target_cursor.execute(create_sql[0])

        print(f"\n📋 system_settings 마이그레이션...")
        for setting in settings:
            placeholders = ','.join(['?'] * len(setting))
            target_cursor.execute(f"INSERT OR IGNORE INTO system_settings VALUES ({placeholders})", setting)
        print(f"  ✅ {len(settings)}개 행 마이그레이션")
    except Exception as e:
        print(f"  ⚠️ system_settings 건너뛰기: {e}")

    # settings_history 마이그레이션 (있다면)
    try:
        source_cursor.execute("SELECT * FROM settings_history")
        history = source_cursor.fetchall()

        # target에 테이블이 없으면 생성
        source_cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='settings_history'")
        create_sql = source_cursor.fetchone()
        if create_sql:
            target_cursor.execute(create_sql[0])

        print(f"\n📋 settings_history 마이그레이션...")
        for record in history:
            placeholders = ','.join(['?'] * len(record))
            target_cursor.execute(f"INSERT OR IGNORE INTO settings_history VALUES ({placeholders})", record)
        print(f"  ✅ {len(history)}개 행 마이그레이션")
    except Exception as e:
        print(f"  ⚠️ settings_history 건너뛰기: {e}")

    # 커밋 및 종료
    target_conn.commit()
    source_conn.close()
    target_conn.close()

    print(f"\n✅ 마이그레이션 완료!")
    print(f"\n📊 결과 확인:")

    # 결과 확인
    check_conn = sqlite3.connect(target_db)
    check_cursor = check_conn.cursor()

    check_cursor.execute("SELECT COUNT(*) FROM system_tests")
    print(f"  - system_tests: {check_cursor.fetchone()[0]}개")

    check_cursor.execute("SELECT COUNT(*) FROM test_executions")
    print(f"  - test_executions: {check_cursor.fetchone()[0]}개")

    try:
        check_cursor.execute("SELECT COUNT(*) FROM system_settings")
        print(f"  - system_settings: {check_cursor.fetchone()[0]}개")
    except:
        pass

    try:
        check_cursor.execute("SELECT COUNT(*) FROM settings_history")
        print(f"  - settings_history: {check_cursor.fetchone()[0]}개")
    except:
        pass

    try:
        check_cursor.execute("SELECT COUNT(*) FROM api_endpoints")
        print(f"  - api_endpoints: {check_cursor.fetchone()[0]}개")
    except:
        pass

    try:
        check_cursor.execute("SELECT COUNT(*) FROM api_test_executions")
        print(f"  - api_test_executions: {check_cursor.fetchone()[0]}개")
    except:
        pass

    check_conn.close()

    return True


def delete_source_db():
    """마이그레이션 확인 후 소스 DB 삭제"""
    source_db = Path("data/db/court_evidence.db")

    if source_db.exists():
        source_db.unlink()
        print(f"\n🗑️ 소스 DB 삭제 완료: {source_db}")
        return True
    return False


if __name__ == "__main__":
    import sys

    success = migrate_databases()

    if success:
        print("\n" + "=" * 60)
        response = input("마이그레이션 결과를 확인하셨습니까? court_evidence.db를 삭제하시겠습니까? (y/N): ")
        if response.lower() == 'y':
            delete_source_db()
            print("\n✅ DB 통합 완료! email_parser.db만 사용합니다.")
        else:
            print("\n⚠️ 삭제 취소. 수동으로 삭제하세요: data/db/court_evidence.db")

if __name__ == '__main__':
    migrate_databases()
