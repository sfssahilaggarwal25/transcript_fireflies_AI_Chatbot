"""
service.py — Public entry point for the production LangGraph pipeline.

Usage
-----
    from production.service import answer_query

    result = answer_query(
        query      = "What did Bhavneet say about the forecasting timeline?",
        project_id = "proj_nolocode_001",
    )
    # result keys: answer, sources, tool_calls, model, error

Difference from app.services.answer_service.answer_question()
--------------------------------------------------------------
  - No fixed intent routing — the LLM decides what to retrieve
  - Handles ANY query, including cross-meeting synthesis and novel question types
  - Multi-hop: LLM can call multiple tools in sequence before answering
  - Returns tool_calls trace so the caller can show the "thinking process"
  - Sources are speaker/meeting-level (no [N] chunk citation numbers)

Compatibility
-------------
  The returned dict includes the same keys as the deterministic pipeline
  (answer, sources, intent, notice) so the existing Streamlit UI can render
  production results without modification.
"""

import logging
import time
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from production.agent import (
    get_graph,
    reset_doc_accumulator,
    get_accumulated_docs,
)
from app.services.answer.builder import format_timestamp

logger = logging.getLogger(__name__)


# ── Source extraction ─────────────────────────────────────────────────────────

def _build_sources(docs) -> list[dict]:
    """
    Convert accumulated LangChain Documents into the source dicts
    that Streamlit's render_sources() expects.

    Each chunk is its own source card — no deduplication.
    _global_chunk_num (set by _append_docs in tools.py) matches the [N]
    citations the LLM placed in the answer text.
    """
    sources: list[dict] = []

    for doc in docs:
        meta        = doc.metadata
        is_summary  = bool(meta.get("is_meeting_summary", False))
        speaker     = "Meeting Summary" if is_summary else meta.get("speaker_name", "Unknown")
        chunk_num   = meta.get("_global_chunk_num", len(sources) + 1)

        sources.append({
            "chunk_num":       chunk_num,
            "speaker_name":    speaker,
            "meeting_title":   meta.get("meeting_title", "Unknown Meeting"),
            "meeting_date":    meta.get("meeting_date", ""),
            "timestamp":       format_timestamp(meta.get("start_time")),
            "content_preview": doc.page_content[:200].strip(),
            "is_summary":      is_summary,
        })

    return sources


# ── FUTURE USE: deduplication approach (1 card per speaker per meeting) ────────
# Uncomment and replace _build_sources() calls with _build_sources_deduped() if
# you want a cleaner sources panel when a speaker appears in many chunks.
#
# Trade-off: [N] citations may mis-align when a speaker has multiple chunks —
# the collapsed card shows chunk [1] but the LLM may have cited [3] or [7].
# Only safe if every speaker appears at most once per request (very rare).
#
# def _build_sources_deduped(docs) -> list[dict]:
#     seen:    set[tuple]  = set()
#     sources: list[dict]  = []
#     for doc in docs:
#         meta       = doc.metadata
#         is_summary = bool(meta.get("is_meeting_summary", False))
#         speaker    = "Meeting Summary" if is_summary else meta.get("speaker_name", "Unknown")
#         dedup_key  = (speaker, meta.get("meeting_id", ""))
#         if dedup_key in seen:
#             continue
#         seen.add(dedup_key)
#         chunk_num  = meta.get("_global_chunk_num", len(sources) + 1)
#         sources.append({
#             "chunk_num":       chunk_num,
#             "speaker_name":    speaker,
#             "meeting_title":   meta.get("meeting_title", "Unknown Meeting"),
#             "meeting_date":    meta.get("meeting_date", ""),
#             "timestamp":       format_timestamp(meta.get("start_time")),
#             "content_preview": doc.page_content[:200].strip(),
#             "is_summary":      is_summary,
#         })
#     return sources


# ── Tool call trace extraction ────────────────────────────────────────────────

