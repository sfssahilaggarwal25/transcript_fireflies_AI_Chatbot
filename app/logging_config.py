import logging
import sys


def setup_pipeline_logging() -> None:
    """
    Configure console logging for pipeline trace output.
    Call once at app startup (streamlit_app.py or main.py).

    Output goes to stderr so Streamlit does not swallow it.
    Only our app modules are set to DEBUG; noisy libraries stay at WARNING.
    """
    fmt = logging.Formatter("%(message)s")

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(fmt)

    # Our modules — full trace
    for name in (
        "app.services.answer_service",
        "app.services.query_intent",
        "app.services.retrieval.retriever",
    ):
        log = logging.getLogger(name)
        log.setLevel(logging.DEBUG)
        if not log.handlers:
            log.addHandler(handler)
        log.propagate = False

    # Everything else — suppress noise
    for noisy in ("httpx", "httpcore", "google", "langchain", "chromadb", "tenacity"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
