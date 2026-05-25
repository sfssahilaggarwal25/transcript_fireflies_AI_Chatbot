"""
tools.py — Production tool definitions for the LangGraph agent.

Every tool enforces project_id via InjectedState — the LLM never supplies it.
The LLM only provides the search/filter parameters shown in each tool's schema.

Tools:
  search_transcripts     — BM25 + dense hybrid search (main workhorse)
  get_meeting_summaries  — fetch high-level meeting summaries
  list_meetings          — metadata: titles, dates, meeting numbers
  list_speakers          — metadata: all participants + their roles

Thread-safe doc accumulator:
  reset_doc_accumulator()  — call at start of each answer_query() request
  get_accumulated_docs()   — call after graph.invoke() to build sources
"""

import logging
from typing import Annotated, Optional

from langchain_core.documents import Document
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from app.services.retrieval import hybrid_retrieve
from app.services.storage.db import get_raw_collection

logger = logging.getLogger(__name__)

# ── Per-request doc accumulator ───────────────────────────────────────────────
# Uses a module-level mutable list (NOT reassignment) so ToolNode's thread pool
# sees the same list object that service.py reads after invoke().
#
# ContextVar is NOT used here because ToolNode copies the context into each
# worker thread — _docs_ctx.set() in the tool would only update the thread's
# copy, leaving the main context unchanged. In-place .clear()/.extend() on a
# shared list object ARE visible across all thread references.
#
# Concurrency note: safe for single-user Streamlit demos. For multi-user
# production, wrap with threading.Lock() or use a per-request-id dict.

_accumulated_docs: list[Document] = []


def reset_doc_accumulator() -> None:
    """Call at the start of every answer_query() to clear the previous run."""
    _accumulated_docs.clear()


def get_accumulated_docs() -> list[Document]:
    return list(_accumulated_docs)


def _append_docs(docs: list[Document]) -> None:
    _accumulated_docs.extend(docs)


# ── Timestamp helper ──────────────────────────────────────────────────────────

def _fmt_ts(sec: int | float | None) -> str:
    if sec is None:
        return ""
    total = int(sec)
    h, rem = divmod(total, 3600)
    m, s   = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
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

    Use this tool for any question about:
    - What was said, discussed, or explained in meetings
    - Specific topics, technical decisions, features, or blockers
    - Speaker contributions (use speaker_name to scope)
    - Decisions made (signal_filter='decision')
    - Action items / commitments (signal_filter='commitment')
    - Questions that were raised (signal_filter='question')

    Parameters
    ----------
    query : str
        Natural language search query. Be specific — 'ONCA forecasting decision' is
        better than 'what was decided'.
    k : int, optional
        Number of chunks to retrieve (default 15, max 25).
    speaker_name : str, optional
        Filter results to a specific speaker's contributions.
    signal_filter : str, optional
        One of: 'decision', 'commitment', 'question', 'open_issue'.
        Restricts results to chunks containing that signal type.
    """
    project_id = state["project_id"]
    scope_where = state.get("scope_where")   # ← None if no scope matched
    k = min(int(k), 25)

    # Build metadata filters
    filters: dict = {}
    if speaker_name:
        filters["speaker_name"] = speaker_name

    _SIGNAL_MAP = {
        "decision":    "contains_decision",
        "commitment":  "contains_commitment",
        "question":    "contains_question",
        "open_issue":  "contains_open_issue",
    }
    if signal_filter and signal_filter in _SIGNAL_MAP:
        filters[_SIGNAL_MAP[signal_filter]] = True

    try:
        docs = hybrid_retrieve(
            query=query,
            project_id=project_id,
            hard_filters=filters if filters else None,
            date_where=scope_where,   # ← NOW PASSED — physically scopes to matched meeting(s
            k=k,
        )
    except Exception as exc:
        logger.warning("search_transcripts error: %s", exc)
        return f"Search failed: {exc}"

    if not docs:
        return "No relevant transcript chunks found for this query."

    # Accumulate for source tracking
    _append_docs(docs)

    # Format for LLM consumption
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
    - The agenda or themes of a meeting

    Parameters
    ----------
    meeting_title : str, optional
        Partial or full meeting title to filter. Leave empty to get all summaries.
    """
    project_id = state["project_id"]
    scope_ids  = state.get("scope_ids")    # flat list of meeting IDs, or None

    try:
        collection  = get_raw_collection()
        where_filter = {
            "$and": [
                {"project_id":         {"$eq": project_id}},
                {"is_meeting_summary": {"$eq": True}},
            ]
        }
        results  = collection.get(where=where_filter, include=["documents", "metadatas"])
        raw_docs = results.get("documents", [])
        metas    = results.get("metadatas", [])
    except Exception as exc:
        logger.warning("get_meeting_summaries error: %s", exc)
        return f"Failed to fetch summaries: {exc}"

    if not raw_docs:
        return "No meeting summaries found for this project."

    # Build LangChain Documents for accumulator
    lc_docs = [
        Document(page_content=text, metadata=meta)
        for text, meta in zip(raw_docs, metas)
    ]

    # Apply meeting scope if query_scope_node resolved specific meeting IDs
    if scope_ids:
        lc_docs = [
            d for d in lc_docs
            if d.metadata.get("meeting_id") in scope_ids
        ]
        if not lc_docs:
            return "No summary found for the specified meeting(s)."

    # Optionally filter further by title (LLM-supplied)
    if meeting_title:
        lc_docs = [
            d for d in lc_docs
            if meeting_title.lower() in d.metadata.get("meeting_title", "").lower()
        ]
        if not lc_docs:
            return f"No summary found matching '{meeting_title}'."

    _append_docs(lc_docs)

    # Format for LLM
    lines: list[str] = [f"Found {len(lc_docs)} meeting summary/summaries:\n"]
    for doc in sorted(lc_docs, key=lambda d: d.metadata.get("meeting_date", "")):
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
    for i, m in enumerate(meetings, 1):
        lines.append(f"  {i}. Meeting #{m['number']}: {m['title']}  —  {m['date']}")

    return "\n".join(lines)


# ── Tool 4: list_speakers ─────────────────────────────────────────────────────

@tool
def list_speakers(
    state: Annotated[dict, InjectedState] = None,
) -> str:
    """List all speakers in this project with their roles.

    Use this tool when asked:
    - Who attended the meetings?
    - Who is the client / project manager / developer?
    - List all participants
    - Who is on the team?
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
        return f"Failed to list speakers: {exc}"

    speakers: dict[str, str] = {}
    for m in metas:
        name = m.get("speaker_name")
        if name and not m.get("is_meeting_summary"):
            if name not in speakers:
                speakers[name] = m.get("speaker_role", "unknown")

    if not speakers:
        return "No speakers found for this project."

    _ROLE_LABEL = {
        "client":          "Client",
        "project_manager": "Project Manager",
        "developer":       "Developer",
    }
    lines = [f"{len(speakers)} speakers in this project:\n"]
    for name, role in sorted(speakers.items()):
        label = _ROLE_LABEL.get(role, role.replace("_", " ").title())
        lines.append(f"  - {name}  [{label}]")

    return "\n".join(lines)


# ── Tool registry (for graph.py) ──────────────────────────────────────────────

TOOLS = [
    search_transcripts,
    get_meeting_summaries,
    list_meetings,
    list_speakers,
]
