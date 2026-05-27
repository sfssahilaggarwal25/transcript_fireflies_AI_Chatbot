"""
test_query_scope.py — Tests for the query scope node.

HOW TO RUN
----------
# Fast (no LLM, runs in ~1 second):
python production/tests/test_query_scope.py

# Full including LLM end-to-end (~20 seconds):
python production/tests/test_query_scope.py --full

HOW TO ADD A NEW TEST
---------------------
1. Find the right section below (Level 1, 2, or 3).
2. Copy any existing check() call as a template.
3. Change the query and the expected result.

MEETING NUMBERS (proj_nolocode_001)
------------------------------------
#1  2026-03-19   01KM2DD6MXGSZ4F1QW0BNJE16N   ← oldest / first
#2  2026-03-25   01KMHQSBYB1RAGY2X4EP6DCMC9
#3  2026-04-14   01KP5NPHRKEK81SCWMBH64172Q
#4  2026-04-14   01KP5V2WV2YFKWZSA1E4Y3SE18
#5  2026-04-15   01KP8S4ZFHR6CGHJVK62931CC6
#6  2026-04-20   01KPN0G7JN7B3SR8HXR0PVFPSZ
#7  2026-04-22   01KPSSB8Z5D7C70WJ11YFFFY2Z
#8  2026-04-24   01KPZQM8QJV019CTG2YBHBNKJB
#9  2026-05-05   01KQVP85XVSYDGBXDMCPD4BB6A
#10 2026-05-07   01KR18Q6AJM5GZX7Q66VHZXZP3   ← latest / newest
"""

import sys
import os
import logging
from pathlib import Path

# Add project root so imports work from anywhere
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Keep logs quiet during tests
logging.basicConfig(level=logging.WARNING)

from langchain_core.messages import HumanMessage, AIMessage
from app.core.scope import parse_meeting_scope
from app.agent.query_scope import query_scope_node

# ─────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────

PROJECT_ID = "proj_nolocode_001"

# Paste a meeting ID here when you want to test a specific one.
# These match the table in the header above.
M1  = "01KM2DD6MXGSZ4F1QW0BNJE16N"   # first / oldest
M2  = "01KMHQSBYB1RAGY2X4EP6DCMC9"
M3  = "01KP5NPHRKEK81SCWMBH64172Q"
M4  = "01KP5V2WV2YFKWZSA1E4Y3SE18"
M5  = "01KP8S4ZFHR6CGHJVK62931CC6"
M6  = "01KPN0G7JN7B3SR8HXR0PVFPSZ"
M7  = "01KPSSB8Z5D7C70WJ11YFFFY2Z"
M8  = "01KPZQM8QJV019CTG2YBHBNKJB"
M9  = "01KQVP85XVSYDGBXDMCPD4BB6A"
M10 = "01KR18Q6AJM5GZX7Q66VHZXZP3"   # latest / newest


# ─────────────────────────────────────────────────────────────
# Simple pass/fail printer
# ─────────────────────────────────────────────────────────────

_passed = 0
_failed = 0

def check(label, condition, got=None, expected=None):
    """Print ✅ or ❌ and keep a running count."""
    global _passed, _failed
    if condition:
        print(f"  ✅  {label}")
        _passed += 1
    else:
        print(f"  ❌  {label}")
        if expected is not None:
            print(f"        expected : {expected}")
        if got is not None:
            print(f"        got      : {got}")
        _failed += 1


# ─────────────────────────────────────────────────────────────
# LEVEL 1 — Test parse_meeting_scope() directly
#
# What it tests: the regex patterns that detect meeting scope
# phrases in a query and return a ChromaDB filter dict.
#
# Why useful: if scope detection breaks, it breaks here first
# with a clear message — before involving any node or graph.
# No LLM. No graph. Just regex + one ChromaDB metadata scan.
# ─────────────────────────────────────────────────────────────

