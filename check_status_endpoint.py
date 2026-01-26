import sqlite3

conn = sqlite3.connect('data/db/court_evidence.db')
cursor = conn.cursor()

# /api/system/status 엔드포인트 확인
cursor.execute("""
    SELECT id, path, method
    FROM api_endpoints
    WHERE path = '/api/system/status'
""")
row = cursor.fetchone()

if row:
    print(f"✅ 엔드포인트 존재: ID={row[0]}, Path={row[1]}, Method={row[2]}")
else:
    print("❌ /api/system/status 엔드포인트 없음")

    # 비슷한 경로 찾기
    cursor.execute("""
        SELECT path, method
        FROM api_endpoints
        WHERE path LIKE '%status%'
        LIMIT 5
    """)
    print("\n비슷한 엔드포인트:")
    for r in cursor.fetchall():
        print(f"  {r[1]:<6} {r[0]}")

conn.close()
