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

from app.services.retrieval import hybrid_retrieve
from app.services.storage.db import get_raw_collection

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
# Uses in-place list mutations (.clear() / .extend()) so ToolNode's threads
# all see the same list object. Do NOT reassign with = [] — that breaks it.

_accumulated_docs: list[Document] = []


def reset_doc_accumulator() -> None:
    """Clear the doc list before each new query. Called by service.py."""
    _accumulated_docs.clear()


def get_accumulated_docs() -> list[Document]:
    """Return a copy of docs collected across all tool calls this request."""
    return list(_accumulated_docs)


def _append_docs(docs: list[Document]) -> None:
    _accumulated_docs.extend(docs)


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
    project_id    = state["project_id"]
    scope_where   = state.get("scope_where")
    recommended_k = state.get("recommended_k", 15)

    # Use the larger of: what the LLM asked for, or what the scope recommends.
    # Never exceed 25. This prevents under-fetching on project-wide queries.
    effective_k = min(max(int(k), recommended_k), 25)

    # Build metadata filters for the retrieval call
    filters: dict = {}
    if speaker_name:
        filters["speaker_name"] = speaker_name

    if signal_filter and signal_filter in _SIGNAL_MAP:
        filters[_SIGNAL_MAP[signal_filter]] = True

    try:
        docs = hybrid_retrieve(
            query=query,
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

    _append_docs(docs)

    # Format results for the LLM to read
    lines: list[str] = [f"Found {len(docs)} relevant chunks:\n"]
    for i, doc in enumerate(docs, 1):
        meta    = doc.metadata
        speaker = meta.get("speaker_name", "Unknown")
        meeting = meta.get("meeting_title", "Unknown Meeting")
        date    = meta.get("meeting_date", "")
        ts      = _fmt_ts(meta.get("start_time"))

        lines.append(f"[{i}] {speaker} {ts} — {meeting} ({date})")
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

    _append_docs(docs)

    # Sort by date and format output
    lines: list[str] = [f"Found {len(docs)} meeting summary/summaries:\n"]
    for doc in sorted(docs, key=lambda d: d.metadata.get("meeting_date", "")):
        title = doc.metadata.get("meeting_title", "Unknown Meeting")
        date  = doc.metadata.get("meeting_date", "")
        num   = doc.metadata.get("meeting_number", "")
        lines.append(f"## Meeting #{num}: {title}  ({date})")
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

    # Build filter clauses — always include project + signal + exclude summaries
    and_clauses = [
        {"project_id":          {"$eq": project_id}},
        {_SIGNAL_MAP[signal_filter]: {"$eq": True}},
        {"is_meeting_summary":  {"$ne": True}},   # $ne catches False AND missing
    ]

    if speaker_name:
        and_clauses.append({"speaker_name": {"$eq": speaker_name}})

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
        results    = collection.get(
            where={"$and": and_clauses},
            include=[],   # IDs are always returned; [] skips content + metadatas
        )
        count = len(results.get("ids", []))
    except Exception as exc:
        logger.warning("count_signal_chunks error: %s", exc)
        return f"Count failed: {exc}"

    # Build a readable description of what was counted
    speaker_desc = f" by {speaker_name}" if speaker_name else ""

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