def test_level1():
    print("\n── LEVEL 1: parse_meeting_scope() ──────────────────────")

    # No scope phrase → should return None (search all meetings)
    result = parse_meeting_scope("What did the client say about the API?", PROJECT_ID)
    check("no scope phrase → None", result is None)

    # "last meeting" / "previous meeting" → latest meeting (#10)
    result = parse_meeting_scope("What was discussed in the last meeting?", PROJECT_ID)
    check("'last meeting' → meeting #10", result == {"meeting_id": {"$eq": M10}})

    result = parse_meeting_scope("Summarize the previous meeting", PROJECT_ID)
    check("'previous meeting' → meeting #10", result == {"meeting_id": {"$eq": M10}})

    result = parse_meeting_scope("What happened in the most recent meeting?", PROJECT_ID)
    check("'most recent meeting' → meeting #10", result == {"meeting_id": {"$eq": M10}})

    # "first meeting" → oldest meeting (#1)
    result = parse_meeting_scope("What happened in the first meeting?", PROJECT_ID)
    check("'first meeting' → meeting #1", result == {"meeting_id": {"$eq": M1}})

    result = parse_meeting_scope("Summarize the earliest meeting", PROJECT_ID)
    check("'earliest meeting' → meeting #1", result == {"meeting_id": {"$eq": M1}})

    # "last N meetings" → $in list with N most recent IDs
    result = parse_meeting_scope("Summarize the last 2 meetings", PROJECT_ID)
    check("'last 2 meetings' → $in [M10, M9]",
          result == {"meeting_id": {"$in": [M10, M9]}})

    result = parse_meeting_scope("What happened in the last 3 meetings?", PROJECT_ID)
    check("'last 3 meetings' → $in [M10, M9, M8]",
          result == {"meeting_id": {"$in": [M10, M9, M8]}})

    # Ordinal phrases → specific meeting by position
    result = parse_meeting_scope("What was decided in the second meeting?", PROJECT_ID)
    check("'the second meeting' → meeting #2", result == {"meeting_id": {"$eq": M2}})

    result = parse_meeting_scope("Show me the third meeting", PROJECT_ID)
    check("'the third meeting' → meeting #3", result == {"meeting_id": {"$eq": M3}})

    # Date phrase → matching meeting by date
    result = parse_meeting_scope("What happened on March 19th?", PROJECT_ID)
    check("'March 19th' → meeting #1 (2026-03-19)",
          result is not None
          and result.get("meeting_id", {}).get("$eq") == M1)

    # Relative days → date range clause (not a meeting_id filter)
    result = parse_meeting_scope("What happened in the last 30 days?", PROJECT_ID)
    check("'last 30 days' → meeting_date range clause",
          result is not None and "meeting_date" in result)


# ─────────────────────────────────────────────────────────────
# LEVEL 2 — Test query_scope_node() directly
#
# What it tests: the actual LangGraph node function.
# We build a fake AgentState dict by hand, call the node,
# and check what it returns.
#
# Why useful: confirms the node reads from state correctly and
# returns the right dict shape that LangGraph expects.
# No LLM. No graph execution.
# ─────────────────────────────────────────────────────────────

def make_state(query):
    """Build a minimal AgentState dict — same shape the graph uses."""
    return {
        "messages":    [HumanMessage(content=query)],
        "project_id":  PROJECT_ID,
        "scope_where": None,
        "scope_ids":   None,
        "scope_type":  "project",
    }


