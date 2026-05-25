import json
import logging
import re
from enum import Enum
from typing import Optional

from pydantic import BaseModel, field_validator

from app.services.prompts import (
    UNDERSTANDING_PROMPT_MEETING_LEVEL,
    UNDERSTANDING_PROMPT_PROJECT_LEVEL,
)

logger = logging.getLogger(__name__)


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  SECTION 1 — Query intent enum                                              ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class QueryIntent(str, Enum):
    GENERAL       = "general_query"
    DECISION      = "decision_query"
    COMMITMENT    = "commitment_query"
    QUESTION      = "question_query"
    SUMMARY       = "summary_query"
    SPEAKER       = "speaker_query"
    TIMELINE      = "timeline_query"
    METADATA      = "metadata_query"
    ANALYTICAL    = "analytical_query"
    TOPIC_SUMMARY = "topic_summary_query"
    ATTRIBUTION   = "attribution_query"
    CONTRIBUTION  = "contribution_query"


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  SECTION 2 — Regex patterns                                                 ║
# ║                                                                              ║
# ║  Rule: regex only for things Python can detect structurally.                ║
# ║  Semantic meaning (topic, speaker name, signal type) → LLM handles.        ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# ── Metadata short-circuit — structural queries needing zero vector search ────
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
    r"|\btimings? of (?:the )?meetings?\b"
    r"|\bwhat (?:are|were) (?:the )?(?:meeting )?timings?\b"
    r"|\bwhen did (?:the )?meetings? (?:start|take place|happen|occur)\b"
    r"|\bwhat time (?:did|were|was|do) (?:the )?meetings?\b"
    r"|\bhow long (?:was|were|did) (?:the )?meetings?\b"
    r"|\bduration of (?:the )?meetings?\b"
    r"|\bhow many (?:people|persons?|participants?|attendees?)\b"
    r"|\bhow many speakers?\b"
    r"|\bwho (?:was|were|attended|participated) in (?:the )?(?:previous|last|this|that|first) meeting\b"
    r"|\bwho (?:attended|participated in|joined|was present in) (?:the )?\w+ meeting\b",
    re.IGNORECASE,
)

# ── Contribution — speaker volume ranking ─────────────────────────────────────
_CONTRIBUTION_RE = re.compile(
    r"\bspoke\s+(?:the\s+)?most\b|\bspoken\s+(?:the\s+)?most\b"
    r"|\bmost\s+active\b|\bcontribut",
    re.IGNORECASE,
)

# ── Meeting content request safety net ───────────────────────────────────────
# Fires when LLM misclassifies "what happened in X meeting" as general
_CONTENT_RE = re.compile(
    r"\bwhat\b.{0,25}\b(discussed|covered|happened|talked\s+about|went\s+over|gone\s+over|was\s+done)\b"
    r"|\bwhat\b.{0,15}\b(agenda|topics?|points?|items?|things?|matters?)\b",
    re.IGNORECASE,
)

# ── Regex fallback — only when LLM call fails entirely ───────────────────────
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

# ── Stopwords for has_topic Python verification ───────────────────────────────
# Rule: a word should be here if it describes HOW to ask, not WHAT is being asked about.
# Temporal/ordinal words ("first", "last") are position references, not topics.
# Generic content words ("topics", "agenda") name the question type, not the subject.
_TOPIC_STOPWORDS = {
    # Question / auxiliary words
    "what", "was", "were", "is", "the", "a", "an", "in", "at", "of", "to",
    "did", "do", "does", "how", "why", "when", "who", "which", "that", "this",
    "be", "been", "has", "have", "had", "by", "me", "us", "we", "they", "our",
    "any", "all", "from", "with", "for", "on", "tell", "related", "about",
    # Action verbs — describe what was done, not what was talked about
    "discuss", "discussed", "discussion",
    "happen", "happened", "happening",
    "cover", "covered", "covering",
    "mention", "mentioned",
    "talk", "talked", "talking",
    "raise", "raised",
    "said", "say",
    "done", "went",
    # Meeting / scope words
    "meeting", "meetings",
    # Summary intent words
    "summary", "summarize", "overview", "recap",
    # Temporal / positional words — these are scope references, never topics
    "previous", "last", "recent", "latest", "next", "upcoming",
    "first", "second", "third", "fourth", "fifth",
    "earliest", "oldest", "newest",
    # Generic content-request words — name the question type, not the subject
    # "What topics were discussed?" → topic="topics" should NOT trigger has_topic
    "topics", "topic", "points", "point", "items", "item", "agenda",
    "things", "thing", "matters", "matter",
}


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  SECTION 3 — Data models                                                    ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class QueryDimensions(BaseModel):
    # ── LLM fills these (semantic — Python cannot reliably detect) ────────────
    has_topic:        bool = False   # named concept: "AI architecture", "budget"
    is_cross_meeting: bool = False   # needs synthesis across multiple meetings
    needs_traces:     bool = False   # user wants citations / attribution
    is_contribution:  bool = False   # "who spoke most" — speaker volume

    # ── Python fills these (structural regex — deterministic) ─────────────────
    is_count:         bool = False   # "how many", "total X", "number of"
    is_yesno:         bool = False   # first word is auxiliary verb
    is_ranking:       bool = False   # "which came first/last/most"
    is_list_request:  bool = False   # "what topics/items were discussed?"
    has_temporal:     bool = False   # scope detection found a meeting reference
    is_attribution:   bool = False   # "which came first", "who first raised/mentioned X"


