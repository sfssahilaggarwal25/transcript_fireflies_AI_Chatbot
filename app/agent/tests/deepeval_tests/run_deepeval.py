"""
run_deepeval.py — Run the DeepEval evaluation suite against the production agent.

HOW IT WORKS
------------
1. Load goldens (input + expected_output) from goldens.py
2. For each golden, call answer_query() to get the actual_output
3. Build a LLMTestCase: input + actual_output + expected_output + retrieval_context
4. Run DeepEval metrics on every test case
5. Print a pass/fail report

METRICS USED
------------
  AnswerRelevancyMetric   — Is the answer relevant to the question asked?
  ContextualRecallMetric  — Does the answer contain what expected_output says it should?

HOW TO RUN
----------
# Run all goldens:
python -m app.agent.tests.deepeval_tests.run_deepeval

# Run one category:
python -m app.agent.tests.deepeval_tests.run_deepeval --category meeting

# Run by signal type (all commitment queries):
python -m app.agent.tests.deepeval_tests.run_deepeval --signal commitment

# Run by query type (all yes/no queries):
python -m app.agent.tests.deepeval_tests.run_deepeval --query-type yesno

# Run by scope (all meeting-scoped queries):
python -m app.agent.tests.deepeval_tests.run_deepeval --scope meeting

# Run by speaker (all queries mentioning a specific speaker):
python -m app.agent.tests.deepeval_tests.run_deepeval --speaker "Bhavneet Mhajan"

# Skip known gaps — clean baseline run (only currently-passing goldens):
python -m app.agent.tests.deepeval_tests.run_deepeval --skip-gaps

# Run specific goldens by ID:
python -m app.agent.tests.deepeval_tests.run_deepeval --ids A1,B2,C3

# Dry run (show what would run without calling the pipeline):
python -m app.agent.tests.deepeval_tests.run_deepeval --dry-run

# Combine filters:
python -m app.agent.tests.deepeval_tests.run_deepeval --scope meeting --signal commitment --skip-gaps
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# ── Project root on sys.path ──────────────────────────────────────────────────
# __file__ = app/agent/tests/deepeval_tests/run_deepeval.py
# .parent×4 = project root
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

from deepeval import evaluate
from deepeval.metrics import AnswerRelevancyMetric, ContextualRecallMetric
from deepeval.models import DeepEvalBaseLLM
from deepeval.test_case import LLMTestCase
from google import genai as google_genai

from app.agent.tests.deepeval_tests.goldens import ALL_QUERIES, MEETING_QUERIES, PROJECT_QUERIES, TOPIC_QUERIES


# ── Custom Gemini model wrapper for DeepEval ──────────────────────────────────
# DeepEval metrics default to OpenAI. We wrap our existing Gemini client so
# the metrics use Gemini Flash Lite for their internal LLM calls.

class _GeminiEvalModel(DeepEvalBaseLLM):
    """
    Thin wrapper that lets DeepEval metrics use Gemini instead of OpenAI.

    DeepEvalBaseLLM requires:
      generate(prompt: str) -> str
      get_model_name() -> str
    """

    _MODEL = "gemini-2.5-flash"

    def __init__(self):
        self._client = google_genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    def load_model(self):
        return self._client

    def generate(self, prompt: str, schema=None) -> str:
        response = self._client.models.generate_content(
            model=self._MODEL,
            contents=prompt,
        )
        return response.text

    async def a_generate(self, prompt: str, schema=None) -> str:
        # Fallback: run synchronously (DeepEval falls back to sync if async raises)
        return self.generate(prompt, schema)

    def get_model_name(self) -> str:
        return self._MODEL

# ── Constants ─────────────────────────────────────────────────────────────────

_PROJECT_ID = "proj_nolocode_001"
_RESULTS_DIR = Path(__file__).parent / "results"

_CATEGORY_MAP = {
    "all":     ALL_QUERIES,
    "project": PROJECT_QUERIES,
    "meeting": MEETING_QUERIES,
    "topic":   TOPIC_QUERIES,
}


# ── Metrics ───────────────────────────────────────────────────────────────────

def get_metrics(threshold: float = 0.5):
    """
    Return the DeepEval metrics used to evaluate each test case.

    AnswerRelevancyMetric
      Score: 0.0–1.0  |  Is the actual_output relevant to the input question?
      Pass threshold: configurable (default 0.5).

    ContextualRecallMetric
      Score: 0.0–1.0  |  Does actual_output cover what expected_output describes?
      Pass threshold: configurable (default 0.5).
      Uses Gemini to check how many rubric elements from expected_output are present.

    Both metrics use our _GeminiEvalModel wrapper — no OpenAI key required.
    """
    gemini = _GeminiEvalModel()
    return [
        AnswerRelevancyMetric(threshold=threshold, model=gemini),
        ContextualRecallMetric(threshold=threshold, model=gemini),
    ]


# ── Pipeline runner ───────────────────────────────────────────────────────────

def run_pipeline(query: str, project_id: str) -> tuple[str, list[str]]:
    """
    Call the production agent and return (answer, retrieval_context).

    retrieval_context is a list of chunk texts — needed for FaithfulnessMetric
    if you add it later. For AnswerRelevancy + ContextualRecall it is not used
    but still passed to LLMTestCase for completeness.
    """
    from app.agent.service import answer_query

    result  = answer_query(query, project_id)
    answer  = result.get("answer", "")

    # Build retrieval context from source previews (each source = one context chunk)
    context = [
        s.get("content_preview", "")
        for s in result.get("sources", [])
        if s.get("content_preview")
    ]

    return answer, context


# ── Test case builder ─────────────────────────────────────────────────────────

def build_test_case(
    golden_input: str,
    golden_expected: str,
    project_id: str,
) -> tuple[LLMTestCase, dict]:
    """
    Run the pipeline for one golden and build a DeepEval LLMTestCase.

    Returns
    -------
    test_case  — LLMTestCase ready for evaluate()
    meta       — timing + source count for the summary table
    """
    t_start = time.time()
    actual_output, retrieval_context = run_pipeline(golden_input, project_id)
    elapsed_ms = round((time.time() - t_start) * 1000)

    # ContextualRecallMetric requires retrieval_context to be non-None.
    # When the pipeline uses metadata retrieval (e.g. list_meetings), no source
    # chunks are returned. Fall back to [actual_output] so recall still measures
    # whether the expected facts appear in what the model stated.
    effective_context = retrieval_context if retrieval_context else [actual_output]

    test_case = LLMTestCase(
        input=golden_input,
        actual_output=actual_output,
        expected_output=golden_expected,
        retrieval_context=effective_context,
    )

    meta = {
        "elapsed_ms":   elapsed_ms,
        "num_sources":  len(retrieval_context),
        "has_answer":   bool(actual_output and "not found" not in actual_output.lower()),
    }

    return test_case, meta


# ── CLI filters ───────────────────────────────────────────────────────────────

def filter_goldens(
    goldens,
    ids:        list[str] | None,
    signal:     str | None,
    query_type: str | None,
    scope:      str | None,
    speaker:    str | None,
    skip_gaps:  bool,
):
    """
    Filter goldens by any combination of metadata fields.

    Filters applied in order:
      --ids         → keep only these specific IDs
      --signal      → keep only goldens with this signal value
      --query-type  → keep only goldens with this query_type value
      --scope       → keep only goldens with this scope value
      --speaker     → keep only goldens where speaker contains this string
      --skip-gaps   → remove goldens with known_gap=True
    """
    result = list(goldens)

    # Filter by IDs
    if ids:
        id_set = set(ids)
        result = [g for g in result if (g.additional_metadata or {}).get("id") in id_set]
        missing = id_set - {(g.additional_metadata or {}).get("id") for g in result}
        if missing:
            print(f"[WARN] No goldens found for IDs: {', '.join(sorted(missing))}")

    # Filter by signal
    if signal:
        result = [g for g in result if (g.additional_metadata or {}).get("signal") == signal]

    # Filter by query_type
    if query_type:
        result = [g for g in result if (g.additional_metadata or {}).get("query_type") == query_type]

    # Filter by scope
    if scope:
        result = [g for g in result if (g.additional_metadata or {}).get("scope") == scope]

    # Filter by speaker (partial match — "Bhavneet" matches "Bhavneet Mhajan")
    if speaker:
        speaker_lower = speaker.lower()
        result = [
            g for g in result
            if (g.additional_metadata or {}).get("speaker")
            and speaker_lower in ((g.additional_metadata or {}).get("speaker") or "").lower()
        ]

    # Skip known gaps
    if skip_gaps:
        before = len(result)
        result = [g for g in result if not (g.additional_metadata or {}).get("known_gap", False)]
        skipped = before - len(result)
        if skipped:
            print(f"[INFO] Skipped {skipped} golden(s) with known_gap=True")

    return result


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run DeepEval metrics against the production agent"
    )
    parser.add_argument(
        "--project-id",
        default=_PROJECT_ID,
        help=f"Project ID to query (default: {_PROJECT_ID})",
    )
    parser.add_argument(
        "--category",
        default="all",
        choices=["all", "project", "meeting", "topic"],
        help="Which golden category to run (default: all)",
    )
    parser.add_argument(
        "--ids",
        type=str, default=None,
        help="Comma-separated golden IDs (e.g. --ids A1,B2,C3)",
    )
    parser.add_argument(
        "--signal",
        type=str, default=None,
        choices=["commitment", "decision", "question", "open_issue", "document_share"],
        help="Run only goldens with this signal type",
    )
    parser.add_argument(
        "--query-type",
        type=str, default=None,
        choices=["yesno", "count", "list", "summary", "attribution", "comparison"],
        help="Run only goldens with this query type",
    )
    parser.add_argument(
        "--scope",
        type=str, default=None,
        choices=["project", "meeting", "multi-meeting"],
        help="Run only goldens with this scope",
    )
    parser.add_argument(
        "--speaker",
        type=str, default=None,
        help="Run only goldens whose speaker field contains this string (partial match)",
    )
    parser.add_argument(
        "--skip-gaps",
        action="store_true",
        help="Skip goldens marked known_gap=True (clean baseline run)",
    )
    parser.add_argument(
        "--threshold",
        type=float, default=0.5,
        help="Metric pass threshold 0.0–1.0 (default: 0.5)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would run without calling the pipeline",
    )
    args = parser.parse_args()

    dataset = _CATEGORY_MAP[args.category]
    goldens = filter_goldens(
        dataset.goldens,
        ids        = [i.strip() for i in args.ids.split(",")] if args.ids else None,
        signal     = args.signal,
        query_type = args.query_type,
        scope      = args.scope,
        speaker    = args.speaker,
        skip_gaps  = args.skip_gaps,
    )
    metrics   = get_metrics(threshold=args.threshold)
    project_id = args.project_id

    # Build active filter summary for display
    active_filters = []
    if args.signal:     active_filters.append(f"signal={args.signal}")
    if args.query_type: active_filters.append(f"query_type={args.query_type}")
    if args.scope:      active_filters.append(f"scope={args.scope}")
    if args.speaker:    active_filters.append(f"speaker={args.speaker}")
    if args.skip_gaps:  active_filters.append("skip_gaps=True")
    filter_str = "  |  ".join(active_filters) if active_filters else "none"

    print(f"\n{'='*62}")
    print(f"  DeepEval Test Run — Production Agent")
    print(f"  Project  : {project_id}")
    print(f"  Category : {args.category}  ({len(goldens)} goldens)")
    print(f"  Filters  : {filter_str}")
    print(f"  Threshold: {args.threshold}")
    print(f"  Metrics  : {[type(m).__name__ for m in metrics]}")
    print(f"{'='*62}\n")

    # ── Dry run ───────────────────────────────────────────────────────────────
    if args.dry_run:
        print("[DRY RUN] Goldens that would run:\n")
        for g in goldens:
            mid = (g.additional_metadata or {}).get("id", "??")
            cat = (g.additional_metadata or {}).get("category", "??")
            print(f"  [{mid}] [{cat}]  {g.input[:65]}")
            print(f"         expected → {g.expected_output[:80]}…")
        print(f"\nTotal: {len(goldens)} goldens. Remove --dry-run to execute.")
        return

    # ── Build test cases by running the pipeline ──────────────────────────────
    test_cases = []
    run_metas  = []

    for i, golden in enumerate(goldens, 1):
        gid = (golden.additional_metadata or {}).get("id", f"#{i}")
        print(f"  [{i:02d}/{len(goldens)}]  [{gid}]  Running: {golden.input[:55]}…", end="", flush=True)

        try:
            tc, meta = build_test_case(golden.input, golden.expected_output, project_id)
            test_cases.append(tc)
            run_metas.append({"id": gid, **meta, "error": None})
            print(f"  {meta['elapsed_ms']}ms  |  {meta['num_sources']} sources")
        except Exception as exc:
            print(f"  ERROR: {exc}")
            run_metas.append({"id": gid, "elapsed_ms": 0, "num_sources": 0, "has_answer": False, "error": str(exc)})

    if not test_cases:
        print("\n[ERROR] All pipeline calls failed. Check GEMINI_API_KEY.")
        sys.exit(1)

    # ── Run DeepEval metrics ──────────────────────────────────────────────────
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Running DeepEval metrics on {len(test_cases)} test cases…\n")

    evaluate(test_cases=test_cases, metrics=metrics)

    # ── Save results JSON ─────────────────────────────────────────────────────
    _RESULTS_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M")
    out_path = _RESULTS_DIR / f"{ts}_{args.category}.json"

    save_data = []
    for tc, meta in zip(test_cases, [m for m in run_metas if not m.get("error")]):
        save_data.append({
            "id":              meta["id"],
            "input":           tc.input,
            "expected_output": tc.expected_output,
            "actual_output":   tc.actual_output,
            "elapsed_ms":      meta["elapsed_ms"],
            "num_sources":     meta["num_sources"],
        })

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(save_data, f, indent=2, ensure_ascii=False)

    print(f"\n[INFO] Results saved to {out_path}")


if __name__ == "__main__":
    main()
