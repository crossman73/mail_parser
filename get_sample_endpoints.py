import sqlite3

conn = sqlite3.connect('data/db/court_evidence.db')
cursor = conn.cursor()

# GET 메서드 엔드포인트 몇 개 확인
cursor.execute("""
    SELECT id, path, method
    FROM api_endpoints
    WHERE method = 'GET' AND deprecated = 0
    LIMIT 10
""")

print("GET 엔드포인트 샘플 (테스트용):")
for r in cursor.fetchall():
    print(f"  ID={r[0]:<4} {r[2]:<6} {r[1]}")

conn.close()
