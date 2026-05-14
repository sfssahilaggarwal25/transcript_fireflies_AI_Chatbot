"""
test_queries.py — Run all test questions against the live system

Usage:
    uv run python test_queries.py              # run all questions
    uv run python test_queries.py decision     # run only one type
    uv run python test_queries.py commitment summary speaker

Types you can filter by:
    decision  commitment  summary  speaker  timeline  general  edge
"""

import sys
import io
import time
import os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from app.services.answer_service import answer_question

PROJECT_ID = "proj_nolocode_001"

# ─────────────────────────────────────────────────────────────────────────────
# TEST QUESTIONS
# Add new questions here as you test more things.
# Format: (query_type, question, what_correct_answer_must_contain)
#   - query_type          : which intent type this should trigger
#   - question            : the actual question text
#   - must_contain        : list of keywords the answer MUST mention (leave [] to skip check)
# ─────────────────────────────────────────────────────────────────────────────

TEST_QUESTIONS = [

    # ── TYPE 1: DECISION ────────────────────────────────────────────────────
    (
        "decision",
        "What was decided about the accumulated depreciation row?",
        ["accumulated depreciation", "remove"],
    ),
    (
        "decision",
        "What was decided about the ONCA forecasting numbers?",
        ["ONCA", "goodwill"],
    ),
    (
        "decision",
        "What was the final decision on fixed assets calculation?",
        ["accumulated depreciation", "property"],  # PP closing may not always appear verbatim
    ),
    (
        "general",
        "What happened with the CE code in the database?",  # "resolved" doesn't trigger decision intent
        ["CE"],
    ),

    # ── TYPE 2: COMMITMENT ──────────────────────────────────────────────────
    (
        "commitment",
        "What action items were assigned and who is responsible?",
        ["Project Manager SFS", "timeline"],
    ),
    (
        "commitment",
        "Who committed to providing the timeline for the AI module?",
        ["Project Manager SFS"],
    ),
    (
        "commitment",
        "What did the project manager commit to doing after this meeting?",
        ["internal team", "timeline"],
    ),
    (
        "commitment",
        "What did Bhavneet commit to checking?",
        ["Bhavneet", "Ashpreet"],
    ),

    # ── TYPE 4: SUMMARY ─────────────────────────────────────────────────────
    (
        "summary",
        "Give me a summary of the project so far",
        ["forecasting", "ONCA"],
    ),
    (
        "summary",
        "What was this meeting about?",
        [],
    ),
    (
        "summary",
        "Give me an overview of what was discussed in the Nolocode meeting",
        [],
    ),

    # ── TYPE 5: SPEAKER ─────────────────────────────────────────────────────
    (
        "speaker",
        "What did Ngumi say about the confusion with the questions?",
        ["confusion", "questions"],
    ),
    (
        "speaker",
        "What did Karan mention about the fixed assets formula?",
        ["fixed"],
    ),
    (
        "speaker",
        "What questions did Bhavneet raise in the meeting?",
        [],
    ),
    (
        "speaker",
        "What did Project Manager SFS say about the forecasting formulas?",
        [],
    ),

    # ── TYPE 6: TIMELINE ────────────────────────────────────────────────────
    (
        "timeline",
        "What is the deadline for providing the timeline?",
        [],
    ),
    (
        "timeline",
        "When will the project manager provide the updated timelines?",
        [],
    ),

    # ── GENERAL ─────────────────────────────────────────────────────────────
    (
        "general",
        "What was discussed about the OCA calculation?",
        ["OCA", "prepaid"],
    ),
    (
        "general",
        "What is the ONCA formula that was agreed upon?",
        ["ONCA"],
    ),
    (
        "general",
        "What was the problem with the CE code in the database?",
        ["CE", "database"],
    ),
    (
        "general",
        "What was discussed about cash flow from financing activities?",
        ["financing", "cash flow"],
    ),
    (
        "general",
        "Why was accumulated depreciation removed from the balance sheet?",
        ["accumulated depreciation"],
    ),
    (
        "general",
        "What is the formula for calculating prepaid OCA?",
        ["prepaid", "close"],
    ),

    # ── TYPE 1: DECISION (meeting 2) ────────────────────────────────────────
    (
        "decision",
        "Was a decision made on which approach to use for the stress test AI module?",
        ["approach"],
    ),

    # ── TYPE 6: TIMELINE (cross-meeting, requires per-meeting retrieval) ───────
    (
        "timeline",
        "How did the discussion about the AI module change between the two meetings?",
        ["2026", "approach"],
    ),
    (
        "timeline",
        "What changed in the project from the first meeting to the second meeting?",
        [],
    ),

    # ── TYPE 5: SPEAKER (meeting 2 — Harsh Vardhan) ─────────────────────────
    (
        "speaker",
        "What did Harsh Vardhan say about approach 2 for stress testing?",
        ["Harsh Vardhan", "approach"],
    ),

    # ── TYPE 2: COMMITMENT (meeting 2 content) ──────────────────────────────
    (
        "commitment",
        "What did Harsh Vardhan commit to in the AI meeting?",
        ["Harsh Vardhan"],
    ),

    # ── EDGE CASES (should return "not found") ──────────────────────────────
    (
        "edge",
        "What was discussed about the homepage design?",
        [],   # answer should say not found — no must_contain check
    ),
    (
        "edge",
        "What is the project budget?",
        [],   # answer should say not found — no must_contain check
    ),
]

