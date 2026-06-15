"""Cross-check meeting IDs between ChromaDB, reingest list, and local cache."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv; load_dotenv()

from app.core.storage.db import get_raw_collection

col = get_raw_collection()
res = col.get(where={"project_id": {"$eq": "proj_nolocode_001"}}, include=["metadatas"])

db_meetings = {}
for m in res["metadatas"]:
    mid = m.get("meeting_id")
    if mid and not m.get("is_meeting_summary") and mid not in db_meetings:
        db_meetings[mid] = m.get("meeting_title", "?")

sys.path.insert(0, ".")
from reingest_all import ALL_MEETING_IDS, CACHE_DIR

cache_files = os.listdir(CACHE_DIR) if os.path.exists(CACHE_DIR) else []
cached_ids  = {f.replace(".json","") for f in cache_files if f.endswith(".json")}

print(f"Distinct meetings in ChromaDB : {len(db_meetings)}")
print(f"IDs in ALL_MEETING_IDS        : {len(ALL_MEETING_IDS)}")
print(f"IDs with local cache file     : {len(set(ALL_MEETING_IDS) & cached_ids)}")

missing_cache = set(ALL_MEETING_IDS) - cached_ids
print(f"IDs WITHOUT cache (need API)  : {len(missing_cache)}")
for mid in missing_cache:
    print(f"  NO CACHE: {mid}  ({db_meetings.get(mid, 'not in DB')})")

print()
extra_in_db = set(db_meetings.keys()) - set(ALL_MEETING_IDS)
print(f"In ChromaDB but NOT in reingest list: {len(extra_in_db)}")
for mid in extra_in_db:
    print(f"  {mid}  {db_meetings[mid]}")

not_in_db = set(ALL_MEETING_IDS) - set(db_meetings.keys())
print(f"\nIn reingest list but NOT in ChromaDB: {len(not_in_db)}")
for mid in not_in_db:
    print(f"  {mid}")

print("\nAll meetings in ChromaDB:")
for i, (mid, title) in enumerate(sorted(db_meetings.items(), key=lambda x: x[1]), 1):
    cached = "CACHED" if mid in cached_ids else "NO CACHE"
    in_list = "IN LIST" if mid in ALL_MEETING_IDS else "NOT IN LIST"
    print(f"  {i:02d}. [{cached}] [{in_list}]  {title}  ({mid})")
