"""
tools.py — Production tool definitions for the LangGraph agent.

Every tool reads project_id and scope from state via InjectedState.
The LLM never supplies these — they are enforced server-side.

Tools
-----
  search_transcripts    — Hybrid BM25 + dense search. The main workhorse.
  get_meeting_summaries — Fetch pre-built meeting summary paragraphs.
  list_meetings         — Meeting titles, dates, and numbers (no content).
  list_speakers         — Speaker names, roles, chunk counts (scope-aware).
  count_signal_chunks   — Exact metadata count for signal-flagged chunks.

Thread-safe doc accumulator
----------------------------
  reset_doc_accumulator()  — Call at start of each answer_query() request.
  get_accumulated_docs()   — Call after graph.invoke() to build sources panel.
"""

import logging
from typing import Annotated, Optional

from langchain_core.documents import Document
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from app.core.retrieval import hybrid_retrieve
from app.core.storage.db import get_raw_collection

logger = logging.getLogger(__name__)


# ── Signal map — shared by search_transcripts AND count_signal_chunks ─────────
# Maps the short name the LLM uses → the actual ChromaDB metadata field name.
# Keep this at module level so both tools can import it.

_SIGNAL_MAP = {
    "decision":       "contains_decision",
    "commitment":     "contains_commitment",
    "question":       "contains_question",
    "open_issue":     "contains_open_issue",
    "document_share": "contains_document_share",
}

# Signal filter behaviour — determined by regex detection precision.
#
# HARD signals → apply as a ChromaDB metadata gate before retrieval.
#   These keywords are specific and unambiguous. If a chunk lacks them it almost
#   certainly isn't that type, so gating is safe and improves precision.
#   "decided / agreed / I will / shared a document" — hard to express without keywords.
#
# SOFT signals → embed intent into the query text; do NOT gate at DB level.
#   These types can be expressed without the expected keywords:
#     question  : "Walk me through this." / "Not sure I follow." — no '?' anywhere
#     open_issue: "The numbers look off." / "X behaves unexpectedly." — no issue keyword
#   Hard-gating silently excludes these valid chunks before retrieval even starts.
#   Embedding in the query lets dense + BM25 rank by relevance instead.

_HARD_SIGNAL_FILTERS = frozenset({"decision", "commitment", "document_share"})
_SOFT_SIGNAL_FILTERS = frozenset({"question", "open_issue"})

# Query prefix injected when a soft signal is requested.
# Steers both BM25 (keyword match) and dense (semantic match) toward the intent.
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


# ── Per-request doc accumulator ───────────────────────────────────────────────
# Collects LangChain Documents from all tool calls in one graph run.
# service.py reads these after graph.invoke() to build the sources panel.
#
# Uses in-place mutations (.clear() / .append()) so ToolNode's threads
# all see the same objects. Do NOT reassign with = [] or = {} — that breaks it.
#
# _chunk_counter  : global sequential [N] assigned to each new chunk this request.
# _chunk_id_to_num: dedup index — if the same chunk_id comes back from two tool
#                   calls we return its existing [N] without re-appending.

_accumulated_docs:  list[Document]  = []
_chunk_counter:     list[int]       = [0]   # single-element list so reset is in-place
_chunk_id_to_num:   dict[str, int]  = {}    # chunk_id → global [N]


def reset_doc_accumulator() -> None:
    """Clear all per-request state before each new query. Called by service.py."""
    _accumulated_docs.clear()
    _chunk_counter[0] = 0
    _chunk_id_to_num.clear()


def get_accumulated_docs() -> list[Document]:
    """Return a copy of docs collected across all tool calls this request."""
    return list(_accumulated_docs)


def _append_docs(docs: list[Document]) -> list[int]:
    """
    Assign a global sequential [N] to each doc and accumulate it.

    Returns the list of [N] numbers — callers embed these directly in tool output
    so the LLM can write [N] citations that align with the sources panel.

    Deduplication: if the same chunk_id appears in multiple tool calls (e.g. the
    same decision chunk retrieved by two different searches), we return its existing
    number without re-appending — no double entries in the sources panel.
    """
    numbers: list[int] = []
    for doc in docs:
        chunk_id = doc.metadata.get("chunk_id", "")
        if chunk_id and chunk_id in _chunk_id_to_num:
            # Already seen this chunk — return existing number, skip re-appending
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


