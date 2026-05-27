import logging
import re
from datetime import date
from typing import Optional
from langchain_core.documents import Document

from app.rag.prompts import (
    ANSWER_PROMPT_TEMPLATES,
    _COUNT_PREFIX, _YESNO_PREFIX, _LIST_PREFIX, _TRACE_PREFIX, _MEETING_SCOPE_PREFIX,
)
from app.core.storage.db import get_raw_collection
from app.core.scope import extract_month_day

logger = logging.getLogger(__name__)

EXPAND_TOP_N = 5

# Output-format prefix lookup — avoids if/elif chain in build_prompt
_FORMAT_PREFIXES: dict[str, str] = {
    "count":             _COUNT_PREFIX,
    "yesno":             _YESNO_PREFIX,
    "list":              _LIST_PREFIX,
    "prose_with_traces": _TRACE_PREFIX,
}


# ──────────────────────────────────────────────────────────────────────────────
# Timestamp helper
# ──────────────────────────────────────────────────────────────────────────────

def format_timestamp(sec: int | float | None) -> str | None:
    """Format seconds-from-meeting-start → MM:SS, or H:MM:SS for long meetings."""
    if sec is None:
        return None
    total_seconds = int(sec)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


# ──────────────────────────────────────────────────────────────────────────────
# Summary chunk retrieval — private helpers
# ──────────────────────────────────────────────────────────────────────────────

def _fetch_all_summary_docs(project_id: str) -> list[Document]:
    """
    Query ChromaDB for every summary chunk in this project.
    Returns docs sorted chronologically (oldest first).
    Logs the full meeting list for pipeline traceability.
    """
    collection = get_raw_collection()
    results = collection.get(
        where={
            "$and": [
                {"project_id": {"$eq": project_id}},
                {"is_meeting_summary": {"$eq": True}},
            ]
        },
        include=["documents", "metadatas"],
    )

    docs = [
        Document(
            page_content=results["documents"][i],
            metadata=results["metadatas"][i],
        )
        for i in range(len(results.get("ids", [])))
    ]
    docs.sort(key=lambda d: d.metadata.get("meeting_date", ""))

    meeting_index = {
        d.metadata.get("meeting_id"): (
            d.metadata.get("meeting_title", "?"),
            d.metadata.get("meeting_date", "?"),
        )
        for d in docs
    }
    logger.info(
        "  [summary] %d summary chunks in project | meetings: %s",
        len(docs),
        " | ".join(
            f"{title!r} ({dt}) [{mid}]"
            for mid, (title, dt) in sorted(meeting_index.items(), key=lambda x: x[1][1])
        ) or "none",
    )
    return docs


def _filter_by_scope_ids(
    docs: list[Document],
    scope_meeting_ids: list[str],
) -> tuple[list[Document], str | None] | None:
    """
    Filter docs to the pre-resolved meeting IDs (fastest path — no extra DB call).

    Returns (filtered_docs, notice) when at least one doc matched.
    Returns None to signal fall-through to the date-regex fallback.
    """
    logger.info(
        "  [summary] scope_meeting_ids requested: [%s]",
        ", ".join(scope_meeting_ids),
    )

    scoped = [d for d in docs if d.metadata.get("meeting_id") in scope_meeting_ids]
    missed = set(scope_meeting_ids) - {d.metadata.get("meeting_id") for d in scoped}

    if missed:
        logger.warning(
            "  [summary] SCOPE MISS — requested IDs not in summary chunks: %s",
            ", ".join(missed),
        )

    if scoped:
        logger.info(
            "  [summary] filtered to %d doc(s): %s",
            len(scoped),
            " | ".join(
                f"{d.metadata.get('meeting_title')!r} ({d.metadata.get('meeting_date')})"
                for d in scoped
            ),
        )
        return scoped, None

    logger.warning(
        "  [summary] scope_meeting_ids matched 0 summary chunks — falling through to date-regex",
    )
    return None  # signal: try next fallback


