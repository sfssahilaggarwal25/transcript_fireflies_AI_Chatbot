"""
tools.py — Agent tool definitions for the LangGraph pipeline.

Every tool reads project_id and scope from state via InjectedState.
The LLM never supplies these — they are enforced server-side.

Tools
-----
  search_transcripts    — Hybrid BM25 + dense search. The main workhorse.
  get_meeting_summaries — Fetch pre-built meeting summary paragraphs.
  list_meetings         — Meeting titles, dates, and numbers (no content).
  list_speakers         — Speaker names, roles, chunk counts (scope-aware).
  count_signal_chunks   — Exact metadata count for signal-flagged chunks.

Private implementation details (helpers, accumulator, signal maps) live in
utils/ — not imported from outside app/agent/.
"""

import logging
from typing import Annotated, Optional

from langchain_core.documents import Document
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from app.core.retrieval import hybrid_retrieve
from app.core.retrieval.reranker import rerank_documents
from app.core.storage.db import get_raw_collection
from .utils import (
    _SIGNAL_MAP,
    _HARD_SIGNAL_FILTERS,
    _SOFT_SIGNAL_FILTERS,
    _SOFT_SIGNAL_PREFIX,
    _ROLE_LABEL,
    _EXPAND_TOP_N,
    RETRIEVAL_PRESETS,
    select_preset,
    _append_docs,
    _fmt_ts,
    fmt_date,
    _resolve_speaker_name,
    _exhaustive_signal_search,
    _expand_short_chunks_for_reranking,
    _expand_context,
    _apply_diversity_cap,
    reset_doc_accumulator,
    get_accumulated_docs,
)

