"""
coverage_check.py — Show what % of atomic chunks are covered by at least one DG group.
Usage: python scripts/coverage_check.py --meeting "Nolocode x Akili"
"""
import sys, os, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv; load_dotenv()
from app.core.storage.db import get_raw_collection


def check(meeting_id, project_id):
    col = get_raw_collection()
    res = col.get(
        where={"$and": [
            {"project_id": {"$eq": project_id}},
            {"meeting_id": {"$eq": meeting_id}},
        ]},
        include=["metadatas"],
    )
    metas = res["metadatas"]

    atomic = [m for m in metas if m.get("chunk_type") == "atomic"]
    dg     = [m for m in metas if m.get("chunk_type") == "dialogue_group"]

    if not atomic:
        print("No atomic chunks found."); return

    # Which atomic chunk_ids appear inside a DG via turn_ids?
    covered = set()
    total_dg_turns = 0
    for m in dg:
        for tid in (m.get("turn_ids") or "").split("|"):
            tid = tid.strip()
            if tid:
                covered.add(tid)
                total_dg_turns += 1

    atomic_ids = {m.get("chunk_id") for m in atomic}
    in_dg      = covered & atomic_ids
    not_in_dg  = atomic_ids - in_dg

    pct_in  = 100 * len(in_dg) // len(atomic)
    pct_out = 100 * len(not_in_dg) // len(atomic)
    avg_turns = round(total_dg_turns / max(len(dg), 1), 1)

    title = next((m.get("meeting_title","?") for m in metas), "?")
    print(f"\n{'='*55}")
    print(f"  {title}")
    print(f"{'='*55}")
    print(f"  Atomic chunks         : {len(atomic)}")
    print(f"  DG groups             : {len(dg)}")
    print(f"  Avg turns per DG      : {avg_turns}")
    print(f"  Total DG turns        : {total_dg_turns}")
    print()
    print(f"  Atomic covered by DG  : {len(in_dg)}  ({pct_in}%)")
    print(f"  Atomic NOT in any DG  : {len(not_in_dg)}  ({pct_out}%)")
    print(f"{'='*55}\n")


def list_meetings(project_id):
    col = get_raw_collection()
    res = col.get(where={"project_id": {"$eq": project_id}}, include=["metadatas"])
    seen = {}
    for m in res["metadatas"]:
        mid = m.get("meeting_id")
        if mid and not m.get("is_meeting_summary") and mid not in seen:
            seen[mid] = m.get("meeting_title", "?")
    return seen


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--meeting", default=None)
    parser.add_argument("--id",      default=None)
    parser.add_argument("--project", default="proj_nolocode_001")
    args = parser.parse_args()

    if args.id:
        check(args.id, args.project)
    else:
        meetings = list_meetings(args.project)
        if args.meeting:
            match = {mid: t for mid, t in meetings.items()
                     if args.meeting.lower() in t.lower()}
            if not match:
                print("No match."); [print(f"  {t}") for t in meetings.values()]
            else:
                check(next(iter(match)), args.project)
        else:
            print("Available meetings:"); [print(f"  {t}") for t in sorted(meetings.values())]
