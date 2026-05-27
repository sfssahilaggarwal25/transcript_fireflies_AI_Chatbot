"""
run_tests.py — Master test runner

Chains: test_runner → report_generator → open summary.md

All test levels run under the SAME run_id so their results land in one
timestamped folder:

    test_results/<run_id>/easy/      ← easy result JSON files
    test_results/<run_id>/medium/    ← medium result JSON files
    test_results/<run_id>/hard/      ← hard result JSON files (when available)
    test_results/<run_id>/run_metadata.json   ← metadata for last difficulty run
    test_results/<run_id>/<difficulty>_summary.md  ← one report per difficulty

Usage:
    python -m app.tests.run_tests --project-id proj_nolocode_001
    python -m app.tests.run_tests --project-id proj_nolocode_001 --difficulty medium
    python -m app.tests.run_tests --project-id proj_nolocode_001 --difficulty all
    python -m app.tests.run_tests --project-id proj_nolocode_001 --difficulty all --no-open
    python -m app.tests.run_tests --project-id proj_nolocode_001 --ids easy_001,easy_003
    python -m app.tests.run_tests --project-id proj_nolocode_001 --tags decision,commitment
"""

import platform
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ── Paths ─────────────────────────────────────────────────────────────────────

_TESTS_DIR   = Path(__file__).parent
_RESULTS_DIR = _TESTS_DIR / "test_results"

_ALL_DIFFICULTIES = ["easy", "medium", "hard"]


# ── Step 1: Run one difficulty level ──────────────────────────────────────────

def _run_difficulty(
    difficulty: str,
    project_id: str,
    run_id: str,
    ids: str | None = None,
    tags: str | None = None,
) -> Path | None:
    """
    Run the test suite for one difficulty level and save results to
    test_results/<run_id>/<difficulty>/.

    Returns the difficulty subfolder on success, None if the query bank is
    missing or no queries matched the filter.
    """
    from app.rag.tests.test_runner import (
        _QUERY_BANK,
        _apply_filters,
        load_queries,
        run_single_query,
        save_result,
        save_run_metadata,
        print_progress,
        print_summary,
    )

    query_file = _QUERY_BANK.get(difficulty)
    if query_file is None or not query_file.exists():
        print(f"[SKIP] No query bank for '{difficulty}': {query_file}")
        print(f"       Generate one with: python -m app.tests.query_generator --project-id {project_id}")
        return None

    queries = load_queries(query_file)
    queries = _apply_filters(queries, ids, tags)

    if not queries:
        print(f"[WARN] No queries matched the filter for '{difficulty}'. Skipping.")
        return None

    # Create the difficulty subfolder inside the shared run_id folder
    run_folder = _RESULTS_DIR / run_id / difficulty
    run_folder.mkdir(parents=True, exist_ok=True)
    print(f"[INFO] Results folder: {run_folder}\n")

    results   = []
    t_start   = time.time()

    print(f"  {'#':>5}  {'STATUS':<6}  {'TIME':>7}  {'QUERY':<50}  INTENT")
    print(f"  {'-'*5}  {'-'*6}  {'-'*7}  {'-'*50}  {'-'*20}")

    for i, q in enumerate(queries, 1):
        result = run_single_query(q, project_id, difficulty)
        results.append(result)
        save_result(result, run_folder)
        print_progress(result, i, len(queries))

    total_ms = round((time.time() - t_start) * 1000)

    # Writes run_metadata.json one level up (the run_id folder)
    save_run_metadata(results, run_folder, project_id, total_ms, difficulty)

    print_summary(results, total_ms, difficulty)
    return run_folder


# ── Step 2: Generate report for one difficulty ─────────────────────────────────

