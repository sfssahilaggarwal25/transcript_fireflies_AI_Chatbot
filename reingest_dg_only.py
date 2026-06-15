"""
reingest_dg_only.py — Rebuild dialogue_group chunks for one or all meetings.

Deletes only the dialogue_group chunks for the target meeting(s), then
recreates them from the atomic chunks already in ChromaDB. Atomic chunks,
summaries, and embeddings are untouched.

~10x faster than full reingest — HQ generation only for new DG chunks.

USAGE
-----
    python reingest_dg_only.py --meeting "Nolocode AI meeting"
    python reingest_dg_only.py --id 01KMHQSBYB1RAGY2X4EP6DCMC9
    python reingest_dg_only.py --all          # all 25 meetings sequentially
    python reingest_dg_only.py --all --dry-run
"""

import argparse
import sys
import os

# Flush stdout immediately so progress is visible in real time
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)
import time
sys.path.insert(0, ".")

from dotenv import load_dotenv
load_dotenv(dotenv_path=".env")

from app.core.storage.db import get_raw_collection, get_vectorstore, reset_vectorstore
from app.core.documents.mapper import chunks_to_documents
from app.core.storage.chunk_store import store_documents
from app.core.transcript.chunking import (
    create_dialogue_groups,
    generate_hypothetical_questions_batch,
)

PROJECT_ID = "proj_nolocode_001"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_all_meeting_ids() -> list:
    """Return all distinct meeting_ids from ChromaDB for this project."""
    col = get_raw_collection()
    res = col.get(where={"project_id": {"$eq": PROJECT_ID}}, include=["metadatas"])
    seen = {}
    for m in res["metadatas"]:
        mid = m.get("meeting_id")
        if mid and not m.get("is_meeting_summary") and mid not in seen:
            seen[mid] = m.get("meeting_title", "?")
    return list(seen.items())   # [(meeting_id, title), ...]


def _resolve_meeting_id(name: str) -> tuple:
    """Find (meeting_id, title) from a partial title match."""
    all_mtgs = _get_all_meeting_ids()
    matches = [(mid, t) for mid, t in all_mtgs if name.lower() in t.lower()]
    if not matches:
        print(f"No meeting found matching '{name}'. Available:")
        for mid, t in sorted(all_mtgs, key=lambda x: x[1]):
            print(f"  {t}  ({mid})")
        sys.exit(1)
    if len(matches) > 1:
        print(f"Multiple matches for '{name}':")
        for mid, t in matches:
            print(f"  {t}  ({mid})")
        print("Use --id to specify exactly.")
        sys.exit(1)
    return matches[0]


def _fetch_atomic_chunks(meeting_id: str) -> list:
    """Fetch all atomic chunks for a meeting and reconstruct chunk dicts."""
    col = get_raw_collection()
    res = col.get(
        where={"$and": [
            {"project_id":  {"$eq": PROJECT_ID}},
            {"meeting_id":  {"$eq": meeting_id}},
            {"chunk_type":  {"$eq": "atomic"}},
        ]},
        include=["metadatas"],
    )
    chunks = []
    for m in res["metadatas"]:
        # Reconstruct the dict create_dialogue_groups() needs
        chunks.append({
            "chunk_id":           m.get("chunk_id", ""),
            "meeting_id":         m.get("meeting_id", ""),
            "meeting_title":      m.get("meeting_title", ""),
            "meeting_date":       m.get("meeting_date", ""),
            "meeting_number":     m.get("meeting_number", 0),
            "speaker_name":       m.get("speaker_name", ""),
            "speaker_role":       m.get("speaker_role", "unknown"),
            "start_time":         m.get("start_time"),
            "end_time":           m.get("end_time"),
            "is_meeting_summary": False,
            # text = raw transcript (not HQ) — this is what TF-IDF runs on
            "text":               m.get("raw_text") or "",
        })
    # Sort by start_time so TF-IDF sees turns in chronological order
    chunks.sort(key=lambda c: c.get("start_time") or 0)
    return chunks


def _delete_dg_chunks(meeting_id: str) -> int:
    """Delete all dialogue_group chunks for this meeting. Returns count deleted."""
    col = get_raw_collection()
    res = col.get(
        where={"$and": [
            {"project_id": {"$eq": PROJECT_ID}},
            {"meeting_id": {"$eq": meeting_id}},
            {"chunk_type": {"$eq": "dialogue_group"}},
        ]},
        include=["metadatas"],
    )
    ids = res.get("ids", [])
    if ids:
        col.delete(ids=ids)
    return len(ids)


# ── Core rebuild ──────────────────────────────────────────────────────────────

