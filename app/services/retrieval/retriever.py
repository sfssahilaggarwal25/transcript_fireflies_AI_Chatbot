import logging
from typing import Optional

from langchain_core.documents import Document
from rank_bm25 import BM25Okapi

from app.services.storage.db import get_raw_collection, get_vectorstore
from app.services.storage.project_store import get_meeting_ids_for_project

logger = logging.getLogger(__name__)

DEFAULT_TOP_K = 8
MAX_TOP_K = 25


def _validate_query(query: str) -> str:
    """
    Validate and normalize user query.
    """

    if not query:
        raise ValueError("Query cannot be empty.")

    cleaned = query.strip()

    if not cleaned:
        raise ValueError("Query cannot be blank.")

    return cleaned


def _validate_project_id(project_id: str) -> str:
    """
    Validate project scoping.
    """

    if not project_id:
        raise ValueError("project_id is required.")

    cleaned = project_id.strip()

    if not cleaned:
        raise ValueError("project_id cannot be blank.")

    return cleaned


def _validate_top_k(k: int) -> int:
    """
    Validate retrieval depth.
    """

    if k <= 0:
        return DEFAULT_TOP_K

    if k > MAX_TOP_K:
        logger.warning(
            "Requested top_k=%s exceeds max. Capping to %s.",
            k,
            MAX_TOP_K,
        )
        return MAX_TOP_K

    return k


def _build_filter(
    project_id: str,
    filters: Optional[dict] = None,
) -> dict:
    """
    Build ChromaDB metadata filter.
    Always excludes is_meeting_summary chunks — those are fetched separately
    via _retrieve_summary_chunks() using the raw collection, not vector search.
    Multiple conditions use $and — ChromaDB 1.5+ rejects flat multi-key dicts.
    """
    base = {"project_id": {"$eq": project_id}}

    if not filters:
        return base

    conditions = [base]
    for key, value in filters.items():
        conditions.append({key: {"$eq": value}})
    return {"$and": conditions}


def retrieve_documents(
    query: str,
    project_id: str,
    filters: Optional[dict] = None,
    k: int = DEFAULT_TOP_K,
) -> list[Document]:
    """
    Retrieve semantically relevant transcript documents.

    Args:
        query:
            User semantic search query.

        project_id:
            Required project isolation boundary.

        filters:
            Optional metadata filters.
            Example:
                {
                    "speaker_role": "client",
                    "contains_commitment": True
                }

        k:
            Number of documents to retrieve.

    Returns:
        List[Document]
    """

    try:
        query = _validate_query(query)
        project_id = _validate_project_id(project_id)
        k = _validate_top_k(k)

        metadata_filter = _build_filter(
            project_id=project_id,
            filters=filters,
        )

        vectorstore = get_vectorstore()
        logger.debug("  filter     : %s", metadata_filter)

        documents = vectorstore.similarity_search(
            query=query,
            k=k,
            filter=metadata_filter,
        )

        logger.info("  retrieved  : %d documents", len(documents))
        for i, doc in enumerate(documents, 1):
            m = doc.metadata
            preview = doc.page_content[:90].replace("\n", " ")
            logger.info(
                "  doc[%d/%d]  : %s (%s) | %s | \"%s...\"",
                i,
                len(documents),
                m.get("meeting_title", "?")[:35],
                m.get("meeting_date", "?"),
                m.get("speaker_name", "?"),
                preview,
            )

        return documents

    except Exception as e:
        logger.exception(
            "Document retrieval failed | query='%s' | project_id=%s",
            query,
            project_id,
        )
        raise RuntimeError(
            f"Document retrieval failed: {str(e)}"
        ) from e


def retrieve_commitment_documents(
    query: str,
    project_id: str,
    k: int = DEFAULT_TOP_K,
) -> list[Document]:
    """
    Retrieve commitment-related candidate chunks.
    Metadata hint only — not authoritative truth.
    """

    return retrieve_documents(
        query=query,
        project_id=project_id,
        filters={
            "contains_commitment": True,
        },
        k=k,
    )


def retrieve_question_documents(
    query: str,
    project_id: str,
    k: int = DEFAULT_TOP_K,
) -> list[Document]:
    """
    Retrieve question-related transcript chunks.
    """

    return retrieve_documents(
        query=query,
        project_id=project_id,
        filters={
            "contains_question": True,
        },
        k=k,
    )


def retrieve_decision_candidates(
    query: str,
    project_id: str,
    k: int = DEFAULT_TOP_K,
) -> list[Document]:
    """
    Retrieve decision candidates.

    IMPORTANT:
    Do NOT hard filter only decision metadata.
    Decision hints are weak signals.
    Use broad semantic retrieval instead.
    Semantic validation happens later.
    """

    return retrieve_documents(
        query=query,
        project_id=project_id,
        filters=None,
        k=k,
    )


def retrieve_timeline_documents(
    query: str,
    project_id: str,
    k_per_meeting: int = 6,
) -> list[Document]:
    """
    Retrieve documents for timeline/historical queries.

    Runs one semantic search per meeting in the project, then merges results
    sorted chronologically by meeting_date. This ensures every meeting
    contributes equally — plain similarity_search would skew toward whichever
    meeting is semantically closer to the query.
    """
    meeting_ids = get_meeting_ids_for_project(project_id)
    if not meeting_ids:
        logger.warning("No meeting IDs found for project_id=%s", project_id)
        return retrieve_documents(query, project_id, k=k_per_meeting * 2)

    all_docs: list[Document] = []
    for meeting_id in meeting_ids:
        try:
            docs = retrieve_documents(
                query=query,
                project_id=project_id,
                filters={"meeting_id": meeting_id},
                k=k_per_meeting,
            )
            all_docs.extend(docs)
            logger.debug("  timeline   : %d docs from meeting_id=%s", len(docs), meeting_id)
        except Exception as e:
            logger.warning("Timeline retrieval skipped for meeting_id=%s: %s", meeting_id, e)

    all_docs.sort(key=lambda d: d.metadata.get("meeting_date", ""))
    return all_docs


