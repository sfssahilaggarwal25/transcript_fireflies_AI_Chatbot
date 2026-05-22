import logging
import re
import unicodedata
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
    date_where: Optional[dict] = None,
) -> dict:
    """
    Build ChromaDB metadata filter.
    Always excludes is_meeting_summary chunks — those are fetched separately
    via _retrieve_summary_chunks() using the raw collection, not vector search.
    Multiple conditions use $and — ChromaDB 1.5+ rejects flat multi-key dicts.

    date_where: pre-built clause from _parse_meeting_scope(), e.g.
      {"meeting_id": {"$eq": "..."}} or {"meeting_date": {"$gte": "2026-05-14"}}
      Added directly — values already contain the operator, no $eq wrapping.
    """
    base = {"project_id": {"$eq": project_id}}
    conditions = [base]

    if filters:
        for key, value in filters.items():
            conditions.append({key: {"$eq": value}})

    if date_where:
        conditions.append(date_where)

    return {"$and": conditions} if len(conditions) > 1 else conditions[0]


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

        _log_chunk_list("DENSE (retrieve_documents)", documents)
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
    scope_meeting_ids: Optional[list[str]] = None,
) -> list[Document]:
    """
    Retrieve documents for timeline/historical queries.

    Runs one semantic search per meeting, then merges results sorted
    chronologically. This ensures every meeting contributes equally —
    project-wide search would skew toward the most semantically similar meeting.

    scope_meeting_ids: pre-resolved meeting IDs from QueryUnderstanding.
      When set, only those meetings are searched (e.g. "last 3 meetings",
      "meetings 2 and 3"). When None, all project meetings are searched.
    """
    all_project_meetings = get_meeting_ids_for_project(project_id)
    if not all_project_meetings:
        logger.warning("No meeting IDs found for project_id=%s", project_id)
        return retrieve_documents(query, project_id, k=k_per_meeting * 2)

    # Respect pre-resolved scope — never search outside the requested meetings
    if scope_meeting_ids:
        meeting_ids = [mid for mid in all_project_meetings if mid in scope_meeting_ids]
        if not meeting_ids:
            logger.warning(
                "  timeline   : scope_meeting_ids %s not in project — falling back to all",
                scope_meeting_ids,
            )
            meeting_ids = all_project_meetings
        else:
            logger.info(
                "  timeline   : scoped to %d/%d meeting(s)",
                len(meeting_ids), len(all_project_meetings),
            )
    else:
        meeting_ids = all_project_meetings

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


# ── Debug logging ─────────────────────────────────────────────────────────────

_DIV  = "=" * 64
_SEP  = "-" * 64

def _log_chunk_list(label: str, docs: list[Document]) -> None:
    """Log each doc in a stage with full text — for debugging retrieval accuracy."""
    logger.info(_DIV)
    logger.info("  %s  [%d docs]", label, len(docs))
    logger.info(_DIV)
    for i, doc in enumerate(docs, 1):
        m   = doc.metadata
        txt = doc.page_content.replace("\n", " ").strip()
        logger.info(
            "  [%d] speaker   : %s",
            i, m.get("speaker_name", "?"),
        )
        logger.info(
            "       meeting   : %s  (%s)",
            m.get("meeting_title", "?"), m.get("meeting_date", "?"),
        )
        logger.info(
            "       signals   : decision=%s | commitment=%s | question=%s",
            m.get("contains_decision",   "?"),
            m.get("contains_commitment", "?"),
            m.get("contains_question",   "?"),
        )
        logger.info("       chunk_id  : %s", m.get("chunk_id", "?"))
        logger.info("       TEXT      : %s", txt)
        logger.info(_SEP)


# ── Hybrid retrieval (BM25 + dense) ───────────────────────────────────────────