def rebuild_dg_for_meeting(meeting_id: str, title: str, dry_run: bool = False) -> dict:
    """
    Rebuild dialogue_group chunks for one meeting.
    Returns a result dict with counts and timing.
    """
    t0 = time.time()

    # Step 1 — fetch existing atomic chunks
    atomic_chunks = _fetch_atomic_chunks(meeting_id)
    if not atomic_chunks:
        return {"meeting_id": meeting_id, "title": title,
                "status": "skipped", "reason": "no atomic chunks found"}

    if dry_run:
        # Preview only — count existing DG and what would be created, no writes
        col = get_raw_collection()
        existing_dg = col.get(
            where={"$and": [
                {"project_id": {"$eq": PROJECT_ID}},
                {"meeting_id": {"$eq": meeting_id}},
                {"chunk_type": {"$eq": "dialogue_group"}},
            ]},
            include=["metadatas"],
        )
        current_dg_count = len(existing_dg.get("ids", []))
        meeting_metadata = {
            "meeting_id":     atomic_chunks[0]["meeting_id"],
            "title":          atomic_chunks[0]["meeting_title"],
            "date":           atomic_chunks[0]["meeting_date"],
            "meeting_number": atomic_chunks[0]["meeting_number"],
        }
        dg_chunks = create_dialogue_groups(atomic_chunks, meeting_metadata)
        print(f"  [DRY RUN] {title}")
        print(f"    atomic chunks   : {len(atomic_chunks)}")
        print(f"    old DG (delete) : {current_dg_count}")
        print(f"    new DG (create) : {len(dg_chunks)}")
        return {"meeting_id": meeting_id, "title": title,
                "status": "dry_run", "new_dg": len(dg_chunks)}

    # Step 2 — delete old DG chunks
    deleted = _delete_dg_chunks(meeting_id)

    # Step 3 — build meeting_metadata for create_dialogue_groups
    meeting_metadata = {
        "meeting_id":     atomic_chunks[0]["meeting_id"],
        "title":          atomic_chunks[0]["meeting_title"],
        "date":           atomic_chunks[0]["meeting_date"],
        "meeting_number": atomic_chunks[0]["meeting_number"],
    }

    # Step 4 — create new DG chunks
    dg_chunks = create_dialogue_groups(atomic_chunks, meeting_metadata)
    if not dg_chunks:
        print(f"  {title}  — 0 DG chunks produced (short or single-speaker meeting)")
        return {"meeting_id": meeting_id, "title": title,
                "status": "ok", "deleted": deleted, "created": 0,
                "elapsed_s": round(time.time() - t0, 1)}

    # Step 5 — stamp project_id (atomic chunks already have it; DG needs it added)
    for chunk in dg_chunks:
        chunk["project_id"] = PROJECT_ID

    # Step 6 — generate HQ for new DG chunks only
    generate_hypothetical_questions_batch(dg_chunks)

    # Step 7 — convert to Documents and store
    documents = chunks_to_documents(dg_chunks)
    store_documents(documents)
    reset_vectorstore()

    elapsed = round(time.time() - t0, 1)
    print(f"  OK  {title}")
    print(f"      atomic={len(atomic_chunks)}  old_dg_deleted={deleted}  new_dg={len(dg_chunks)}  elapsed={elapsed}s")

    return {
        "meeting_id": meeting_id,
        "title":      title,
        "status":     "ok",
        "atomic":     len(atomic_chunks),
        "deleted":    deleted,
        "created":    len(dg_chunks),
        "elapsed_s":  elapsed,
    }


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--meeting", help="Partial meeting title")
    group.add_argument("--id",      help="Exact meeting_id")
    group.add_argument("--all",     action="store_true", help="All 25 meetings")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview what would happen without writing")
    args = parser.parse_args()

    if args.all:
        meetings = _get_all_meeting_ids()
        meetings.sort(key=lambda x: x[1])
        print(f"\nRebuilding DG chunks for {len(meetings)} meetings"
              + (" [DRY RUN]" if args.dry_run else "") + "\n")

        results = []
        for i, (mid, title) in enumerate(meetings, 1):
            print(f"[{i:02d}/{len(meetings)}] {title}  ({mid})")
            r = rebuild_dg_for_meeting(mid, title, dry_run=args.dry_run)
            results.append(r)

        # Summary
        ok      = [r for r in results if r["status"] == "ok"]
        skipped = [r for r in results if r["status"] == "skipped"]
        total_deleted = sum(r.get("deleted", 0) for r in ok)
        total_created = sum(r.get("created", 0) for r in ok)
        total_elapsed = sum(r.get("elapsed_s", 0) for r in ok)

        print(f"\n{'='*55}")
        print(f"  SUMMARY")
        print(f"  Meetings processed : {len(ok)}")
        print(f"  Skipped            : {len(skipped)}")
        print(f"  Old DG deleted     : {total_deleted}")
        print(f"  New DG created     : {total_created}")
        print(f"  Total time         : {total_elapsed:.0f}s  ({total_elapsed/60:.1f}min)")
        print(f"{'='*55}\n")

    else:
        if args.id:
            all_mtgs = dict(_get_all_meeting_ids())
            title = all_mtgs.get(args.id, args.id)
            mid   = args.id
        else:
            mid, title = _resolve_meeting_id(args.meeting)

        print(f"\nRebuilding DG chunks for: {title}  ({mid})"
              + (" [DRY RUN]" if args.dry_run else "") + "\n")
        rebuild_dg_for_meeting(mid, title, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
