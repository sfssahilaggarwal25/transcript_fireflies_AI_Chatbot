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

from app.core.storage.db import get_vectorstore
from .base import (
    _validate_query,
    _validate_project_id,
    _validate_top_k,
    _build_filter,
    _fetch_project_corpus,
    _log_chunk_list,
    _fmt_date,
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
    """Tokenize and remove stopwords, then add adjacent-word bigrams.

    Bigrams (e.g. "ai_architecture", "harsh_vardhan") give BM25 a co-location
    signal that is absent from unigrams alone — a chunk where "AI" and
    "architecture" appear in separate sentences scores the same as one where
    the speaker said "AI architecture" as a phrase. Bigrams fix that.
    Their IDF is naturally high (rare compound tokens) so BM25 weights them
    strongly without any manual tuning.
    """
    tokens   = _normalize_for_bm25(text).split()
    unigrams = [t for t in tokens if t not in _BM25_STOPWORDS and len(t) > 1]
    bigrams  = [f"{a}_{b}" for a, b in zip(unigrams, unigrams[1:])]
    return unigrams + bigrams


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
    dense_docs:   list[Document],
    bm25_docs:    list[Document],
    rrf_k:        int   = 30,   # 60→30: k=30 ensures BM25 35% weight remains visible
                                # even at lower ranks. k=60+35% compressed BM25 too
                                # much — exact name matches lost rank → retrieval failed.
                                # k=30 is the original RRF paper value, k=60 was a
                                # conservative default for noisy web search — not right
                                # for meeting transcript semantic retrieval.
    dense_weight: float = 0.65, # dense dominates: meeting speech is informal, semantic
                                # search finds "I think that makes sense" as a decision;
                                # BM25 cannot match what has no keyword overlap.
    bm25_weight:  float = 0.35, # BM25 still contributes for exact names ("Harsh Vardhan"),
                                # technical terms ("hybrid search", "Module 4"), and any
                                # chunk where the user's keyword literally appears.
) -> tuple[list[Document], dict]:
    """
    Weighted Reciprocal Rank Fusion: score = Σ weight / (rrf_k + rank).

    Dense and BM25 contribute with different weights because meeting transcripts
    are informal speech — semantic search (dense) is more reliable than keyword
    matching (BM25) for this data. A chunk in BOTH lists gets both contributions
    (0.65 + 0.35 = 1.0), which is the strongest possible signal.

    Returns (merged_by_score_desc, overlap_stats).
    """
    scores:      dict[str, float]    = {}
    doc_map:     dict[str, Document] = {}
    dense_rank:  dict[str, int]      = {}   # for tie-breaking: prefer lower dense rank
    dense_ids:   set[str] = set()
    bm25_ids:    set[str] = set()

    for rank, doc in enumerate(dense_docs):
        cid = doc.metadata.get("chunk_id", str(id(doc)))
        scores[cid]     = scores.get(cid, 0.0) + dense_weight / (rrf_k + rank + 1)
        doc_map[cid]    = doc
        dense_rank[cid] = rank   # store dense rank for tie-breaking
        dense_ids.add(cid)

    for rank, doc in enumerate(bm25_docs):
        cid = doc.metadata.get("chunk_id", str(id(doc)))
        scores[cid]  = scores.get(cid, 0.0) + bm25_weight / (rrf_k + rank + 1)
        doc_map[cid] = doc
        bm25_ids.add(cid)

    overlap = dense_ids & bm25_ids
    stats   = {
        "dense_only":   len(dense_ids - overlap),
        "bm25_only":    len(bm25_ids  - overlap),
        "overlap":      len(overlap),
        "dense_weight": dense_weight,
        "bm25_weight":  bm25_weight,
        "rrf_k":        rrf_k,
    }

    # Tie-breaking: equal RRF scores → prefer dense-retrieved chunks (lower dense rank
    # wins). BM25-only chunks (not in dense list) get rank=infinity → sorted last.
    # This is intentional: dense = semantic understanding, BM25 = keyword match.
    # When equally scored, semantic match is the more reliable signal.
    sorted_ids = sorted(
        scores,
        key=lambda cid: (-scores[cid], dense_rank.get(cid, float("inf"))),
    )
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


# ── Side-by-side Dense vs BM25 comparison table ───────────────────────────────

