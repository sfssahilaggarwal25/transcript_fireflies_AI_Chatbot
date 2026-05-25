"""
base.py — Shared retrieval utilities.

Validation helpers, ChromaDB filter builder, corpus fetch, debug logging.
Used by hybrid.py, structured.py, and topic.py — not imported externally.
"""
import logging
from typing import Optional

from langchain_core.documents import Document

from app.services.storage.db import get_raw_collection

logger = logging.getLogger(__name__)

DEFAULT_TOP_K = 8
MAX_TOP_K = 25

_DIV = "=" * 64
_SEP = "-" * 64


# ── Input validation ──────────────────────────────────────────────────────────

def _validate_query(query: str) -> str:
    if not query:
        raise ValueError("Query cannot be empty.")
    cleaned = query.strip()
    if not cleaned:
        raise ValueError("Query cannot be blank.")
    return cleaned


def _validate_project_id(project_id: str) -> str:
    if not project_id:
        raise ValueError("project_id is required.")
    cleaned = project_id.strip()
    if not cleaned:
        raise ValueError("project_id cannot be blank.")
    return cleaned


def _validate_top_k(k: int) -> int:
    """Cap k at MAX_TOP_K (used by legacy retrieve_documents only)."""
    if k <= 0:
        return DEFAULT_TOP_K
    if k > MAX_TOP_K:
        logger.warning("Requested top_k=%s exceeds max. Capping to %s.", k, MAX_TOP_K)
        return MAX_TOP_K
    return k


# ── ChromaDB filter builder ───────────────────────────────────────────────────

def _build_filter(
    project_id: str,
    filters: Optional[dict] = None,
    date_where: Optional[dict] = None,
) -> dict:
    """
    Build ChromaDB metadata filter.

    Always scopes to project_id. Multiple conditions use $and — ChromaDB 1.5+
    rejects flat multi-key dicts.

    date_where: pre-built clause from parse_meeting_scope(), e.g.
      {"meeting_id": {"$eq": "..."}} or {"meeting_date": {"$gte": "2026-05-14"}}
      Added as-is — values already contain the operator.
    """
    conditions = [{"project_id": {"$eq": project_id}}]
    if filters:
        for key, value in filters.items():
            conditions.append({key: {"$eq": value}})
    if date_where:
        conditions.append(date_where)
    return {"$and": conditions} if len(conditions) > 1 else conditions[0]


# ── Corpus fetch ──────────────────────────────────────────────────────────────

def _fetch_project_corpus(
    project_id: str,
    hard_filters: Optional[dict],
    date_where: Optional[dict] = None,
) -> list[Document]:
    """
    Fetch all matching transcript chunks as the BM25 corpus.

    Summary chunks (is_meeting_summary=True) are excluded — they are pre-written
    AI overviews, not actual transcript content. Including them would cause BM25
    to rank summary text above the speaker's actual words for topic queries.

    hard_filters narrow the corpus (e.g. speaker_name for compound retrieval).
    date_where scopes to specific meeting(s) from scope resolution.
    """
    collection = get_raw_collection()
    conditions = [{"project_id": {"$eq": project_id}}]
    if hard_filters:
        for key, value in hard_filters.items():
            conditions.append({key: {"$eq": value}})
    if date_where:
        conditions.append(date_where)
    where_filter = {"$and": conditions} if len(conditions) > 1 else conditions[0]

    results = collection.get(where=where_filter, include=["documents", "metadatas"])
    return [
        Document(page_content=results["documents"][i], metadata=results["metadatas"][i])
        for i in range(len(results.get("ids", [])))
        if not results["metadatas"][i].get("is_meeting_summary")  # exclude AI summaries
    ]


# ── Debug logging ─────────────────────────────────────────────────────────────

def _log_chunk_list(label: str, docs: list[Document]) -> None:
    """Log each retrieved chunk with full metadata — for retrieval debugging."""
    logger.info(_DIV)
    logger.info("  %s  [%d docs]", label, len(docs))
    logger.info(_DIV)
    for i, doc in enumerate(docs, 1):
        m   = doc.metadata
        txt = doc.page_content.replace("\n", " ").strip()
        logger.info("  [%d] speaker   : %s", i, m.get("speaker_name", "?"))
        logger.info("       meeting   : %s  (%s)", m.get("meeting_title", "?"), m.get("meeting_date", "?"))
        logger.info(
            "       signals   : decision=%s | commitment=%s | question=%s",
            m.get("contains_decision",   "?"),
            m.get("contains_commitment", "?"),
            m.get("contains_question",   "?"),
        )
        logger.info("       chunk_id  : %s", m.get("chunk_id", "?"))
        logger.info("       TEXT      : %s", txt)
        logger.info(_SEP)
