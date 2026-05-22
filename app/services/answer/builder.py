import logging
from datetime import date
from typing import Optional
from langchain_core.documents import Document

from app.services.query_intent import QueryIntent
from app.services.prompts import ANSWER_PROMPT_TEMPLATES, _COUNT_PREFIX, _YESNO_PREFIX, _LIST_PREFIX, _TRACE_PREFIX, _MEETING_SCOPE_PREFIX
from app.services.storage.db import get_raw_collection
from app.services.answer.scope import extract_month_day, parse_meeting_scope, get_scoped_meeting_ids

logger = logging.getLogger(__name__)

EXPAND_TOP_N = 5


def format_timestamp(sec: int | float | None) -> str | None:
    """Format seconds-from-meeting-start to MM:SS (or H:MM:SS for long meetings).
    normalize.py stores start_time/end_time in seconds (converted from rawStartTimeMs).
    """
    if sec is None:
        return None
    total_seconds = int(sec)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def retrieve_summary_chunks(
    project_id: str,
    query: str = "",
    scope_meeting_ids: Optional[list[str]] = None,
) -> tuple[list[Document], str | None]:
    """
    Fetch summary chunks for the project chronologically.

    scope_meeting_ids: pre-resolved meeting IDs from QueryUnderstanding — when set,
      only those meetings' summary chunks are returned (no extra DB call needed).
      Falls back to extract_month_day() date matching when not provided.

    Returns (docs, notice) where notice is a UI-level string when something
    noteworthy happened (approximate date match, no date match).
    """
    try:
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

        docs = []
        for i in range(len(results.get("ids", []))):
            docs.append(Document(
                page_content=results["documents"][i],
                metadata=results["metadatas"][i],
            ))

        docs.sort(key=lambda d: d.metadata.get("meeting_date", ""))
        logger.info("  summary    : %d chunks found for project", len(docs))

        # Fast path: scope already resolved upstream — filter directly, no extra DB call
        if scope_meeting_ids:
            scoped_docs = [d for d in docs if d.metadata.get("meeting_id") in scope_meeting_ids]
            if scoped_docs:
                logger.info(
                    "  scope      : filtered to %d meeting(s) via scope_meeting_ids",
                    len(scoped_docs),
                )
                return scoped_docs, None

        # Fallback: extract month/day from query (e.g. "May 9th") when no pre-resolved scope
        month_day = extract_month_day(query)
        if month_day is None:
            return docs, None

        target_month, target_day = month_day
        logger.info("  date filter: query references month=%d day=%d", target_month, target_day)

        matched = []
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

    except Exception as e:
        logger.exception("Summary chunk retrieval failed: %s", e)
        return [], None


def expand_context(documents: list[Document], n: int = EXPAND_TOP_N) -> list[Document]:
    """
    For the top-n docs, fetch their prev/next neighbors from ChromaDB and
    inject them adjacent to their anchor doc. Max 2*n DB lookups (constant cost).

    Neighbors are tagged with _position='before'/'after' in metadata so
    build_context() can label them and extract_sources() can skip them.
    """
    if not documents:
        return documents

    collection = get_raw_collection()
    existing_ids: set[str] = {doc.metadata.get("chunk_id", "") for doc in documents}
    result: list[Document] = []

    for doc in documents[:n]:
        m = doc.metadata

        if m.get("is_meeting_summary"):
            result.append(doc)
            continue

        prev_id = m.get("prev_chunk_id")
        if prev_id and prev_id not in existing_ids:
            try:
                rows = collection.get(ids=[prev_id], include=["documents", "metadatas"])
                if rows.get("ids"):
                    result.append(Document(
                        page_content=rows["documents"][0],
                        metadata={**rows["metadatas"][0], "_position": "before"},
                    ))
                    existing_ids.add(prev_id)
            except Exception:
                pass

        result.append(doc)

        next_id = m.get("next_chunk_id")
        if next_id and next_id not in existing_ids:
            try:
                rows = collection.get(ids=[next_id], include=["documents", "metadatas"])
                if rows.get("ids"):
                    result.append(Document(
                        page_content=rows["documents"][0],
                        metadata={**rows["metadatas"][0], "_position": "after"},
                    ))
                    existing_ids.add(next_id)
            except Exception:
                pass

    for doc in documents[n:]:
        if doc.metadata.get("chunk_id", "") not in existing_ids:
            result.append(doc)
            existing_ids.add(doc.metadata.get("chunk_id", ""))

    return result


