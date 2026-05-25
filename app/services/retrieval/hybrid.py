"""
hybrid.py — BM25 + dense vector search, merged via RRF.

Public functions:
  retrieve_documents()  — pure dense search (used by topic.py internally)
  hybrid_retrieve()     — BM25 + dense + RRF (default retrieval mode)
  compound_retrieve()   — 3-pass speaker-first retrieval
"""
import logging
import re
from typing import Optional

from langchain_core.documents import Document
from rank_bm25 import BM25Okapi

from app.services.storage.db import get_vectorstore
from .base import (
    _validate_query,
    _validate_project_id,
    _validate_top_k,
    _build_filter,
    _fetch_project_corpus,
    _log_chunk_list,
    DEFAULT_TOP_K,
)

logger = logging.getLogger(__name__)


# ── BM25 internals ────────────────────────────────────────────────────────────

# Common English words that appear in almost every transcript chunk.
# Including them hurts BM25 precision — they match everything and signal nothing.
# "what", "did", "say", "about" appear in nearly every turn of conversation.
_BM25_STOPWORDS = frozenset({
    # Articles / prepositions
    "a", "an", "the", "in", "on", "at", "to", "for", "of", "by", "with",
    "from", "about", "into", "through", "during", "before", "after",
    # Auxiliary verbs
    "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did",
    "will", "would", "could", "should", "may", "might", "shall", "can",
    # Pronouns
    "i", "me", "my", "we", "our", "you", "your",
    "he", "his", "she", "her", "it", "its", "they", "them", "their",
    "this", "that", "these", "those",
    # Conjunctions / connectors
    "and", "or", "but", "not", "if", "then", "so", "as", "because",
    # Question words (appear in nearly every query — not content signals)
    "what", "which", "who", "when", "where", "why", "how",
    # Common transcript verbs / filler
    "say", "said", "tell", "told", "think", "know", "just", "also",
    "all", "any", "some", "other", "each", "both", "than", "very",
})


def _normalize_for_bm25(text: str) -> str:
    """
    Lowercase + canonicalize acronyms + strip punctuation.
    C.E. → ce, P.M. → pm, C-E → ce, so BM25 matches them consistently.
    """
    text = text.lower()
    text = re.sub(
        r'(?<!\w)[a-z](?:\s*[.\-\/]+\s*[a-z])+[.\-\/]*(?!\w)',
        lambda m: re.sub(r'[^a-z]', '', m.group()),
        text,
    )
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _tokenize(text: str) -> list[str]:
    """Tokenize and remove stopwords. Single-char tokens also dropped."""
    tokens = _normalize_for_bm25(text).split()
    return [t for t in tokens if t not in _BM25_STOPWORDS and len(t) > 1]


def _bm25_search(query: str, corpus: list[Document], k: int) -> list[Document]:
    """BM25Okapi over corpus. Zero-score docs excluded from results."""
    if not corpus:
        return []
    tokenized = [_tokenize(doc.page_content) for doc in corpus]
    bm25   = BM25Okapi(tokenized)
    scores = bm25.get_scores(_tokenize(query))
    ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    top    = [i for i in ranked if scores[i] > 0][:k]
    return [corpus[i] for i in top]


def _rrf_merge(
    dense_docs: list[Document],
    bm25_docs:  list[Document],
    rrf_k: int = 60,
) -> tuple[list[Document], dict]:
    """
    Reciprocal Rank Fusion: score = Σ 1/(rrf_k + rank).
    rrf_k=60 is the standard constant.
    Chunks appearing in both lists get double boost.
    Returns (merged_by_score_desc, overlap_stats).
    """
    scores:   dict[str, float]    = {}
    doc_map:  dict[str, Document] = {}
    dense_ids: set[str] = set()
    bm25_ids:  set[str] = set()

    for rank, doc in enumerate(dense_docs):
        cid = doc.metadata.get("chunk_id", str(id(doc)))
        scores[cid]  = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank + 1)
        doc_map[cid] = doc
        dense_ids.add(cid)

    for rank, doc in enumerate(bm25_docs):
        cid = doc.metadata.get("chunk_id", str(id(doc)))
        scores[cid]  = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank + 1)
        doc_map[cid] = doc
        bm25_ids.add(cid)

    overlap = dense_ids & bm25_ids
    stats   = {
        "dense_only": len(dense_ids - overlap),
        "bm25_only":  len(bm25_ids  - overlap),
        "overlap":    len(overlap),
    }
    sorted_ids = sorted(scores, key=lambda x: scores[x], reverse=True)
    return [doc_map[i] for i in sorted_ids], stats


