from langchain_core.documents import Document
from typing import Any


def chunk_to_document(chunk: dict[str, Any]) -> Document:
    """
    Convert internal chunk dict into LangChain Document.

    Validates required fields and sanitizes metadata.
    """

    if not isinstance(chunk, dict):
        raise TypeError(
            f"chunk must be a dict, got {type(chunk).__name__}"
        )

    if "text" not in chunk:
        raise ValueError(
            f"Chunk missing required 'text' field. chunk_id={chunk.get('chunk_id', 'unknown')}"
        )

    text = chunk["text"]

    if text is None:
        raise ValueError(
            f"Chunk text is None. chunk_id={chunk.get('chunk_id', 'unknown')}"
        )

    if not isinstance(text, str):
        text = str(text)

    text = text.strip()

    if not text:
        raise ValueError(
            f"Chunk text is empty after stripping whitespace. chunk_id={chunk.get('chunk_id', 'unknown')}"
        )

    metadata = {}

    for key, value in chunk.items():
        if key == "text":
            continue

        if value is None:
            continue

        if isinstance(value, (str, int, float, bool)):
            metadata[key] = value
        else:
            metadata[key] = str(value)

    return Document(
        page_content=text,
        metadata=metadata,
    )


def chunks_to_documents(chunks: list[dict[str, Any]]) -> list[Document]:
    """
    Convert list of chunks into LangChain Documents.
    Invalid chunks are skipped.
    """

    if not chunks:
        return []

    documents = []

    for chunk in chunks:
        try:
            documents.append(chunk_to_document(chunk))
        except Exception as e:
            print(f"Skipping invalid chunk: {e}")

    return documents