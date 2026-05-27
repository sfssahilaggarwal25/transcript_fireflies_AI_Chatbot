import logging
import re
from datetime import date

from app.rag.query_intent import QueryIntent
from app.core.storage.db import get_raw_collection
from app.core.scope import parse_meeting_scope, get_scoped_meeting_ids
from app.clients.gemini_client import call_gemini

logger = logging.getLogger(__name__)

_TIMING_RE = re.compile(
    r"\btimings?\b|\bduration\b|\bhow long\b|"
    r"\bwhen did.{0,20}meeting.{0,10}start\b|"
    r"\bwhat time.{0,20}meeting\b",
    re.IGNORECASE,
)

_ATTENDANCE_RE = re.compile(
    r"\bpeople\b|\bpersons?\b|\bparticipants?\b|\battendees?\b|"
    r"\bwho (?:was|were|attended|joined|participated)\b",
    re.IGNORECASE,
)


def _get_meeting_timings(project_id: str) -> list[dict]:
    """Return [{meeting_id, meeting_title, meeting_date, duration_minutes}, ...]
    sorted by date. Duration estimated from max(end_time) across all chunks."""
    collection = get_raw_collection()
    results = collection.get(
        where={"project_id": {"$eq": project_id}},
        include=["metadatas"],
    )
    meetings: dict[str, dict] = {}
    for m in results.get("metadatas", []):
        if m.get("is_meeting_summary"):
            continue
        mid = m.get("meeting_id", "")
        if not mid:
            continue
        if mid not in meetings:
            meetings[mid] = {
                "meeting_id":    mid,
                "meeting_title": m.get("meeting_title", ""),
                "meeting_date":  m.get("meeting_date", ""),
                "max_end_time":  None,
            }
        et = m.get("end_time")
        if et is not None:
            cur = meetings[mid]["max_end_time"]
            meetings[mid]["max_end_time"] = max(cur, et) if cur is not None else et

    result = []
    for info in sorted(meetings.values(), key=lambda x: x["meeting_date"]):
        max_end = info["max_end_time"]
        duration_min = round(max_end / 60) if max_end is not None else None
        result.append({
            "meeting_id":       info["meeting_id"],
            "meeting_title":    info["meeting_title"],
            "meeting_date":     info["meeting_date"],
            "duration_minutes": duration_min,
        })
    return result


