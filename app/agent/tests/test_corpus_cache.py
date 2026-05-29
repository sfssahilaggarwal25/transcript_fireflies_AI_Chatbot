"""
test_corpus_cache.py — Tests for the per-request BM25 corpus cache in base.py.

What is tested
--------------
1. cache MISS  — first fetch for a key hits ChromaDB
2. cache HIT   — identical key on second call skips ChromaDB
3. key isolation — different (project_id / hard_filters / date_where) each get
                   their own independent MISS
4. reset        — reset_corpus_cache() clears all keys; next call is a MISS again
5. multi-tool   — simulates 3 back-to-back search_transcripts calls the way the
                  LangGraph agent fires them in one query

Uses unittest.mock.patch(wraps=...) so the real ChromaDB is always called on a
MISS — we never stub the database, only count how many times it is invoked.
"""

import sys
from pathlib import Path
from unittest.mock import patch

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.core.retrieval.base import (
    _corpus_cache,
    _fetch_project_corpus,
    _make_corpus_key,
    reset_corpus_cache,
)
from app.core.storage.db import get_raw_collection as _real_get_raw_collection

PROJECT_ID = "proj_nolocode_001"
PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"

_results: list[tuple[str, bool, str]] = []   # (test_name, passed, detail)


def record(name: str, passed: bool, detail: str = "") -> None:
    _results.append((name, passed, detail))
    status = PASS if passed else FAIL
    print(f"  {status}  {name}" + (f" — {detail}" if detail else ""))


# ── helpers ───────────────────────────────────────────────────────────────────

def fresh_start() -> None:
    """Always reset before each test so cache state doesn't bleed."""
    reset_corpus_cache()


def db_call_counter():
    """
    Return a context manager that wraps the real get_raw_collection and counts
    how many times it was called.  Yields a list; list[0] is the call count.
    """
    call_log: list[int] = [0]

    real_collection = _real_get_raw_collection()

    class _Spy:
        """Wraps the real ChromaDB collection, counting every .get() call."""
        def get(self, *args, **kwargs):
            call_log[0] += 1
            return real_collection.get(*args, **kwargs)

        def __getattr__(self, item):
            return getattr(real_collection, item)

    return call_log, _Spy()


# ── Test 1: cache MISS on first call ─────────────────────────────────────────

def test_miss_on_first_call():
    fresh_start()
    key = _make_corpus_key(PROJECT_ID, None, None)

    assert key not in _corpus_cache, "cache should be empty after reset"

    call_log, spy = db_call_counter()
    with patch("app.core.retrieval.base.get_raw_collection", return_value=spy):
        corpus = _fetch_project_corpus(PROJECT_ID, None, None)

    db_calls   = call_log[0]
    cache_size = len(_corpus_cache)
    in_cache   = key in _corpus_cache

    record(
        "MISS on first call",
        db_calls == 1 and in_cache and cache_size == 1,
        f"db_calls={db_calls}, cache_size={cache_size}, in_cache={in_cache}, corpus_len={len(corpus)}",
    )


# ── Test 2: cache HIT on second identical call ───────────────────────────────

def test_hit_on_second_call():
    fresh_start()

    call_log, spy = db_call_counter()
    with patch("app.core.retrieval.base.get_raw_collection", return_value=spy):
        corpus_1 = _fetch_project_corpus(PROJECT_ID, None, None)
        corpus_2 = _fetch_project_corpus(PROJECT_ID, None, None)

    db_calls = call_log[0]
    same_obj = corpus_1 is corpus_2          # cache returns the exact same list object

    record(
        "HIT on second identical call",
        db_calls == 1 and same_obj,
        f"db_calls={db_calls} (expected 1), same_object={same_obj}",
    )


# ── Test 3: different project_id → separate MISS ─────────────────────────────

def test_different_project_ids_are_independent():
    fresh_start()

    call_log, spy = db_call_counter()
    with patch("app.core.retrieval.base.get_raw_collection", return_value=spy):
        _fetch_project_corpus(PROJECT_ID, None, None)
        # second project — not in ChromaDB but we still want a MISS, not a HIT
        try:
            _fetch_project_corpus("proj_OTHER_999", None, None)
        except Exception:
            pass   # no data for fake project — MISS still happened

    db_calls   = call_log[0]
    cache_size = len(_corpus_cache)

    record(
        "different project_id → separate MISS",
        db_calls == 2 and cache_size == 2,
        f"db_calls={db_calls} (expected 2), cache_keys={cache_size}",
    )


# ── Test 4: different hard_filters → separate MISS ───────────────────────────

def test_different_hard_filters_are_independent():
    fresh_start()

    call_log, spy = db_call_counter()
    with patch("app.core.retrieval.base.get_raw_collection", return_value=spy):
        corpus_no_filter  = _fetch_project_corpus(PROJECT_ID, None, None)
        corpus_speaker_a  = _fetch_project_corpus(PROJECT_ID, {"speaker_name": "Harsh Vardhan"}, None)
        corpus_speaker_b  = _fetch_project_corpus(PROJECT_ID, {"speaker_name": "Bhavneet Mhajan"}, None)

    db_calls   = call_log[0]
    cache_size = len(_corpus_cache)
    all_diff   = len({id(corpus_no_filter), id(corpus_speaker_a), id(corpus_speaker_b)}) == 3

    record(
        "different hard_filters → separate MISS",
        db_calls == 3 and cache_size == 3 and all_diff,
        f"db_calls={db_calls} (expected 3), cache_keys={cache_size}",
    )


