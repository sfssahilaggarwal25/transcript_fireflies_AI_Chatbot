import json
import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

from pydantic import BaseModel

from app.services.prompts import (
    UNDERSTANDING_PROMPT_MEETING_LEVEL,
    UNDERSTANDING_PROMPT_PROJECT_LEVEL,
)

logger = logging.getLogger(__name__)


class QueryIntent(str, Enum):
    GENERAL      = "general_query"
    DECISION     = "decision_query"
    COMMITMENT   = "commitment_query"
    QUESTION     = "question_query"
    SUMMARY      = "summary_query"
    SPEAKER      = "speaker_query"
    TIMELINE     = "timeline_query"
    METADATA     = "metadata_query"
    # New intents for Phase 2–4 routing
    ANALYTICAL   = "analytical_query"
    TOPIC_SUMMARY = "topic_summary_query"
    ATTRIBUTION  = "attribution_query"
    CONTRIBUTION = "contribution_query"


# ── Regex fallback ────────────────────────────────────────────────────────────
# Used when the LLM call fails or returns invalid JSON.
# Intentionally narrow — the LLM handles the hard cases.

_DECISION_RE = re.compile(
    r"\b(decision|decisions|decided|agreed|finalized|approved|confirmed|"
    r"what was decided|what did we decide|final decision)\b",
    re.IGNORECASE,
)
_COMMITMENT_RE = re.compile(
    r"\b(commitment|commitments|action item|action items|follow up|follow-up|"
    r"who will|who committed|what needs to be done|next steps|deliverable|deliverables)\b",
    re.IGNORECASE,
)
_SUMMARY_RE = re.compile(
    r"\b(summary|summarize|overview|recap|progress summary|project summary|high level summary)\b",
    re.IGNORECASE,
)
_SPEAKER_RE = re.compile(
    r"(what did (?!we\b|they\b|it\b|the\b|you\b).+? (?:say|mention|discuss|state|think)\b|"
    r"what (?:has|have) (?!we\b|they\b|it\b|the\b|you\b).+? (?:said|mentioned|discussed|stated)\b|"
    r"what was .+? saying\b|according to|who said)",
    re.IGNORECASE,
)
_QUESTION_RE = re.compile(
    r"\b(question|questions|what did they ask|what was asked|client questions)\b",
    re.IGNORECASE,
)
_TIMELINE_RE = re.compile(
    r"(\b(?:timeline|deadline|due date|schedule|roadmap)\b|"
    r"\b(?:last week|last month|this week|historically|over time)\b|"
    r"\bwhat changed\b|\bhow (?:has|did|have|were?).{0,30}changed?\b|"
    r"\bchanged? (?:since|between|across|from)\b|\bevolved?\b|"
    r"\bbetween (?:the )?(?:two|both|meetings?|meeting \d|first|second|last)\b|"
    r"\bacross (?:both|the|all|meetings?)\b|"
    r"\bcompared? to (?:the )?(?:first|second|last|previous|earlier)\b|"
    r"\bprevious meeting\b|\bfirst meeting\b|\bsecond meeting\b|"
    r"\bfrom .{0,20} to .{0,20} meeting\b)",
    re.IGNORECASE,
)


