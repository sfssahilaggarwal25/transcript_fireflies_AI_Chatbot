"""
utils/ — Agent tool utilities package.

Re-exports everything so tools.py import stays unchanged:
    from .utils import (...)

Modules
-------
  constants.py   signal maps, thresholds, fmt_date, _fmt_ts
  presets.py     RETRIEVAL_PRESETS, select_preset
  accumulator.py per-request doc collection and citation numbering
  expansion.py   neighbor chunk expansion (pre-rerank + post-rerank)
  search.py      speaker resolver, exhaustive signal scan, diversity cap
"""

from .constants import (
    _SIGNAL_MAP,
    _HARD_SIGNAL_FILTERS,
    _SOFT_SIGNAL_FILTERS,
    _SOFT_SIGNAL_PREFIX,
    _ROLE_LABEL,
    _EXPAND_TOP_N,
    SHORT_CHUNK_THRESHOLD,
    fmt_date,
    _fmt_ts,
)

from .presets import (
    RETRIEVAL_PRESETS,
    select_preset,
)

from .accumulator import (
    reset_doc_accumulator,
    get_accumulated_docs,
    _append_docs,
)

from .expansion import (
    _fetch_neighbor,
    _expand_short_chunks_for_reranking,
    _expand_context,
)

from .search import (
    _apply_diversity_cap,
    _resolve_speaker_name,
    _exhaustive_signal_search,
)

__all__ = [
    # constants
    "_SIGNAL_MAP",
    "_HARD_SIGNAL_FILTERS",
    "_SOFT_SIGNAL_FILTERS",
    "_SOFT_SIGNAL_PREFIX",
    "_ROLE_LABEL",
    "_EXPAND_TOP_N",
    "SHORT_CHUNK_THRESHOLD",
    "fmt_date",
    "_fmt_ts",
    # presets
    "RETRIEVAL_PRESETS",
    "select_preset",
    # accumulator
    "reset_doc_accumulator",
    "get_accumulated_docs",
    "_append_docs",
    # expansion
    "_fetch_neighbor",
    "_expand_short_chunks_for_reranking",
    "_expand_context",
    # search
    "_apply_diversity_cap",
    "_resolve_speaker_name",
    "_exhaustive_signal_search",
]