# ── Public retrieval functions ────────────────────────────────────────────────

def retrieve_documents(
    query: str,
    project_id: str,
    filters: Optional[dict] = None,
    k: int = DEFAULT_TOP_K,
) -> list[Document]:
    """
    Pure dense (vector) search.
    Used internally by topic.py and as a fallback; the pipeline uses hybrid_retrieve.
    """
    try:
        query      = _validate_query(query)
        project_id = _validate_project_id(project_id)
        k          = _validate_top_k(k)

        meta_filter = _build_filter(project_id=project_id, filters=filters)
        vectorstore = get_vectorstore()
        logger.debug("  filter     : %s", meta_filter)

        docs = vectorstore.similarity_search(query=query, k=k, filter=meta_filter)
        _log_chunk_list("DENSE (retrieve_documents)", docs)
        return docs

    except Exception as e:
        logger.exception("retrieve_documents failed | query=%r | project=%s", query, project_id)
        raise RuntimeError(f"Document retrieval failed: {e}") from e


def hybrid_retrieve(
    query: str,
    project_id: str,
    hard_filters: Optional[dict] = None,
    date_where: Optional[dict] = None,
    k: int = 25,
) -> list[Document]:
    """
    Hybrid retrieval: dense vector search + BM25, merged via RRF.

    hard_filters: applied to BOTH stages (e.g. meeting_id, speaker_name).
    date_where: pre-built ChromaDB clause from parse_meeting_scope() — scopes
      retrieval to specific meeting(s) or a date range.
    k: adaptive — caller passes from get_retrieval_config().
    """
    query      = _validate_query(query)
    project_id = _validate_project_id(project_id)

    # Stage 1a: dense — post-filter summaries (DB filter can't exclude absent fields)
    dense_filter = _build_filter(project_id, hard_filters, date_where)
    vectorstore  = get_vectorstore()
    raw_dense    = vectorstore.similarity_search(query=query, k=k, filter=dense_filter)
    dense_docs   = [d for d in raw_dense if not d.metadata.get("is_meeting_summary")]
    logger.debug("  filter     : %s", dense_filter)
    if len(raw_dense) != len(dense_docs):
        logger.info("  dense      : dropped %d summary chunk(s)", len(raw_dense) - len(dense_docs))
    _log_chunk_list("STAGE 1a — DENSE", dense_docs)

    # Stage 1b: BM25 (corpus already excludes summaries via _fetch_project_corpus)
    corpus    = _fetch_project_corpus(project_id, hard_filters, date_where)
    bm25_docs = _bm25_search(query, corpus, k=k)
    logger.info("  corpus size: %d transcript docs (summaries excluded)", len(corpus))
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