_METADATA_RE = re.compile(
    r"\bhow many meetings?\b"
    r"|\blist (?:all )?(?:the )?meetings?\b"
    r"|\blist (?:all )?(?:the )?speakers?\b"
    r"|\bshow (?:all )?(?:the )?meetings?\b"
    r"|\bshow (?:all )?(?:the )?speakers?\b"
    r"|\bwho are (?:all )?(?:the )?speakers?\b"
    r"|\bwhat meetings?\b.{0,20}\bproject\b"
    r"|\bwhen was.{0,15}(?:last|latest|first|recent) meeting\b"
    r"|\ball (?:the )?meetings? in this project\b"
    # timing queries
    r"|\btimings? of (?:the )?meetings?\b"
    r"|\bwhat (?:are|were) (?:the )?(?:meeting )?timings?\b"
    r"|\bwhen did (?:the )?meetings? (?:start|take place|happen|occur)\b"
    r"|\bwhat time (?:did|were|was|do) (?:the )?meetings?\b"
    r"|\bhow long (?:was|were|did) (?:the )?meetings?\b"
    r"|\bduration of (?:the )?meetings?\b"
    # attendance queries
    r"|\bhow many (?:people|persons?|participants?|attendees?)\b"
    r"|\bhow many speakers?\b"
    r"|\bwho (?:was|were|attended|participated) in (?:the )?(?:previous|last|this|that|first) meeting\b"
    r"|\bwho (?:attended|participated in|joined|was present in) (?:the )?\w+ meeting\b",
    re.IGNORECASE,
)


def is_metadata_query(query: str) -> bool:
    """
    Fast regex pre-check — runs before the LLM classifier.
    Returns True for pure structural queries (list meetings, list speakers,
    count meetings, last meeting date) that need zero semantic search.
    Kept narrow intentionally: misses go to the full pipeline, not vice versa.
    """
    return bool(_METADATA_RE.search(query.strip()))


def _regex_fallback(query: str) -> QueryIntent:
    """Regex classifier — only runs when the LLM call fails."""
    if _DECISION_RE.search(query):   return QueryIntent.DECISION
    if _COMMITMENT_RE.search(query): return QueryIntent.COMMITMENT
    if _SUMMARY_RE.search(query):    return QueryIntent.SUMMARY
    if _SPEAKER_RE.search(query):    return QueryIntent.SPEAKER
    if _QUESTION_RE.search(query):   return QueryIntent.QUESTION
    if _TIMELINE_RE.search(query):   return QueryIntent.TIMELINE
    return QueryIntent.GENERAL


# ── Public interface ──────────────────────────────────────────────────────────

