"""
accumulator.py — Per-request document accumulator.

Collects LangChain Documents from all tool calls in one graph run.
service.py reads these after graph.invoke() to build the sources panel.

Uses in-place mutations (.clear() / .append()) so ToolNode's threads
all see the same objects. Do NOT reassign with = [] or = {}.

_chunk_counter  : global sequential [N] assigned to each new chunk this request.
_chunk_id_to_num: dedup index — same chunk_id from two tool calls gets
                  its existing [N] without re-appending.
"""

from langchain_core.documents import Document

_accumulated_docs: list[Document] = []
_chunk_counter:    list[int]      = [0]
_chunk_id_to_num:  dict[str, int] = {}


def reset_doc_accumulator() -> None:
    """Clear all per-request state. Called by service.py before graph.invoke()."""
    _accumulated_docs.clear()
    _chunk_counter[0] = 0
    _chunk_id_to_num.clear()


def get_accumulated_docs() -> list[Document]:
    """Return a copy of docs collected across all tool calls this request."""
    return list(_accumulated_docs)


def _append_docs(docs: list[Document]) -> list[int]:
    """
    Assign a global sequential [N] to each doc and accumulate it.
    Returns [N] numbers — callers embed these in tool output for LLM citations.
    Deduplicates: same chunk_id across multiple tool calls gets one entry only.
    """
    numbers: list[int] = []
    for doc in docs:
        chunk_id = doc.metadata.get("chunk_id", "")
        if chunk_id and chunk_id in _chunk_id_to_num:
            numbers.append(_chunk_id_to_num[chunk_id])
        else:
            _chunk_counter[0] += 1
            n = _chunk_counter[0]
            doc.metadata["_global_chunk_num"] = n
            numbers.append(n)
            _accumulated_docs.append(doc)
            if chunk_id:
                _chunk_id_to_num[chunk_id] = n
    return numbers