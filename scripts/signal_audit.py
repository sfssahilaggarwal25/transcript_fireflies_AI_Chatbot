"""
signal_audit.py — Write every signal-tagged chunk to a file for manual review.

Usage:
    uv run python scripts/signal_audit.py
    uv run python scripts/signal_audit.py --project-id proj_nolocode_001
    uv run python scripts/signal_audit.py --signal decision
    uv run python scripts/signal_audit.py --project-id proj_nolocode_001 --signal question

Output:
    scripts/signal_audit_<project_id>.txt  (all signals)
    scripts/signal_audit_<project_id>_<signal>.txt  (one signal)

Each chunk entry shows:
    [CHUNK N]
    Signal    : <which signals are True on this chunk>
    Speaker   : name [role]
    Meeting   : title  #number  (date)
    Timestamp : MM:SS
    Text      : <full chunk text, no truncation>
    ---
"""

import argparse
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.storage.db import get_raw_collection

SIGNALS = [
    "contains_decision",
    "contains_commitment",
    "contains_question",
    "contains_open_issue",
    "contains_document_share",
]

SIGNAL_ALIASES = {
    "decision":       "contains_decision",
    "commitment":     "contains_commitment",
    "question":       "contains_question",
    "open_issue":     "contains_open_issue",
    "document_share": "contains_document_share",
}


def fmt_ts(sec) -> str:
    if sec is None:
        return "—"
    try:
        total = int(float(sec))
        h, rem = divmod(total, 3600)
        m, s = divmod(rem, 60)
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
    except Exception:
        return "—"


def fetch_signal_chunks(collection, project_id: str, signal_field: str) -> list[dict]:
    """Fetch all chunks where signal_field=True for a given project."""
    clauses = [
        {"project_id":      {"$eq": project_id}},
        {signal_field:      {"$eq": True}},
        {"is_meeting_summary": {"$ne": True}},
    ]
    results = collection.get(
        where={"$and": clauses},
        include=["documents", "metadatas"],
    )
    chunks = []
    for doc, meta in zip(results.get("documents", []), results.get("metadatas", [])):
        chunks.append({"text": doc, "meta": meta})
    # Sort by meeting date then start_time
    chunks.sort(key=lambda c: (
        str(c["meta"].get("meeting_date", "")),
        c["meta"].get("start_time") or 0,
    ))
    return chunks


def fetch_all_chunks(collection, project_id: str) -> list[dict]:
    """Fetch every non-summary chunk for the project."""
    clauses = [
        {"project_id":         {"$eq": project_id}},
        {"is_meeting_summary": {"$ne": True}},
    ]
    results = collection.get(
        where={"$and": clauses},
        include=["documents", "metadatas"],
    )
    chunks = []
    for doc, meta in zip(results.get("documents", []), results.get("metadatas", [])):
        chunks.append({"text": doc, "meta": meta})
    return chunks


def count_signal(collection, project_id: str, signal_field: str) -> int:
    clauses = [
        {"project_id":         {"$eq": project_id}},
        {signal_field:         {"$eq": True}},
        {"is_meeting_summary": {"$ne": True}},
    ]
    results = collection.get(where={"$and": clauses}, include=[])
    return len(results.get("ids", []))


def write_signal_section(f, signal_field: str, chunks: list[dict], total_chunks: int):
    label = signal_field.replace("contains_", "").upper()
    count = len(chunks)
    pct   = round(100 * count / total_chunks, 1) if total_chunks else 0

    f.write(f"\n{'═' * 70}\n")
    f.write(f"  SIGNAL: {label}\n")
    f.write(f"  Chunks with this signal : {count}  ({pct}% of all transcript chunks)\n")
    f.write(f"{'═' * 70}\n\n")

    if not chunks:
        f.write("  (no chunks found for this signal)\n\n")
        return

    for i, chunk in enumerate(chunks, 1):
        meta    = chunk["meta"]
        text    = chunk["text"]

        # All signals active on this chunk
        active = [s.replace("contains_", "") for s in SIGNALS if meta.get(s)]
        signal_str = " + ".join(active) if active else "—"

        f.write(f"[{i}/{count}]\n")
        f.write(f"  Signal(s)  : {signal_str}\n")
        f.write(f"  Speaker    : {meta.get('speaker_name', '?')}  [{meta.get('speaker_role', '?')}]\n")
        f.write(f"  Meeting    : {meta.get('meeting_title', '?')}  #{meta.get('meeting_number', '?')}  ({meta.get('meeting_date', '?')})\n")
        f.write(f"  Timestamp  : {fmt_ts(meta.get('start_time'))}\n")
        f.write(f"  chunk_id   : {meta.get('chunk_id', '?')}\n")
        f.write(f"  Text       :\n")
        # Full text, wrapped at 80 chars for readability
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            while len(line) > 80:
                f.write(f"    {line[:80]}\n")
                line = line[80:]
            f.write(f"    {line}\n")
        f.write(f"  {'─' * 66}\n\n")


