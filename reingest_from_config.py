"""
reingest_from_config.py — Clear ChromaDB and re-ingest 10 meetings from CONSTANT_TRANSCRIPT.

WHY THIS EXISTS
--------------
After implementing contextual embedding (mapper.py adds [Meeting: X | Speaker: Y] prefix
before vectorising each chunk), all existing ChromaDB embeddings are stale — they were
built without the prefix.

This script:
  1. Clears all project chunks from ChromaDB
  2. Re-ingests all 10 meetings from config.py CONSTANT_TRANSCRIPT (zero API calls)
  3. Runs 2 retrieval checks to verify the new embeddings surface the right meetings

USAGE
-----
    python reingest_from_config.py             # re-ingest + verify
    python reingest_from_config.py --dry-run   # show what would happen, no changes
"""

import argparse
import sys
import time
sys.path.insert(0, ".")

from dotenv import load_dotenv
load_dotenv(dotenv_path=".env")

from app.config import CONSTANT_TRANSCRIPT
from app.core.storage.db import get_raw_collection, reset_vectorstore
from app.services.ingest_service import ingest_from_data
from app.core.retrieval.hybrid import hybrid_retrieve

PROJECT_ID = "proj_nolocode_001"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _clear_project() -> int:
    col = get_raw_collection()
    result = col.get(where={"project_id": {"$eq": PROJECT_ID}}, include=[])
    count = len(result["ids"])
    if count > 0:
        col.delete(where={"project_id": {"$eq": PROJECT_ID}})
    return count


def _chunk_stats(label: str) -> None:
    col = get_raw_collection()
    data = col.get(
        where={"project_id": {"$eq": PROJECT_ID}},
        include=["documents", "metadatas"],
    )
    docs  = data.get("documents", [])
    metas = data.get("metadatas", [])

    content = [d for d, m in zip(docs, metas) if not m.get("is_meeting_summary")]
    total   = len(content)

    print(f"\n── {label} ──────────────────────────────────────────")
    if not total:
        print("  No content chunks in DB.")
        return

    u80  = sum(1 for d in content if len(d) < 80)
    u200 = sum(1 for d in content if len(d) < 200)
    o200 = sum(1 for d in content if len(d) >= 200)
    print(f"  Content chunks : {total}")
    print(f"  Under 80 chars : {u80:>5}  ({u80/total*100:.1f}%)  ← tiny chunks")
    print(f"  Under 200 chars: {u200:>5}  ({u200/total*100:.1f}%)")
    print(f"  Over  200 chars: {o200:>5}  ({o200/total*100:.1f}%)  ← well-sized")

    # Show meeting breakdown
    meetings: dict[str, dict] = {}
    for d, m in zip(docs, metas):
        if m.get("is_meeting_summary"):
            continue
        tid = m.get("meeting_id", "?")
        if tid not in meetings:
            meetings[tid] = {"title": m.get("meeting_title", "?"), "count": 0}
        meetings[tid]["count"] += 1

    print(f"\n  {'Title':<40} {'Chunks':>6}")
    print(f"  {'─'*40} {'─'*6}")
    for info in sorted(meetings.values(), key=lambda x: x["count"], reverse=True):
        print(f"  {info['title'][:40]:<40} {info['count']:>6}")
    print()


# ── Retrieval verification ────────────────────────────────────────────────────

_CHECKS = [
    {
        "name": "Formula/financial content retrieval",
        "query": "formula calculation retained earnings accrual",
        "expected_keyword": "formula",
        "why": "Short chunks like 'Change in earnings.' (19 chars) should now match via "
               "[Meeting: Nolocode-M2-formula-discussion] prefix in embedding",
    },
    {
        "name": "AWS deployment retrieval",
        "query": "deployment server backend frontend build",
        "expected_keyword": "aws",
        "why": "Chunks from Nolocode-AWS-deployment should surface via meeting title in prefix "
               "even when the chunk text itself is short (e.g. 'Basically on back end only.')",
    },
]


