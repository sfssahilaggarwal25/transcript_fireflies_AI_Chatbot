# System Architecture — AI Meeting Intelligence
<!-- AUTO-UPDATE RULE: Update this file whenever you change any of the sections below.
     Sections are tagged with the file they mirror. If you change that file, update this section.
     Last updated: 2026-05-25 -->

---

## Table of Contents
1. [One-Line Goal](#1-one-line-goal)
2. [Tech Stack](#2-tech-stack)
3. [File Map](#3-file-map)
4. [Data Flow — Two Pipelines](#4-data-flow--two-pipelines)
5. [Ingestion Pipeline (Webhook → ChromaDB)](#5-ingestion-pipeline-webhook--chromadb)
6. [Query Pipeline (Question → Answer)](#6-query-pipeline-question--answer)
7. [Step 1 — Query Understanding](#7-step-1--query-understanding)
8. [Step 2 — Retrieval (8 Modes)](#8-step-2--retrieval-8-modes)
9. [Step 3 — Re-ranking](#9-step-3--re-ranking)
10. [Step 3.5 — Context Expansion](#10-step-35--context-expansion)
11. [Step 4 — Context + Prompt Building](#11-step-4--context--prompt-building)
12. [Step 5 — LLM Answer Generation](#12-step-5--llm-answer-generation)
13. [Source Extraction](#13-source-extraction)
14. [Chunk Schema (Full 5-Level)](#14-chunk-schema-full-5-level)
15. [Content Signals (5 Types)](#15-content-signals-5-types)
16. [Routing Decision Tree](#16-routing-decision-tree)
17. [Prompt Templates (11 Types)](#17-prompt-templates-11-types)
18. [Adaptive k Configuration](#18-adaptive-k-configuration)
19. [Streamlit UI](#19-streamlit-ui)
20. [Test Infrastructure](#20-test-infrastructure)
21. [Config & Environment](#21-config--environment)
22. [Known Gaps & Planned Work](#22-known-gaps--planned-work)

---

## 1. One-Line Goal

> A Project Manager selects a project, asks any question about what was said, decided, or assigned across all meetings, and gets a correct grounded answer with the exact source — in under 10 seconds.

**Scope enforcement rule:** Every query is filtered by `project_id` at the backend. This is not a UI feature — Project A data can never appear in Project B's results.

---

## 2. Tech Stack

| Layer | Technology | Why |
|---|---|---|
| **API** | FastAPI (`main.py`) | Webhook receiver + `/query` endpoint |
| **UI** | Streamlit (`streamlit_app.py`) | POC chat interface |
| **Vector DB** | ChromaDB (local, persistent) | Free, no server, LangChain abstraction |
| **Embeddings** | `gemini-embedding-001` via `langchain-google-genai` | Gemini API already in use |
| **LLM** | `gemini-2.5-flash-lite` (`gemini_client.py`) | Fast, cheap, 3-attempt retry with backoff |
| **BM25** | `rank_bm25` Python library | Exact keyword search alongside dense embeddings |
| **Transcript source** | Fireflies.ai webhook + GraphQL API | Meeting transcript provider |
| **Project config** | `projects.json` | Maps `project_id → meeting_ids + speaker roles` |

---

## 3. File Map
<!-- mirror: all files in app/ -->

```
fireflies_transcript_project/
│
├── main.py                          FastAPI app — /webhook/fireflies + /query endpoints
├── streamlit_app.py                 Streamlit chat UI
├── projects.json                    Project config (meeting_ids, speaker roles)
├── ARCHITECTURE.md                  ← this file
│
├── app/
│   ├── config.py                    Env vars (GEMINI_API_KEY, DEVELOPMENT_MODE, etc.)
│   ├── logging_config.py            setup_pipeline_logging() — stderr handler, suppresses 3rd-party noise
│   │
│   ├── clients/
│   │   ├── fireflies_client.py      GraphQL client — fetches transcript + summary from Fireflies API
│   │   └── gemini_client.py         Gemini API — call_gemini(), call_gemini_raw(), generate_meeting_summary()
│   │                                Model: gemini-2.5-flash-lite | 3-attempt retry (2s/5s/10s backoff)
│   │                                Summary: max 80,000 chars input, 1,024 tokens output cap
│   │
│   ├── handlers/
│   │   └── webhook_handler.py       6-step ingestion pipeline triggered by Fireflies webhook
│   │
│   ├── services/
│   │   │
│   │   ├── answer_service.py        Backward-compat re-export — external callers use answer_question() from here
│   │   ├── prompts.py               ALL prompt templates + understanding prompts + select_template_key()
│   │   ├── query_intent.py          Query understanding — LLM + routing + scope detection
│   │   │
│   │   ├── answer/
│   │   │   ├── pipeline.py          Main RAG pipeline — answer_question() — 5-step orchestrator
│   │   │   ├── builder.py           Context building — build_context(), build_prompt(), extract_sources()
│   │   │   │                        expand_context(), retrieve_summary_chunks(), build_not_found_message()
│   │   │   ├── scope.py             Scope resolution — parse_meeting_scope(), get_scoped_meeting_ids()
│   │   │   └── metadata.py          Metadata short-circuit — handle_metadata_query(), _get_meeting_timings()
│   │   │
│   │   ├── retrieval/
│   │   │   ├── __init__.py          Public API — re-exports all retrieval functions
│   │   │   ├── config.py            RetrievalConfig dataclass + get_retrieval_config() — adaptive k
│   │   │   ├── base.py              Shared utils — _validate_*, _build_filter(), _fetch_project_corpus()
│   │   │   ├── hybrid.py            BM25 + dense hybrid — hybrid_retrieve(), compound_retrieve()
│   │   │   │                        _normalize_for_bm25(), _tokenize(), _bm25_search(), _rrf_merge()
│   │   │   ├── topic.py             topic_summary_retrieve(), retrieve_timeline_documents()
│   │   │   ├── metadata_retrieve.py analytical_retrieve(), contribution_retrieve()
│   │   │   ├── reranker.py          LLM re-ranker — rerank_documents() via Gemini Flash Lite
│   │   │   └── retriever.py         20-line backward-compat shim (kept for trace_query.py)
│   │   │
│   │   ├── storage/
│   │   │   ├── db.py                get_vectorstore() (LangChain Chroma) + get_raw_collection() (raw ChromaDB)
│   │   │   ├── chunk_store.py       store_documents(), get_chunks_by_meeting(), get_chunk_count()
│   │   │   └── project_store.py     get_project_for_meeting(), get_speaker_role(), get_speaker_names()
│   │   │
│   │   ├── transcript/
│   │   │   ├── normalize.py         normalize_transcript() — flatten API response, clean ASR noise,
│   │   │   │                        unify start_time/end_time to seconds, parse dateString → YYYY-MM-DD
│   │   │   ├── chunking.py          create_chunks() — utterance splitting, signal detection, adjacency links
│   │   │   │                        build_summary_chunk() — one summary chunk per meeting
│   │   │   └── metadata.py          Meeting metadata extraction (meeting_id, title, date)
│   │   │
│   │   ├── documents/
│   │   │   └── mapper.py            chunks_to_documents() — dict → LangChain Document
│   │   └── embeddings/
│   │       └── gemini_embeddings.py get_embedding_model() — singleton GoogleGenerativeAIEmbeddings
│   │
│   └── tests/
│       ├── query_bank/
│       │   ├── easy.json            21 easy queries, 7 intents, expected_intent + expected_mode
│       │   ├── medium.json          20 meeting-scoped queries, 7 routing rules
│       │   └── hard.json            Edge cases (not yet written)
│       ├── query_generator.py       Gemini-powered query generation grounded in real ChromaDB summaries
│       ├── test_runner.py           Calls answer_question() directly — real pipeline, no HTTP
│       ├── test_retrieval.py        46 no-LLM retrieval assertions
│       ├── report_generator.py      Generates summary.md from test_runner results
│       └── answer_evaluator.py      LLM-based answer quality scoring (1–10)
```

---

## 4. Data Flow — Two Pipelines

```
┌─────────────────────────────────────────────────────────────────┐
│  PIPELINE A — INGESTION  (one-time per meeting)                 │
│                                                                 │
│  Fireflies webhook                                              │
│       │                                                         │
│       ▼                                                         │
│  webhook_handler.py  ──►  normalize.py  ──►  chunking.py       │
│                                │                │               │
│                                │           create_chunks()      │
│                                │           build_summary_chunk() │
│                                │                │               │
│                                ▼                ▼               │
│                          mapper.py  ──►  LangChain Documents    │
│                                               │                 │
│                                               ▼                 │
│                             gemini-embedding-001  (embed)       │
│                                               │                 │
│                                               ▼                 │
│                                      ChromaDB  (persist)        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  PIPELINE B — QUERY  (every PM question)                        │
│                                                                 │
│  Streamlit UI / POST /query                                     │
│       │                                                         │
│       ▼                                                         │
│  pipeline.py → answer_question(query, project_id)              │
│       │                                                         │
│  [1] understand_query()  → QueryUnderstanding                   │
│       │  • Scope detection (pre-LLM, regex)                     │
│       │  • LLM extraction (topic, speaker, signal, dims)        │
│       │  • Python routing (_apply_routing)                      │
│       │                                                         │
│  [2] _retrieve_for_understanding()  → 8 modes                  │
│       │  (hybrid / compound / summary / timeline /              │
│       │   topic_summary / analytical / contribution /           │
│       │   signal_fetch / metadata short-circuit)                │
│       │                                                         │
│  [3] rerank_documents()  → top-N by relevance                  │
│       │                                                         │
│  [3.5] expand_context()  → add prev/next neighbors             │
│       │                                                         │
│  [3.6] chronological sort  (speaker/timeline/topic modes)      │
│       │                                                         │
│  [4] build_context() + build_prompt()                          │
│       │                                                         │
│  [5] call_gemini()  → answer text                              │
│       │                                                         │
│  extract_sources()  → source cards with chunk_num anchors      │
│       │                                                         │
│  {answer, sources, intent, retrieval_mode, num_context_chunks} │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Ingestion Pipeline (Webhook → ChromaDB)
<!-- mirror: app/handlers/webhook_handler.py, app/services/transcript/ -->

**Trigger:** `POST /webhook/fireflies` receives notification from Fireflies.ai when a meeting ends.

**6 Steps:**

```
Step 1 — Fetch transcript
  fireflies_client.py → GraphQL → { id, title, dateString, sentences[], summary{} }
  Retry: 3 attempts × 10s (Fireflies eventual consistency)

Step 2 — Normalize
  normalize.py → normalize_transcript()
  • Flatten nested API response
  • Parse dateString (ISO "T"-split) → YYYY-MM-DD
  • Unify timestamps: rawStartTimeMs/rawEndTimeMs (ms) OR start_time/end_time (seconds)
    → always output start_time/end_time in seconds
  • ASR noise cleaning: strip um/uh/hmm, repeated words
  • Resolve summary: Fireflies summary.overview → Gemini fallback → None

Step 3 — Chunk
  chunking.py → create_chunks()
  • Utterance-based splitting (one speaker = one chunk)
  • MAX_CHARS = 500, MIN_CHARS = 80, HARD_MIN = 15
  • _is_low_quality() junk filter: unique-token ratio < 0.4 OR meaningful-word count < 4
  • _TOPIC_SHIFT_RE: splits same-speaker block on "now"/"next"/"moving on"/etc.
  • _detect_signals() → 5 content signals per chunk (see Section 15)
  • Post-loop pass: prev_chunk_id / next_chunk_id adjacency links
  • build_summary_chunk() → one special chunk per meeting (is_meeting_summary=True)

Step 4 — Stamp project metadata
  project_store.py → get_project_for_meeting(meeting_id)
  • Adds: project_id, project_name, company_id, company_name, speaker_role
  • If meeting_id not in projects.json → pipeline aborts (no broken data stored)

Step 5 — Convert to LangChain Documents
  mapper.py → chunks_to_documents()
  • Chunk dict → Document(page_content=text, metadata={all fields})

Step 6 — Embed + Store
  gemini_embeddings.py → gemini-embedding-001
  chunk_store.py → store_documents() → ChromaDB upsert (chunk_id as document ID)
  • Upsert is idempotent — re-ingestion never creates duplicates
```

**Current DB state:** 1,669 chunks across 10 meetings (1 project: proj_nolocode_001)

---

## 6. Query Pipeline (Question → Answer)
<!-- mirror: app/services/answer/pipeline.py -->

**Entry point:** `answer_question(query: str, project_id: str) → dict`

**Pre-check — Metadata short-circuit:**
```python
if is_metadata_query(query):   # regex, no LLM, no embedding
    return handle_metadata_query(query, project_id)
    # ~80ms — handles: "how many meetings", "list speakers",
    # "who attended X meeting", "meeting timings"
```

**5 Main Steps:**

| Step | Function | Cost | Notes |
|---|---|---|---|
| 1 | `understand_query()` | 1 LLM call (Gemini) | Scope detection is regex (free) |
| 2 | `_retrieve_for_understanding()` | 0 LLM calls | ChromaDB + BM25 math |
| 3 | `rerank_documents()` | 1 LLM call (Gemini Flash Lite) | Skipped for summary/topic_summary/signal_fetch |
| 3.5 | `expand_context()` | 0 LLM calls | ≤10 ChromaDB lookups (top-5 docs × 2 neighbors) |
| 4 | `build_context()` + `build_prompt()` | 0 LLM calls | String assembly |
| 5 | `call_gemini()` | 1 LLM call (Gemini) | Answer generation |

**Total LLM calls per query:** 2–3 (understand + rerank + answer)  
**Total avg latency:** ~3–5 seconds

---

## 7. Step 1 — Query Understanding
<!-- mirror: app/services/query_intent.py, app/services/prompts.py -->

**Function:** `understand_query(query, project_id) → QueryUnderstanding`

### Phase A — Scope Detection (Python regex, runs BEFORE LLM)

```python
# Patterns detected:
"previous meeting"     → scope to most recent meeting
"last meeting"         → scope to most recent meeting
"the first meeting"    → scope to meetings[0] chronologically
"the second meeting"   → scope to meetings[1]
"that meeting"         → scope to most recent meeting
"May 7th meeting"      → date match → ChromaDB metadata lookup → meeting_id(s)
"2026-05-07"           → exact date match

# Result stored in:
scope_meeting_ids: list[str]   # ["01KM2DD6MXGSZ4F1QW0BNJE16N"]
scope_type: str                # "meeting" | "project"
```

### Phase B — LLM Extraction (1 Gemini call)

Two prompt templates depending on scope:
- `UNDERSTANDING_PROMPT_MEETING_LEVEL` — for single-meeting queries
- `UNDERSTANDING_PROMPT_PROJECT_LEVEL` — for project-wide queries

LLM returns JSON:
```json
{
  "topic": "AI architecture",
  "intent_type": "topic_summary_query",
  "named_speaker": "Bhavneet Mhajan",
  "signal_filter": "question",
  "dimensions": {
    "has_topic": true,
    "is_cross_meeting": false,
    "needs_traces": false,
    "is_contribution": false
  }
}
```

### Phase C — Python Post-Processing (deterministic, no LLM)

```python
_fill_syntactic_dimensions()   # fills Python-only dims
  is_attribution  → regex: "who first raised", "which came first"
  is_yesno        → first word is auxiliary verb (is/are/was/did/has/...)
  is_count        → "how many", "total X", "number of"
  is_ranking      → "which came first/last/most"
  is_list_request → "what topics/items were discussed"
  has_temporal    → scope_meeting_ids is not empty

_python_verify_has_topic()     # upgrades LLM=False if topic field has real words
_python_infer_needs_summary()  # overrides needs_summary (more reliable than LLM)
_apply_routing()               # 3-layer routing → retrieval_mode + routing_label
_derive_output_format()        # prose / count / yesno / list
```

### QueryUnderstanding Output

```python
class QueryUnderstanding:
    topic:             str          # "AI module architecture"
    intent_type:       QueryIntent  # 12 possible values (see below)
    named_speaker:     str | None   # "Bhavneet Mhajan" (canonicalized)
    needs_summary:     bool         # fetch pre-written summary chunks
    temporal_focus:    str | None   # "cross_meeting"
    signal_filter:     str | None   # "commitment" | "decision" | "question"
    retrieval_mode:    str          # 8 possible values (see Section 8)
    output_format:     str          # "prose" | "count" | "yesno" | "list"
    dimensions:        QueryDimensions
    scope_meeting_ids: list[str]    # [] = project-wide, [id] = one meeting
    scope_type:        str          # "meeting" | "project"
```

### 12 Query Intent Values

```
general_query      → catch-all, BM25+dense hybrid
decision_query     → contains_decision signal
commitment_query   → contains_commitment signal
question_query     → contains_question signal
summary_query      → pre-written meeting summary chunks
speaker_query      → named speaker narrative
timeline_query     → cross-meeting chronological comparison
metadata_query     → structural facts (no embedding, no LLM)
analytical_query   → exact counts from DB metadata
topic_summary_query → per-meeting topic deep-dive
attribution_query  → "who first raised X?" (timeline variant)
contribution_query → speaker participation ranking
```

---

## 8. Step 2 — Retrieval (8 Modes)
<!-- mirror: app/services/retrieval/, app/services/answer/pipeline.py -->

### 8-Mode Dispatch

```
retrieval_mode      function called                    returns
─────────────────── ─────────────────────────────────── ──────────────────
summary             retrieve_summary_chunks()           list[Document]
timeline            retrieve_timeline_documents()       list[Document]
compound            compound_retrieve()                 list[Document]
signal_fetch        signal_fetch_retrieve()             list[Document]
topic_summary       topic_summary_retrieve()            list[Document]
analytical          analytical_retrieve()               dict  (no LLM counting)
contribution        contribution_retrieve()             dict  (no LLM)
metadata            handle_metadata_query()             dict  (short-circuit)
hybrid (default)    hybrid_retrieve()                   list[Document]
```

### How Each Mode Works

**`hybrid` (default)**
```
BM25 keyword search  (rank_bm25 — acronym-normalized, stopword-filtered)
  +
Dense vector search  (ChromaDB similarity, gemini-embedding-001)
  →
RRF merge (Reciprocal Rank Fusion) → top k_final chunks

hard_filters applied BEFORE search (speaker_name, contains_X signal)
Summary chunks excluded from BM25 corpus (avoids AI-written text polluting results)
```

**`compound`**
```
Two-pass speaker retrieval:
  Pass 1: fetch ALL chunks for named_speaker from ChromaDB (no vector search)
  Pass 2: run hybrid_retrieve() on those chunks + add signal_filter
  Fallback: if < 3 speaker chunks found → return broad hybrid results
Fixes: speaker queries where hybrid would rank by keyword density, not speaker identity
```

**`signal_fetch`**
```
Exhaustive DB fetch: ALL chunks matching (speaker + signal) via ChromaDB metadata filter
No BM25, no vector search — guarantees zero missed signal hits
Used when: named_speaker + signal_filter + (is_yesno OR is_list_request)
"Did Bhavneet ask any questions?" → fetch ALL Bhavneet question chunks
Trimmed to top 25 before LLM (signal_fetch_retrieve handles ordering)
```

**`topic_summary`**
```
Per-meeting hybrid_retrieve(topic, k_per_meeting) for EACH meeting in scope
Results merged chronologically by meeting_date
Single-meeting scope: inject meeting's summary chunk at [1] so LLM can
  correctly say "topic X was not discussed in this meeting"
```

**`timeline`**
```
Per-meeting dense search (no BM25) for each meeting
k_per_meeting chunks per meeting, merged chronologically
Used for: "how did X change between meetings"
```

**`summary`**
```
Direct ChromaDB metadata filter: is_meeting_summary=True
No vector search — fetches pre-written summary chunks by project_id (+ scope)
Chronological order preserved — no reranking
```

**`analytical`** → returns dict (not documents)
```
Pure ChromaDB metadata count — no vector search, no LLM counting
Returns: { total_chunks, signal_count, meeting_count, meetings, speakers }
Prevents LLM hallucinating counts from transcript text
```

**`contribution`** → returns dict (not documents)
```
Counts chunks per speaker, returns ranked list
{ ranked_speakers: [{speaker_name, chunk_count, meeting_count}] }
```

### BM25 Normalization
<!-- mirror: app/services/retrieval/hybrid.py -->

```python
_normalize_for_bm25(text):
  1. lowercase
  2. collapse abbreviations: C.E. → ce, P.M. → pm, C-E → ce, C. E. → ce
     Pattern: (?<!\w)[a-z](?:\s*[.\-\/]+\s*[a-z])+[.\-\/]*(?!\w)
  3. remove remaining punctuation
  4. collapse whitespace

_tokenize(text):
  normalize → split → filter stopwords (30+ words: what/did/say/about/...) → drop 1-char tokens
  Applied to BOTH corpus and query → always in sync
```

---

## 9. Step 3 — Re-ranking
<!-- mirror: app/services/retrieval/reranker.py -->

**Function:** `rerank_documents(query, documents, intent_hint, topic_hint, speaker_hint)`

**Model:** `gemini-2.5-flash-lite` (fast, cheap — 1 call per query)

**What it does:**
- Scores all retrieved chunks (up to ~25) against the true query intent
- Understands semantic causality: "who raised confusion" ≠ "who mentioned the topic"
- Promotes the chunk expressing the action (Rhythm raising confusion) over the chunk discussing the topic (Karan discussing it)
- Max preview per chunk: 450 chars (raised from 300 to prevent mid-sentence cutoffs)

**Skipped for:** `summary`, `topic_summary`, `signal_fetch`
- Summary/signal_fetch are already ordered correctly (chronological, not relevance-ranked)
- Reranking these would break the intended ordering

**Fallback:** If Gemini call fails → returns original order (no crash)

---

## 10. Step 3.5 — Context Expansion
<!-- mirror: app/services/answer/builder.py — expand_context() -->

**Function:** `expand_context(documents, n=EXPAND_TOP_N=5)`

**What it does:**
- For the top 5 re-ranked docs: fetches `prev_chunk_id` and `next_chunk_id` neighbors from ChromaDB
- Max 10 DB lookups per query (constant cost regardless of corpus size)
- Neighbor chunks tagged with `_position="before"` or `_position="after"` in metadata
- `build_context()` labels them `[CONTEXT — just before]` / `[CONTEXT — just after]`

**Why:**
- Reranker picks isolated chunks — neighbors give the LLM the conversational context
- Enables "After Neha explained X, Bhavneet responded Y" narratives in speaker queries

**Source handling:** Neighbor chunks are normally excluded from sources UNLESS the LLM cited them (i.e., their `[n]` number appears in the answer text). Cited neighbors always get a source card.

---

## 11. Step 4 — Context + Prompt Building
<!-- mirror: app/services/answer/builder.py -->

### `build_context(documents) → str`

```
For each document (numbered [1]...[N]):

  Primary chunk:   "[N] Meeting: {title} ({date})\nSpeaker: {name} ({role}) [{MM:SS}]\nContent: {text}"
  Neighbor before: "[N] [CONTEXT — just before] Meeting: {title} ({date})\nSpeaker: ..."
  Neighbor after:  "[N] [CONTEXT — just after]  Meeting: {title} ({date})\nSpeaker: ..."

ALL documents numbered sequentially [1]..[N] — neighbors included in numbering.
LLM uses these [N] numbers for inline citations.
```

### `build_prompt(query, context, template_key, output_format, scope_type) → str`

```
output_format prefix prepended:
  "count" → _COUNT_PREFIX    (answer MUST begin with exact count)
  "yesno" → _YESNO_PREFIX    (answer MUST begin with YES or NO)
  "list"  → _LIST_PREFIX     (answer MUST be a numbered/bulleted list)
  "prose" → no prefix

scope_type == "meeting" + template_key == "summary_query":
  → _MEETING_SCOPE_PREFIX prepended
  → instructs LLM to open with **[Meeting Title] — [YYYY-MM-DD]**

Template injected: ANSWER_PROMPT_TEMPLATES[template_key]
  .format(query=query, context=context)
```

### Context Window Limits

| Mode | Max chunks sent to LLM | Why |
|---|---|---|
| `topic_summary` | 15 | No reranker — all chunks relevant; more = better coverage |
| `signal_fetch` | 25 | Exhaustive fetch; trimming drops valid signal hits |
| All others | 10 | Reranker already picked best 10 |

---

## 12. Step 5 — LLM Answer Generation
<!-- mirror: app/clients/gemini_client.py -->

**Function:** `call_gemini(prompt) → str`

**Model:** `gemini-2.5-flash-lite`

**Retry logic:**
```python
3 attempts:
  attempt 1 → wait 2s on failure
  attempt 2 → wait 5s on failure
  attempt 3 → raise RuntimeError
Retryable: 503 Service Unavailable, connection errors
Non-retryable: 400 Bad Request, auth errors
```

**Two rules every template enforces:**

`_TIMESTAMP_RULE` — every speaker mention MUST include `(MM:SS)` from their chunk's Speaker line.
```
CORRECT: "Bhavneet Mhajan (06:04) explained that..."
WRONG:   "Bhavneet Mhajan explained that..."
```

`_CITATION_RULE` — cite source chunks inline with `[N]` at end of sentences.
```
CORRECT: "The budget was confirmed at $50k. [2]"
WRONG:   "[2] The budget was confirmed at $50k."
```

---

## 13. Source Extraction
<!-- mirror: app/services/answer/builder.py — extract_sources() -->

**Function:** `extract_sources(documents: list[Document], answer: str) → list[dict]`

### How sources are built

```
For i, doc in enumerate(documents, 1):  # same numbering as build_context()

  if doc._position and i NOT IN cited_nums:
      skip  # uncited neighbor = pure context padding

  → source entry:
    {
      chunk_num:       i,        ← matches [N] the LLM wrote in the answer
      meeting_title:   str,
      meeting_date:    str,
      speaker_name:    str,      ← "Meeting Summary" for is_meeting_summary=True
      timestamp:       "MM:SS",
      content_preview: first 200 chars,
      is_summary:      bool,
    }
```

**Key design:** `chunk_num` = exact `[N]` the LLM cited. In the Streamlit UI, clicking `[6]` scrolls to `div id="src-6"`.

**Neighbor chunks:** Normally excluded. Exception: if the LLM cited `[6]` (a neighbor), chunk 6 appears in sources because the LLM found it worth citing (e.g., a real question from a speaker whose chunk wasn't tagged as a primary signal hit).

**NO deduplication by speaker.** Each primary chunk gets its own source card. Multiple Bhavneet chunks = multiple Bhavneet source entries, each with their own timestamp.

### Streamlit citation linkage

```
LLM writes:     "Bhavneet explained X [6]"
_linkify_citations(answer, num_context_chunks=12):
  → [6] ≤ 12 → converts to <a href="#src-6">[6]</a>
render_sources():
  → source entry with chunk_num=6 renders <div id="src-6">
  → displays as "[6] Bhavneet Mhajan · Nolocode-AI-meeting · 2026-04-22 · ⏱ 06:04"
```

---

## 14. Chunk Schema (Full 5-Level)
<!-- mirror: app/services/transcript/chunking.py — create_chunks() -->

```python
{
  # Identity
  "chunk_id":              "01KM2DD6MXGSZ4F1QW0BNJE16N_1",  # meeting_id + "_" + chunk_index

  # Level 1 — Project scope
  "project_id":            "proj_nolocode_001",
  "project_name":          "Nolocode",
  "company_id":            "comp_001",
  "company_name":          "Nolocode",

  # Level 2 — Meeting
  "meeting_id":            "01KM2DD6MXGSZ4F1QW0BNJE16N",
  "meeting_title":         "Nolocode meeting with Ashpreet",
  "meeting_date":          "2026-05-08",               # ISO, from Fireflies dateString
  "meeting_number":        1,                           # 1-indexed within project
  "meeting_type":          "unknown",                   # placeholder

  # Level 3 — Speaker
  "speaker_name":          "Ngũmi Gituro",
  "speaker_id":            "ngumi_gituro",              # slugified, ASCII-safe
  "speaker_role":          "client",                   # from projects.json speakers map

  # Level 4 — Chunk position
  "chunk_index":           1,
  "chunk_type":            "utterance",                 # "utterance" | "summary"
  "is_meeting_summary":    False,                       # True for the 1 summary chunk per meeting

  # Tier 2a — Timing (seconds from recording start; None if API didn't provide)
  "start_time":            14.96,
  "end_time":              33.26,

  # Tier 2a — Adjacency links
  "prev_chunk_id":         None,                        # first chunk
  "next_chunk_id":         "01KM2DD6MXGSZ4F1QW0BNJE16N_2",

  # Level 5 — Content signals (5 types, regex at ingest time)
  "contains_decision":     False,
  "contains_commitment":   True,
  "contains_question":     False,
  "contains_document_share": False,
  "contains_open_issue":   False,
  "sentiment":             "neutral",                   # placeholder

  # Content
  "text":                  "We should finalize...",
  "text_length":           162,
}
```

---

## 15. Content Signals (5 Types)
<!-- mirror: app/services/transcript/chunking.py — _detect_signals() -->

All signals detected at **ingest time** using **regex only** (zero LLM cost at ingestion).

| Signal | Field | Trigger examples |
|---|---|---|
| Decision | `contains_decision` | "we decided", "confirmed", "going with", "agreed to", "final decision" |
| Commitment | `contains_commitment` | "I will", "I'll", "action item", "by Friday", "will do", "responsible for" |
| Question | `contains_question` | Ends with `?` OR starts with question word (what/how/why/when/who/...) |
| Document share | `contains_document_share` | "shared doc", "spreadsheet", "file", "link", "attached", "sent over" |
| Open issue | `contains_open_issue` | "unresolved", "concern", "problem", "discrepancy", "flagged", "issue" |

**At query time:** `signal_filter` from `QueryUnderstanding` maps to:
- `"question"` → `contains_question=True` hard filter
- `"commitment"` → `contains_commitment=True` hard filter
- `"decision"` → `contains_decision=True` hard filter

**Note:** Decision signal intentionally NOT used as hard filter in `compound_retrieve()` — decision signals are weak hints, semantic search is more reliable for finding actual decisions.

---

## 16. Routing Decision Tree
<!-- mirror: app/services/query_intent.py — _structural_route, _shape_route, _content_route -->

```
is_metadata_query() ?  ────────────────────────────────► metadata short-circuit
  YES → handle_metadata_query() (no LLM, no embedding)

Layer 1 — Structural (no vector search needed)
  _METADATA_RE match          ──────────────────────────► mode=metadata
  is_contribution OR
  _CONTRIBUTION_RE match      ──────────────────────────► mode=contribution

Layer 2 — Shape (answer form overrides content)
  is_attribution              ──────────────────────────► mode=timeline (attribution template)
  is_count
    + has_temporal            ──────────────────────────► mode=analytical (scoped_count)
    + signal_filter (no topic)──────────────────────────► mode=analytical (signal_count)
    + named_speaker           ──────────────────────────► mode=analytical (speaker_count)
    + has_topic               ──────────────────────────► mode=topic_summary (semantic_count)
    fallback                  ──────────────────────────► mode=analytical (any_count)
  is_ranking (no speaker)     ──────────────────────────► mode=hybrid (scoped_ranking)

Layer 3 — Content (always returns)
  named_speaker
    + signal_filter + (yesno OR list_request) ─────────► mode=signal_fetch (exhaustive)
    otherwise                 ──────────────────────────► mode=compound
  has_topic
    + signal_filter           ──────────────────────────► mode=hybrid (flag enforced)
    + has_temporal            ──────────────────────────► mode=topic_summary (scoped)
    + is_cross_meeting        ──────────────────────────► mode=topic_summary (cross-meeting)
    alone                     ──────────────────────────► mode=topic_summary
  needs_summary               ──────────────────────────► mode=summary
  is_list_request             ──────────────────────────► mode=summary
  is_cross_meeting            ──────────────────────────► mode=timeline
  has_temporal + _CONTENT_RE  ──────────────────────────► mode=summary (safety net)
  default                     ──────────────────────────► mode=hybrid
```

---

## 17. Prompt Templates (11 Types)
<!-- mirror: app/services/prompts.py — ANSWER_PROMPT_TEMPLATES + select_template_key() -->

### Template Selection — `select_template_key(understanding)`

```python
compound      → speaker_query       (named-speaker narrative)
analytical    → analytical_query    (format pre-computed numbers)
contribution  → contribution_query  (ranked speaker table)
topic_summary → topic_summary_query (per-topic deep-dive)
summary       → summary_query       (meeting overview)
timeline + is_attribution → attribution_query   (temporal origin)
timeline      → timeline_query      (chronological evolution)
signal_fetch (decision)   → decision_query
signal_fetch (commitment) → commitment_query
signal_fetch (question)   → question_query
hybrid (default)          → general_query
```

### What Each Template Instructs

| Template | Key instruction |
|---|---|
| `decision_query` | Identify specific decisions, who made them, when. Only explicitly confirmed decisions. |
| `commitment_query` | Extract action items: who committed, what they'll do, deadline if mentioned. |
| `question_query` | List each question: who asked, which meeting, was it answered or unresolved. |
| `summary_query` | "What topics?" → numbered list: **Bold Topic** + natural attribution + outcome. NEVER write "Raised by: Meeting Summary". |
| `speaker_query` | Speaker INTENT + narrative thread. Before/after context used naturally (never copy the `[CONTEXT]` labels). |
| `timeline_query` | Compare chronologically. Highlight what changed between meetings. |
| `attribution_query` | Pinpoint first mention. Distinguish originator from later references. Chronological order. |
| `topic_summary_query` | If topic absent → state clearly + describe what meeting DID cover. If present → numbered subtopics with natural attribution. |
| `analytical_query` | Format pre-computed numbers ONLY. Never invent or alter any count. |
| `contribution_query` | Numbered ranked list. Each speaker: name, segment count, meetings. One sentence on what they drove. |
| `general_query` | Best answer evidence supports. Commit to most-supported conclusion. Note confidence inline if partial. |

### Two Rules Applied to ALL Free-Text Templates

```
_TIMESTAMP_RULE (mandatory):
  Every speaker mention MUST include their (MM:SS) timestamp.
  "Bhavneet Mhajan (06:04) explained..."

_CITATION_RULE:
  Cite source chunks inline [N] at end of sentences.
  Only traceable claims. After punctuation. Never cite neighbor context chunks.
```

### Forbidden Patterns (enforced in templates)

- ❌ `"Raised by: Meeting Summary"` — forbidden
- ❌ `"Raised by: (unknown)"` — forbidden
- ❌ `"[CONTEXT — just before]"` in the answer — forbidden
- ❌ Invented timestamps — forbidden

---

## 18. Adaptive k Configuration
<!-- mirror: app/services/retrieval/config.py -->

```
Mode          Scope       k_dense  k_bm25  k_final  k_per_meeting
─────────────────────────────────────────────────────────────────
compound      project     40       40      25       —
compound      1 meeting   20       20      15       —
compound      2-5 meet.   30       30      20       —
  (+ signal_filter: k_final × 0.7, min 10)

topic_summary project     —        —       —        6
topic_summary 1 meeting   —        —       —        15
topic_summary 2-3 meet.   —        —       —        10
topic_summary 4-6 meet.   —        —       —        8
topic_summary 7+ meet.    —        —       —        6

timeline      project     —        —       —        5
timeline      1 meeting   —        —       —        8
timeline      2-3 meet.   —        —       —        6
timeline      4+ meet.    —        —       —        5

hybrid        project     25       25      25       —
hybrid        1 meeting   20       20      20       —
```

**Context budget:** Pipeline trims to top-10 after rerank+expand (topic_summary=15, signal_fetch=25).

---

## 19. Streamlit UI
<!-- mirror: streamlit_app.py -->

### Components

**Sidebar:**
- Project selector dropdown (enforces scope — clears chat on switch)
- 3-metric bar: Meetings / Speakers / Chunks
- Meeting list with dates
- Speaker list with role icons (🔴 client / 🟡 PM / 🔵 developer)
- "What can I ask?" query guide expander
- Clear Chat + Refresh buttons

**Chat window:**
- `st.chat_message` for user + assistant
- Intent badge (colored pill HTML): 🔵 Decision / 🟠 Action Item / 🟢 Summary / 🟣 Questions / 🔷 Speaker / 🟡 Timeline / 📊 Analytics / ⚫ General
- Answer rendered via `_linkify_citations()` (see below)
- Source panel expander (📎 N sources)

### `_linkify_citations(answer, num_context_chunks)`

```python
1. Convert [N] citation markers → <a href="#src-N"> links
   (only when N ≤ num_context_chunks — total context window size, NOT num_sources)
2. Convert "- item" and "* item" bullet lines → <ul><li> HTML
   (both dash and asterisk bullets — LLM uses both styles)
3. Convert remaining \n → <br>
   (prevents numbered items and sub-bullets collapsing into one paragraph)
```

### Source Cards in `render_sources(sources)`

```
[N] 📋 Meeting Summary · 📅 Nolocode-meeting · 2026-05-07
[N] Bhavneet Mhajan · 📅 Nolocode-AI-meeting · 2026-04-22 · ⏱ 06:04
❝ first 200 chars of chunk content...
```

Each card has `div id="src-N"` where N = `chunk_num` (the context [N] the LLM cited).

---

## 20. Test Infrastructure
<!-- mirror: app/tests/ -->

### Query Banks

| File | Queries | What's tested |
|---|---|---|
| `easy.json` | 21 | 7 easy intents, regex-triggerable keywords |
| `medium.json` | 20 | 7 routing rules, paraphrased, meeting-scoped, speaker-detected |
| `hard.json` | 0 | Not yet written — edge cases, contradictions, negative-space |

Each query schema:
```json
{
  "id": "ml_001",
  "query": "...",
  "project_id": "proj_nolocode_001",
  "expected_intent": "topic_summary_query",
  "expected_mode": "topic_summary",
  "tags": ["topic", "scoped"],
  "notes": "...",
  "evaluation_hints": "..."
}
```

### Test Runner — `test_runner.py`

```bash
uv run python -m app.tests.test_runner --project-id proj_nolocode_001 --difficulty easy
uv run python -m app.tests.test_runner --project-id proj_nolocode_001 --difficulty medium
uv run python -m app.tests.test_runner --ids ml_001,ml_005 --tags decision
```

- Calls `answer_question()` directly (no HTTP)
- Pass criteria: `intent_match=True` AND `has_answer=True` (not a "not found" response)
- When `expected_mode` is set: `mode_match` overrides `intent_match` for pass/fail
- Saves per-query JSON + `run_metadata.json` in timestamped folder

### Current Baseline (2026-05-25)

```
test_retrieval.py   46/46  PASS  (no LLM — pure retrieval assertions)
easy.json           21/21  PASS  avg 9.0/10
medium.json         20/20  PASS  avg 8.8/10
```

### Remaining Sprint 4 Work

- `run_tests.py` — one master command: query_generator → test_runner → report_generator → open summary.md
- `hard.json` — 10-15 hard queries (cross-meeting, contradiction, negative-space)
- `compare.py` — regression tracker: diff two run folders (what improved / regressed / stayed same)

---

## 21. Config & Environment
<!-- mirror: app/config.py, projects.json -->

### `.env` required keys

```
GEMINI_API_KEY=...          Required for all LLM + embedding calls
FIREFLIES_API_KEY=...       Required for live webhook ingestion
DEVELOPMENT_MODE=true       Use CONSTANT_TRANSCRIPT instead of live API
```

### `projects.json` structure

```json
{
  "proj_nolocode_001": {
    "project_name": "Nolocode",
    "company_id": "comp_001",
    "company_name": "Nolocode",
    "meeting_ids": ["01KM2DD6...", ...],   // 10 meetings currently
    "speakers": {
      "Ngũmi Gituro": "client",
      "Project Manager SFS": "project_manager",
      "Karan Middha": "developer",
      "Bhavneet Mhajan": "client",
      "Rhythm jalhotra": "developer",
      "Neha": "developer",
      "Ashpreet Singh": "client",
      "Nolocode AI": "client",
      "Harsh Vardhan Dixit": "developer"
    }
  }
}
```

**To add a new meeting:** Add its `meeting_id` to `meeting_ids`. Pipeline aborts cleanly if an incoming webhook meeting_id is not registered here.

**To add a new project:** Add a new top-level key. Copy the structure above.

### How to run

```bash
# Start the API server
uv run uvicorn main:app --reload --port 8000

# Start the Streamlit UI
uv run streamlit run streamlit_app.py

# Ingest a transcript (dev mode)
# Set DEVELOPMENT_MODE=true in .env, then POST to /webhook/fireflies with {}

# Run tests
uv run python -m app.tests.test_runner --project-id proj_nolocode_001 --difficulty easy
uv run python -m app.tests.test_runner --project-id proj_nolocode_001 --difficulty medium
uv run python app/tests/test_retrieval.py
```

---

## 22. Known Gaps & Planned Work

### Sprint 4 remaining (immediate)
- [ ] `run_tests.py` master runner
- [ ] `hard.json` query bank (10-15 queries)
- [ ] `compare.py` regression tracker

### Known accuracy gaps (need design work)
| Gap | Scenario | Why hard |
|---|---|---|
| S10 | "Which topic was most important?" | "Importance" is subjective — no signal |
| S13 | "Can we answer Bhavneet's questions?" | Needs Q&A chunk pairing (question → answer) |
| S28 | "Which unresolved issue was discussed last?" | No `is_resolved` flag in schema |

### Post-POC production gaps
| Gap | Priority | Blocker for |
|---|---|---|
| **Type 3 Miscommunication Detection** | P1 | Biggest differentiator vs Otter.AI |
| **D1 Auto-registration of new meeting IDs** | P1 | Production pipeline (currently manual `projects.json`) |
| **More projects + meetings** | P2 | Scale test — currently 1 project, 10 meetings |
| **Role-based speaker queries** | P2 | "What did the client say?" (full design in `FUTURE_SCOPE.md`) |
| **Confidence scoring** | P3 | Flag low-confidence answers |
| **PM usability test** | P3 | Real PM feedback |

### Sprint 5 — Agentic Tool Calling (planned)
Four tools: `search_transcripts`, `list_meetings`, `list_speakers`, `count_chunks_matching`
Enables compound analytical queries the routing rules can't pre-determine.
Prerequisite: Sprint 4 complete so regressions are caught.

---

## How to Keep This File Updated

When you change any of the following, update the matching section in this file:

| Changed file/area | Update section |
|---|---|
| `app/services/answer/pipeline.py` | §6, §7, §8, §9, §10, §11 |
| `app/services/query_intent.py` | §7, §16 |
| `app/services/prompts.py` | §7, §17 |
| `app/services/retrieval/*.py` | §8, §9, §18 |
| `app/services/retrieval/config.py` | §18 |
| `app/services/answer/builder.py` | §11, §13 |
| `app/services/transcript/chunking.py` | §5, §14, §15 |
| `app/services/transcript/normalize.py` | §5 |
| `streamlit_app.py` | §19 |
| `projects.json` | §21 |
| `app/tests/` | §20 |
| `app/clients/gemini_client.py` | §2, §12 |
| Any new file added | §3 (File Map) |