def classify_query_intent(query: str, project_id: str = "") -> QueryIntent:
    """
    Return the `intent_type` from a full `understand_query()` call.

    This is a thin wrapper kept for backward compatibility (used in trace_query.py
    and legacy callers). All routing and dimensional enrichment is handled inside
    `understand_query()` — do NOT add new logic here.

    For production code use `understand_query(query, project_id)` directly so you
    get the full `QueryUnderstanding` object with `retrieval_mode`, `output_format`,
    `named_speaker`, `signal_filter`, and `dimensions`.
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    understanding = understand_query(query.strip(), project_id)
    return understanding.intent_type


# ── Query dimensions — semantic (LLM) + syntactic (Python regex) ─────────────

class QueryDimensions(BaseModel):
    # LLM fills these (semantic understanding)
    has_topic:        bool = False  # named concept in query ("AI architecture", "feedback")
    is_cross_meeting: bool = False  # needs synthesis across multiple meetings
    needs_traces:     bool = False  # user wants citations ("with traces", "with sources")
    is_contribution:  bool = False  # "who spoke most" — speaker volume analysis

    # Python fills these (deterministic regex — never sent to LLM)
    is_count:         bool = False  # "how many", "total X", "number of"
    is_yesno:         bool = False  # first word is auxiliary verb ("Did", "Was", "Any")
    is_ranking:       bool = False  # "which came first/last/most"
    is_list_request:  bool = False  # "what topics/items/issues were discussed?"
    has_temporal:     bool = False  # parse_meeting_scope() found a time reference


# ── Flexible query understanding (Step 1 — production pipeline) ───────────────

class QueryUnderstanding(BaseModel):
    topic:           str                  # main subject, 1-10 words
    intent_type:     QueryIntent          # for prompt template selection
    named_speaker:   Optional[str] = None # canonicalized speaker name if any
    needs_summary:   bool = False         # True → fetch summary chunks, skip vector search
    temporal_focus:  Optional[str] = None # "cross_meeting" → per-meeting timeline retrieval
    signal_filter:   Optional[str] = None # "question"|"commitment"|"decision"|"open_issue"|"document_share"
    # Routing outputs — set by _post_process_understanding(), not the LLM
    retrieval_mode:  str = "hybrid"       # which retrieval function to call
    output_format:   str = "prose"        # how the LLM should structure its answer
    dimensions:      QueryDimensions = QueryDimensions()
    # Scope — resolved once here, propagated to all retrieval functions
    # Empty list = project-level (search all meetings); non-empty = locked to these meeting IDs
    scope_meeting_ids: list[str] = []
    scope_type:        str = "project"   # "meeting" | "project"


def _build_understanding_from_regex(query: str) -> QueryUnderstanding:
    intent = _regex_fallback(query)
    return QueryUnderstanding(
        topic=query[:80],
        intent_type=intent,
        needs_summary=(intent == QueryIntent.SUMMARY),
        temporal_focus="cross_meeting" if intent == QueryIntent.TIMELINE else None,
    )


# ── Layer 2 — Python syntactic dimension filling ─────────────────────────────

def _fill_syntactic_dimensions(
    u: QueryUnderstanding, query: str, project_id: str
) -> "dict | None":
    """
    Fill deterministic regex-based fields.

    Scope (has_temporal / scope_meeting_ids) is handled differently depending
    on the call path:
    - Normal path (understand_query): scope already pre-detected and stored in
      u.scope_meeting_ids before this runs — we just set has_temporal from it,
      no DB call needed.
    - Regex fallback path: scope not yet detected — call parse_meeting_scope()
      and return the raw where-clause for _post_process_understanding() to resolve.
    """
    q = query.lower().strip()
    first_word = q.split()[0] if q else ""

    u.dimensions.is_yesno = first_word in {
        "is", "are", "was", "were", "did", "has", "have",
        "can", "could", "would", "should", "will", "may", "might", "shall",
        "do", "does", "any",
    }
    u.dimensions.is_count = bool(re.search(
        r'\bhow\s+many\b|\btotal\s+\w+\b|\bnumber\s+of\b|\bcount\b',
        q,
    ))
    u.dimensions.is_ranking = bool(re.search(
        r'\bwhich\b.*\b(most|first|last|latest|earliest|oldest|newest)\b'
        r'|\btop\s+\d+\b|\brank\b',
        q,
    ))
    u.dimensions.is_list_request = bool(re.search(
        r'\bwhat\s+(?:are|were|is|was|\'s)?\s*(?:the|a|some|all)?\s*'
        r'(topics?|items?|things?|points?|issues?|matters?|agenda)\b'
        r'|\blist\s+(?:the|all|of)\b',
        q,
    ))

    # Scope: if already pre-detected (normal path) use it directly — no DB call
    if u.scope_meeting_ids:
        u.dimensions.has_temporal = True
        return None  # scope already stored, no scope_where needed

    # Regex fallback path: detect scope now
    from app.services.answer.scope import parse_meeting_scope
    scope_where = parse_meeting_scope(query, project_id)
    u.dimensions.has_temporal = scope_where is not None
    return scope_where


# ── Layer 3a — 16-rule priority routing matrix ────────────────────────────────

@dataclass(frozen=True)
class RoutingRule:
    condition: Callable[["QueryUnderstanding", str], bool]
    mode:      str
    label:     str


ROUTING_RULES: list[RoutingRule] = [
    RoutingRule(
        condition=lambda u, q: bool(re.search(
            r'\btimings?\b|when.*meeting.*start'
            r'|\bhow\s+many\s+(meetings?|persons?|people|speakers?|participants?|attendees?)\b',
            q.lower(),
        )),
        mode="metadata",
        label="structural_metadata",
    ),
    RoutingRule(
        condition=lambda u, q: u.dimensions.is_contribution or bool(re.search(
            r'\bspoke\s+(?:the\s+)?most\b|\bspoken\s+(?:the\s+)?most\b'
            r'|\bmost\s+active\b|\bcontribut',
            q.lower(),
        )),
        mode="contribution",
        label="contribution_volume",
    ),
    RoutingRule(
        condition=lambda u, q: u.intent_type == QueryIntent.ATTRIBUTION,
        mode="timeline",
        label="attribution_origin",
    ),
    RoutingRule(
        condition=lambda u, q: u.dimensions.is_count and u.dimensions.has_temporal,
        mode="analytical",
        label="scoped_count",
    ),
    RoutingRule(
        condition=lambda u, q: (
            u.dimensions.is_count
            and bool(u.signal_filter)
            and not u.dimensions.has_topic
        ),
        mode="analytical",
        label="signal_count",
    ),
    RoutingRule(
        condition=lambda u, q: u.dimensions.is_count and bool(u.named_speaker),
        mode="analytical",
        label="named_speaker_count",
    ),
    RoutingRule(
        condition=lambda u, q: u.dimensions.is_count and u.dimensions.has_topic,
        mode="topic_summary",
        label="semantic_count",
    ),
    RoutingRule(
        condition=lambda u, q: u.dimensions.is_count,
        mode="analytical",
        label="any_count_fallback",
    ),
    RoutingRule(
        condition=lambda u, q: bool(u.named_speaker) and not u.dimensions.is_count,
        mode="compound",
        label="compound_any_speaker",
    ),
    # Ranking queries need 25 diverse chunks from hybrid search — NOT 1-2 pre-written summary chunks.
    # "Which topic is most important in previous meeting?" → hybrid (temporal scope applied downstream)
    # "Which came up first — X or Y?" → handled earlier by attribution_origin (Rule 3)
    # Guards: no speaker (compound handles those), no count (analytical handles those).
    RoutingRule(
        condition=lambda u, q: (
            u.dimensions.is_ranking
            and not bool(u.named_speaker)
            and not u.dimensions.is_count
        ),
        mode="hybrid",
        label="scoped_ranking",
    ),
    RoutingRule(
        # Topic deep-dive: "Summarize the AI architecture discussion"
        # NOT for list-of-topics requests ("What topics were discussed?") — those need summary mode.
        # NOT for ranking requests ("Which topic is most important?") — those need hybrid mode.
        # is_list_request guard prevents "What are the topics?" from being treated as a topic deep-dive.
        condition=lambda u, q: (
            (u.intent_type == QueryIntent.SUMMARY
             or bool(re.search(
                 r'\b(overall|full|entire)\s+(conversation|discussion|dialogue)\s+(about|on|regarding)\b',
                 q.lower(),
             )))
            and u.dimensions.has_topic
            and not u.dimensions.is_list_request
            and not u.dimensions.is_ranking
            and not re.search(r'\b(project|all\s+meetings?|overall\s+project)\b', q.lower())
        ),
        mode="topic_summary",
        label="topic_summary",
    ),
    RoutingRule(
        condition=lambda u, q: u.needs_summary and not u.dimensions.is_ranking,
        mode="summary",
        label="meeting_summary",
    ),
    RoutingRule(
        condition=lambda u, q: (
            u.temporal_focus == "cross_meeting" or u.dimensions.is_cross_meeting
        ),
        mode="timeline",
        label="cross_meeting_timeline",
    ),
    # Safety net: "What was discussed / what happened / what topics in [meeting]?"
    # Fires when LLM misclassifies as general_query instead of summary_query.
    # Python-computed fields only — not affected by LLM mistakes.
    # Guards: no speaker (compound handles those), no count (analytical handles those).
    RoutingRule(
        condition=lambda u, q: (
            u.dimensions.has_temporal
            and not bool(u.named_speaker)
            and not u.dimensions.is_count
            and bool(re.search(
                r'\bwhat\b.{0,25}\b(discussed|covered|happened|talked\s+about|went\s+over|gone\s+over|was\s+done)\b'
                r'|\bwhat\b.{0,15}\b(agenda|topics?|points?|items?|things?|matters?)\b',
                q.lower(),
            ))
        ),
        mode="summary",
        label="meeting_content_request",
    ),
    # Safety net: "What are the topics / list the agenda?" without temporal scope
    # Catches is_list_request=True when LLM doesn't set needs_summary
    RoutingRule(
        condition=lambda u, q: (
            u.dimensions.is_list_request
            and not bool(u.named_speaker)
            and not u.dimensions.is_count
        ),
        mode="summary",
        label="list_request_summary",
    ),
    RoutingRule(
        condition=lambda u, q: True,
        mode="hybrid",
        label="hybrid_default",
    ),
]


def _apply_routing(u: QueryUnderstanding, query: str) -> tuple[str, str]:
    """Walk the priority table and return (mode, rule_label)."""
    for rule in ROUTING_RULES:
        if rule.condition(u, query):
            return rule.mode, rule.label
    return "hybrid", "hybrid_default"


# ── Layer 3b — output format derivation ──────────────────────────────────────

def _derive_output_format(u: QueryUnderstanding) -> str:
    if u.dimensions.is_count:          return "count"
    if u.dimensions.is_yesno:          return "yesno"
    if u.dimensions.is_ranking:        return "list"
    if u.dimensions.is_contribution:   return "table"
    if u.dimensions.is_list_request:   return "list"
    if u.dimensions.needs_traces:      return "prose_with_traces"
    return "prose"


# ── Public post-processing entry point ───────────────────────────────────────

def _post_process_understanding(
    u: QueryUnderstanding, query: str, project_id: str
) -> QueryUnderstanding:
    """
    Runs after LLM parse — three steps in order:

    1. Fill syntactic dims (Python regex) + get scope_where back in one call.
    2. Resolve scope_where → concrete meeting IDs stored in u.scope_meeting_ids.
       This is the single point where scope is detected. Pipeline and all retrieval
       functions read from u.scope_meeting_ids — they never call parse_meeting_scope().
    3. Apply routing matrix + derive output format.
    """
    scope_where = _fill_syntactic_dimensions(u, query, project_id)

    # Resolve meeting IDs — done ONCE here, propagated everywhere downstream
    if scope_where:
        from app.services.answer.scope import get_scoped_meeting_ids
        ids = list(get_scoped_meeting_ids(scope_where, project_id))
        if ids:
            u.scope_meeting_ids = ids
            u.scope_type = "meeting"

    mode, label = _apply_routing(u, query)
    u.retrieval_mode = mode
    u.output_format  = _derive_output_format(u)
    logger.info(
        "  routing    : mode=%s | rule=%s | output_format=%s | scope=%s (%d meeting(s))",
        mode, label, u.output_format, u.scope_type, len(u.scope_meeting_ids),
    )
    return u


def understand_query(query: str, project_id: str) -> QueryUnderstanding:
    """
    Structured query understanding — scope detected FIRST, then LLM called.

    Flow:
      1. Python detects scope (meeting-level vs project-level) — no LLM needed.
      2. Choose the right understanding prompt based on scope.
         Meeting-level: 6 intents, no temporal_focus, no is_cross_meeting.
         Project-level: all 8 intents, full field set.
      3. Call LLM with scope-aware prompt — better classification, fewer mistakes.
      4. Build QueryUnderstanding with pre-resolved scope already stored.
      5. _post_process_understanding() fills syntactic dims + routing (scope reused).
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    cleaned = query.strip()

    # ── Step 1: Detect scope BEFORE LLM call ────────────────────────────────
    from app.services.answer.scope import parse_meeting_scope, get_scoped_meeting_ids

    scope_meeting_ids: list[str] = []
    scope_type = "project"
    try:
        scope_where = parse_meeting_scope(cleaned, project_id)
        if scope_where:
            ids = list(get_scoped_meeting_ids(scope_where, project_id))
            if ids:
                scope_meeting_ids = ids
                scope_type = "meeting"
    except Exception:
        pass  # scope detection failure is non-fatal — fall through to project-level

    logger.info(
        "  scope      : %s (%d meeting(s)) — detected before LLM call",
        scope_type, len(scope_meeting_ids),
    )

    # ── Step 2: Choose prompt based on scope ────────────────────────────────
    try:
        from app.services.storage.project_store import get_speaker_names
        speaker_list = ", ".join(get_speaker_names(project_id)) or "none"
    except Exception:
        speaker_list = "none"

    if scope_type == "meeting":
        prompt_template = UNDERSTANDING_PROMPT_MEETING_LEVEL
    else:
        prompt_template = UNDERSTANDING_PROMPT_PROJECT_LEVEL

    prompt = prompt_template.format(speaker_list=speaker_list)

    # ── Step 3: Call LLM ────────────────────────────────────────────────────
    try:
        from app.clients.gemini_client import call_gemini_raw

        raw = call_gemini_raw(f"{prompt}\n\nQuery: {cleaned}")
        if raw.startswith("```"):
            raw = re.sub(r"^```[a-z]*\n?", "", raw).rstrip("`").strip()

        logger.info("In understand_query raw content: %s", raw)
        data = json.loads(raw)

        # Validate intent — fall back to GENERAL if unknown
        raw_intent = data.get("intent_type", "general_query")
        try:
            intent = QueryIntent(raw_intent)
        except ValueError:
            intent = QueryIntent.GENERAL

        # Meeting-level prompt doesn't return temporal_focus / is_cross_meeting
        # — those fields are meaningless for single-meeting scope.
        raw_dims = data.get("dimensions", {})
        dims = QueryDimensions(
            has_topic        = bool(raw_dims.get("has_topic", False)),
            is_cross_meeting = bool(raw_dims.get("is_cross_meeting", False)),  # always False for meeting-level
            needs_traces     = bool(raw_dims.get("needs_traces", False)),
            is_contribution  = bool(raw_dims.get("is_contribution", False)),
        )

        # ── Step 4: Build understanding with pre-resolved scope ──────────────
        understanding = QueryUnderstanding(
            topic             = data.get("topic", cleaned[:80]),
            intent_type       = intent,
            named_speaker     = data.get("named_speaker") or None,
            needs_summary     = bool(data.get("needs_summary", False)),
            temporal_focus    = data.get("temporal_focus") or None,
            signal_filter     = data.get("signal_filter") or None,
            dimensions        = dims,
            scope_meeting_ids = scope_meeting_ids,
            scope_type        = scope_type,
        )

        logger.info(
            "  understand : topic=\"%s\" | intent=%s | speaker=%s | summary=%s"
            " | temporal=%s | signal=%s | prompt=%s",
            understanding.topic,
            understanding.intent_type.value,
            understanding.named_speaker or "none",
            understanding.needs_summary,
            understanding.temporal_focus or "none",
            understanding.signal_filter or "none",
            scope_type,  # which prompt was used
        )

        # ── Step 5: fill syntactic dims + routing (scope already in understanding)
        return _post_process_understanding(understanding, cleaned, project_id)

    except Exception as e:
        logger.warning("LLM understanding failed — falling back to regex: %s", e)
        fallback = _build_understanding_from_regex(cleaned)
        # Carry pre-detected scope into the regex fallback as well
        fallback.scope_meeting_ids = scope_meeting_ids
        fallback.scope_type = scope_type
        logger.info(
            "  understand : topic=\"%s\" | intent=%s | speaker=none | source=regex_fallback",
            fallback.topic, fallback.intent_type.value,
        )
        return _post_process_understanding(fallback, cleaned, project_id)
