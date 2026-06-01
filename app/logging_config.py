# import logging
# import sys


# def setup_pipeline_logging() -> None:
#     """
#     Configure console logging for pipeline trace output.
#     Call once at app startup (streamlit_app.py or main.py).

#     Writes to both sys.__stderr__ (terminal) and pipeline.log (file fallback).
#     """
#     fmt = logging.Formatter("%(message)s")

#     # Terminal handler — use sys.__stderr__ (original fd, not Streamlit-patched sys.stderr)
#     stderr_handler = logging.StreamHandler(sys.__stderr__)
#     stderr_handler.setFormatter(fmt)

#     # File handler — always reliable regardless of terminal state
#     file_handler = logging.FileHandler("pipeline.log", mode="a", encoding="utf-8")
#     file_handler.setFormatter(fmt)

#     # Our modules — full trace
#     for name in (
#     "app.rag.answer.pipeline",
#     "app.rag.answer.builder",
#     "app.rag.answer.metadata",
#     "app.core.scope",
#     "app.rag.query_intent",
#     "app.services.retrieval.retriever",
#     "app.services.retrieval.reranker",
#     ):
#         log = logging.getLogger(name)
#         log.handlers.clear()          # drop stale handlers from hot-reload
#         log.setLevel(logging.DEBUG)
#         log.addHandler(stderr_handler)
#         log.addHandler(file_handler)
#         log.propagate = False

#     # Everything else — suppress noise
#     for noisy in ("httpx", "httpcore", "google", "langchain", "chromadb", "tenacity"):
#         logging.getLogger(noisy).setLevel(logging.WARNING)


# new way
import logging
import sys


def setup_pipeline_logging() -> None:
    """
    Configure logging for the meeting intelligence pipeline.

    Covers both app.agent (LangGraph agent + chat history + scope resolver)
    and app.services / app.core (retrieval, chunking, old RAG pipeline).

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
        "app.services.retrieval.retriever",
        "app.services.retrieval.reranker",
        "app.core.retrieval.hybrid",
        "app.core.retrieval.reranker",
        "app.core.scope",
        "app.rag.answer.pipeline",
        "app.rag.answer.builder",
        "app.rag.answer.metadata",
        "app.rag.query_intent",
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