"""
query_scope.py — Deterministic meeting scope resolver.

Runs ONCE before the agent node. Reads the original query, applies
parse_meeting_scope() regex patterns, and writes three fields into state:

  scope_where  — ChromaDB where-clause, passed to hybrid_retrieve as date_where.
  scope_ids    — Flat list of resolved meeting IDs (None for date_range / project).
  scope_type   — "project" | "meeting" | "date_range"

Tools read all three via InjectedState.
  search_transcripts  → uses scope_where (passed to hybrid_retrieve)
  get_meeting_summaries → uses scope_ids (post-fetch filter)

If no scope pattern matches → scope_where=None, scope_ids=None, scope_type="project".
"""

import logging
from typing import Optional

from app.services.answer.scope import parse_meeting_scope
from langchain_core.messages import HumanMessage
from .state import AgentState

logger = logging.getLogger(__name__)


def _extract_scope_ids(scope_where: Optional[dict]) -> Optional[list]:
    """Pull the flat meeting ID list out of a scope_where clause."""
    if scope_where is None:
        return None
    meeting_clause = scope_where.get("meeting_id")
    if not meeting_clause:
        return None                          # date_range — no specific IDs
    if "$eq" in meeting_clause:
        return [meeting_clause["$eq"]]       # single meeting
    if "$in" in meeting_clause:
        return list(meeting_clause["$in"])   # multiple meetings
    return None


def query_scope_node(state: AgentState) -> dict:
    """
    Resolve meeting scope from the original query.
    Writes scope_where, scope_ids, scope_type — does not touch messages.
    """
    # Always read from the first HumanMessage (the original query)
    query = ""
    for msg in state["messages"]:
        if isinstance(msg, HumanMessage):
            query = msg.content
            break

    project_id  = state["project_id"]
    scope_where = parse_meeting_scope(query, project_id)
    scope_ids   = _extract_scope_ids(scope_where)

    # Determine scope type
    if scope_where is None:
        scope_type = "project"
    elif "meeting_date" in scope_where:
        scope_type = "date_range"
    else:
        scope_type = "meeting"

    logger.info(
        "query_scope | type=%-10s | ids=%s | where=%s",
        scope_type,
        scope_ids,
        scope_where,
    )

    return {
        "scope_where": scope_where,
        "scope_ids":   scope_ids,
        "scope_type":  scope_type,
    }
