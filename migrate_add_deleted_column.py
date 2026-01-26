"""
데이터베이스에 deleted 컬럼 추가 마이그레이션
"""
import sqlite3
from pathlib import Path

db_path = Path("data/db/email_parser.db")

if not db_path.exists():
    print(f"❌ 데이터베이스 파일이 없습니다: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # uploaded_files 테이블에 deleted, deleted_at 컬럼 추가
    print("📝 uploaded_files 테이블에 deleted 컬럼 추가 중...")
    cursor.execute("""
        ALTER TABLE uploaded_files
        ADD COLUMN deleted INTEGER DEFAULT 0
    """)
    print("✅ deleted 컬럼 추가 완료")

    cursor.execute("""
        ALTER TABLE uploaded_files
        ADD COLUMN deleted_at TEXT
    """)
    print("✅ deleted_at 컬럼 추가 완료")

    # processed_emails 테이블에도 추가
    print("📝 processed_emails 테이블에 deleted 컬럼 추가 중...")
    cursor.execute("""
        ALTER TABLE processed_emails
        ADD COLUMN deleted INTEGER DEFAULT 0
    """)
    print("✅ deleted 컬럼 추가 완료")

    cursor.execute("""
        ALTER TABLE processed_emails
        ADD COLUMN deleted_at TEXT
    """)
    print("✅ deleted_at 컬럼 추가 완료")

    conn.commit()
    print("\n🎉 마이그레이션 완료!")

    # 결과 확인
    cursor.execute("PRAGMA table_info(uploaded_files)")
    columns = cursor.fetchall()
    print("\n📊 uploaded_files 테이블 구조:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")

except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print(f"⚠️ 컬럼이 이미 존재합니다: {e}")
    else:
        print(f"❌ 오류 발생: {e}")
        conn.rollback()
except Exception as e:
    print(f"❌ 예상치 못한 오류: {e}")
    conn.rollback()
finally:
    conn.close()
