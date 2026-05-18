import logging
import sys


def setup_pipeline_logging() -> None:
    """
    Configure console logging for pipeline trace output.
    Call once at app startup (streamlit_app.py or main.py).

    Writes to both sys.__stderr__ (terminal) and pipeline.log (file fallback).
    """
    fmt = logging.Formatter("%(message)s")

    # Terminal handler — use sys.__stderr__ (original fd, not Streamlit-patched sys.stderr)
    stderr_handler = logging.StreamHandler(sys.__stderr__)
    stderr_handler.setFormatter(fmt)

    # File handler — always reliable regardless of terminal state
    file_handler = logging.FileHandler("pipeline.log", mode="a", encoding="utf-8")
    file_handler.setFormatter(fmt)

    # Our modules — full trace
    for name in (
        "app.services.answer_service",
        "app.services.query_intent",
        "app.services.retrieval.retriever",
        "app.services.retrieval.reranker",
    ):
        log = logging.getLogger(name)
        log.handlers.clear()          # drop stale handlers from hot-reload
        log.setLevel(logging.DEBUG)
        log.addHandler(stderr_handler)
        log.addHandler(file_handler)
        log.propagate = False

    # Everything else — suppress noise
    for noisy in ("httpx", "httpcore", "google", "langchain", "chromadb", "tenacity"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