def _filter_by_date_ref(
    docs: list[Document],
    query: str,
) -> tuple[list[Document], str | None]:
    """
    Fallback: extract a month/day reference from the query (e.g. "May 9th")
    and fuzzy-match it against meeting dates with ±1 day tolerance.

    Returns (all_docs, None) when no date reference found in query.
    Returns (matched_docs, notice) otherwise — notice is set if the match was approximate.
    Returns ([], None) when a date was found but nothing matched.
    """
    month_day = extract_month_day(query)
    if month_day is None:
        return docs, None   # no date reference → caller gets all summary docs

    target_month, target_day = month_day
    logger.info("  date filter: query references month=%d day=%d", target_month, target_day)

    matched: list[Document] = []
    match_delta = 0

    for doc in docs:
        raw = doc.metadata.get("meeting_date", "")
        try:
            meeting_date = date.fromisoformat(raw)
            delta = abs(
                (date(meeting_date.year, target_month, target_day) - meeting_date).days
            )
            if delta <= 1:
                matched.append(doc)
                match_delta = delta
                logger.info(
                    "  date match : %s (%s) — delta=%d day(s)",
                    doc.metadata.get("meeting_title", "?"), raw, delta,
                )
        except ValueError:
            continue

    if not matched:
        available = [
            f"{d.metadata.get('meeting_date')} ({d.metadata.get('meeting_title')})"
            for d in docs
        ]
        logger.info("  date filter: no match — available: %s", available)
        return [], None

    notice = None
    if match_delta > 0:
        m = matched[0].metadata
        notice = (
            f"No meeting found on {target_day:02d}/{target_month:02d}. "
            f"Showing the closest meeting: **{m.get('meeting_title')}** "
            f"({m.get('meeting_date')})."
        )
        logger.info("  notice     : approximate match — %s", notice)

    return matched, notice


# ──────────────────────────────────────────────────────────────────────────────
# Summary chunk retrieval — public
# ──────────────────────────────────────────────────────────────────────────────

def retrieve_summary_chunks(
    project_id: str,
    query: str = "",
    scope_meeting_ids: Optional[list[str]] = None,
) -> tuple[list[Document], str | None]:
    """
    Fetch summary chunks for the project, applying scope or date filters.

    Resolution priority:
      1. scope_meeting_ids — pre-resolved upstream, fastest (no extra DB call)
      2. Date reference in query text (e.g. "May 9th") — fuzzy ±1 day match
      3. All summary docs when no scope or date reference exists

    Returns (docs, notice) where notice is a UI string for approximate date matches.
    """
    try:
        docs = _fetch_all_summary_docs(project_id)

        if scope_meeting_ids:
            result = _filter_by_scope_ids(docs, scope_meeting_ids)
            if result is not None:
                return result
            # Scope matched 0 chunks — fall through to date-regex

        return _filter_by_date_ref(docs, query)

    except Exception as e:
        logger.exception("Summary chunk retrieval failed: %s", e)
        return [], None


# ──────────────────────────────────────────────────────────────────────────────
# Context expansion — private helper
# ──────────────────────────────────────────────────────────────────────────────

def _fetch_neighbor(collection, chunk_id: str, position: str) -> Document | None:
    """
    Fetch one neighbor chunk from ChromaDB by ID.
    position: "before" or "after" — stored in _position metadata so the
    caller can label and exclude it from source attribution.
    Returns None if the chunk is missing or the DB call fails.
    """
    try:
        rows = collection.get(ids=[chunk_id], include=["documents", "metadatas"])
        if rows.get("ids"):
            return Document(
                page_content=rows["documents"][0],
                metadata={**rows["metadatas"][0], "_position": position},
            )
    except Exception:
        pass
    return None


# ──────────────────────────────────────────────────────────────────────────────
# Context expansion — public
# ──────────────────────────────────────────────────────────────────────────────

