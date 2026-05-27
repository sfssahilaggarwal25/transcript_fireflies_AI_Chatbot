import os
import logging
from langchain_chroma import Chroma
from app.core.embeddings.gemini_embeddings import get_embedding_model


from chromadb.api.models.Collection import Collection

logger = logging.getLogger(__name__)

_VECTORSTORE = None

COLLECTION_NAME = "meeting_chunks"

PERSIST_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "../../../chroma_db",
    )
)


def get_vectorstore() -> Chroma:
    """
    Return singleton LangChain Chroma vector store instance.
    Creates it if not already initialized.
    """

    global _VECTORSTORE

    if _VECTORSTORE is not None:
        return _VECTORSTORE

    try:
        if not os.path.exists(PERSIST_DIR):
            os.makedirs(PERSIST_DIR, exist_ok=True)
            logger.info("Created Chroma persistence directory: %s", PERSIST_DIR)

        embedding_model = get_embedding_model()

        _VECTORSTORE = Chroma(
            collection_name=COLLECTION_NAME,
            persist_directory=PERSIST_DIR,
            embedding_function=embedding_model,
        )

        logger.info(
            "Initialized LangChain Chroma vector store | collection=%s | path=%s",
            COLLECTION_NAME,
            PERSIST_DIR,
        )

        return _VECTORSTORE

    except Exception as e:
        logger.exception("Failed to initialize vector store: %s", e)
        raise RuntimeError(
            f"Vector store initialization failed: {str(e)}"
        ) from e


def reset_vectorstore() -> None:
    """
    Force the singleton to re-initialize on the next get_vectorstore() call.
    Call this after wiping and re-ingesting chroma_db/ — without it, the in-memory
    HNSW index still references old IDs and throws 'Error finding id' on queries.
    """
    global _VECTORSTORE
    _VECTORSTORE = None
    logger.info("Vectorstore singleton reset — next call will reinitialize from disk")


def get_raw_collection() -> Collection:
    """
    Return underlying raw Chroma collection.

    Used for metadata-only operations where semantic embedding
    search is unnecessary.
    """

    try:
        vectorstore = get_vectorstore()

        if not hasattr(vectorstore, "_collection"):
            raise RuntimeError(
                "Vectorstore does not expose raw Chroma collection."
            )

        return vectorstore._collection

    except Exception as e:
        logger.exception("Failed to access raw Chroma collection: %s", e)
        raise RuntimeError(
            f"Raw collection access failed: {str(e)}"
        ) from e

