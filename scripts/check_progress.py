"""Quick check of DG chunk counts for all meetings in ChromaDB."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv; load_dotenv()
from app.core.storage.db import get_raw_collection

col = get_raw_collection()
res = col.get(where={"project_id": {"$eq": "proj_nolocode_001"}}, include=["metadatas"])

from collections import defaultdict
counts = defaultdict(lambda: {"title": "", "atomic": 0, "dg": 0})
for m in res["metadatas"]:
    mid = m.get("meeting_id", "")
    ct  = m.get("chunk_type", "")
    if m.get("is_meeting_summary") or not mid:
        continue
    counts[mid]["title"] = m.get("meeting_title", "?")[:35]
    if ct == "atomic":
        counts[mid]["atomic"] += 1
    elif ct == "dialogue_group":
        counts[mid]["dg"] += 1

total_atomic = sum(v["atomic"] for v in counts.values())
total_dg     = sum(v["dg"]     for v in counts.values())

print(f"\n{'Meeting':<37} {'Atomic':>7} {'DG':>6}")
print("-" * 52)
for mid, v in sorted(counts.items(), key=lambda x: x[1]["title"]):
    print(f"  {v['title']:<35} {v['atomic']:>7} {v['dg']:>6}")
print("-" * 52)
print(f"  {'TOTAL':<35} {total_atomic:>7} {total_dg:>6}")
print()
