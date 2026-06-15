"""
Try to recover ChromaDB after crash-kill.
Attempts WAL checkpoint via SQLite first, then tests if ChromaDB can open.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chroma_db")
SQLITE  = os.path.join(DB_PATH, "chroma.sqlite3")

# Step 1 — force SQLite WAL checkpoint
print("Step 1: SQLite WAL checkpoint...")
try:
    import sqlite3
    conn = sqlite3.connect(SQLITE)
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    conn.execute("PRAGMA integrity_check")
    result = conn.execute("PRAGMA integrity_check").fetchone()
    print(f"  SQLite integrity: {result[0]}")
    conn.close()
except Exception as e:
    print(f"  SQLite error: {e}")

# Step 2 — try opening ChromaDB collection
print("\nStep 2: Opening ChromaDB client...")
try:
    import chromadb
    client = chromadb.PersistentClient(path=DB_PATH)
    cols = client.list_collections()
    print(f"  Collections found: {[c.name for c in cols]}")
except Exception as e:
    print(f"  ChromaDB open failed: {e}")
    sys.exit(1)

# Step 3 — try count on each collection
print("\nStep 3: Collection counts...")
for col in cols:
    try:
        c = client.get_collection(col.name)
        print(f"  {col.name}: {c.count()} items")
    except Exception as e:
        print(f"  {col.name}: ERROR — {e}")

print("\nDone.")
