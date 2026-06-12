"""
run_comparison.py — Side-by-side accuracy comparison: no-rerank vs with-rerank.

Runs all PROJECT_LEVEL_GOLDENS (11 queries) twice:
  Pass 1: RERANK_ENABLED=0  → hybrid retrieval order, top-k slice only
  Pass 2: RERANK_ENABLED=1  → full Gemini reranker

Prints a per-query diff table and summary showing where reranking helps/hurts.
"""
import os
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[4]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv
load_dotenv(_ROOT / ".env")

import logging
logging.disable(logging.CRITICAL)  # silence pipeline noise during eval

from app.agent.tests.deepeval_tests.goldens import PROJECT_LEVEL_GOLDENS
from app.agent.tests.deepeval_tests.eval_runner import run_single_eval, EvalResult


def run_pass(label: str, rerank_enabled: bool) -> list[EvalResult]:
    os.environ["RERANK_ENABLED"] = "1" if rerank_enabled else "0"
    results = []
    print(f"\n{'='*60}")
    print(f"  PASS: {label}  (RERANK_ENABLED={'1' if rerank_enabled else '0'})")
    print(f"{'='*60}")
    for golden in PROJECT_LEVEL_GOLDENS:
        gid = golden.additional_metadata["id"]
        print(f"  [{gid}] ...", end="", flush=True)
        t0 = time.time()
        result = run_single_eval(golden)
        elapsed = time.time() - t0
        results.append(result)
        print(f" {result.overall_score:.2f}  ({elapsed:.0f}s)")
    return results


def print_comparison(no_rerank: list[EvalResult], with_rerank: list[EvalResult]):
    by_id_nr = {r.golden_id: r for r in no_rerank}
    by_id_wr = {r.golden_id: r for r in with_rerank}

    all_ids = [r.golden_id for r in no_rerank]

    print("\n" + "=" * 100)
    print(f"{'ID':<42} {'NO-RERANK':>10} {'WITH-RERANK':>12} {'DELTA':>8}  {'VERDICT'}")
    print("-" * 100)

    improved, degraded, same = [], [], []

    for gid in all_ids:
        nr = by_id_nr[gid]
        wr = by_id_wr[gid]
        delta = wr.overall_score - nr.overall_score

        if delta >= 0.05:
            verdict = "✓ RERANK HELPS"
            improved.append(gid)
        elif delta <= -0.05:
            verdict = "✗ RERANK HURTS"
            degraded.append(gid)
        else:
            verdict = "  no change"
            same.append(gid)

        print(
            f"{gid:<42} {nr.overall_score:>10.2f} {wr.overall_score:>12.2f} "
            f"{delta:>+8.2f}  {verdict}"
        )

    print("=" * 100)
    print(f"\nSummary: {len(improved)} improved | {len(degraded)} degraded | {len(same)} unchanged")

    avg_nr = sum(r.overall_score for r in no_rerank) / len(no_rerank)
    avg_wr = sum(r.overall_score for r in with_rerank) / len(with_rerank)
    print(f"Average score — no-rerank: {avg_nr:.3f}  |  with-rerank: {avg_wr:.3f}  |  delta: {avg_wr - avg_nr:+.3f}")

    if improved:
        print(f"\nWhere reranking HELPS ({len(improved)}):")
        for gid in improved:
            nr, wr = by_id_nr[gid], by_id_wr[gid]
            delta = wr.overall_score - nr.overall_score
            print(f"  {gid}")
            print(f"    query   : {nr.query[:80]}")
            print(f"    scores  : {nr.overall_score:.2f} → {wr.overall_score:.2f} (+{delta:.2f})")
            print(f"    no-rank missing  : {nr.facts_missing}")
            print(f"    rerank  missing  : {wr.facts_missing}")
            nr_hall = nr.hallucinations_found
            wr_hall = wr.hallucinations_found
            if nr_hall and not wr_hall:
                print(f"    hallucination fixed: {nr_hall}")

    if degraded:
        print(f"\nWhere reranking HURTS ({len(degraded)}):")
        for gid in degraded:
            nr, wr = by_id_nr[gid], by_id_wr[gid]
            delta = wr.overall_score - nr.overall_score
            print(f"  {gid}")
            print(f"    query   : {nr.query[:80]}")
            print(f"    scores  : {nr.overall_score:.2f} → {wr.overall_score:.2f} ({delta:.2f})")
            print(f"    rerank introduced missing: {[f for f in wr.facts_missing if f not in nr.facts_missing]}")
            print(f"    rerank introduced halluc : {[h for h in wr.hallucinations_found if h not in nr.hallucinations_found]}")


if __name__ == "__main__":
    print("Starting comparison run — 11 queries × 2 passes")
    print("Pass 1 (no-rerank) will be fast (~2 min)")
    print("Pass 2 (with-rerank) will be slow (~8-10 min, Gemini API)")

    no_rerank_results  = run_pass("NO-RERANK  (hybrid order only)", rerank_enabled=False)
    with_rerank_results = run_pass("WITH-RERANK (Gemini reranker)", rerank_enabled=True)

    print_comparison(no_rerank_results, with_rerank_results)

    # restore to default (disabled)
    os.environ["RERANK_ENABLED"] = "0"