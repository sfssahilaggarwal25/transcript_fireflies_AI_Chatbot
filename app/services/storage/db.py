import chromadb
import os

_client = None
_collection = None

COLLECTION_NAME = "meeting_chunks"
PERSIST_DIR = os.path.join(os.path.dirname(__file__), "../../../../chroma_db")


def get_collection():
    """Return the ChromaDB collection, creating it if it doesn't exist."""
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=PERSIST_DIR)
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection
