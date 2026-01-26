import sqlite3

conn = sqlite3.connect('data/db/court_evidence.db')
cursor = conn.cursor()

# 새로 추가된 엔드포인트 확인
cursor.execute("""
    SELECT path, method, summary
    FROM api_endpoints
    WHERE path LIKE '%test%' OR path LIKE '%history%'
    ORDER BY path
""")
rows = cursor.fetchall()

print("테스트 관련 엔드포인트:")
for r in rows:
    print(f"  {r[1]:<6} {r[0]:<40} {r[2]}")

conn.close()
