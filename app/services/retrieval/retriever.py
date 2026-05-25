"""
retriever.py — Backward-compatibility shim.

This module's content has been split into focused files:
  config.py           → RetrievalConfig, get_retrieval_config
  base.py             → shared utilities (_validate_*, _build_filter, etc.)
  hybrid.py           → hybrid_retrieve, compound_retrieve, retrieve_documents
  metadata_retrieve.py → analytical_retrieve, contribution_retrieve
  topic.py            → topic_summary_retrieve, retrieve_timeline_documents

New code should import from the package:
  from app.services.retrieval import hybrid_retrieve, ...

This shim keeps existing scripts (check_timeline.py, trace_query.py) working.
"""
from app.services.retrieval import (  # noqa: F401
    RetrievalConfig,
    get_retrieval_config,
    hybrid_retrieve,
    compound_retrieve,
    retrieve_documents,
    retrieve_commitment_documents,
    retrieve_question_documents,
    retrieve_decision_candidates,
    analytical_retrieve,
    contribution_retrieve,
    topic_summary_retrieve,
    retrieve_timeline_documents,
)