class QueryUnderstanding(BaseModel):
    topic:             str = ""              # main subject, 1-10 words (LLM); empty when no specific topic

    @field_validator("topic", mode="before")
    @classmethod
    def _coerce_topic(cls, v: object) -> str:
        """Accept null/None from LLM (broad queries have no specific topic)."""
        return v if isinstance(v, str) else ""
    intent_type:       QueryIntent           # drives prompt template selection, attribution routing, and speaker fallback detection
    named_speaker:     Optional[str] = None  # canonicalized name (LLM)
    needs_summary:     bool = False          # Python infers this — not LLM
    temporal_focus:    Optional[str] = None  # "cross_meeting" (LLM, project-level only)
    signal_filter:     Optional[str] = None  # commitment/decision/question (LLM)
    # ── Routing outputs — set by _post_process_understanding() ────────────────
    retrieval_mode:    str = "hybrid"
    output_format:     str = "prose"
    dimensions:        QueryDimensions = QueryDimensions()
    # ── Scope — resolved ONCE in understand_query(), propagated everywhere ────
    scope_meeting_ids: list[str] = []
    scope_type:        str = "project"       # "meeting" | "project"


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  SECTION 4 — Public helpers                                                 ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def is_metadata_query(query: str) -> bool:
    """
    Fast regex pre-check — runs before LLM classifier.
    Only for pure structural queries needing zero semantic search.
    Narrow intentionally: misses go to the full pipeline, not vice versa.
    """
    return bool(_METADATA_RE.search(query.strip()))


def classify_query_intent(query: str, project_id: str = "") -> QueryIntent:
    """Backward-compat wrapper. Prefer understand_query() directly."""
    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")
    return understand_query(query.strip(), project_id).intent_type


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  SECTION 5 — Python dimension filling (Layer 2)                             ║
# ║                                                                              ║
# ║  These are STRUCTURAL detections — regex is more reliable than LLM here.   ║
# ║  LLM fills semantic fields (topic, speaker, signal); Python fills shape.    ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

_PUNCT_STRIP_RE = re.compile(r"[^\w\s]")   # strips punctuation before stopword check


def _python_verify_has_topic(u: QueryUnderstanding) -> bool:
    """
    LLM sometimes misses has_topic=True even when topic text is clearly present.
    Strategy: if LLM said True  -> trust it.
               if LLM said False -> check topic field for non-stopword content.

    Rules applied before upgrading:
      1. Strip punctuation ("meeting?" -> "meeting") — avoids punctuated stopwords
         slipping through.
      2. Skip words that match the already-detected named_speaker — speaker names
         in the topic field don't make a query about a topic (e.g. "bhavneet
         meeting" should not get has_topic=True; the speaker route handles it).

    Example:
        topic="AI architecture"  -> words={"AI","architecture"} -> True
        topic="meeting summary"  -> words={"meeting","summary"} -> both stopwords -> False
        topic="first meeting"    -> words={}                    -> False  (both stopwords)
        topic="bhavneet meeting" -> words={}                    -> False  (speaker + stopword)
    """
    if u.dimensions.has_topic:
        return True

    # Strip punctuation, lowercase, split; drop pure numbers (e.g. "2" in "last 2 meetings")
    cleaned = _PUNCT_STRIP_RE.sub("", u.topic.lower())
    raw_words = set(cleaned.split())

    # Remove stopwords and pure numeric tokens
    candidate_words = {w for w in raw_words - _TOPIC_STOPWORDS if not w.isdigit()}

    # Remove the named_speaker's tokens — speaker names are not topics
    if u.named_speaker and candidate_words:
        speaker_tokens = set(_PUNCT_STRIP_RE.sub("", u.named_speaker.lower()).split())
        candidate_words -= speaker_tokens

    if candidate_words:
        logger.info(
            "  [dims]  has_topic UPGRADED True by Python "
            "(LLM=False, meaningful words found: %s)", candidate_words,
        )
        return True
    return False


