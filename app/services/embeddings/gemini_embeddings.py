import os
import logging
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv()

logger = logging.getLogger(__name__)

_EMBEDDING_MODEL = None
DEFAULT_EMBEDDING_MODEL = "gemini-embedding-001"


def get_embedding_model() -> GoogleGenerativeAIEmbeddings:
    """
    Return singleton Gemini embedding model instance.
    Reads API key from environment (.env).
    """

    global _EMBEDDING_MODEL

    if _EMBEDDING_MODEL is not None:
        return _EMBEDDING_MODEL

    try:
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY not found in environment variables."
            )

        _EMBEDDING_MODEL = GoogleGenerativeAIEmbeddings(
            model=DEFAULT_EMBEDDING_MODEL,
            google_api_key=api_key,
        )

        logger.info(
            "Gemini embedding model initialized successfully: %s",
            DEFAULT_EMBEDDING_MODEL,
        )

        return _EMBEDDING_MODEL

    except Exception as e:
        logger.exception("Failed to initialize Gemini embeddings: %s", e)
        raise RuntimeError(
            f"Embedding initialization failed: {str(e)}"
        ) from e