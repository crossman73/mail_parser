"""
DB 마이그레이션: system_settings에 created_at 컬럼 추가
"""
import sqlite3
from pathlib import Path


def migrate_created_at():
    db_path = Path(__file__).parent.parent / 'data' / 'db' / 'email_parser.db'

    print(f"DB 경로: {db_path}")
    print(f"DB 존재: {db_path.exists()}")

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    try:
        # 1. 컬럼이 이미 존재하는지 확인
        cursor.execute("PRAGMA table_info(system_settings)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"\n현재 컬럼: {columns}")

        if 'created_at' in columns:
            print("\n✅ created_at 컬럼이 이미 존재합니다.")
            return

        # 2. created_at 컬럼 추가 (updated_at을 기본값으로 사용)
        print("\n🔧 created_at 컬럼 추가 중...")
        cursor.execute("""
            ALTER TABLE system_settings
            ADD COLUMN created_at TEXT
        """)

        # 3. 기존 데이터의 created_at을 updated_at으로 설정
        print("🔧 기존 데이터 마이그레이션 중...")
        cursor.execute("""
            UPDATE system_settings
            SET created_at = updated_at
            WHERE created_at IS NULL
        """)

        updated_rows = cursor.rowcount
        print(f"✅ {updated_rows}개 행 마이그레이션 완료")

        # 4. 검증
        cursor.execute("SELECT key, created_at, updated_at FROM system_settings LIMIT 5")
        rows = cursor.fetchall()
        print("\n검증 (샘플 5개):")
        for row in rows:
            print(f"  키: {row[0]}, 등록일: {row[1]}, 수정일: {row[2]}")

        conn.commit()
        print("\n✅ 마이그레이션 성공!")

    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_created_at()
