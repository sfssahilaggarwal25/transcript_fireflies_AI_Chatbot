"""
retrieval/__init__.py — Public API for the retrieval package.

Internal file layout:
  config.py           RetrievalConfig + get_retrieval_config()
  base.py             _validate_*, _build_filter, _fetch_project_corpus, _log_chunk_list
  hybrid.py           BM25/RRF internals + hybrid_retrieve + compound_retrieve + retrieve_documents
  metadata_retrieve.py analytical_retrieve + contribution_retrieve + signal_fetch_retrieve
  topic.py            topic_summary_retrieve + retrieve_timeline_documents
  reranker.py         rerank_documents (unchanged)

Import from this package:
  from app.core.retrieval import hybrid_retrieve, compound_retrieve, ...
"""

from .config import RetrievalConfig, get_retrieval_config
from .hybrid import (
    hybrid_retrieve,
    compound_retrieve,
    retrieve_documents,
    retrieve_commitment_documents,
    retrieve_question_documents,
    retrieve_decision_candidates,
)
from .metadata_retrieve import analytical_retrieve, contribution_retrieve, signal_fetch_retrieve
from .topic import topic_summary_retrieve, retrieve_timeline_documents

__all__ = [
    # Config
    "RetrievalConfig",
    "get_retrieval_config",
    # Core retrieval
    "hybrid_retrieve",
    "compound_retrieve",
    "retrieve_documents",
    # Metadata aggregation
    "analytical_retrieve",
    "contribution_retrieve",
    "signal_fetch_retrieve",
    # Per-meeting search
    "topic_summary_retrieve",
    "retrieve_timeline_documents",
    # Legacy signal wrappers (kept for backward compat)
    "retrieve_commitment_documents",
    "retrieve_question_documents",
    "retrieve_decision_candidates",
]
