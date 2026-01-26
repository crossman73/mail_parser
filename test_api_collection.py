"""API 수집 테스트 스크립트"""
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.api.api_collector import collect_api_docs
from src.database.connection import db_connection
from src.web.app import create_app

if __name__ == '__main__':
    print("🔍 Flask 앱 생성 중...")
    app = create_app()

    print("📊 API 수집 시작...")
    with app.app_context():
        try:
            count = collect_api_docs(app, db_connection)
            print(f"✅ API 문서 자동 수집 완료: {count}개 엔드포인트")

            # DB 확인
            with db_connection.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM api_endpoints")
                db_count = cursor.fetchone()[0]
                print(f"📦 DB에 저장된 엔드포인트: {db_count}개")

                # 카테고리별 통계
                cursor.execute("""
                    SELECT category, COUNT(*) as count
                    FROM api_endpoints
                    GROUP BY category
                    ORDER BY count DESC
                """)
                categories = cursor.fetchall()
                print("\n📋 카테고리별 통계:")
                for cat, cnt in categories:
                    print(f"  - {cat}: {cnt}개")

        except Exception as e:
            print(f"❌ API 수집 실패: {e}")
            import traceback
            traceback.print_exc()