def _log_side_by_side(
    dense_docs:  list,
    bm25_docs:   list,
    bm25_tokens: list,
    dense_query: str,
) -> None:
    """
    Log Dense and BM25 results in two parallel columns so you can read both
    lists at the same time and immediately see overlaps vs misses.

    Column layout (113 chars wide):
      #rank  Dense: speaker · meeting · date / status / text   │  #rank  BM25: same fields

    Status indicators (Dense column):
      🟣 OVERLAP  — this chunk also appears in BM25 at rank N
      ❌ BM25 miss — BM25 never found it; shows which query tokens are absent

    Status indicators (BM25 column):
      🎯 matched   — which query tokens triggered BM25 to return this chunk
      🟣 in dense  — this BM25 chunk also appears in the Dense list
      🟠 BM25-only — BM25 found it but Dense did not
    """
    C = 46  # content chars per column (after rank prefix)
    R = 4   # rank prefix width

    # ── Pre-compute per-chunk lookups ────────────────────────────────────────
    bm25_rank_of: dict = {}
    bm25_matched: dict = {}
    for i, doc in enumerate(bm25_docs):
        cid = doc.metadata.get("chunk_id", str(id(doc)))
        bm25_rank_of[cid] = i + 1
        ctoks = set(_tokenize(doc.page_content))
        bm25_matched[cid] = [t for t in bm25_tokens if t in ctoks]

    dense_cid_set = {d.metadata.get("chunk_id", str(id(d))) for d in dense_docs}

    # ── Cell formatter ───────────────────────────────────────────────────────
    def _fit(s, n: int = C) -> str:
        s = str(s)
        return (s[: n - 1] + "…") if len(s) > n else s.ljust(n)

    # ── Entry builders — return exactly 3 lines each ─────────────────────────
    def _dense_entry(doc) -> tuple:
        m       = doc.metadata
        cid     = m.get("chunk_id", str(id(doc)))
        speaker = m.get("speaker_name", "?")[:18]
        date    = _fmt_date(m.get("meeting_date"))
        mtg     = m.get("meeting_title", "?")[:18]
        preview = doc.page_content.replace("\n", " ").strip()

        if cid in bm25_rank_of:
            toks   = bm25_matched.get(cid, [])
            status = "🟣 OVERLAP  BM25 #%-2d  tokens:%s" % (bm25_rank_of[cid], toks[:3])
        else:
            ctoks  = set(_tokenize(doc.page_content))
            miss   = [t for t in bm25_tokens if t not in ctoks]
            status = ("❌ miss  no tokens: %s" % miss[:3]) if miss else "❌ miss  low IDF (tokens present)"

        return (
            _fit("%s  ·  %s  (%s)" % (speaker, mtg, date)),
            _fit(status),
            _fit('"%s"' % preview[:C - 3]),
        )

    def _bm25_entry(doc) -> tuple:
        m       = doc.metadata
        cid     = m.get("chunk_id", str(id(doc)))
        speaker = m.get("speaker_name", "?")[:18]
        date    = _fmt_date(m.get("meeting_date"))
        mtg     = m.get("meeting_title", "?")[:18]
        toks    = bm25_matched.get(cid, [])
        flag    = "🟣 in dense" if cid in dense_cid_set else "🟠 BM25-only"
        status  = "🎯 matched:%s  %s" % (toks[:4], flag)
        preview = doc.page_content.replace("\n", " ").strip()

        return (
            _fit("%s  ·  %s  (%s)" % (speaker, mtg, date)),
            _fit(status),
            _fit('"%s"' % preview[:C - 3]),
        )

    def _blank_entry() -> tuple:
        return (_fit(""), _fit("(no chunk at this rank)"), _fit(""))

    # ── Table structure ───────────────────────────────────────────────────────
    W       = R + 2 + C           # one column width
    BAR     = "═" * W
    THIN    = "─" * W
    HDR_SEP = "  " + BAR + "═╪═" + BAR
    ROW_SEP = "  " + THIN + "─┼─" + THIN

    def _line(rk_d, dl, rk_b, bl):
        return "  %-*s  %s  │  %-*s  %s" % (R, rk_d, dl, R, rk_b, bl)

    # ── Emit header ──────────────────────────────────────────────────────────
    logger.info(HDR_SEP)
    logger.info(_line(
        "🔵",
        _fit("DENSE  [%d chunks]   query: %r" % (len(dense_docs), dense_query[:34])),
        "🟠",
        _fit("BM25   [%d chunks]" % len(bm25_docs)),
    ))
    logger.info(_line(
        "",
        _fit("semantic — finds conceptually related text"),
        "",
        _fit("tokens: %s" % bm25_tokens[:6]),
    ))
    logger.info(HDR_SEP)
    logger.info(_line(
        "#",
        _fit("Speaker  ·  Meeting  (Date)  /  Status  /  Text"),
        "#",
        _fit("Speaker  ·  Meeting  (Date)  /  Tokens  /  Text"),
    ))
    logger.info(ROW_SEP)

    # ── One row per rank position ─────────────────────────────────────────────
    n_rows = max(len(dense_docs), len(bm25_docs))
    for i in range(n_rows):
        d_doc = dense_docs[i] if i < len(dense_docs) else None
        b_doc = bm25_docs[i]  if i < len(bm25_docs)  else None

        d_lines = _dense_entry(d_doc) if d_doc else _blank_entry()
        b_lines = _bm25_entry(b_doc)  if b_doc else _blank_entry()

        d_rank = "#%d" % (i + 1) if d_doc else ""
        b_rank = "#%d" % (i + 1) if b_doc else ""

        for li in range(3):
            rk_d = d_rank if li == 0 else ""
            rk_b = b_rank if li == 0 else ""
            logger.info(_line(rk_d, d_lines[li], rk_b, b_lines[li]))

        logger.info(_line("", _fit(""), "", _fit("")))
        if i < n_rows - 1:
            logger.info(ROW_SEP)

    logger.info(HDR_SEP)