def _extract_tool_calls(messages: list) -> list[dict]:
    """
    Pull the tool call trace out of the message thread for transparency.
    Each entry shows: tool name + args (project_id excluded — backend detail).
    """
    trace: list[dict] = []
    for msg in messages:
        if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", []):
            for tc in msg.tool_calls:
                # Strip injected state args that the LLM didn't supply
                args = {k: v for k, v in tc["args"].items() if k != "state"}
                trace.append({"tool": tc["name"], "args": args})
    return trace


# ── Main entry point ──────────────────────────────────────────────────────────

def answer_query(query: str, project_id: str) -> dict:
    """
    Run the production LangGraph agent and return a structured result.

    Parameters
    ----------
    query      : Natural language question from the PM
    project_id : Project scope — enforced backend-side, never from LLM

    Returns
    -------
    dict with keys:
      answer          (str)        — LLM-generated answer
      sources         (list[dict]) — speaker/meeting-level source entries
      tool_calls      (list[dict]) — tool call trace [{tool, args}, ...]
      intent          (str)        — always "production_agent" for routing detection
      notice          (str|None)   — any advisory notice (None for prod path)
      num_context_chunks (int)     — number of docs retrieved across all tool calls
      model           (str)        — model used
      error           (str|None)   — exception message if something failed
    """
    t_start = time.time()

    # Clear the per-request doc accumulator before invoking the graph
    reset_doc_accumulator()

    graph          = get_graph()
    print(f"Graph output is: \n\n {graph} \n\n ")
    initial_state  = {
        "messages":    [HumanMessage(content=query)],
        "project_id":  project_id,
        "scope_where":   None,        # filled by query_scope_node
        "scope_ids":     None,        # filled by query_scope_node
        "scope_type":    "project",   # filled by query_scope_node (default = all meetings)
        "recommended_k": 15,          # filled by query_scope_node; default = single-meeting k
    }

    error:  str | None = None
    answer: str        = ""
    messages: list     = []

    try:
        result   = graph.invoke(initial_state)
        print(f"Graph Initial State is: \n\n {initial_state} \n\n ")
        print(f"Graph Result is: \n\n {result} \n\n ")
        messages = result.get("messages", [])
        scope_ids = result.get("scope_ids", [])
        scope_type = result.get("scope_type", "project")
        print(f"\n\n Graph Scope Type is: {scope_type} \n\n ")
        print(f"\n\n Graph Scope IDs is:  {scope_ids} \n\n ")
        print(f"\n\n Graph Messages is: {messages} \n\n ")

        # The final answer is the content of the last AIMessage.
        # Gemini 2.5 with extended thinking returns content as a list of blocks;
        # Gemini 2.0 returns a plain string. Handle both formats.
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and msg.content:
                raw = msg.content
                if isinstance(raw, str):
                    answer = raw
                elif isinstance(raw, list):
                    # Extract text blocks from extended-thinking content format
                    text_parts = [
                        block["text"]
                        for block in raw
                        if isinstance(block, dict) and block.get("type") == "text"
                    ]
                    answer = "\n".join(text_parts).strip()
                if answer:
                    break

        if not answer:
            answer = "I could not generate an answer. Please try rephrasing your question."

    except Exception as exc:
        logger.exception("Production agent error for query=%r project=%s", query, project_id)
        error  = str(exc)
        answer = f"Something went wrong: {exc}"

    # Build sources from accumulated docs
    docs    = get_accumulated_docs()
    sources = _build_sources(docs)

    elapsed_ms = round((time.time() - t_start) * 1000)
    tool_calls = _extract_tool_calls(messages)

    logger.info(
        "production answer_query | project=%s | tools_called=%d | docs=%d | "
        "sources=%d | elapsed=%dms",
        project_id, len(tool_calls), len(docs), len(sources), elapsed_ms,
    )

    return {
        "answer":             answer,
        "sources":            sources,
        "tool_calls":         tool_calls,
        "intent":             "production_agent",
        "notice":             None,
        "num_context_chunks": len(docs),
        "model":              "gemini-2.5-flash (agent)",
        "error":              error,
    }
