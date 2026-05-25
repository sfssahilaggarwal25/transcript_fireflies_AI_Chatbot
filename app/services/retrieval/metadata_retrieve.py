"""
metadata_retrieve.py — Pure metadata aggregation (no vector search).

analytical_retrieve   — COUNT queries: how many questions/commitments/decisions?
contribution_retrieve — VOLUME queries: who spoke the most?
signal_fetch_retrieve — CONTENT queries: list ALL chunks for a speaker+signal combo.
                        Used instead of compound when speaker+signal+yesno/list is needed —
                        hybrid search samples by relevance; this guarantees exhaustive results.
"""
import logging
from typing import Optional

from langchain_core.documents import Document

from app.services.storage.db import get_raw_collection

logger = logging.getLogger(__name__)


def analytical_retrieve(
    project_id: str,
    signal_filter: Optional[str] = None,
    date_where: Optional[dict] = None,
    named_speaker: Optional[str] = None,
) -> dict:
    """
    Pure metadata count — no vector search, no LLM counting.

    signal_filter: "question" | "commitment" | "decision" | "open_issue" | None
    Returns a structured dict the LLM formats into a count sentence.
    """
    collection = get_raw_collection()
    conditions: list[dict] = [{"project_id": {"$eq": project_id}}]
    if named_speaker:
        conditions.append({"speaker_name": {"$eq": named_speaker}})
    if date_where:
        conditions.append(date_where)
    where_filter = {"$and": conditions} if len(conditions) > 1 else conditions[0]

    logger.info(
        "  [analytical] signal=%s | speaker=%s | scope=%s",
        signal_filter or "none", named_speaker or "none", date_where or "all",
    )

    results  = collection.get(where=where_filter, include=["metadatas"])
    all_meta = [m for m in results.get("metadatas", []) if not m.get("is_meeting_summary")]

    signal_meta = (
        [m for m in all_meta if m.get(f"contains_{signal_filter}", False)]
        if signal_filter else all_meta
    )

    meetings: dict[str, str] = {}
    speakers: set[str] = set()
    for m in signal_meta:
        mid = m.get("meeting_id", "")
        if mid:
            meetings[mid] = m.get("meeting_title", mid)
        name = m.get("speaker_name", "")
        if name:
            speakers.add(name)

    result = {
        "total_chunks":  len(all_meta),
        "signal_count":  len(signal_meta),
        "meeting_count": len(meetings),
        "meetings":      list(meetings.values()),
        "speaker_count": len(speakers),
        "speakers":      sorted(speakers),
        "signal_filter": signal_filter,
        "named_speaker": named_speaker,
    }

    logger.info(
        "  [analytical] total=%d | signal=%d | %d meeting(s): [%s] | %d speaker(s): [%s]",
        result["total_chunks"],
        result["signal_count"],
        result["meeting_count"],
        ", ".join(result["meetings"][:5]),
        result["speaker_count"],
        ", ".join(result["speakers"][:5]),
    )
    return result


def contribution_retrieve(
    project_id: str,
    date_where: Optional[dict] = None,
) -> dict:
    """
    Speaker contribution ranking — chunk count per speaker.

    chunk_count is a proxy for speaking volume (each chunk ≈ 30-60s of speech).
    Returns speakers sorted most → least active.
    """
    collection = get_raw_collection()
    conditions: list[dict] = [{"project_id": {"$eq": project_id}}]
    if date_where:
        conditions.append(date_where)
    where_filter = {"$and": conditions} if len(conditions) > 1 else conditions[0]

    results      = collection.get(where=where_filter, include=["metadatas"])
    speaker_data: dict[str, dict] = {}

    for m in results.get("metadatas", []):
        if m.get("is_meeting_summary"):
            continue
        name = m.get("speaker_name", "")
        mid  = m.get("meeting_id", "")
        if not name:
            continue
        if name not in speaker_data:
            speaker_data[name] = {"chunk_count": 0, "meetings": set()}
        speaker_data[name]["chunk_count"] += 1
        if mid:
            speaker_data[name]["meetings"].add(mid)

    ranked = sorted(
        [
            {
                "speaker_name":  name,
                "chunk_count":   data["chunk_count"],
                "meeting_count": len(data["meetings"]),
            }
            for name, data in speaker_data.items()
        ],
        key=lambda x: x["chunk_count"],
        reverse=True,
    )

    logger.info("  contribution: %d speakers ranked", len(ranked))
    return {"ranked_speakers": ranked, "total_speakers": len(ranked)}


def signal_fetch_retrieve(
    project_id: str,
    named_speaker: str,
    signal_filter: str,
    scope_meeting_ids: Optional[list[str]] = None,
) -> list[Document]:
    """
    Exhaustive metadata fetch — returns ALL chunks for a speaker+signal combination.

    WHY this exists instead of compound_retrieve():
      compound_retrieve() uses hybrid search (BM25 + dense) → scores by relevance → top-N only.
      For "did X ask any questions?" or "list all commitments by X", you need EVERY matching
      chunk, not just the most semantically similar ones. Hybrid search misses chunks that are
      valid signal hits but score low on the query text.

    Use when: named_speaker + signal_filter + (is_yesno OR is_list_request)
    Do NOT use for open-ended speaker+topic queries ("what did X say about Y?") — those
    genuinely benefit from relevance ranking. Use compound_retrieve() for those.

    Returns chunks sorted chronologically (meeting_date ASC, start_time ASC).
    """
    collection = get_raw_collection()
    conditions: list[dict] = [
        {"project_id":     {"$eq": project_id}},
        {"speaker_name":   {"$eq": named_speaker}},
        {f"contains_{signal_filter}": {"$eq": True}},
        {"is_meeting_summary": {"$eq": False}},
    ]
    if scope_meeting_ids:
        if len(scope_meeting_ids) == 1:
            conditions.append({"meeting_id": {"$eq": scope_meeting_ids[0]}})
        else:
            conditions.append({"meeting_id": {"$in": list(scope_meeting_ids)}})

    where = {"$and": conditions}

    results = collection.get(where=where, include=["documents", "metadatas"])
    docs = [
        Document(
            page_content=results["documents"][i],
            metadata=results["metadatas"][i],
        )
        for i in range(len(results.get("ids", [])))
    ]
    docs.sort(key=lambda d: (
        d.metadata.get("meeting_date", ""),
        d.metadata.get("start_time") or 0,
    ))

    logger.info(
        "  [signal_fetch] speaker=%s | signal=%s | scope=%s → %d chunks",
        named_speaker, signal_filter,
        f"{len(scope_meeting_ids)} meeting(s)" if scope_meeting_ids else "project-wide",
        len(docs),
    )
    return docs
