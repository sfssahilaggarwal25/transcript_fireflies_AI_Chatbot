"""
constants.py — Signal maps, thresholds, and small formatters.

All magic numbers and lookup tables live here so they have one source of truth.
fmt_date and _fmt_ts are folded in — they are too small to warrant their own file.
"""

from datetime import datetime, timezone

# ── Signal maps ───────────────────────────────────────────────────────────────

_SIGNAL_MAP = {
    "decision":       "contains_decision",
    "commitment":     "contains_commitment",
    "question":       "contains_question",
    "open_issue":     "contains_open_issue",
    "document_share": "contains_document_share",
}

# HARD signals → applied as a ChromaDB metadata gate before retrieval.
# Only document_share stays hard — file sharing is always explicit ("shared a doc",
# "here's the link") so regex precision is near-perfect. Hard-gating safe here.
#
# SOFT signals → intent embedded into the query text; NOT gated at DB level.
# decision/commitment moved from hard → soft because meeting conversations express
# these implicitly ("I don't think it's required", "let's go with X", "makes sense")
# without using explicit "decided/committed" keywords. Hard-gating silently excluded
# the most valuable chunks. Soft lets reranker find them semantically.
#
# count_signal_chunks and _exhaustive_signal_search still use the stored
# contains_* tags directly — they are unaffected by this change.

_HARD_SIGNAL_FILTERS = frozenset({"document_share"})
_SOFT_SIGNAL_FILTERS = frozenset({"decision", "commitment", "question", "open_issue"})

_SOFT_SIGNAL_PREFIX = {
    "decision":   "decided about",
    "commitment": "committed to about",
    "question":   "questions and clarifications raised about",
    "open_issue": "unresolved issues problems and blockers about",
}

# Human-readable role labels for list_speakers output
_ROLE_LABEL = {
    "client":          "Client",
    "project_manager": "Project Manager",
    "developer":       "Developer",
}

# ── Expansion threshold ───────────────────────────────────────────────────────

# Only the top-N ranked chunks get post-rerank neighbor expansion.
# At most 2 * _EXPAND_TOP_N ChromaDB ID-lookups per search_transcripts call.
_EXPAND_TOP_N = 5

# Chunks shorter than this are treated as fragments that lose meaning without
# context. They get neighbor expansion BEFORE reranking so the reranker can
# score the full conversational unit, not just the isolated fragment.
SHORT_CHUNK_THRESHOLD = 120


# ── Formatters ────────────────────────────────────────────────────────────────

def fmt_date(val) -> str:
    """
    Convert any meeting_date value to a human-readable YYYY-MM-DD string.

    Handles three formats stored in ChromaDB:
      - Unix milliseconds (13-digit int, e.g. 1775044800000) → divide by 1000
      - Unix seconds      (10-digit int, e.g. 1775044800)    → use directly
      - ISO string        ("2026-03-10")                     → return as-is
    """
    if val is None:
        return ""
    if isinstance(val, (int, float)) and val > 0:
        ts = val / 1000 if val > 1e10 else val
        try:
            return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
        except (OSError, OverflowError, ValueError):
            return str(int(val))
    s = str(val).strip()
    return s if s else ""


def _fmt_ts(sec: int | float | None) -> str:
    """Convert seconds-from-meeting-start → (MM:SS) or (H:MM:SS)."""
    if sec is None:
        return ""
    total = int(sec)
    h, rem = divmod(total, 3600)
    m, s   = divmod(rem, 60)
    return f"({h}:{m:02d}:{s:02d})" if h else f"({m:02d}:{s:02d})"