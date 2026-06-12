"""
base.py — Shared retrieval utilities.

Validation helpers, ChromaDB filter builder, corpus fetch, debug logging.
Used by hybrid.py, structured.py, and topic.py — not imported externally.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from langchain_core.documents import Document

from app.core.storage.db import get_raw_collection


def _fmt_date(val) -> str:
    """Epoch-ms / epoch-s / ISO string → YYYY-MM-DD for log output."""
    if val is None:
        return ""
    if isinstance(val, (int, float)) and val > 0:
        ts = val / 1000 if val > 1e10 else val
        try:
            return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
        except (OSError, OverflowError, ValueError):
            return str(val)
    return str(val)

logger = logging.getLogger(__name__)


# ── Per-request BM25 corpus cache ─────────────────────────────────────────────
# _fetch_project_corpus() pulls ALL matching chunks from ChromaDB on every call.
# Within one query the LLM can call search_transcripts 3-6 times — each call
# would re-fetch the same 1,669 chunks. scope_where is fixed for the whole query
# (set once by query_scope_node), so the corpus is identical across tool calls
# with the same (project_id, hard_filters, date_where).
#
# Cache key: (project_id, hard_filters_json, date_where_json)
# Lifetime:  one query — reset_corpus_cache() is called by service.py at the
#            start of answer_query(), before graph.invoke().
#
# Thread safety: each HTTP request gets its own Python thread (FastAPI/uvicorn
# default). Module-level dicts are per-process, not per-thread. If you move to
# async workers or multi-threading, replace this with a contextvars.ContextVar.

_corpus_cache: dict[tuple, list[Document]] = {}


def reset_corpus_cache() -> None:
    """Clear the BM25 corpus cache. Call once at the start of each new query."""
    _corpus_cache.clear()


def _make_corpus_key(
    project_id: str,
    hard_filters: Optional[dict],
    date_where: Optional[dict],
) -> tuple:
    """Build a hashable cache key from the three corpus-defining parameters."""
    hf_key = json.dumps(hard_filters, sort_keys=True) if hard_filters else None
    dw_key = json.dumps(date_where,   sort_keys=True) if date_where   else None
    return (project_id, hf_key, dw_key)

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

    Results are cached per (project_id, hard_filters, date_where) for the
    duration of one query. The LLM calls search_transcripts multiple times with
    the same scope — without this cache each call re-fetches the full corpus
    from ChromaDB. Cache is reset by reset_corpus_cache() in service.py before
    each new query so stale data is never returned.
    """
    key = _make_corpus_key(project_id, hard_filters, date_where)
    if key in _corpus_cache:
        cached = _corpus_cache[key]
        logger.debug("corpus cache HIT  | key=%s | %d docs", key, len(cached))
        return cached

    collection = get_raw_collection()
    conditions = [{"project_id": {"$eq": project_id}}]
    if hard_filters:
        for k, value in hard_filters.items():
            conditions.append({k: {"$eq": value}})
    if date_where:
        conditions.append(date_where)
    where_filter = {"$and": conditions} if len(conditions) > 1 else conditions[0]

    results = collection.get(where=where_filter, include=["documents", "metadatas"])
    corpus = [
        Document(page_content=results["documents"][i], metadata=results["metadatas"][i])
        for i in range(len(results.get("ids", [])))
        if not results["metadatas"][i].get("is_meeting_summary")  # exclude AI summaries
    ]

    _corpus_cache[key] = corpus
    logger.debug("corpus cache MISS | key=%s | %d docs fetched", key, len(corpus))
    return corpus


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
        logger.info("       meeting   : %s  (%s)", m.get("meeting_title", "?"), _fmt_date(m.get("meeting_date")))
        logger.info(
            "       signals   : decision=%s | commitment=%s | question=%s",
            m.get("contains_decision",   "?"),
            m.get("contains_commitment", "?"),
            m.get("contains_question",   "?"),
        )
        logger.info("       TEXT      : %s", txt)
        logger.info(_SEP)
