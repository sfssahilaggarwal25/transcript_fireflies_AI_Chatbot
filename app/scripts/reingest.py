"""
reingest.py — Re-run signal detection on all stored chunks and update ChromaDB metadata.

WHAT IT DOES
------------
Reads every chunk already stored in ChromaDB, re-runs the signal detection
logic (contains_question, contains_decision, contains_commitment, contains_open_issue,
contains_document_share) on the stored text, and writes the updated flags back —
WITHOUT re-embedding or re-fetching from the Fireflies API.

USE THIS WHEN
-------------
  - You fix the signal detection regex in chunking.py (e.g. the endswith("?") bug)
  - You want all historical chunks to reflect the corrected detection
  - You do NOT want to re-fetch transcripts or regenerate embeddings

HOW TO RUN
----------
  # Dry-run (shows what would change, makes no writes)
  python -m app.scripts.reingest --project-id proj_nolocode_001 --dry-run

  # Apply to all meetings in a project
  python -m app.scripts.reingest --project-id proj_nolocode_001

  # Apply to one specific meeting only
  python -m app.scripts.reingest --project-id proj_nolocode_001 --meeting-id 01KM2DD6MXGSZ4F1QW0BNJE16N
"""

import argparse
import sys
import time
from pathlib import Path

# ── Project root on sys.path ──────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

from app.core.storage.db import get_raw_collection
from app.core.transcript.chunking import _detect_signals