def build_context(documents: list[Document]) -> str:
    parts = []
    for i, doc in enumerate(documents, 1):
        meta = doc.metadata
        meeting = meta.get("meeting_title", "Unknown Meeting")
        date_str = meta.get("meeting_date", "")
        speaker = meta.get("speaker_name", "Unknown Speaker")
        role = meta.get("speaker_role", "")
        speaker_line = f"{speaker} ({role})" if role else speaker

        ts = format_timestamp(meta.get("start_time"))
        ts_str = f" [at {ts}]" if ts else ""

        position = meta.get("_position", "")
        if position == "before":
            label = f"[{i}] [CONTEXT — just before] Meeting: {meeting} ({date_str}){ts_str}\n"
        elif position == "after":
            label = f"[{i}] [CONTEXT — just after] Meeting: {meeting} ({date_str}){ts_str}\n"
        else:
            label = f"[{i}] Meeting: {meeting} ({date_str}){ts_str}\n"

        parts.append(label + f"Speaker: {speaker_line}\nContent: {doc.page_content}")
    return "\n\n".join(parts)


def build_prompt(
    query: str,
    context: str,
    intent: QueryIntent,
    output_format: str = "prose",
    scope_type: str = "project",
) -> str:
    template = ANSWER_PROMPT_TEMPLATES.get(intent.value, ANSWER_PROMPT_TEMPLATES["general_query"])
    prompt = template.format(query=query, context=context)

    # When the query targets ONE specific meeting, prevent the LLM from writing a
    # generic "project overview" by injecting a clear scope instruction at the top.
    # Applied only to summary_query — other templates are already scope-neutral.
    if scope_type == "meeting" and intent == QueryIntent.SUMMARY:
        prompt = _MEETING_SCOPE_PREFIX + prompt

    if output_format == "count":
        prompt = _COUNT_PREFIX + prompt
    elif output_format == "yesno":
        prompt = _YESNO_PREFIX + prompt
    elif output_format == "list":
        prompt = _LIST_PREFIX + prompt
    elif output_format == "prose_with_traces":
        prompt = _TRACE_PREFIX + prompt

    return prompt


def extract_sources(documents: list[Document]) -> list[dict]:
    seen: set[tuple] = set()
    sources = []

    for doc in documents:
        meta = doc.metadata

        # Skip neighbor chunks injected by expand_context — not primary sources
        if meta.get("_position"):
            continue

        is_summary = meta.get("is_meeting_summary", False)

        meeting_title = meta.get("meeting_title", "Unknown Meeting")
        meeting_date  = meta.get("meeting_date", "")
        speaker_name  = "Meeting Summary" if is_summary else meta.get("speaker_name", "")
        content       = doc.page_content

        key = (meeting_title, meeting_date, speaker_name)
        if key not in seen:
            seen.add(key)
            ts = format_timestamp(meta.get("start_time"))
            sources.append({
                "meeting_title":   meeting_title,
                "meeting_date":    meeting_date,
                "speaker_name":    speaker_name,
                "timestamp":       ts,
                "content_preview": content[:200].strip(),
                "is_summary":      is_summary,
            })

    return sources


def build_not_found_message(intent: QueryIntent, query: str, project_id: str) -> str:
    """
    Return a helpful "not found" message.
    For SUMMARY queries with a date reference, lists the actual meeting dates
    so the PM knows what dates are available instead of getting a generic error.
    """
    if intent == QueryIntent.SUMMARY and extract_month_day(query):
        try:
            collection = get_raw_collection()
            results = collection.get(
                where={
                    "$and": [
                        {"project_id": {"$eq": project_id}},
                        {"is_meeting_summary": {"$eq": True}},
                    ]
                },
                include=["metadatas"],
            )
            meetings = sorted(
                {
                    f"{m.get('meeting_date')} — {m.get('meeting_title')}"
                    for m in results.get("metadatas", [])
                    if m.get("meeting_date")
                }
            )
            if meetings:
                meeting_list = "\n".join(f"  • {m}" for m in meetings)
                return (
                    f"No meeting was found on the date you mentioned.\n\n"
                    f"Meetings available in this project:\n{meeting_list}\n\n"
                    f"Try asking about one of these dates."
                )
        except Exception:
            pass

    return (
        "I couldn't find relevant information in the meeting transcripts for this project. "
        "Make sure the project has been ingested and that the project_id is correct."
    )
