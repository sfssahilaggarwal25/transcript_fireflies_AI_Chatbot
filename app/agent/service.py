"""
service.py — Public entry point for the production LangGraph pipeline.

Usage
-----
    from app.agent.service import answer_query

    result = answer_query(
        query      = "What did Bhavneet say about the forecasting timeline?",
        project_id = "proj_nolocode_001",
        session_id = "abc123",   # optional — omit for stateless mode
    )
    # result keys: answer, sources, tool_calls, model, error

Chat history
------------
  Pass session_id (obtained from chat_store.create_session) to enable:
    - Conversation history injected into the LLM context (last 5 turns)
    - Scope inheritance across turns ("that meeting" resolves correctly)
    - Turn persisted to PostgreSQL after each successful query

  If session_id is None or DATABASE_URL is not set, the pipeline runs
  stateless — identical to the original behaviour before chat history.
"""

import logging
import time
from langchain_core.messages import HumanMessage, AIMessage

from app.agent import (
    get_graph,
    reset_doc_accumulator,
    get_accumulated_docs,
)
from app.agent.chat_store import get_chat_store
from app.agent._tool_utils import fmt_date
from app.core.retrieval import reset_corpus_cache
from app.core.retrieval.reranker import reset_rejected_docs, get_rejected_docs

logger = logging.getLogger(__name__)


# ── Timestamp formatter ───────────────────────────────────────────────────────

def format_timestamp(sec: int | float | None) -> str | None:
    """Format seconds-from-meeting-start → MM:SS, or H:MM:SS for long meetings."""
    if sec is None:
        return None
    total_seconds = int(sec)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


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
            "speaker_role":    meta.get("speaker_role", "unknown") if not is_summary else "summary",
            "meeting_title":   meta.get("meeting_title", "Unknown Meeting"),
            "meeting_date":    fmt_date(meta.get("meeting_date", "")),
            "timestamp":       format_timestamp(meta.get("start_time")),
            "content_preview": doc.page_content[:350].strip(),
            "is_summary":      is_summary,
        })

    return sources


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
                args = {k: v for k, v in tc["args"].items() if k != "state"}
                trace.append({"tool": tc["name"], "args": args})
    return trace


# ── Answer extractor ──────────────────────────────────────────────────────────

def _extract_answer(messages: list) -> str:
    """
    Extract the final answer text from the last AIMessage in the thread.
    Handles both plain string content (Gemini 2.0) and list-of-blocks
    content (Gemini 2.5 extended thinking).
    """
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content:
            raw = msg.content
            if isinstance(raw, str):
                return raw
            if isinstance(raw, list):
                parts = [
                    b["text"]
                    for b in raw
                    if isinstance(b, dict) and b.get("type") == "text"
                ]
                text = "\n".join(parts).strip()
                if text:
                    return text
    return ""


# ── Main entry point ──────────────────────────────────────────────────────────

