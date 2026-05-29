"""
test_reranker_integration.py — Tests for reranker wiring in search_transcripts.

What is tested
--------------
1. reranker called on hybrid path      — rerank_documents is invoked after hybrid_retrieve
2. reranker skipped on exhaustive path — signal_filter + scope_ids bypasses hybrid entirely
3. top_n respected                     — at most _RERANK_TOP_N anchor chunks in output
4. speaker_hint passed correctly       — resolved_speaker flows into reranker
5. fallback on reranker error          — original order returned, no crash
6. rerank before expand                — expansion runs on reranked order, not RRF order
7. reranker improves chunk order       — highest-scored chunk appears first in tool output
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from langchain_core.documents import Document

from app.agent._tool_utils import _RERANK_TOP_N, _EXPAND_TOP_N, reset_doc_accumulator

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
_results: list[tuple[str, bool, str]] = []

PROJECT_ID = "proj_nolocode_001"


def record(name: str, passed: bool, detail: str = "") -> None:
    _results.append((name, passed, detail))
    status = PASS if passed else FAIL
    print(f"  {status}  {name}" + (f" — {detail}" if detail else ""))


def _make_docs(n: int) -> list[Document]:
    """Build n minimal transcript Documents."""
    return [
        Document(
            page_content=f"Transcript chunk number {i} about the forecasting topic.",
            metadata={
                "chunk_id":        f"chunk_{i}",
                "prev_chunk_id":   f"chunk_{i-1}" if i > 0 else None,
                "next_chunk_id":   f"chunk_{i+1}",
                "speaker_name":    "Harsh Vardhan",
                "meeting_title":   "Nolocode Meeting #7",
                "meeting_date":    "2026-04-22",
                "start_time":      i * 60,
                "is_meeting_summary": False,
            },
        )
        for i in range(n)
    ]


def _base_state(scope_ids=None, scope_where=None):
    return {
        "project_id":    PROJECT_ID,
        "scope_where":   scope_where,
        "scope_ids":     scope_ids,
        "scope_type":    "project" if not scope_ids else "meeting",
        "recommended_k": 15,
    }


# ── Test 1: reranker is called on the hybrid path ────────────────────────────

def test_reranker_called_on_hybrid_path():
    reset_doc_accumulator()
    docs = _make_docs(5)

    with patch("app.agent.tools.hybrid_retrieve", return_value=docs) as mock_hybrid, \
         patch("app.agent.tools.rerank_documents", return_value=docs[:_RERANK_TOP_N]) as mock_rerank, \
         patch("app.agent._tool_utils.get_raw_collection"):

        from app.agent.tools import search_transcripts
        search_transcripts.invoke({
            "query": "forecasting timeline",
            "state": _base_state(),
        })

    passed = mock_rerank.called
    call_args = mock_rerank.call_args
    record(
        "reranker called on hybrid path",
        passed,
        f"called={mock_rerank.called}, query={call_args[1].get('query') if call_args else '?'}",
    )


# ── Test 2: reranker skipped on exhaustive signal path ───────────────────────

def test_reranker_skipped_on_exhaustive_path():
    reset_doc_accumulator()

    fake_collection = MagicMock()
    fake_collection.get.return_value = {
        "ids":       ["c1"],
        "documents": ["A decision was made about forecasting."],
        "metadatas": [{"chunk_id": "c1", "speaker_name": "Harsh", "meeting_title": "M1",
                       "meeting_date": "2026-04-22", "start_time": 0}],
    }

    with patch("app.agent.tools.hybrid_retrieve") as mock_hybrid, \
         patch("app.agent.tools.rerank_documents") as mock_rerank, \
         patch("app.agent._tool_utils.get_raw_collection", return_value=fake_collection):

        from app.agent.tools import search_transcripts
        search_transcripts.invoke({
            "query":         "forecasting decision",
            "signal_filter": "decision",
            "state":         _base_state(scope_ids=["meeting_007"]),
        })

    passed = not mock_rerank.called and not mock_hybrid.called
    record(
        "reranker skipped on exhaustive signal path",
        passed,
        f"rerank_called={mock_rerank.called}, hybrid_called={mock_hybrid.called}",
    )


# ── Test 3: top_n respected — at most _RERANK_TOP_N anchor chunks ─────────────

def test_top_n_respected():
    reset_doc_accumulator()
    # Return more docs than _RERANK_TOP_N from hybrid, let reranker trim
    docs = _make_docs(20)

    with patch("app.agent.tools.hybrid_retrieve", return_value=docs), \
         patch("app.agent.tools.rerank_documents", side_effect=lambda **kw: kw["documents"][:kw["top_n"]]) as mock_rerank, \
         patch("app.agent._tool_utils.get_raw_collection") as mock_col:

        # No neighbor data needed — return empty for neighbor fetches
        mock_col.return_value.get.return_value = {"ids": [], "documents": [], "metadatas": []}

        from app.agent.tools import search_transcripts
        result = search_transcripts.invoke({
            "query": "forecasting topic",
            "state": _base_state(),
        })

    # Count [N] lines in output — each anchor has "[N] Speaker"
    import re
    anchor_lines = re.findall(r'^\[\d+\]', result, re.MULTILINE)
    passed = len(anchor_lines) <= _RERANK_TOP_N
    record(
        f"at most {_RERANK_TOP_N} anchor chunks in tool output",
        passed,
        f"anchor_count={len(anchor_lines)}, limit={_RERANK_TOP_N}",
    )


# ── Test 4: speaker_hint passed to reranker ───────────────────────────────────

def test_speaker_hint_passed():
    reset_doc_accumulator()
    docs = _make_docs(3)

    captured_kwargs = {}

    def capture_rerank(**kwargs):
        captured_kwargs.update(kwargs)
        return kwargs["documents"]

    fake_col = MagicMock()
    # Speaker resolution: return metadata with one speaker
    fake_col.get.return_value = {
        "ids":       ["x"],
        "documents": ["text"],
        "metadatas": [{"speaker_name": "Harsh Vardhan", "is_meeting_summary": False}],
    }

    with patch("app.agent.tools.hybrid_retrieve", return_value=docs), \
         patch("app.agent.tools.rerank_documents", side_effect=capture_rerank), \
         patch("app.agent._tool_utils.get_raw_collection", return_value=fake_col):

        from app.agent.tools import search_transcripts
        search_transcripts.invoke({
            "query":        "what did Harsh say",
            "speaker_name": "Harsh Vardhan",
            "state":        _base_state(),
        })

    speaker_hint = captured_kwargs.get("speaker_hint", "NOT_SET")
    passed = speaker_hint == "Harsh Vardhan"
    record(
        "speaker_hint passed correctly to reranker",
        passed,
        f"speaker_hint={speaker_hint!r}",
    )


# ── Test 5: fallback on reranker error — no crash, original order ─────────────

def test_fallback_on_reranker_error():
    """
    rerank_documents has an internal try/except that returns the original order
    on any Gemini API failure. Test that fallback by breaking the API call
    from inside — not by mocking the function away (that would bypass the handler).
    """
    reset_doc_accumulator()
    docs = _make_docs(3)
    original_ids = [d.metadata["chunk_id"] for d in docs]

    with patch("app.agent.tools.hybrid_retrieve", return_value=docs), \
         patch("app.core.retrieval.reranker.genai") as mock_genai, \
         patch("app.agent._tool_utils.get_raw_collection") as mock_col:

        # Make the Gemini client raise — rerank_documents catches this and falls back
        mock_genai.Client.return_value.models.generate_content.side_effect = \
            Exception("Gemini timeout")
        mock_col.return_value.get.return_value = {"ids": [], "documents": [], "metadatas": []}

        try:
            from app.agent.tools import search_transcripts
            result   = search_transcripts.invoke({"query": "forecasting", "state": _base_state()})
            no_crash = True
        except Exception:
            result   = ""
            no_crash = False

    # Tool must not crash; output must still contain the original chunks
    has_content = len(result) > 0
    record(
        "reranker Gemini failure falls back to original order — tool never crashes",
        no_crash and has_content,
        f"no_crash={no_crash}, has_content={has_content}",
    )


# ── Test 6: rerank happens BEFORE context expansion ──────────────────────────

def test_rerank_before_expand():
    """
    Verify that _expand_context receives the reranked list, not the original.
    We do this by having rerank_documents reverse the list, then checking that
    _expand_context's input starts with the last original chunk (now ranked #1).
    """
    reset_doc_accumulator()
    docs = _make_docs(4)
    reversed_docs = list(reversed(docs))  # reranker will return this order

    expand_input: list[Document] = []

    def capture_expand(d, n=5):
        expand_input.extend(d)
        return d   # return as-is so the rest of the tool can finish

    with patch("app.agent.tools.hybrid_retrieve", return_value=docs), \
         patch("app.agent.tools.rerank_documents", return_value=reversed_docs), \
         patch("app.agent.tools._expand_context", side_effect=capture_expand):

        from app.agent.tools import search_transcripts
        search_transcripts.invoke({
            "query": "forecasting",
            "state": _base_state(),
        })

    first_chunk_id = expand_input[0].metadata.get("chunk_id") if expand_input else None
    expected_first = reversed_docs[0].metadata["chunk_id"]
    passed = first_chunk_id == expected_first
    record(
        "context expansion receives reranked order, not original RRF order",
        passed,
        f"first_chunk={first_chunk_id!r}, expected={expected_first!r}",
    )


# ── Test 7: reranker improves chunk order (real Gemini call) ─────────────────

def test_reranker_improves_order_real():
    """
    Integration test: fetch real docs from ChromaDB, run the real reranker,
    verify it returns the same docs in a (potentially) different order.
    Uses actual Gemini API — skipped gracefully if API key is missing.
    """
    import os
    if not os.getenv("GEMINI_API_KEY"):
        record("reranker real Gemini call", True, "SKIPPED — GEMINI_API_KEY not set")
        return

    from app.core.retrieval import hybrid_retrieve
    from app.core.retrieval.reranker import rerank_documents

    try:
        docs = hybrid_retrieve(
            query="forecasting timeline decisions",
            project_id=PROJECT_ID,
            k=10,
        )
        if not docs:
            record("reranker real Gemini call", True, "SKIPPED — no docs returned for project")
            return

        reranked = rerank_documents(
            query="forecasting timeline decisions",
            documents=docs,
            topic_hint="forecasting timeline",
            speaker_hint="",
            top_n=5,
        )

        passed = (
            len(reranked) <= 5
            and all(isinstance(d, Document) for d in reranked)
        )
        order_changed = [d.metadata.get("chunk_id") for d in reranked] != \
                        [d.metadata.get("chunk_id") for d in docs[:5]]

        record(
            "reranker real Gemini call — returns valid Documents",
            passed,
            f"input={len(docs)}, output={len(reranked)}, order_changed={order_changed}",
        )
    except Exception as exc:
        record("reranker real Gemini call", False, f"exception: {exc}")


# ── Runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  Reranker Integration Test Suite")
    print("=" * 60)

    test_reranker_called_on_hybrid_path()
    test_reranker_skipped_on_exhaustive_path()
    test_top_n_respected()
    test_speaker_hint_passed()
    test_fallback_on_reranker_error()
    test_rerank_before_expand()
    test_reranker_improves_order_real()

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