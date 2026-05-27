"""
trace_query.py — Step-by-step trace of the full RAG pipeline

Run this to see EXACTLY what happens when a PM asks a question:
    uv run python trace_query.py

Change QUERY and PROJECT_ID at the bottom to test different questions.
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from app.rag.query_intent import classify_query_intent, QueryIntent
from app.core.retrieval.retriever import (
    retrieve_documents,
    retrieve_commitment_documents,
    retrieve_decision_candidates,
)
from app.services.answer_service import (
    _detect_speaker_name,
    _retrieve_summary_chunks,
    _build_context,
    _build_prompt,
    _call_gemini,
    _extract_sources,
)
from app.core.storage.db import get_raw_collection


# ─────────────────────────────────────────────────────────────
# CHANGE THESE TO TEST DIFFERENT QUERIES
# ─────────────────────────────────────────────────────────────
QUERY      = "What did Harsh Vardhan explain about the two AI approaches?"
PROJECT_ID = "proj_nolocode_001"
# ─────────────────────────────────────────────────────────────


def divider(title):
    print()
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)


def sub(label, value=""):
    print(f"  >> {label}: {value}")


def trace_pipeline(query: str, project_id: str):

    # ─── STEP 0: What are we starting with? ─────────────────
    divider("STEP 0 — Input")
    sub("Question", query)
    sub("Project ID", project_id)
    print("""
  What this means:
    - We only look inside this one project's meetings.
    - Data from other projects NEVER mixes in. That is enforced
      at every retrieval call — project_id is always a filter.
""")

    # ─── STEP 1: Intent Classification ──────────────────────
    divider("STEP 1 — Classify Query Intent")
    print("""
  What is happening:
    We read the question and decide WHAT TYPE of answer is needed.
    This determines HOW we search the database.
    It uses simple regex pattern matching — no AI needed here.

  The 7 possible types:
    DECISION    → "decided / agreed / confirmed / what was decided"
    COMMITMENT  → "action item / who will / next steps / deliverable"
    QUESTION    → "what questions were asked / client questions"
    SUMMARY     → "summary / overview / recap / progress summary"
    SPEAKER     → "what did [name] say / mention / discuss / according to"
    TIMELINE    → "timeline / deadline / last week / what changed"
    GENERAL     → anything else (catch-all)
""")

    intent = classify_query_intent(query)
    sub("Detected intent", intent.value)

    # Explain why this intent was chosen
    intent_reasons = {
        QueryIntent.DECISION:   "Found keywords like: decided / agreed / confirmed / final decision",
        QueryIntent.COMMITMENT: "Found keywords like: action item / who will / next steps / deliverable",
        QueryIntent.QUESTION:   "Found keywords like: question / what was asked / client questions",
        QueryIntent.SUMMARY:    "Found keywords like: summary / overview / recap / progress",
        QueryIntent.SPEAKER:    "Found speech-act pattern: 'what did [name] say/mention/discuss' or 'according to'",
        QueryIntent.TIMELINE:   "Found keywords like: timeline / deadline / last week / what changed",
        QueryIntent.GENERAL:    "No specific keywords matched — using general semantic search",
    }
    sub("Why", intent_reasons[intent])

    # ─── STEP 2: Choose Retrieval Strategy ──────────────────
    divider("STEP 2 — Choose Retrieval Strategy")
    print("""
  What is happening:
    Based on the intent, we pick HOW to search ChromaDB.

  ChromaDB is our local database that stores all meeting chunks.
  Each chunk = one speaker's block of speech + its metadata.

  Two ways to search:
    1. SEMANTIC SEARCH  → Converts your question into a vector
                          (768 numbers), then finds chunks whose
                          vectors are mathematically closest.
                          Used for most query types.

    2. METADATA FILTER  → Directly filters by fields like
                          speaker_name="Bhavneet Mhajan" or
                          is_meeting_summary=True.
                          No vector math — like a SQL WHERE clause.
                          Used for SUMMARY and signal-tagged chunks.
