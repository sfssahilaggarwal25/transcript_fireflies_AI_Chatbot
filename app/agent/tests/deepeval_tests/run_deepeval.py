"""
run_deepeval.py — Check retrieval accuracy using DeepEval metrics.

HOW TO RUN
----------
    python -m app.agent.tests.deepeval_tests.run_deepeval

WHAT IT DOES
------------
1. Load test questions (goldens) from goldens.py
2. For each question, call the retriever DIRECTLY (no LLM answer generation)
3. Score the retrieved chunks using 3 pure retrieval metrics
4. Print a pass/fail table with scores

WHY CALL THE RETRIEVER DIRECTLY (not the full agent)?
-----------------------------------------------------
We want to measure retrieval accuracy — did we fetch the RIGHT chunks?
The full agent also generates an answer, which adds LLM noise.
Calling the retriever directly gives a clean signal on retrieval quality alone.

METRICS
-------
  ContextualRelevancyMetric — Are the retrieved chunks relevant to the query?
  ContextualRecallMetric    — Do the retrieved chunks cover the expected facts?
  ContextualPrecisionMetric — Are the most relevant chunks ranked first?

  (AnswerRelevancyMetric is intentionally excluded — that measures answer
  quality, not retrieval quality.)
"""

import asyncio
import os
import sys
import time
from pathlib import Path

# Add project root to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

from deepeval import evaluate
from deepeval.metrics import (
    ContextualPrecisionMetric,
    ContextualRecallMetric,
    ContextualRelevancyMetric,
)
from deepeval.models import DeepEvalBaseLLM
from deepeval.test_case import LLMTestCase
from google import genai as google_genai

from app.agent.tests.deepeval_tests.goldens import PROJECT_QUERIES, CORRECT_QUERIES
from app.core.retrieval.hybrid import hybrid_retrieve
from app.core.retrieval.reranker import rerank_documents


# ── Step 1: Tell DeepEval to use Gemini instead of OpenAI ────────────────────
# DeepEval uses OpenAI by default to judge answers.
# We don't have an OpenAI key, so we wrap our Gemini client here.

class GeminiJudge(DeepEvalBaseLLM):

    MODEL = "gemini-2.5-pro"

    def __init__(self):
        self.client = google_genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    def load_model(self):
        return self.client

    def generate(self, prompt: str, schema=None) -> str:
        response = self.client.models.generate_content(
            model=self.MODEL,
            contents=prompt,
        )
        return response.text

    async def a_generate(self, prompt: str, schema=None) -> str:
        # Run blocking call in thread pool so the event loop stays free for
        # concurrent metric evaluations (asyncio.gather).
        # Retry up to 3 times with exponential backoff — Gemini Pro drops
        # connections under concurrent load (RemoteProtocolError / timeout).
        last_exc: Exception | None = None
        for attempt in range(3):
            try:
                return await asyncio.to_thread(self.generate, prompt)
            except Exception as exc:
                last_exc = exc
                wait = 2 ** attempt   # 1s → 2s → 4s
                await asyncio.sleep(wait)
        raise RuntimeError(f"GeminiJudge failed after 3 attempts") from last_exc

    def get_model_name(self) -> str:
        return self.MODEL


# ── Step 2: Retrieve chunks for a question (no LLM, no answer generation) ────

PROJECT_ID = "proj_nolocode_001"

