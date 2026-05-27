"""app.agent — LangGraph-based agentic pipeline for AI Meeting Intelligence.

Approach 2: The LLM decides what to retrieve via multi-hop tool calling.
For the deterministic RAG pipeline (Approach 1), see app.rag.
"""
from .graph import get_graph
from .state import AgentState
from .tools import TOOLS, reset_doc_accumulator, get_accumulated_docs
from .service import answer_query

__all__ = [
    "get_graph",
    "AgentState",
    "TOOLS",
    "reset_doc_accumulator",
    "get_accumulated_docs",
    "answer_query",
]