""")

    strategy_map = {
        QueryIntent.SUMMARY:    "Metadata filter only — fetch is_meeting_summary=True (no vector search)",
        QueryIntent.DECISION:   "Semantic search (broad — no hard filter, decision signals are weak)",
        QueryIntent.COMMITMENT: "Semantic search + metadata filter: contains_commitment=True",
        QueryIntent.QUESTION:   "Semantic search + metadata filter: contains_question=True",
        QueryIntent.SPEAKER:    "Semantic search + metadata filter: speaker_name=<name detected from query>",
        QueryIntent.TIMELINE:   "Semantic search (date filtering added when multiple meetings exist)",
        QueryIntent.GENERAL:    "Semantic search (no extra filters)",
    }
    sub("Strategy chosen", strategy_map[intent])

    # ─── STEP 3: Run Retrieval ───────────────────────────────
    divider("STEP 3 — Retrieve Relevant Chunks from ChromaDB")
    print("""
  What is happening:
    We query ChromaDB. It returns the most relevant chunks
    (pieces of transcript text) for this question + project.

    Each chunk has:
      - text        : what was actually said
      - speaker_name: who said it
      - speaker_role: client / developer / project_manager
      - meeting_date: when the meeting happened
      - signals     : contains_decision / contains_commitment / etc.
""")

    # Run the right retrieval based on intent
    if intent == QueryIntent.SUMMARY:
        print("  [Fetching summary chunks via metadata filter...]")
        documents = _retrieve_summary_chunks(project_id)

    elif intent == QueryIntent.DECISION:
        print("  [Running broad semantic search for decision context...]")
        documents = retrieve_decision_candidates(query, project_id, k=10)

    elif intent == QueryIntent.COMMITMENT:
        print("  [Running semantic search + contains_commitment=True filter...]")
        documents = retrieve_commitment_documents(query, project_id, k=10)

    elif intent == QueryIntent.QUESTION:
        name = _detect_speaker_name(query, project_id)
        filters = {"contains_question": True}
        if name:
            filters["speaker_name"] = name
            print(f"  [Detected speaker name in query: '{name}']")
            print(f"  [Running semantic search filtered to contains_question=True + speaker_name={name}...]")
        else:
            print("  [Running semantic search filtered to contains_question=True...]")
        documents = retrieve_documents(query, project_id, filters=filters, k=10)

    elif intent == QueryIntent.SPEAKER:
        name = _detect_speaker_name(query, project_id)
        if name:
            print(f"  [Detected speaker name in query: '{name}']")
            print(f"  [Running semantic search filtered to speaker_name={name}...]")
        else:
            print("  [No speaker name detected — running general semantic search...]")
        filters = {"speaker_name": name} if name else None
        documents = retrieve_documents(query, project_id, filters=filters, k=10)

    else:
        print("  [Running standard semantic search...]")
        documents = retrieve_documents(query, project_id, k=10)

    sub("Chunks retrieved", len(documents))

    if not documents:
        print("\n  WARNING: No chunks found! Check that the meeting was ingested.")
        print("           Run: uv run python inspect_db.py")
        return

    print()
    print("  Chunks retrieved (each = one speaker's turn in the meeting):")
    print()
    for i, doc in enumerate(documents, 1):
        m = doc.metadata
        print(f"  Chunk #{i}")
        print(f"    Speaker : {m.get('speaker_name','?')} [{m.get('speaker_role','?')}]")
        print(f"    Meeting : {m.get('meeting_title','?')} ({m.get('meeting_date','?')})")
        print(f"    Signals : decision={m.get('contains_decision')}  "
              f"commitment={m.get('contains_commitment')}  "
              f"question={m.get('contains_question')}")
        print(f"    Text    : {doc.page_content[:120]}{'...' if len(doc.page_content) > 120 else ''}")
        print()

    # ─── STEP 4: Build Context ───────────────────────────────
    divider("STEP 4 — Build Context String for the LLM")
    print("""
  What is happening:
    We take all the retrieved chunks and format them into
    one big text block. This is what we will send to Gemini
    so it can read the relevant parts of the meeting.

    Format per chunk:
      [N] Meeting: <title> (<date>)
      Speaker: <name> (<role>)
      Content: <what they said>
