import json
import logging
import re
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ValidationError

from app.config import Config
from app.services.prompts import CLASSIFIER_SYSTEM_PROMPT, UNDERSTANDING_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)

_CLASSIFIER_MODEL = "gemini-2.5-flash-lite"


class QueryIntent(str, Enum):
    GENERAL    = "general_query"
    DECISION   = "decision_query"
    COMMITMENT = "commitment_query"
    QUESTION   = "question_query"
    SUMMARY    = "summary_query"
    SPEAKER    = "speaker_query"
    TIMELINE   = "timeline_query"


class ClassificationResult(BaseModel):
    intent:     QueryIntent
    confidence: str   # "high" | "medium" | "low"
    reason:     str   # one-line explanation — shown in pipeline trace


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


def _regex_fallback(query: str) -> QueryIntent:
    """Regex classifier — only runs when the LLM call fails."""
    if _DECISION_RE.search(query):   return QueryIntent.DECISION
    if _COMMITMENT_RE.search(query): return QueryIntent.COMMITMENT
    if _SUMMARY_RE.search(query):    return QueryIntent.SUMMARY
    if _SPEAKER_RE.search(query):    return QueryIntent.SPEAKER
    if _QUESTION_RE.search(query):   return QueryIntent.QUESTION
    if _TIMELINE_RE.search(query):   return QueryIntent.TIMELINE
    return QueryIntent.GENERAL


# ── LLM classifier ────────────────────────────────────────────────────────────

def _call_llm_classifier(query: str) -> ClassificationResult | None:
    """
    Call Gemini Flash Lite to classify the query intent.
    Returns None on any failure — caller falls back to regex.
    """
    try:
        from google import genai

        if not Config.GEMINI_API_KEY:
            return None

        client = genai.Client(api_key=Config.GEMINI_API_KEY)
        response = client.models.generate_content(
            model=_CLASSIFIER_MODEL,
            contents=f"{CLASSIFIER_SYSTEM_PROMPT}\n\nQuestion: {query}",
        )
        raw = response.text.strip()

        # Strip markdown fences if model wraps output anyway
        if raw.startswith("```"):
            raw = re.sub(r"^```[a-z]*\n?", "", raw).rstrip("`").strip()

        result = ClassificationResult.model_validate_json(raw)
        return result

    except (ValidationError, json.JSONDecodeError) as e:
        logger.warning("LLM classifier returned invalid response — falling back to regex: %s", e)
        return None
    except Exception as e:
        logger.warning("LLM classifier call failed — falling back to regex: %s", e)
        return None


# ── Public interface ──────────────────────────────────────────────────────────

def classify_query_intent(query: str) -> QueryIntent:
    """
    Classify user query intent for retrieval routing.

    Primary  : Gemini Flash Lite LLM — understands paraphrasing and context
    Fallback : regex patterns — runs silently if LLM fails or is unavailable
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    cleaned = query.strip()

    result = _call_llm_classifier(cleaned)

    if result:
        logger.info(
            "  classifier : %-20s  confidence=%-6s  reason=%s",
            result.intent.value,
            result.confidence,
            result.reason,
        )
        return result.intent

    # Fallback path
    intent = _regex_fallback(cleaned)
    logger.info("  classifier : %-20s  source=regex_fallback", intent.value)
    return intent


# ── Flexible query understanding (Step 1 — production pipeline) ───────────────

class QueryUnderstanding(BaseModel):
    topic:          str                  # main subject, 1-10 words
    intent_type:    QueryIntent          # for prompt template selection
    named_speaker:  Optional[str] = None # canonicalized speaker name if any
    needs_summary:  bool = False         # True → fetch summary chunks, skip vector search
    temporal_focus: Optional[str] = None # "cross_meeting" → per-meeting timeline retrieval


def _build_understanding_from_regex(query: str) -> QueryUnderstanding:
    intent = _regex_fallback(query)
    return QueryUnderstanding(
        topic=query[:80],
        intent_type=intent,
        needs_summary=(intent == QueryIntent.SUMMARY),
        temporal_focus="cross_meeting" if intent == QueryIntent.TIMELINE else None,
    )


def understand_query(query: str, project_id: str) -> QueryUnderstanding:
    """
    Structured query understanding — replaces fixed 7-intent enum routing.

    Returns QueryUnderstanding whose fields drive retrieval routing directly:
      needs_summary=True  → summary chunk fetch (no vector search)
      temporal_focus='cross_meeting' → per-meeting timeline retrieval
      named_speaker       → speaker_name hard filter on hybrid_retrieve
      intent_type         → selects the LLM prompt template

    Primary: LLM extraction with speaker canonicalization.
    Fallback: regex classifier (no speaker detection).
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")
    
    cleaned = query.strip()

    try:
        from app.services.storage.project_store import get_speaker_names
        speaker_list = ", ".join(get_speaker_names(project_id)) or "none"
    except Exception:
        speaker_list = "none"

    prompt = UNDERSTANDING_PROMPT_TEMPLATE.format(speaker_list=speaker_list)

    try:
        from google import genai

        if not Config.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY not set")

        client = genai.Client(api_key=Config.GEMINI_API_KEY)
        response = client.models.generate_content(
            model=_CLASSIFIER_MODEL,
            contents=f"{prompt}\n\nQuery: {cleaned}",
        )
        raw = response.text.strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```[a-z]*\n?", "", raw).rstrip("`").strip()

        data = json.loads(raw)

        # Validate intent_type — fall back to GENERAL if unknown value
        raw_intent = data.get("intent_type", "general_query")
        try:
            intent = QueryIntent(raw_intent)
        except ValueError:
            intent = QueryIntent.GENERAL

        understanding = QueryUnderstanding(
            topic=data.get("topic", cleaned[:80]),
            intent_type=intent,
            named_speaker=data.get("named_speaker") or None,
            needs_summary=bool(data.get("needs_summary", False)),
            temporal_focus=data.get("temporal_focus") or None,
        )

        logger.info(
            "  understand : topic=\"%s\" | intent=%s | speaker=%s | summary=%s | temporal=%s",
            understanding.topic,
            understanding.intent_type.value,
            understanding.named_speaker or "none",
            understanding.needs_summary,
            understanding.temporal_focus or "none",
        )
        return understanding

    except Exception as e:
        logger.warning("LLM understanding failed — falling back to regex: %s", e)
        fallback = _build_understanding_from_regex(cleaned)
        logger.info(
            "  understand : topic=\"%s\" | intent=%s | speaker=none | source=regex_fallback",
            fallback.topic,
            fallback.intent_type.value,
        )
        return fallback