def hybrid_retrieve(
    query: str,
    project_id: str,
    hard_filters: Optional[dict] = None,
    date_where: Optional[dict] = None,
    k: int = 25,
    dense_query: Optional[str] = None,
) -> list[Document]:
    """
    Hybrid retrieval: dense vector search + BM25, merged via RRF.

    hard_filters: applied to BOTH stages (e.g. meeting_id, speaker_name).
    date_where: pre-built ChromaDB clause from parse_meeting_scope() — scopes
      retrieval to specific meeting(s) or a date range.
    k: adaptive — caller passes from get_retrieval_config().
    dense_query: if provided, used for dense vector search instead of query.
      Lets callers pass the full natural-language PM question for semantic
      search while keeping a cleaned keyword form in query for BM25.
    """
    query      = _validate_query(query)
    project_id = _validate_project_id(project_id)
    _dense_q   = dense_query.strip() if dense_query and dense_query.strip() else query

    # ── Stage 1a: dense vector search ────────────────────────────────────────
    import os as _os
    _DENSE_MIN_SCORE = float(_os.getenv("DENSE_MIN_SCORE", "0.0"))

    dense_filter = _build_filter(project_id, hard_filters, date_where)
    vectorstore  = get_vectorstore()
    scored       = vectorstore.similarity_search_with_relevance_scores(
        query=_dense_q, k=k, filter=dense_filter
    )
    # Stamp each doc with its cosine similarity score for logging + filtering
    for doc, score in scored:
        doc.metadata["_dense_score"] = round(score, 3)

    # Log full score distribution BEFORE any filtering — shows where all k chunks sit
    if scored:
        all_scores = [s for _, s in scored]
        s_min    = min(all_scores)
        s_max    = max(all_scores)
        s_avg    = sum(all_scores) / len(all_scores)
        above_55 = sum(1 for s in all_scores if s >= 0.55)
        above_50 = sum(1 for s in all_scores if s >= 0.50)
        above_45 = sum(1 for s in all_scores if s >= 0.45)
        above_40 = sum(1 for s in all_scores if s >= 0.40)
        logger.info(
            "   📊 ALL %d chunks — min=%.3f  max=%.3f  avg=%.3f  | ≥0.55:%d  ≥0.50:%d  ≥0.45:%d  ≥0.40:%d",
            len(all_scores), s_min, s_max, s_avg, above_55, above_50, above_45, above_40,
        )
        # Per-chunk score ladder so you can see exactly where each chunk sits
        logger.info("   📈 scores: %s", "  ".join("%.3f" % s for s in all_scores))

    # Apply minimum score threshold when set (env DENSE_MIN_SCORE > 0).
    # Without a threshold, k=40 guarantees noise — chunks 35-40 have cosine
    # similarity ≈0.3 with the query topic, the same as a barely-related sentence.
    if _DENSE_MIN_SCORE > 0:
        before  = len(scored)
        scored  = [(d, s) for d, s in scored if s >= _DENSE_MIN_SCORE]
        dropped = before - len(scored)
        if dropped:
            logger.info(
                "  dense: threshold=%.2f kept %d/%d chunks (dropped %d)",
                _DENSE_MIN_SCORE, len(scored), before, dropped,
            )

    raw_dense  = [d for d, _ in scored]
    dense_docs = [d for d in raw_dense if not d.metadata.get("is_meeting_summary")]
    if len(raw_dense) != len(dense_docs):
        logger.info("  dense: dropped %d summary chunk(s)", len(raw_dense) - len(dense_docs))

    logger.info("🔵 DENSE  [%d chunks]  query: %r", len(dense_docs), _dense_q[:80])
    logger.info("   " + "─" * 65)
    for i, doc in enumerate(dense_docs, 1):
        m     = doc.metadata
        txt   = doc.page_content.replace("\n", " ").strip()
        score = m.get("_dense_score", 0.0)
        sigs  = "  ".join(
            f"✅{s}" for s, k_ in [
                ("decision",   "contains_decision"),
                ("commit",     "contains_commitment"),
                ("question",   "contains_question"),
            ] if m.get(k_)
        ) or "—"
        logger.info(
            "   [%d/%d] 👤 %-22s  📅 %s  🏢 %-38s  🎯 score=%.3f",
            i, len(dense_docs),
            m.get("speaker_name", "?"),
            _fmt_date(m.get("meeting_date")),
            m.get("meeting_title", "?")[:38],
            score,
        )
        logger.info("          🔖 %s", sigs)
        logger.info("          💬 %s", txt[:280])
        logger.info("          " + "·" * 58)

    # ── Stage 1b: BM25 keyword search ────────────────────────────────────────
    bm25_tokens = _tokenize(query)
    corpus      = _fetch_project_corpus(project_id, hard_filters, date_where)
    bm25_docs   = _bm25_search(query, corpus, k=k)

    logger.info("🟠 BM25   [%d chunks]  corpus: %d docs", len(bm25_docs), len(corpus))
    logger.info("   📌 BM25 query tokens: %s", bm25_tokens)
    if not bm25_docs:
        logger.info("   ⚠️  BM25 returned 0 results — none of the tokens above appear in any chunk")
    logger.info("   " + "─" * 65)
    for i, doc in enumerate(bm25_docs, 1):
        m           = doc.metadata
        txt         = doc.page_content.replace("\n", " ").strip()
        chunk_toks  = set(_tokenize(doc.page_content))
        matched     = [t for t in bm25_tokens if t in chunk_toks]
        logger.info(
            "   [%d/%d] 👤 %-22s  📅 %s  🏢 %s",
            i, len(bm25_docs),
            m.get("speaker_name", "?"),
            _fmt_date(m.get("meeting_date")),
            m.get("meeting_title", "?")[:38],
        )
        logger.info("          🎯 matched tokens: %s", matched)
        logger.info("          💬 %s", txt[:280])
        logger.info("          " + "·" * 58)

    # ── Side-by-side comparison table ────────────────────────────────────────
    _log_side_by_side(dense_docs, bm25_docs, bm25_tokens, _dense_q)

    # ── Stage 2: RRF merge ────────────────────────────────────────────────────
    merged, stats = _rrf_merge(dense_docs, bm25_docs)
    logger.info(
        "⚗️  RRF MERGE  total=%d | 🔵 dense_only=%d | 🟠 bm25_only=%d | 🟣 overlap=%d | weights=%.2f/%.2f",
        len(merged), stats["dense_only"], stats["bm25_only"], stats["overlap"],
        stats["dense_weight"], stats["bm25_weight"],
    )

    result = merged[:k]
    _log_chunk_list("🏆 HYBRID RESULT (top %d after RRF)" % k, result)
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