def compound_retrieve(
    query: str,
    project_id: str,
    named_speaker: str,
    signal_filter: Optional[str] = None,
    date_where: Optional[dict] = None,
    k_final: int = 25,
) -> list[Document]:
    """
    3-pass speaker-first retrieval — guarantees speaker chunks are always found.

    Pass 1: Fetch ALL of speaker's chunks from DB (no k limit — guaranteed corpus).
    Pass 2: BM25 within speaker corpus → topic-relevant chunks from their words.
    Pass 3: Dense search filtered to speaker → semantic match within their chunks.
    Merge:  RRF of Pass 2 + Pass 3 → best topic-relevant speaker chunks.
    Signal: Apply signal_filter after merge (commitment / question / decision).
    Fallback: Speaker has 0 chunks in scope → broad hybrid so LLM can report that.
    """
    # Pass 1 ─────────────────────────────────────────────────────────────────
    speaker_corpus = _fetch_project_corpus(
        project_id,
        hard_filters={"speaker_name": named_speaker},
        date_where=date_where,
    )
    logger.info(
        "  compound   : %d chunks for speaker=%s (scope: %s)",
        len(speaker_corpus), named_speaker, "scoped" if date_where else "project-wide",
    )

    if not speaker_corpus:
        logger.info("  compound   : 0 chunks — broad fallback")
        return hybrid_retrieve(query, project_id, date_where=date_where, k=k_final)

    # Tiny corpus guard — BM25 ranking over ≤4 chunks is statistically meaningless.
    # Return all of the speaker's chunks directly; signal filter still applied below.
    if len(speaker_corpus) <= 4:
        logger.info("  compound   : tiny corpus (%d chunks) — skipping BM25/dense", len(speaker_corpus))
        candidates = speaker_corpus
        if signal_filter:
            key      = f"contains_{signal_filter}"
            filtered = [d for d in candidates if d.metadata.get(key, False)]
            return filtered if filtered else candidates
        return candidates

    # Pass 2: BM25 within speaker ─────────────────────────────────────────────
    bm25_docs = _bm25_search(query, speaker_corpus, k=k_final)
    logger.info(
        "  [compound] BM25   : %d results | top: %s",
        len(bm25_docs),
        " | ".join(
            f"{d.metadata.get('meeting_title','?')!r} [{d.page_content[:50].replace(chr(10),' ')}]"
            for d in bm25_docs[:3]
        ) or "none",
    )

    # Pass 3: Dense filtered to speaker (summaries dropped — speaker filter mostly
    # handles this, but post-filter ensures clean results regardless)
    dense_filter = _build_filter(project_id, {"speaker_name": named_speaker}, date_where)
    vectorstore  = get_vectorstore()
    raw_dense    = vectorstore.similarity_search(query=query, k=k_final, filter=dense_filter)
    dense_docs   = [d for d in raw_dense if not d.metadata.get("is_meeting_summary")]
    logger.info(
        "  [compound] dense  : %d results | top: %s",
        len(dense_docs),
        " | ".join(
            f"{d.metadata.get('meeting_title','?')!r} [{d.page_content[:50].replace(chr(10),' ')}]"
            for d in dense_docs[:3]
        ) or "none",
    )

    # RRF merge ───────────────────────────────────────────────────────────────
    merged, stats = _rrf_merge(dense_docs, bm25_docs)
    logger.info(
        "  [compound] RRF    : dense_only=%d | bm25_only=%d | overlap=%d | total=%d",
        stats["dense_only"], stats["bm25_only"], stats["overlap"], len(merged),
    )

    # Signal filter ───────────────────────────────────────────────────────────
    if signal_filter:
        key      = f"contains_{signal_filter}"
        filtered = [d for d in merged if d.metadata.get(key, False)]
        if filtered:
            logger.info("  compound   : signal=%s → %d/%d kept", signal_filter, len(filtered), len(merged))
            return filtered[:k_final]
        logger.info("  compound   : signal=%s → 0 matches, returning unfiltered", signal_filter)

    return merged[:k_final]


# ── Legacy signal wrappers (backward compat) ──────────────────────────────────
# Superseded by hybrid_retrieve() with hard_filters. Kept for older scripts.

def retrieve_commitment_documents(query: str, project_id: str, k: int = DEFAULT_TOP_K) -> list[Document]:
    return retrieve_documents(query, project_id, filters={"contains_commitment": True}, k=k)


def retrieve_question_documents(query: str, project_id: str, k: int = DEFAULT_TOP_K) -> list[Document]:
    return retrieve_documents(query, project_id, filters={"contains_question": True}, k=k)


def retrieve_decision_candidates(query: str, project_id: str, k: int = DEFAULT_TOP_K) -> list[Document]:
    return retrieve_documents(query, project_id, filters=None, k=k)
