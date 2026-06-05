"""
presets.py — Retrieval preset system.

Maps query intent + scope to a named preset that controls k, rerank_top_n,
diversity_cap_floor, and sort order. select_preset() is the single entry point.
"""

from typing import Optional

# ── Preset table ──────────────────────────────────────────────────────────────
#
# k            : chunks fetched by hybrid_retrieve (ChromaDB + BM25 pool size)
# rerank_top_n : how many top chunks the reranker keeps before passing to LLM
#
# focused  — single-meeting scope: small corpus, precision beats recall
#            k=20 → diversity cap passes ~10 → reranker keeps best 8
# standard — project-wide topic/detail queries (~80% of all real queries)
#            k=40 → diversity cap passes ~20 → reranker keeps best 10
# broad    — overview/synthesis spanning all meetings, maximize recall
#            k=55 → diversity cap passes ~25 → reranker keeps best 12
# temporal — cross-meeting timeline queries: floor=6 guarantees per-meeting
#            coverage; sort_by=date preserves timeline order after reranking.
#
# Preset is chosen once per tool call by select_preset() — never by formula.
# This keeps cost, latency, and test assertions predictable.

RETRIEVAL_PRESETS: dict[str, dict] = {
    "focused":  {"k": 20, "rerank_top_n": 8,  "diversity_cap_floor": 3, "sort_by": "relevance"},
    "standard": {"k": 40, "rerank_top_n": 10, "diversity_cap_floor": 3, "sort_by": "relevance"},
    "broad":    {"k": 55, "rerank_top_n": 12, "diversity_cap_floor": 3, "sort_by": "relevance"},
    "temporal": {"k": 55, "rerank_top_n": 16, "diversity_cap_floor": 6, "sort_by": "date"},
}

# Words that signal a broad cross-meeting synthesis query → broad preset
_OVERVIEW_SIGNALS = frozenset({
    "overview", "all", "across", "throughout",
    "explain", "describe", "complete", "full", "entire",
    "summarize", "summary", "detail", "everything",
})

# Words that signal a temporal/evolution query → temporal preset.
# Checked before _OVERVIEW_SIGNALS so "across meetings" with "evolve" → temporal not broad.
# Scoped queries (scope_ids set) bypass both — focused always wins.
_TEMPORAL_SIGNALS = frozenset({
    "evolve", "evolution", "evolved",
    "progress", "changed", "changes",
    "over time", "across meetings",
    "history", "timeline",
    "how did", "develop", "when did", "what changed",
})


def select_preset(scope_ids: Optional[list], query: str) -> str:
    """
    Map scope + query signals to a retrieval preset name.

    focused  — scope_ids is set (specific meeting or explicit meeting list)
    temporal — project-wide query with evolution/timeline keywords
    broad    — project-wide query with overview/synthesis keywords
    standard — everything else; the safe default covering ~80% of queries
    """
    if scope_ids:
        return "focused"
    q = query.lower()
    if any(w in q for w in _TEMPORAL_SIGNALS):
        return "temporal"
    if any(w in q for w in _OVERVIEW_SIGNALS):
        return "broad"
    return "standard"