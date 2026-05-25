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

logger = logging.getLogger(__name__)

# ── Model config ──────────────────────────────────────────────────────────────
# gemini-2.5-flash: best balance of capability + speed for multi-step tool use.
# Falls back to gemini-2.0-flash if needed (both support function calling).

_AGENT_MODEL   = "gemini-2.5-flash"
_MAX_ITERATIONS = 6   # max tool-call rounds before forcing a final answer


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
        # Prepend system prompt as the first message every time
        scope_type = state.get("scope_type", "project")
        scope_ids  = state.get("scope_ids")
        
        scope_note = ""
        if scope_type == "meeting" and scope_ids:
            scope_note = f"\n\nSCOPE RESOLVED: This query is scoped to meeting(s): {scope_ids}. Do NOT call list_meetings — the scope is already known."
        elif scope_type == "date_range":
          scope_note = "\n\nSCOPE RESOLVED: This query uses a date-range filter already applied in retrieval."

        system = SystemMessage(content=SYSTEM_PROMPT + scope_note)
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
