"""
scope_llm.py — Two-stage LLM-based meeting scope resolver for the agent pipeline.

Replaces the regex-only parse_meeting_scope() in the agent path.
The old regex function still lives in app/core/scope.py.

Two-stage design
----------------
Stage 1  — LLM call (current query + meeting list, NO history in prompt).
           Returns: {scope_type, is_history_required, meeting_ids?, date_cutoff?}
           Cost: ~$0.0001, ~200ms using gemini-2.0-flash-lite.

           is_history_required=false → scope fully determined, done.
           is_history_required=true  → proceed to Stage 2.

Stage 2  — scope_parser() (pure Python, no LLM, ~5ms DB read).
           Reads the last non-project-wide scope from PostgreSQL.
           Applies simple inheritance rules — no second LLM call.

Failure contract (M4)
---------------------
Any exception in the LLM scope call is caught inside resolve_scope().
Fallback is always project-wide — never raises to the caller.
"""

import json
import logging
import os
import re
from datetime import date, timedelta
from typing import Optional, TYPE_CHECKING

from app.core.scope import get_project_meetings_sorted

if TYPE_CHECKING:
    from app.agent.chat_store import ChatStore

logger = logging.getLogger(__name__)

_SCOPE_MODEL = "gemini-2.5-flash-lite"

# ── Prompt ────────────────────────────────────────────────────────────────────

_SCOPE_PROMPT = """\
You are a meeting scope classifier for a Project Manager AI assistant.
Your ONLY job: determine which meetings the current query is about.

AVAILABLE MEETINGS (this project only — use ONLY these IDs):
{meeting_list}

CURRENT QUERY: "{query}"

TODAY'S DATE: {today}

Return ONLY valid JSON — no explanation, no markdown, no extra text:
{{
  "scope_type": "project" | "meeting" | "date_range",
  "is_history_required": true | false,
  "meeting_ids": [...] or null,
  "date_cutoff": "YYYY-MM-DD" or null
}}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SCOPE RULES (is_history_required = false — resolve from query alone)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"last/previous/latest/most recent meeting"
  → scope_type="meeting", meeting_ids=[<latest id>]

"first/earliest/oldest meeting"
  → scope_type="meeting", meeting_ids=[<oldest id>]

"last N meetings" / "previous N meetings"
  → scope_type="meeting", meeting_ids=[<N most recent ids>]

"the second/third/fourth/fifth/sixth meeting"
  → scope_type="meeting", meeting_ids=[<Nth oldest id>]

"Meeting #N" or "Meeting N" (number reference)
  → scope_type="meeting", meeting_ids=[<matching id by meeting_number>]

"[Month] [Day]" e.g. "May 9th", "April 15th", "9th of May"
  → scope_type="meeting", meeting_ids=[<id of meeting closest to that date>]

"last N days/weeks" / "past N days"
  → scope_type="date_range", date_cutoff="YYYY-MM-DD" (today minus N days/weeks)

"last week"   → date_cutoff = today minus 7 days
"last month"  → date_cutoff = today minus 30 days
"last year"   → date_cutoff = today minus 365 days
"since [date]" → date_cutoff = that date

"across all meetings" / "in this project" / "overall" / "in total"
  → scope_type="project", is_history_required=false

Explicit metadata queries ("how many meetings?", "list all speakers", "list meetings")
  → scope_type="project", is_history_required=false

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONTEXT RULES (is_history_required = true — need prior conversation to resolve)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"that meeting" / "those meetings" / "this meeting"
  → scope_type="meeting", is_history_required=true

"that session" / "those sessions" / "that call" / "those calls"
  → scope_type="meeting", is_history_required=true

"the same meeting" / "both meetings"
  → scope_type="meeting", is_history_required=true

"during that period" / "during that time" / "that time frame" / "that timeframe"
  → scope_type="date_range", is_history_required=true

Pronouns referring to a prior speaker: "he said", "she committed", "they decided"
  → scope_type="project", is_history_required=true

Short ambiguous follow-up with no explicit scope:
  e.g. "Was AI discussed?", "What about the budget?", "And the timeline?"
  → scope_type="project", is_history_required=true

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FIELD RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
meeting_ids  : Populate ONLY when scope_type="meeting" AND is_history_required=false.
               Use ONLY IDs from the AVAILABLE MEETINGS list above. Never invent IDs.

date_cutoff  : Populate ONLY when scope_type="date_range" AND is_history_required=false.
               Format: YYYY-MM-DD.

CONSERVATIVE RULE: When uncertain → set is_history_required=true.
  Cost of false positive: one cheap DB read (~5ms).
  Cost of false negative: wrong meeting searched → wrong answer.
"""


# ── Stage 1: LLM call ────────────────────────────────────────────────────────

