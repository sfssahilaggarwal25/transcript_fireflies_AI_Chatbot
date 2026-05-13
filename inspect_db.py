"""
Run this to inspect what is stored in ChromaDB.
Usage: uv run python inspect_db.py
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import json
from app.services.storage.db import get_collection
from app.services.storage.chunk_store import get_chunk_count, get_chunks_by_meeting, get_distinct_meeting_ids


def main():
    collection = get_collection()

    # ── Total count ──────────────────────────────────────────
    total = collection.count()
    print(f"\n{'='*55}")
    print(f"  ChromaDB — meeting_chunks collection")
    print(f"{'='*55}")
    print(f"  Total chunks stored : {total}")

    if total == 0:
        print("  Collection is empty.")
        return

    # ── All projects + meetings ───────────────────────────────
    all_results = collection.get(include=["metadatas"])
    projects = {}
    for m in all_results["metadatas"]:
        pid = m.get("project_id", "unknown")
        mid = m.get("meeting_id", "unknown")
        if pid not in projects:
            projects[pid] = {}
        projects[pid][mid] = projects[pid].get(mid, 0) + 1

    print(f"\n  Projects & meetings:")
    for pid, meetings in projects.items():
        print(f"\n    project_id : {pid}")
        for mid, count in meetings.items():
            print(f"      meeting_id : {mid}  ->  {count} chunks")

    # ── Summary chunks ────────────────────────────────────────
    summary_results = collection.get(where={"is_meeting_summary": True}, include=["metadatas", "documents"])
    print(f"\n  Summary chunks : {len(summary_results['ids'])}")
    for i, doc_id in enumerate(summary_results["ids"]):
        m = summary_results["metadatas"][i]
        text = summary_results["documents"][i]
        print(f"\n    [{doc_id}]")
        print(f"    meeting : {m.get('meeting_title')}  ({m.get('meeting_date')})")
        print(f"    text    : {text[:200]}{'...' if len(text) > 200 else ''}")

    # ── Decision + commitment chunks ──────────────────────────
    decision_results = collection.get(where={"contains_decision": True})
    commitment_results = collection.get(where={"contains_commitment": True})
    question_results = collection.get(where={"contains_question": True})
    print(f"\n  Signal counts:")
    print(f"    contains_decision   : {len(decision_results['ids'])}")
    print(f"    contains_commitment : {len(commitment_results['ids'])}")
    print(f"    contains_question   : {len(question_results['ids'])}")

    # ── Sample: first 3 chunks ────────────────────────────────
    sample = collection.get(limit=3, include=["metadatas", "documents"])
    print(f"\n  Sample (first 3 chunks):")
    for i, doc_id in enumerate(sample["ids"]):
        m = sample["metadatas"][i]
        text = sample["documents"][i]
        print(f"\n    chunk_id   : {doc_id}")
        print(f"    speaker    : {m.get('speaker_name')}  [{m.get('speaker_role')}]")
        print(f"    meeting    : {m.get('meeting_title')}  #{m.get('meeting_number')}")
        print(f"    signals    : decision={m.get('contains_decision')}  commitment={m.get('contains_commitment')}  question={m.get('contains_question')}")
        print(f"    text       : {text[:150]}{'...' if len(text) > 150 else ''}")

    print(f"\n{'='*55}\n")


if __name__ == "__main__":
    main()