def answer_query(
    query:      str,
    project_id: str,
    session_id: str | None = None,
    max_turns:  int = 5,
) -> dict:
    """
    Run the production LangGraph agent and return a structured result.

    Parameters
    ----------
    query      : Natural language question from the PM
    project_id : Project scope — enforced backend-side, never from LLM
    session_id : PostgreSQL session ID for chat history (None = stateless)
    max_turns  : Max prior turns to load as LLM context (default 5)

    Returns
    -------
    dict with keys:
      answer             (str)        — LLM-generated answer
      sources            (list[dict]) — speaker/meeting-level source entries
      tool_calls         (list[dict]) — tool call trace [{tool, args}, ...]
      intent             (str)        — always "production_agent"
      notice             (str|None)   — advisory notice (None for prod path)
      num_context_chunks (int)        — docs retrieved across all tool calls
      model              (str)        — model used
      error              (str|None)   — exception message if something failed
    """
    t_start = time.time()

    reset_doc_accumulator()
    reset_corpus_cache()
    reset_rejected_docs()

    logger.info("═══============================= Starting production agent query ═══=============================")
    logger.info(
        "══ NEW QUERY ══ | project=%s | session=%s\n          query: %s",
        project_id, session_id or "stateless", query,
    )

    # ── [1] Load conversation history ─────────────────────────────────────────
    # M2/M3: get_chat_store() returns None if DATABASE_URL not set or DB is down.
    # get_llm_messages() returns [] on any DB failure — query proceeds stateless.
    store = get_chat_store()
    history_messages = []
    if store and session_id:
        history_messages = store.get_llm_messages(session_id, max_turns)
        logger.info(
            "[1] HISTORY  — %d messages (%d prior turns) loaded | session=%s",
            len(history_messages), len(history_messages) // 2, session_id,
        )
    else:
        logger.info("[1] HISTORY  — stateless (no session / no DB)")

    graph = get_graph()
    initial_state = {
        "messages":      history_messages + [HumanMessage(content=query)],
        "project_id":    project_id,
        "session_id":    session_id,
        "scope_where":   None,
        "scope_ids":     None,
        "scope_type":    "project",
        "recommended_k": 15,
    }

    # F1 FIX: initialise result before the try block so that if graph.invoke()
    # raises before assigning result, the save_turn block inside the try is
    # simply skipped — no NameError, no polluting history with error turns.
    result:   dict       = {}
    messages: list       = []
    answer:   str        = ""
    error:    str | None = None

    try:
        result   = graph.invoke(initial_state)
        logger.info("[2] GRAPH    — invocation complete | session=%s", session_id or "stateless")
        messages = result.get("messages", [])
        answer   = _extract_answer(messages)

        if not answer:
            answer = "I could not generate an answer. Please try rephrasing your question."

        logger.info(
            "    answer ready | %d chars | %d docs retrieved",
            len(answer), len(get_accumulated_docs()),
        )

        # Save turn INSIDE try — only persist successful queries.
        # Failed queries must NOT appear in history (would corrupt future context).
        # M2: save_turn is a silent no-op on DB failure.
        if store and session_id and answer:
            docs_for_save = get_accumulated_docs()
            sources_for_save = _build_sources(docs_for_save)
            turn_index = store.get_next_turn_index(session_id)
            store.save_turn(
                session_id=session_id,
                turn_index=turn_index,
                human=query,
                ai=answer,
                sources=sources_for_save,
                tool_calls=_extract_tool_calls(messages),
                num_chunks=len(docs_for_save),
                scope_type=result.get("scope_type", "project"),
                scope_ids=result.get("scope_ids"),
                scope_where=result.get("scope_where"),
            )

    except Exception as exc:
        logger.exception(
            "Production agent error for query=%r project=%s", query, project_id
        )
        error  = str(exc)
        answer = f"Something went wrong: {exc}"
        # save_turn intentionally skipped — don't pollute history with error turns

    docs       = get_accumulated_docs()
    sources    = _build_sources(docs)
    elapsed_ms = round((time.time() - t_start) * 1000)
    tool_calls = _extract_tool_calls(messages)

    logger.info(
        "══ DONE (%dms) ══ | tools=%d | docs=%d | answer=%d chars | project=%s | session=%s",
        elapsed_ms, len(tool_calls), len(docs), len(answer),
        project_id, session_id or "stateless",
    )

    # ── Log the full result so it appears in the per-query log file ───────────
    import os as _os
    _rerank_on = _os.getenv("RERANK_ENABLED", "0") != "0"
    _SEP  = "─" * 72
    _SEP2 = "═" * 72

    # ── Tool calls ────────────────────────────────────────────────────────────
    logger.info(_SEP2)
    logger.info("RESULT — TOOL CALLS  (%d)", len(tool_calls))
    logger.info(_SEP2)
    if tool_calls:
        for i, tc in enumerate(tool_calls, 1):
            logger.info("  %d. %s", i, tc["tool"])
            for k, v in tc["args"].items():
                logger.info("       %-18s: %s", k, v)
    else:
        logger.info("  (no tool calls)")

    # ── Selected chunks (full text + rerank score) ────────────────────────────
    logger.info(_SEP2)
    logger.info(
        "RESULT — SELECTED CHUNKS  (%d)%s",
        len(docs),
        "  [rerank OFF — order = RRF rank]" if not _rerank_on else "  [rerank ON]",
    )
    logger.info(_SEP2)
    for doc in docs:
        m       = doc.metadata
        num     = m.get("_global_chunk_num", "?")
        score   = m.get("_rerank_score")
        rel     = m.get("_relevance", "")
        speaker = "Meeting Summary" if m.get("is_meeting_summary") else m.get("speaker_name", "?")
        meeting = m.get("meeting_title", "?")
        date    = fmt_date(m.get("meeting_date", ""))
        ts      = format_timestamp(m.get("start_time"))
        ts_str  = f"  [{ts}]" if ts else ""

        if score is not None:
            relevance = m.get("_relevance", "")
            icon = "🟢" if relevance == "high" else ("🟡" if relevance == "low" else "⚪")
            score_str = f"score={score:.1f} {icon}"
        else:
            score_str = "score=—  (rerank off)"

        low_tag = "  ⚠️ LOW RELEVANCE" if rel == "low" else ""
        logger.info(_SEP)
        logger.info(
            "  [%s]  %s  |  %-25s  |  %-32s  |  %s%s%s",
            num, score_str, speaker, meeting, date, ts_str, low_tag,
        )
        logger.info("  TEXT:")
        for line in doc.page_content.strip().splitlines():
            logger.info("    %s", line.strip())

    # ── Rejected chunks (hard-dropped by reranker) ────────────────────────────
    rejected = get_rejected_docs()
    logger.info(_SEP2)
    if not _rerank_on:
        logger.info("RESULT — REJECTED CHUNKS  (rerank is OFF — no chunks were scored/dropped)")
    elif rejected:
        logger.info("RESULT — REJECTED CHUNKS  (%d hard-dropped, score ≤ 2)", len(rejected))
        logger.info(_SEP2)
        for doc in rejected:
            m       = doc.metadata
            score   = m.get("_rerank_score", 0)
            speaker = m.get("speaker_name", "?")
            meeting = m.get("meeting_title", "?")
            date    = fmt_date(m.get("meeting_date", ""))
            ts      = format_timestamp(m.get("start_time"))
            ts_str  = f"  [{ts}]" if ts else ""
            logger.info(_SEP)
            logger.info(
                "  🔴 score=%-3.1f  |  %-25s  |  %-32s  |  %s%s",
                score, speaker, meeting, date, ts_str,
            )
            logger.info("  TEXT:")
            for line in doc.page_content.strip().splitlines():
                logger.info("    %s", line.strip())
    else:
        logger.info("RESULT — REJECTED CHUNKS  (0 hard-dropped — all scored chunks passed)")

    # ── Final answer ──────────────────────────────────────────────────────────
    logger.info(_SEP2)
    logger.info("RESULT — ANSWER")
    logger.info(_SEP2)
    for line in answer.splitlines():
        logger.info("  %s", line)
    logger.info(_SEP2)

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