def expand_context(documents: list[Document], n: int = EXPAND_TOP_N) -> list[Document]:
    """
    Fetch prev/next neighbor chunks for the top-n re-ranked docs and inject
    them adjacent to their anchor. At most 2*n ChromaDB lookups (constant cost).

    Neighbors carry _position='before'/'after' so build_context() labels them
    and extract_sources() skips them from source attribution.
    """
    if not documents:
        return documents

    collection   = get_raw_collection()
    existing_ids: set[str] = {doc.metadata.get("chunk_id", "") for doc in documents}
    result:       list[Document] = []

    for doc in documents[:n]:
        m = doc.metadata

        # Summary chunks have no adjacency links — inject directly
        if m.get("is_meeting_summary"):
            result.append(doc)
            continue

        prev_id = m.get("prev_chunk_id")
        if prev_id and prev_id not in existing_ids:
            neighbor = _fetch_neighbor(collection, prev_id, "before")
            if neighbor:
                result.append(neighbor)
                existing_ids.add(prev_id)

        result.append(doc)

        next_id = m.get("next_chunk_id")
        if next_id and next_id not in existing_ids:
            neighbor = _fetch_neighbor(collection, next_id, "after")
            if neighbor:
                result.append(neighbor)
                existing_ids.add(next_id)

    # Remaining docs (beyond top-n) are appended without neighbor expansion
    for doc in documents[n:]:
        if doc.metadata.get("chunk_id", "") not in existing_ids:
            result.append(doc)
            existing_ids.add(doc.metadata.get("chunk_id", ""))

    return result


# ──────────────────────────────────────────────────────────────────────────────
# Prompt building — private helper
# ──────────────────────────────────────────────────────────────────────────────

def _make_chunk_label(i: int, meta: dict) -> str:
    """
    Build the numbered header line for one chunk in the context string.
    Neighbor chunks get a [CONTEXT — just before/after] marker.
    Timestamp is kept on the header line for meeting/date context.
    """
    meeting  = meta.get("meeting_title", "Unknown Meeting")
    date_str = meta.get("meeting_date", "")

    position = meta.get("_position", "")
    if position == "before":
        return f"[{i}] [CONTEXT — just before] Meeting: {meeting} ({date_str})\n"
    if position == "after":
        return f"[{i}] [CONTEXT — just after] Meeting: {meeting} ({date_str})\n"
    return f"[{i}] Meeting: {meeting} ({date_str})\n"


# ──────────────────────────────────────────────────────────────────────────────
# Prompt building — public
# ──────────────────────────────────────────────────────────────────────────────

def build_context(documents: list[Document]) -> str:
    """
    Serialise a list of Documents into a numbered context string for the LLM.

    Timestamp is placed on the Speaker line (not the header) so the LLM naturally
    associates it with the speaker rather than the meeting date.
    Format: Speaker: Rhythm jalhotra (developer) [02:51]
    """
    parts = []
    for i, doc in enumerate(documents, 1):
        meta         = doc.metadata
        speaker      = meta.get("speaker_name", "Unknown Speaker")
        role         = meta.get("speaker_role", "")
        ts           = format_timestamp(meta.get("start_time"))
        ts_str       = f" [{ts}]" if ts else ""
        # role + timestamp on the same Speaker line: "Rhythm jalhotra (developer) [02:51]"
        if role:
            speaker_line = f"{speaker} ({role}){ts_str}"
        else:
            speaker_line = f"{speaker}{ts_str}"
        label        = _make_chunk_label(i, meta)
        parts.append(label + f"Speaker: {speaker_line}\nContent: {doc.page_content}")
    return "\n\n".join(parts)


def build_prompt(
    query: str,
    context: str,
    template_key: str,
    output_format: str = "prose",
    scope_type: str = "project",
) -> str:
    """
    Select the answer template by template_key, inject context and query,
    then prepend the appropriate scope and output-format prefix.
    """
    template = ANSWER_PROMPT_TEMPLATES.get(template_key, ANSWER_PROMPT_TEMPLATES["general_query"])
    prompt   = template.format(query=query, context=context)

    # Single-meeting queries: stop the LLM writing a generic project-wide overview.
    # Only needed for summary_query — other templates are already scope-neutral.
    if scope_type == "meeting" and template_key == "summary_query":
        prompt = _MEETING_SCOPE_PREFIX + prompt

    prefix = _FORMAT_PREFIXES.get(output_format)
    if prefix:
        prompt = prefix + prompt

    return prompt


