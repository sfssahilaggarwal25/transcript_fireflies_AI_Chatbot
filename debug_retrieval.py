"""
debug_retrieval.py — Step 2: inspect every stage of the retrieval pipeline
for the 3 failing eval queries without touching production code.

Run:
    python debug_retrieval.py
"""
import logging
import os
import sys

# Enable full DEBUG logging so hybrid.py logs are visible
logging.basicConfig(
    level=logging.INFO,
    format="%(name)s | %(message)s",
    stream=sys.stdout,
)
# Silence noisy libs
for lib in ("httpx", "httpcore", "chromadb", "urllib3", "google"):
    logging.getLogger(lib).setLevel(logging.WARNING)

from dotenv import load_dotenv
load_dotenv()

from app.core.retrieval.hybrid import hybrid_retrieve
from app.core.retrieval.reranker import rerank_documents

PROJECT_ID = "proj_nolocode_001"

# The 6 timestamps we NEED to see in results for the Harsh query
HARSH_REQUIRED_TS = {
    "27:36", "28:40", "31:32", "36:39", "45:24", "55:49"
}


def _fmt_ts(sec) -> str:
    if sec is None:
        return "?:??"
    total = int(sec)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def _show_pool(label: str, docs: list, required_ts: set = None):
    print(f"\n{'='*65}")
    print(f"  {label}  ({len(docs)} chunks)")
    print(f"{'='*65}")
    for i, doc in enumerate(docs, 1):
        m   = doc.metadata
        ts  = _fmt_ts(m.get("start_time"))
        spk = m.get("speaker_name", "?")
        mtg = m.get("meeting_title", "?")[:35]
        txt = doc.page_content.replace("\n", " ").strip()[:120]
        hit = " ◀ REQUIRED" if required_ts and ts in required_ts else ""
        print(f"  [{i:02d}] {ts}  {spk}{hit}")
        print(f"        {mtg}")
        print(f"        \"{txt}\"")
    if required_ts:
        found_ts = {
            _fmt_ts(d.metadata.get("start_time"))
            for d in docs
        }
        hits = required_ts & found_ts
        misses = required_ts - found_ts
        print(f"\n  Required timestamps in this stage:")
        print(f"    FOUND  ({len(hits)}/6): {sorted(hits) or 'none'}")
        print(f"    MISSED ({len(misses)}/6): {sorted(misses) or 'none'}")


def run_harsh_query():
    print("\n" + "█"*65)
    print("  QUERY: What did Harsh Vardhan say about the stress test?")
    print("  Speaker filter: Harsh Vardhan Dixit")
    print("  Preset: standard → k=40, rerank_top_n=10")
    print("█"*65)

    # Exact same call the agent makes
    query          = "stress test implementation"
    original_query = "What did Harsh Vardhan say about the stress test implementation?"
    speaker_filter = {"speaker_name": "Harsh Vardhan Dixit"}

    # Stage 1: hybrid pool (k=40, same as standard preset)
    pool = hybrid_retrieve(
        query=query,
        project_id=PROJECT_ID,
        hard_filters=speaker_filter,
        k=40,
        dense_query=original_query,
    )
    _show_pool("STAGE 1 — HYBRID POOL (k=40)", pool, HARSH_REQUIRED_TS)

    # Stage 2: after rerank, top_n=10
    reranked = rerank_documents(
        query=original_query,
        documents=pool,
        topic_hint=query,
        speaker_hint="Harsh Vardhan Dixit",
        top_n=10,
    )
    _show_pool("STAGE 2 — AFTER RERANK (top_n=10)", reranked, HARSH_REQUIRED_TS)

    # Stage 3: what if top_n=18?
    reranked_18 = rerank_documents(
        query=original_query,
        documents=pool,
        topic_hint=query,
        speaker_hint="Harsh Vardhan Dixit",
        top_n=18,
    )
    _show_pool("STAGE 3 — AFTER RERANK (top_n=18, hypothetical)", reranked_18, HARSH_REQUIRED_TS)


def run_karan_query():
    print("\n" + "█"*65)
    print("  QUERY: What has Karan Middha contributed across all meetings?")
    print("  Speaker filter: Karan Middha")
    print("  Preset: broad → k=55, rerank_top_n=12")
    print("█"*65)

    query          = "contributed discussed"
    original_query = "What has Karan Middha contributed across all meetings?"
    speaker_filter = {"speaker_name": "Karan Middha"}

    KARAN_REQUIRED_TS = {"33:19", "44:25", "55:56", "59:02", "22:43", "07:37"}

    pool = hybrid_retrieve(
        query=query,
        project_id=PROJECT_ID,
        hard_filters=speaker_filter,
        k=55,
        dense_query=original_query,
    )
    _show_pool("STAGE 1 — HYBRID POOL (k=55)", pool, KARAN_REQUIRED_TS)

    reranked = rerank_documents(
        query=original_query,
        documents=pool,
        topic_hint=query,
        speaker_hint="Karan Middha",
        top_n=12,
    )
    _show_pool("STAGE 2 — AFTER RERANK (top_n=12)", reranked, KARAN_REQUIRED_TS)


if __name__ == "__main__":
    run_harsh_query()