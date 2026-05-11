from app.services.storage.db import get_collection

# Fields that go into ChromaDB metadata (everything except text which is the document)
_EXCLUDE_FROM_METADATA = {"text"}


def _to_metadata(chunk: dict) -> dict:
    """Strip document-level fields — ChromaDB metadata must be str/int/float/bool only."""
    return {k: v for k, v in chunk.items() if k not in _EXCLUDE_FROM_METADATA}


def store_chunks(chunks: list[dict]) -> int:
    """Embed and store chunks in ChromaDB. Uses upsert so re-ingestion is safe."""
    if not chunks:
        return 0

    collection = get_collection()

    collection.upsert(
        ids=[c["chunk_id"] for c in chunks],
        documents=[c["text"] for c in chunks],
        metadatas=[_to_metadata(c) for c in chunks],
    )

    return len(chunks)


def get_chunks_by_meeting(meeting_id: str) -> list[dict]:
    """Return all chunks for a meeting as flat dicts (text + metadata merged)."""
    collection = get_collection()
    results = collection.get(where={"meeting_id": meeting_id})

    chunks = []
    for i, doc_id in enumerate(results["ids"]):
        chunk = results["metadatas"][i].copy()
        chunk["text"] = results["documents"][i]
        chunks.append(chunk)

    return chunks


def get_chunk_count(project_id: str) -> int:
    """Return total chunks stored for a project."""
    collection = get_collection()
    results = collection.get(where={"project_id": project_id})
    return len(results["ids"])


def get_distinct_meeting_ids(project_id: str) -> set:
    """Return set of distinct meeting_ids already stored for a project."""
    collection = get_collection()
    results = collection.get(where={"project_id": project_id}, include=["metadatas"])
    return {m["meeting_id"] for m in results["metadatas"]}