def speaker_hybrid_retrieve(
    query: str,
    project_id: str,
    speaker_name: str,
    other_hard_filters: Optional[dict] = None,
    date_where: Optional[dict] = None,
    k: int = 25,
    dense_query: Optional[str] = None,
) -> list[Document]:
    """
    Two-pass speaker retrieval covering both chunk types.

    Pass A: hybrid_retrieve with speaker_name=$eq → atomic chunks where speaker spoke.
    Pass B: dialogue_group corpus post-filtered by the pipe-separated speakers field,
            then BM25 + dense within that subset, RRF merged.
    Final:  equal-weight RRF of A + B, deduplicated, top k returned.

    Needed because dialogue_group chunks have speaker_name="" (multi-speaker) so an
    exact speaker_name filter silently drops all cross-speaker exchange chunks.
    """
    query      = _validate_query(query)
    project_id = _validate_project_id(project_id)
    _dense_q   = (dense_query or query).strip()

    # ── Pass A: atomic chunks (speaker_name exact match) ─────────────────────
    filters_a = {"speaker_name": speaker_name}
    if other_hard_filters:
        filters_a.update(other_hard_filters)

    atomic_docs = hybrid_retrieve(
        query=query,
        project_id=project_id,
        hard_filters=filters_a,
        date_where=date_where,
        k=k,
        dense_query=dense_query,
    )

    # ── Pass B: dialogue_group chunks where speaker participated ─────────────
    dg_corpus_all = _fetch_project_corpus(
        project_id,
        hard_filters={"chunk_type": "dialogue_group"},
        date_where=date_where,
    )
    dg_corpus = [
        doc for doc in dg_corpus_all
        if speaker_name in (doc.metadata.get("speakers") or "").split("|")
    ]
    logger.info(
        "  speaker_hybrid: %d/%d dialogue_group chunks contain speaker=%s",
        len(dg_corpus), len(dg_corpus_all), speaker_name,
    )

    if not dg_corpus:
        return atomic_docs

    # BM25 within the speaker's dialogue_group chunks
    bm25_dg = _bm25_search(query, dg_corpus, k=k)

    # Dense: search all dialogue_group chunks in scope, then post-filter by speakers
    dg_filter  = _build_filter(project_id, {"chunk_type": "dialogue_group"}, date_where)
    vectorstore = get_vectorstore()
    raw_dense_dg = vectorstore.similarity_search(query=_dense_q, k=k, filter=dg_filter)
    dense_dg = [
        d for d in raw_dense_dg
        if speaker_name in (d.metadata.get("speakers") or "").split("|")
        and not d.metadata.get("is_meeting_summary")
    ]

    merged_dg, dg_stats = _rrf_merge(dense_dg, bm25_dg)
    logger.info(
        "  speaker_hybrid: dg RRF → dense_only=%d bm25_only=%d overlap=%d total=%d",
        dg_stats["dense_only"], dg_stats["bm25_only"], dg_stats["overlap"], len(merged_dg),
    )

    # ── Final merge: equal-weight RRF of atomic + dialogue_group ─────────────
    final_merged, final_stats = _rrf_merge(
        atomic_docs, merged_dg, dense_weight=0.5, bm25_weight=0.5
    )
    logger.info(
        "  speaker_hybrid: final → atomic=%d dg=%d merged=%d returned=%d",
        len(atomic_docs), len(merged_dg), len(final_merged), min(len(final_merged), k),
    )
    return final_merged[:k]


# ── Legacy signal wrappers (backward compat) ──────────────────────────────────
# Superseded by hybrid_retrieve() with hard_filters. Kept for older scripts.

def retrieve_commitment_documents(query: str, project_id: str, k: int = DEFAULT_TOP_K) -> list[Document]:
    return retrieve_documents(query, project_id, filters={"contains_commitment": True}, k=k)


def retrieve_question_documents(query: str, project_id: str, k: int = DEFAULT_TOP_K) -> list[Document]:
    return retrieve_documents(query, project_id, filters={"contains_question": True}, k=k)


def retrieve_decision_candidates(query: str, project_id: str, k: int = DEFAULT_TOP_K) -> list[Document]:
    return retrieve_documents(query, project_id, filters=None, k=k)