def _run_retrieval_checks() -> None:
    print("\n── RETRIEVAL VERIFICATION ──────────────────────────────")
    print("  Checks whether contextual embedding routes queries to the right meetings.")
    print("  Pass = expected meeting found in top 5 results.\n")

    for check in _CHECKS:
        print(f"  ┌─ {check['name']}")
        print(f"  │  Query  : \"{check['query']}\"")
        print(f"  │  Why    : {check['why']}")

        try:
            docs = hybrid_retrieve(
                query=check["query"],
                project_id=PROJECT_ID,
                k=10,
            )

            top5    = docs[:5]
            matched = [
                d for d in top5
                if check["expected_keyword"] in d.metadata.get("meeting_title", "").lower()
            ]

            if matched:
                print(f"  │  Result : ✅ PASS — {len(matched)} matching chunk(s) in top 5")
                for d in matched[:2]:
                    title   = d.metadata.get("meeting_title", "?")
                    speaker = d.metadata.get("speaker_name", "?")
                    preview = d.page_content[:120].replace("\n", " ")
                    print(f"  │    [{speaker}]  {title}")
                    print(f"  │    \"{preview}\"")
            else:
                top_titles = [d.metadata.get("meeting_title", "?")[:30] for d in top5]
                print(f"  │  Result : ❌ FAIL — expected meeting not in top 5")
                print(f"  │    Top 5 meetings: {top_titles}")

        except Exception as e:
            print(f"  │  Result : ⚠️  Error — {e}")

        print(f"  └{'─'*60}\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would happen without making changes")
    args = parser.parse_args()

    transcripts = CONSTANT_TRANSCRIPT.get("data", {}).get("transcript", [])

    print(f"Re-ingesting {len(transcripts)} meetings from config | project: {PROJECT_ID}")
    if args.dry_run:
        print("DRY RUN — no changes will be made\n")

    _chunk_stats("BEFORE")

    if args.dry_run:
        print("Dry run complete. Run without --dry-run to apply.\n")
        return

    # ── Step 1: Clear ─────────────────────────────────────────────────────────
    deleted = _clear_project()
    reset_vectorstore()
    print(f"  Cleared {deleted} old chunks from ChromaDB")

    # ── Step 2: Re-ingest ─────────────────────────────────────────────────────
    print("\n── RE-INGESTING ────────────────────────────────────────")
    t_total = time.time()
    ok = 0
    fail = 0

    for i, transcript in enumerate(transcripts, 1):
        title   = transcript.get("title", "?")[:45]
        wrapped = {"data": {"transcript": transcript}}

        print(f"\n[{i:02d}/{len(transcripts)}] {title}")
        t = time.time()
        try:
            result  = ingest_from_data(wrapped, PROJECT_ID, meeting_number=i)
            elapsed = int((time.time() - t) * 1000)
            print(f"  ✅ {result['chunks_stored']} chunks  |  {elapsed}ms")
            ok += 1
        except Exception as e:
            elapsed = int((time.time() - t) * 1000)
            print(f"  ❌ FAILED ({elapsed}ms): {e}")
            fail += 1

    elapsed_total = int(time.time() - t_total)
    print(f"\n── SUMMARY ─────────────────────────────────────────────")
    print(f"  ✅ Success : {ok}")
    print(f"  ❌ Failed  : {fail}")
    print(f"  Total time : {elapsed_total}s")

    _chunk_stats("AFTER")

    # ── Step 3: Verify retrieval ──────────────────────────────────────────────
    _run_retrieval_checks()

    print("── NEXT STEPS ──────────────────────────────────────────")
    print("  Inspect specific meetings / speakers / signals:")
    print("    python -m app.agent.tests.deepeval_tests.verify_chunks meetings")
    print("    python -m app.agent.tests.deepeval_tests.verify_chunks keyword --keyword 'deployment'")
    print("    python -m app.agent.tests.deepeval_tests.verify_chunks keyword --keyword 'formula' --keyword 'earnings'")
    print()
    print("  Run a live query through the agent:")
    print("    python -m app.agent.tests.deepeval_tests.probe_query \"What was discussed about deployment?\"")
    print()


if __name__ == "__main__":
    main()