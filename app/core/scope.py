"""
scope.py — Meeting scope / temporal filter resolution.

Answers the question: "which meetings should we search for this query?"
All time-related query phrases (previous meeting, last 7 days, May 9th, etc.)
flow through parse_meeting_scope() and come out as a single ChromaDB where-clause.
"""
import logging
import re
from datetime import date, timedelta

from app.core.storage.db import get_raw_collection

logger = logging.getLogger(__name__)

# ── Month name -> number ───────────────────────────────────────────────────────

_MONTH_MAP = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

_MONTH_PATTERN = "|".join(_MONTH_MAP.keys())

# Matches: "9th of May", "9 May", "May 9th", "May 9"
_DATE_RE = re.compile(
    r"\b(?:(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?(" + _MONTH_PATTERN + r")"
    r"|(" + _MONTH_PATTERN + r")\s+(\d{1,2})(?:st|nd|rd|th)?)\b",
    re.IGNORECASE,
)

_RELATIVE_DAYS_RE = re.compile(
    r"(?:previous|last|past)\s+(\d+)\s+(days?|weeks?)",
    re.IGNORECASE,
)
_LAST_N_MEETINGS_RE = re.compile(
    r"\b(?:last|previous|past)\s+(\d+)\s+meetings?\b",
    re.IGNORECASE,
)
_PREVIOUS_MEETING_RE = re.compile(
    r"\b(?:previous|last|most\s+recent|latest)\s+meeting\b",
    re.IGNORECASE,
)
_FIRST_MEETING_RE = re.compile(
    r"\b(?:first|earliest|oldest)\s+meeting\b",
    re.IGNORECASE,
)
# "that meeting" / "this meeting" -> most recent meeting (user refers to a specific one
# they have in mind, default to latest in the absence of other context)
_THAT_MEETING_RE = re.compile(
    r"\b(?:that|this)\s+meeting\b",
    re.IGNORECASE,
)
# "the second/third/fourth/fifth meeting" -> Nth meeting chronologically
_ORDINAL_MEETING_RE = re.compile(
    r"\bthe\s+(second|third|fourth|fifth|2nd|3rd|4th|5th)\s+meeting\b",
    re.IGNORECASE,
)
_ORDINAL_INDEX = {
    "second": 1, "2nd": 1,
    "third":  2, "3rd": 2,
    "fourth": 3, "4th": 3,
    "fifth":  4, "5th": 4,
}


def extract_month_day(query: str) -> tuple[int, int] | None:
    """
    Extract (month, day) from a query string.
    Returns None if no recognisable date phrase is found.
    Ignores year — all meetings are in the same year so month+day is enough.
    """
    m = _DATE_RE.search(query)
    if not m:
        return None
    if m.group(1) and m.group(2):       # "9th of May"
        return _MONTH_MAP[m.group(2).lower()], int(m.group(1))
    if m.group(3) and m.group(4):       # "May 9th"
        return _MONTH_MAP[m.group(3).lower()], int(m.group(4))
    return None


def get_project_meetings_sorted(project_id: str) -> list[tuple[str, str]]:
    """Return [(meeting_id, meeting_date), ...] sorted by date descending."""
    try:
        collection = get_raw_collection()
        results = collection.get(
            where={"project_id": {"$eq": project_id}},
            include=["metadatas"],
        )
        seen: dict[str, str] = {}
        seen_titles: dict[str, str] = {}
        for m in results.get("metadatas", []):
            mid   = m.get("meeting_id", "")
            d     = m.get("meeting_date", "")
            title = m.get("meeting_title", "")
            if mid and d and mid not in seen:
                seen[mid]        = d
                seen_titles[mid] = title
        sorted_meetings = sorted(seen.items(), key=lambda x: x[1], reverse=True)
        logger.debug(
            "  [scope] project meetings (newest->oldest): %s",
            " | ".join(
                f"{title!r} ({d}) [{mid[:12]}]"
                for mid, d in sorted_meetings
                for title in [seen_titles.get(mid, "?")]
            ),
        )
        return sorted_meetings
    except Exception:
        return []


def get_scoped_meeting_ids(scope_where: dict, project_id: str) -> set[str]:
    """
    Convert a ChromaDB where-clause back into a set of meeting_id strings.
    Used by retrieve_summary_chunks() and topic_summary_retrieve() to filter
    docs without an extra DB query.
    """
    if not scope_where:
        return set()

    if "$and" in scope_where:
        ids: set[str] = set()
        for clause in scope_where["$and"]:
            ids |= get_scoped_meeting_ids(clause, project_id)
        return ids

    if "meeting_id" in scope_where:
        val = scope_where["meeting_id"]
        if "$eq" in val:
            return {val["$eq"]}
        if "$in" in val:
            return set(val["$in"])

    if "meeting_date" in scope_where:
        val = scope_where["meeting_date"]
        cutoff = val.get("$gte")
        if cutoff:
            return {mid for mid, d in get_project_meetings_sorted(project_id) if d >= cutoff}

    return set()