def _normalize_for_bm25(text: str) -> str:
    text = text.lower()
    # Canonicalize acronyms: C.E.→ce, P.M.→pm, U.S.A.→usa, C-E→ce, C. E.→ce
    # Requires at least one dot/dash/slash so normal single-letter words are never merged
    text = re.sub(
        r'(?<!\w)[a-z](?:\s*[.\-\/]+\s*[a-z])+[.\-\/]*(?!\w)',
        lambda m: re.sub(r'[^a-z]', '', m.group()),
        text,
    )
    text = re.sub(r'[^\w\s]', ' ', text)   # remove remaining punctuation
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _tokenize(text: str) -> list[str]:
    return _normalize_for_bm25(text).split()


def _fetch_project_corpus(
    project_id: str,
    hard_filters: Optional[dict],
    date_where: Optional[dict] = None,
) -> list[Document]:
    """
    Fetch all chunks for the project from the raw ChromaDB collection.
    This is the BM25 corpus — built at query time, pure in-memory math.
    hard_filters (e.g. speaker_name) narrow the corpus to the relevant subset.
    date_where: pre-built clause from _parse_meeting_scope() — applied as-is.
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
    date_where: Optional[dict] = None,
    k: int = 25,
) -> list[Document]:
    """
    Hybrid retrieval: dense vector search + BM25 keyword search, merged via RRF.

    hard_filters: applied to BOTH stages (e.g. speaker_name for speaker queries).
    date_where: pre-built ChromaDB clause from _parse_meeting_scope() — scopes
      retrieval to a specific meeting, N recent meetings, or a date range.
    Do NOT pass signal filters (contains_question, contains_commitment) here —
    those block valid chunks. Signal relevance is handled downstream by the re-ranker.
    """
    query = _validate_query(query)
    project_id = _validate_project_id(project_id)

    # Stage 1a: dense
    dense_filter = _build_filter(project_id, hard_filters, date_where)
    vectorstore = get_vectorstore()
    dense_docs = vectorstore.similarity_search(query=query, k=k, filter=dense_filter)
    logger.debug("  filter     : %s", dense_filter)
    _log_chunk_list("STAGE 1a — DENSE", dense_docs)

    # Stage 1b: BM25
    corpus = _fetch_project_corpus(project_id, hard_filters, date_where)
    bm25_docs = _bm25_search(query, corpus, k=k)
    logger.info("  corpus size: %d docs", len(corpus))
    _log_chunk_list("STAGE 1b — BM25", bm25_docs)

    # Stage 2: RRF merge
    merged, stats = _rrf_merge(dense_docs, bm25_docs)
    logger.info(
        "  rrf stats  : dense_only=%d | bm25_only=%d | overlap=%d | total=%d",
        stats["dense_only"], stats["bm25_only"], stats["overlap"], len(merged),
    )

    result = merged[:k]
    _log_chunk_list("STAGE 2 — HYBRID (after RRF, top %d)" % k, result)

    return result


def _norm_name(name: str) -> str:
    return unicodedata.normalize("NFD", name).encode("ascii", "ignore").decode().lower()


def compound_retrieve(
    query: str,
    project_id: str,
    named_speaker: str,
    signal_filter: Optional[str] = None,
    date_where: Optional[dict] = None,
    k_broad: int = 40,
    k_final: int = 25,
) -> list[Document]:
    """
    3-pass speaker-first retrieval — guarantees speaker chunks are found.

    Old 2-pass problem:
      Broad search (all speakers) → post-filter by speaker.
      If the speaker's chunks rank outside the top-40, they're silently dropped.
      "What did Rahul say about X?" fails when Rahul's X-chunks are at rank #41+.

    New 3-pass approach:
      Pass 1: Fetch ALL of speaker's chunks directly from DB (guaranteed corpus).
      Pass 2: BM25 keyword search within that corpus — topic relevance inside
              the speaker's own words, not against the full project.
      Pass 3: Dense vector search filtered to speaker — semantic similarity
              scoped to speaker, respects date_where if set.
      Merge:  RRF of Pass 2 + Pass 3 → best topic-relevant speaker chunks.
      Signal: Apply signal_filter (question/commitment/decision) after merge.
      Fallback: Only when speaker has ZERO chunks in project/scope —
                returns broad hybrid so LLM can explain they weren't found.
    """
    target = _norm_name(named_speaker)

    # ── Pass 1: pull the speaker's complete corpus from DB ───────────────────
    # Direct DB fetch — no vector search — guaranteed to find all their chunks.
    # date_where scopes to the right meeting(s) when set.
    speaker_corpus = _fetch_project_corpus(
        project_id,
        hard_filters={"speaker_name": named_speaker},
        date_where=date_where,
    )

    logger.info(
        "  compound   : %d total chunks for speaker=%s (scope: %s)",
        len(speaker_corpus), named_speaker,
        "scoped" if date_where else "project-wide",
    )

    # ── Fallback: speaker has no data at all ─────────────────────────────────
    # Only hit when the speaker name doesn't exist in this project/scope.
    # Return broad hybrid so the LLM can inform the PM rather than going silent.
    if not speaker_corpus:
        logger.info(
            "  compound   : speaker=%s has 0 chunks — returning broad fallback",
            named_speaker,
        )
        return hybrid_retrieve(query, project_id, date_where=date_where, k=k_final)

    # ── Pass 2: BM25 within speaker corpus ───────────────────────────────────
    # Keyword match on the query — finds the topic-relevant chunks from this speaker.
    bm25_docs = _bm25_search(query, speaker_corpus, k=k_final)

    # ── Pass 3: Dense vector search filtered to speaker ──────────────────────
    # Semantic similarity search — also scoped to this speaker and date_where.
    dense_filter = _build_filter(project_id, {"speaker_name": named_speaker}, date_where)
    vectorstore = get_vectorstore()
    dense_docs = vectorstore.similarity_search(query=query, k=k_final, filter=dense_filter)

    # ── Merge: RRF of dense + BM25 ───────────────────────────────────────────
    merged_docs, stats = _rrf_merge(dense_docs, bm25_docs)
    logger.info(
        "  compound   : rrf dense_only=%d bm25_only=%d overlap=%d merged=%d",
        stats["dense_only"], stats["bm25_only"], stats["overlap"], len(merged_docs),
    )

    # ── Apply signal filter ───────────────────────────────────────────────────
    # Post-filter for commitment/question/decision signals — keeps only flagged chunks.
    if signal_filter:
        signal_key = f"contains_{signal_filter}"
        filtered = [d for d in merged_docs if d.metadata.get(signal_key, False)]
        if filtered:
            logger.info(
                "  compound   : signal_filter=%s → %d/%d chunks kept",
                signal_filter, len(filtered), len(merged_docs),
            )
            return filtered[:k_final]
        # If signal filter removes everything, fall back to unfiltered speaker docs
        # (better to show what the speaker said than return nothing)
        logger.info(
            "  compound   : signal_filter=%s returned 0 — returning unfiltered speaker docs",
            signal_filter,
        )

    return merged_docs[:k_final]


def analytical_retrieve(
    project_id: str,
    signal_filter: Optional[str] = None,
    date_where: Optional[dict] = None,
    named_speaker: Optional[str] = None,
) -> dict:
    """
    Pure metadata count — no vector search, no LLM counting.

    Returns a structured dict the LLM formats into a sentence:
      {total_chunks, signal_count, meeting_count, meetings, speaker_count, speakers}

    signal_filter: "question" | "commitment" | "decision" | "open_issue" |
                   "document_share" | None (count all chunks)
    """
    collection = get_raw_collection()
    conditions: list[dict] = [{"project_id": {"$eq": project_id}}]
    if named_speaker:
        conditions.append({"speaker_name": {"$eq": named_speaker}})
    if date_where:
        conditions.append(date_where)
    where_filter = {"$and": conditions} if len(conditions) > 1 else conditions[0]

    results = collection.get(where=where_filter, include=["metadatas"])
    all_metas = [
        m for m in results.get("metadatas", [])
        if not m.get("is_meeting_summary")
    ]

    if signal_filter:
        key = f"contains_{signal_filter}"
        signal_metas = [m for m in all_metas if m.get(key, False)]
    else:
        signal_metas = all_metas

    meetings: dict[str, str] = {}
    speakers: set[str] = set()
    for m in signal_metas:
        mid = m.get("meeting_id", "")
        if mid:
            meetings[mid] = m.get("meeting_title", mid)
        name = m.get("speaker_name", "")
        if name:
            speakers.add(name)

    return {
        "total_chunks":  len(all_metas),
        "signal_count":  len(signal_metas),
        "meeting_count": len(meetings),
        "meetings":      list(meetings.values()),
        "speaker_count": len(speakers),
        "speakers":      sorted(speakers),
        "signal_filter": signal_filter,
        "named_speaker": named_speaker,
    }


def topic_summary_retrieve(
    topic: str,
    project_id: str,
    scope_meeting_ids: Optional[list[str]] = None,
    k_per_meeting: int = 8,
) -> list[Document]:
    """
    Deep-dive retrieval for a specific topic across meetings (or within a scope).

    scope_meeting_ids: pre-resolved meeting IDs from QueryUnderstanding.
      When set, only those meetings are searched — no extra DB call needed.
      When None, all project meetings are searched.

    Runs per-meeting hybrid search for the topic, then merges chronologically.
    Per-meeting search ensures every meeting contributes equally — project-wide
    hybrid_retrieve would skew toward whichever meeting is semantically closest.
    """
    all_project_meetings = get_meeting_ids_for_project(project_id)
    if not all_project_meetings:
        return hybrid_retrieve(topic, project_id, k=k_per_meeting * 3)

    # Filter to scoped meetings upfront — no per-iteration DB call
    meetings_to_search = (
        [mid for mid in all_project_meetings if mid in scope_meeting_ids]
        if scope_meeting_ids
        else all_project_meetings
    )

    if not meetings_to_search:
        logger.warning("  topic_sum  : no meetings in scope — falling back to all meetings")
        meetings_to_search = all_project_meetings

    all_docs: list[Document] = []
    for mid in meetings_to_search:
        try:
            docs = hybrid_retrieve(
                topic, project_id,
                hard_filters={"meeting_id": mid},
                date_where=None,
                k=k_per_meeting,
            )
            all_docs.extend(docs)
        except Exception as e:
            logger.warning("topic_summary_retrieve skipped meeting_id=%s: %s", mid, e)

    all_docs.sort(key=lambda d: (
        d.metadata.get("meeting_date", ""),
        d.metadata.get("start_time") or 0,
    ))
    logger.info(
        "  topic_sum  : %d docs for topic=%r across %d/%d meetings",
        len(all_docs), topic, len(meetings_to_search), len(all_project_meetings),
    )
    return all_docs


def contribution_retrieve(
    project_id: str,
    date_where: Optional[dict] = None,
) -> dict:
    """
    Speaker contribution analysis — counts transcript chunks per speaker.
    Returns a ranked list (most to least active) with meeting attendance.
    No vector search needed — pure metadata aggregation.
    """
    collection = get_raw_collection()
    conditions: list[dict] = [{"project_id": {"$eq": project_id}}]
    if date_where:
        conditions.append(date_where)
    where_filter = {"$and": conditions} if len(conditions) > 1 else conditions[0]

    results = collection.get(where=where_filter, include=["metadatas"])
    speaker_data: dict[str, dict] = {}

    for m in results.get("metadatas", []):
        if m.get("is_meeting_summary"):
            continue
        name = m.get("speaker_name", "")
        mid  = m.get("meeting_id", "")
        if not name:
            continue
        if name not in speaker_data:
            speaker_data[name] = {"chunk_count": 0, "meetings": set()}
        speaker_data[name]["chunk_count"] += 1
        if mid:
            speaker_data[name]["meetings"].add(mid)

    ranked = sorted(
        [
            {
                "speaker_name":    name,
                "chunk_count":     data["chunk_count"],
                "meeting_count":   len(data["meetings"]),
            }
            for name, data in speaker_data.items()
        ],
        key=lambda x: x["chunk_count"],
        reverse=True,
    )

    logger.info("  contribution: %d speakers ranked", len(ranked))
    return {"ranked_speakers": ranked, "total_speakers": len(ranked)}