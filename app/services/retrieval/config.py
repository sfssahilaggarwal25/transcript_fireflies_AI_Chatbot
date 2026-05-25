"""
config.py — Adaptive retrieval parameters.

Computes k values once per query based on scope size and retrieval mode.
Passed from pipeline._retrieve_for_understanding() into retrieval functions.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class RetrievalConfig:
    """
    k_dense / k_bm25 : candidates fetched in each search stage
    k_final          : what the retrieval function returns to the pipeline
    k_per_meeting    : per-meeting budget for topic_summary and timeline modes
    """
    k_dense:       int
    k_bm25:        int
    k_final:       int
    k_per_meeting: int


def get_retrieval_config(
    mode: str,
    scope_meeting_ids: Optional[list[str]],
    signal_filter: Optional[str] = None,
) -> RetrievalConfig:
    """
    Adaptive k — scope size and mode determine how many chunks to fetch.

    Core logic:
      n=0 (project-wide)  → large corpus  → moderate per-meeting, wider total
      n=1 (one meeting)   → small corpus  → go deep, fewer total needed
      n>1 (N meetings)    → shared budget → inverse relationship per meeting

    Pipeline context budget:
      Pipeline trims to top-10 after rerank + expand_context.
      k_final 15-25 is the sweet spot — reranker needs options, LLM needs 10.
      k_final > 30 is wasteful — chunks beyond 30 rarely survive to LLM.
    """
    n = len(scope_meeting_ids) if scope_meeting_ids else 0
    # n=0 = project-wide (count unknown, treat as large corpus)

    # ── compound: 3-pass speaker search ─────────────────────────────────────
    # Pass 1 fetches ALL speaker chunks (no k limit).
    # k_final controls what BM25 + dense each return before RRF merge.
    if mode == "compound":
        if n == 0:     k, k_final = 40, 25   # project-wide — speaker across many meetings
        elif n == 1:   k, k_final = 20, 15   # single meeting — small corpus
        else:          k, k_final = 30, 20   # 2-5 meetings
        if signal_filter:
            k_final = max(10, int(k_final * 0.7))  # signal narrows result set
        return RetrievalConfig(k_dense=k, k_bm25=k, k_final=k_final, k_per_meeting=0)

    # ── topic_summary: per-meeting hybrid search ─────────────────────────────
    # More meetings → fewer per meeting (shared context budget).
    # Single meeting → go deep (need thorough topic coverage).
    if mode == "topic_summary":
        if n == 0:     k_per = 6   # all meetings — conservative
        elif n == 1:   k_per = 15  # single meeting deep-dive
        elif n <= 3:   k_per = 10  # 2-3 meetings
        elif n <= 6:   k_per = 8   # 4-6 meetings
        else:          k_per = 6   # 7+ meetings
        return RetrievalConfig(k_dense=k_per, k_bm25=k_per, k_final=k_per * max(n, 5), k_per_meeting=k_per)

    # ── timeline: per-meeting dense search (no BM25) ─────────────────────────
    # Same inverse logic but shallower — timeline only needs representative chunks.
    if mode == "timeline":
        if n == 0:     k_per = 5
        elif n == 1:   k_per = 8
        elif n <= 3:   k_per = 6
        else:          k_per = 5
        return RetrievalConfig(k_dense=k_per, k_bm25=0, k_final=k_per * max(n, 5), k_per_meeting=k_per)

    # ── hybrid: BM25 + dense default ─────────────────────────────────────────
    # Single meeting → 20 (small corpus, sufficient).
    # Project-wide → 25 (gives reranker variety).
    if mode == "hybrid":
        k = 20 if n == 1 else 25
        return RetrievalConfig(k_dense=k, k_bm25=k, k_final=k, k_per_meeting=0)

    # ── fallback (analytical / contribution / summary / metadata ignore k) ───
    return RetrievalConfig(k_dense=25, k_bm25=25, k_final=25, k_per_meeting=8)