def handle_metadata_query(query: str, project_id: str) -> dict:
    """
    Answer structural queries (list meetings, list speakers, count meetings,
    meeting timings, attendance).
    Applies temporal scope filtering when the query contains a time reference.
    Uses LLM to format a natural language answer.
    """
    collection = get_raw_collection()
    results = collection.get(
        where={"project_id": {"$eq": project_id}},
        include=["metadatas"],
    )
    metadatas = results.get("metadatas", [])

    q = query.lower()
    scope_where = parse_meeting_scope(query, project_id)
    scoped_ids  = get_scoped_meeting_ids(scope_where, project_id) if scope_where else set()

    # ── Timing query ──────────────────────────────────────────────────────────
    if _TIMING_RE.search(q):
        timings = _get_meeting_timings(project_id)
        if scoped_ids:
            timings = [t for t in timings if t["meeting_id"] in scoped_ids]

        lines = []
        for t in timings:
            dur = f"{t['duration_minutes']} min" if t["duration_minutes"] is not None else "duration unknown"
            lines.append(f"  • {t['meeting_date']} — {t['meeting_title']} ({dur})")

        structured_data = (
            f"Total meetings: {len(timings)}\n"
            f"Meeting timings:\n" + ("\n".join(lines) if lines else "  (none)")
        )

    # ── Speaker / people / attendance query ───────────────────────────────────
    elif any(w in q for w in ["speaker", "who are", "who was"]) or _ATTENDANCE_RE.search(q):
        # Build speaker list, optionally scoped to a specific meeting
        seen_speakers: set[tuple] = set()
        for m in metadatas:
            name = m.get("speaker_name", "")
            role = m.get("speaker_role", "")
            mid  = m.get("meeting_id", "")
            if name and not m.get("is_meeting_summary"):
                if not scoped_ids or mid in scoped_ids:
                    seen_speakers.add((name, role))
        speakers = sorted(seen_speakers, key=lambda x: x[0])

        scope_note = f" (scoped to {len(scoped_ids)} meeting(s))" if scoped_ids else ""
        speaker_lines = "\n".join(
            f"  • {name}" + (f" — {role}" if role else "")
            for name, role in speakers
        )
        structured_data = (
            f"Total speakers{scope_note}: {len(speakers)}\n"
            f"Speakers:\n{speaker_lines if speaker_lines else '  (none)'}"
        )
        date_note = ""

    # ── Meeting query (count / list / when) ───────────────────────────────────
    else:
        seen_meetings: dict[str, tuple[str, str]] = {}
        for m in metadatas:
            mid   = m.get("meeting_id", "")
            title = m.get("meeting_title", "")
            d     = m.get("meeting_date", "")
            if mid and title and d and mid not in seen_meetings:
                seen_meetings[mid] = (d, title)

        all_meetings = sorted(seen_meetings.values())

        date_note = ""
        if scoped_ids:
            filtered = [
                (d, t) for mid, (d, t) in seen_meetings.items()
                if mid in scoped_ids
            ]
            date_note = f"Filter: {len(filtered)} specific meeting(s) matched"
            logger.info(
                "  scope filter: %d → %d/%d meetings match",
                len(scoped_ids), len(filtered), len(all_meetings),
            )
        else:
            filtered = all_meetings

        summary_results = collection.get(
            where={
                "$and": [
                    {"project_id": {"$eq": project_id}},
                    {"is_meeting_summary": {"$eq": True}},
                ]
            },
            include=["documents", "metadatas"],
        )
        summaries: dict[str, str] = {}
        for i, sm in enumerate(summary_results.get("metadatas", [])):
            mid = sm.get("meeting_id", "")
            if mid:
                summaries[mid] = summary_results["documents"][i][:400].strip()

        meeting_lines = []
        for d_str, title in filtered:
            mid_key = next(
                (mid for mid, (d2, t2) in seen_meetings.items() if d2 == d_str and t2 == title),
                None,
            )
            summary_snippet = summaries.get(mid_key, "")
            if summary_snippet:
                meeting_lines.append(f"  • {d_str} — {title}\n    Summary: {summary_snippet[:250]}")
            else:
                meeting_lines.append(f"  • {d_str} — {title}")

        structured_data = (
            f"Total meetings matching query: {len(filtered)}\n"
            f"Total meetings in project: {len(all_meetings)}\n"
            + (f"{date_note}\n" if date_note else "")
            + "Meetings:\n"
            + ("\n".join(meeting_lines) if meeting_lines else "  (none in this range)")
        )

    # ── LLM formats the final answer ──────────────────────────────────────────
    prompt = (
        f"You are a meeting intelligence assistant for a project manager.\n"
        f"The user asked: \"{query}\"\n\n"
        f"Here is the data from the project:\n"
        f"{structured_data}\n\n"
        f"Instructions:\n"
        f"- Answer the user's question naturally and accurately.\n"
        f"- If they asked 'how many', lead with the count as a direct answer.\n"
        f"- If a date filter was applied and no meetings match, say so clearly and "
        f"mention what the most recent meeting date was.\n"
        f"- If meeting summaries are provided, briefly mention what each meeting covered.\n"
        f"- Keep the answer concise and helpful."
    )

    try:
        answer = call_gemini(prompt)
    except Exception as e:
        logger.warning("Metadata LLM call failed — using structured fallback: %s", e)
        answer = structured_data

    logger.info("  metadata   : answered with LLM formatting + scope=%s", scope_where)
    return {
        "answer": answer,
        "sources": [],
        "intent": QueryIntent.METADATA.value,
        "notice": None,
    }
