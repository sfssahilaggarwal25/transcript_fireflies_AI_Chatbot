"""
answer_evaluator.py

LLM-based answer quality evaluator.
Uses Gemini to score each answer against the evaluation_hints in the query bank.

Called by test_runner.py immediately after each pipeline run.
"""

import json
import logging

from google import genai

from app.config import Config

logger = logging.getLogger(__name__)

_EVAL_MODEL = "gemini-2.5-flash-lite"

_EVAL_PROMPT = """\
You are a strict evaluator checking whether an AI assistant's answer meets quality criteria.

---
QUESTION ASKED:
{query}

AI ANSWER:
{answer}

---
EVALUATION CRITERIA:

MUST CONTAIN (check if each concept is semantically present in the answer):
{must_contain}

MUST NOT CONTAIN (flag if any of these appear in the answer):
{must_not_contain}

SOURCES REQUIREMENT: {sources_requirement}
SOURCES ACTUALLY PRESENT: {sources_present}

---
Return ONLY a valid JSON object with this exact structure. No markdown fences, no explanation outside the JSON:
{{
  "score": <integer 1-10>,
  "checks_passed": [<must_contain items that ARE satisfied>],
  "checks_failed": [<must_contain items NOT found in the answer>],
  "violations": [<must_not_contain phrases actually found in the answer>],
  "sources_cited": <true or false>,
  "reasoning": "<1-2 sentences explaining the score>"
}}

Scoring guide:
  9-10  All must_contain met, no violations, sources cited when required
  7-8   Most must_contain met, minor gaps, no violations
  5-6   Partially meets criteria, noticeable gaps
  3-4   Fails several criteria or has violations
  1-2   Answer is wrong, empty, or completely off-topic
"""


def evaluate_answer(
    query: str,
    answer: str,
    evaluation_hints: dict,
    sources: list[dict],
) -> dict:
    """
    Score an answer 1-10 using Gemini against the evaluation_hints from the query bank.

    Args:
        query            - the original question text
        answer           - the pipeline-generated answer
        evaluation_hints - dict from the query bank (must_contain, must_not_contain, etc.)
        sources          - list of source dicts returned by the pipeline

    Returns a dict with:
        score          → int 1-10 (0 if eval failed)
        checks_passed  → list of must_contain items found
        checks_failed  → list of must_contain items missing
        violations     → list of must_not_contain items that appeared
        sources_cited  → bool
        reasoning      → brief explanation string
        eval_error     → error message string if evaluation itself failed, else null
    """
    must_contain     = evaluation_hints.get("must_contain", [])
    must_not_contain = evaluation_hints.get("must_not_contain", [])
    should_cite      = evaluation_hints.get("should_cite_sources", False)
    has_sources      = bool(sources)

    mc_text  = "\n".join(f"  - {item}" for item in must_contain)  or "  (none specified)"
    mnc_text = "\n".join(f"  - {item}" for item in must_not_contain) or "  (none specified)"

    prompt = _EVAL_PROMPT.format(
        query=query,
        answer=answer,
        must_contain=mc_text,
        must_not_contain=mnc_text,
        sources_requirement="Required" if should_cite else "Not required",
        sources_present="Yes" if has_sources else "No",
    )

    fallback: dict = {
        "score":        0,
        "checks_passed": [],
        "checks_failed": list(must_contain),
        "violations":   [],
        "sources_cited": False,
        "reasoning":    "",
        "eval_error":   None,
    }

    try:
        client   = genai.Client(api_key=Config.GEMINI_API_KEY)
        response = client.models.generate_content(
            model=_EVAL_MODEL,
            contents=prompt,
        )
        raw = response.text.strip()

        # Strip markdown code fences Gemini sometimes adds
        if raw.startswith("```"):
            parts = raw.split("```")
            raw = parts[1] if len(parts) > 1 else raw
            if raw.lower().startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        parsed = json.loads(raw)
        return {
            "score":         int(parsed.get("score", 0)),
            "checks_passed": parsed.get("checks_passed", []),
            "checks_failed": parsed.get("checks_failed", []),
            "violations":    parsed.get("violations", []),
            "sources_cited": bool(parsed.get("sources_cited", False)),
            "reasoning":     parsed.get("reasoning", ""),
            "eval_error":    None,
        }

    except Exception as exc:
        logger.warning("Answer evaluation failed for query '%s': %s", query[:60], exc)
        fallback["eval_error"] = str(exc)
        return fallback


def compute_confidence_score(
    intent_match: bool | None,
    answer_score: int,
    has_sources: bool,
) -> float:
    """
    Composite confidence score (0.0 – 1.0):
      40% → intent classification correct
      40% → answer quality (score / 10)
      20% → sources returned by pipeline
    """
    intent_part  = 1.0 if intent_match else 0.0
    answer_part  = answer_score / 10.0
    sources_part = 1.0 if has_sources else 0.0
    return round(0.4 * intent_part + 0.4 * answer_part + 0.2 * sources_part, 2)
