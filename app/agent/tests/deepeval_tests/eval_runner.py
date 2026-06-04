import csv
import json
import re
from dataclasses import dataclass

from google import genai
from google.genai import types as genai_types

from app.config import Config
from app.agent.service import answer_query
from app.agent.tests.deepeval_tests.goldens import Golden, PROJECT_LEVEL_GOLDENS

_PROJECT_ID  = "proj_nolocode_001"
_JUDGE_MODEL = "gemini-2.5-pro"


@dataclass
class EvalResult:
    golden_id: str
    query: str
    actual_answer: str
    cited_meetings: list[str]

    # Scores
    retrieval_score: float
    fact_recall_score: float
    hallucination_score: float
    overall_score: float

    # Debug info
    facts_found: list[str]
    facts_missing: list[str]
    hallucinations_found: list[str]


# ── Layer 1: Retrieval ────────────────────────────────────────────────────────

def _meeting_matches(expected: str, actual: str) -> bool:
    """Title-only match — strips date in parens to avoid format mismatch."""
    expected_title = expected.split("(")[0].strip().lower()
    actual_title   = actual.split("(")[0].strip().lower()
    return expected_title in actual_title or actual_title in expected_title


def eval_retrieval(
    actual_meetings: list[str],
    expected_meetings: list[str] | None,
) -> float:
    # None = golden doesn't constrain retrieval → always pass
    if expected_meetings is None:
        return 1.0
    # [] = golden explicitly expects NO meetings cited (known_gap queries)
    if not expected_meetings:
        return 1.0 if not actual_meetings else 0.0

    found = sum(
        1 for expected in expected_meetings
        if any(_meeting_matches(expected, actual) for actual in actual_meetings)
    )
    return found / len(expected_meetings)


# ── Layer 2: Fact Recall (LLM judge) ─────────────────────────────────────────

def eval_fact_recall(
    answer: str,
    must_have_facts: list[str],
) -> tuple[float, list[str], list[str]]:
    if not must_have_facts:
        return 1.0, [], []

    clean_answer = re.sub(r'\[\d+\]', '', answer).strip()

    prompt = f"""You are a strict evaluator checking if facts are present in an answer.

Answer:
{clean_answer}

Rules:
1. Mark present=true only if the CORE MEANING is clearly conveyed — exact words not needed,
   but the specific claim must be there. A vague related mention does NOT count.
2. "approach one" = "first approach" = "Approach 1" → present
3. If fact says "X not discussed" → only mark present if answer EXPLICITLY says X was NOT discussed or not found
4. If fact says "X decided" → only mark present if answer clearly states a decision was made about X

Respond ONLY as valid JSON array, no explanation, no markdown:
[{{"fact": "...", "present": true/false, "reason": "one line"}}]

Facts to check:
{json.dumps(must_have_facts)}"""

    try:
        client   = genai.Client(api_key=Config.GEMINI_API_KEY)
        response = client.models.generate_content(
            model=_JUDGE_MODEL,
            contents=prompt,
            config=genai_types.GenerateContentConfig(temperature=0.0),
        )
        raw = response.text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        results = json.loads(raw)
        found   = [r["fact"] for r in results if r["present"]]
        missing = [r["fact"] for r in results if not r["present"]]
        score   = len(found) / len(must_have_facts)
        return score, found, missing

    except Exception as e:
        print(f"  [WARN] eval_fact_recall LLM call failed: {e} — falling back to substring")
        answer_lower = answer.lower()
        found   = [f for f in must_have_facts if f.lower() in answer_lower]
        missing = [f for f in must_have_facts if f.lower() not in answer_lower]
        return len(found) / len(must_have_facts), found, missing


# ── Layer 3: Hallucination ────────────────────────────────────────────────────

def eval_hallucination(
    answer: str,
    must_not_have: list[str],
) -> tuple[float, list[str]]:
    answer_lower = answer.lower()
    violations   = [item for item in must_not_have if item.lower() in answer_lower]
    return (0.0 if violations else 1.0), violations


# ── Source extractor ──────────────────────────────────────────────────────────

