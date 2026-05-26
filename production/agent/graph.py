"""
graph.py — LangGraph agent graph for the production pipeline.

Graph structure:

    START
      │
      ▼
   ┌─────────────┐
   │ query_scope │  — Deterministic. Runs ONCE. Resolves meeting scope from the
   └─────────────┘    query using regex (parse_meeting_scope). Stores the result
      │                in state["scope_where"] as a ChromaDB where-clause.
      │                No LLM call. ~50ms. Zero API cost.
      │
      ▼
   ┌───────┐   has tool_calls   ┌───────┐
   │ agent │ ─────────────────► │ tools │
   │ (LLM) │                    └───────┘
   └───────┘ ◄──────────────────────┘
      │         ToolMessages (loop)
      │ no tool_calls
      ▼
     END

Node responsibilities:
  query_scope  — Python-only. Resolves "last meeting", "first meeting",
                 "the third meeting", "May 9th", "last 3 meetings" etc.
                 to a ChromaDB meeting_id / date filter. Stored in
                 state["scope_where"]. Tools read this via InjectedState
                 and pass it to hybrid_retrieve as date_where.

  agent        — Calls the LLM with all tools bound. LLM decides which
                 tools to call and with what arguments. Runs on every
                 iteration of the ReAct loop.

  tools        — ToolNode (prebuilt). Executes tool calls from the last
                 AIMessage. Injects state (project_id, scope_where) into
                 each tool via InjectedState. Returns ToolMessages.

project_id enforcement:
  Tools use InjectedState to read project_id from the graph state.
  The LLM's tool arguments are NEVER trusted for project_id — it is
  injected server-side from the state that was set at graph entry.

scope_where enforcement:
  query_scope resolves meeting scope deterministically before the LLM runs.
  Tools read scope_where from state via InjectedState — the LLM never
  controls which meetings are searched.
"""

import logging
import os
from functools import lru_cache

from langchain_core.messages import SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from .prompts import SYSTEM_PROMPT
from .state import AgentState
from .tools import TOOLS
from .query_scope import query_scope_node
from app.services.storage.db import get_raw_collection

logger = logging.getLogger(__name__)

# ── Model config ──────────────────────────────────────────────────────────────

_AGENT_MODEL    = "gemini-2.5-flash"
_MAX_ITERATIONS = 6   # max tool-call rounds before forcing a final answer


# ── Scope label helper ────────────────────────────────────────────────────────

def _resolve_scope_labels(project_id: str, scope_ids: list) -> str:
    """Convert a list of meeting IDs into a human-readable string.

    Example output: "'Nolocode Meeting #7' (2026-04-22), 'Nolocode Meeting #8' (2026-04-23)"

    Falls back to raw IDs if the DB lookup fails.
    """
    try:
        collection = get_raw_collection()
        labels = []
        for mid in scope_ids:
            res = collection.get(
                where={
                    "$and": [
                        {"project_id": {"$eq": project_id}},
                        {"meeting_id":  {"$eq": mid}},
                    ]
                },
                include=["metadatas"],
                limit=1,
            )
            metas = res.get("metadatas", [])
            if metas:
                title = metas[0].get("meeting_title", mid)
                date  = metas[0].get("meeting_date", "")
                labels.append(f"'{title}' ({date})")
            else:
                labels.append(mid)
        return ", ".join(labels)
    except Exception:
        return str(scope_ids)


# ── Nodes ─────────────────────────────────────────────────────────────────────

def _build_llm() -> ChatGoogleGenerativeAI:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")
    return ChatGoogleGenerativeAI(
        model=_AGENT_MODEL,
        google_api_key=api_key,
        temperature=0,
    )


def _make_call_llm(llm_with_tools):
    """Return a node function that calls the LLM (with tools bound)."""

    def call_llm(state: AgentState) -> dict:
        scope_type = state.get("scope_type", "project")
        scope_ids  = state.get("scope_ids")
        project_id = state.get("project_id", "")

        # Tell the LLM which meeting(s) are in scope — in plain English, not raw IDs.
        # This prevents the LLM from wasting a tool call on list_meetings.
        scope_note = ""
        if scope_type == "meeting" and scope_ids:
            readable = _resolve_scope_labels(project_id, scope_ids)
            scope_note = (
                f"\n\nSCOPE ALREADY RESOLVED: This query is limited to {readable}. "
                f"Do NOT call list_meetings — the scope is already applied. "
                f"All tools will automatically restrict results to this meeting."
            )
        elif scope_type == "date_range":
            scope_note = (
                "\n\nSCOPE ALREADY RESOLVED: A date-range filter is active. "
                "All tools will automatically restrict results to meetings within that range."
            )

        system   = SystemMessage(content=SYSTEM_PROMPT + scope_note)
        messages = [system] + list(state["messages"])

        logger.debug("call_llm | messages=%d", len(messages))
        response = llm_with_tools.invoke(messages)

        tool_calls = getattr(response, "tool_calls", [])
        logger.info(
            "llm response | tool_calls=%d | content_len=%d",
            len(tool_calls),
            len(str(response.content)),
        )
        return {"messages": [response]}

    return call_llm


# ── Conditional edge ──────────────────────────────────────────────────────────

def _should_continue(state: AgentState) -> str:
    """
    Route to 'tools' if the LLM issued tool calls, else to END.

    Iteration guard: count how many ToolMessages are already in the state.
    If >= _MAX_ITERATIONS rounds have happened, force END regardless — this
    prevents infinite loops on ambiguous or unanswerable queries.
    """
    last_msg = state["messages"][-1]
    has_calls = bool(getattr(last_msg, "tool_calls", []))

    if not has_calls:
        return END

    # Count completed tool rounds (each round adds ToolMessages)
    from langchain_core.messages import ToolMessage
    tool_rounds = sum(1 for m in state["messages"] if isinstance(m, ToolMessage))
    if tool_rounds >= _MAX_ITERATIONS:
        logger.warning("Max iterations (%d) reached — forcing END", _MAX_ITERATIONS)
        return END

    return "tools"


# ── Graph assembly ────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_graph():
    """
    Build and compile the agent graph (singleton — built once per process).

    lru_cache ensures we don't re-initialize the LLM or rebuild the graph
    on every request.
    """
    llm         = _build_llm()
    llm_w_tools = llm.bind_tools(TOOLS)
    call_llm    = _make_call_llm(llm_w_tools)
    tools_node  = ToolNode(TOOLS)   # handles InjectedState automatically

    builder = StateGraph(AgentState)
    builder.add_node("query_scope", query_scope_node)
    builder.add_node("agent", call_llm)
    builder.add_node("tools", tools_node)

    builder.add_edge(START, "query_scope")
    builder.add_edge("query_scope", "agent")
    builder.add_conditional_edges(
        "agent",
        _should_continue,
        {"tools": "tools", END: END},
    )
    builder.add_edge("tools", "agent")

    graph = builder.compile()
    logger.info("Production graph compiled | model=%s | tools=%d", _AGENT_MODEL, len(TOOLS))
    return graph
