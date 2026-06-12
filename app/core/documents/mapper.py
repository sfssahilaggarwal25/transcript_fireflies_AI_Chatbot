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

    # Contextual prefix: prepend meeting + speaker context before embedding.
    # This dramatically improves retrieval for short chunks (e.g. "Change in earnings."
    # now embeds as a financial-meeting chunk, not just a generic phrase).
    # Only applied to utterance chunks — summary chunks already have full context.
    if chunk.get("segment_type") == "content":
        meeting_title = chunk.get("meeting_title", "")
        speaker_name  = chunk.get("speaker_name", "")
        if meeting_title or speaker_name:
            parts = []
            if meeting_title:
                parts.append(f"Meeting: {meeting_title}")
            if speaker_name:
                parts.append(f"Speaker: {speaker_name}")
            prefix = "[" + " | ".join(parts) + "] "
            text = prefix + text

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