def _python_infer_needs_summary(u: QueryUnderstanding, query: str) -> bool:
    """
    Python decides needs_summary — more reliable than LLM for this field.

    needs_summary=True means: fetch pre-written summary chunks, skip vector search.
    This is only correct when the user wants a GENERAL meeting overview with no
    specific topic or speaker in mind.

    Rules:
      - has_topic    -> False  (topic_summary mode will handle it)
      - named_speaker -> False  (compound mode will handle it)
      - Query must contain a summary-intent word
    """
    if u.dimensions.has_topic:
        return False
    if u.named_speaker:
        return False

    return bool(re.search(
        r"\b(summary|summarize|overview|recap|what happened|"
        r"what was discussed|what was covered|what did we talk|"
        r"bring me up to speed|catch me up)\b",
        query.lower(),
    ))


def _fill_syntactic_dimensions(
    u: QueryUnderstanding, query: str, project_id: str
) -> "dict | None":
    """
    Fill all Python-computable fields on u.dimensions.
    Returns scope_where dict only on the regex-fallback path (when scope_meeting_ids
    is not yet populated). Normal path: scope already in u.scope_meeting_ids.
    """
    q = query.lower().strip()
    first_word = q.split()[0] if q else ""

    # ── Attribution shape dim ─────────────────────────────────────────────────
    _ATTRIBUTION_RE = re.compile(
        r"\bwhich\b.{0,40}\b(came\s+first|mentioned\s+first|raised\s+first|appeared\s+first)\b"
        r"|\bwho\s+first\s+(raised|mentioned|introduced|brought\s+up)\b"
        r"|\bwhen\s+did.{0,30}\bfirst\b"
        r"|\b(first|initial)\s+(mention|occurrence|time|instance)\b",
        re.IGNORECASE,
    )
    u.dimensions.is_attribution = bool(_ATTRIBUTION_RE.search(query))

    # ── Structural shape dims ─────────────────────────────────────────────────
    u.dimensions.is_yesno = first_word in {
        "is", "are", "was", "were", "did", "has", "have",
        "can", "could", "would", "should", "will", "may", "might", "shall",
        "do", "does", "any",
    }
    u.dimensions.is_count = bool(re.search(
        r"\bhow\s+many\b|\btotal\s+\w+\b|\bnumber\s+of\b|\bcount\b",
        q,
    ))
    u.dimensions.is_ranking = bool(re.search(
        r"\bwhich\b.*\b(most|first|last|latest|earliest|oldest|newest)\b"
        r"|\btop\s+\d+\b|\brank\b",
        q,
    ))
    u.dimensions.is_list_request = bool(re.search(
        r"\bwhat\s+(?:are|were|is|was|\'s)?\s*(?:the|a|some|all)?\s*"
        r"(topics?|items?|things?|points?|issues?|matters?|agenda)\b"
        r"|\blist\s+(?:the|all|of)\b",
        q,
    ))

    # ── Semantic dim upgrades (Python verifies LLM output) ────────────────────
    u.dimensions.has_topic = _python_verify_has_topic(u)
    u.needs_summary        = _python_infer_needs_summary(u, query)

    # ── Auto needs_traces for scoped topic discussion queries ─────────────────
    if not u.dimensions.needs_traces and u.dimensions.has_temporal and u.dimensions.has_topic:
        u.dimensions.needs_traces = bool(re.search(
            r"\bwhat\b.{0,40}\b(discussion|discussions)\b"
            r"|\bwhat\b.{0,20}\b(?:was|were|have|had|did)\b.{0,25}"
            r"\b(?:discuss(?:ed)?|said|raised|mentioned|talked|covered)\b"
            r"|\bwhat\b.{0,20}\b(?:happened?|came\s+up|went\s+on)\b",
            q,
        ))
        if u.dimensions.needs_traces:
            logger.info(
                "  [dims]  needs_traces AUTO-SET True "
                "(discussion pattern + has_topic + has_temporal)",
            )

    # ── Scope / has_temporal ──────────────────────────────────────────────────
    if u.scope_meeting_ids:
        # Normal path — scope already resolved in understand_query()
        u.dimensions.has_temporal = True
        scope_where = None
    else:
        # Regex-fallback path — detect scope now
        from app.services.answer.scope import parse_meeting_scope
        scope_where = parse_meeting_scope(query, project_id)
        u.dimensions.has_temporal = scope_where is not None

    logger.info(
        "  [dims]  is_count=%-5s | is_yesno=%-5s | is_ranking=%-5s"
        " | is_list=%-5s | has_temporal=%-5s | has_topic=%-5s | needs_traces=%-5s",
        u.dimensions.is_count, u.dimensions.is_yesno, u.dimensions.is_ranking,
        u.dimensions.is_list_request, u.dimensions.has_temporal,
        u.dimensions.has_topic, u.dimensions.needs_traces,
    )
    return scope_where


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  SECTION 6 — Routing (Layer 3)                                              ║
# ║                                                                              ║
# ║  Three sub-functions, called in priority order via `or` short-circuit.      ║
# ║                                                                              ║
# ║  _structural_route  — no vector search needed (metadata, contribution)      ║
# ║  _shape_route       — answer shape dominates (count, ranking)               ║
# ║  _content_route     — what content to fetch (speaker, topic, summary, etc.) ║
# ║                                                                              ║
# ║  IMPORTANT: intent_type is NOT used in routing. Routing depends only on     ║
# ║  Python-computed dimensions + LLM semantic fields (topic, speaker, signal). ║
# ║  This makes routing deterministic and LLM-classification-error resistant.   ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def _structural_route(u: QueryUnderstanding, q: str) -> "tuple[str,str] | None":
    """
    Layer 1 — Structural short-circuits.
    These queries need zero vector search — pure metadata aggregation.
    Must be checked first so they never fall into semantic retrieval.
    """
    # Metadata: "how many meetings", "list speakers", "meeting timings"
    if _METADATA_RE.search(q):
        return "metadata", "structural_metadata"

    # Contribution: "who spoke most", "most active speaker"
    # Both LLM dim and regex checked — belt-and-suspenders
    if u.dimensions.is_contribution or _CONTRIBUTION_RE.search(q):
        return "contribution", "contribution_volume"

    return None


