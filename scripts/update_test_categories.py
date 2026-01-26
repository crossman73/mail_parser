"""
기존 테스트 데이터에 카테고리 정보 추가
"""
import sqlite3
from pathlib import Path

# 테스트 함수 이름 기반 카테고리 매핑
CATEGORY_MAPPING = {
    'test_web_application': 'web',
    'test_health_check': 'web',
    'test_database_connection': 'database',
    'test_config_file': 'system',
    'test_directory_structure': 'system',
    'test_email_processor': 'email',
    'test_forensic_integrity_service': 'forensic',
    'test_api_endpoints': 'api',
    'test_system_settings': 'system',
    'test_disk_space': 'system'
}

def update_categories():
    """기존 테스트에 카테고리 추가"""
    db_path = Path('data/db/court_evidence.db')

    if not db_path.exists():
        print(f"❌ 데이터베이스 파일을 찾을 수 없습니다: {db_path}")
        return False

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # 현재 테스트 목록 조회
            cursor.execute("SELECT id, test_key, test_name, test_category FROM system_tests")
            tests = cursor.fetchall()

            print(f"\n📊 총 {len(tests)}개의 테스트 발견")
            print("=" * 80)

            updated_count = 0
            for test_id, test_key, test_name, current_category in tests:
                # 카테고리가 이미 설정되어 있으면 건너뛰기
                if current_category and current_category.strip():
                    print(f"⏭️  {test_name} - 이미 카테고리 설정됨: {current_category}")
                    continue

                # test_function 이름으로 카테고리 결정
                cursor.execute("SELECT test_function FROM system_tests WHERE id = ?", (test_id,))
                result = cursor.fetchone()

                if not result:
                    continue

                test_function = result[0]
                category = CATEGORY_MAPPING.get(test_function, 'system')

                # 카테고리 업데이트
                cursor.execute(
                    "UPDATE system_tests SET test_category = ? WHERE id = ?",
                    (category, test_id)
                )

                print(f"✅ {test_name} → {category}")
                updated_count += 1

            conn.commit()

            print("=" * 80)
            print(f"\n✨ 완료: {updated_count}개 테스트에 카테고리 추가됨")

            # 결과 확인
            cursor.execute("""
                SELECT test_category, COUNT(*) as count
                FROM system_tests
                GROUP BY test_category
                ORDER BY count DESC
            """)

            print("\n📈 카테고리별 테스트 수:")
            for category, count in cursor.fetchall():
                print(f"  - {category}: {count}개")

            return True

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("🔄 테스트 카테고리 업데이트 시작...\n")
    success = update_categories()

    if success:
        print("\n✅ 카테고리 업데이트 성공!")
        print("💡 서버를 재시작하면 테스트 이력에서 카테고리가 표시됩니다.")
    else:
        print("\n❌ 카테고리 업데이트 실패")
