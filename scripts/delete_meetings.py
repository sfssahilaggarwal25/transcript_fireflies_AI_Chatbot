"""Delete specified meetings from ChromaDB."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv; load_dotenv()
from app.core.storage.db import get_raw_collection, reset_vectorstore

REMOVE_IDS = [
    "01KQF1G1MWVNM7AKDNHVAS0Z38",  # fireflies automation testing
    "01KRB5ZSVZ8CW3TCG2B65VBYZM",
    "01KQEV18WT3P3Z2HYDNS1HZS6X",
    "01KQEZW99HYC05A8YWEC3Z17G0",
]

col = get_raw_collection()
for mid in REMOVE_IDS:
    res = col.get(
        where={"$and": [
            {"project_id": {"$eq": "proj_nolocode_001"}},
            {"meeting_id": {"$eq": mid}},
        ]},
        include=["metadatas"],
    )
    ids = res.get("ids", [])
    if ids:
        col.delete(ids=ids)
        print(f"DELETED {len(ids):3d} chunks  {mid}")
    else:
        print(f"NOT IN DB              {mid}")

reset_vectorstore()
print("Done. Vectorstore cache reset.")