""")

    context = _build_context(documents)
    print("  Context preview (first 600 chars of what Gemini will read):")
    print()
    print("  " + "\n  ".join(context[:600].split("\n")))
    if len(context) > 600:
        print(f"  ... [{len(context) - 600} more characters]")

    # ─── STEP 5: Build Prompt ────────────────────────────────
    divider("STEP 5 — Build Prompt for Gemini")
    print("""
  What is happening:
    We wrap the context + the user's question inside a
    prompt template. The template gives Gemini instructions
    on HOW to answer — different templates for each intent type.

    For example:
      COMMITMENT template → "Extract action items. For each,
                              state who committed, what they will
                              do, and deadline if mentioned."
      SUMMARY template    → "Synthesize summaries chronologically.
                              Cover decisions, status, open issues."
""")

    prompt = _build_prompt(query, context, intent)
    print(f"  Total prompt length: {len(prompt)} characters")
    print()
    print("  Full prompt being sent to Gemini:")
    print()
    print("  " + "\n  ".join(prompt[:800].split("\n")))
    if len(prompt) > 800:
        print(f"  ... [{len(prompt) - 800} more characters]")

    # ─── STEP 6: Call Gemini ─────────────────────────────────
    divider("STEP 6 — Send Prompt to Gemini LLM")
    print("""
  What is happening:
    We send the full prompt (context + instructions + question)
    to Gemini via the Google AI API.

    Gemini reads all the transcript chunks and generates a
    grounded answer — it can ONLY use what is in the context
    we provided. It cannot make things up from outside.

    Model: gemini-2.5-flash-lite
""")

    print("  [Calling Gemini API... this takes 2-5 seconds]")
    try:
        answer = _call_gemini(prompt)
        print("  [Response received]")
    except Exception as e:
        print(f"  ERROR calling Gemini: {e}")
        return

    # ─── STEP 7: Extract Sources ─────────────────────────────
    divider("STEP 7 — Extract Sources")
    print("""
  What is happening:
    We read the metadata of every chunk we retrieved and
    build a deduplicated list of sources — meeting + speaker.

    This is what lets the PM know WHERE the answer came from.
    Every answer must be traceable to a real meeting moment.
""")

    sources = _extract_sources(documents)
    print(f"  {len(sources)} unique sources found:")
    for s in sources:
        print(f"    - {s['meeting_title']} ({s['meeting_date']}) | {s['speaker_name']}")

    # ─── FINAL OUTPUT ────────────────────────────────────────
    divider("FINAL OUTPUT — What the PM Sees")
    print()
    print(f"  Question : {query}")
    print(f"  Intent   : {intent.value}")
    print()
    print("  Answer:")
    print()
    for line in answer.split("\n"):
        print(f"    {line}")
    print()
    print("  Sources:")
    for s in sources:
        print(f"    - {s['meeting_title']} ({s['meeting_date']}) — {s['speaker_name']}")
    print()
    divider("PIPELINE COMPLETE")
    print()
    print("  Summary of what just happened:")
    print(f"    1. Query classified as '{intent.value}'")
    print(f"    2. {len(documents)} chunks retrieved from ChromaDB")
    print(f"    3. Context built ({len(context)} chars)")
    print(f"    4. Prompt built ({len(prompt)} chars) and sent to Gemini")
    print(f"    5. Answer generated from real transcript data")
    print(f"    6. {len(sources)} sources attributed")
    print()


if __name__ == "__main__":
    trace_pipeline(QUERY, PROJECT_ID)
