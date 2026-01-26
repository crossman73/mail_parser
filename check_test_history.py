import sqlite3

conn = sqlite3.connect('data/db/court_evidence.db')
cursor = conn.cursor()

# 저장된 테스트 이력 확인
cursor.execute("""
    SELECT
        t.id, e.path, e.method, t.status_code,
        t.response_time_ms, t.success, t.executed_at
    FROM api_test_executions t
    JOIN api_endpoints e ON t.endpoint_id = e.id
    ORDER BY t.executed_at DESC
    LIMIT 5
""")

print("최근 API 테스트 이력:")
print(f"{'ID':<5} {'Path':<30} {'Method':<8} {'Status':<8} {'Time(ms)':<10} {'Success':<8} {'Executed At':<20}")
print("-" * 100)

for row in cursor.fetchall():
    test_id, path, method, status, time_ms, success, executed = row
    success_str = "✅" if success else "❌"
    print(f"{test_id:<5} {path:<30} {method:<8} {status:<8} {time_ms:<10} {success_str:<8} {executed:<20}")

conn.close()
