"""
score_analysis.py — Dense retrieval score distribution analysis across 10 representative queries.

Run:
    uv run python -m app.agent.tests.score_analysis

Purpose:
    Measures the actual cosine similarity score distribution ChromaDB returns for
    10 real PM query types. Output shows where scores naturally fall so we can pick
    a DENSE_MIN_SCORE threshold based on data, not guessing.

    Each query is tested with the same dense_query decoupling logic the pipeline
    uses in production: speaker queries use topic-only dense query (since the speaker
    is already filtered via hard_filters).
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv
load_dotenv(_ROOT / ".env")

from app.core.storage.db import get_vectorstore
from app.core.retrieval.base import _build_filter

PROJECT_ID = "proj_nolocode_001"
K = 40  # same k used in production standard preset

# ── 10 representative queries ─────────────────────────────────────────────────
# Each entry: (description, full_query, dense_query, hard_filters)
#
# dense_query mirrors the production decoupling in tools.py:
#   - Speaker query  → topic-only (speaker already filtered via hard_filters)
#   - No speaker     → full question (natural language gives better semantic signal)
#
QUERIES = [
    (
        "Speaker + topic",
        "What did Ashpreet say about AI architecture?",
        "AI architecture",                              # speaker decoupled
        {"speaker_name": "Ashpreet Singh"},
    ),
    (
        "Decision query",
        "What AI approach did we decide to go with?",
        "What AI approach did we decide to go with?",  # no speaker filter
        None,
    ),
    (
        "Speaker overview",
        "Give me an overview of what Bhavneet is trying to build.",
        "Bhavneet building modules financial intelligence",  # topic for dense
        {"speaker_name": "Bhavneet Mhajan"},
    ),
    (
        "Attribution + commitment",
        "When and where did Harsh commit to using hybrid search?",
        "hybrid search commitment",                    # speaker decoupled
        {"speaker_name": "Harsh Vardhan Dixit"},
    ),
    (
        "Speaker contribution",
        "What has Karan Middha contributed across all meetings?",
        "Karan Middha contributions architecture microservices",  # speaker decoupled
        {"speaker_name": "Karan Middha"},
    ),
    (
        "Speaker + topic 2",
        "What did Harsh Vardhan say about the stress test implementation?",
        "stress test implementation deterministic",    # speaker decoupled
        {"speaker_name": "Harsh Vardhan Dixit"},
    ),
    (
        "Broad topic",
        "What was discussed about the multi-agent system?",
        "What was discussed about the multi-agent system?",
        None,
    ),
    (
        "Broad decisions",
        "What decisions were made about the project architecture?",
        "What decisions were made about the project architecture?",
        None,
    ),
    (
        "Open issues / blockers",
        "What are the open issues or blockers in the project?",
        "What are the open issues or blockers in the project?",
        None,
    ),
    (
        "Specific decision",
        "What did the team decide about Redis implementation?",
        "What did the team decide about Redis implementation?",
        None,
    ),
]


def percentile(scores: list[float], p: int) -> float:
    if not scores:
        return 0.0
    sorted_s = sorted(scores)
    idx = int(len(sorted_s) * p / 100)
    return sorted_s[min(idx, len(sorted_s) - 1)]


def main():
    vectorstore = get_vectorstore()

    print(f"\n{'═'*100}")
    print(f"  DENSE SCORE DISTRIBUTION — {len(QUERIES)} queries, k={K} each")
    print(f"  Project: {PROJECT_ID}")
    print(f"{'═'*100}")
    print(f"\n  {'#':<3}  {'Type':<25}  {'n':>4}  {'min':>5}  {'p25':>5}  {'p50':>5}  {'p75':>5}  {'max':>5}  {'≥0.50':>6}  {'≥0.47':>6}  {'≥0.45':>6}")
    print(f"  {'─'*95}")

    all_scores: list[float] = []
    per_query: list[dict]   = []

    for i, (desc, full_q, dense_q, filters) in enumerate(QUERIES, 1):
        meta_filter = _build_filter(PROJECT_ID, filters)

        try:
            results = vectorstore.similarity_search_with_relevance_scores(
                query=dense_q, k=K, filter=meta_filter
            )
        except Exception as e:
            print(f"  {i:<3}  {'ERROR: ' + str(e)[:50]}")
            continue

        scores = sorted([s for _, s in results], reverse=True)
        if not scores:
            print(f"  {i:<3}  {desc:<25}  {'0':>4}  (no results)")
            continue

        all_scores.extend(scores)
        p25 = percentile(scores, 25)
        p50 = percentile(scores, 50)
        p75 = percentile(scores, 75)
        above_50 = sum(1 for s in scores if s >= 0.50)
        above_47 = sum(1 for s in scores if s >= 0.47)
        above_45 = sum(1 for s in scores if s >= 0.45)

        per_query.append({
            "desc": desc, "scores": scores,
            "min": min(scores), "max": max(scores),
            "p50": p50, "above_50": above_50,
        })

        print(
            f"  {i:<3}  {desc:<25}  {len(scores):>4}"
            f"  {min(scores):>5.3f}  {p25:>5.3f}  {p50:>5.3f}  {p75:>5.3f}  {max(scores):>5.3f}"
            f"  {above_50:>6}  {above_47:>6}  {above_45:>6}"
        )

    if not all_scores:
        print("\n  No scores collected — check PROJECT_ID and DB connection.")
        return

    # ── Overall stats ─────────────────────────────────────────────────────────
    all_sorted = sorted(all_scores)
    print(f"\n  {'─'*95}")
    print(
        f"  {'OVERALL':<29}  {len(all_scores):>4}"
        f"  {min(all_scores):>5.3f}  {percentile(all_scores,25):>5.3f}"
        f"  {percentile(all_scores,50):>5.3f}  {percentile(all_scores,75):>5.3f}"
        f"  {max(all_scores):>5.3f}"
        f"  {sum(1 for s in all_scores if s >= 0.50):>6}"
        f"  {sum(1 for s in all_scores if s >= 0.47):>6}"
        f"  {sum(1 for s in all_scores if s >= 0.45):>6}"
    )

    # ── Threshold impact table ─────────────────────────────────────────────────
    print(f"\n{'═'*100}")
    print(f"  THRESHOLD IMPACT — how many chunks each threshold keeps across all {len(all_scores)} total")
    print(f"{'─'*100}")
    print(f"  {'Threshold':>10}  {'Kept':>6}  {'Dropped':>8}  {'% kept':>7}  Recommendation")
    print(f"  {'─'*85}")

    thresholds = [0.38, 0.40, 0.42, 0.44, 0.45, 0.46, 0.47, 0.48, 0.49, 0.50, 0.52, 0.55]
    for t in thresholds:
        kept    = sum(1 for s in all_scores if s >= t)
        dropped = len(all_scores) - kept
        pct     = kept / len(all_scores) * 100

        if pct > 85:
            note = "too permissive — keeps too much noise"
        elif pct > 65:
            note = "✅ good range — cuts clear noise, keeps most relevant"
        elif pct > 40:
            note = "⚠️  aggressive — may cut borderline-relevant chunks"
        else:
            note = "❌ too strict — will miss relevant chunks"

        print(f"  {t:>10.2f}  {kept:>6}  {dropped:>8}  {pct:>6.0f}%  {note}")

    # ── Per-query top-5 score preview ─────────────────────────────────────────
    print(f"\n{'═'*100}")
    print(f"  TOP-5 SCORES PER QUERY (to check if relevant chunks are truly at the top)")
    print(f"{'─'*100}")
    for q in per_query:
        top5 = "  ".join(f"{s:.3f}" for s in q["scores"][:5])
        tail3 = "  ".join(f"{s:.3f}" for s in q["scores"][-3:])
        print(f"  {q['desc']:<28}  top-5: {top5}  ...  bottom-3: {tail3}")

    # ── Final recommendation ──────────────────────────────────────────────────
    print(f"\n{'═'*100}")
    p80 = percentile(all_scores, 80)
    p85 = percentile(all_scores, 85)
    print(f"  SUGGESTED THRESHOLD RANGE:  {p80:.3f} – {p85:.3f}")
    print(f"  (p80={p80:.3f} keeps top 20%, p85={p85:.3f} keeps top 15% of all retrieved chunks)")
    print(f"  Set DENSE_MIN_SCORE in .env to a value in this range, then re-run to verify.")
    print(f"{'═'*100}\n")


if __name__ == "__main__":
    main()