def _shape_route(u: QueryUnderstanding, q: str) -> "tuple[str,str] | None":
    """
    Layer 2 — Answer shape routing.
    The SHAPE of the answer (a number, a ranked list) overrides content decisions.
    Count queries always go here regardless of topic/speaker/scope.

    Count priority inside (most-specific first):
      scoped_count        -> has_temporal + is_count  (meeting-level count)
      signal_count        -> signal_filter + is_count  (count a specific signal type)
      named_speaker_count -> speaker + is_count
      semantic_count      -> topic + is_count  (needs text search, not just flags)
      any_count_fallback  -> catch-all for remaining counts

    Why attribution here as timeline? It's a "which came first" shape question.
    """
    # Attribution — "which came first?", "who first raised X?" — deterministic regex, no LLM needed
    if u.dimensions.is_attribution:
        return "timeline", "attribution_origin"

    if u.dimensions.is_count:
        # Most-specific scoped count first
        if u.dimensions.has_temporal:
            return "analytical", "scoped_count"
        if u.signal_filter and not u.dimensions.has_topic:
            return "analytical", "signal_count"
        if u.named_speaker:
            return "analytical", "named_speaker_count"
        if u.dimensions.has_topic:
            # Topic count needs semantic search — topic_summary gives better results
            # than raw metadata count for "how many times was AI mentioned"
            return "topic_summary", "semantic_count"
        return "analytical", "any_count_fallback"

    # Ranking — "which topic was most discussed?" — needs diverse hybrid chunks
    # NOT summary chunks (pre-written summaries lose granular ranking signal)
    if u.dimensions.is_ranking and not u.named_speaker:
        return "hybrid", "scoped_ranking"

    return None


