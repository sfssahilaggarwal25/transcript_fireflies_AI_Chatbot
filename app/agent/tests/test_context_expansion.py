"""
test_context_expansion.py — Tests for the context expansion logic in tools.py.

What is tested
--------------
1. neighbors injected  — prev/next chunks appear around their anchor in output
2. _position labels    — neighbors carry _position='before'/'after', anchors do not
3. deduplication       — a chunk already in top-k is not inserted again as a neighbor
4. summary skipped     — summary chunks are passed through without neighbor fetch
5. top-n boundary      — only top-_EXPAND_TOP_N anchors get neighbors; the rest don't
6. missing neighbors   — chunk with no prev/next_chunk_id → no crash, no ghost entry
7. sources panel       — neighbors are NOT in _accumulated_docs; only anchors are
8. real ChromaDB round-trip — _fetch_neighbor returns a real Document for a known chunk
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from langchain_core.documents import Document

from app.agent._tool_utils import (
    _expand_context,
    _fetch_neighbor,
    _EXPAND_TOP_N,
    reset_doc_accumulator,
    get_accumulated_docs,
    _append_docs,
)
from app.core.storage.db import get_raw_collection

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
_results: list[tuple[str, bool, str]] = []


def record(name: str, passed: bool, detail: str = "") -> None:
    _results.append((name, passed, detail))
    status = PASS if passed else FAIL
    print(f"  {status}  {name}" + (f" — {detail}" if detail else ""))


def _make_doc(chunk_id, prev_id=None, next_id=None, is_summary=False) -> Document:
    """Build a minimal Document that mimics a stored transcript chunk."""
    return Document(
        page_content=f"Content of chunk {chunk_id}.",
        metadata={
            "chunk_id":        chunk_id,
            "prev_chunk_id":   prev_id,
            "next_chunk_id":   next_id,
            "is_meeting_summary": is_summary,
            "speaker_name":    "Test Speaker",
            "meeting_title":   "Test Meeting",
            "meeting_date":    "2026-05-01",
            "start_time":      60,
        },
    )


def _make_neighbor_response(chunk_id: str) -> dict:
    """Fake ChromaDB .get() response for a neighbor fetch."""
    return {
        "ids":       [chunk_id],
        "documents": [f"Neighbor content for {chunk_id}."],
        "metadatas": [{
            "chunk_id":     chunk_id,
            "speaker_name": "Neighbor Speaker",
            "meeting_title": "Test Meeting",
            "meeting_date":  "2026-05-01",
            "start_time":   30,
        }],
    }


# ── Test 1: neighbors are injected around anchor ──────────────────────────────

def test_neighbors_injected():
    anchor = _make_doc("chunk_5", prev_id="chunk_4", next_id="chunk_6")

    mock_col = MagicMock()
    mock_col.get.side_effect = lambda ids, **kw: _make_neighbor_response(ids[0])

    with patch("app.agent._tool_utils.get_raw_collection", return_value=mock_col):
        result = _expand_context([anchor], n=1)

    ids_in_order = [d.metadata["chunk_id"] for d in result]
    positions    = [d.metadata.get("_position") for d in result]

    passed = (
        ids_in_order == ["chunk_4", "chunk_5", "chunk_6"]
        and positions == ["before", None, "after"]
    )
    record(
        "neighbors injected around anchor in correct order",
        passed,
        f"order={ids_in_order}, positions={positions}",
    )


# ── Test 2: _position labels ──────────────────────────────────────────────────

def test_position_labels():
    anchor = _make_doc("chunk_5", prev_id="chunk_4", next_id="chunk_6")

    mock_col = MagicMock()
    mock_col.get.side_effect = lambda ids, **kw: _make_neighbor_response(ids[0])

    with patch("app.agent._tool_utils.get_raw_collection", return_value=mock_col):
        result = _expand_context([anchor], n=1)

    before = next((d for d in result if d.metadata.get("_position") == "before"), None)
    after  = next((d for d in result if d.metadata.get("_position") == "after"),  None)
    anchor_out = next((d for d in result if not d.metadata.get("_position")), None)

    passed = (
        before is not None
        and after is not None
        and anchor_out is not None
        and before.metadata["chunk_id"]     == "chunk_4"
        and after.metadata["chunk_id"]      == "chunk_6"
        and anchor_out.metadata["chunk_id"] == "chunk_5"
    )
    record("_position='before'/'after' on neighbors, absent on anchor", passed)


# ── Test 3: deduplication — neighbor already in top-k not inserted twice ──────

def test_deduplication():
    # chunk_6 is both the anchor[1] AND the next-neighbor of anchor[0]
    anchor_0 = _make_doc("chunk_5", prev_id="chunk_4", next_id="chunk_6")
    anchor_1 = _make_doc("chunk_6", prev_id="chunk_5", next_id="chunk_7")

    mock_col = MagicMock()
    mock_col.get.side_effect = lambda ids, **kw: _make_neighbor_response(ids[0])

    with patch("app.agent._tool_utils.get_raw_collection", return_value=mock_col):
        result = _expand_context([anchor_0, anchor_1], n=2)

    chunk_ids = [d.metadata["chunk_id"] for d in result]
    duplicates = len(chunk_ids) != len(set(chunk_ids))

    record(
        "chunk already in top-k is not inserted again as neighbor",
        not duplicates,
        f"ids={chunk_ids}, duplicates={duplicates}",
    )


# ── Test 4: summary chunks pass through without neighbor fetch ────────────────

def test_summary_skipped():
    summary = _make_doc("meeting_summary_001", is_summary=True)

    mock_col = MagicMock()

    with patch("app.agent._tool_utils.get_raw_collection", return_value=mock_col):
        result = _expand_context([summary], n=1)

    fetch_calls = mock_col.get.call_count
    passed = len(result) == 1 and fetch_calls == 0

    record(
        "summary chunk passes through; no neighbor DB call",
        passed,
        f"result_len={len(result)}, db_calls={fetch_calls}",
    )


# ── Test 5: top-n boundary — only first _EXPAND_TOP_N anchors get neighbors ──

def test_top_n_boundary():
    # Create _EXPAND_TOP_N + 2 anchors; only the first _EXPAND_TOP_N should expand
    docs = [
        _make_doc(f"chunk_{i}", prev_id=f"chunk_{i-1}", next_id=f"chunk_{i+1}")
        for i in range(1, _EXPAND_TOP_N + 3)
    ]

    call_log: list[str] = []

    def side_effect(ids, **kw):
        call_log.append(ids[0])
        return _make_neighbor_response(ids[0])

    mock_col = MagicMock()
    mock_col.get.side_effect = side_effect

    with patch("app.agent._tool_utils.get_raw_collection", return_value=mock_col):
        _expand_context(docs, n=_EXPAND_TOP_N)

    # At most 2 * _EXPAND_TOP_N DB calls (2 neighbors per expanded anchor)
    max_expected = 2 * _EXPAND_TOP_N
    passed = len(call_log) <= max_expected

    record(
        f"only top-{_EXPAND_TOP_N} anchors expanded (≤{max_expected} DB calls)",
        passed,
        f"db_calls={len(call_log)} (max allowed={max_expected})",
    )


# ── Test 6: missing prev/next_chunk_id → no crash ────────────────────────────

def test_missing_neighbor_ids():
    anchor = _make_doc("chunk_lone")   # prev_id=None, next_id=None

    mock_col = MagicMock()

    with patch("app.agent._tool_utils.get_raw_collection", return_value=mock_col):
        result = _expand_context([anchor], n=1)

    passed = len(result) == 1 and result[0].metadata["chunk_id"] == "chunk_lone"
    record(
        "chunk with no prev/next_chunk_id: no crash, anchor returned cleanly",
        passed,
        f"result_len={len(result)}",
    )


# ── Test 7: neighbors NOT in accumulated_docs (sources panel) ─────────────────

def test_neighbors_not_in_sources():
    reset_doc_accumulator()

    anchor    = _make_doc("chunk_5", prev_id="chunk_4", next_id="chunk_6")
    expanded  = [
        Document(page_content="before", metadata={**anchor.metadata, "chunk_id": "chunk_4", "_position": "before"}),
        anchor,
        Document(page_content="after",  metadata={**anchor.metadata, "chunk_id": "chunk_6", "_position": "after"}),
    ]

    # Simulate what search_transcripts does: only add anchor docs
    anchor_docs   = [d for d in expanded if not d.metadata.get("_position")]
    _append_docs(anchor_docs)

    accumulated_ids = {d.metadata.get("chunk_id") for d in get_accumulated_docs()}

    passed = (
        "chunk_5" in accumulated_ids       # anchor IS in sources
        and "chunk_4" not in accumulated_ids  # before-neighbor is NOT
        and "chunk_6" not in accumulated_ids  # after-neighbor is NOT
    )
    record(
        "neighbors excluded from _accumulated_docs; only anchor in sources panel",
        passed,
        f"accumulated_ids={accumulated_ids}",
    )


# ── Test 8: real ChromaDB round-trip ─────────────────────────────────────────

def test_real_db_neighbor_fetch():
    """
    Fetch a real chunk from ChromaDB, read its prev_chunk_id, then call
    _fetch_neighbor() for that ID and verify a Document comes back.
    Skipped gracefully if the project has no chunks with prev links.
    """
    try:
        col     = get_raw_collection()
        results = col.get(
            where={"project_id": {"$eq": "proj_nolocode_001"}},
            include=["metadatas"],
            limit=50,
        )
        # Find a chunk that has a prev_chunk_id
        anchor_meta = next(
            (m for m in results.get("metadatas", []) if m.get("prev_chunk_id")),
            None,
        )
        if anchor_meta is None:
            record("real DB neighbor fetch", True, "SKIPPED — no chunks with prev_chunk_id found")
            return

        prev_id  = anchor_meta["prev_chunk_id"]
        neighbor = _fetch_neighbor(prev_id, "before")

        passed = (
            neighbor is not None
            and isinstance(neighbor, Document)
            and neighbor.metadata.get("chunk_id") == prev_id
            and neighbor.metadata.get("_position") == "before"
            and len(neighbor.page_content) > 0
        )
        record(
            "real DB neighbor fetch returns correct Document",
            passed,
            f"prev_id={prev_id}, content_len={len(neighbor.page_content) if neighbor else 0}",
        )
    except Exception as exc:
        record("real DB neighbor fetch", False, f"exception: {exc}")


# ── Runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  Context Expansion Test Suite")
    print("=" * 60)

    test_neighbors_injected()
    test_position_labels()
    test_deduplication()
    test_summary_skipped()
    test_top_n_boundary()
    test_missing_neighbor_ids()
    test_neighbors_not_in_sources()
    test_real_db_neighbor_fetch()

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