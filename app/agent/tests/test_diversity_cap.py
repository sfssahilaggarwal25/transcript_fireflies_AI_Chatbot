"""
test_diversity_cap.py — Tests for the meeting diversity cap in _tool_utils.py.

What is tested
--------------
1. non-dominant meeting capped at floor (3)
2. dominant meeting gets proportional cap above floor
3. two dominant meetings both get independent proportional caps
4. RRF rank order preserved within each meeting after cap
5. single-chunk meeting passes all its docs (floor ≥ actual count)
6. empty docs list → no crash, returns []
7. overview k-boost fires for project-wide queries with overview signal
8. overview k-boost does NOT fire for single-meeting scope (scope_ids set)
9. overview k-boost does NOT fire for focused queries (no overview signal)
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from langchain_core.documents import Document

from app.agent._tool_utils import (
    _apply_diversity_cap,
    _DIVERSITY_CAP_FLOOR,
    _DIVERSITY_PASS_RATE,
    _DIVERSITY_MAX_MEETING_FRACTION,
    reset_doc_accumulator,
)

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
_results: list[tuple[str, bool, str]] = []

PROJECT_ID = "proj_nolocode_001"


def record(name: str, passed: bool, detail: str = "") -> None:
    _results.append((name, passed, detail))
    status = PASS if passed else FAIL
    print(f"  {status}  {name}" + (f" — {detail}" if detail else ""))


def _make_docs(meeting_id: str, count: int, start_rank: int = 0) -> list[Document]:
    """Build `count` minimal Documents all from `meeting_id`."""
    return [
        Document(
            page_content=f"Content from {meeting_id} chunk {i}.",
            metadata={
                "chunk_id":        f"{meeting_id}_chunk_{i}",
                "meeting_id":      meeting_id,
                "speaker_name":    "Test Speaker",
                "meeting_title":   f"Meeting {meeting_id}",
                "meeting_date":    "2026-04-22",
                "start_time":      (start_rank + i) * 60,
                "is_meeting_summary": False,
            },
        )
        for i in range(count)
    ]


# ── Test 1: non-dominant meeting capped at floor ──────────────────────────────

def test_non_dominant_capped_at_floor():
    """
    Meeting A contributes 8/25 = 32% — below 25% ceiling threshold.
    Expected cap = max(floor, min(ceiling, round(8 * 0.5))) = max(3, min(6, 4)) = 4.
    Wait — 32% of 25 = 8 docs. ceiling = round(25 * 0.25) = 6.
    cap = max(3, min(6, round(8*0.5))) = max(3, min(6, 4)) = 4.
    So meeting A gets 4 (proportional), not floor.
    The floor test: meeting with 5 docs (20%) → cap = max(3, min(6, round(5*0.5))) = max(3,2) = 3.
    """
    # 5 from meeting_a (20%), 20 from meeting_b (80%)
    docs = _make_docs("meeting_a", 5) + _make_docs("meeting_b", 20, start_rank=5)
    result = _apply_diversity_cap(docs)

    a_count = sum(1 for d in result if d.metadata["meeting_id"] == "meeting_a")
    b_count = sum(1 for d in result if d.metadata["meeting_id"] == "meeting_b")

    # meeting_a: 5 docs, 20% of 25 → cap = max(3, min(6, round(5*0.5))) = max(3,2) = 3
    # meeting_b: 20 docs, 80% of 25 → cap = max(3, min(6, round(20*0.5))) = max(3, min(6,10)) = 6
    passed = a_count == 3 and b_count == 6
    record(
        "non-dominant meeting (20%) gets floor cap=3",
        passed,
        f"meeting_a={a_count} (expected 3), meeting_b={b_count} (expected 6)",
    )


# ── Test 2: dominant meeting gets proportional cap above floor ────────────────

def test_dominant_meeting_proportional_cap():
    """
    Meeting A: 12/25 = 48% → cap = max(3, min(6, round(12*0.5))) = max(3, min(6, 6)) = 6.
    """
    docs = _make_docs("meeting_a", 12) + _make_docs("meeting_b", 13, start_rank=12)
    result = _apply_diversity_cap(docs)

    a_count = sum(1 for d in result if d.metadata["meeting_id"] == "meeting_a")
    # meeting_b: 13 docs, 52% → cap = max(3, min(6, round(13*0.5))) = max(3, min(6, 6)) = 6
    b_count = sum(1 for d in result if d.metadata["meeting_id"] == "meeting_b")

    passed = a_count == 6 and b_count == 6
    record(
        "dominant meeting (48%) gets proportional cap=6",
        passed,
        f"meeting_a={a_count} (expected 6), meeting_b={b_count} (expected 6)",
    )


# ── Test 3: two dominant meetings both get independent proportional caps ───────

def test_two_dominant_meetings():
    """
    Two meetings at 44% each — both above floor, both capped proportionally.
    total=25, meeting_a=11 (44%), meeting_b=11 (44%), others=3 (12%)
    """
    docs = (
        _make_docs("meeting_a", 11) +
        _make_docs("meeting_b", 11, start_rank=11) +
        _make_docs("meeting_c", 3,  start_rank=22)
    )
    result = _apply_diversity_cap(docs)

    a_count = sum(1 for d in result if d.metadata["meeting_id"] == "meeting_a")
    b_count = sum(1 for d in result if d.metadata["meeting_id"] == "meeting_b")
    c_count = sum(1 for d in result if d.metadata["meeting_id"] == "meeting_c")

    # ceiling = round(25 * 0.25) = 6
    # meeting_a: round(11 * 0.5) = 6 → cap = max(3, min(6, 6)) = 6 (wait, round(5.5)=6)
    # meeting_b: same → 6
    # meeting_c: round(3 * 0.5) = 2 → cap = max(3, 2) = 3 → but only has 3 → 3 pass
    passed = a_count == 6 and b_count == 6 and c_count == 3
    record(
        "two dominant meetings (44% each) both get cap=6 independently",
        passed,
        f"meeting_a={a_count} (expected 6), meeting_b={b_count} (expected 6), meeting_c={c_count} (expected 3)",
    )


# ── Test 4: RRF rank order preserved within each meeting ─────────────────────

def test_rrf_order_preserved():
    """
    Docs arrive as: [a1, a2, b1, a3, a4, b2, a5] — interleaved by RRF rank.
    After cap (meeting_a hits cap=3), the kept a-docs must still be a1, a2, a3
    in that order (not a4 or a5 which appear later in the list).
    """
    docs = [
        Document(page_content="a1", metadata={"chunk_id": "a1", "meeting_id": "mtg_a", "start_time": 0}),
        Document(page_content="a2", metadata={"chunk_id": "a2", "meeting_id": "mtg_a", "start_time": 60}),
        Document(page_content="b1", metadata={"chunk_id": "b1", "meeting_id": "mtg_b", "start_time": 0}),
        Document(page_content="a3", metadata={"chunk_id": "a3", "meeting_id": "mtg_a", "start_time": 120}),
        Document(page_content="a4", metadata={"chunk_id": "a4", "meeting_id": "mtg_a", "start_time": 180}),
        Document(page_content="b2", metadata={"chunk_id": "b2", "meeting_id": "mtg_b", "start_time": 60}),
        Document(page_content="a5", metadata={"chunk_id": "a5", "meeting_id": "mtg_a", "start_time": 240}),
    ]
    # total=7, mtg_a=5 (71%), mtg_b=2 (29%)
    # ceiling = round(7 * 0.25) = 2 → max(3, 2) = 3
    # mtg_a: cap = max(3, min(3, round(5*0.5))) = max(3, min(3, 2)) = 3
    # → a1, a2, a3 kept (a4, a5 skipped — appeared later in the list)
    result = _apply_diversity_cap(docs)

    a_ids = [d.metadata["chunk_id"] for d in result if d.metadata["meeting_id"] == "mtg_a"]
    passed = a_ids == ["a1", "a2", "a3"]
    record(
        "RRF rank order preserved — a1,a2,a3 kept, a4,a5 dropped",
        passed,
        f"kept a-docs={a_ids}",
    )


# ── Test 5: single-chunk meeting passes all its docs ─────────────────────────

def test_single_chunk_meeting_passes():
    """
    Meeting A: 1 doc (4%) → cap=max(3, round(1*0.5))=max(3,0)=3
    But meeting only HAS 1 doc → 1 passes (cap is a ceiling, not a target).
    """
    docs = _make_docs("meeting_a", 1) + _make_docs("meeting_b", 24, start_rank=1)
    result = _apply_diversity_cap(docs)

    a_count = sum(1 for d in result if d.metadata["meeting_id"] == "meeting_a")
    passed = a_count == 1
    record(
        "single-chunk meeting passes its 1 doc (floor ≥ actual count)",
        passed,
        f"meeting_a passed={a_count} (expected 1)",
    )


# ── Test 6: empty docs list → no crash ───────────────────────────────────────

def test_empty_docs_no_crash():
    try:
        result = _apply_diversity_cap([])
        passed = result == []
        record("empty docs list → returns [] without crash", passed, f"result={result}")
    except Exception as exc:
        record("empty docs list → returns [] without crash", False, f"exception: {exc}")


# ── Test 7: overview k-boost fires for project-wide overview query ────────────

def test_overview_k_boost_fires():
    """
    Query contains "overview" + scope_ids=None → effective_k should double.
    Verify hybrid_retrieve is called with boosted k.
    """
    reset_doc_accumulator()
    captured_k: list[int] = []

    def capture_hybrid(**kwargs):
        captured_k.append(kwargs.get("k", 0))
        return []

    with patch("app.agent.tools.hybrid_retrieve", side_effect=capture_hybrid), \
         patch("app.agent._tool_utils.get_raw_collection"):

        from app.agent.tools import search_transcripts
        search_transcripts.invoke({
            "query": "give the AI architecture overview",
            "state": {
                "project_id":    PROJECT_ID,
                "scope_where":   None,
                "scope_ids":     None,
                "scope_type":    "project",
                "recommended_k": 15,
            },
        })

    k_used = captured_k[0] if captured_k else 0
    passed = k_used > 25
    record(
        "overview query on project scope → k boosted above 25",
        passed,
        f"k_used={k_used} (expected >25)",
    )


# ── Test 8: k-boost does NOT fire when scope_ids is set ──────────────────────

def test_k_boost_skipped_for_single_meeting():
    """
    scope_ids set → single-meeting query → k-boost must not apply.
    """
    reset_doc_accumulator()

    fake_collection = MagicMock()
    fake_collection.get.return_value = {
        "ids": [], "documents": [], "metadatas": [],
    }
    captured_k: list[int] = []

    def capture_hybrid(**kwargs):
        captured_k.append(kwargs.get("k", 0))
        return []

    with patch("app.agent.tools.hybrid_retrieve", side_effect=capture_hybrid), \
         patch("app.agent._tool_utils.get_raw_collection", return_value=fake_collection):

        from app.agent.tools import search_transcripts
        search_transcripts.invoke({
            "query": "give the AI architecture overview",
            "state": {
                "project_id":    PROJECT_ID,
                "scope_where":   {"meeting_id": {"$eq": "meeting_007"}},
                "scope_ids":     ["meeting_007"],
                "scope_type":    "meeting",
                "recommended_k": 15,
            },
        })

    k_used = captured_k[0] if captured_k else 0
    passed = k_used <= 25
    record(
        "overview query with scope_ids set → k NOT boosted (stays ≤25)",
        passed,
        f"k_used={k_used} (expected ≤25)",
    )


# ── Test 9: k-boost does NOT fire for focused queries ────────────────────────

def test_k_boost_skipped_for_focused_query():
    """
    Focused query with no overview signals → k stays at recommended_k / 25 max.
    """
    reset_doc_accumulator()
    captured_k: list[int] = []

    def capture_hybrid(**kwargs):
        captured_k.append(kwargs.get("k", 0))
        return []

    with patch("app.agent.tools.hybrid_retrieve", side_effect=capture_hybrid), \
         patch("app.agent._tool_utils.get_raw_collection"):

        from app.agent.tools import search_transcripts
        search_transcripts.invoke({
            "query": "what did Harsh say about deployment",
            "state": {
                "project_id":    PROJECT_ID,
                "scope_where":   None,
                "scope_ids":     None,
                "scope_type":    "project",
                "recommended_k": 15,
            },
        })

    k_used = captured_k[0] if captured_k else 0
    passed = k_used <= 25
    record(
        "focused query (no overview signal) → k NOT boosted (stays ≤25)",
        passed,
        f"k_used={k_used} (expected ≤25)",
    )


# ── Runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  Diversity Cap Test Suite")
    print("=" * 60)

    test_non_dominant_capped_at_floor()
    test_dominant_meeting_proportional_cap()
    test_two_dominant_meetings()
    test_rrf_order_preserved()
    test_single_chunk_meeting_passes()
    test_empty_docs_no_crash()
    test_overview_k_boost_fires()
    test_k_boost_skipped_for_single_meeting()
    test_k_boost_skipped_for_focused_query()

    print("=" * 60)
    passed_count = sum(1 for _, ok, _ in _results if ok)
    total        = len(_results)
    print(f"  Result: {passed_count}/{total} passed")

    if passed_count < total:
        print("\n  Failed tests:")
        for name, ok, detail in _results:
            if not ok:
                print(f"    ✗  {name}  ({detail})")

    print("=" * 60 + "\n")
    sys.exit(0 if passed_count == total else 1)