def _content_route(u: QueryUnderstanding, q: str) -> tuple[str, str]:
    """
    Layer 3 — Content routing. Always returns a value (never None).
    Last line is the guaranteed hybrid fallback.

    Decision tree:
      speaker present  -> compound (2-pass speaker-first retrieval)
      topic present
        + signal_filter -> hybrid  (metadata flag hard_filter must be applied)
        + temporal      -> topic_summary (scoped to specific meeting(s))
        + cross_meeting -> topic_summary (project-wide per-meeting search)
        alone           -> topic_summary (project-wide)
      needs_summary    -> summary (pre-written summary chunks)
      list_request     -> summary (topic list comes from summary chunks)
      cross_meeting    -> timeline (per-meeting retrieval + chronological merge)
      temporal + content words -> summary (safety net for LLM misclassification)
      default          -> hybrid (BM25 + dense, best general-purpose mode)
    """
    # ── Speaker queries ───────────────────────────────────────────────────────
    if u.named_speaker:
        # signal_fetch: speaker + signal + exhaustive-list intent
        # "Did Bhavneet ask any questions?" needs ALL matching chunks, not top-N.
        # Hybrid search misses valid signal hits that score low on the query text.
        # Direct DB fetch (signal_fetch_retrieve) guarantees completeness.
        if u.signal_filter and (u.dimensions.is_yesno or u.dimensions.is_list_request):
            return "signal_fetch", "speaker_signal_exhaustive"

        # compound handles speaker+topic, speaker+signal, speaker+scope
        # all those combinations are resolved inside compound_retrieve()
        return "compound", "compound_any_speaker"

    # ── Topic queries ─────────────────────────────────────────────────────────
    if u.dimensions.has_topic:
        # Signal queries (commitment/question/decision) use metadata flags like
        # contains_question, contains_commitment as ChromaDB hard_filters.
        # topic_summary mode NEVER applies these flags — it only does text search.
        # Always route to hybrid when signal_filter is set so the flag is enforced.
        if u.signal_filter:
            return "hybrid", "signal_with_topic"

        if u.dimensions.has_temporal:
            # "AI in previous meeting" — search only scoped meeting(s) for topic
            # scope_meeting_ids already populated -> topic_summary_retrieve() uses it
            return "topic_summary", "scoped_topic_summary"

        if u.dimensions.is_cross_meeting:
            # "how has AI discussion evolved across meetings?"
            return "topic_summary", "cross_meeting_topic_summary"

        # Project-wide topic deep-dive — no scope restriction
        return "topic_summary", "topic_only_summary"

    # ── Summary / list queries ────────────────────────────────────────────────
    if u.needs_summary:
        return "summary", "meeting_summary"

    if u.dimensions.is_list_request:
        # "what topics were discussed?" -> summary chunks have the best topic list
        return "summary", "list_request_summary"

    # ── Timeline / cross-meeting ──────────────────────────────────────────────
    if u.temporal_focus == "cross_meeting" or u.dimensions.is_cross_meeting:
        return "timeline", "cross_meeting_timeline"

    # ── Safety net — LLM returned general_query but query clearly wants meeting content
    # Python regex catches "what was discussed/happened/covered in [meeting]"
    if u.dimensions.has_temporal and _CONTENT_RE.search(q):
        return "summary", "meeting_content_request"

    # ── Default fallback ──────────────────────────────────────────────────────
    return "hybrid", "hybrid_default"