def _generate_report(diff_folder: Path) -> Path:
    """
    Generate summary.md for a completed difficulty run.

    diff_folder  is the difficulty subfolder  (e.g. test_results/<run_id>/easy).
    The parent    is the run_id folder         (e.g. test_results/<run_id>).
    run_metadata.json lives in the parent.

    The report is written to test_results/<run_id>/<difficulty>_summary.md so
    multiple difficulty reports coexist under the same run_id folder.
    """
    from app.rag.tests.report_generator import load_run_data, write_report

    parent   = diff_folder.parent   # run_id folder
    metadata, results = load_run_data(parent)

    # Override the default output path so each difficulty gets its own file
    difficulty  = metadata.get("difficulty", diff_folder.name)
    output_path = parent / f"{difficulty}_summary.md"

    # write_report() normally writes to run_folder / "summary.md" — we monkey-patch
    # the path by writing directly:
    from app.rag.tests.report_generator import (
        _section_header,
        _section_summary,
        _section_results_table,
        _section_answer_quality,
        _section_intent_breakdown,
        _section_failures,
        _section_sources,
    )

    sections = [
        _section_header(metadata),
        "---\n",
        _section_summary(metadata),
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
    output_path.write_text(report, encoding="utf-8")

    return output_path


# ── Step 3: Open the report file ──────────────────────────────────────────────

def _open_file(path: Path) -> None:
    """Open a file using the OS default handler (VS Code on macOS if set)."""
    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.run(["open", str(path)], check=False)
        elif system == "Windows":
            subprocess.run(["start", str(path)], shell=True, check=False)
        else:
            subprocess.run(["xdg-open", str(path)], check=False)
    except Exception as exc:
        print(f"[WARN] Could not auto-open file: {exc}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Master test runner — chains test_runner → report_generator → open report.\n"
            "Run a single difficulty or all levels in one command."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--project-id",
        required=True,
        metavar="ID",
        help="Project ID to query (e.g. proj_nolocode_001)",
    )
    parser.add_argument(
        "--difficulty",
        default="easy",
        choices=["easy", "medium", "hard", "all"],
        help=(
            "Difficulty level to run (default: easy). "
            "'all' runs easy → medium → hard in sequence."
        ),
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Do not auto-open the report after the run completes",
    )
    parser.add_argument(
        "--ids",
        default=None,
        metavar="ID_LIST",
        help="Comma-separated query IDs to run (e.g. --ids easy_001,easy_003). Passed to test_runner.",
    )
    parser.add_argument(
        "--tags",
        default=None,
        metavar="TAG_LIST",
        help=(
            "Comma-separated tags to filter by (e.g. --tags decision,commitment). "
            "Queries matching ANY listed tag are included. Passed to test_runner."
        ),
    )
    args = parser.parse_args()

    difficulties = _ALL_DIFFICULTIES if args.difficulty == "all" else [args.difficulty]
    run_id       = datetime.now().strftime("%Y-%m-%d_%H-%M")

    print(f"\n{'='*62}")
    print(f"  AI Meeting Intelligence — Master Test Runner")
    print(f"  Project    : {args.project_id}")
    print(f"  Level(s)   : {', '.join(d.capitalize() for d in difficulties)}")
    print(f"  Run ID     : {run_id}")
    if args.ids:
        print(f"  Filter IDs : {args.ids}")
    if args.tags:
        print(f"  Filter tags: {args.tags}")
    print(f"{'='*62}")

    report_paths: list[Path] = []

    for difficulty in difficulties:
        print(f"\n{'─'*62}")
        print(f"  ▶  {difficulty.capitalize()} Level")
        print(f"{'─'*62}")

        diff_folder = _run_difficulty(
            difficulty  = difficulty,
            project_id  = args.project_id,
            run_id      = run_id,
            ids         = args.ids,
            tags        = args.tags,
        )
        if diff_folder is None:
            continue  # query bank missing or no queries matched — skip

        report_path = _generate_report(diff_folder)
        report_paths.append(report_path)
        print(f"\n[REPORT] {report_path.relative_to(_TESTS_DIR)}")

    # ── Final summary ──────────────────────────────────────────────────────────
    print(f"\n{'='*62}")
    if not report_paths:
        print("  No runs completed — check query bank files and --ids / --tags.")
        print(f"{'='*62}\n")
        sys.exit(1)

    print(f"  Run complete.  ID: {run_id}")
    print(f"  Reports:")
    for rp in report_paths:
        print(f"    {rp}")
    print(f"{'='*62}\n")

    if not args.no_open:
        # Open the last report (highest difficulty that completed)
        print("[INFO] Opening report...")
        _open_file(report_paths[-1])


if __name__ == "__main__":
    main()
