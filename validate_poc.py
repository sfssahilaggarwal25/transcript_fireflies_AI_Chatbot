"""
validate_poc.py — Phase 5 validation: scope isolation, multi-meeting synthesis, speed test
"""
import sys
import io
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from app.services.answer_service import answer_question

PROJECT_ID = "proj_nolocode_001"
FAKE_PROJECT = "proj_fake_999"

separator = "=" * 60


# ── 1. SCOPE ISOLATION TEST ─────────────────────────────────────────────────
print()
print(separator)
print("TEST 1: SCOPE ISOLATION")
print(separator)

questions_to_isolate = [
    "What was decided about the AI module?",
    "Who are the speakers in the project?",
    "What are the commitments from the last meeting?",
]

all_isolated = True
for q in questions_to_isolate:
    result = answer_question(q, FAKE_PROJECT)
    sources = result["sources"]
    answer = result["answer"]
    leaked = any(
        kw in answer
        for kw in ["Nolocode", "Karan", "Bhavneet", "Ashpreet", "Harsh Vardhan", "Project Manager SFS"]
    )
    status = "FAIL - DATA LEAKED" if leaked else "PASS"
    if leaked:
        all_isolated = False
    print(f"  Q: {q[:55]}")
    print(f"  Project: {FAKE_PROJECT}  Sources: {len(sources)}  {status}")
    print(f"  Answer:  {answer[:150]}")
    print()

print("SCOPE ISOLATION:", "PASS — no data leaked across project boundary" if all_isolated else "FAIL — data leaked!")
print()


# ── 2. MULTI-MEETING SYNTHESIS TEST ─────────────────────────────────────────
print(separator)
print("TEST 2: MULTI-MEETING SYNTHESIS")
print(separator)

synthesis_questions = [
    ("Give me a summary of the project so far", ["summary_query"]),
    ("How did the discussion about the AI module change between the two meetings?", ["timeline_query"]),
    ("What are all the action items across both meetings?", ["commitment_query"]),
]

for q, expected_intents in synthesis_questions:
    t0 = time.time()
    result = answer_question(q, PROJECT_ID)
    elapsed = time.time() - t0

    answer = result["answer"]
    intent = result["intent"]
    sources = result["sources"]

    meets_meeting1 = any(kw in answer for kw in ["2026-05-08", "May 8", "Nolocode meeting with Ashpreet", "Ashpreet"])
    meets_meeting2 = any(kw in answer for kw in ["2026-05-14", "May 14", "AI meeting", "stress test", "Harsh Vardhan"])
    cross_meeting = meets_meeting1 and meets_meeting2

    print(f"  Q: {q[:60]}")
    print(f"  Intent: {intent}  Sources: {len(sources)}  Time: {elapsed:.1f}s")
    print(f"  Covers Meeting 1: {meets_meeting1}  |  Covers Meeting 2: {meets_meeting2}")
    print(f"  Cross-meeting synthesis: {'PASS' if cross_meeting else 'PARTIAL'}")
    print(f"  Answer: {answer[:250]}")
    print()


# ── 3. SPEED TEST ───────────────────────────────────────────────────────────
print(separator)
print("TEST 3: SPEED TEST (target: <10s per query)")
print(separator)

speed_questions = [
    ("decision", "What decisions were made about the forecasting formulas?"),
    ("commitment", "What are all the action items and who owns them?"),
    ("summary", "Give me a project overview"),
    ("speaker", "What did Bhavneet say about the balance sheet?"),
    ("timeline", "How did the project change between the first and second meeting?"),
    ("general", "What was discussed about the AI module architecture?"),
]

times = []
all_under_10 = True
for qtype, q in speed_questions:
    t0 = time.time()
    result = answer_question(q, PROJECT_ID)
    elapsed = time.time() - t0
    times.append(elapsed)
    status = "OK" if elapsed < 10 else "SLOW"
    if elapsed >= 10:
        all_under_10 = False
    print(f"  [{qtype.upper():10}] {elapsed:.1f}s  {status}  —  {q[:50]}")

avg = sum(times) / len(times)
max_t = max(times)
print()
print(f"  Average: {avg:.1f}s  |  Max: {max_t:.1f}s  |  All under 10s: {all_under_10}")
print(f"  SPEED TEST: {'PASS' if all_under_10 else 'FAIL (some queries over 10s)'}")
print()

print(separator)
print("PHASE 5 VALIDATION COMPLETE")
print(separator)