# ──────────────────────────────────────────────────────────────────────────────
# Source extraction
# ──────────────────────────────────────────────────────────────────────────────

def extract_sources(documents: list[Document], answer: str = "") -> list[dict]:
    """
    Build the sources list returned alongside every answer.

    Each primary (non-neighbor) chunk becomes its own source entry tagged with
    chunk_num — the same [n] number the LLM sees in build_context(). This keeps
    citation numbers and source card numbers in sync so _linkify_citations() in
    the UI can turn every [n] into a clickable anchor link.

    Neighbor chunks (_position set) are normally skipped, BUT if the LLM
    actually cited one (i.e., its [n] appears in the answer text), it is
    included as a source. This handles cases where a neighbor chunk contains a
    real question or statement the LLM correctly identified and cited, even
    though it was not a primary retrieval hit (e.g. a speaker whose chunk wasn't
    tagged with the right signal but was picked up as context).
    """
    # Parse chunk numbers the LLM actually cited, e.g. [3], [6, 7], [10]
    cited_nums: set[int] = set(
        int(m.group(1))
        for m in re.finditer(r'\[(\d{1,3})\](?!:)', answer)
    ) if answer else set()

    sources: list[dict] = []

    for i, doc in enumerate(documents, 1):   # same enumeration as build_context()
        meta       = doc.metadata
        is_neighbor = bool(meta.get("_position"))

        # Skip neighbors the LLM never cited — they are pure context padding
        if is_neighbor and i not in cited_nums:
            continue

        is_summary    = meta.get("is_meeting_summary", False)
        meeting_title = meta.get("meeting_title", "Unknown Meeting")
        meeting_date  = meta.get("meeting_date", "")
        speaker_name  = "Meeting Summary" if is_summary else meta.get("speaker_name", "")

        sources.append({
            "chunk_num":       i,            # matches the [n] label the LLM used
            "meeting_title":   meeting_title,
            "meeting_date":    meeting_date,
            "speaker_name":    speaker_name,
            "timestamp":       format_timestamp(meta.get("start_time")),
            "content_preview": doc.page_content[:200].strip(),
            "is_summary":      is_summary,
        })

    return sources


# ──────────────────────────────────────────────────────────────────────────────
# Not-found message — private helper
# ──────────────────────────────────────────────────────────────────────────────

def _list_available_meetings(project_id: str) -> list[str]:
    """
    Return sorted 'YYYY-MM-DD — Meeting Title' strings for all ingested meetings.
    Used to give the PM actionable options when their requested date had no match.
    """
    try:
        collection = get_raw_collection()
        results    = collection.get(
            where={
                "$and": [
                    {"project_id": {"$eq": project_id}},
                    {"is_meeting_summary": {"$eq": True}},
                ]
            },
            include=["metadatas"],
        )
        return sorted(
            {
                f"{m.get('meeting_date')} — {m.get('meeting_title')}"
                for m in results.get("metadatas", [])
                if m.get("meeting_date")
            }
        )
    except Exception:
        return []


# ──────────────────────────────────────────────────────────────────────────────
# Not-found message — public
# ──────────────────────────────────────────────────────────────────────────────

def build_not_found_message(template_key: str, query: str, project_id: str) -> str:
    """
    Return a helpful "not found" message.
    For summary queries with a date reference, lists the available meeting dates
    so the PM knows what to ask about instead of seeing a generic error.
    """
    if template_key == "summary_query" and extract_month_day(query):
        meetings = _list_available_meetings(project_id)
        if meetings:
            meeting_list = "\n".join(f"  • {m}" for m in meetings)
            return (
                f"No meeting was found on the date you mentioned.\n\n"
                f"Meetings available in this project:\n{meeting_list}\n\n"
                f"Try asking about one of these dates."
            )

    return (
        "I couldn't find relevant information in the meeting transcripts for this project. "
        "Make sure the project has been ingested and that the project_id is correct."
    )
