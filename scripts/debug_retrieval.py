"""
debug_retrieval.py — Run a single query and show atomic vs dialogue_group chunk breakdown.

Usage:
  python scripts/debug_retrieval.py "what did Harsh Vardhan say about architecture"
  python scripts/debug_retrieval.py "what decisions were made about the AI model"
  python scripts/debug_retrieval.py "what did Harsh Vardhan say about architecture" --speaker "Harsh Vardhan Dixit"

Options:
  --speaker NAME   Filter to a specific speaker (exercises speaker_hybrid_retrieve)
  --k N            Override retrieval k (default: 40)
  --project ID     Project ID (default: proj_nolocode_001)
"""

import sys
import os
import argparse

# Make sure app/ is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app.core.retrieval import hybrid_retrieve, speaker_hybrid_retrieve
from app.core.retrieval.base import reset_corpus_cache


def run(query: str, speaker, k: int, project_id: str):
    reset_corpus_cache()

    print(f"\n{'='*65}")
    print(f"  QUERY      : {query!r}")
    spk_label = repr(speaker) if speaker else "(none -- hybrid_retrieve)"
    print(f"  SPEAKER    : {spk_label}")
    print(f"  k          : {k}")
    print(f"  project_id : {project_id}")
    print(f"{'='*65}\n")

    if speaker:
        docs = speaker_hybrid_retrieve(
            query=query,
            project_id=project_id,
            speaker_name=speaker,
            k=k,
            dense_query=query,
        )
    else:
        docs = hybrid_retrieve(
            query=query,
            project_id=project_id,
            k=k,
            dense_query=query,
        )

    atomic_docs = [d for d in docs if d.metadata.get("chunk_type") == "atomic"]
    dg_docs     = [d for d in docs if d.metadata.get("chunk_type") == "dialogue_group"]
    other_docs  = [d for d in docs if d.metadata.get("chunk_type") not in ("atomic", "dialogue_group")]

    print(f"RESULTS: {len(docs)} total  |  atomic={len(atomic_docs)}  dialogue_group={len(dg_docs)}  other={len(other_docs)}\n")

    def _fmt_chunk(i, label, meeting, date, ts, hq, raw):
        mm  = int(ts // 60) if ts else 0
        ss  = int(ts % 60) if ts else 0
        hq_  = (hq  or "").replace("\n", " ").strip()
        raw_ = (raw or "").replace("\n", " ").strip()
        print(f"  [{i:02d}] {label} ({mm:02d}:{ss:02d})  |  {meeting} ({date})")
        print(f"       HQ  : {hq_[:120]}")
        print(f"       RAW : {raw_[:200]}")
        print()

    # ── Atomic chunks ──────────────────────────────────────────────────────────
    if atomic_docs:
        print(f"{'─'*65}")
        print(f"  ATOMIC CHUNKS ({len(atomic_docs)})")
        print(f"{'─'*65}")
        for i, doc in enumerate(atomic_docs, 1):
            m = doc.metadata
            _fmt_chunk(
                i,
                label   = m.get("speaker_name", "?"),
                meeting = m.get("meeting_title", "?"),
                date    = str(m.get("meeting_date", ""))[:10],
                ts      = m.get("start_time", 0) or 0,
                hq      = doc.page_content,
                raw     = m.get("raw_text", ""),
            )

    # ── Dialogue group chunks ──────────────────────────────────────────────────
    if dg_docs:
        print(f"{'─'*65}")
        print(f"  DIALOGUE_GROUP CHUNKS ({len(dg_docs)})")
        print(f"{'─'*65}")
        for i, doc in enumerate(dg_docs, 1):
            m = doc.metadata
            _fmt_chunk(
                i,
                label   = "[" + m.get("speakers", "").replace("|", " · ") + "]",
                meeting = m.get("meeting_title", "?"),
                date    = str(m.get("meeting_date", ""))[:10],
                ts      = m.get("start_time", 0) or 0,
                hq      = doc.page_content,
                raw     = m.get("raw_text", ""),
            )

    # ── Summary table ──────────────────────────────────────────────────────────
    print(f"{'='*65}")
    print(f"  SUMMARY")
    print(f"{'─'*65}")
    print(f"  Total returned   : {len(docs)}")
    print(f"  Atomic           : {len(atomic_docs)}  ({100*len(atomic_docs)//max(len(docs),1)}%)")
    print(f"  Dialogue group   : {len(dg_docs)}  ({100*len(dg_docs)//max(len(docs),1)}%)")

    if dg_docs:
        meetings_in_dg = {d.metadata.get("meeting_title") for d in dg_docs}
        print(f"  DG meetings      : {', '.join(sorted(meetings_in_dg))}")
    print(f"{'='*65}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="Search query")
    parser.add_argument("--speaker", default=None, help="Speaker name filter")
    parser.add_argument("--k", type=int, default=40, help="Number of results to retrieve")
    parser.add_argument("--project", default="proj_nolocode_001", help="Project ID")
    args = parser.parse_args()

    run(args.query, args.speaker, args.k, args.project)
