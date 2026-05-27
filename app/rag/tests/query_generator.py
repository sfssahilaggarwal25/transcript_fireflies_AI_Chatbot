"""
query_generator.py

Generates additional easy-level test queries using the Gemini API.
Uses existing easy.json entries as few-shot examples so Gemini matches
the exact schema and difficulty standard.

Usage:
    python -m app.tests.query_generator --project-id <id> --count 5
    python -m app.tests.query_generator --project-id <id> --count 10 --dry-run
    python -m app.tests.query_generator --count 5   (no DB context — generic queries)
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from google import genai

load_dotenv()

# ── Paths ─────────────────────────────────────────────────────────────────────

_TESTS_DIR = Path(__file__).parent
_EASY_FILE = _TESTS_DIR / "query_bank" / "easy.json"

_MODEL = "gemini-2.5-flash-lite"

# ── Regex patterns copied from query_intent.py ────────────────────────────────
# These define EXACTLY what keywords make a query "easy" (regex-catchable).
# Gemini must use at least one of these words per query it generates.

EASY_KEYWORD_MAP = {
    "summary_query": [
        "summary", "summarize", "overview", "recap",
        "progress summary", "project summary", "high level summary",
    ],
    "decision_query": [
        "decision", "decisions", "decided", "agreed", "finalized",
        "approved", "confirmed", "what was decided", "what did we decide",
        "final decision",
    ],
    "commitment_query": [
        "commitment", "commitments", "action item", "action items",
        "follow up", "follow-up", "who will", "who committed",
        "what needs to be done", "next steps", "deliverable", "deliverables",
    ],
    "question_query": [
        "question", "questions", "what did they ask",
        "what was asked", "client questions",
    ],
    "general_query": [],  # no keywords — falls through all regex patterns
}


# ── Step 1a: Fetch meeting summaries from ChromaDB ────────────────────────────

def fetch_meeting_summaries(project_id: str) -> list[dict]:
    """
    Pull is_meeting_summary=True chunks from ChromaDB for the given project.
    These are already condensed versions of the transcripts — short enough to
    inject into a prompt without blowing up the token count.

    Returns a list of dicts:
        [{"meeting_title": ..., "meeting_date": ..., "summary": ...}, ...]
    sorted chronologically.

    Returns [] with a warning if ChromaDB is unavailable or project has no data.
    """
    try:
        from app.core.storage.db import get_raw_collection

        collection = get_raw_collection()
        results    = collection.get(
            where={
                "$and": [
                    {"project_id": {"$eq": project_id}},
                    {"is_meeting_summary": {"$eq": True}},
                ]
            },
            include=["documents", "metadatas"],
        )

        ids = results.get("ids", [])
        if not ids:
            print(f"[WARN] No summary chunks found in ChromaDB for project_id='{project_id}'")
            print("       Queries will be generated without meeting context.")
            return []

        summaries = []
        for i in range(len(ids)):
            meta = results["metadatas"][i]
            summaries.append({
                "meeting_title": meta.get("meeting_title", "Unknown Meeting"),
                "meeting_date":  meta.get("meeting_date", ""),
                "summary":       results["documents"][i],
            })

        summaries.sort(key=lambda x: x["meeting_date"])
        print(f"[INFO] Fetched {len(summaries)} meeting summary chunk(s) from ChromaDB")
        return summaries

    except Exception as e:
        print(f"[WARN] Could not connect to ChromaDB: {e}")
        print("       Queries will be generated without meeting context.")
        return []


# ── Step 1b: Load existing queries ────────────────────────────────────────────

def load_existing(filepath: Path) -> tuple[list[dict], list[str]]:
    """
    Returns (all_query_objects, all_query_texts).
    query_texts is used for deduplication.
    """
    if not filepath.exists():
        print(f"[ERROR] File not found: {filepath}")
        sys.exit(1)

    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    queries = data.get("queries", [])
    texts   = [q["query"].lower().strip() for q in queries]
    return queries, texts


# ── Step 2: Build the prompt ──────────────────────────────────────────────────

def _build_prompt(
    existing_queries: list[dict],
    count: int,
    summaries: list[dict],
) -> str:
    """
    Build a detailed prompt that gives Gemini:
    - What this chatbot does (context)
    - Real meeting summaries fetched from ChromaDB (grounding — avoids hallucination)
    - The 5 easy intents and their exact trigger keywords
    - The exact JSON schema each query must follow
    - All existing queries as few-shot examples (so it doesn't duplicate)
    - A precise instruction for how many to generate
    """

    existing_block = json.dumps(existing_queries, indent=2, ensure_ascii=False)

    keywords_block = ""
    for intent, keywords in EASY_KEYWORD_MAP.items():
        if keywords:
            kw_list = ", ".join(f'"{k}"' for k in keywords)
            keywords_block += f"  {intent}: {kw_list}\n"
        else:
            keywords_block += f"  {intent}: (no keywords — used as fallback when nothing else matches)\n"

    # Build the meeting context block from real ChromaDB summary chunks.
    # If no summaries were fetched (DB unavailable), fall back to the generic domain description.
    if summaries:
        meeting_lines = []
        for i, s in enumerate(summaries, 1):
            meeting_lines.append(
                f"Meeting {i}: \"{s['meeting_title']}\" ({s['meeting_date']})\n"
                f"{s['summary']}"
            )
        meetings_block = "\n\n".join(meeting_lines)
        context_section = f"""## Actual Meeting Content — USE THIS to write grounded queries
The following are real summaries of the meetings stored in this project's database.
Your queries MUST be about topics, speakers, decisions, or themes that appear in these summaries.
Do NOT invent topics that are not present below.

{meetings_block}"""
    else:
        context_section = """## Domain Context (no DB summaries available — use general tech meeting topics)
This chatbot is used by project managers at a SERVICE-BASED SOFTWARE COMPANY.
All meeting transcripts are TECHNICAL discussions only — between developers, project managers, and clients.

Topics that appear in these meetings:
- Software development: API design, backend/frontend work, database schema, code reviews
- Project delivery: sprint planning, feature delivery, deployment, bug fixes, release timelines
- Client requirements: client feedback on features, requirement changes, acceptance criteria
- Technical blockers: integration issues, performance problems, third-party API problems
- Team coordination: task assignment, developer responsibilities, testing, QA

Topics that DO NOT appear in these meetings (do NOT generate queries about):
- Marketing, sales, HR, finance, accounting, legal, or non-technical business strategy"""

    prompt = f"""You are a test query generator for an AI Meeting Intelligence chatbot.
The chatbot answers questions about past project meetings stored as transcripts in a vector database.
Every query is scoped to a project_id. The chatbot retrieves transcript chunks and generates answers using an LLM.

{context_section}

## Intent Classification System
The chatbot classifies each query into one of these intents:
- summary_query    → fetch meeting summary chunks (no vector search)
- decision_query   → retrieve decision-related chunks via hybrid search
- commitment_query → retrieve chunks with contains_commitment=True metadata
- question_query   → retrieve chunks with contains_question=True metadata
- general_query    → broad hybrid retrieval, no metadata filter

## What makes a query EASY
An "easy" query must contain at least one keyword that the regex classifier can catch directly.
No LLM intent classification should be needed — the regex alone handles it.

Regex trigger keywords per intent:
{keywords_block}

## JSON Schema — every query you generate MUST follow this exactly
{{
  "id": "easy_NNN",
  "query": "the question text",
  "expected_intent": "one of the 5 intents above",
  "expected_strategy": "one of: summary_chunks_raw_collection | hybrid_retrieve_no_filter | hybrid_retrieve_contains_commitment_filter | hybrid_retrieve_contains_question_filter",
  "tags": ["array", "of", "short", "labels"],
  "notes": "one sentence: what this query specifically tests and why it is easy",
  "evaluation_hints": {{
    "must_contain": ["what a good answer must include"],
    "must_not_contain": ["what a good answer must NOT say"],
    "should_cite_sources": true,
    "expected_source_type": "brief description of the chunk type expected"
  }}
}}

## Existing queries — DO NOT duplicate these
{existing_block}

## Your task
Generate exactly {count} NEW easy-level queries that:
1. Are NOT duplicates of the existing queries above (different wording, different phrasing)
2. Cover a variety of the 5 intents — do not generate all the same intent
3. Each contains at least one regex trigger keyword for its intent
4. Use natural, realistic language a project manager would actually say
5. Are answerable from the actual meeting content shown above
6. Follow the JSON schema above exactly — no extra fields, no missing fields

IDs must continue from where the existing ones end. If the last existing ID is "easy_012", start at "easy_013".

Return ONLY a valid JSON array of {count} query objects. No explanation text, no markdown fences.
The response must start with [ and end with ].
"""
    return prompt


# ── Step 3: Call Gemini API ───────────────────────────────────────────────────

def call_gemini(prompt: str) -> str:
    """
    Call Gemini API and return the raw response text.
    Follows the same pattern used in answer_service.py.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[ERROR] GEMINI_API_KEY is not set in your .env file.")
        sys.exit(1)

    print(f"[INFO] Calling Gemini API ({_MODEL})...")

    client   = genai.Client(api_key=api_key)
    response = client.models.generate_content(model=_MODEL, contents=prompt)
    return response.text.strip()


# ── Step 4: Parse and validate response ──────────────────────────────────────

_REQUIRED_FIELDS = {
    "id", "query", "expected_intent", "expected_strategy",
    "tags", "notes", "evaluation_hints",
}

_VALID_INTENTS = set(EASY_KEYWORD_MAP.keys())


def _extract_json_array(raw: str) -> list:
    """
    Extract JSON array from Gemini's response.
    Handles cases where the model wraps output in markdown fences.
    """
    text = raw.strip()

    # Strip markdown fences if present
    if text.startswith("```"):
        text = re.sub(r"^```[a-z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text).strip()

    start = text.find("[")
    end   = text.rfind("]")
    if start == -1 or end == -1:
        raise ValueError("No JSON array found in response")

    return json.loads(text[start : end + 1])


def validate_queries(raw_queries: list, existing_texts: list[str]) -> list[dict]:
    """
    Validate each query against the schema and deduplicate.
    Returns only the valid, non-duplicate queries.
    """
    valid = []
    seen  = set(existing_texts)

    for i, q in enumerate(raw_queries):
        label = q.get("id", f"item[{i}]")

        # Schema check
        missing = _REQUIRED_FIELDS - set(q.keys())
        if missing:
            print(f"  [SKIP] {label} — missing fields: {missing}")
            continue

        # Intent check
        if q["expected_intent"] not in _VALID_INTENTS:
            print(f"  [SKIP] {label} — unknown intent: {q['expected_intent']}")
            continue

        # Duplicate check
        query_text = q["query"].lower().strip()
        if query_text in seen:
            print(f"  [SKIP] {label} — duplicate query text")
            continue

        seen.add(query_text)
        valid.append(q)
        print(f"  [OK]   {label} | intent={q['expected_intent']} | \"{q['query'][:60]}\"")

    return valid


# ── Step 5: Merge and save ────────────────────────────────────────────────────

def _next_id_number(existing_queries: list[dict]) -> int:
    """Find the highest existing easy_NNN number and return the next integer."""
    max_n = 0
    for q in existing_queries:
        match = re.search(r"easy_(\d+)", q.get("id", ""))
        if match:
            max_n = max(max_n, int(match.group(1)))
    return max_n + 1


def save_merged(new_queries: list[dict], filepath: Path, dry_run: bool = False) -> None:
    """
    Re-assign sequential IDs, merge with existing queries, and save.
    dry_run=True prints the merged result without writing to disk.
    """
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    existing = data.get("queries", [])
    start_n  = _next_id_number(existing)

    # Re-assign IDs sequentially — Gemini's IDs might be off
    for offset, q in enumerate(new_queries):
        q["id"] = f"easy_{start_n + offset:03d}"

    merged = existing + new_queries

    data["queries"]              = merged
    data["_metadata"]["count"]   = len(merged)

    output = json.dumps(data, indent=2, ensure_ascii=False)

    if dry_run:
        print("\n[DRY RUN] Would write the following to easy.json:")
        print(output)
        return

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(output)

    print(f"\n[SAVED] easy.json now has {len(merged)} queries (+{len(new_queries)} new)")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate easy-level test queries using Gemini API"
    )
    parser.add_argument(
        "--project-id",
        type=str,
        default=None,
        help="Project ID to fetch real meeting summaries from ChromaDB (recommended)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=5,
        help="Number of new queries to generate (default: 5)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print generated queries without saving to easy.json",
    )
    args = parser.parse_args()

    print(f"\n{'='*55}")
    print(f"  Query Generator — Easy Level")
    print(f"  Generating {args.count} new queries via Gemini")
    if args.project_id:
        print(f"  Project ID: {args.project_id}")
    else:
        print(f"  Project ID: not provided — generic mode")
    print(f"{'='*55}\n")

    # Step 1a: Fetch meeting summaries from ChromaDB (for context grounding)
    summaries = []
    if args.project_id:
        summaries = fetch_meeting_summaries(args.project_id)
    else:
        print("[WARN] No --project-id given. Gemini will generate generic queries.")
        print("       Run with --project-id <id> for queries grounded in your real data.\n")

    # Step 1b: Load existing
    existing_queries, existing_texts = load_existing(_EASY_FILE)
    print(f"[INFO] Loaded {len(existing_queries)} existing queries from easy.json")

    # Step 2: Build prompt
    prompt = _build_prompt(existing_queries, args.count, summaries)
    print(f"[INFO] Prompt built ({len(prompt)} chars)\n")

    # Step 3: Call Gemini
    raw_response = call_gemini(prompt)
    print(f"[INFO] Response received ({len(raw_response)} chars)\n")

    # Step 4: Parse + validate
    print("[INFO] Validating generated queries:")
    try:
        raw_queries = _extract_json_array(raw_response)
    except (ValueError, json.JSONDecodeError) as e:
        print(f"[ERROR] Could not parse Gemini's response as JSON: {e}")
        print("[RAW RESPONSE]:", raw_response[:500])
        sys.exit(1)

    valid_queries = validate_queries(raw_queries, existing_texts)
    print(f"\n[INFO] {len(valid_queries)} valid queries out of {len(raw_queries)} generated")

    if not valid_queries:
        print("[ERROR] No valid queries generated. Try again or increase --count.")
        sys.exit(1)

    # Step 5: Save
    save_merged(valid_queries, _EASY_FILE, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
