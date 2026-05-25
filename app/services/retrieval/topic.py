"""
topic.py — Per-meeting search functions.

Both functions run independent searches per meeting and merge chronologically.
Per-meeting search ensures every meeting contributes equally — a project-wide
search would skew toward the meeting with the most topic-relevant chunks.

topic_summary_retrieve       — deep-dive on one topic across meetings
retrieve_timeline_documents  — cross-meeting evolution / attribution queries
"""
import logging
from typing import Optional

from langchain_core.documents import Document

from app.services.storage.project_store import get_meeting_ids_for_project
from .hybrid import hybrid_retrieve, retrieve_documents

logger = logging.getLogger(__name__)


def topic_summary_retrieve(
    topic: str,
    project_id: str,
    scope_meeting_ids: Optional[list[str]] = None,
    k_per_meeting: int = 8,
) -> list[Document]:
    """
    Deep-dive retrieval for a specific topic.

    Runs hybrid_retrieve(k=k_per_meeting) per meeting, then merges chronologically.
    scope_meeting_ids: pre-resolved IDs from QueryUnderstanding — when set, only
      those meetings are searched (no extra DB call needed).
    k_per_meeting: from get_retrieval_config() — scales inversely with meeting count.
    """
    all_meetings = get_meeting_ids_for_project(project_id)
    if not all_meetings:
        return hybrid_retrieve(topic, project_id, k=k_per_meeting * 3)

    meetings_to_search = (
        [mid for mid in all_meetings if mid in scope_meeting_ids]
        if scope_meeting_ids else all_meetings
    )
    if not meetings_to_search:
        logger.warning("  topic_sum  : no meetings in scope — falling back to all")
        meetings_to_search = all_meetings

    all_docs: list[Document] = []
    for mid in meetings_to_search:
        try:
            docs = hybrid_retrieve(
                topic, project_id,
                hard_filters={"meeting_id": mid},
                k=k_per_meeting,
            )
            all_docs.extend(docs)
        except Exception as e:
            logger.warning("topic_summary_retrieve skipped meeting=%s: %s", mid, e)

    all_docs.sort(key=lambda d: (
        d.metadata.get("meeting_date", ""),
        d.metadata.get("start_time") or 0,
    ))
    logger.info(
        "  topic_sum  : %d docs | topic=%r | %d/%d meetings",
        len(all_docs), topic, len(meetings_to_search), len(all_meetings),
    )
    return all_docs


def retrieve_timeline_documents(
    query: str,
    project_id: str,
    k_per_meeting: int = 6,
    scope_meeting_ids: Optional[list[str]] = None,
) -> list[Document]:
    """
    Cross-meeting timeline / evolution / attribution retrieval.

    Runs dense-only search per meeting (no BM25 — timeline queries are
    semantically complex and BM25 misses paraphrased mentions).
    Merges sorted by meeting_date ascending for chronological narrative.
    k_per_meeting: from get_retrieval_config() — scales with scope size.
    """
    all_meetings = get_meeting_ids_for_project(project_id)
    if not all_meetings:
        logger.warning("No meetings found for project_id=%s", project_id)
        return retrieve_documents(query, project_id, k=k_per_meeting * 2)

    if scope_meeting_ids:
        meeting_ids = [mid for mid in all_meetings if mid in scope_meeting_ids]
        if not meeting_ids:
            logger.warning("  timeline   : scope not in project — falling back to all")
            meeting_ids = all_meetings
        else:
            logger.info("  timeline   : scoped to %d/%d meeting(s)", len(meeting_ids), len(all_meetings))
    else:
        meeting_ids = all_meetings

    all_docs: list[Document] = []
    for mid in meeting_ids:
        try:
            docs = retrieve_documents(
                query, project_id,
                filters={"meeting_id": mid},
                k=k_per_meeting,
            )
            all_docs.extend(docs)
            logger.debug("  timeline   : %d docs from meeting=%s", len(docs), mid)
        except Exception as e:
            logger.warning("retrieve_timeline_documents skipped meeting=%s: %s", mid, e)

    all_docs.sort(key=lambda d: d.metadata.get("meeting_date", ""))
    return all_docs
