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
23. [Production Agent Pipeline (LangGraph)](#23-production-agent-pipeline-langgraph)
24. [Production — Graph Structure](#24-production--graph-structure)
25. [Production — AgentState Fields](#25-production--agentstate-fields)
26. [Production — query_scope_node](#26-production--query_scope_node)
27. [Production — 5 Tools](#27-production--5-tools)
28. [Production — System Prompt Design](#28-production--system-prompt-design)
29. [Production — service.py Entry Point](#29-production--servicepy-entry-point)

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
<!-- mirror: all files in app/, production/ -->

```
fireflies_transcript_project/
│
├── main.py                          FastAPI app — /webhook/fireflies + /query endpoints
├── streamlit_app.py                 Streamlit chat UI
├── projects.json                    Project config (meeting_ids, speaker roles)
├── ARCHITECTURE.md                  ← this file
│
├── production/                      LangGraph agent pipeline (Sprint 5)
│   ├── __init__.py                  Re-exports get_graph, reset_doc_accumulator, get_accumulated_docs
│   ├── service.py                   Public entry — answer_query(query, project_id) → dict
│   ├── ARCHITECTURE.md              Production-specific architecture (agent flow, state, tools)
│   ├── PLAN.md                      30 PM query scenarios mapped to tool flows + 6 gap analysis
│   │
│   ├── agent/
│   │   ├── __init__.py              Re-exports get_graph, reset/get_accumulated_docs
│   │   ├── state.py                 AgentState TypedDict — 6 fields (messages, project_id, scope_*)
│   │   ├── graph.py                 LangGraph graph — START→query_scope→agent↔tools→END
│   │   ├── query_scope.py           Deterministic scope resolver — no LLM, regex only
│   │   ├── tools.py                 5 tools: search_transcripts, get_meeting_summaries,
│   │   │                            list_meetings, list_speakers, count_signal_chunks
│   │   └── prompts.py               System prompt — TOOLS section + QUERY PATTERNS section
│   │
│   └── tests/
│       └── test_query_scope.py      30 assertions for scope node (Level 1 + 2 + 3 with --full)
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

### Sprint 5 — Production Agent Pipeline (LangGraph) ✅ IMPLEMENTED
See Section 23–29 for the full architecture.
Five tools: `search_transcripts`, `get_meeting_summaries`, `list_meetings`, `list_speakers`, `count_signal_chunks`
Entry point: `production/service.py → answer_query(query, project_id)`
Handles all 30 PM query scenarios including cross-meeting synthesis, multi-hop Q&A, and chronological comparison.

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
| `production/agent/state.py` | §25 |
| `production/agent/graph.py` | §24 |
| `production/agent/query_scope.py` | §26 |
| `production/agent/tools.py` | §27 |
| `production/agent/prompts.py` | §28 |
| `production/service.py` | §29 |
| Any new file added | §3 (File Map) |

---

## 23. Production Agent Pipeline (LangGraph)
<!-- mirror: production/ -->

### What it is and how it differs from Pipeline B

The **deterministic pipeline** (§6–§12) uses a fixed routing tree: classify query → pick retrieval mode → retrieve → rerank → answer. It works well for known query patterns but cannot handle novel or compound questions.

The **production agent pipeline** (`production/`) uses a LangGraph **ReAct loop**: the LLM decides which tools to call, in what order, with what parameters — then synthesizes the final answer from all tool results. No fixed routing.

| Dimension | Deterministic Pipeline (§6) | Production Agent (§23) |
|---|---|---|
| Routing | Fixed Python rules | LLM decides per query |
| Retrieval | 1 fixed call per query | 1–6 tool calls in sequence |
| Multi-hop | Not supported | Native (agent loops) |
| Novel queries | Falls back to hybrid | Handles naturally |
| LLM calls per query | 2–3 | 1–4 (per tool loop iteration) |
| Latency | ~3–5 s | ~5–12 s |
| Entry point | `answer_question(query, project_id)` | `answer_query(query, project_id)` |

**Classification = Retrieval:** In the production agent, the LLM's tool selection IS the classification. The system prompt and tool docstrings are the primary accuracy lever — clearer tool guidance = more accurate tool selection = better retrieval.

> **Most important tuning file:** `production/agent/prompts.py`
> When accuracy is poor on a query type, fix the system prompt or tool docstring BEFORE changing any retrieval logic.

---

## 24. Production — Graph Structure
<!-- mirror: production/agent/graph.py -->

```
START
  │
  ▼
┌─────────────┐
│ query_scope │  Deterministic. Runs ONCE. Resolves meeting scope from
└─────────────┘  query using regex. Writes 4 scope fields into state.
  │              No LLM call. ~50ms. Zero API cost.
  │
  ▼
┌───────┐   has tool_calls   ┌───────┐
│ agent │ ─────────────────► │ tools │
│ (LLM) │                    └───────┘
└───────┘ ◄──────────────────────┘
  │         ToolMessages (loop)
  │ no tool_calls (or MAX_ITERATIONS reached)
  ▼
 END
```

**Model:** `gemini-2.5-flash` (temperature=0)
**Max iterations:** 6 tool-call rounds before forcing END (prevents infinite loops)
**Graph singleton:** `get_graph()` uses `@lru_cache(maxsize=1)` — LLM + graph built once per process

### Node responsibilities

| Node | Type | Cost | What it does |
|---|---|---|---|
| `query_scope` | Python function | ~50ms, 0 API calls | Regex scope detection, sets 4 state fields |
| `agent` (call_llm) | LLM call | ~1–3s per iteration | Decides tool calls or writes final answer |
| `tools` (ToolNode) | Tool execution | ~50–200ms per call | Runs tools, injects state via InjectedState |

### Security: project_id and scope never come from the LLM

- `project_id` — set once in `service.py` initial_state, read by all tools via `InjectedState`. LLM never sees or supplies it.
- `scope_where` — resolved deterministically by `query_scope_node`. Tools pass it to `hybrid_retrieve` as `date_where`. LLM never controls which meetings are searched.

### Scope injection into system message

Before each LLM call, `call_llm()` appends a scope note to the system prompt:
```
Meeting scope → "SCOPE ALREADY RESOLVED: This query is limited to 'Nolocode Meeting #10' (2026-05-07).
                 Do NOT call list_meetings — scope is already applied."
Date range   → "SCOPE ALREADY RESOLVED: A date-range filter is active."
Project-wide → (no note appended)
```
This prevents the LLM from wasting a tool call on `list_meetings` when scope is already known.

---

## 25. Production — AgentState Fields
<!-- mirror: production/agent/state.py -->

```python
class AgentState(TypedDict):
    messages:      Annotated[list[AnyMessage], add_messages]  # full conversation thread
    project_id:    str           # immutable — set once at graph entry
    scope_where:   Optional[dict]     # ChromaDB where-clause → hybrid_retrieve date_where
    scope_ids:     Optional[List[str]]# flat meeting ID list → summaries filter
    scope_type:    str                # "project" | "meeting" | "date_range"
    recommended_k: int                # min k for search_transcripts (scope-based)
```

| Field | Set by | Read by | Notes |
|---|---|---|---|
| `messages` | all nodes | agent node | `add_messages` reducer appends each step |
| `project_id` | `service.py` | all tools via InjectedState | Never changes |
| `scope_where` | `query_scope_node` | `search_transcripts` | Passed as `date_where` to `hybrid_retrieve` |
| `scope_ids` | `query_scope_node` | `get_meeting_summaries`, `list_speakers`, `count_signal_chunks` | Flat ID list for post-fetch filter |
| `scope_type` | `query_scope_node` | `call_llm`, `count_signal_chunks` | Drives scope note injection |
| `recommended_k` | `query_scope_node` | `search_transcripts` | `effective_k = max(llm_k, recommended_k)` |

---

## 26. Production — query_scope_node
<!-- mirror: production/agent/query_scope.py -->

**Function:** `query_scope_node(state) → dict`  
**Reads:** first `HumanMessage` from `state["messages"]`  
**Writes:** `scope_where`, `scope_ids`, `scope_type`, `recommended_k`  
**Does NOT touch:** `messages`

### How scope is detected

Calls `parse_meeting_scope(query, project_id)` from `app/services/answer/scope.py` (same regex the deterministic pipeline uses). Converts the ChromaDB clause into simpler state fields:

```python
scope_where = parse_meeting_scope(query, project_id)   # None → project-wide
scope_ids   = _extract_scope_ids(scope_where)          # flat list or None

# scope_where = {"meeting_id": {"$eq": M10}}  → scope_ids = [M10],  scope_type = "meeting"
# scope_where = {"meeting_id": {"$in": [M9, M10]}}  → scope_ids = [M9, M10], scope_type = "meeting"
# scope_where = {"meeting_date": {"$gte": "2026-04-25"}}  → scope_ids = None, scope_type = "date_range"
# scope_where = None  → scope_ids = None, scope_type = "project"
```

### Scope phrases detected (examples)

```
"last meeting" / "previous meeting" / "most recent meeting" → latest meeting ID
"first meeting" / "earliest meeting" → oldest meeting ID
"the second meeting" / "the third meeting" → Nth oldest by date
"last 2 meetings" / "previous 3 meetings" → $in list of N most recent IDs
"March 19th" / "April 22nd meeting" → date lookup → matching meeting_id
"last 30 days" / "past 2 weeks" → {"meeting_date": {"$gte": cutoff}} clause
No phrase → None (project-wide, all meetings)
```

### recommended_k formula

```
scope_type = "project"        → recommended_k = 25   (project-wide, 1,659 chunks)
scope_type = "meeting", 1 mtg → recommended_k = 15   (~150 chunks per meeting)
scope_type = "meeting", 2 mtg → recommended_k = 20
scope_type = "meeting", 3+    → recommended_k = 25
scope_type = "date_range"     → recommended_k = 20   (unknown size)
```

`search_transcripts` enforces: `effective_k = min(max(llm_k, recommended_k), 25)`.  
If the LLM asks for k=15 but scope is project-wide (recommended=25), the tool uses 25.

---

## 27. Production — 5 Tools
<!-- mirror: production/agent/tools.py -->

All 5 tools enforce `project_id` via `InjectedState` — the LLM never supplies it.
Scope fields (`scope_where`, `scope_ids`, `scope_type`, `recommended_k`) are also injected from state.

### Tool table

| Tool | Data accessed | Returns | Primary use |
|---|---|---|---|
| `search_transcripts` | Chunk content via BM25+dense hybrid | Matching chunks (speaker, time, meeting, text) | Main workhorse — any "what was said" question |
| `get_meeting_summaries` | Pre-built summary chunks (1 per meeting) | 1 paragraph per meeting | Meeting overview, agenda, what happened |
| `list_meetings` | Meeting metadata only (no content) | Title + date + number per meeting | Meeting count, date order |
| `list_speakers` | Speaker metadata (scope-aware) | Name + role + chunk count, sorted | Attendance, who spoke most |
| `count_signal_chunks` | Signal flags only (metadata scan) | Exact integer count | "How many commitments / questions?" |

### Tool 1: search_transcripts (the main workhorse)

```
Parameters LLM supplies:
  query         — natural language search query (be specific: topic + keywords)
  k             — number of chunks (default 15, max 25; system auto-adjusts)
  speaker_name  — restrict to one speaker's chunks only
  signal_filter — one of: 'decision' | 'commitment' | 'question' | 'open_issue' | 'document_share'

Parameters injected from state (LLM never sets these):
  project_id    — always enforced
  scope_where   — passed to hybrid_retrieve as date_where
  recommended_k — effective_k = min(max(k, recommended_k), 25)

Output format per chunk:
  [N] Speaker Name (MM:SS) — Meeting Title (YYYY-MM-DD)
      First 400 chars of chunk text
```

**Signal map** (shared with `count_signal_chunks`):
```python
_SIGNAL_MAP = {
    "decision":       "contains_decision",
    "commitment":     "contains_commitment",
    "question":       "contains_question",
    "open_issue":     "contains_open_issue",
    "document_share": "contains_document_share",
}
```

### Tool 4: list_speakers (scope-aware)

When `scope_ids` is set, the ChromaDB query is restricted to those meetings only.  
Output sorted by chunk count descending — LLM sees "who spoke most" directly.

```
3 speakers (scoped to 1 meeting(s)):

  - Harsh Vardhan  [Developer]  (47 chunks)
  - Bhavneet Mahajan  [Client]  (31 chunks)
  - Simarjot Kaur  [Project Manager]  (22 chunks)
```

### Tool 5: count_signal_chunks (exact metadata count)

Pure ChromaDB metadata scan — zero embedding calls, ~50ms.  
Scope applied automatically: meeting IDs or date_range clause added to filter.

```python
# Example internal filter:
{"$and": [
    {"project_id":          {"$eq": project_id}},
    {"contains_commitment": {"$eq": True}},
    {"is_meeting_summary":  {"$ne": True}},
    {"meeting_id":          {"$eq": scope_ids[0]}},   # if scoped
]}
# Returns: len(results["ids"]) — no content fetched
```

**When to use count_signal_chunks vs search_transcripts for counts:**

| Query type | Tool | Why |
|---|---|---|
| "How many commitments?" | `count_signal_chunks` | No k limit, exact metadata count |
| "How many questions did Bhavneet raise?" | `count_signal_chunks(speaker_name=...)` | Exact per-speaker count |
| "How many questions about AI architecture?" | `search_transcripts(query=..., signal_filter='question')` | Topic filter needs semantic search |
| "How many distinct AI approaches discussed?" | `search_transcripts(query=..., k=25)` | Semantic dedup, LLM counts unique items |

### Thread-safe doc accumulator

`search_transcripts` and `get_meeting_summaries` append retrieved docs to `_accumulated_docs` (module-level list).  
`service.py` calls `reset_doc_accumulator()` before each request and `get_accumulated_docs()` after `graph.invoke()` to build the sources panel.

Uses **in-place mutations** (`.clear()` / `.extend()`) — NOT reassignment (`= []`). This is required because `ToolNode` runs tools in threads: reassignment only updates the thread's local reference, not the shared list object.

---

## 28. Production — System Prompt Design
<!-- mirror: production/agent/prompts.py -->

**File:** `production/agent/prompts.py → SYSTEM_PROMPT`

The system prompt has 3 sections:

### Section 1 — TOOLS

One block per tool. Each block specifies exactly when to use the tool and what parameters to set:

```
search_transcripts
  For: specific topics, technical decisions, what someone said, blockers,
       action items, questions raised, documents shared, any discussion content.
  signal_filter options:
    'decision' | 'commitment' | 'question' | 'open_issue' | 'document_share'
  speaker_name: scope to one person's contributions.
  Call MULTIPLE TIMES with different queries/filters for complex questions.
  If signal_filter gives 0 results, retry WITHOUT the filter.
  k: system auto-adjusts based on scope. Override only when needed.

count_signal_chunks
  For: counting how many times a signal type appears (no topic filter needed).
  ⚠️ Signals are regex-detected — report as "about N" not "exactly N".

list_speakers
  Output includes chunk count per speaker sorted highest first.
  When scope is active, shows only speakers from that meeting.

list_meetings
  Do NOT call this to find out which meeting is "last" — that is already resolved.
```

### Section 2 — QUERY PATTERNS

Explicit step-by-step guidance for specific query types. Prevents the LLM from inventing approaches:

| Pattern | Guidance |
|---|---|
| COUNT (metadata) | Use `count_signal_chunks`, report as "about N" |
| COUNT (semantic) | Use `search_transcripts` high-k, count from header |
| 0 results | Retry in 4 steps: drop signal → drop speaker → simplify → get summaries |
| YES/NO | Search first, then answer Yes/No with evidence |
| DOCUMENTS | `signal_filter='document_share'` + include sharer + timestamp |
| SPEAKER CONTRIBUTION | Always set `speaker_name`, add `signal_filter` if type specified |
| CHRONOLOGICAL | Two separate searches, compare `meeting_date` + `start_time` from results |
| MULTI-HOP Q&A | Step 1: find questions; Step 2: per question, search for answer |
| TWO-SPEAKER | Search each speaker separately, present both, then synthesize |
| WHO SPOKE MOST | Call `list_speakers()` — chunk counts already sorted |

### Section 3 — ANSWER FORMAT RULES

```
1. ATTRIBUTION — always name speaker + meeting
2. TIMESTAMPS — include (MM:SS) when speaker is mentioned
3. ATTRIBUTION VERBS — raised / explained / confirmed / committed to / flagged
4. NEGATIVE CASE — one sentence "not discussed" + 2–3 sentences what WAS covered
5. STRUCTURED TOPICS — **N. Bold Topic** + paragraph + sub-bullets
6. ACTION ITEMS — list: "Owner Name: what they committed to (meeting, date)"
7. DECISIONS — "Decision: [what] — agreed by [who] in [meeting / date]"
8. SIGNAL COUNTS — "About N commitments" never "Exactly N"
9. No invented content
10. No "Raised by: Meeting Summary" or "Unknown speaker"
```

---

## 29. Production — service.py Entry Point
<!-- mirror: production/service.py -->

**Function:** `answer_query(query: str, project_id: str) → dict`

**Returns:**
```python
{
    "answer":             str,         # LLM-generated answer
    "sources":            list[dict],  # speaker/meeting-level source entries (deduped)
    "tool_calls":         list[dict],  # [{tool, args}, ...] trace (project_id stripped)
    "intent":             "production_agent",
    "notice":             None,
    "num_context_chunks": int,         # total docs retrieved across all tool calls
    "model":              "gemini-2.5-flash (agent)",
    "error":              str | None,
}
```

**Initial state built in service.py:**
```python
initial_state = {
    "messages":    [HumanMessage(content=query)],
    "project_id":  project_id,
    "scope_where": None,       # filled by query_scope_node
    "scope_ids":   None,       # filled by query_scope_node
    "scope_type":  "project",  # filled by query_scope_node (default = all meetings)
    "recommended_k": 15,       # overridden by query_scope_node
}
```

**Source deduplication:** `_build_sources()` deduplicates by `(speaker_name, meeting_id)`. Multiple chunks from the same speaker in the same meeting produce one source card — not one per chunk.

**Content format handling:** Gemini 2.5 extended thinking returns content as a list of blocks. `answer_query()` handles both plain string and list-of-blocks formats:
```python
if isinstance(raw, list):
    text_parts = [b["text"] for b in raw if b.get("type") == "text"]
    answer = "\n".join(text_parts).strip()
```

**How to run:**
```bash
python -c "
from production.service import answer_query
r = answer_query('What did Bhavneet commit to in the last meeting?', 'proj_nolocode_001')
print(r['answer'][:300])
print('tools:', [t['tool'] for t in r['tool_calls']])
"
```

**Test the scope node (no LLM needed):**
```bash
python production/tests/test_query_scope.py
# Expected: 30/30 passed

# With full pipeline (~20s, needs GEMINI_API_KEY):
python production/tests/test_query_scope.py --full
```
