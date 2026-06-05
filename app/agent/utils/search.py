"""
search.py — Search-time helpers: speaker resolution, exhaustive signal scan,
            and meeting diversity cap.

All three operate on the retrieved docs pool before or after hybrid_retrieve,
making them natural companions in one file.
"""

import logging
from collections import Counter
from typing import Optional

from langchain_core.documents import Document

from app.core.storage.db import get_raw_collection
from .constants import _SIGNAL_MAP, _fmt_ts, fmt_date
from .accumulator import _append_docs

logger = logging.getLogger(__name__)


# ── Diversity cap ─────────────────────────────────────────────────────────────
# Applied after hybrid_retrieve, before reranking. Project-wide queries only —
# bypassed when scope_ids is set (single-meeting queries need no diversity).
#
# _DIVERSITY_CAP_FLOOR: minimum slots guaranteed to every meeting in the pool.
# _DIVERSITY_PASS_RATE: fraction of a meeting's retrieved docs that pass through.
#   Each meeting contributes at most round(count × rate) chunks, floored at 3.
# _DIVERSITY_MAX_MEETING_FRACTION: the ceiling = round(total × fraction).
#   No single meeting exceeds this share of the reranker pool.
#   Scales with k automatically — at k=40: ceiling=10, at k=55: ceiling=13.

_DIVERSITY_CAP_FLOOR            = 3
_DIVERSITY_PASS_RATE            = 0.5   # each meeting passes half its retrieved docs
_DIVERSITY_MAX_MEETING_FRACTION = 0.25  # no meeting exceeds 25% of the reranker pool


def _apply_diversity_cap(
    docs: list[Document],
    floor: int = _DIVERSITY_CAP_FLOOR,
) -> list[Document]:
    """
    Limit chunks per meeting_id before reranking.

    Each meeting passes at most PASS_RATE of its retrieved docs, with a
    minimum of `floor` and a ceiling that scales with the total pool size
    (round(total × _DIVERSITY_MAX_MEETING_FRACTION)).

    floor is preset-driven:
      standard/broad/focused → floor=3 (default)
      temporal               → floor=6 (guarantees timeline coverage per meeting)

    RRF rank order is preserved within each meeting.
    Called only for project-wide queries (scope_ids=None in tools.py).
    """
    if not docs:
        return docs

    counts      = Counter(d.metadata.get("meeting_id", "") for d in docs)
    total       = len(docs)
    cap_ceiling = max(floor, round(total * _DIVERSITY_MAX_MEETING_FRACTION))

    seen:    dict[str, int] = {}
    diverse: list[Document] = []

    for doc in docs:
        mid = doc.metadata.get("meeting_id", "")
        cap = max(
            floor,
            min(cap_ceiling, round(counts[mid] * _DIVERSITY_PASS_RATE)),
        )
        if seen.get(mid, 0) < cap:
            diverse.append(doc)
            seen[mid] = seen.get(mid, 0) + 1

    logger.info(
        "  diversity_cap : input=%d | after_cap=%d | dropped=%d | ceiling=%d | floor=%d | meetings=%d",
        total, len(diverse), total - len(diverse), cap_ceiling, floor, len(counts),
    )
    for mid, kept in seen.items():
        logger.info(
            "    meeting_id=%s | retrieved=%d | kept=%d | dropped=%d",
            mid, counts[mid], kept, counts[mid] - kept,
        )
    return diverse


# ── Speaker name resolver ─────────────────────────────────────────────────────
# LLMs often guess names slightly wrong ("Bhavneet Mahajan" vs "Bhavneet Mhajan").
# ChromaDB $eq is exact-match only — wrong name = 0 results silently.

def _resolve_speaker_name(partial_name: str, project_id: str) -> Optional[str]:
    """
    Resolve a partial/approximate speaker name to the exact stored name.

    Resolution order (stops at first match):
      1. Exact match
      2. Case-insensitive exact
      3. All words in partial_name appear in candidate name
      4. First name only (safe only when unique in project)

    Returns None if no match — caller falls back to unfiltered search.
    """
    if not partial_name:
        return None
    try:
        collection = get_raw_collection()
        results    = collection.get(
            where={"project_id": {"$eq": project_id}},
            include=["metadatas"],
        )
        names: set[str] = {
            m["speaker_name"]
            for m in results.get("metadatas", [])
            if m.get("speaker_name") and not m.get("is_meeting_summary")
        }

        if partial_name in names:
            return partial_name

        partial_lower = partial_name.lower()
        for name in names:
            if name.lower() == partial_lower:
                return name

        partial_words = [w.lower() for w in partial_name.split() if w]
        if partial_words:
            word_matches = [n for n in names if all(pw in n.lower() for pw in partial_words)]
            if len(word_matches) == 1:
                return word_matches[0]

            first_matches = [n for n in names if n.lower().split()[0] == partial_words[0]]
            if len(first_matches) == 1:
                return first_matches[0]

        logger.info("_resolve_speaker_name | no match for %r | known: %s", partial_name, sorted(names))
        return None

    except Exception as exc:
        logger.warning("_resolve_speaker_name error: %s", exc)
        return None


# ── Exhaustive signal search ──────────────────────────────────────────────────
# Used by search_transcripts when signal_filter + scope_ids are both set.
# Completeness beats ranking here — must return ALL matching chunks, not top-k.

def _exhaustive_signal_search(
    project_id:    str,
    signal_filter: str,
    scope_ids:     list,
    speaker_name:  Optional[str] = None,
) -> str:
    """
    Fetch every chunk matching (project + signal + scope) via metadata scan.
    Sorted chronologically. Returns a formatted string for the LLM.
    """
    and_clauses: list[dict] = [
        {"project_id":               {"$eq": project_id}},
        {_SIGNAL_MAP[signal_filter]: {"$eq": True}},
        {"is_meeting_summary":       {"$ne": True}},
    ]
    if len(scope_ids) == 1:
        and_clauses.append({"meeting_id": {"$eq": scope_ids[0]}})
    else:
        and_clauses.append({"meeting_id": {"$in": scope_ids}})
    if speaker_name:
        and_clauses.append({"speaker_name": {"$eq": speaker_name}})

    try:
        collection = get_raw_collection()
        results    = collection.get(
            where={"$and": and_clauses},
            include=["documents", "metadatas"],
        )
    except Exception as exc:
        logger.warning("_exhaustive_signal_search error: %s", exc)
        return f"Search failed: {exc}"

    raw_docs  = results.get("documents", [])
    raw_metas = results.get("metadatas", [])

    if not raw_docs:
        return f"No '{signal_filter}' chunks found in the specified meeting(s)."

    docs = [Document(page_content=t, metadata=m) for t, m in zip(raw_docs, raw_metas)]
    docs.sort(key=lambda d: d.metadata.get("start_time", 0))

    chunk_numbers = _append_docs(docs)
    spk_note = f" by {speaker_name}" if speaker_name else ""
    lines: list[str] = [
        f"Found {len(docs)} '{signal_filter}' chunks{spk_note} "
        f"(complete scan of {len(scope_ids)} meeting(s) — all matches returned):\n"
    ]
    for doc, num in zip(docs, chunk_numbers):
        meta = doc.metadata
        ts   = _fmt_ts(meta.get("start_time"))
        lines.append(
            f"[{num}] {meta.get('speaker_name','Unknown')} {ts} — "
            f"{meta.get('meeting_title','Unknown Meeting')} ({fmt_date(meta.get('meeting_date',''))})"
        )
        lines.append(f"    {doc.page_content.strip()[:400]}")
        lines.append("")
    return "\n".join(lines)