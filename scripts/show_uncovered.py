"""show uncovered atomic chunks for a meeting — should all be solo monologues"""
import sys, os, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv; load_dotenv()
from app.core.storage.db import get_raw_collection

parser = argparse.ArgumentParser()
parser.add_argument("--id",      default="01KKGA075M7EANGQ289WYZZ8XZ")
parser.add_argument("--meeting", default=None)
parser.add_argument("--project", default="proj_nolocode_001")
args = parser.parse_args()
PID  = args.project

if args.meeting:
    col  = get_raw_collection()
    res0 = col.get(where={"project_id": {"$eq": PID}}, include=["metadatas"])
    MID  = next((m["meeting_id"] for m in res0["metadatas"]
                 if args.meeting.lower() in (m.get("meeting_title","")).lower()), args.id)
else:
    MID = args.id

col = get_raw_collection()
res = col.get(
    where={"$and": [{"project_id": {"$eq": PID}}, {"meeting_id": {"$eq": MID}}]},
    include=["documents", "metadatas"],
)

dg_metas = [m for m in res["metadatas"] if m.get("chunk_type") == "dialogue_group"]
covered  = set()
for m in dg_metas:
    for tid in (m.get("turn_ids") or "").split("|"):
        if tid.strip():
            covered.add(tid.strip())

pairs = [(d, m) for d, m in zip(res["documents"], res["metadatas"])
         if m.get("chunk_type") == "atomic"]
pairs.sort(key=lambda x: x[1].get("start_time", 0) or 0)

not_covered = [(d, m) for d, m in pairs if m.get("chunk_id") not in covered]
print(f"Atomic NOT in any DG: {len(not_covered)}\n")

for doc, m in not_covered:
    ts     = m.get("start_time", 0) or 0
    raw    = (m.get("raw_text") or "").replace("\n", " ")[:130]
    tokens = len((m.get("raw_text") or "").split())
    spk    = m.get("speaker_name", "?")
    print(f"  {spk[:22]} @{int(ts//60):02d}:{int(ts%60):02d}  tokens={tokens}")
    print(f"    {raw}")
    print()