logger = logging.getLogger(__name__)


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
        Ignored — k is controlled automatically by the retrieval preset system.
        focused preset (single meeting) = 20, standard (default) = 40, broad (overview) = 55.
    speaker_name : str, optional
        Filter results to a specific speaker's contributions only. Use the full name
        as it appears in meeting records (e.g. 'Harsh Vardhan', 'Bhavneet Mahajan').
    signal_filter : str, optional
        Restrict results to chunks containing a specific signal type.
        One of: 'decision', 'commitment', 'question', 'open_issue', 'document_share'.
        If this filter returns 0 results, retry the call WITHOUT this filter.
    """
    if not query or not query.strip():
        return (
            "Error: 'query' cannot be empty. "
            "Provide 2–4 keywords describing what to search for "
            "(e.g. 'questions raised timeline', 'AI architecture decision'). "
            "signal_filter alone is not enough — query is always required."
        )

    project_id  = state["project_id"]
    scope_where = state.get("scope_where")
    scope_ids   = state.get("scope_ids")

    resolved_speaker = None
    if speaker_name:
        resolved_speaker = _resolve_speaker_name(speaker_name, project_id)
        if resolved_speaker and resolved_speaker != speaker_name:
            logger.info("search_transcripts | speaker resolved: %r → %r", speaker_name, resolved_speaker)
        elif not resolved_speaker:
            logger.warning("search_transcripts | speaker %r not found — searching without filter", speaker_name)

    # Exhaustive path: signal + scope → completeness beats ranking
    if signal_filter and signal_filter in _SIGNAL_MAP and scope_ids:
        return _exhaustive_signal_search(
            project_id=project_id,
            signal_filter=signal_filter,
            scope_ids=scope_ids,
            speaker_name=resolved_speaker,
        )

    filters: dict   = {}
    effective_query = query

    # Extract original user query early — used for both preset selection and reranking.
    # The LLM often strips intent words ("details", "all", "explain") when forming
    # the tool query. Using the original preserves those signals so the preset system
    # can correctly detect broad/overview intent.
    messages = state.get("messages", []) if state else []
    original_user_query = next(
        (m.content for m in reversed(messages) if isinstance(m, HumanMessage)),
        effective_query,  # fallback if no HumanMessage found
    )

    if resolved_speaker:
        filters["speaker_name"] = resolved_speaker

    if signal_filter and signal_filter in _SIGNAL_MAP:
        if signal_filter in _HARD_SIGNAL_FILTERS:
            filters[_SIGNAL_MAP[signal_filter]] = True
        elif signal_filter in _SOFT_SIGNAL_FILTERS:
            prefix = _SOFT_SIGNAL_PREFIX.get(signal_filter, "")
            if prefix:
                effective_query = f"{prefix} {query}"
                logger.info("search_transcripts | soft signal=%s → query rewritten: %r", signal_filter, effective_query)

    # Preset selection uses original_user_query so intent words stripped by the LLM
    # ("details", "explain", "all", "summarize") still trigger the broad preset.
    # Example: user says "give me the details about AI Architecture"
    #          LLM sends query="AI Architecture" — "detail" lost, standard preset fires
    #          With original query — "detail" detected, broad preset fires (k=55)
    preset_name          = select_preset(scope_ids, original_user_query)
    preset               = RETRIEVAL_PRESETS[preset_name]
    effective_k          = preset["k"]
    rerank_top_n         = preset["rerank_top_n"]
    diversity_cap_floor  = preset["diversity_cap_floor"]
    sort_by              = preset["sort_by"]
    logger.info(
        "search_transcripts | preset=%s | k=%d | rerank_top_n=%d | floor=%d | sort=%s | trigger=%r",
        preset_name, effective_k, rerank_top_n, diversity_cap_floor, sort_by, original_user_query[:60],
    )

    try:
        docs = hybrid_retrieve(
            query=effective_query,
            project_id=project_id,
            hard_filters=filters if filters else None,
            date_where=scope_where,
            k=effective_k,
            dense_query=original_user_query,
        )
    except Exception as exc:
        logger.warning("search_transcripts error: %s", exc)
        return f"Search failed: {exc}"

    if not docs:
        return "No relevant transcript chunks found for this query."

    # Diversity cap: prevent one meeting from filling all reranker slots.
    # Each meeting passes proportionally to how much of the pool it contributes,
    # with a floor of 3 and a ceiling that scales with total retrieved (k).
    # Bypassed for single-meeting scope (scope_ids set) — all chunks come from
    # one meeting by design, capping would cut relevant content.
    if not scope_ids and not resolved_speaker:
        logger.info("search_transcripts | applying diversity cap for project wide query")
        docs = _apply_diversity_cap(docs, floor=diversity_cap_floor)
        if not docs:
            return "No relevant transcript chunks found for this query."

    # Pre-rerank expansion: short fragments get their neighbors added to the
    # candidate pool so the reranker scores the full conversational unit.
    # See expansion.py → _expand_short_chunks_for_reranking for details.
    docs = _expand_short_chunks_for_reranking(docs)

    # Rerank: score all hybrid results by true relevance to the query, then
    # trim to preset rerank_top_n before passing anything to the LLM.
    #
    # Why here and not inside hybrid_retrieve:
    #   Reranking needs the full query intent — hybrid_retrieve only knows keywords.
    #   Doing it here lets us pass speaker_hint so the named speaker's chunks
    #   get a post-score boost even if they scored slightly lower on content alone.
    #
    # Two-stage expansion strategy:
    #   Stage 1 (above): short chunks get neighbors added BEFORE reranking so the
    #     reranker can score the full conversational unit, not a fragment.
    #   Stage 2 (_expand_context below): all direct_pass (score 7+) chunks get
    #     neighbors added AFTER reranking to give the LLM richer display context.
    #
    # The exhaustive signal path already returned above — no skip needed here.
    #
    # Query decoupling: retrieval uses effective_query (LLM-simplified keywords,
    # better for vector/BM25 matching). Reranker uses original_user_query
    # (full natural language, preserves intent for the LLM scorer).
    if original_user_query != effective_query:
        logger.info(
            "search_transcripts | rerank query decoupled | retrieval=%r | rerank=%r",
            effective_query, original_user_query,
        )

    docs = rerank_documents(
        query=original_user_query,  # full user intent → reranker understands scope
        documents=docs,
        topic_hint=effective_query, # clean keyword topic → modifier-aware rule fires correctly
        speaker_hint=resolved_speaker or "",
        top_n=rerank_top_n,
    )

    # Temporal sort: after reranking filters irrelevant chunks, re-sort by date so
    # the LLM sees chronological evolution rather than relevance-ranked order.
    # Only applies to temporal preset — other presets keep relevance order.
    if sort_by == "date" and docs:
        def _date_sort_key(doc):
            date = doc.metadata.get("meeting_date")
            ts   = doc.metadata.get("start_time", 0) or 0
            if not date:
                return (0, ts)
            if isinstance(date, (int, float)):
                # epoch milliseconds → convert to seconds for comparison
                return (int(date) // 1000, ts)
            # ISO string "YYYY-MM-DD" — convert to epoch seconds for uniform comparison
            try:
                from datetime import datetime
                return (int(datetime.fromisoformat(str(date)).timestamp()), ts)
            except Exception:
                return (0, ts)

        docs.sort(key=_date_sort_key)
        logger.info("search_transcripts | temporal sort applied — %d docs sorted by date", len(docs))

    # Expand context: inject prev/next neighbors for top-5 ranked chunks
    expanded      = _expand_context(docs, n=_EXPAND_TOP_N)
    anchor_docs   = [d for d in expanded if not d.metadata.get("_position")]
    chunk_numbers = _append_docs(anchor_docs)
    num_iter      = iter(chunk_numbers)

    lines: list[str] = [f"Found {len(anchor_docs)} relevant chunks:\n"]
    for doc in expanded:
        meta     = doc.metadata
        position = meta.get("_position")
        speaker  = meta.get("speaker_name", "Unknown")
        meeting  = meta.get("meeting_title", "Unknown Meeting")
        date     = meta.get("meeting_date", "")
        ts       = _fmt_ts(meta.get("start_time"))

        date_str = fmt_date(date)
        relevance     = meta.get("_relevance", "high")
        relevance_tag = " [LOW RELEVANCE — treat as background context only]" if relevance == "low" else ""

        if position == "before":
            lines.append(f"[CONTEXT ↑ before] {speaker} {ts} — {meeting} ({date_str})")
            lines.append(f"    {doc.page_content.strip()[:300]}")
        elif position == "after":
            lines.append(f"[CONTEXT ↓ after] {speaker} {ts} — {meeting} ({date_str})")
            lines.append(f"    {doc.page_content.strip()[:300]}")
        else:
            lines.append(f"[{next(num_iter)}] {speaker} {ts} — {meeting} ({date_str}){relevance_tag}")
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
        Partial or full meeting title to filter. Leave empty to get all summaries.
    """
    project_id = state["project_id"]
    scope_ids  = state.get("scope_ids")

    try:
        collection = get_raw_collection()
        results    = collection.get(
            where={"$and": [
                {"project_id":         {"$eq": project_id}},
                {"is_meeting_summary": {"$eq": True}},
            ]},
            include=["documents", "metadatas"],
        )
        raw_docs = results.get("documents", [])
        metas    = results.get("metadatas", [])
    except Exception as exc:
        logger.warning("get_meeting_summaries error: %s", exc)
        return f"Failed to fetch summaries: {exc}"

    if not raw_docs:
        return "No meeting summaries found for this project."

    docs = [Document(page_content=t, metadata=m) for t, m in zip(raw_docs, metas)]

    if scope_ids:
        docs = [d for d in docs if d.metadata.get("meeting_id") in scope_ids]
        if not docs:
            return "No summary found for the specified meeting(s)."

    if meeting_title:
        docs = [d for d in docs if meeting_title.lower() in d.metadata.get("meeting_title", "").lower()]
        if not docs:
            return f"No summary found matching '{meeting_title}'."

    sorted_docs   = sorted(docs, key=lambda d: str(d.metadata.get("meeting_date", "")))
    chunk_numbers = _append_docs(sorted_docs)

    lines: list[str] = [f"Found {len(sorted_docs)} meeting summary/summaries:\n"]
    for doc, num in zip(sorted_docs, chunk_numbers):
        meta = doc.metadata
        lines.append(f"[{num}] ## Meeting #{meta.get('meeting_number','')}: {meta.get('meeting_title','Unknown Meeting')}  ({fmt_date(meta.get('meeting_date',''))})")
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
        results = get_raw_collection().get(
            where={"project_id": {"$eq": project_id}},
            include=["metadatas"],
        )
        metas = results.get("metadatas", [])
    except Exception as exc:
        return f"Failed to list meetings: {exc}"

    seen: dict[str, dict] = {}
    for m in metas:
        mid = m.get("meeting_id")
        if mid and not m.get("is_meeting_summary") and mid not in seen:
            seen[mid] = {
                "title":  m.get("meeting_title", "Unknown"),
                "date":   m.get("meeting_date", ""),
                "number": m.get("meeting_number", "?"),
            }

    if not seen:
        return "No meetings found for this project."

    meetings = sorted(seen.values(), key=lambda x: fmt_date(x["date"]))
    lines = [f"{len(meetings)} meetings in this project:\n"]
    for m in meetings:
        lines.append(f"  Meeting #{m['number']}: {m['title']}  —  {fmt_date(m['date'])}")
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

    if scope_ids:
        meeting_clause = {"meeting_id": {"$eq": scope_ids[0]}} if len(scope_ids) == 1 else {"meeting_id": {"$in": scope_ids}}
        where = {"$and": [{"project_id": {"$eq": project_id}}, meeting_clause]}
    else:
        where = {"project_id": {"$eq": project_id}}

    try:
        metas = get_raw_collection().get(where=where, include=["metadatas"]).get("metadatas", [])
    except Exception as exc:
        return f"Failed to list speakers: {exc}"

    speakers: dict[str, dict] = {}
    for m in metas:
        name = m.get("speaker_name")
        if name and not m.get("is_meeting_summary"):
            if name not in speakers:
                speakers[name] = {"role": m.get("speaker_role", "unknown"), "count": 0}
            speakers[name]["count"] += 1

    if not speakers:
        return "No speakers found for this project."

    header = f"{len(speakers)} speakers (scoped to {len(scope_ids)} meeting(s)):\n" if scope_ids else f"{len(speakers)} speakers in this project:\n"
    lines  = [header]
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
    - "How many issues in the previous meeting?" → count_signal_chunks(signal_filter='open_issue')
    - "How many decisions were made in this project?" → count_signal_chunks(signal_filter='decision')
    - "How many documents were shared?" → count_signal_chunks(signal_filter='document_share')

    Signal Detection Note: counts are regex-based estimates. Say "about N" not "exactly N".
    For "how many X about [topic]", use search_transcripts(query=topic, signal_filter=signal) instead.

    Parameters
    ----------
    signal_filter : str
        Required. One of: 'decision', 'commitment', 'question', 'open_issue', 'document_share'.
    speaker_name : str, optional
        Restrict the count to one specific speaker.
    """
    if signal_filter not in _SIGNAL_MAP:
        return f"Unknown signal_filter '{signal_filter}'. Valid options: {list(_SIGNAL_MAP.keys())}"

    project_id  = state["project_id"]
    scope_ids   = state.get("scope_ids")
    scope_where = state.get("scope_where")
    scope_type  = state.get("scope_type", "project")

    resolved_speaker = _resolve_speaker_name(speaker_name, project_id) if speaker_name else None

    and_clauses = [
        {"project_id":               {"$eq": project_id}},
        {_SIGNAL_MAP[signal_filter]: {"$eq": True}},
        {"is_meeting_summary":       {"$ne": True}},
    ]
    if resolved_speaker:
        and_clauses.append({"speaker_name": {"$eq": resolved_speaker}})
    if scope_ids:
        and_clauses.append({"meeting_id": {"$eq": scope_ids[0]}} if len(scope_ids) == 1 else {"meeting_id": {"$in": scope_ids}})
    elif scope_type == "date_range" and scope_where:
        and_clauses.append(scope_where)

    try:
        results = get_raw_collection().get(
            where={"$and": and_clauses},
            include=["documents", "metadatas"],
        )
        count     = len(results.get("ids", []))
        raw_docs  = results.get("documents", [])
        raw_metas = results.get("metadatas", [])
        if raw_docs:
            docs = [Document(page_content=t, metadata=m) for t, m in zip(raw_docs, raw_metas)]
            docs.sort(key=lambda d: (str(d.metadata.get("meeting_date", "")), d.metadata.get("start_time", 0) or 0))
            _append_docs(docs)
    except Exception as exc:
        logger.warning("count_signal_chunks error: %s", exc)
        return f"Count failed: {exc}"

    speaker_desc = f" by {resolved_speaker}" if resolved_speaker else ""
    scope_desc   = f" in {len(scope_ids)} meeting(s)" if scope_ids else (" (date-filtered)" if scope_type == "date_range" else " across all meetings")

    return (
        f"Detected count: {count} '{signal_filter}' chunks{speaker_desc}{scope_desc}.\n"
        f"(Signal detection is regex-based — this is a comprehensive estimate. "
        f"Use search_transcripts to explore specific instances.)"
    )


# ── Tool registry ─────────────────────────────────────────────────────────────

TOOLS = [
    search_transcripts,
    get_meeting_summaries,
    list_meetings,
    list_speakers,
    count_signal_chunks,
]