# ── Test 5: same speaker called twice → HIT on second ────────────────────────

def test_same_speaker_twice_is_hit():
    fresh_start()

    filters = {"speaker_name": "Harsh Vardhan"}
    call_log, spy = db_call_counter()
    with patch("app.core.retrieval.base.get_raw_collection", return_value=spy):
        c1 = _fetch_project_corpus(PROJECT_ID, filters, None)
        c2 = _fetch_project_corpus(PROJECT_ID, filters, None)

    db_calls = call_log[0]
    same_obj = c1 is c2

    record(
        "same speaker called twice → HIT on second",
        db_calls == 1 and same_obj,
        f"db_calls={db_calls} (expected 1), same_object={same_obj}",
    )


# ── Test 6: reset clears cache, next call is MISS again ──────────────────────

def test_reset_then_miss():
    fresh_start()

    call_log, spy = db_call_counter()
    with patch("app.core.retrieval.base.get_raw_collection", return_value=spy):
        _fetch_project_corpus(PROJECT_ID, None, None)   # MISS → fills cache

    size_before_reset = len(_corpus_cache)

    reset_corpus_cache()                                 # ← the reset
    size_after_reset = len(_corpus_cache)

    with patch("app.core.retrieval.base.get_raw_collection", return_value=spy):
        _fetch_project_corpus(PROJECT_ID, None, None)   # MISS again after reset

    total_db_calls = call_log[0]

    record(
        "reset clears cache; next call is MISS again",
        size_before_reset == 1 and size_after_reset == 0 and total_db_calls == 2,
        f"size_before={size_before_reset}, size_after={size_after_reset}, db_calls={total_db_calls}",
    )


# ── Test 7: multi-tool-call simulation ───────────────────────────────────────
# Mimics what the LangGraph agent does in one query:
#   Round 1: search_transcripts("Sahil deployment")          → calls _fetch_project_corpus(project, None, scope)
#   Round 2: search_transcripts("Bhavneet deployment")       → calls _fetch_project_corpus(project, None, scope)
#   Round 3: search_transcripts("deployment timeline")       → calls _fetch_project_corpus(project, None, scope)
# All 3 have identical (project_id, hard_filters=None, date_where=scope_where).
# Expected: 1 DB call, 2 cache hits.

def test_multi_tool_call_simulation():
    fresh_start()

    scope_where = {"meeting_id": {"$eq": "proj_nolocode_001_meeting_10"}}

    call_log, spy = db_call_counter()
    with patch("app.core.retrieval.base.get_raw_collection", return_value=spy):
        c1 = _fetch_project_corpus(PROJECT_ID, None, scope_where)   # MISS
        c2 = _fetch_project_corpus(PROJECT_ID, None, scope_where)   # HIT
        c3 = _fetch_project_corpus(PROJECT_ID, None, scope_where)   # HIT

    db_calls = call_log[0]
    all_same = (c1 is c2) and (c2 is c3)

    record(
        "multi-tool-call (3 rounds, same scope) → 1 DB call, 2 HITs",
        db_calls == 1 and all_same,
        f"db_calls={db_calls} (expected 1), all_same_object={all_same}",
    )


# ── Test 8: key builder correctness ──────────────────────────────────────────

def test_key_builder():
    k1 = _make_corpus_key("proj_a", None, None)
    k2 = _make_corpus_key("proj_a", None, None)
    k3 = _make_corpus_key("proj_b", None, None)
    k4 = _make_corpus_key("proj_a", {"speaker_name": "Alice"}, None)
    k5 = _make_corpus_key("proj_a", {"speaker_name": "Alice"}, None)
    k6 = _make_corpus_key("proj_a", {"speaker_name": "Bob"},   None)
    k7 = _make_corpus_key("proj_a", None, {"meeting_id": {"$eq": "m1"}})
    k8 = _make_corpus_key("proj_a", None, {"meeting_id": {"$eq": "m1"}})
    k9 = _make_corpus_key("proj_a", None, {"meeting_id": {"$eq": "m2"}})

    passed = (
        k1 == k2          # same args → same key
        and k1 != k3      # different project → different key
        and k4 == k5      # same speaker → same key
        and k4 != k6      # different speaker → different key
        and k7 == k8      # same date_where → same key
        and k7 != k9      # different date_where → different key
        and k1 != k4      # no filter vs filter → different key
        and k1 != k7      # no scope vs scope → different key
    )
    record("key builder produces correct (in)equality", passed)


# ── Runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  Corpus Cache Test Suite")
    print("=" * 60)

    test_miss_on_first_call()
    test_hit_on_second_call()
    test_different_project_ids_are_independent()
    test_different_hard_filters_are_independent()
    test_same_speaker_twice_is_hit()
    test_reset_then_miss()
    test_multi_tool_call_simulation()
    test_key_builder()

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