from langchain_core.documents import Document
from app.services.storage.db import get_vectorstore, get_raw_collection

import logging

logger = logging.getLogger(__name__)


def store_documents(documents: list[Document]) -> int:
    """
    Store LangChain Documents in Chroma vector store.
    Safe for re-ingestion if document IDs are stable.
    """
    if not documents:
        logger.warning("No documents provided for storage.")
        return 0

    vectorstore = get_vectorstore()

    try:
        vectorstore.add_documents(
            documents,
            ids=[doc.metadata["chunk_id"] for doc in documents]
        )
        logger.info("Stored %d documents in Chroma.", len(documents))
        return len(documents)

    except Exception as e:
        logger.exception("Failed to store documents in Chroma: %s", e)
        raise


def get_chunks_by_meeting(meeting_id: str) -> list[Document]:
    """
    Retrieve all documents for a given meeting via metadata filter.
    Uses raw collection — no embedding call, no similarity scoring.
    """
    if not meeting_id:
        raise ValueError("meeting_id is required")

    collection = get_raw_collection()

    try:
        results = collection.get(
            where={"meeting_id": {"$eq": meeting_id}},
            include=["documents", "metadatas"],
        )
        docs = []
        for i in range(len(results.get("ids", []))):
            docs.append(Document(
                page_content=results["documents"][i],
                metadata=results["metadatas"][i],
            ))
        return docs

    except Exception as e:
        logger.exception("Failed to retrieve chunks for meeting_id=%s", meeting_id)
        raise


def get_chunk_count(project_id: str) -> int:
    """
    Count documents for a project via metadata filter.
    Uses raw collection — no embedding call, exact count guaranteed.
    """
    if not project_id:
        raise ValueError("project_id is required")

    collection = get_raw_collection()

    try:
        results = collection.get(
            where={"project_id": {"$eq": project_id}},
            include=[],
        )
        return len(results.get("ids", []))

    except Exception as e:
        logger.exception("Failed to count chunks for project_id=%s", project_id)
        raise


def get_distinct_meeting_ids(project_id: str) -> set[str]:
    if not project_id:
        raise ValueError("project_id is required")

    collection = get_raw_collection()

    results = collection.get(
        where={"project_id": {"$eq": project_id}},
        include=["metadatas"],
    )

    return {
        m["meeting_id"]
        for m in results["metadatas"]
        if "meeting_id" in m
    }
