"""
expansion.py — Neighbor chunk expansion (pre-rerank and post-rerank).

Two expansion strategies:

  _expand_short_chunks_for_reranking()  [pre-rerank]
    Short fragments lose meaning in isolation. Fetching their neighbors before
    reranking gives the reranker full conversational context to score correctly.
    Neighbors enter the rerank pool as full candidates (no _position tag).

  _expand_context()  [post-rerank]
    After reranking selects the best chunks, inject their neighbors as labeled
    context for the LLM. Neighbors carry _position='before'/'after' so the
    formatter labels them [CONTEXT] and excludes them from the sources panel.
"""

import logging
from typing import Optional

from langchain_core.documents import Document

from app.core.storage.db import get_raw_collection
from .constants import _EXPAND_TOP_N, SHORT_CHUNK_THRESHOLD

logger = logging.getLogger(__name__)


def _fetch_neighbor(chunk_id: str, position: str) -> Optional[Document]:
    """
    Fetch one neighbor chunk by chunk_id from ChromaDB. O(1) ID-lookup.
    Returns None on miss or DB error.
    position is stored in _position metadata so callers can label or strip it.
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


def _expand_short_chunks_for_reranking(docs: list[Document]) -> list[Document]:
    """
    Pre-rerank neighbor expansion for short chunks.

    Short utterances ("Agreed.", "Yes, confirmed.", "That's wrong.") score low
    in isolation — the reranker drops them even when they are the most relevant
    fragment (e.g. a one-line decision or confirmation). Fetching adjacent chunks
    gives the reranker the full conversational unit to score instead of a fragment.

    Difference from _expand_context:
      - Runs BEFORE reranking so neighbors enter the scoring pool.
      - Neighbors carry no _position tag — they are full rerank candidates,
        not display-only context labels.
      - Deduplication uses existing_ids built from the complete docs list so a
        neighbor already retrieved by hybrid search is never added twice.

    Cost: at most 2 × (short chunk count) ChromaDB ID-lookups per call.
    """
    if not docs:
        return docs

    existing_ids: set[str] = {d.metadata.get("chunk_id", "") for d in docs}
    neighbors: list[Document] = []
    short_count = 0

    for doc in docs:
        if len(doc.page_content) >= SHORT_CHUNK_THRESHOLD:
            continue
        short_count += 1

        prev_id = doc.metadata.get("prev_chunk_id")
        if prev_id and prev_id not in existing_ids:
            neighbor = _fetch_neighbor(prev_id, "before")
            if neighbor:
                neighbor.metadata.pop("_position", None)
                neighbors.append(neighbor)
                existing_ids.add(prev_id)

        next_id = doc.metadata.get("next_chunk_id")
        if next_id and next_id not in existing_ids:
            neighbor = _fetch_neighbor(next_id, "after")
            if neighbor:
                neighbor.metadata.pop("_position", None)
                neighbors.append(neighbor)
                existing_ids.add(next_id)

    if neighbors:
        logger.info(
            "pre-rerank expansion: %d short chunks → +%d neighbor chunks added to rerank pool",
            short_count, len(neighbors),
        )
    return docs + neighbors


def _expand_context(docs: list[Document], n: int = _EXPAND_TOP_N) -> list[Document]:
    """
    Post-rerank: inject prev/next neighbor chunks adjacent to the top-n anchor docs.

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