# ─────────────────────────────────────────────────────────────────────────────

def check_answer(answer: str, must_contain: list[str]) -> tuple[bool, list[str]]:
    """Returns (passed, missing_keywords)."""
    if not must_contain:
        return True, []
    missing = [kw for kw in must_contain if kw.lower() not in answer.lower()]
    return len(missing) == 0, missing


def run_tests(filter_types: list[str] = None):
    questions = TEST_QUESTIONS
    if filter_types:
        questions = [q for q in TEST_QUESTIONS if q[0] in filter_types]

    if not questions:
        print(f"No questions found for types: {filter_types}")
        return

    print()
    print("=" * 70)
    print(f"  TEST RUN — {len(questions)} questions | project: {PROJECT_ID}")
    print("=" * 70)

    passed = 0
    failed = 0
    errors = 0
    results = []

    for i, (qtype, question, must_contain) in enumerate(questions, 1):
        print(f"\n[{i}/{len(questions)}] [{qtype.upper()}]")
        print(f"  Q: {question}")

        try:
            t0 = time.time()
            result = answer_question(question, PROJECT_ID)
            elapsed = time.time() - t0

            intent = result["intent"]
            answer = result["answer"]
            sources = result["sources"]

            ok, missing = check_answer(answer, must_contain)

            if ok:
                status = "PASS"
                passed += 1
            else:
                status = "FAIL"
                failed += 1

            print(f"  Status  : {status}")
            print(f"  Intent  : {intent}")
            print(f"  Sources : {len(sources)}")
            print(f"  Time    : {elapsed:.1f}s")
            print(f"  Answer  : {answer[:200]}{'...' if len(answer) > 200 else ''}")

            if missing:
                print(f"  MISSING keywords in answer: {missing}")

            results.append((qtype, question, status, intent, elapsed))

        except Exception as e:
            errors += 1
            status = "ERROR"
            print(f"  Status  : ERROR — {str(e)[:120]}")
            results.append((qtype, question, "ERROR", "—", 0))

        time.sleep(1)  # avoid SSL rate-throttling on rapid consecutive embedding calls

    # ── SUMMARY ──────────────────────────────────────────────────────────────
    print()
    print("=" * 70)
    print("  RESULTS SUMMARY")
    print("=" * 70)
    print(f"  Total   : {len(questions)}")
    print(f"  Passed  : {passed}")
    print(f"  Failed  : {failed}")
    print(f"  Errors  : {errors}")
    print()

    if failed > 0 or errors > 0:
        print("  Failed / Errored questions:")
        for qtype, question, status, intent, _ in results:
            if status in ("FAIL", "ERROR"):
                print(f"    [{status}] [{qtype}] {question[:60]}")
    else:
        print("  All questions passed.")

    total_time = sum(r[4] for r in results)
    if total_time > 0:
        print(f"\n  Total time  : {total_time:.1f}s")
        print(f"  Avg per Q   : {total_time / len(questions):.1f}s")

    print()
    print("=" * 70)
    print()


if __name__ == "__main__":
    filter_types = [a.lower() for a in sys.argv[1:]] if len(sys.argv) > 1 else None
    run_tests(filter_types)