def _apply_routing(u: QueryUnderstanding, query: str) -> tuple[str, str]:
    """
    Entry point for routing. Calls three layers via `or` short-circuit:
      - _structural_route first (no search needed)
      - _shape_route second  (answer shape dominates)
      - _content_route last  (always returns, never None)

    `or` short-circuits: first non-None result wins, others not evaluated.
    _content_route is guaranteed to return -> this function never returns None.
    """
    return (
        _structural_route(u, query)
        or _shape_route(u, query)
        or _content_route(u, query)
    )


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  SECTION 7 — Output format derivation                                       ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def _derive_output_format(u: QueryUnderstanding) -> str:
    """
    Determines how the LLM should structure its final answer.
    Checked in priority order — first match wins.
    """
    if u.dimensions.is_count:        return "count"
    if u.dimensions.is_yesno:        return "yesno"
    if u.dimensions.is_ranking:      return "list"
    if u.dimensions.is_contribution: return "table"
    if u.dimensions.is_list_request: return "list"
    if u.dimensions.needs_traces:    return "prose_with_traces"
    return "prose"


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  SECTION 8 — Post-processing (glues everything together)                    ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def _python_detect_speaker(query: str, project_id: str) -> "str | None":
    """
    Python fallback for speaker detection — runs when LLM misses named_speaker.
    Uses the same 2-level match that's fast enough to call here (DB lookup once).

    Level 1: full name contained in query (most reliable)
    Level 2: first name (>2 chars) contained in query

    The 4-level extended matching (last-name, abbreviation) lives in
    pipeline.py detect_speaker_name() and runs at retrieval time.
    """
    try:
        from app.services.storage.project_store import get_speaker_names
        names = get_speaker_names(project_id)
    except Exception:
        return None

    q = _PUNCT_STRIP_RE.sub("", query.lower())

    # Level 1: full name
    for name in names:
        if _PUNCT_STRIP_RE.sub("", name.lower()) in q:
            return name

    # Level 2: first name (>2 chars, prevents "Al", "Li" false matches)
    for name in names:
        parts = name.split()
        if parts:
            first = _PUNCT_STRIP_RE.sub("", parts[0].lower())
            if len(first) > 2 and first in q:
                return name

    return None


def _post_process_understanding(
    u: QueryUnderstanding, query: str, project_id: str
) -> QueryUnderstanding:
    """
    Runs after LLM parse. Steps in order:

    1. Fill syntactic dims (Python regex).
       Also returns scope_where on regex-fallback path.
    2. Resolve scope_where -> concrete meeting IDs (regex-fallback path only).
       Normal path: scope already in u.scope_meeting_ids from understand_query().
    3. Python speaker fallback — if LLM missed named_speaker, detect from query.
       Must run BEFORE routing so compound mode fires correctly.
    4. Apply routing + derive output format.
    """
    scope_where = _fill_syntactic_dimensions(u, query, project_id)

    # Resolve scope only on regex-fallback path (normal path already has IDs)
    if scope_where:
        from app.services.answer.scope import get_scoped_meeting_ids
        ids = list(get_scoped_meeting_ids(scope_where, project_id))
        if ids:
            u.scope_meeting_ids = ids
            u.scope_type = "meeting"

    # Speaker fallback — catches cases where LLM returned topic/general intent
    # but the query clearly mentions a known speaker name (e.g. "What did Bhavneet say?")
    if not u.named_speaker:
        detected = _python_detect_speaker(query, project_id)
        if detected:
            u.named_speaker = detected
            logger.info(
                "  [dims]  named_speaker DETECTED by Python (LLM missed it): %s",
                detected,
            )

    mode, label = _apply_routing(u, query)
    u.retrieval_mode = mode
    u.output_format  = _derive_output_format(u)

    logger.info(
        "  routing    : mode=%-15s | rule=%-30s | output=%-18s | scope=%s (%d meeting(s))",
        mode, label, u.output_format, u.scope_type, len(u.scope_meeting_ids),
    )
    return u


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  SECTION 9 — Regex fallback (LLM failure recovery)                         ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def _regex_fallback(query: str) -> QueryIntent:
    """Regex intent classifier — only runs when LLM call fails entirely."""
    if _DECISION_RE.search(query):   return QueryIntent.DECISION
    if _COMMITMENT_RE.search(query): return QueryIntent.COMMITMENT
    if _SUMMARY_RE.search(query):    return QueryIntent.SUMMARY
    if _SPEAKER_RE.search(query):    return QueryIntent.SPEAKER
    if _QUESTION_RE.search(query):   return QueryIntent.QUESTION
    if _TIMELINE_RE.search(query):   return QueryIntent.TIMELINE
    return QueryIntent.GENERAL