def _format_meeting_list(meetings: list[tuple[str, str]]) -> str:
    """Format meeting list for the scope prompt."""
    lines = []
    for i, (mid, mdate) in enumerate(meetings):
        ordinal = i + 1
        # newest-first list: ordinal 1 = latest
        lines.append(f"  ID={mid}  date={mdate}  (meeting #{ordinal} from newest)")
    return "\n".join(lines) if lines else "  (no meetings in this project)"


def _call_scope_llm(query: str, meetings: list[tuple[str, str]]) -> dict:
    """
    Call Gemini to classify the scope of the query.
    Uses google.genai directly (same pattern as gemini_client.py) with retry.
    Returns a raw dict — caller must validate with _validate_stage1().
    """
    import time
    from google import genai
    from app.config import Config

    api_key = Config.GEMINI_API_KEY
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")

    prompt = _SCOPE_PROMPT.format(
        meeting_list=_format_meeting_list(meetings),
        query=query,
        today=date.today().isoformat(),
    )

    client     = genai.Client(api_key=api_key)
    max_tries  = 3
    delays     = [1, 3, 6]
    last_exc: Exception | None = None

    for attempt in range(max_tries):
        try:
            response = client.models.generate_content(
                model=_SCOPE_MODEL,
                contents=prompt,
                config={"temperature": 0.0, "max_output_tokens": 256},
            )
            raw_text = response.text.strip()

            # Strip markdown code fences if present
            raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
            raw_text = re.sub(r"\s*```$", "", raw_text)

            return json.loads(raw_text)

        except json.JSONDecodeError as exc:
            logger.warning(
                "scope_llm | JSON parse failed (attempt %d): %s — raw=%r",
                attempt + 1, exc, response.text[:200] if "response" in dir() else "?",
            )
            last_exc = exc
            # Don't retry JSON errors — the model gave bad output, retrying rarely helps
            raise

        except Exception as exc:
            last_exc = exc
            msg = str(exc).lower()
            is_transient = any(k in msg for k in ("503", "429", "unavailable", "rate limit"))
            if is_transient and attempt < max_tries - 1:
                logger.warning(
                    "scope_llm | transient error (attempt %d/%d) — retry in %ds: %s",
                    attempt + 1, max_tries, delays[attempt], exc,
                )
                time.sleep(delays[attempt])
            else:
                raise

    raise RuntimeError(f"scope_llm failed after {max_tries} attempts") from last_exc


# ── Stage 1: validation ───────────────────────────────────────────────────────

def _validate_stage1(result: dict, known_ids: set[str]) -> dict:
    """
    F5 FIX: Sanitise every field of the LLM output before use.

    Hallucinated meeting IDs, wrong types, or bad date formats would otherwise
    flow into scope_parser and then into ChromaDB → 0 results → wrong answers.

    Any invalid output falls back to project-wide safe default.
    """
    _SAFE: dict = {
        "scope_type":          "project",
        "is_history_required": False,
        "meeting_ids":         None,
        "date_cutoff":         None,
    }

    try:
        # scope_type
        if result.get("scope_type") not in ("project", "meeting", "date_range"):
            logger.warning(
                "scope_llm | unknown scope_type=%r — fallback project-wide",
                result.get("scope_type"),
            )
            return _SAFE

        # is_history_required must be bool
        if not isinstance(result.get("is_history_required"), bool):
            result["is_history_required"] = True    # conservative default

        # meeting_ids — validate every ID against known ChromaDB IDs
        raw_ids = result.get("meeting_ids")
        if raw_ids is not None:
            if not isinstance(raw_ids, list):
                logger.warning("scope_llm | meeting_ids not a list: %r", raw_ids)
                return _SAFE
            valid_ids = [i for i in raw_ids if isinstance(i, str) and i in known_ids]
            if not valid_ids:
                logger.warning(
                    "scope_llm | all meeting_ids invalid %r (known %d) — project-wide",
                    raw_ids, len(known_ids),
                )
                return _SAFE
            if len(valid_ids) < len(raw_ids):
                logger.warning(
                    "scope_llm | %d/%d meeting_ids were hallucinated — keeping %s",
                    len(raw_ids) - len(valid_ids), len(raw_ids), valid_ids,
                )
            result["meeting_ids"] = valid_ids

        # date_cutoff must parse as ISO date
        cutoff = result.get("date_cutoff")
        if cutoff is not None:
            try:
                date.fromisoformat(str(cutoff))
            except ValueError:
                logger.warning("scope_llm | bad date_cutoff=%r — cleared", cutoff)
                result["date_cutoff"] = None
                result["scope_type"]  = "project"

        return result

    except Exception as e:
        logger.warning("scope_llm | _validate_stage1 crashed (%s) — safe default", e)
        return _SAFE


