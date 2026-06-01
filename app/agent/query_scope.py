"""
query_scope.py — Meeting scope resolver node for the production agent pipeline.

Runs ONCE before the agent node. Writes scope fields into AgentState:
  scope_where, scope_ids, scope_type, recommended_k

REPLACED: the old regex-only parse_meeting_scope() approach.
NOW USES:  two-stage LLM resolver (app/agent/scope_llm.py).

The old regex function (parse_meeting_scope) still lives in app/core/scope.py
and is used by the deprecated app/rag/ pipeline — it is NOT touched here.

Key fixes applied here
----------------------
  FIX (first-vs-last): reads the LAST HumanMessage, not the first.
    With chat history in state["messages"] the first HumanMessage is from
    the oldest turn. The current query is always the last one.

  M6 GUARD: empty/whitespace query → project-wide immediately, no LLM call.
    Streamlit prevents empty input but direct API callers may not.
"""

import logging
from typing import Optional

from langchain_core.messages import HumanMessage

from app.agent.scope_llm import resolve_scope
from app.agent.chat_store import get_chat_store
from app.agent.state import AgentState

logger = logging.getLogger(__name__)


def query_scope_node(state: AgentState) -> dict:
    """
    Resolve meeting scope from the current query using the LLM scope resolver.

    Steps
    -----
    A. Read the LAST HumanMessage (the current query — not an older history turn).
    B. M6 guard: if query is empty/whitespace → project-wide, no LLM call.
    C. Call resolve_scope() — two-stage LLM + scope_parser.
    D. Write scope fields into state.
    """
    # A. Read LAST HumanMessage
    query = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            query = msg.content
            break

    # B. M6 guard — empty query
    if not query.strip():
        logger.warning("[2] SCOPE    — empty query, defaulting to project-wide")
        return {
            "scope_where":   None,
            "scope_ids":     None,
            "scope_type":    "project",
            "recommended_k": 25,
        }

    logger.info("[2] SCOPE    — resolving: %r", query[:100])

    project_id = state["project_id"]
    session_id = state.get("session_id")   # None when DATABASE_URL not set

    # C. Two-stage LLM scope resolution
    result = resolve_scope(
        query=query,
        project_id=project_id,
        session_id=session_id,
        chat_store=get_chat_store(),   # None-safe — resolve_scope handles it
    )

    # D. Log and return
    logger.info(
        "[2] SCOPE    — resolved | type=%-12s  ids=%-30s  k=%d",
        result["scope_type"],
        str(result["scope_ids"]),
        result["recommended_k"],
    )
    return result