def get_projects(collection) -> list[str]:
    results = collection.get(include=["metadatas"])
    ids = set()
    for m in results.get("metadatas", []):
        pid = m.get("project_id")
        if pid:
            ids.add(pid)
    return sorted(ids)


def main():
    parser = argparse.ArgumentParser(description="Audit signal-tagged chunks from ChromaDB")
    parser.add_argument("--project-id", default=None, help="Filter to one project (default: first found)")
    parser.add_argument("--signal",     default=None, help="Audit only one signal: decision|commitment|question|open_issue|document_share")
    args = parser.parse_args()

    collection = get_raw_collection()

    # Resolve project_id
    if args.project_id:
        project_id = args.project_id
    else:
        projects = get_projects(collection)
        if not projects:
            print("No projects found in ChromaDB.")
            sys.exit(1)
        project_id = projects[0]
        if len(projects) > 1:
            print(f"Multiple projects found: {projects}")
            print(f"Using first: {project_id}  (pass --project-id to specify)")

    # Resolve which signals to audit
    if args.signal:
        key = SIGNAL_ALIASES.get(args.signal, args.signal)
        if key not in SIGNALS:
            print(f"Unknown signal '{args.signal}'. Valid: {list(SIGNAL_ALIASES.keys())}")
            sys.exit(1)
        signals_to_audit = [key]
    else:
        signals_to_audit = SIGNALS

    # Output file name
    if args.signal:
        out_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            f"signal_audit_{project_id}_{args.signal}.txt",
        )
    else:
        out_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            f"signal_audit_{project_id}.txt",
        )

    # Total non-summary chunk count
    all_chunks   = fetch_all_chunks(collection, project_id)
    total_chunks = len(all_chunks)

    print(f"Project      : {project_id}")
    print(f"Total chunks : {total_chunks}")
    print(f"Signals      : {[s.replace('contains_','') for s in signals_to_audit]}")
    print(f"Writing to   : {out_path}")

    with open(out_path, "w", encoding="utf-8") as f:

        # ── Header ────────────────────────────────────────────────────────────
        f.write("SIGNAL AUDIT REPORT\n")
        f.write(f"Generated  : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Project    : {project_id}\n")
        f.write(f"Total non-summary chunks: {total_chunks}\n\n")

        # ── Summary table ─────────────────────────────────────────────────────
        f.write("SIGNAL SUMMARY\n")
        f.write(f"{'─' * 50}\n")
        for sig in SIGNALS:
            cnt = count_signal(collection, project_id, sig)
            pct = round(100 * cnt / total_chunks, 1) if total_chunks else 0
            label = sig.replace("contains_", "").ljust(20)
            f.write(f"  {label}: {cnt:4d}  ({pct:5.1f}%)\n")
        f.write(f"{'─' * 50}\n\n")

        # ── Co-occurrence table ───────────────────────────────────────────────
        # Shows how many chunks have 2+ signals (helps spot noisy chunks)
        multi = [c for c in all_chunks if sum(1 for s in SIGNALS if c["meta"].get(s)) >= 2]
        f.write(f"Chunks with 2+ signals simultaneously: {len(multi)}\n")
        if multi:
            f.write("  (These are worth reviewing — may indicate overly broad signal detection)\n")
        f.write("\n")

        # ── Per-signal sections ───────────────────────────────────────────────
        for sig in signals_to_audit:
            chunks = fetch_signal_chunks(collection, project_id, sig)
            write_signal_section(f, sig, chunks, total_chunks)

    print(f"\nDone. Open: {out_path}")


if __name__ == "__main__":
    main()