# ── Hybrid retrieval (BM25 + dense) ───────────────────────────────────────────

def _tokenize(text: str) -> list[str]:
    return text.lower().split()


def _fetch_project_corpus(
    project_id: str,
    hard_filters: Optional[dict],
) -> list[Document]:
    """
    Fetch all chunks for the project from the raw ChromaDB collection.
    This is the BM25 corpus — built at query time, pure in-memory math.
    hard_filters (e.g. speaker_name) narrow the corpus to the relevant subset.
    """
    collection = get_raw_collection()
    conditions = [{"project_id": {"$eq": project_id}}]
    if hard_filters:
        for key, value in hard_filters.items():
            conditions.append({key: {"$eq": value}})
    where_filter = {"$and": conditions} if len(conditions) > 1 else conditions[0]

    results = collection.get(where=where_filter, include=["documents", "metadatas"])
    corpus = []
    for i in range(len(results.get("ids", []))):
        corpus.append(Document(
            page_content=results["documents"][i],
            metadata=results["metadatas"][i],
        ))
    return corpus


def _bm25_search(query: str, corpus: list[Document], k: int) -> list[Document]:
    """
    Keyword search over corpus using BM25Okapi.
    Returns top-k documents by BM25 score, zero-score docs excluded.
    """
    if not corpus:
        return []
    tokenized_corpus = [_tokenize(doc.page_content) for doc in corpus]
    bm25 = BM25Okapi(tokenized_corpus)
    scores = bm25.get_scores(_tokenize(query))
    ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    top = [i for i in ranked if scores[i] > 0][:k]
    return [corpus[i] for i in top]


def _rrf_merge(
    dense_docs: list[Document],
    bm25_docs: list[Document],
    rrf_k: int = 60,
) -> tuple[list[Document], dict]:
    """
    Reciprocal Rank Fusion: score = sum(1 / (rrf_k + rank)) across both lists.
    rrf_k=60 is the standard constant — balances short and long ranked lists.
    Returns (merged_docs_sorted_by_score, overlap_stats).
    """
    scores: dict[str, float] = {}
    doc_map: dict[str, Document] = {}
    dense_ids: set[str] = set()
    bm25_ids: set[str] = set()

    for rank, doc in enumerate(dense_docs):
        doc_id = doc.metadata.get("chunk_id", str(id(doc)))
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (rrf_k + rank + 1)
        doc_map[doc_id] = doc
        dense_ids.add(doc_id)

    for rank, doc in enumerate(bm25_docs):
        doc_id = doc.metadata.get("chunk_id", str(id(doc)))
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (rrf_k + rank + 1)
        doc_map[doc_id] = doc
        bm25_ids.add(doc_id)

    overlap = dense_ids & bm25_ids
    stats = {
        "dense_only": len(dense_ids - overlap),
        "bm25_only":  len(bm25_ids - overlap),
        "overlap":    len(overlap),
    }
    sorted_ids = sorted(scores, key=lambda x: scores[x], reverse=True)
    return [doc_map[i] for i in sorted_ids], stats


def hybrid_retrieve(
    query: str,
    project_id: str,
    hard_filters: Optional[dict] = None,
    k: int = 25,
) -> list[Document]:
    """
    Hybrid retrieval: dense vector search + BM25 keyword search, merged via RRF.

    hard_filters: applied to BOTH stages (e.g. speaker_name for speaker queries).
    Do NOT pass signal filters (contains_question, contains_commitment) here —
    those block valid chunks. Signal relevance is handled downstream by the re-ranker.
    """
    query = _validate_query(query)
    project_id = _validate_project_id(project_id)

    # Stage 1a: dense
    dense_filter = _build_filter(project_id, hard_filters)
    vectorstore = get_vectorstore()
    dense_docs = vectorstore.similarity_search(query=query, k=k, filter=dense_filter)
    logger.debug("  filter     : %s", dense_filter)
    logger.info("  dense      : %d docs", len(dense_docs))

    # Stage 1b: BM25
    corpus = _fetch_project_corpus(project_id, hard_filters)
    bm25_docs = _bm25_search(query, corpus, k=k)
    logger.info("  bm25       : %d docs (corpus size=%d)", len(bm25_docs), len(corpus))

    # Stage 2: RRF merge
    merged, stats = _rrf_merge(dense_docs, bm25_docs)
    logger.info(
        "  hybrid     : dense_only=%d | bm25_only=%d | overlap=%d | total=%d",
        stats["dense_only"], stats["bm25_only"], stats["overlap"], len(merged),
    )

    result = merged[:k]
    logger.info("  retrieved  : %d documents (hybrid)", len(result))
    for i, doc in enumerate(result, 1):
        m = doc.metadata
        preview = doc.page_content[:90].replace("\n", " ")
        logger.info(
            "  doc[%d/%d]  : %s (%s) | %s | \"%s...\"",
            i, len(result),
            m.get("meeting_title", "?")[:35],
            m.get("meeting_date", "?"),
            m.get("speaker_name", "?"),
            preview,
        )

    return result