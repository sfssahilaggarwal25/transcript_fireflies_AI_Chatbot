import logging
import re
from enum import Enum

logger = logging.getLogger(__name__)


class QueryIntent(str, Enum):
    """
    Supported query intent types.
    """

    GENERAL = "general_query"
    DECISION = "decision_query"
    COMMITMENT = "commitment_query"
    QUESTION = "question_query"
    SUMMARY = "summary_query"
    SPEAKER = "speaker_query"
    TIMELINE = "timeline_query"


_DECISION_RE = re.compile(
    r"\b("
    r"decision|"
    r"decisions|"
    r"decided|"
    r"agreed|"
    r"finalized|"
    r"approved|"
    r"confirmed|"
    r"what was decided|"
    r"what did we decide|"
    r"final decision"
    r")\b",
    re.IGNORECASE,
)

_COMMITMENT_RE = re.compile(
    r"\b("
    r"commitment|"
    r"commitments|"
    r"action item|"
    r"action items|"
    r"follow up|"
    r"follow-up|"
    r"who will|"
    r"who committed|"
    r"what needs to be done|"
    r"next steps|"
    r"deliverable|"
    r"deliverables"
    r")\b",
    re.IGNORECASE,
)

_QUESTION_RE = re.compile(
    r"\b("
    r"question|"
    r"questions|"
    r"what did they ask|"
    r"what was asked|"
    r"client questions"
    r")\b",
    re.IGNORECASE,
)

_SUMMARY_RE = re.compile(
    r"\b("
    r"summary|"
    r"summarize|"
    r"overview|"
    r"recap|"
    r"progress summary|"
    r"project summary|"
    r"high level summary"
    r")\b",
    re.IGNORECASE,
)

_SPEAKER_RE = re.compile(
    r"("
    # "what did [name] say/mention/discuss/state/think" — exclude "we/they/it/the/you"
    r"what did (?!we\b|they\b|it\b|the\b|you\b).+? (?:say|mention|discuss|state|think)\b|"
    # "what has/have [name] said/mentioned/discussed"
    r"what (?:has|have) (?!we\b|they\b|it\b|the\b|you\b).+? (?:said|mentioned|discussed|stated)\b|"
    # "what was [name] saying"
    r"what was .+? saying\b|"
    r"according to|"
    r"who said"
    r")",
    re.IGNORECASE,
)

_TIMELINE_RE = re.compile(
    r"("
    r"\b(?:timeline|deadline|due date|schedule|roadmap)\b|"
    r"\b(?:last week|last month|this week|historically|over time)\b|"
    r"\bprogress over time\b|"
    # explicit change-tracking phrases
    r"\bwhat changed\b|"
    r"\bhow (?:has|did|have|were?).{0,30}changed?\b|"
    r"\bchanged? (?:since|between|across|from)\b|"
    r"\bevolved?\b|"
    # cross-meeting comparison
    r"\bbetween (?:the )?(?:two|both|meetings?|meeting \d|first|second|last)\b|"
    r"\bacross (?:both|the|all|meetings?)\b|"
    r"\bcompared? to (?:the )?(?:first|second|last|previous|earlier)\b|"
    r"\bprevious meeting\b|"
    r"\bfirst meeting\b|"
    r"\bsecond meeting\b|"
    r"\bfrom .{0,20} to .{0,20} meeting\b"
    r")",
    re.IGNORECASE,
)


def classify_query_intent(query: str) -> QueryIntent:
    """
    Classify user query intent for retrieval routing.

    Returns:
        QueryIntent enum
    """

    if not query:
        raise ValueError("Query cannot be empty.")

    cleaned = query.strip()

    if not cleaned:
        raise ValueError("Query cannot be blank.")

    matched_by = "none (fallback)"

    if _DECISION_RE.search(cleaned):
        intent = QueryIntent.DECISION
        matched_by = "_DECISION_RE"
    elif _COMMITMENT_RE.search(cleaned):
        intent = QueryIntent.COMMITMENT
        matched_by = "_COMMITMENT_RE"
    elif _SUMMARY_RE.search(cleaned):
        intent = QueryIntent.SUMMARY
        matched_by = "_SUMMARY_RE"
    # SPEAKER before QUESTION: "What did Ngumi say about the questions?" must route
    # to SPEAKER (name detected), not QUESTION (keyword match). Speech-act patterns
    # are specific enough that false positives are rare.
    elif _SPEAKER_RE.search(cleaned):
        intent = QueryIntent.SPEAKER
        matched_by = "_SPEAKER_RE"
    elif _QUESTION_RE.search(cleaned):
        intent = QueryIntent.QUESTION
        matched_by = "_QUESTION_RE"
    elif _TIMELINE_RE.search(cleaned):
        intent = QueryIntent.TIMELINE
        matched_by = "_TIMELINE_RE"
    else:
        intent = QueryIntent.GENERAL

    logger.info(
        "  classifier : %-20s  matched by %s",
        intent.value,
        matched_by,
    )

    return intent