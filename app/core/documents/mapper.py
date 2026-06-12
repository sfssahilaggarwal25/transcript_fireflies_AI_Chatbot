from langchain_core.documents import Document
from typing import Any


def chunk_to_document(chunk: dict[str, Any]) -> Document:
    """
    Convert an internal chunk dict into a LangChain Document.

    page_content strategy:
      - If chunk["hypothetical_q"] is present and non-empty → use it as
        page_content. This applies to both atomic and dialogue_group chunks.
      - Summary chunks never have hypothetical_q, so they fall through to
        plain text.

    Metadata strategy:
      - chunk["text"] (the original transcript text) is stored as "raw_text"
        in metadata so the retrieval layer can surface the real quote.
      - "text" and "hypothetical_q" are excluded from the metadata iteration
        loop — they are handled explicitly above.
      - All other chunk fields pass through as-is (str, int, float, bool only;
        other types are coerced to str to satisfy ChromaDB constraints).
    """

    if not isinstance(chunk, dict):
        raise TypeError(
            f"chunk must be a dict, got {type(chunk).__name__}"
        )

    if "text" not in chunk:
        raise ValueError(
            f"Chunk missing required 'text' field. chunk_id={chunk.get('chunk_id', 'unknown')}"
        )

    raw_text = chunk["text"]

    if raw_text is None:
        raise ValueError(
            f"Chunk text is None. chunk_id={chunk.get('chunk_id', 'unknown')}"
        )

    if not isinstance(raw_text, str):
        raw_text = str(raw_text)

    raw_text = raw_text.strip()

    if not raw_text:
        raise ValueError(
            f"Chunk text is empty after stripping. chunk_id={chunk.get('chunk_id', 'unknown')}"
        )

    # Determine page_content ──────────────────────────────────────────────────
    hq = (chunk.get("hypothetical_q") or "").strip()

    if hq:
        # Preferred path: embed the hypothetical question, not the raw text.
        # Retrieval queries match questions, so question↔question similarity
        # outperforms query↔passage similarity on most PM lookup patterns.
        page_content = hq
    else:
        # Fallback for summary chunks (no HQ generated) and any unexpected case.
        # Summary chunks already have full context in their text; no prefix needed.
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
                page_content = prefix + raw_text
            else:
                page_content = raw_text
        else:
            page_content = raw_text

    # Build metadata ──────────────────────────────────────────────────────────
    metadata: dict[str, Any] = {}

    for key, value in chunk.items():
        # Skip fields handled separately — they must not appear redundantly.
        if key in ("text", "hypothetical_q"):
            continue

        if value is None:
            continue

        if isinstance(value, (str, int, float, bool)):
            metadata[key] = value
        else:
            metadata[key] = str(value)

    # Always store the original transcript text so the UI / retrieval layer
    # can show the real quote rather than the hypothetical question.
    metadata["raw_text"] = raw_text

    return Document(
        page_content=page_content,
        metadata=metadata,
    )


def chunks_to_documents(chunks: list[dict[str, Any]]) -> list[Document]:
    """Convert list of chunk dicts into LangChain Documents. Invalid chunks are skipped."""

    if not chunks:
        return []

    documents = []

    for chunk in chunks:
        try:
            documents.append(chunk_to_document(chunk))
        except Exception as e:
            print(f"Skipping invalid chunk: {e}")

    return documents