def _build_understanding_from_regex(query: str) -> QueryUnderstanding:
    intent = _regex_fallback(query)
    return QueryUnderstanding(
        topic         = query[:80],
        intent_type   = intent,
        needs_summary = (intent == QueryIntent.SUMMARY),
        temporal_focus = "cross_meeting" if intent == QueryIntent.TIMELINE else None,
    )


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  SECTION 10 — Main entry point                                              ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def understand_query(query: str, project_id: str) -> QueryUnderstanding:
    """
    Full query understanding pipeline.

    Flow (scope detected BEFORE LLM to improve classification accuracy):

      Step 1 — Python detects scope (meeting vs project) via parse_meeting_scope().
               Result stored in scope_meeting_ids — no second DB call ever needed.

      Step 2 — Choose prompt based on scope.
               Meeting-level prompt: simpler, no cross-meeting fields.
               Project-level prompt: full field set including temporal_focus.

      Step 3 — LLM extracts semantic fields:
               topic, named_speaker, signal_filter, has_topic, is_cross_meeting,
               needs_traces, is_contribution.
               LLM does NOT make routing decisions — it only extracts meaning.

      Step 4 — Build QueryUnderstanding with pre-resolved scope.

      Step 5 — _post_process_understanding():
               Python fills structural dims, verifies LLM fields, applies routing.
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    cleaned = query.strip()

    # ── Step 1: Detect scope BEFORE LLM call ─────────────────────────────────
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
        pass  # non-fatal — falls through to project-level

    logger.info(
        "  [scope] pre-LLM : scope_type=%-8s | %d meeting(s) -> [%s]",
        scope_type, len(scope_meeting_ids),
        ", ".join(scope_meeting_ids) if scope_meeting_ids else "all",
    )

    # ── Step 2: Choose prompt based on scope ──────────────────────────────────
    try:
        from app.services.storage.project_store import get_speaker_names
        speaker_list = ", ".join(get_speaker_names(project_id)) or "none"
    except Exception:
        speaker_list = "none"

    from app.services.prompts import (
        UNDERSTANDING_PROMPT_MEETING_LEVEL,
        UNDERSTANDING_PROMPT_PROJECT_LEVEL,
    )
    prompt_template = (
        UNDERSTANDING_PROMPT_MEETING_LEVEL
        if scope_type == "meeting"
        else UNDERSTANDING_PROMPT_PROJECT_LEVEL
    )
    prompt = prompt_template.format(speaker_list=speaker_list)

    # ── Step 3 + 4: Call LLM, build QueryUnderstanding ───────────────────────
    try:
        from app.clients.gemini_client import call_gemini_raw

        raw = call_gemini_raw(f"{prompt}\n\nQuery: {cleaned}")
        if raw.startswith("```"):
            raw = re.sub(r"^```[a-z]*\n?", "", raw).rstrip("`").strip()

        logger.info("  [llm]   raw response: %s", raw)
        data = json.loads(raw)

        # Validate intent — fall back to GENERAL if LLM returns unknown value
        try:
            intent = QueryIntent(data.get("intent_type", "general_query"))
        except ValueError:
            intent = QueryIntent.GENERAL

        raw_dims = data.get("dimensions", {})
        dims = QueryDimensions(
            has_topic        = bool(raw_dims.get("has_topic", False)),
            is_cross_meeting = bool(raw_dims.get("is_cross_meeting", False)),
            needs_traces     = bool(raw_dims.get("needs_traces", False)),
            is_contribution  = bool(raw_dims.get("is_contribution", False)),
        )

        understanding = QueryUnderstanding(
            topic             = data.get("topic", cleaned[:80]),
            intent_type       = intent,            # stored but NOT used in routing
            named_speaker     = data.get("named_speaker") or None,
            needs_summary     = False,             # Python will infer in Step 5
            temporal_focus    = data.get("temporal_focus") or None,
            signal_filter     = data.get("signal_filter") or None,
            dimensions        = dims,
            scope_meeting_ids = scope_meeting_ids,
            scope_type        = scope_type,
        )

        logger.info(
            "  [llm]   topic=\"%s\" | intent=%s | speaker=%s"
            " | signal=%s | has_topic(llm)=%s | cross_meeting=%s",
            understanding.topic,
            understanding.intent_type.value,
            understanding.named_speaker or "none",
            understanding.signal_filter or "none",
            understanding.dimensions.has_topic,
            understanding.dimensions.is_cross_meeting,
        )

        # ── Step 5: Python fills dims + routing ───────────────────────────────
        return _post_process_understanding(understanding, cleaned, project_id)

    except Exception as e:
        logger.warning("LLM understanding failed — falling back to regex: %s", e)
        fallback = _build_understanding_from_regex(cleaned)
        # Carry pre-detected scope into fallback
        fallback.scope_meeting_ids = scope_meeting_ids
        fallback.scope_type        = scope_type
        logger.info(
            "  [regex] topic=\"%s\" | intent=%s",
            fallback.topic, fallback.intent_type.value,
        )
        return _post_process_understanding(fallback, cleaned, project_id)