def retrieve_chunks(
    question: str,
    hard_filters: dict | None = None,
    speaker: str | None = None,
    dense_query: str | None = None,
    reranker_hint: str | None = None,
) -> list[str]:
    """
    Run the retriever and return chunk texts ready for DeepEval scoring.

    Two paths based on whether a speaker filter is active:

    Speaker query  (speaker != None)
      → hard_filters applied at DB level (only that speaker's chunks returned)
      → dense_query strips the speaker name so vector search focuses on the
        topic only ("AI architecture", not "What did Ashpreet say about AI
        architecture?"). Speaker is already handled by hard_filters — encoding
        the name again in the embedding dilutes the topical signal.
      → chunk text prepended with "Speaker Name: ..." so ContextualRelevancy
        judge can see the attribution (first-person speech has no name in text).

    Topic query  (speaker == None)
      → no speaker filter, chunks returned as-is
      → ContextualRelevancy judges topic match directly against chunk text

    Both paths run through the reranker after retrieval, mirroring production.
    The reranker scores each chunk 0-10 and hard-drops score ≤ 2 — this is the
    adaptive K: talkative speakers return more raw candidates but the reranker
    cuts to the relevant ones regardless of speaker volume.
    """
    docs = hybrid_retrieve(
        query=question,
        project_id=PROJECT_ID,
        hard_filters=hard_filters or None,
        dense_query=dense_query or None,
    )

    # Rerank mirrors the production pipeline and acts as adaptive K:
    # 25 raw candidates → reranker scores → quality chunks only.
    #
    # topic_hint rule:
    #   reranker_hint (explicit) → always takes priority when provided in golden metadata.
    #     Use for decision/commitment queries where the question alone can't distinguish
    #     "presenting an approach" from "confirming a decision was made".
    #   Speaker query (no reranker_hint) → use dense_query (strips speaker name,
    #     keeps specific topic vocab so reranker focuses on the right sub-domain).
    #   No-speaker query (no reranker_hint) → use "" (original question guides reranker).
    effective_topic_hint = reranker_hint or (dense_query if speaker else "")
    docs = rerank_documents(
        query=question,
        documents=docs,
        topic_hint=effective_topic_hint,
        speaker_hint=speaker or "",
    )

    # DEBUG: show every chunk's reranker score before the quality filter
    print(f"\n  ── RERANKER SCORES ({len(docs)} docs after rerank) ──")
    for d in docs:
        score = d.metadata.get("_rerank_score", "?")
        rel   = d.metadata.get("_relevance", "?")
        spk   = d.metadata.get("speaker_name", "?")
        preview = d.page_content[:90].replace("\n", " ")
        print(f"    [{score:>5}] {rel:<4} | {spk:<25} | {preview}")

    # Keep only direct-pass chunks (rerank score ≥ 7, _relevance == "high").
    # Soft-pass chunks (3-6) are tangential — the LLM can use them in production
    # but ContextualRelevancy penalises every irrelevant chunk in retrieval_context,
    # so they drag the score down without adding coverage.
    # Fallback: if fewer than 3 high-quality chunks, include all (avoids empty context).
    high_quality = [d for d in docs if d.metadata.get("_relevance") == "high"]
    docs = high_quality if len(high_quality) >= 3 else docs

    chunks = []
    for doc in docs:
        if not doc.page_content:
            continue
        if speaker:
            # Prepend speaker name so the relevancy judge sees attribution
            stored_name = doc.metadata.get("speaker_name", speaker)
            chunks.append(f"{stored_name}: {doc.page_content}")
        else:
            chunks.append(doc.page_content)

    return chunks


# ── Step 3: Main — run all goldens and evaluate ───────────────────────────────

def main():
    # Load all test questions, skip ones marked as known gaps
    # all_goldens = PROJECT_QUERIES.goldens
    all_goldens = CORRECT_QUERIES.goldens
    goldens = [
        g for g in all_goldens
        if not (g.additional_metadata or {}).get("known_gap", False)
    ]

    print(f"\nRunning {len(goldens)} goldens (skipped {len(all_goldens) - len(goldens)} known gaps)\n")

    # 3 pure retrieval metrics — all use Gemini as the judge
    judge = GeminiJudge()
    PASS_THRESHOLD = 0.7

    metrics = [
        # async_mode=False: metrics run sequentially, not concurrently.
        # Gemini Pro drops connections when 3 metrics fire ~50 API calls simultaneously.
        # Sequential mode trades speed for stability — acceptable for offline eval.
        ContextualRelevancyMetric(threshold=PASS_THRESHOLD, model=judge, include_reason=True, async_mode=False),
        ContextualRecallMetric(threshold=PASS_THRESHOLD, model=judge, include_reason=True, async_mode=False),
        ContextualPrecisionMetric(threshold=PASS_THRESHOLD, model=judge, include_reason=True, async_mode=False),
    ]

    # Run the retriever for each golden and build DeepEval test cases
    test_cases = []

    for i, golden in enumerate(goldens, 1):
        gid = (golden.additional_metadata or {}).get("id", f"#{i}")
        print(f"  [{i:02d}/{len(goldens)}] {gid}  →  {golden.input[:60]}…", end="", flush=True)

        meta          = golden.additional_metadata or {}
        speaker       = meta.get("speaker")        # None for topic queries
        dense_query   = meta.get("dense_query")    # topic-only query for vector search
        reranker_hint = meta.get("reranker_hint")  # intent hint for reranker (optional)

        hard_filters = {}
        if speaker:
            hard_filters["speaker_name"] = speaker

        t0 = time.time()
        chunks = retrieve_chunks(
            golden.input,
            hard_filters=hard_filters or None,
            speaker=speaker,                    # triggers name-prepend path
            dense_query=dense_query,            # None falls back to full question
            reranker_hint=reranker_hint,        # None → uses topic_hint rule
        )
        elapsed = round((time.time() - t0) * 1000)

        # LLMTestCase for retrieval-only evaluation:
        #   input            = the PM's question
        #   actual_output    = expected_output (we're not testing the LLM answer here)
        #   expected_output  = the ideal answer (used by ContextualRecall to check coverage)
        #   retrieval_context = chunks the retriever actually fetched
        test_case = LLMTestCase(
            input=golden.input,
            actual_output=golden.expected_output,
            expected_output=golden.expected_output,
            # context     = ideal chunks from the golden (ground truth)
            # retrieval_context = what the retriever actually fetched right now
            context=golden.context or [],
            retrieval_context=chunks,
        )
        test_cases.append(test_case)

        print(f"  {elapsed}ms  ({len(chunks)} chunks)")

    # Run DeepEval — it scores all test cases and prints a table
    print(f"\nScoring {len(test_cases)} test cases with DeepEval…\n")
    evaluate(test_cases=test_cases, metrics=metrics)


if __name__ == "__main__":
    main()