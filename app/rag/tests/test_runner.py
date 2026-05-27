"""
test_runner.py

Runs easy-level test queries against the real RAG pipeline and saves results.
Each query gets its own JSON result file. A run_metadata.json summarises the run.

Usage:
    python -m app.rag.tests.test_runner --project-id proj_nolocode_001
    python -m app.rag.tests.test_runner --project-id proj_nolocode_001 --dry-run
    python -m app.rag.tests.test_runner --project-id proj_nolocode_001 --ids ml_005,ml_015,ml_019
    python -m app.rag.tests.test_runner --project-id proj_nolocode_001 --tags decision,commitment
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from app.rag.tests.answer_evaluator import compute_confidence_score, evaluate_answer

# ── Paths ─────────────────────────────────────────────────────────────────────

_TESTS_DIR = Path(__file__).parent
_QUERY_BANK = {
    "easy":   _TESTS_DIR / "query_bank" / "easy.json",
    "medium": _TESTS_DIR / "query_bank" / "medium.json",
    "hard":   _TESTS_DIR / "query_bank" / "hard.json",
}
_RESULTS_DIR = _TESTS_DIR / "test_results"

# ── Log capture ───────────────────────────────────────────────────────────────

# These 4 loggers have propagate=False in logging_config.py.
# That means records ONLY go to their own handlers and never travel
# up to any parent logger. We must attach our capture handler directly
# to each one — attaching to the "app" parent logger is invisible to them.
_PIPELINE_LOGGERS = [
    "app.services.answer_service",
    "app.rag.query_intent",
    "app.services.retrieval.retriever",
    "app.services.retrieval.reranker",
]


class _LogCapture(logging.Handler):
    """
    A logging handler that collects formatted log lines into a list.

    One instance is shared across all 4 pipeline loggers per query run.
    Attached before the pipeline runs, detached in the finally block.
    Stores lines in insertion order — the natural pipeline sequence.
    """

    _FMT = logging.Formatter("%(levelname)-8s  %(name)s  %(message)s")

    def __init__(self) -> None:
        super().__init__()
        self.setFormatter(self._FMT)
        self.setLevel(logging.DEBUG)
        self.lines: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.lines.append(self.format(record))


# ── NOT-FOUND signal phrases from answer_service.py ──────────────────────────
# answer_question() returns these strings when no chunks are found.
# We use them to detect an empty/unhelpful answer without parsing the full text.

_NOT_FOUND_SIGNALS = [
    "i couldn't find relevant information",
    "no meeting was found",
    "make sure the project has been ingested",
]


# ── Step 1: Load queries ──────────────────────────────────────────────────────

def load_queries(filepath: Path) -> list[dict]:
    if not filepath.exists():
        print(f"[ERROR] Query bank not found: {filepath}")
        sys.exit(1)

    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    queries = data.get("queries", [])
    if not queries:
        print(f"[ERROR] No queries found in {filepath}")
        sys.exit(1)

    print(f"[INFO] Loaded {len(queries)} queries from {filepath.name}")
    return queries


# ── Step 2: Create output folder ──────────────────────────────────────────────

def create_run_folder(difficulty: str = "easy") -> Path:
    """
    Create a timestamped folder for this test run.
    Example: test_results/2026-05-20_14-30/easy/
             test_results/2026-05-20_14-30/medium/
    Returns the path to the difficulty subfolder.
    """
    timestamp  = datetime.now().strftime("%Y-%m-%d_%H-%M")
    run_folder = _RESULTS_DIR / timestamp / difficulty
    run_folder.mkdir(parents=True, exist_ok=True)
    print(f"[INFO] Results folder: {run_folder}\n")
    return run_folder


# ── Step 3: Run one query ─────────────────────────────────────────────────────

def _is_empty_answer(answer: str) -> bool:
    """Return True if the answer is a 'not found' response from the pipeline."""
    lower = answer.lower().strip()
    return any(signal in lower for signal in _NOT_FOUND_SIGNALS)


_ANSWER_PASS_THRESHOLD = 5  # minimum answer_score to count as passed


def run_single_query(query_obj: dict, project_id: str, difficulty: str = "easy") -> dict:
    """
    Call answer_question() for one query, evaluate answer quality, and return
    a structured result dict.

    Fields in the result:
        query_id          → from easy.json (e.g. "easy_001")
        query             → the question text
        project_id        → which project was queried
        timestamp         → when this query ran (ISO format)
        response_time_ms  → how long the full pipeline took
        expected_intent   → what easy.json says the classifier should return
        actual_intent     → what the pipeline actually classified it as
        intent_match      → True if expected == actual
        answer            → the LLM-generated answer text
        sources           → list of source dicts from the pipeline
        notice            → any notice string from the pipeline
        has_answer        → True if the answer is not a "not found" response
        answer_score      → int 1-10 from LLM evaluator (0 if eval failed)
        answer_evaluation → dict: checks_passed, checks_failed, violations, reasoning
        confidence_score  → float 0.0-1.0 composite (intent 40% + answer 40% + sources 20%)
        status            → "passed" | "failed" | "error"
        failure_reason    → "intent" | "answer" | "low_score" | null
        error             → exception message if status="error", else null
    """
    from app.services.answer_service import answer_question

    result = {
        "query_id":          query_obj["id"],
        "difficulty":        difficulty,
        "query":             query_obj["query"],
        "project_id":        project_id,
        "timestamp":         datetime.now().isoformat(),
        "response_time_ms":  None,
        "expected_intent":   query_obj["expected_intent"],
        "expected_mode":     query_obj.get("expected_mode"),        # optional routing mode check
        "actual_intent":     None,
        "actual_mode":       None,                                   # retrieval_mode from pipeline
        "intent_match":      None,
        "mode_match":        None,                                   # None when expected_mode not set
        "answer":            None,
        "sources":           [],
        "notice":            None,
        "has_answer":        None,
        "answer_score":      None,
        "answer_evaluation": None,
        "confidence_score":  None,
        "status":            "error",
        "failure_reason":    None,
        "error":             None,
        "pipeline_logs":     [],
    }

    capture          = _LogCapture()
    pipeline_loggers = [logging.getLogger(name) for name in _PIPELINE_LOGGERS]
    for log in pipeline_loggers:
        log.setLevel(logging.INFO)
        log.addHandler(capture)

    t_start = time.time()
    try:
        response = answer_question(query_obj["query"], project_id)

        result["response_time_ms"] = round((time.time() - t_start) * 1000)
        result["actual_intent"]    = response.get("intent")
        result["actual_mode"]      = response.get("retrieval_mode")
        result["answer"]           = response.get("answer", "")
        result["sources"]          = response.get("sources", [])
        result["notice"]           = response.get("notice")

        result["intent_match"] = (
            result["actual_intent"] == result["expected_intent"]
        )
        # Mode match: checked only when expected_mode is explicitly set in the query bank.
        # When present, mode_match overrides intent_match for pass/fail — routing correctness
        # is more meaningful than LLM intent label after the QueryIntent / routing decoupling.
        if result["expected_mode"] is not None:
            result["mode_match"] = (result["actual_mode"] == result["expected_mode"])

        result["has_answer"] = not _is_empty_answer(result["answer"])

        # ── Answer quality evaluation ─────────────────────────────────────────
        evaluation_hints = query_obj.get("evaluation_hints", {})
        eval_result = evaluate_answer(
            query=result["query"],
            answer=result["answer"],
            evaluation_hints=evaluation_hints,
            sources=result["sources"],
        )
        result["answer_score"]      = eval_result["score"]
        result["answer_evaluation"] = {
            "checks_passed": eval_result["checks_passed"],
            "checks_failed": eval_result["checks_failed"],
            "violations":    eval_result["violations"],
            "sources_cited": eval_result["sources_cited"],
            "reasoning":     eval_result["reasoning"],
            "eval_error":    eval_result["eval_error"],
        }

        # ── Confidence score ──────────────────────────────────────────────────
        # Use mode_match when available (more precise after QueryIntent/routing decoupling)
        routing_ok = (
            result["mode_match"]
            if result["mode_match"] is not None
            else result["intent_match"]
        )
        result["confidence_score"] = compute_confidence_score(
            intent_match=routing_ok,
            answer_score=result["answer_score"],
            has_sources=bool(result["sources"]),
        )

        # ── Pass / fail logic ─────────────────────────────────────────────────
        # routing_ok = mode_match when expected_mode is set, else intent_match.
        # This means queries with expected_mode pass/fail on routing accuracy, not
        # on the raw LLM intent label (which may differ from routing mode after decoupling).
        answer_pass = result["answer_score"] >= _ANSWER_PASS_THRESHOLD

        if routing_ok and result["has_answer"] and answer_pass:
            result["status"] = "passed"
        else:
            result["status"] = "failed"
            if not routing_ok:
                result["failure_reason"] = (
                    "mode"   if result["mode_match"] is not None else "intent"
                )
            elif not result["has_answer"]:
                result["failure_reason"] = "answer"
            else:
                result["failure_reason"] = "low_score"

    except Exception as e:
        result["response_time_ms"] = round((time.time() - t_start) * 1000)
        result["error"]  = str(e)
        result["status"] = "error"

    finally:
        for log in pipeline_loggers:
            log.removeHandler(capture)
        result["pipeline_logs"] = capture.lines

    return result


# ── Step 4: Save individual result ────────────────────────────────────────────

def save_result(result: dict, folder: Path) -> None:
    filename = f"{result['query_id']}_result.json"
    filepath = folder / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)


# ── Step 5: Print live progress ───────────────────────────────────────────────

_STATUS_ICON = {
    "passed": "PASS",
    "failed": "FAIL",
    "error":  "ERR ",
}

def print_progress(result: dict, index: int, total: int) -> None:
    eval_err   = (result.get("answer_evaluation") or {}).get("eval_error")
    # Show EVAL_ERR on the progress line when the evaluator itself failed
    if result["status"] == "failed" and eval_err:
        icon = "EVAL"
    else:
        icon = _STATUS_ICON.get(result["status"], "??? ")

    ms         = result["response_time_ms"] or 0
    intent     = result["actual_intent"] or "unknown"
    query      = result["query"][:45].ljust(45)
    score      = result.get("answer_score")
    confidence = result.get("confidence_score")

    score_str = f"  score={score}/10" if score is not None else ""
    conf_str  = f"  conf={confidence:.2f}" if confidence is not None else ""

    routing_note = ""
    if result.get("mode_match") is not None:
        # expected_mode was set — show mode mismatch info
        if result["mode_match"] is False:
            routing_note = f"  [mode: expected={result['expected_mode']} got={result['actual_mode']}]"
    elif result["intent_match"] is False:
        routing_note = f"  [expected={result['expected_intent']}]"

    eval_note = "  [eval_api_err]" if eval_err else ""

    print(f"  [{index:02d}/{total}] {icon}  {ms:>5}ms  {query}  intent={intent}{routing_note}{score_str}{conf_str}{eval_note}")


# ── Step 6: Save run metadata ─────────────────────────────────────────────────

def save_run_metadata(
    results: list[dict],
    run_folder: Path,
    project_id: str,
    total_ms: int,
    difficulty: str = "easy",
) -> None:
    """
    Write run_metadata.json one level above the difficulty folder.
    This gives report_generator.py a single file to read for the summary.
    """
    passed  = sum(1 for r in results if r["status"] == "passed")
    failed  = sum(1 for r in results if r["status"] == "failed")
    errors  = sum(1 for r in results if r["status"] == "error")
    total   = len(results)
    avg_ms  = round(sum(r["response_time_ms"] or 0 for r in results) / total) if total else 0

    scored  = [r for r in results if r.get("answer_score") is not None]
    avg_score = round(sum(r["answer_score"] for r in scored) / len(scored), 1) if scored else None
    avg_conf  = round(
        sum(r["confidence_score"] for r in results if r.get("confidence_score") is not None)
        / total, 2
    ) if total else None

    intent_mismatches = [
        {
            "query_id":        r["query_id"],
            "query":           r["query"],
            "expected_intent": r["expected_intent"],
            "actual_intent":   r["actual_intent"],
        }
        for r in results
        if r["intent_match"] is False
    ]

    low_score_failures = [
        {
            "query_id":    r["query_id"],
            "query":       r["query"],
            "answer_score": r.get("answer_score"),
            "reasoning":   (r.get("answer_evaluation") or {}).get("reasoning", ""),
        }
        for r in results
        if r.get("failure_reason") == "low_score"
    ]

    metadata = {
        "run_timestamp":       datetime.now().isoformat(),
        "project_id":          project_id,
        "difficulty":          difficulty,
        "total_queries":       total,
        "passed":              passed,
        "failed":              failed,
        "errors":              errors,
        "pass_rate_pct":       round(passed / total * 100, 1) if total else 0,
        "total_time_ms":       total_ms,
        "avg_response_ms":     avg_ms,
        "avg_answer_score":    avg_score,
        "avg_confidence_score": avg_conf,
        "intent_mismatches":   intent_mismatches,
        "low_score_failures":  low_score_failures,
    }

    # Save in the parent of the 'easy' folder (i.e. the timestamp folder)
    meta_path = run_folder.parent / "run_metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"\n[INFO] Run metadata saved: {meta_path}")


# ── Step 7: Print final summary ───────────────────────────────────────────────

def print_summary(results: list[dict], total_ms: int, difficulty: str = "easy") -> None:
    passed = sum(1 for r in results if r["status"] == "passed")
    failed = sum(1 for r in results if r["status"] == "failed")
    errors = sum(1 for r in results if r["status"] == "error")
    total  = len(results)

    scored    = [r for r in results if r.get("answer_score") is not None]
    avg_score = round(sum(r["answer_score"] for r in scored) / len(scored), 1) if scored else "n/a"
    avg_conf  = round(
        sum(r["confidence_score"] for r in results if r.get("confidence_score") is not None)
        / total, 2
    ) if total else "n/a"

    print(f"\n{'='*60}")
    print(f"  RESULTS — {difficulty.capitalize()} Level")
    print(f"{'='*60}")
    print(f"  Total         : {total}")
    print((f"  Passed        : {passed}  ({round(passed/total*100)}%)") if total else "  Passed  : 0")
    print(f"  Failed        : {failed}")
    print(f"  Errors        : {errors}")
    print(f"  Avg score     : {avg_score}/10")
    print(f"  Avg confidence: {avg_conf}")
    print(f"  Time          : {total_ms}ms total")
    print(f"{'='*60}")

    failures = [r for r in results if r["status"] != "passed"]
    if failures:
        print("\n  Failed queries:")
        for r in failures:
            reason    = r.get("failure_reason", "")
            eval_err  = (r.get("answer_evaluation") or {}).get("eval_error")
            if r["status"] == "error":
                print(f"    {r['query_id']}  PIPELINE_ERR -> {r['error']}")
            elif eval_err:
                # Evaluator itself failed — score=0 is not a real score
                print(f"    {r['query_id']}  EVAL_ERR     -> evaluator API failed: {eval_err[:60]}")
            elif reason == "mode":
                print(f"    {r['query_id']}  MODE         -> expected={r['expected_mode']}  got={r['actual_mode']}")
            elif reason == "intent":
                print(f"    {r['query_id']}  INTENT       -> expected={r['expected_intent']}  got={r['actual_intent']}")
            elif reason == "answer":
                print(f"    {r['query_id']}  NO ANSWER    -> pipeline returned not-found response")
            elif reason == "low_score":
                score     = r.get("answer_score", "?")
                reasoning = (r.get("answer_evaluation") or {}).get("reasoning", "")
                print(f"    {r['query_id']}  LOW SCORE    -> score={score}/10  {reasoning[:80]}")
    else:
        print("\n  All queries passed.")


# ── Main ──────────────────────────────────────────────────────────────────────

def _apply_filters(queries: list[dict], ids: str | None, tags: str | None) -> list[dict]:
    """
    Filter queries by --ids and/or --tags.

    --ids  ml_005,ml_019      → run only those query IDs (comma-separated)
    --tags decision,commitment → run only queries whose tags list contains ANY of the given tags
    Both filters can be combined — a query must match BOTH to be included.
    """
    result = queries

    if ids:
        id_set = {x.strip() for x in ids.split(",") if x.strip()}
        result = [q for q in result if q["id"] in id_set]
        missing = id_set - {q["id"] for q in result}
        if missing:
            print(f"[WARN] --ids: no queries found for: {', '.join(sorted(missing))}")

    if tags:
        tag_set = {x.strip().lower() for x in tags.split(",") if x.strip()}
        result = [q for q in result if tag_set & {t.lower() for t in q.get("tags", [])}]

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run test queries against the RAG pipeline"
    )
    parser.add_argument(
        "--project-id",
        type=str,
        required=True,
        help="Project ID to query (e.g. proj_nolocode_001)",
    )
    parser.add_argument(
        "--difficulty",
        type=str,
        default="easy",
        choices=["easy", "medium", "hard"],
        help="Query difficulty level to run (default: easy)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List queries that would run without calling the pipeline",
    )
    parser.add_argument(
        "--ids",
        type=str,
        default=None,
        help="Comma-separated query IDs to run (e.g. --ids mm_001,mm_005)",
    )
    parser.add_argument(
        "--tags",
        type=str,
        default=None,
        help="Comma-separated tags to filter by (e.g. --tags compound,analytical). "
             "Queries matching ANY listed tag are included.",
    )
    args = parser.parse_args()

    difficulty = args.difficulty

    print(f"\n{'='*55}")
    print(f"  Test Runner — {difficulty.capitalize()} Level")
    print(f"  Project: {args.project_id}")
    if args.ids:
        print(f"  Filter (ids) : {args.ids}")
    if args.tags:
        print(f"  Filter (tags): {args.tags}")
    print(f"{'='*55}\n")

    # Step 1: Load queries from the chosen difficulty bank
    query_file = _QUERY_BANK[difficulty]
    queries = load_queries(query_file)

    # Apply --ids / --tags filters
    queries = _apply_filters(queries, args.ids, args.tags)
    if not queries:
        print("[ERROR] No queries matched the filter. Check --ids or --tags.")
        sys.exit(1)
    if args.ids or args.tags:
        print(f"[INFO] Running {len(queries)} query/queries after filter\n")

    # Dry run — just list the queries and exit
    if args.dry_run:
        print("\n[DRY RUN] Queries that would run:")
        for q in queries:
            print(f"  {q['id']}  {q['expected_intent']:<25}  \"{q['query'][:55]}\"")
        print(f"\nTotal: {len(queries)} queries. Run without --dry-run to execute.")
        return

    # Step 2: Create output folder
    run_folder = create_run_folder(difficulty)

    # Step 3–5: Run each query, save result, print progress
    results   = []
    t_run_start = time.time()

    print(f"  {'#':>5}  {'STATUS':<6}  {'TIME':>7}  {'QUERY':<50}  INTENT")
    print(f"  {'-'*5}  {'-'*6}  {'-'*7}  {'-'*50}  {'-'*20}")

    for i, query_obj in enumerate(queries, 1):
        result = run_single_query(query_obj, args.project_id, difficulty)
        results.append(result)

        # Step 4: Save individual result file
        save_result(result, run_folder)

        # Step 5: Print live progress line
        print_progress(result, i, len(queries))

    total_ms = round((time.time() - t_run_start) * 1000)

    # Step 6: Save run_metadata.json
    save_run_metadata(results, run_folder, args.project_id, total_ms, difficulty)

    # Step 7: Print final summary
    print_summary(results, total_ms, difficulty)


if __name__ == "__main__":
    main()
