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
    r"\b("
    r"client|"
    r"customer|"
    r"founder|"
    r"engineer|"
    r"project manager|"
    r"speaker|"
    r"who said"
    r")\b",
    re.IGNORECASE,
)

_TIMELINE_RE = re.compile(
    r"\b("
    r"timeline|"
    r"deadline|"
    r"due date|"
    r"schedule|"
    r"roadmap|"
    r"last week|"
    r"last month|"
    r"this week|"
    r"what changed|"
    r"progress over time"
    r")\b",
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

    if _DECISION_RE.search(cleaned):
        intent = QueryIntent.DECISION

    elif _COMMITMENT_RE.search(cleaned):
        intent = QueryIntent.COMMITMENT

    elif _QUESTION_RE.search(cleaned):
        intent = QueryIntent.QUESTION

    elif _SUMMARY_RE.search(cleaned):
        intent = QueryIntent.SUMMARY

    elif _SPEAKER_RE.search(cleaned):
        intent = QueryIntent.SPEAKER

    elif _TIMELINE_RE.search(cleaned):
        intent = QueryIntent.TIMELINE

    else:
        intent = QueryIntent.GENERAL

    logger.info(
        "Query intent classified | query='%s' | intent=%s",
        cleaned,
        intent.value,
    )

    return intent