def _log_scope_result(pattern_label: str, clause: "dict | None", sorted_meetings: list) -> None:
    """Log which pattern fired and which meeting(s) it resolved to."""
    if clause is None:
        logger.info("  [scope] pattern=%-22s -> NO MATCH (project-wide search)", pattern_label)
        return
    id_to_date = {mid: d for mid, d in sorted_meetings}
    if "$eq" in clause.get("meeting_id", {}):
        mid   = clause["meeting_id"]["$eq"]
        d_str = id_to_date.get(mid, "?")
        logger.info(
            "  [scope] pattern=%-22s -> 1 meeting  : %s (%s)",
            pattern_label, mid, d_str,
        )
    elif "$in" in clause.get("meeting_id", {}):
        ids = clause["meeting_id"]["$in"]
        names = [f"{m} ({id_to_date.get(m, '?')})" for m in ids]
        logger.info(
            "  [scope] pattern=%-22s -> %d meetings : %s",
            pattern_label, len(ids), " | ".join(names),
        )
    elif "meeting_date" in clause:
        logger.info(
            "  [scope] pattern=%-22s -> date range : %s",
            pattern_label, clause,
        )
    else:
        logger.info("  [scope] pattern=%-22s -> %s", pattern_label, clause)


def parse_meeting_scope(query: str, project_id: str) -> dict | None:
    """
    Single entry point for all temporal scope detection.
    Returns a ChromaDB where-clause dict, or None (search all meetings).

    Supported phrases:
      "previous meeting" / "last meeting"          -> latest meeting only
      "last N meetings" / "previous N meetings"    -> N most recent meetings
      "that meeting" / "this meeting"              -> latest meeting
      "the second/third/fourth meeting"            -> Nth chronologically
      "first meeting" / "earliest meeting"         -> oldest meeting only
      "previous N days" / "last N weeks"           -> meetings within date range
      "9th of May" / "May 9th"                     -> specific meeting by date (±1 day)
    """
    logger.info("  [scope] checking query: %r", query)

    # Check "last N meetings" before "last meeting" — more specific pattern first
    m = _LAST_N_MEETINGS_RE.search(query)
    if m:
        n = int(m.group(1))
        sorted_meetings = get_project_meetings_sorted(project_id)
        ids = [mid for mid, _ in sorted_meetings[:n]]
        if not ids:
            logger.info("  [scope] pattern=last_N_meetings     -> matched N=%d but NO meetings in project", n)
            return None
        clause = {"meeting_id": {"$eq": ids[0]}} if len(ids) == 1 else {"meeting_id": {"$in": ids}}
        _log_scope_result(f"last_{n}_meetings", clause, sorted_meetings)
        return clause

    if _PREVIOUS_MEETING_RE.search(query):
        sorted_meetings = get_project_meetings_sorted(project_id)
        if sorted_meetings:
            clause = {"meeting_id": {"$eq": sorted_meetings[0][0]}}
            _log_scope_result("previous_meeting", clause, sorted_meetings)
            return clause
        logger.info("  [scope] pattern=previous_meeting      -> matched but NO meetings in project")
        return None

    if _THAT_MEETING_RE.search(query):
        sorted_meetings = get_project_meetings_sorted(project_id)
        if sorted_meetings:
            clause = {"meeting_id": {"$eq": sorted_meetings[0][0]}}
            _log_scope_result("that/this_meeting", clause, sorted_meetings)
            return clause
        return None

    if _FIRST_MEETING_RE.search(query):
        sorted_meetings = get_project_meetings_sorted(project_id)
        if sorted_meetings:
            clause = {"meeting_id": {"$eq": sorted_meetings[-1][0]}}
            _log_scope_result("first_meeting", clause, sorted_meetings)
            return clause
        return None

    om = _ORDINAL_MEETING_RE.search(query)
    if om:
        ordinal = om.group(1).lower()
        idx = _ORDINAL_INDEX.get(ordinal, 1)
        sorted_meetings = get_project_meetings_sorted(project_id)
        # sorted descending: [-1]=oldest=1st, [-2]=2nd oldest, [-3]=3rd oldest…
        chron_idx = -(idx + 1)
        if len(sorted_meetings) >= idx + 1:
            clause = {"meeting_id": {"$eq": sorted_meetings[chron_idx][0]}}
            _log_scope_result(f"ordinal_{ordinal}", clause, sorted_meetings)
            return clause
        logger.info(
            "  [scope] pattern=ordinal_%s             -> not enough meetings (need %d, have %d)",
            ordinal, idx + 1, len(sorted_meetings),
        )
        return None

    dm = _RELATIVE_DAYS_RE.search(query)
    if dm:
        n    = int(dm.group(1))
        unit = dm.group(2).lower().rstrip("s")
        days = n if unit == "day" else n * 7
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        clause = {"meeting_date": {"$gte": cutoff}}
        logger.info(
            "  [scope] pattern=relative_days         -> last %d %s(s) -> cutoff=%s",
            n, unit, cutoff,
        )
        return clause

    month_day = extract_month_day(query)
    if month_day:
        target_month, target_day = month_day
        sorted_meetings = get_project_meetings_sorted(project_id)
        best_id, best_delta = None, 999
        for mid, d_str in sorted_meetings:
            try:
                md = date.fromisoformat(d_str)
                delta = abs((date(md.year, target_month, target_day) - md).days)
                if delta <= 1 and delta < best_delta:
                    best_id, best_delta = mid, delta
            except ValueError:
                continue
        if best_id:
            clause = {"meeting_id": {"$eq": best_id}}
            _log_scope_result(f"date_{target_month:02d}/{target_day:02d}", clause, sorted_meetings)
            return clause
        logger.info(
            "  [scope] pattern=specific_date         -> %02d/%02d found no meeting within ±1 day",
            target_month, target_day,
        )

    logger.info("  [scope] NO pattern matched -> project-wide search (all meetings)")
    return None
