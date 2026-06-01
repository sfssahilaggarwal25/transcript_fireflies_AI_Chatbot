"""
state.py — AgentState for the production LangGraph pipeline.

Fields
------
messages     — Full conversation thread (HumanMessage, AIMessage, ToolMessage).
               The add_messages reducer appends on every graph step.

project_id   — Immutable project scope. Set once at graph entry in service.py.
               NEVER modified by nodes or tools. Read by tools via InjectedState.

scope_where  — ChromaDB where-clause resolved by query_scope_node.
               Passed directly to hybrid_retrieve() as date_where.
               Format: {"meeting_id": {"$eq": "..."}}
                     | {"meeting_id": {"$in": [...]}}
                     | {"meeting_date": {"$gte": "..."}}
                     | None  (no scope → search all meetings)

scope_ids    — Flat list of resolved meeting IDs, or None.
               Extracted from scope_where by query_scope_node.
               Used by get_meeting_summaries() to filter summaries — simpler
               than merging scope_where into a nested $and filter.
               None when scope_type is "date_range" or "project".

scope_type   — Human-readable scope label. One of:
               "project"    → no scope phrase matched, search all meetings
               "meeting"    → scoped to one or more specific meeting IDs
               "date_range" → scoped to a date cutoff (last N days/weeks)
               Set by query_scope_node. Never changes after that.

recommended_k — Minimum chunk count the system recommends based on scope size.
               Computed by query_scope_node via _compute_recommended_k().
               search_transcripts enforces: effective_k = max(k, recommended_k).
               Prevents the LLM from under-fetching on project-wide queries.
               Default 15 (set in service.py initial_state).

session_id   — PostgreSQL session ID linking this graph run to a chat session.
               Set once at graph entry in service.py from the caller.
               Read by query_scope_node to load previous scope for inheritance.
               None when DATABASE_URL is not set or chat history is disabled.
               NEVER modified after initial_state is created.
"""

from typing import Annotated, List, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage


class AgentState(TypedDict):
    messages:      Annotated[list[AnyMessage], add_messages]
    project_id:    str
    session_id:    Optional[str]         # PostgreSQL session → scope inheritance
    scope_where:   Optional[dict]        # ChromaDB clause → hybrid_retrieve date_where
    scope_ids:     Optional[List[str]]   # flat meeting ID list → summaries filter
    scope_type:    str                   # "project" | "meeting" | "date_range"
    recommended_k: int                   # min k for search_transcripts (scope-based)
