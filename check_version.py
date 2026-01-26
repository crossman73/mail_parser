import sqlite3

conn = sqlite3.connect('data/db/court_evidence.db')
cursor = conn.cursor()

print("schema_version 테이블 상세:")
cursor.execute("SELECT * FROM schema_version ORDER BY id")
rows = cursor.fetchall()
print(f"{'ID':<5} {'Version':<10} {'Description':<50} {'Applied At':<25}")
print("-" * 90)
for r in rows:
    print(f"{r[0]:<5} {r[1]:<10} {r[2]:<50} {r[3] if len(r) > 3 else 'N/A':<25}")

conn.close()