def _extract_cited_meetings(sources: list[dict]) -> list[str]:
    """Pull unique 'meeting_title (date)' strings from the sources list."""
    seen, result = set(), []
    for s in sources:
        label = f"{s.get('meeting_title', '')} ({s.get('meeting_date', '')})"
        if label not in seen:
            seen.add(label)
            result.append(label)
    return result


# ── Single eval ───────────────────────────────────────────────────────────────

def run_single_eval(golden: Golden) -> EvalResult:
    response = answer_query(
        query=golden.input,
        project_id=_PROJECT_ID,
    )

    actual_answer  = response["answer"]
    cited_meetings = _extract_cited_meetings(response.get("sources", []))

    meta    = golden.additional_metadata
    weights = meta.get("eval_weights", {"retrieval": 0.3, "fact_recall": 0.5, "hallucination_free": 0.2})

    retrieval = eval_retrieval(
        actual_meetings=cited_meetings,
        expected_meetings=meta.get("expected_meetings"),  # None if key absent
    )

    fact_recall, facts_found, facts_missing = eval_fact_recall(
        answer=actual_answer,
        must_have_facts=meta.get("must_have_facts", []),
    )

    hallucination, hallucinations_found = eval_hallucination(
        answer=actual_answer,
        must_not_have=meta.get("must_not_have", []),
    )

    overall = (
        retrieval     * weights["retrieval"] +
        fact_recall   * weights["fact_recall"] +
        hallucination * weights["hallucination_free"]
    )

    return EvalResult(
        golden_id=meta["id"],
        query=golden.input,
        actual_answer=actual_answer,
        cited_meetings=cited_meetings,
        retrieval_score=retrieval,
        fact_recall_score=fact_recall,
        hallucination_score=hallucination,
        overall_score=overall,
        facts_found=facts_found,
        facts_missing=facts_missing,
        hallucinations_found=hallucinations_found,
    )


# ── Full eval run ─────────────────────────────────────────────────────────────

def run_full_eval(goldens: list[Golden]):
    results = []

    for golden in goldens:
        print(f"Running: {golden.additional_metadata['id']} — {golden.input[:60]}")
        result = run_single_eval(golden)
        results.append(result)
        print(
            f"  Score: {result.overall_score:.2f} | "
            f"retrieval={result.retrieval_score:.2f} | "
            f"fact_recall={result.fact_recall_score:.2f} | "
            f"hallucination_free={result.hallucination_score:.2f}"
        )
        if result.facts_missing:
            print(f"  Missing facts: {result.facts_missing}")
        if result.hallucinations_found:
            print(f"  Hallucinations: {result.hallucinations_found}")

    save_to_csv(results)
    print_summary(results)
    return results


def save_to_csv(results: list[EvalResult]):
    with open("eval_results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "golden_id", "query",
            "retrieval", "fact_recall",
            "hallucination", "overall",
            "facts_missing", "hallucinations_found",
        ])
        writer.writeheader()
        for r in results:
            writer.writerow({
                "golden_id":            r.golden_id,
                "query":                r.query,
                "retrieval":            f"{r.retrieval_score:.2f}",
                "fact_recall":          f"{r.fact_recall_score:.2f}",
                "hallucination":        f"{r.hallucination_score:.2f}",
                "overall":              f"{r.overall_score:.2f}",
                "facts_missing":        str(r.facts_missing),
                "hallucinations_found": str(r.hallucinations_found),
            })
    print(f"\n✓ Results saved to eval_results.csv")


def print_summary(results: list[EvalResult]):
    avg     = sum(r.overall_score for r in results) / len(results)
    passing = sum(1 for r in results if r.overall_score >= 0.75)

    print("\n" + "=" * 50)
    print(f"Total queries  : {len(results)}")
    print(f"Passing (≥0.75): {passing}/{len(results)}")
    print(f"Average score  : {avg:.2f}")
    print("=" * 50)

    sorted_results = sorted(results, key=lambda x: x.overall_score)
    print("\nWorst 3 queries:")
    for r in sorted_results[:3]:
        print(f"  {r.golden_id}: {r.overall_score:.2f} — {r.query[:60]}")


if __name__ == "__main__":
    run_full_eval(PROJECT_LEVEL_GOLDENS)