# ── Speaker name resolver ─────────────────────────────────────────────────────
# LLMs often guess speaker names slightly wrong (e.g. "Bhavneet Mahajan" when
# the stored name is "Bhavneet Mhajan"). ChromaDB $eq is exact — wrong name = 0
# results. This helper resolves partial/approximate names to exact stored names.

def _resolve_speaker_name(partial_name: str, project_id: str) -> Optional[str]:
    """
    Find the best matching exact speaker name from the project's ChromaDB data.

    Resolution order (stops at first match):
      1. Exact match                    "Bhavneet Mhajan" → "Bhavneet Mhajan"
      2. Case-insensitive exact         "bhavneet mhajan" → "Bhavneet Mhajan"
      3. All words present in name      "Bhavneet Mahajan" → tries each word
      4. First name only (unique)       "Bhavneet" → "Bhavneet Mhajan" (if only one)

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
        # Collect unique non-summary speaker names
        names: set[str] = set()
        for m in results.get("metadatas", []):
            n = m.get("speaker_name")
            if n and not m.get("is_meeting_summary"):
                names.add(n)

        # 1. Exact match
        if partial_name in names:
            return partial_name

        # 2. Case-insensitive exact
        partial_lower = partial_name.lower()
        for name in names:
            if name.lower() == partial_lower:
                return name

        # 3. All words in partial_name appear somewhere in the candidate name
        partial_words = [w.lower() for w in partial_name.split() if w]
        if partial_words:
            word_matches = [
                n for n in names
                if all(pw in n.lower() for pw in partial_words)
            ]
            if len(word_matches) == 1:
                return word_matches[0]

        # 4. First name only — safe only if unique
        if partial_words:
            first = partial_words[0]
            first_matches = [
                n for n in names
                if n.lower().split()[0] == first
            ]
            if len(first_matches) == 1:
                return first_matches[0]

        logger.info(
            "_resolve_speaker_name | no match for %r | known: %s",
            partial_name, sorted(names),
        )
        return None

    except Exception as exc:
        logger.warning("_resolve_speaker_name error: %s", exc)
        return None


# ── Exhaustive signal search ──────────────────────────────────────────────────
# Used by search_transcripts when signal_filter + scope_ids are both set.
# Returns ALL matching chunks via metadata scan — no k limit, no missed results.

def _exhaustive_signal_search(
    project_id:    str,
    signal_filter: str,
    scope_ids:     list,
    speaker_name:  Optional[str] = None,
) -> str:
    """
    Fetch EVERY chunk matching (signal_filter + scope_ids) from ChromaDB metadata.

    Why this exists:
      hybrid_retrieve uses semantic ranking and caps results at k.
      For "list ALL questions in this meeting", completeness beats ranking —
      we must return every signal-flagged chunk, not just the top-k most relevant.

    Sorted chronologically by start_time so the LLM sees events in order.
    """
    # Build the filter — always include project + signal + exclude summary chunks
    and_clauses: list[dict] = [
        {"project_id":         {"$eq": project_id}},
        {_SIGNAL_MAP[signal_filter]: {"$eq": True}},
        {"is_meeting_summary": {"$ne": True}},
    ]

    # Scope to specific meeting(s)
    if len(scope_ids) == 1:
        and_clauses.append({"meeting_id": {"$eq": scope_ids[0]}})
    else:
        and_clauses.append({"meeting_id": {"$in": scope_ids}})

    # Optional speaker restriction
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

    # Build Document objects and sort chronologically
    docs = [
        Document(page_content=text, metadata=meta)
        for text, meta in zip(raw_docs, raw_metas)
    ]
    docs.sort(key=lambda d: d.metadata.get("start_time", 0))

    # Assign global [N] numbers before formatting — LLM uses these for citations
    chunk_numbers = _append_docs(docs)

    # Header tells the LLM this is exhaustive — not a ranked top-k
    n_mtgs   = len(scope_ids)
    spk_note = f" by {speaker_name}" if speaker_name else ""
    lines: list[str] = [
        f"Found {len(docs)} '{signal_filter}' chunks{spk_note} "
        f"(complete scan of {n_mtgs} meeting(s) — all matches returned):\n"
    ]
    for doc, num in zip(docs, chunk_numbers):
        meta    = doc.metadata
        speaker = meta.get("speaker_name", "Unknown")
        meeting = meta.get("meeting_title", "Unknown Meeting")
        date    = meta.get("meeting_date", "")
        ts      = _fmt_ts(meta.get("start_time"))
        lines.append(f"[{num}] {speaker} {ts} — {meeting} ({date})")
        lines.append(f"    {doc.page_content.strip()[:400]}")
        lines.append("")

    return "\n".join(lines)


# ── Timestamp formatter ───────────────────────────────────────────────────────

def _fmt_ts(sec: int | float | None) -> str:
    """Convert seconds to (MM:SS) or (H:MM:SS) string."""
    if sec is None:
        return ""
    total = int(sec)
    h, rem = divmod(total, 3600)
    m, s   = divmod(rem, 60)
    if h:
        return f"({h}:{m:02d}:{s:02d})"
    return f"({m:02d}:{s:02d})"


# ── Tool 1: search_transcripts ────────────────────────────────────────────────

@tool
def search_transcripts(
    query: str,
    k: int = 15,
    speaker_name: Optional[str] = None,
    signal_filter: Optional[str] = None,
    state: Annotated[dict, InjectedState] = None,
) -> str:
    """Search meeting transcript chunks using hybrid semantic + keyword search.

    This is the MAIN tool for retrieving spoken content. Use it for any question about:
    - What was said, discussed, or explained in meetings
    - Specific topics, technical decisions, features, or blockers
    - Speaker contributions (use speaker_name to scope to one person)
    - Decisions made (signal_filter='decision')
    - Action items / commitments (signal_filter='commitment')
    - Questions that were raised (signal_filter='question')
    - Open issues / blockers (signal_filter='open_issue')
    - Documents / files shared by participants (signal_filter='document_share')

    For COUNTING signal types (e.g. "how many commitments?"), use count_signal_chunks instead.
    For SUMMARIES of a meeting, use get_meeting_summaries instead.

    Parameters
    ----------
    query : str
        Natural language search query. Be specific — 'ONCA forecasting decision' is
        better than 'what was decided'. Good queries include topic keywords, names,
        or technical terms likely to appear in the transcript.
    k : int, optional
        Number of chunks to retrieve (default 15, max 25). The system automatically
        adjusts k based on query scope — only override when you need more than default:
        set k=25 for "give me ALL", set k=10 for "find any single example".
    speaker_name : str, optional
        Filter results to a specific speaker's contributions only. Use the full name
        as it appears in meeting records (e.g. 'Harsh Vardhan', 'Bhavneet Mahajan').
    signal_filter : str, optional
        Restrict results to chunks containing a specific signal type.
        One of: 'decision', 'commitment', 'question', 'open_issue', 'document_share'.
        Use 'decision' for what was decided/agreed.
        Use 'commitment' for action items and ownership statements.
        Use 'question' for questions raised and clarifications asked.
        Use 'open_issue' for unresolved problems and blockers.
        Use 'document_share' for files, links, or documents shared by participants.
        If this filter returns 0 results, retry the call WITHOUT this filter.
    """
    # Guard: empty query breaks BM25 and produces meaningless results.
    # Return a clear error so the LLM retries with real keywords — never silently proceed.
    if not query or not query.strip():
        return (
            "Error: 'query' cannot be empty. "
            "Provide 2–4 keywords describing what to search for "
            "(e.g. 'questions raised timeline', 'AI architecture decision'). "
            "signal_filter alone is not enough — query is always required."
        )

    project_id    = state["project_id"]
    scope_where   = state.get("scope_where")
    scope_ids     = state.get("scope_ids")
    recommended_k = state.get("recommended_k", 15)

    # Resolve approximate speaker name → exact stored name.
    # LLMs often guess names slightly wrong (e.g. "Bhavneet Mahajan" vs "Bhavneet Mhajan").
    # ChromaDB $eq is exact-match only — wrong name = 0 results silently.
    resolved_speaker = None
    if speaker_name:
        resolved_speaker = _resolve_speaker_name(speaker_name, project_id)
        if resolved_speaker and resolved_speaker != speaker_name:
            logger.info(
                "search_transcripts | speaker name resolved: %r → %r",
                speaker_name, resolved_speaker,
            )
        elif not resolved_speaker:
            logger.warning(
                "search_transcripts | speaker %r not found in project — searching without filter",
                speaker_name,
            )

    # ── Exhaustive signal path ────────────────────────────────────────────────
    # When signal_filter + scope_ids are both set, we need COMPLETENESS not ranking.
    # hybrid_retrieve caps results at k — it would miss signal chunks ranked below k.
    # Example: 28 question chunks in a meeting, k=25 → 3 missed silently.
    #
    # Fix: use collection.get() (pure metadata scan, no k limit) to fetch EVERY
    # chunk with that signal flag in the scoped meeting(s), then sort by time.
    # This path is only for scoped queries — project-wide signal queries still use
    # hybrid_retrieve because semantic ranking matters more than completeness there.
    if signal_filter and signal_filter in _SIGNAL_MAP and scope_ids:
        return _exhaustive_signal_search(
            project_id=project_id,
            signal_filter=signal_filter,
            scope_ids=scope_ids,
            speaker_name=resolved_speaker,  # use resolved name
        )

    # Use the larger of: what the LLM asked for, or what the scope recommends.
    # Never exceed 25. This prevents under-fetching on project-wide queries.
    effective_k = min(max(int(k), recommended_k), 25)

    # Build metadata filters for the retrieval call
    filters: dict = {}
    if resolved_speaker:
        filters["speaker_name"] = resolved_speaker   # exact resolved name

    # Signal filter — two behaviours based on detection precision:
    #
    #   HARD (decision, commitment, document_share):
    #     Apply as a ChromaDB metadata gate. High-precision regex means chunks
    #     without these keywords almost certainly aren't that type — gating is safe.
    #
    #   SOFT (question, open_issue):
    #     Do NOT gate at DB level. Regex misses implicit forms — questions without '?',
    #     issues phrased as observations. Hard-gating silently excludes those chunks
    #     before retrieval starts. Instead, embed the intent into the query so
    #     hybrid_retrieve ranks by relevance rather than gates by metadata flag.
    effective_query = query
    if signal_filter and signal_filter in _SIGNAL_MAP:
        if signal_filter in _HARD_SIGNAL_FILTERS:
            filters[_SIGNAL_MAP[signal_filter]] = True
        elif signal_filter in _SOFT_SIGNAL_FILTERS:
            prefix = _SOFT_SIGNAL_PREFIX.get(signal_filter, "")
            if prefix:
                effective_query = f"{prefix} {query}"
                logger.info(
                    "search_transcripts | soft signal=%s → query rewritten: %r",
                    signal_filter, effective_query,
                )

    try:
        docs = hybrid_retrieve(
            query=effective_query,
            project_id=project_id,
            hard_filters=filters if filters else None,
            date_where=scope_where,
            k=effective_k,
        )
    except Exception as exc:
        logger.warning("search_transcripts error: %s", exc)
        return f"Search failed: {exc}"

    if not docs:
        return "No relevant transcript chunks found for this query."

    # Assign global [N] numbers before formatting — LLM uses these for citations
    chunk_numbers = _append_docs(docs)

    # Format results for the LLM to read
    lines: list[str] = [f"Found {len(docs)} relevant chunks:\n"]
    for doc, num in zip(docs, chunk_numbers):
        meta    = doc.metadata
        speaker = meta.get("speaker_name", "Unknown")
        meeting = meta.get("meeting_title", "Unknown Meeting")
        date    = meta.get("meeting_date", "")
        ts      = _fmt_ts(meta.get("start_time"))

        lines.append(f"[{num}] {speaker} {ts} — {meeting} ({date})")
        lines.append(f"    {doc.page_content.strip()[:400]}")
        lines.append("")

    return "\n".join(lines)


# ── Tool 2: get_meeting_summaries ─────────────────────────────────────────────

@tool
def get_meeting_summaries(
    meeting_title: Optional[str] = None,
    state: Annotated[dict, InjectedState] = None,
) -> str:
    """Fetch high-level summaries of project meetings.

    Use this tool when the user asks for:
    - Overall project progress or status
    - What happened in a specific meeting
    - A recap or overview of any meeting
    - The agenda or main themes of a meeting

    Parameters
    ----------
    meeting_title : str, optional
        Partial or full meeting title to filter. Leave empty to get all summaries
        (or all summaries within the active scope).
    """
    project_id = state["project_id"]
    scope_ids  = state.get("scope_ids")    # list of meeting IDs, or None

    try:
        collection = get_raw_collection()
        results    = collection.get(
            where={
                "$and": [
                    {"project_id":         {"$eq": project_id}},
                    {"is_meeting_summary": {"$eq": True}},
                ]
            },
            include=["documents", "metadatas"],
        )
        raw_docs = results.get("documents", [])
        metas    = results.get("metadatas", [])
    except Exception as exc:
        logger.warning("get_meeting_summaries error: %s", exc)
        return f"Failed to fetch summaries: {exc}"

    if not raw_docs:
        return "No meeting summaries found for this project."

    # Build LangChain Documents
    docs = [
        Document(page_content=text, metadata=meta)
        for text, meta in zip(raw_docs, metas)
    ]

    # Filter to active scope (specific meeting IDs) if set
    if scope_ids:
        docs = [d for d in docs if d.metadata.get("meeting_id") in scope_ids]
        if not docs:
            return "No summary found for the specified meeting(s)."

    # Optional: filter further by title (LLM-supplied)
    if meeting_title:
        docs = [
            d for d in docs
            if meeting_title.lower() in d.metadata.get("meeting_title", "").lower()
        ]
        if not docs:
            return f"No summary found matching '{meeting_title}'."

    # Sort chronologically BEFORE assigning global numbers so [N] matches reading order
    sorted_docs   = sorted(docs, key=lambda d: str(d.metadata.get("meeting_date", "")))
    chunk_numbers = _append_docs(sorted_docs)

    # Format output with [N] citations so LLM can reference summaries inline
    lines: list[str] = [f"Found {len(sorted_docs)} meeting summary/summaries:\n"]
    for doc, num in zip(sorted_docs, chunk_numbers):
        title = doc.metadata.get("meeting_title", "Unknown Meeting")
        date  = doc.metadata.get("meeting_date", "")
        num_m = doc.metadata.get("meeting_number", "")
        lines.append(f"[{num}] ## Meeting #{num_m}: {title}  ({date})")
        lines.append(doc.page_content.strip()[:800])
        lines.append("")

    return "\n".join(lines)


# ── Tool 3: list_meetings ─────────────────────────────────────────────────────

@tool
def list_meetings(
    state: Annotated[dict, InjectedState] = None,
) -> str:
    """List all meetings in this project with their titles, dates, and numbers.

    Use this tool when asked:
    - How many meetings have happened?
    - When was the last (or first) meeting?
    - Show me all meetings in order
    - Which meetings occurred in April / May?
    """
    project_id = state["project_id"]

    try:
        collection = get_raw_collection()
        results    = collection.get(
            where={"project_id": {"$eq": project_id}},
            include=["metadatas"],
        )
        metas = results.get("metadatas", [])
    except Exception as exc:
        return f"Failed to list meetings: {exc}"

    # Collect unique meetings (skip summary chunks)
    seen: dict[str, dict] = {}
    for m in metas:
        mid = m.get("meeting_id")
        if mid and not m.get("is_meeting_summary"):
            if mid not in seen:
                seen[mid] = {
                    "title":  m.get("meeting_title", "Unknown"),
                    "date":   m.get("meeting_date", ""),
                    "number": m.get("meeting_number", "?"),
                }

    if not seen:
        return "No meetings found for this project."

    meetings = sorted(seen.values(), key=lambda x: x["date"])
    lines = [f"{len(meetings)} meetings in this project:\n"]
    for m in meetings:
        lines.append(f"  Meeting #{m['number']}: {m['title']}  —  {m['date']}")

    return "\n".join(lines)


# ── Tool 4: list_speakers ─────────────────────────────────────────────────────

@tool
def list_speakers(
    state: Annotated[dict, InjectedState] = None,
) -> str:
    """List all speakers in this project with their roles and participation count.

    Use this tool when asked:
    - Who attended the meetings?
    - Who attended the previous / last meeting?
    - Who is the client / project manager / developer?
    - Who spoke the most in this project?
    - How many people were in the last meeting?

    When a meeting scope is active, shows only speakers from that meeting.
    Output is sorted by chunk count (most talkative first).
    """
    project_id = state["project_id"]
    scope_ids  = state.get("scope_ids")

    # Build the ChromaDB where clause.
    # If scope_ids is set, restrict to those meetings only.
    if scope_ids:
        if len(scope_ids) == 1:
            where = {
                "$and": [
                    {"project_id": {"$eq": project_id}},
                    {"meeting_id": {"$eq": scope_ids[0]}},
                ]
            }
        else:
            where = {
                "$and": [
                    {"project_id": {"$eq": project_id}},
                    {"meeting_id": {"$in": scope_ids}},
                ]
            }
    else:
        where = {"project_id": {"$eq": project_id}}

    try:
        collection = get_raw_collection()
        results    = collection.get(where=where, include=["metadatas"])
        metas      = results.get("metadatas", [])
    except Exception as exc:
        return f"Failed to list speakers: {exc}"

    # Count chunks per speaker (skip summary chunks — they don't represent a speaker)
    speakers: dict[str, dict] = {}   # name → {"role": ..., "count": N}
    for m in metas:
        name = m.get("speaker_name")
        if name and not m.get("is_meeting_summary"):
            if name not in speakers:
                speakers[name] = {
                    "role":  m.get("speaker_role", "unknown"),
                    "count": 0,
                }
            speakers[name]["count"] += 1

    if not speakers:
        return "No speakers found for this project."

    # Header: note scope if active so LLM knows it's not project-wide
    if scope_ids:
        header = f"{len(speakers)} speakers (scoped to {len(scope_ids)} meeting(s)):\n"
    else:
        header = f"{len(speakers)} speakers in this project:\n"

    # Sort by chunk count descending so LLM sees "who spoke most" directly
    lines: list[str] = [header]
    for name, info in sorted(speakers.items(), key=lambda x: x[1]["count"], reverse=True):
        label = _ROLE_LABEL.get(info["role"], info["role"].replace("_", " ").title())
        lines.append(f"  - {name}  [{label}]  ({info['count']} chunks)")

    return "\n".join(lines)


# ── Tool 5: count_signal_chunks ───────────────────────────────────────────────

@tool
def count_signal_chunks(
    signal_filter: str,
    speaker_name: Optional[str] = None,
    state: Annotated[dict, InjectedState] = None,
) -> str:
    """Return the DETECTED count of chunks containing a specific signal type.

    Use for:
    - "How many commitments were made?" → count_signal_chunks(signal_filter='commitment')
    - "How many questions did Bhavneet raise?" → count_signal_chunks(signal_filter='question', speaker_name='Bhavneet Mahajan')
    - "How many issues in the previous meeting?" → count_signal_chunks(signal_filter='open_issue') [scope auto-applied]
    - "How many decisions were made in this project?" → count_signal_chunks(signal_filter='decision')
    - "How many documents were shared?" → count_signal_chunks(signal_filter='document_share')

    Returns count from ChromaDB metadata — no k limit, scope applied automatically.

    Signal Detection Note
    ---------------------
    Signals are detected by regex patterns at ingestion time. The count is a
    comprehensive estimate — it may slightly over or under-count compared to
    ground truth. When reporting to the user, say "about N" or "at least N",
    not "exactly N". Use search_transcripts to verify specific instances.

    For "how many X about [topic]" (e.g. "questions about AI architecture"),
    use search_transcripts(query=topic, signal_filter=signal) instead — that
    does a semantic search and you count the results shown in the header.

    Parameters
    ----------
    signal_filter : str
        Required. One of: 'decision', 'commitment', 'question', 'open_issue',
        'document_share'.
    speaker_name : str, optional
        Restrict the count to one specific speaker.
    """
    # Guard against unknown signal types before touching the database
    if signal_filter not in _SIGNAL_MAP:
        return (
            f"Unknown signal_filter '{signal_filter}'. "
            f"Valid options: {list(_SIGNAL_MAP.keys())}"
        )

    project_id  = state["project_id"]
    scope_ids   = state.get("scope_ids")
    scope_where = state.get("scope_where")
    scope_type  = state.get("scope_type", "project")

    # Resolve approximate speaker name to exact stored name
    resolved_speaker = _resolve_speaker_name(speaker_name, project_id) if speaker_name else None

    # Build filter clauses — always include project + signal + exclude summaries
    and_clauses = [
        {"project_id":          {"$eq": project_id}},
        {_SIGNAL_MAP[signal_filter]: {"$eq": True}},
        {"is_meeting_summary":  {"$ne": True}},   # $ne catches False AND missing
    ]

    if resolved_speaker:
        and_clauses.append({"speaker_name": {"$eq": resolved_speaker}})

    # Add scope filter:
    #   "meeting" scope → filter by specific meeting IDs
    #   "date_range" scope → scope_where already has {"meeting_date": {"$gte": ...}}
    #   "project" scope → no extra clause (count everything)
    if scope_ids:
        if len(scope_ids) == 1:
            and_clauses.append({"meeting_id": {"$eq": scope_ids[0]}})
        else:
            and_clauses.append({"meeting_id": {"$in": scope_ids}})
    elif scope_type == "date_range" and scope_where:
        and_clauses.append(scope_where)

    try:
        collection = get_raw_collection()
        # Fetch documents + metadatas (not just IDs) so we can:
        #   1. Provide citations in the UI (the doc accumulator needs actual content)
        #   2. Still return an exact count (len of results)
        # Cost is negligible — count queries are scoped (meeting or project) and
        # metadata-only fetches have no embedding overhead.
        results = collection.get(
            where={"$and": and_clauses},
            include=["documents", "metadatas"],
        )
        count = len(results.get("ids", []))

        # Accumulate docs for the citations panel.
        # Sort chronologically so the UI shows sources in meeting order.
        raw_docs  = results.get("documents", [])
        raw_metas = results.get("metadatas", [])
        if raw_docs:
            docs = [
                Document(page_content=text, metadata=meta)
                for text, meta in zip(raw_docs, raw_metas)
            ]
            docs.sort(key=lambda d: (
                str(d.metadata.get("meeting_date", "")),
                d.metadata.get("start_time", 0) or 0,
            ))
            _append_docs(docs)

    except Exception as exc:
        logger.warning("count_signal_chunks error: %s", exc)
        return f"Count failed: {exc}"

    # Build a readable description of what was counted
    speaker_desc = f" by {resolved_speaker}" if resolved_speaker else ""

    if scope_ids:
        scope_desc = f" in {len(scope_ids)} meeting(s)"
    elif scope_type == "date_range":
        scope_desc = " (date-filtered)"
    else:
        scope_desc = " across all meetings"

    return (
        f"Detected count: {count} '{signal_filter}' chunks{speaker_desc}{scope_desc}.\n"
        f"(Signal detection is regex-based — this is a comprehensive estimate. "
        f"Use search_transcripts to explore specific instances.)"
    )


# ── Tool registry ─────────────────────────────────────────────────────────────
# graph.py imports this list to build ToolNode and bind tools to the LLM.

TOOLS = [
    search_transcripts,
    get_meeting_summaries,
    list_meetings,
    list_speakers,
    count_signal_chunks,
]
