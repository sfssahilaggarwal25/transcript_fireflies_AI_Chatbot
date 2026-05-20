"""
report_generator.py

Reads all result JSON files from a test run and generates summary.md.

Usage:
    python -m app.tests.report_generator                        # latest run
    python -m app.tests.report_generator --run 2026-05-20_11-06  # specific run
"""

import argparse
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────

_TESTS_DIR   = Path(__file__).parent
_RESULTS_DIR = _TESTS_DIR / "test_results"


# ── Step 1: Find the run folder ───────────────────────────────────────────────

def find_run_folder(run_id: str | None) -> Path:
    """
    If run_id given (e.g. "2026-05-20_11-06") → use that folder directly.
    Otherwise → pick the most recently created run folder.
    """
    if not _RESULTS_DIR.exists():
        print(f"[ERROR] test_results/ folder not found at {_RESULTS_DIR}")
        print("        Run the test runner first: python -m app.tests.test_runner --project-id <id>")
        sys.exit(1)

    if run_id:
        folder = _RESULTS_DIR / run_id
        if not folder.exists():
            print(f"[ERROR] Run folder not found: {folder}")
            sys.exit(1)
        return folder

    # Auto-find latest — folders are named by timestamp so lexicographic sort works
    run_folders = sorted(
        [f for f in _RESULTS_DIR.iterdir() if f.is_dir()],
        reverse=True,
    )
    if not run_folders:
        print("[ERROR] No test runs found in test_results/")
        sys.exit(1)

    latest = run_folders[0]
    print(f"[INFO] Using latest run: {latest.name}")
    return latest


# ── Step 2: Load all data ─────────────────────────────────────────────────────

def load_run_data(run_folder: Path) -> tuple[dict, list[dict]]:
    """
    Returns (metadata, results_sorted_by_id).
    Exits if run_metadata.json or the easy/ subfolder is missing.
    """
    meta_path = run_folder / "run_metadata.json"
    if not meta_path.exists():
        print(f"[ERROR] run_metadata.json not found in {run_folder}")
        sys.exit(1)

    with open(meta_path, encoding="utf-8") as f:
        metadata = json.load(f)

    easy_folder = run_folder / "easy"
    if not easy_folder.exists():
        print(f"[ERROR] easy/ subfolder not found in {run_folder}")
        sys.exit(1)

    result_files = sorted(easy_folder.glob("*_result.json"))
    if not result_files:
        print(f"[ERROR] No result files found in {easy_folder}")
        sys.exit(1)

    results = []
    for fp in result_files:
        with open(fp, encoding="utf-8") as f:
            results.append(json.load(f))

    print(f"[INFO] Loaded {len(results)} result files + run_metadata.json")
    return metadata, results


# ── Step 3: Build each section of the report ──────────────────────────────────

def _section_header(meta: dict) -> str:
    run_ts  = meta.get("run_timestamp", "")
    project = meta.get("project_id", "unknown")
    now     = datetime.now().strftime("%Y-%m-%d %H:%M")

    return (
        f"# Test Report — Easy Level\n\n"
        f"**Project:** `{project}`  \n"
        f"**Run timestamp:** {run_ts}  \n"
        f"**Report generated:** {now}  \n"
    )


def _section_summary(meta: dict) -> str:
    passed    = meta["passed"]
    failed    = meta["failed"]
    errors    = meta["errors"]
    total     = meta["total_queries"]
    rate      = meta["pass_rate_pct"]
    avg_ms    = meta["avg_response_ms"]
    total_ms  = meta["total_time_ms"]
    avg_score = meta.get("avg_answer_score", "n/a")
    avg_conf  = meta.get("avg_confidence_score", "n/a")

    filled = round(rate / 100 * 20)
    bar    = "█" * filled + "░" * (20 - filled)

    lines = [
        "## Summary\n",
        f"Pass rate: `[{bar}]` **{rate}%**\n",
        "| Metric | Value |",
        "|---|---|",
        f"| Total queries | {total} |",
        f"| Passed | {passed} |",
        f"| Failed | {failed} |",
        f"| Errors | {errors} |",
        f"| Avg answer score | {avg_score}/10 |",
        f"| Avg confidence | {avg_conf} |",
        f"| Avg response time | {avg_ms:,}ms |",
        f"| Total run time | {total_ms/1000:.1f}s |",
    ]
    return "\n".join(lines) + "\n"



