import logging
import sys


class _SectionFormatter(logging.Formatter):
    """
    Inserts a blank line + horizontal rule before messages that mark the
    start of a major pipeline step, so sections are visually separated in
    the log file without any changes to the application code.
    """
    _TRIGGERS = (
        "═══",                        # query start / end banners
        "══ NEW QUERY",               # new query banner
        "══ DONE",                    # query done banner
        "[1] HISTORY",                # step 1 — history load
        "[2] GRAPH",                  # step 2 — graph invocation complete
        "[3] AGENT",                  # step 3 — each agent round
        "► STAGE 1",                  # scope: LLM classifier call
        "► STAGE 2",                  # scope: history-aware parser
        "Scope resolved",             # scope: final result
        "scope_parser |",             # scope: parser logic
        "search_transcripts | preset", # retrieval: hybrid search call
        "[GRAPH COMPILATION]",        # graph built
    )

    def format(self, record: logging.LogRecord) -> str:
        full = super().format(record)
        if any(t in record.getMessage() for t in self._TRIGGERS):
            return f"\n{'─' * 80}\n{full}"
        return full


def setup_query_file_logging(
    query: str,
    project_id: str = "",
    log_dir: str | None = None,
) -> str:
    """
    Create a per-query log file and attach it to all pipeline loggers.

    Each call produces one new timestamped file so every run is isolated —
    no more hunting through a shared pipeline.log for the query you care about.

    File location: app/agent/tests/logs/ by default (override with log_dir).
    File name:     YYYY-MM-DD_HH-MM-SS__first_6_query_words.log

    Returns the absolute path to the created file so callers can print it.
    """
    import re as _re
    import datetime
    from pathlib import Path

    if log_dir is None:
        # Default: co-located with test_production.py
        log_dir = str(Path(__file__).resolve().parent / "agent" / "tests" / "logs")
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    now  = datetime.datetime.now()
    ts   = now.strftime("%Y-%m-%d_%H-%M-%S")
    slug = "_".join(query.strip().split()[:6])
    slug = _re.sub(r"[^\w\-]", "", slug)[:60]
    filepath = str(Path(log_dir) / f"{ts}__{slug}.log")

    # ── Write a human-readable header at the top of the file ─────────────────
    W   = 78  # inner width between ║ borders
    bar = "═" * W

    def _row(label: str, value: str) -> str:
        content = f"  {label:<10}: {value}"
        if len(content) > W:
            content = content[: W - 3] + "..."
        return f"║{content.ljust(W)}║"

    with open(filepath, "w", encoding="utf-8") as fh:
        fh.write(f"╔{bar}╗\n")
        fh.write(f"║{'  PIPELINE TRACE LOG'.ljust(W)}║\n")
        fh.write(f"╠{bar}╣\n")
        fh.write(f"{_row('Query', query)}\n")
        fh.write(f"{_row('Project', project_id)}\n")
        fh.write(f"{_row('Started', now.strftime('%Y-%m-%d  %H:%M:%S'))}\n")
        fh.write(f"╚{bar}╝\n\n")
        fh.write(
            "  Each section below is separated by a ── line.\n"
            "  Sections: SCOPE RESOLUTION → AGENT ROUNDS → TOOL CALLS → DONE\n\n"
        )

    # ── Formatter: timestamp | level | module | message (+ section separators) ─
    fmt = _SectionFormatter(
        "%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%H:%M:%S",
    )

    file_handler    = logging.FileHandler(filepath, mode="a", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)

    console_handler = logging.StreamHandler(sys.__stderr__)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(fmt)

    # ── Instrument all pipeline modules ───────────────────────────────────────
    _MODULES = (
        "app.agent.scope_llm",           # Stage 1 LLM + Stage 2 scope_parser
        "app.agent.query_scope",         # query_scope_node
        "app.agent.service",             # main entry + answer extraction
        "app.agent.graph",               # LLM rounds + tool call routing
        "app.agent.tools",               # each tool execution
        "app.core.retrieval.hybrid",     # BM25 + dense + RRF merge
        "app.core.retrieval.reranker",   # reranking step
        "app.core.retrieval.base",       # _log_chunk_list (final hybrid result)
        "app.core.scope",                # meeting list helpers
    )
    for name in _MODULES:
        log = logging.getLogger(name)
        log.handlers.clear()
        log.setLevel(logging.DEBUG)
        log.addHandler(file_handler)
        log.addHandler(console_handler)
        log.propagate = False

    for lib in ("httpx", "httpcore", "google", "langchain", "chromadb",
                "tenacity", "urllib3", "openai", "anthropic"):
        logging.getLogger(lib).setLevel(logging.WARNING)

    return filepath


# ── Streamlit / server logging (unchanged) ────────────────────────────────────

def setup_pipeline_logging() -> None:
    """
    Configure logging for the meeting intelligence pipeline.

    Covers app.agent (LangGraph agent + chat history + scope resolver)
    and app.core (retrieval, chunking).

    Output:
      - pipeline.log  — always written, survives Streamlit output capture
      - stderr        — visible in the terminal where `streamlit run` was launched

    How to watch live:
      tail -f pipeline.log          (Mac/Linux terminal)
    """

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )

    # File handler — reliable regardless of Streamlit output redirection
    file_handler = logging.FileHandler(
        "pipeline.log",
        mode="a",
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)

    # Console handler — use sys.__stderr__ (original fd, not Streamlit-patched)
    console_handler = logging.StreamHandler(sys.__stderr__)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(fmt)

    # ── Modules to instrument ─────────────────────────────────────────────────
    # Each module gets both handlers attached directly (propagate=False prevents
    # duplicate lines from parent logger catchall).
    _AGENT_MODULES = (
        "app.agent.streamlit_app",    # query banner + DONE footer (UI path)
        "app.agent.chat_store",       # PostgreSQL session/turn CRUD
        "app.agent.scope_llm",        # Stage 1 LLM + Stage 2 scope_parser
        "app.agent.query_scope",      # query_scope_node output
        "app.agent.service",          # history load + final answer save (API path)
        "app.agent.graph",            # LLM calls + tool_calls count
        "app.agent.tools",            # individual tool execution
    )

    _SERVICE_MODULES = (
        "app.core.retrieval.hybrid",
        "app.core.retrieval.reranker",
        "app.core.scope",
    )

    for name in _AGENT_MODULES + _SERVICE_MODULES:
        log = logging.getLogger(name)
        log.handlers.clear()          # drop stale handlers from hot-reload
        log.setLevel(logging.DEBUG)
        log.addHandler(file_handler)
        log.addHandler(console_handler)
        log.propagate = False

    # ── Silence noisy third-party libraries ───────────────────────────────────
    for lib in ("httpx", "httpcore", "google", "langchain", "chromadb",
                "tenacity", "urllib3", "openai", "anthropic"):
        logging.getLogger(lib).setLevel(logging.WARNING)