# Signal fields managed by this script
_SIGNAL_FIELDS = [
    "contains_question",
    "contains_commitment",
    "contains_decision",
    "contains_open_issue",
    "contains_document_share",
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_meeting_ids(project_id: str, filter_meeting_id: str | None) -> list[str]:
    """Return the list of meeting IDs to process."""
    collection = get_raw_collection()
    results    = collection.get(
        where={"project_id": {"$eq": project_id}},
        include=["metadatas"],
    )
    seen: set[str] = set()
    for m in results.get("metadatas", []):
        mid = m.get("meeting_id")
        if mid:
            seen.add(mid)

    if filter_meeting_id:
        if filter_meeting_id not in seen:
            print(f"[ERROR] meeting_id '{filter_meeting_id}' not found in project '{project_id}'")
            sys.exit(1)
        return [filter_meeting_id]

    return sorted(seen)


def _get_meeting_title(meeting_id: str, project_id: str) -> str:
    """Fetch the human-readable title for a meeting ID."""
    collection = get_raw_collection()
    results    = collection.get(
        where={
            "$and": [
                {"project_id": {"$eq": project_id}},
                {"meeting_id": {"$eq": meeting_id}},
            ]
        },
        include=["metadatas"],
        limit=1,
    )
    metas = results.get("metadatas", [])
    if metas:
        title = metas[0].get("meeting_title", "?")
        date  = metas[0].get("meeting_date", "?")
        num   = metas[0].get("meeting_number", "?")
        return f"Meeting #{num}: {title} ({date})"
    return meeting_id


def _process_meeting(
    meeting_id: str,
    project_id: str,
    dry_run: bool,
) -> dict:
    """
    Re-run signal detection on all non-summary chunks in a meeting.

    Returns a stats dict:
      total    — chunks processed
      changed  — chunks where at least one signal flag changed
      by_field — per-field counts of how many flipped True / False
    """
    collection = get_raw_collection()

    # Fetch all non-summary chunks for this meeting
    results = collection.get(
        where={
            "$and": [
                {"project_id":         {"$eq": project_id}},
                {"meeting_id":         {"$eq": meeting_id}},
                {"is_meeting_summary": {"$ne": True}},
            ]
        },
        include=["documents", "metadatas"],
    )

    ids      = results.get("ids", [])
    texts    = results.get("documents", [])
    metas    = results.get("metadatas", [])

    stats = {
        "total":    len(ids),
        "changed":  0,
        "by_field": {f: {"now_true": 0, "now_false": 0} for f in _SIGNAL_FIELDS},
    }

    # For each chunk, re-detect signals and compare
    updated_ids      = []
    updated_metas    = []

    for chunk_id, text, meta in zip(ids, texts, metas):
        new_signals = _detect_signals(text)
        changed = False

        for field in _SIGNAL_FIELDS:
            old_val = bool(meta.get(field, False))
            new_val = bool(new_signals.get(field, False))

            if old_val != new_val:
                changed = True
                if new_val:
                    stats["by_field"][field]["now_true"]  += 1
                else:
                    stats["by_field"][field]["now_false"] += 1

        if changed:
            stats["changed"] += 1
            # Build updated metadata — keep all existing fields, overwrite signal flags
            updated_meta = {**meta, **{f: new_signals[f] for f in _SIGNAL_FIELDS}}
            updated_ids.append(chunk_id)
            updated_metas.append(updated_meta)

    # Write updates back to ChromaDB (metadata-only, no re-embedding)
    if updated_ids and not dry_run:
        collection.update(
            ids=updated_ids,
            metadatas=updated_metas,
        )

    return stats


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Re-run signal detection on stored chunks and update ChromaDB metadata"
    )
    parser.add_argument("--project-id",  required=True,  help="Project ID to process")
    parser.add_argument("--meeting-id",  default=None,   help="Process one specific meeting only")
    parser.add_argument("--dry-run",     action="store_true",
                        help="Show what would change without writing anything")
    args = parser.parse_args()

    project_id = args.project_id
    dry_label  = "  [DRY RUN — no writes]" if args.dry_run else ""

    print(f"\n{'='*62}")
    print(f"  Signal Re-detection — ChromaDB Metadata Update{dry_label}")
    print(f"  Project : {project_id}")
    print(f"{'='*62}\n")

    meeting_ids = _get_meeting_ids(project_id, args.meeting_id)
    print(f"Meetings to process: {len(meeting_ids)}\n")

    t_start        = time.time()
    total_chunks   = 0
    total_changed  = 0
    grand_by_field = {f: {"now_true": 0, "now_false": 0} for f in _SIGNAL_FIELDS}

    for mid in meeting_ids:
        label = _get_meeting_title(mid, project_id)
        print(f"  [{label}]")

        stats = _process_meeting(mid, project_id, args.dry_run)

        total_chunks  += stats["total"]
        total_changed += stats["changed"]

        if stats["changed"] == 0:
            print(f"    → {stats['total']} chunks checked  |  0 changed  ✅ all signals correct\n")
        else:
            print(f"    → {stats['total']} chunks checked  |  {stats['changed']} changed  ⚠️\n")
            for field, counts in stats["by_field"].items():
                if counts["now_true"] or counts["now_false"]:
                    # Shorten field name for display
                    short = field.replace("contains_", "")
                    if counts["now_true"]:
                        verb = "DRY-would-add" if args.dry_run else "added"
                        print(f"      {short:15}  +{counts['now_true']:3} newly TRUE  ({verb})")
                    if counts["now_false"]:
                        verb = "DRY-would-remove" if args.dry_run else "removed"
                        print(f"      {short:15}  -{counts['now_false']:3} newly FALSE ({verb})")
                    grand_by_field[field]["now_true"]  += counts["now_true"]
                    grand_by_field[field]["now_false"] += counts["now_false"]
            print()

    elapsed = round(time.time() - t_start, 1)

    print(f"{'='*62}")
    print(f"  SUMMARY")
    print(f"  Total chunks checked : {total_chunks}")
    print(f"  Total chunks changed : {total_changed}")
    print(f"  Elapsed              : {elapsed}s")
    if args.dry_run:
        print(f"  Mode                 : DRY RUN — nothing written")
        print(f"  Run without --dry-run to apply changes")
    else:
        print(f"  Mode                 : APPLIED — ChromaDB updated")
    print(f"{'='*62}\n")

    if total_changed > 0:
        print("Signal changes summary:")
        for field, counts in grand_by_field.items():
            if counts["now_true"] or counts["now_false"]:
                short = field.replace("contains_", "")
                print(f"  {short:20} +{counts['now_true']:3} TRUE   -{counts['now_false']:3} FALSE")


if __name__ == "__main__":
    main()