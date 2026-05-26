"""
query_scope.py — Deterministic meeting scope resolver.

Runs ONCE before the agent node. Reads the original query, applies
regex patterns, and writes 4 fields into state:

  scope_where   — ChromaDB where-clause passed to hybrid_retrieve as date_where.
  scope_ids     — Flat list of resolved meeting IDs (None for date_range / project).
  scope_type    — "project" | "meeting" | "date_range"
  recommended_k — Minimum k for search_transcripts, based on how many meetings
                  are in scope. Prevents under-fetching on project-wide queries.

No LLM call here — pure Python. ~50ms.
"""

import logging
from typing import Optional

from app.services.answer.scope import parse_meeting_scope
from langchain_core.messages import HumanMessage
from .state import AgentState

logger = logging.getLogger(__name__)


def _extract_scope_ids(scope_where: Optional[dict]) -> Optional[list]:
    """Pull meeting IDs out of the scope_where clause as a flat list.

    Returns None for date_range (no specific IDs) or project-wide (no clause).
    """
    if scope_where is None:
        return None

    meeting_clause = scope_where.get("meeting_id")
    if not meeting_clause:
        return None                          # date_range — no specific IDs

    if "$eq" in meeting_clause:
        return [meeting_clause["$eq"]]       # single meeting → list of 1

    if "$in" in meeting_clause:
        return list(meeting_clause["$in"])   # multiple meetings

    return None


def _compute_recommended_k(scope_type: str, scope_ids: Optional[list]) -> int:
    """Return the minimum k that search_transcripts should use.

    Why this matters:
      - Project-wide corpus is ~1,659 chunks across 10 meetings.
      - k=15 only covers 0.9% of that — easy to miss things.
      - A single meeting has ~150 chunks, so k=15 is fine (10% coverage).

    Formula:
      project-wide   → 25  (max, broad coverage needed)
      1 meeting      → 15  (sufficient for ~150 chunks)
      2 meetings     → 20
      3+ meetings    → 25
      date_range     → 20  (unknown size, use medium coverage)
    """
    if scope_type == "project":
        return 25

    if scope_type == "meeting":
        n = len(scope_ids) if scope_ids else 1
        # 1 meeting → 15, 2 → 20, 3 or more → 25
        return min(15 + (n - 1) * 5, 25)

    if scope_type == "date_range":
        return 20

    return 15   # safe default


def query_scope_node(state: AgentState) -> dict:
    """Resolve meeting scope from the user's original query.

    Reads the first HumanMessage, runs regex patterns to detect scope phrases
    ("last meeting", "previous 3 meetings", "May 9th", etc.), and writes
    scope fields + recommended_k into state.

    Does NOT touch messages — only adds scope fields.
    """
    # Find the original query (first HumanMessage in the thread)
    query = ""
    for msg in state["messages"]:
        if isinstance(msg, HumanMessage):
            query = msg.content
            break

    project_id  = state["project_id"]
    scope_where = parse_meeting_scope(query, project_id)
    scope_ids   = _extract_scope_ids(scope_where)

    # Label the scope type
    if scope_where is None:
        scope_type = "project"
    elif "meeting_date" in scope_where:
        scope_type = "date_range"
    else:
        scope_type = "meeting"

    recommended_k = _compute_recommended_k(scope_type, scope_ids)

    logger.info(
        "query_scope | type=%-10s | ids=%s | recommended_k=%d | where=%s",
        scope_type, scope_ids, recommended_k, scope_where,
    )

    return {
        "scope_where":   scope_where,
        "scope_ids":     scope_ids,
        "scope_type":    scope_type,
        "recommended_k": recommended_k,
    }
