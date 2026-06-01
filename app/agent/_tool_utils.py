"""
_tool_utils.py — Private implementation details for the agent tools.

Not imported by anything outside app/agent/. All public-facing tool
definitions live in tools.py — this file only contains the internals
that support them.

Contents
--------
  Signal maps & constants     _SIGNAL_MAP, _HARD/_SOFT_SIGNAL_FILTERS,
                               _SOFT_SIGNAL_PREFIX, _ROLE_LABEL, _EXPAND_TOP_N
  Doc accumulator             reset_doc_accumulator, get_accumulated_docs, _append_docs
  Timestamp formatter         _fmt_ts
  Speaker name resolver       _resolve_speaker_name
  Exhaustive signal search    _exhaustive_signal_search
  Context expansion           _fetch_neighbor, _expand_context
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from langchain_core.documents import Document

from app.core.storage.db import get_raw_collection

logger = logging.getLogger(__name__)


# ── Shared date formatter ─────────────────────────────────────────────────────

def fmt_date(val) -> str:
    """
    Convert any meeting_date value to a human-readable YYYY-MM-DD string.

    Handles three formats stored in ChromaDB:
      - Unix milliseconds (13-digit int, e.g. 1775044800000) → divide by 1000
      - Unix seconds      (10-digit int, e.g. 1775044800)    → use directly
      - ISO string        ("2026-03-10")                     → return as-is

    Use this everywhere meeting_date is shown — in tool output the LLM reads,
    in source cards, and in the sidebar. Never pass raw metadata dates to output.
    """
    if val is None:
        return ""
    if isinstance(val, (int, float)) and val > 0:
        ts = val / 1000 if val > 1e10 else val   # ms → s conversion only for 13-digit values
        try:
            return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
        except (OSError, OverflowError, ValueError):
            return str(int(val))
    s = str(val).strip()
    return s if s else ""


# ── Signal maps & constants ───────────────────────────────────────────────────

_SIGNAL_MAP = {
    "decision":       "contains_decision",
    "commitment":     "contains_commitment",
    "question":       "contains_question",
    "open_issue":     "contains_open_issue",
    "document_share": "contains_document_share",
}

# HARD signals → applied as a ChromaDB metadata gate before retrieval.
# High-precision regex means chunks without these keywords almost certainly
# aren't that type — gating is safe and improves precision.
#
# SOFT signals → intent embedded into the query text; NOT gated at DB level.
# These types can be expressed without the expected keywords
# (e.g. questions without '?', issues phrased as observations).
# Hard-gating would silently exclude valid chunks before retrieval starts.

_HARD_SIGNAL_FILTERS = frozenset({"decision", "commitment", "document_share"})
_SOFT_SIGNAL_FILTERS = frozenset({"question", "open_issue"})

_SOFT_SIGNAL_PREFIX = {
    "question":   "questions and clarifications raised about",
    "open_issue": "unresolved issues problems and blockers about",
}

# Human-readable role labels for list_speakers output
_ROLE_LABEL = {
    "client":          "Client",
    "project_manager": "Project Manager",
    "developer":       "Developer",
}

# Only the top-N ranked chunks get neighbor expansion.
# At most 2 * _EXPAND_TOP_N ChromaDB ID-lookups per search_transcripts call.
_EXPAND_TOP_N = 5

# After reranking, keep only the best N chunks before passing to the LLM.
# Matches the old RAG pipeline's post-rerank trim (10 was validated there).
# Lower = higher precision; higher = more recall. 10 is the production-tested value.
_RERANK_TOP_N = 10

# ── Diversity cap constants ───────────────────────────────────────────────────
# Applied after hybrid_retrieve, before reranking. Project-wide queries only —
# bypassed when scope_ids is set (single-meeting queries need no diversity).
#
# _DIVERSITY_CAP_FLOOR: minimum slots guaranteed to every meeting in the pool.
# _DIVERSITY_PASS_RATE: fraction of a meeting's retrieved docs that pass through.
#   Each meeting contributes at most round(count × rate) chunks, floored at 3.
# _DIVERSITY_MAX_MEETING_FRACTION: the ceiling = round(total × fraction).
#   No single meeting exceeds this share of the reranker pool.
#   Scales with k automatically — at k=25: ceiling=6, at k=40: ceiling=10.
#
# Two dominant meetings: both hit their proportional cap independently.
# One chunk meetings: cap=floor=3, but only 1 doc exists → 1 passes (floor ≠ target).

_DIVERSITY_CAP_FLOOR            = 3
_DIVERSITY_PASS_RATE            = 0.5   # each meeting passes half its retrieved docs
_DIVERSITY_MAX_MEETING_FRACTION = 0.25  # no meeting exceeds 25% of the reranker pool

# Query words that signal a broad synthesis request across meetings.
# search_transcripts doubles effective_k when detected (project-wide only).
_OVERVIEW_SIGNALS = frozenset({
    "overview", "all", "across", "throughout",
    "explain", "describe", "complete", "full", "entire",
    "summarize", "summary", "detail", "everything",
})


# ── Doc accumulator ───────────────────────────────────────────────────────────
# Collects LangChain Documents from all tool calls in one graph run.
# service.py reads these after graph.invoke() to build the sources panel.
#
# Uses in-place mutations (.clear() / .append()) so ToolNode's threads
# all see the same objects. Do NOT reassign with = [] or = {}.
#
# _chunk_counter  : global sequential [N] assigned to each new chunk this request.
# _chunk_id_to_num: dedup index — same chunk_id from two tool calls gets
#                   its existing [N] without re-appending.

_accumulated_docs: list[Document] = []
_chunk_counter:    list[int]      = [0]
_chunk_id_to_num:  dict[str, int] = {}


def reset_doc_accumulator() -> None:
    """Clear all per-request state. Called by service.py before graph.invoke()."""
    _accumulated_docs.clear()
    _chunk_counter[0] = 0
    _chunk_id_to_num.clear()


def get_accumulated_docs() -> list[Document]:
    """Return a copy of docs collected across all tool calls this request."""
    return list(_accumulated_docs)


def _append_docs(docs: list[Document]) -> list[int]:
    """
    Assign a global sequential [N] to each doc and accumulate it.
    Returns [N] numbers — callers embed these in tool output for LLM citations.
    Deduplicates: same chunk_id across multiple tool calls gets one entry only.
    """
    numbers: list[int] = []
    for doc in docs:
        chunk_id = doc.metadata.get("chunk_id", "")
        if chunk_id and chunk_id in _chunk_id_to_num:
            numbers.append(_chunk_id_to_num[chunk_id])
        else:
            _chunk_counter[0] += 1
            n = _chunk_counter[0]
            doc.metadata["_global_chunk_num"] = n
            numbers.append(n)
            _accumulated_docs.append(doc)
            if chunk_id:
                _chunk_id_to_num[chunk_id] = n
    return numbers


# ── Timestamp formatter ───────────────────────────────────────────────────────

def _fmt_ts(sec: int | float | None) -> str:
    """Convert seconds-from-meeting-start → (MM:SS) or (H:MM:SS)."""
    if sec is None:
        return ""
    total = int(sec)
    h, rem = divmod(total, 3600)
    m, s   = divmod(rem, 60)
    return f"({h}:{m:02d}:{s:02d})" if h else f"({m:02d}:{s:02d})"


# ── Speaker name resolver ─────────────────────────────────────────────────────
# LLMs often guess names slightly wrong ("Bhavneet Mahajan" vs "Bhavneet Mhajan").
# ChromaDB $eq is exact-match only — wrong name = 0 results silently.

def _resolve_speaker_name(partial_name: str, project_id: str) -> Optional[str]:
    """
    Resolve a partial/approximate speaker name to the exact stored name.

    Resolution order (stops at first match):
      1. Exact match
      2. Case-insensitive exact
      3. All words in partial_name appear in candidate name
      4. First name only (safe only when unique in project)

    Returns None if no match — caller falls back to unfiltered search.
    """
    if not partial_name:
        return None
    try:
        collection = get_raw_collection()
        results    = collection.get(
            where={"project_id": {"$eq": project_id}},
            include=["metadatas"],
        )
        names: set[str] = {
            m["speaker_name"]
            for m in results.get("metadatas", [])
            if m.get("speaker_name") and not m.get("is_meeting_summary")
        }

        if partial_name in names:
            return partial_name

        partial_lower = partial_name.lower()
        for name in names:
            if name.lower() == partial_lower:
                return name

        partial_words = [w.lower() for w in partial_name.split() if w]
        if partial_words:
            word_matches = [n for n in names if all(pw in n.lower() for pw in partial_words)]
            if len(word_matches) == 1:
                return word_matches[0]

            first_matches = [n for n in names if n.lower().split()[0] == partial_words[0]]
            if len(first_matches) == 1:
                return first_matches[0]

        logger.info("_resolve_speaker_name | no match for %r | known: %s", partial_name, sorted(names))
        return None

    except Exception as exc:
        logger.warning("_resolve_speaker_name error: %s", exc)
        return None


# ── Exhaustive signal search ──────────────────────────────────────────────────
# Used by search_transcripts when signal_filter + scope_ids are both set.
# completeness beats ranking here — must return ALL matching chunks, not top-k.

def _exhaustive_signal_search(
    project_id:    str,
    signal_filter: str,
    scope_ids:     list,
    speaker_name:  Optional[str] = None,
) -> str:
    """
    Fetch every chunk matching (project + signal + scope) via metadata scan.
    Sorted chronologically. Returns a formatted string for the LLM.
    """
    and_clauses: list[dict] = [
        {"project_id":              {"$eq": project_id}},
        {_SIGNAL_MAP[signal_filter]: {"$eq": True}},
        {"is_meeting_summary":      {"$ne": True}},
    ]
    if len(scope_ids) == 1:
        and_clauses.append({"meeting_id": {"$eq": scope_ids[0]}})
    else:
        and_clauses.append({"meeting_id": {"$in": scope_ids}})
    if speaker_name:
        and_clauses.append({"speaker_name": {"$eq": speaker_name}})

    try:
        collection = get_raw_collection()
        results    = collection.get(
            where={"$and": and_clauses},
            include=["documents", "metadatas"],
        )
    except Exception as exc:
        logger.warning("_exhaustive_signal_search error: %s", exc)
        return f"Search failed: {exc}"

    raw_docs  = results.get("documents", [])
    raw_metas = results.get("metadatas", [])

    if not raw_docs:
        return f"No '{signal_filter}' chunks found in the specified meeting(s)."

    docs = [Document(page_content=t, metadata=m) for t, m in zip(raw_docs, raw_metas)]
    docs.sort(key=lambda d: d.metadata.get("start_time", 0))

    chunk_numbers = _append_docs(docs)
    spk_note = f" by {speaker_name}" if speaker_name else ""
    lines: list[str] = [
        f"Found {len(docs)} '{signal_filter}' chunks{spk_note} "
        f"(complete scan of {len(scope_ids)} meeting(s) — all matches returned):\n"
    ]
    for doc, num in zip(docs, chunk_numbers):
        meta = doc.metadata
        ts   = _fmt_ts(meta.get("start_time"))
        lines.append(f"[{num}] {meta.get('speaker_name','Unknown')} {ts} — {meta.get('meeting_title','Unknown Meeting')} ({fmt_date(meta.get('meeting_date',''))})")
        lines.append(f"    {doc.page_content.strip()[:400]}")
        lines.append("")
    return "\n".join(lines)


# ── Context expansion ─────────────────────────────────────────────────────────

def _fetch_neighbor(chunk_id: str, position: str) -> Optional[Document]:
    """
    Fetch one neighbor chunk by chunk_id. Returns None on miss or DB error.
    position ('before'/'after') is stored in _position metadata so the
    formatter labels it and _append_docs skips it from the sources panel.
    """
    try:
        rows = get_raw_collection().get(ids=[chunk_id], include=["documents", "metadatas"])
        if rows.get("ids"):
            return Document(
                page_content=rows["documents"][0],
                metadata={**rows["metadatas"][0], "_position": position},
            )
    except Exception as exc:
        logger.debug("_fetch_neighbor failed for %s: %s", chunk_id, exc)
    return None


def _expand_context(docs: list[Document], n: int = _EXPAND_TOP_N) -> list[Document]:
    """
    Inject prev/next neighbor chunks adjacent to the top-n anchor docs.

    A retrieved chunk is a ~500-char slice of conversation. The sentence just
    before or after often contains the cause, consequence, or reply the LLM
    needs for a complete answer.

    Cost: at most 2*n ChromaDB ID-lookups (O(1) fetches, not corpus scans).
    Dedup: existing_ids prevents a neighbor appearing twice if it was also top-k.
    Neighbors carry _position='before'/'after' → labeled [CONTEXT] in output,
    excluded from accumulated_docs so they don't appear as citable sources.
    """
    if not docs:
        return docs

    existing_ids: set[str] = {d.metadata.get("chunk_id", "") for d in docs}
    result: list[Document] = []

    for i, doc in enumerate(docs):
        m = doc.metadata

        if i >= n or m.get("is_meeting_summary"):
            result.append(doc)
            continue

        prev_id = m.get("prev_chunk_id")
        if prev_id and prev_id not in existing_ids:
            neighbor = _fetch_neighbor(prev_id, "before")
            if neighbor:
                result.append(neighbor)
                existing_ids.add(prev_id)

        result.append(doc)

        next_id = m.get("next_chunk_id")
        if next_id and next_id not in existing_ids:
            neighbor = _fetch_neighbor(next_id, "after")
            if neighbor:
                result.append(neighbor)
                existing_ids.add(next_id)

    return result


# ── Meeting diversity cap ─────────────────────────────────────────────────────

def _apply_diversity_cap(docs: list[Document]) -> list[Document]:
    """
    Limit chunks per meeting_id before reranking.

    Each meeting passes at most PASS_RATE of its retrieved docs, with a
    minimum floor of _DIVERSITY_CAP_FLOOR and a ceiling that scales with
    the total pool size (round(total × _DIVERSITY_MAX_MEETING_FRACTION)).

    Proportional ceiling means overview queries (k=40) allow more chunks
    from a dedicated meeting than focused queries (k=25) — consistent with
    the k-boost intent. RRF rank order is preserved within each meeting.

    Called only for project-wide queries (scope_ids=None in tools.py).
    """
    if not docs:
        return docs

    from collections import Counter
    counts      = Counter(d.metadata.get("meeting_id", "") for d in docs)
    total       = len(docs)
    cap_ceiling = max(_DIVERSITY_CAP_FLOOR, round(total * _DIVERSITY_MAX_MEETING_FRACTION))

    seen:    dict[str, int] = {}
    diverse: list[Document] = []

    for doc in docs:
        mid = doc.metadata.get("meeting_id", "")
        cap = max(
            _DIVERSITY_CAP_FLOOR,
            min(cap_ceiling, round(counts[mid] * _DIVERSITY_PASS_RATE)),
        )
        if seen.get(mid, 0) < cap:
            diverse.append(doc)
            seen[mid] = seen.get(mid, 0) + 1

    logger.debug(
        "diversity_cap | input=%d | output=%d | ceiling=%d | meetings_in_pool=%d",
        total, len(diverse), cap_ceiling, len(counts),
    )
    return diverse