# ── Stage 1: result builder ───────────────────────────────────────────────────

def _build_result_from_stage1(stage1: dict, meetings: list[tuple[str, str]]) -> dict:
    """Convert a validated Stage 1 dict into the scope result dict for AgentState."""
    scope_type = stage1["scope_type"]

    if scope_type == "meeting":
        ids         = stage1["meeting_ids"]     # already validated, non-empty
        scope_where = (
            {"meeting_id": {"$eq": ids[0]}}
            if len(ids) == 1
            else {"meeting_id": {"$in": ids}}
        )
        return _make_result("meeting", scope_where, ids)

    if scope_type == "date_range":
        cutoff = stage1["date_cutoff"]
        # meetings already has normalized ISO dates from get_project_meetings_sorted().
        # Using meeting_id filter instead of meeting_date string comparison avoids a
        # type mismatch in ChromaDB: older meetings store meeting_date as epoch int,
        # newer ones as ISO string — "$gte ISO-string" silently skips epoch-int rows.
        matching_ids = [mid for mid, d in meetings if d >= cutoff]
        if not matching_ids:
            return _make_result("project", None, None)
        scope_where = (
            {"meeting_id": {"$eq": matching_ids[0]}}
            if len(matching_ids) == 1
            else {"meeting_id": {"$in": matching_ids}}
        )
        return _make_result("date_range", scope_where, None)

    # project-wide
    return _make_result("project", None, None)


def _make_result(
    scope_type:  str,
    scope_where: Optional[dict],
    scope_ids:   Optional[list],
) -> dict:
    """Build the final scope dict written into AgentState."""
    n = len(scope_ids) if scope_ids else 0

    if scope_type == "project":
        recommended_k = 25
    elif scope_type == "meeting":
        recommended_k = min(15 + (n - 1) * 5, 25) if n > 0 else 15
    else:  # date_range
        recommended_k = 20

    return {
        "scope_where":   scope_where,
        "scope_ids":     scope_ids,
        "scope_type":    scope_type,
        "recommended_k": recommended_k,
    }


# ── Stage 2: scope_parser ────────────────────────────────────────────────────

def _build_id_clause(ids: list[str]) -> dict:
    return (
        {"meeting_id": {"$eq": ids[0]}}
        if len(ids) == 1
        else {"meeting_id": {"$in": ids}}
    )


def _scope_parser(
    stage1:     dict,
    prev_scope: Optional[dict],
    query:      str,
    meetings:   list[tuple[str, str]],
    project_id: str,
) -> dict:
    """
    Pure Python — no LLM call.
    Resolves the final scope when Stage 1 flagged is_history_required=true.

    Six combinations of (stage1.scope_type × prev_scope.scope_type):

    meeting  + prev=meeting     → inherit prev meeting IDs
    meeting  + prev=date_range  → inherit prev date filter
    meeting  + prev=project/None→ fallback: latest meeting
    date_range + prev=date_range→ inherit prev date_where clause exactly
    date_range + prev=other     → fallback: project-wide
    project  + prev=meeting     → short query (≤8 words) → inherit meeting
    project  + prev=other       → project-wide
    """
    scope_type = stage1["scope_type"]
    prev_type  = prev_scope.get("scope_type")  if prev_scope else None
    prev_ids   = prev_scope.get("scope_ids")   if prev_scope else None
    prev_where = prev_scope.get("scope_where") if prev_scope else None

    # ── "that meeting" / "those sessions" ────────────────────────────────────
    if scope_type == "meeting":
        if prev_type == "meeting" and prev_ids:
            scope_where = _build_id_clause(prev_ids)
            logger.info(
                "scope_parser | 'that meeting' → inherited prev meeting scope: ids=%s\n"
                "               ► NEXT: search_transcripts will be locked to these meetings",
                prev_ids,
            )
            return _make_result("meeting", scope_where, prev_ids)

        if prev_type == "date_range" and prev_where:
            logger.info(
                "scope_parser | 'that meeting' + prev=date_range → inherited date filter\n"
                "               ► NEXT: search_transcripts will use the same date range"
            )
            return _make_result("date_range", prev_where, None)

        # No useful prev scope — fall back to latest meeting
        latest = meetings[0][0] if meetings else None
        latest_date = meetings[0][1] if meetings else "?"
        if latest:
            logger.info(
                "scope_parser | 'that meeting' + no prev scope → fallback to latest meeting\n"
                "               latest=%s (%s)\n"
                "               ► NEXT: search_transcripts will search this meeting",
                latest, latest_date,
            )
            return _make_result(
                "meeting", {"meeting_id": {"$eq": latest}}, [latest]
            )
        return _make_result("project", None, None)

    # ── "during that period" ──────────────────────────────────────────────────
    if scope_type == "date_range":
        if prev_type == "date_range" and prev_where:
            logger.info(
                "scope_parser | 'during that period' → inherited prev date filter\n"
                "               ► NEXT: search_transcripts will use the same date range"
            )
            return _make_result("date_range", prev_where, None)
        logger.info(
            "scope_parser | 'during that period' + no prev date_range → project-wide\n"
            "               ► NEXT: agent will search all meetings"
        )
        return _make_result("project", None, None)

    # ── Implicit continuation ("Was AI discussed?", pronouns) ─────────────────
    # scope_type == "project"
    query_words = len(query.strip().split())
    if query_words <= 8 and prev_type == "meeting" and prev_ids:
        scope_where = _build_id_clause(prev_ids)
        logger.info(
            "scope_parser | short implicit follow-up (%d words) + prev=meeting\n"
            "               → inherited prev scope: ids=%s\n"
            "               ► NEXT: agent will search within this meeting scope",
            query_words, prev_ids,
        )
        return _make_result("meeting", scope_where, prev_ids)

    logger.info(
        "scope_parser | project-wide (prev=%s, query_words=%d)\n"
        "               ► NEXT: agent will search across all %d meetings",
        prev_type, query_words, len(meetings),
    )
    return _make_result("project", None, None)