def _intent_status(r: dict) -> str:
    if r["status"] == "error":
        return "ERR"
    reason = r.get("failure_reason")
    if reason == "intent":
        return "FAIL — wrong intent"
    if reason == "answer":
        return "FAIL — no answer"
    if reason == "low_score":
        return "FAIL — low score"
    return "PASS"


def _section_results_table(results: list[dict]) -> str:
    lines = [
        "## Results\n",
        "| ID | Query | Status | Score | Confidence | Expected Intent | Actual Intent | Time |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        qid        = r["query_id"]
        query      = r["query"][:50] + ("…" if len(r["query"]) > 50 else "")
        status     = _intent_status(r)
        score      = f"{r['answer_score']}/10" if r.get("answer_score") is not None else "—"
        confidence = f"{r['confidence_score']:.2f}" if r.get("confidence_score") is not None else "—"
        expected   = r.get("expected_intent", "—")
        actual     = r.get("actual_intent") or "—"
        ms         = f"{r['response_time_ms']:,}ms" if r["response_time_ms"] else "—"

        if r["status"] != "passed":
            actual = f"**{actual}**"

        lines.append(f"| {qid} | {query} | {status} | {score} | {confidence} | {expected} | {actual} | {ms} |")

    return "\n".join(lines) + "\n"


def _section_failures(results: list[dict]) -> str:
    failures = [r for r in results if r["status"] != "passed"]
    if not failures:
        return "## Failed Queries\n\nAll queries passed. No failures to report.\n"

    lines = ["## Failed Queries\n"]

    for r in failures:
        status_label = _intent_status(r)
        lines.append(f"### {r['query_id']} — {status_label}\n")
        lines.append(f"**Query:** \"{r['query']}\"\n")

        reason = r.get("failure_reason")

        if r["status"] == "error":
            lines.append(f"**Error:** `{r['error']}`\n")

        elif reason == "intent":
            lines.append(f"**Expected intent:** `{r['expected_intent']}`  ")
            lines.append(f"**Actual intent:** `{r['actual_intent']}`\n")
            lines.append(
                "> The classifier routed this query to the wrong retrieval path. "
                "Check the pipeline trace below — look at the `[1/5] UNDERSTAND QUERY` step "
                "to see why the LLM or regex chose the wrong intent.\n"
            )

        elif reason == "answer":
            lines.append(f"**Intent:** `{r['actual_intent']}` (correct)  \n")
            lines.append(
                "> The intent was classified correctly but the pipeline returned "
                "a 'not found' response. Check the `[2/5] RETRIEVE` step in the "
                "trace below — likely no chunks were retrieved for this query.\n"
            )

        elif reason == "low_score":
            score = r.get("answer_score", "?")
            conf  = r.get("confidence_score", "?")
            eval_ = r.get("answer_evaluation") or {}
            lines.append(f"**Intent:** `{r['actual_intent']}` (correct)  ")
            lines.append(f"**Answer score:** {score}/10  **Confidence:** {conf}\n")
            if eval_.get("reasoning"):
                lines.append(f"> **Evaluator:** {eval_['reasoning']}\n")
            if eval_.get("checks_failed"):
                failed_str = ", ".join(f"`{c}`" for c in eval_["checks_failed"])
                lines.append(f"**Missing:** {failed_str}  \n")
            if eval_.get("violations"):
                viol_str = ", ".join(f"`{v}`" for v in eval_["violations"])
                lines.append(f"**Violations found:** {viol_str}  \n")

        # Pipeline trace
        logs = r.get("pipeline_logs", [])
        if logs:
            lines.append("**Pipeline trace:**")
            lines.append("```")
            lines.extend(logs)
            lines.append("```")
        else:
            lines.append("*No pipeline logs captured.*")

        lines.append("")

    return "\n".join(lines) + "\n"


def _section_sources(results: list[dict]) -> str:
    counter: Counter = Counter()
    for r in results:
        for src in r.get("sources", []):
            title = src.get("meeting_title", "Unknown")
            date  = src.get("meeting_date", "")
            counter[f"{title} ({date})"] += 1

    lines = ["## Sources Referenced\n"]
    if not counter:
        lines.append("No source data available.\n")
    else:
        lines.append("How often each meeting was used to answer queries:\n")
        lines.append("| Meeting | Times referenced |")
        lines.append("|---|---|")
        for meeting, count in counter.most_common():
            lines.append(f"| {meeting} | {count} |")

    return "\n".join(lines) + "\n"


def _section_answer_quality(results: list[dict]) -> str:
    scored = [r for r in results if r.get("answer_score") is not None]
    if not scored:
        return "## Answer Quality\n\nNo answer scores available (evaluator did not run).\n"

    lines = [
        "## Answer Quality\n",
        "LLM evaluator scores each answer 1–10 against the query bank's `evaluation_hints`.\n",
        "| ID | Score | Confidence | Checks Passed | Checks Failed | Evaluator Reasoning |",
        "|---|---|---|---|---|---|",
    ]
    for r in scored:
        score = r.get("answer_score", "—")
        conf  = f"{r['confidence_score']:.2f}" if r.get("confidence_score") is not None else "—"
        eval_ = r.get("answer_evaluation") or {}

        passed_str = "; ".join(eval_.get("checks_passed", [])) or "—"
        failed_str = "; ".join(eval_.get("checks_failed", [])) or "—"
        reasoning  = (eval_.get("reasoning") or "—")[:100]

        lines.append(f"| {r['query_id']} | {score}/10 | {conf} | {passed_str} | {failed_str} | {reasoning} |")

    return "\n".join(lines) + "\n"


def _section_intent_breakdown(results: list[dict]) -> str:
    intent_stats: dict[str, dict] = {}
    for r in results:
        intent = r.get("expected_intent", "unknown")
        if intent not in intent_stats:
            intent_stats[intent] = {"total": 0, "passed": 0}
        intent_stats[intent]["total"] += 1
        if r["status"] == "passed":
            intent_stats[intent]["passed"] += 1

    lines = ["## Intent Breakdown\n"]
    lines.append("Pass rate per intent type — useful for spotting which classifier path is weakest:\n")
    lines.append("| Intent | Passed | Total | Pass Rate |")
    lines.append("|---|---|---|---|")
    for intent, stats in sorted(intent_stats.items()):
        t    = stats["total"]
        p    = stats["passed"]
        rate = f"{round(p/t*100)}%" if t else "—"
        lines.append(f"| {intent} | {p} | {t} | {rate} |")

    return "\n".join(lines) + "\n"


# ── Step 4: Write summary.md ──────────────────────────────────────────────────

def write_report(run_folder: Path, meta: dict, results: list[dict]) -> Path:
    sections = [
        _section_header(meta),
        "---\n",
        _section_summary(meta),
        "---\n",
        _section_results_table(results),
        "---\n",
        _section_answer_quality(results),
        "---\n",
        _section_intent_breakdown(results),
        "---\n",
        _section_failures(results),
        "---\n",
        _section_sources(results),
    ]

    report = "\n".join(sections)
    output_path = run_folder / "summary.md"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    return output_path


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate summary.md from a test run"
    )
    parser.add_argument(
        "--run",
        type=str,
        default=None,
        help="Run folder name (e.g. 2026-05-20_11-06). Defaults to latest run.",
    )
    args = parser.parse_args()

    print(f"\n{'='*55}")
    print(f"  Report Generator")
    print(f"{'='*55}\n")

    run_folder        = find_run_folder(args.run)
    metadata, results = load_run_data(run_folder)

    output_path = write_report(run_folder, metadata, results)

    print(f"[DONE] Report written: {output_path}")
    print(f"\n       Open it in your IDE or run:")
    print(f"       code \"{output_path}\"")


if __name__ == "__main__":
    main()
