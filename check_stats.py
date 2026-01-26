import sqlite3

conn = sqlite3.connect('data/db/court_evidence.db')
cursor = conn.cursor()

# 통계 조회 (최근 7일)
cursor.execute("""
    SELECT
        COUNT(*) as total,
        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_count,
        AVG(response_time_ms) as avg_response_time
    FROM api_test_executions
    WHERE executed_at >= datetime('now', '-7 days')
""")

stats = cursor.fetchone()
total, success_count, avg_time = stats

print("📊 API 테스트 이력 통계 (최근 7일)")
print("=" * 50)
print(f"전체 테스트:     {total}개")
print(f"성공 테스트:     {success_count}개")
print(f"성공률:          {(success_count/total*100):.1f}%" if total > 0 else "성공률:          N/A")
print(f"평균 응답 시간:  {avg_time:.0f}ms" if avg_time else "평균 응답 시간:  N/A")

conn.close()