# ── Public entry point ────────────────────────────────────────────────────────

def resolve_scope(
    query:      str,
    project_id: str,
    session_id: Optional[str],
    chat_store: Optional["ChatStore"],
) -> dict:
    """
    Full two-stage scope resolution.
    Returns a dict with keys: scope_where, scope_ids, scope_type, recommended_k.

    M4 FAILURE CONTRACT: any exception in the LLM scope call is caught here.
    Fallback is always project-wide — resolve_scope() never raises to the caller.
    """
    _PROJECT_WIDE = _make_result("project", None, None)

    meetings = get_project_meetings_sorted(project_id)
    if not meetings:
        logger.info("scope_llm | no meetings found for project=%s", project_id)
        return _PROJECT_WIDE

    known_ids = {m[0] for m in meetings}

    # ── Stage 1: LLM scope classification ────────────────────────────────────
    logger.info("scope_llm | ► STAGE 1 — sending query to Gemini scope classifier...")
    try:
        stage1 = _call_scope_llm(query, meetings)
        stage1 = _validate_stage1(stage1, known_ids)
    except Exception as e:
        logger.warning(
            "scope_llm | Stage 1 LLM failed (%s) — fallback project-wide\n"
            "            ► NEXT: agent will search all %d meetings",
            e, len(meetings),
        )
        return _PROJECT_WIDE

    logger.info(
        "scope_llm | Stage 1 result → scope_type=%-12s  is_history_required=%-5s  "
        "ids=%-30s  cutoff=%s",
        stage1["scope_type"],
        stage1["is_history_required"],
        stage1.get("meeting_ids"),
        stage1.get("date_cutoff"),
    )

    # ── Stage 1 resolved fully — no history needed ────────────────────────────
    if not stage1["is_history_required"]:
        result = _build_result_from_stage1(stage1, meetings)
        logger.info(
            "scope_llm | Scope resolved (no history needed) → type=%s  ids=%s\n"
            "            ► NEXT: agent LLM will search within this scope",
            result["scope_type"], result["scope_ids"],
        )
        return result

    # ── Stage 2: load previous scope from DB, run scope_parser ───────────────
    logger.info(
        "scope_llm | ► STAGE 2 — query has contextual reference, loading previous "
        "scope from PostgreSQL..."
    )
    prev_scope: Optional[dict] = None
    if chat_store and session_id:
        prev_scope = chat_store.get_last_non_project_scope(session_id)
        if prev_scope:
            logger.info(
                "scope_llm | Previous scope found → type=%s  ids=%s\n"
                "            ► NEXT: scope_parser will inherit this scope",
                prev_scope.get("scope_type"), prev_scope.get("scope_ids"),
            )
        else:
            logger.info(
                "scope_llm | No previous scoped turn found (first turn or all project-wide)\n"
                "            ► NEXT: scope_parser will use fallback logic"
            )
    else:
        logger.info(
            "scope_llm | No session_id / store — skipping DB lookup\n"
            "            ► NEXT: scope_parser will use fallback logic"
        )

    logger.info("scope_llm | ► STAGE 2 — running scope_parser (pure Python, no LLM)...")
    result = _scope_parser(stage1, prev_scope, query, meetings, project_id)
    logger.info(
        "scope_llm | Scope resolved (via history) → type=%s  ids=%s\n"
        "            ► NEXT: agent LLM will search within this scope",
        result["scope_type"], result["scope_ids"],
    )
    return result