def test_level2():
    print("\n── LEVEL 2: query_scope_node() ──────────────────────────")

    # Basic shape: node must return all three scope fields, not messages
    state  = make_state("What was discussed?")
    result = query_scope_node(state)
    check("returns a dict",          isinstance(result, dict))
    check("has 'scope_where'",       "scope_where" in result)
    check("has 'scope_ids'",         "scope_ids"   in result)
    check("has 'scope_type'",        "scope_type"  in result)
    check("does not touch messages", "messages"    not in result)

    # No scope phrase → all three reflect project-wide defaults
    state  = make_state("What did the team decide about the architecture?")
    result = query_scope_node(state)
    check("no scope → scope_where is None",     result["scope_where"] is None)
    check("no scope → scope_ids is None",       result["scope_ids"]   is None)
    check("no scope → scope_type = 'project'",  result["scope_type"]  == "project")

    # "last meeting" → single meeting, scope_type = "meeting"
    state  = make_state("What was discussed in the last meeting?")
    result = query_scope_node(state)
    check("'last meeting' → scope_where = meeting #10",
          result["scope_where"] == {"meeting_id": {"$eq": M10}})
    check("'last meeting' → scope_ids = [M10]",
          result["scope_ids"] == [M10])
    check("'last meeting' → scope_type = 'meeting'",
          result["scope_type"] == "meeting")

    # "first meeting" → single meeting #1
    state  = make_state("Summarize what happened in the first meeting")
    result = query_scope_node(state)
    check("'first meeting' → scope_ids = [M1]",
          result["scope_ids"] == [M1])

    # "last 2 meetings" → two IDs in scope_ids
    state  = make_state("Give me a summary of the last 2 meetings")
    result = query_scope_node(state)
    check("'last 2 meetings' → scope_ids = [M10, M9]",
          result["scope_ids"] == [M10, M9])
    check("'last 2 meetings' → scope_type = 'meeting'",
          result["scope_type"] == "meeting")

    # Date range phrase → scope_type = "date_range", scope_ids = None
    state  = make_state("What happened in the last 30 days?")
    result = query_scope_node(state)
    check("'last 30 days' → scope_type = 'date_range'",
          result["scope_type"] == "date_range")
    check("'last 30 days' → scope_ids is None",
          result["scope_ids"] is None)
    check("'last 30 days' → scope_where has meeting_date clause",
          result["scope_where"] is not None and "meeting_date" in result["scope_where"])

    # Node reads the FIRST HumanMessage even when other messages follow
    state = {
        "messages": [
            HumanMessage(content="What happened in the last meeting?"),
            AIMessage(content="Let me search that."),   # should be ignored
        ],
        "project_id":  PROJECT_ID,
        "scope_where": None,
        "scope_ids":   None,
        "scope_type":  "project",
    }
    result = query_scope_node(state)
    check("reads first HumanMessage even with other messages present",
          result["scope_ids"] == [M10])


# ─────────────────────────────────────────────────────────────
# LEVEL 3 — Full pipeline test (uses LLM, ~20 seconds)
#
# What it tests: the whole answer_query() pipeline.
# Checks that scope_where actually reaches the retrieval layer
# by inspecting which meetings appear in the returned sources.
#
# Run with:  python test_query_scope.py --full
# ─────────────────────────────────────────────────────────────

def test_level3():
    print("\n── LEVEL 3: answer_query() end-to-end ───────────────────")

    if not os.getenv("GEMINI_API_KEY"):
        print("  ⚠️  GEMINI_API_KEY not set — skipping Level 3")
        return

    from app.agent.service import answer_query

    # ── Test A: scoped query → only latest meeting in sources ─────────────────
    print("\n  Query → 'What was discussed in the last meeting?'")
    r = answer_query("What was discussed in the last meeting?", PROJECT_ID)

    check("answer is not empty",        bool(r.get("answer")))
    check("no error",                   r.get("error") is None)
    check("at least 1 source",          len(r.get("sources", [])) >= 1)

    # Every non-summary source must be from meeting #10 (date 2026-05-07)
    wrong = [s for s in r["sources"] if not s["is_summary"] and s["meeting_date"] != "2026-05-07"]
    check("all sources are from meeting #10 only",
          len(wrong) == 0,
          got=[s["meeting_date"] for s in wrong] or "✓ all correct")

    print(f"  answer   : {r['answer'][:160]}...")
    print(f"  tools    : {[t['tool'] for t in r.get('tool_calls', [])]}")
    print(f"  sources  : {len(r['sources'])} total")

    # ── Test B: project-wide query → multiple meetings in sources ─────────────
    print("\n  Query → 'What were the main decisions across all meetings?'")
    r2 = answer_query("What were the main decisions across all meetings?", PROJECT_ID)

    unique_dates = {s["meeting_date"] for s in r2["sources"] if not s["is_summary"]}
    check("project-wide → sources from more than 1 meeting",
          len(unique_dates) > 1,
          got=f"{len(unique_dates)} unique dates: {sorted(unique_dates)}")


# ─────────────────────────────────────────────────────────────
# Run
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n====================================================")
    print("  Query Scope Node — Test Suite")
    print("  Project: proj_nolocode_001  (10 meetings)")
    print("====================================================")

    test_level1()
    test_level2()

    if "--full" in sys.argv:
        test_level3()
    else:
        print("\n  ℹ️  Level 3 (LLM) skipped. Add --full flag to run it.")

    print(f"\n====================================================")
    print(f"  {_passed} passed  |  {_failed} failed  |  {_passed + _failed} total")
    if _failed == 0:
        print("  ✅ All passed")
    print("====================================================\n")

    sys.exit(0 if _failed == 0 else 1)
