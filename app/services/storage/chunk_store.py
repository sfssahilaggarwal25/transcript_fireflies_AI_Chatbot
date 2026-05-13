# from app.services.storage.db import get_collection

# # Fields that go into ChromaDB metadata (everything except text which is the document)
# _EXCLUDE_FROM_METADATA = {"text"}


# def _to_metadata(chunk: dict) -> dict:
#     """Strip document-level fields — ChromaDB metadata must be str/int/float/bool only."""
#     return {k: v for k, v in chunk.items() if k not in _EXCLUDE_FROM_METADATA}


# def store_chunks(chunks: list[dict]) -> int:
#     """Embed and store chunks in ChromaDB. Uses upsert so re-ingestion is safe."""
#     if not chunks:
#         return 0

#     collection = get_collection()

#     collection.upsert(
#         ids=[c["chunk_id"] for c in chunks],
#         documents=[c["text"] for c in chunks],
#         metadatas=[_to_metadata(c) for c in chunks],
#     )

#     return len(chunks)


# def get_chunks_by_meeting(meeting_id: str) -> list[dict]:
#     """Return all chunks for a meeting as flat dicts (text + metadata merged)."""
#     collection = get_collection()
#     results = collection.get(where={"meeting_id": meeting_id})

#     chunks = []
#     for i, doc_id in enumerate(results["ids"]):
#         chunk = results["metadatas"][i].copy()
#         chunk["text"] = results["documents"][i]
#         chunks.append(chunk)

#     return chunks


# def get_chunk_count(project_id: str) -> int:
#     """Return total chunks stored for a project."""
#     collection = get_collection()
#     results = collection.get(where={"project_id": project_id})
#     return len(results["ids"])


# def get_distinct_meeting_ids(project_id: str) -> set:
#     """Return set of distinct meeting_ids already stored for a project."""
#     collection = get_collection()
#     results = collection.get(where={"project_id": project_id}, include=["metadatas"])
#     return {m["meeting_id"] for m in results["metadatas"]}


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
    Retrieve all documents for a given meeting.
    """

    if not meeting_id:
        raise ValueError("meeting_id is required")

    vectorstore = get_vectorstore()

    try:
        docs = vectorstore.similarity_search(
            query="meeting transcript",
            k=500,
            filter={"meeting_id": meeting_id},
        )
        return docs

    except Exception as e:
        logger.exception("Failed to retrieve chunks for meeting_id=%s", meeting_id)
        raise


def get_chunk_count(project_id: str) -> int:
    """
    Count documents for a project.
    """

    if not project_id:
        raise ValueError("project_id is required")

    vectorstore = get_vectorstore()

    try:
        docs = vectorstore.similarity_search(
            query="project transcript",
            k=10000,
            filter={"project_id": project_id},
        )
        return len(docs)

    except Exception as e:
        logger.exception("Failed to count chunks for project_id=%s", project_id)
        raise


def get_distinct_meeting_ids(project_id: str) -> set[str]:
    if not project_id:
        raise ValueError("project_id is required")

    collection = get_raw_collection()

    results = collection.get(
        where={"project_id": project_id},
        include=["metadatas"],
    )

    return {
        m["meeting_id"]
        for m in results["metadatas"]
        if "meeting_id" in m
    }