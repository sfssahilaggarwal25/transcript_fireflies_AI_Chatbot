"""Check SQLite schema and whether embeddings are stored in DB."""
import sqlite3, os, sys

db = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chroma_db", "chroma.sqlite3")
conn = sqlite3.connect(db, timeout=5)

tables = [t[0] for t in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print("Tables:", tables)
print()

for t in tables:
    try:
        n = conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        cols = [c[1] for c in conn.execute(f'PRAGMA table_info("{t}")').fetchall()]
        print(f"  {t}: {n} rows  |  cols: {cols}")
    except Exception as e:
        print(f"  {t}: {e}")

# Check if embeddings table has vector data
print()
try:
    row = conn.execute("SELECT * FROM embeddings LIMIT 1").fetchone()
    if row:
        print("Sample embeddings row:")
        cols = [c[1] for c in conn.execute("PRAGMA table_info(embeddings)").fetchall()]
        for col, val in zip(cols, row):
            if isinstance(val, bytes):
                print(f"  {col}: <bytes len={len(val)}>")
            else:
                print(f"  {col}: {str(val)[:80]}")
except Exception as e:
    print(f"embeddings sample error: {e}")

conn.close()
