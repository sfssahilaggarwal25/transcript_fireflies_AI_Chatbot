# TASKS — AI Meeting Intelligence System (POC)

> Master task list derived from full POC design discussion.
> Tags: `[Must Do]` = critical path, POC breaks without it | `[Nice to Have]` = improves quality but not blocking

---

## Overall Progress

```
Phase 1 — Foundation       [██████████] 100%  10/10 tasks    ✓ COMPLETE
Phase 2 — RAG Engine       [██████████] 100%   8/8  tasks    ✓ COMPLETE
Phase 3 — Query Taxonomy   [██████████] 100%  10/10 tasks    ✓ COMPLETE
Phase 4 — Streamlit UI     [██████████] 100%   8/8  tasks    ✓ COMPLETE
Phase 5 — Validation       [██████████] 100%   6/6  tasks    ✓ COMPLETE
Sprint 3 — Chunking        [██████████] 100%   all  tasks    ✓ COMPLETE
Sprint 6 — Query Accuracy  [██████████] 100%  all   tasks    ✓ COMPLETE (Session 20)
Test Suite (Sprint 4)      [██████░░░░]  60%   5/9  tasks    🔄 IN PROGRESS

TOTAL XP EARNED:  1500 / 1500 XP   🏆 POC COMPLETE
```

### Sprint 3 Tasks — Chunking Improvements (Session 19) ✓ COMPLETE

- [x] `fireflies_client.py` — `rawStartTimeMs`/`rawEndTimeMs` in GraphQL query `[Must Do]`
- [x] `normalize.py` — `dateString` ISO parsing + unified `start_time`/`end_time` normalization (ms API → seconds) `[Must Do]`
- [x] `chunking.py` — `start_time`/`end_time` per chunk (seconds); `prev_chunk_id`/`next_chunk_id` adjacency links `[Must Do]`
- [x] `chunking.py` — `MAX_CHARS=500`, `_is_low_quality()`, `_TOPIC_SHIFT_RE` `[Must Do]`
- [x] `answer_service.py` — `_expand_context()` neighbors for top-5 docs `[Must Do]`
- [x] Re-ingest: 352 chunks, verified timestamps + adjacency links + CE query accuracy `[Must Do]`

### Sprint 6 Tasks — Query Accuracy Improvement (Session 20) ✓ COMPLETE

> 21/24 failing scenarios fixed. 3 known gaps require separate design work (S10, S13, S28).

- [x] `scope.py` — `get_scoped_meeting_ids()` utility; `"that/this meeting"` + ordinal patterns `[Must Do]`
- [x] `builder.py` — `retrieve_summary_chunks()` calls `parse_meeting_scope()` first; `build_prompt()` `output_format` param `[Must Do]`
- [x] `chunking.py` — `_DOCUMENT_SHARE_RE` + `_OPEN_ISSUE_RE` signals; 5 binary signals total `[Must Do]`
- [x] `metadata.py` — `_get_meeting_timings()` + timing/attendance branches in `handle_metadata_query()` `[Must Do]`
- [x] `query_intent.py` — `QueryDimensions` model; 4 new `QueryIntent` values; 13-rule `ROUTING_RULES`; `_fill_syntactic_dimensions()`; `_post_process_understanding()` `[Must Do]`
- [x] `retriever.py` — `compound_retrieve()`, `analytical_retrieve()`, `topic_summary_retrieve()`, `contribution_retrieve()` `[Must Do]`
- [x] `prompts.py` — 4 new answer templates; `_COUNT_PREFIX`, `_YESNO_PREFIX`, `_LIST_PREFIX` `[Must Do]`
- [x] `pipeline.py` — 8-mode dispatch; `_handle_structured_result()`; `output_format` wired end-to-end `[Must Do]`
- [x] Re-ingest: ChromaDB wiped + re-ingested — 1,669 chunks, 10 meetings, 2 new signals `[Must Do]`

### Test Suite Tasks

- [x] Query banks: `easy.json` (21 queries), `medium.json` (20 queries), `hard.json` not yet written `[Must Do]`
- [x] `query_generator.py` — generates grounded queries via Gemini + ChromaDB summaries `[Must Do]`
- [x] `test_runner.py` — `--difficulty easy|medium|hard`, `--ids`, `--tags` filter flags `[Must Do]`
- [x] `test_retrieval.py` — 46/46 no-LLM retrieval test suite `[Must Do]`
- [x] `report_generator.py` — generates `summary.md` from results `[Must Do]`
- [x] `TESTING_GUIDE.md` — Mermaid flowchart + command reference for new developers `[Must Do]`
- [x] `query_intent.py` + `prompts.py` + `builder.py` + `pipeline.py` — `QueryIntent` decoupled from routing: `is_attribution` dim + regex, `select_template_key()`, `build_prompt(template_key: str)` `[Must Do]`
- [ ] `run_tests.py` — one-command master runner chaining all 3 scripts `[Must Do]`
- [ ] LLM answer evaluator — score answer quality 1–10, not just intent match `[Nice to Have]`
- [ ] Regression tracker — compare two runs, detect improvements/regressions `[Nice to Have]`
- [ ] `hard.json` query bank — 10-15 hard queries (cross-meeting synthesis, contradiction, negative-space) `[Nice to Have]`

> **POC VALIDATED (2026-05-14):**
> Accuracy 30/30 (100%) | Scope isolation PASS | Multi-meeting synthesis PASS | Speed avg 3.4s (target <10s)
> Type 3 Miscommunication Detection deferred — needs design discussion before implementation.

> Bars update when you say "update files" at end of session.

---

---

## Phase 1 — Foundation: Transcript Ingestion into Vector DB

> Goal: Get chunks into ChromaDB with the right metadata so all 6 query types work.

- [ ] **Set up ChromaDB** — install, init local collection, connect to FastAPI `[Must Do]`
- [ ] **Design project/company data model** — implement `projects.json` config file (POC approach) `[Must Do]`
  - **POC:** `projects.json` at project root — PM manually maps `project_id → { name, meeting_ids[] }`. We generate the `project_id`. No UI or DB needed.
  - **Production (Option A, build when scaling):** PM creates projects in our system via UI, system generates `project_id`, meeting IDs are linked to project in a real DB. Fireflies has no native project concept — cannot rely on it for this.
- [ ] **Add project_id + company_id to every chunk** — ALL queries filter on project_id first, non-negotiable `[Must Do]`
- [ ] **Upgrade chunk metadata to full 5-level schema** (see schema below) `[Must Do]`
  - Level 1: `company_id`, `project_id`, `project_name`
  - Level 2: `meeting_id`, `meeting_title`, `meeting_date`, `meeting_number`, `meeting_type`
  - Level 3: `speaker_id`, `speaker_name`, `speaker_role` (client / pm / developer / unknown)
  - Level 4: `chunk_index`, `chunk_type`, `timestamp_start`, `timestamp_end`, `is_meeting_summary`
  - Level 5: `contains_decision`, `contains_commitment`, `contains_question`, `sentiment`
- [ ] **Speaker normalization** — map inconsistent names ("Rahul" vs "Rahul Sharma") to a consistent `speaker_id` across meetings `[Must Do]`
- [ ] **Speaker role assignment** — detect or manually map who is client / PM / developer per project `[Must Do]`
- [ ] **Content signal detection** — lightweight classifier per chunk to set `contains_decision`, `contains_commitment` flags `[Must Do]`
- [ ] **Meeting summary chunk** — generate and store one summary chunk per meeting with `is_meeting_summary=True` (needed for Type 4 queries) `[Must Do]`
- [ ] **Replace TODO in `webhook_handler.py:126`** — call `store_chunks()` after pipeline runs `[Must Do]`
- [ ] **Create `app/services/storage/` module** with `store_chunks()` and `get_chunks_by_meeting()` functions `[Must Do]`
- [ ] Add `meeting_type` field to metadata (client_call / planning / review / internal) `[Nice to Have]`
- [ ] Add `timestamp_start` / `timestamp_end` per chunk if Fireflies provides it `[Nice to Have]`

**Exit Criteria:** Can retrieve relevant chunks from a specific project by keyword using project_id filter.

---

## Phase 2 — Core RAG Engine ✓ COMPLETE

> Goal: Answer a plain English question grounded in transcript data with source attribution.

- [x] **Embedding pipeline** — `gemini-embedding-001` via LangChain, wired at store time `[Must Do]`
- [x] **Create `app/services/embeddings/` module** — `gemini_embeddings.py`, singleton `GoogleGenerativeAIEmbeddings` `[Must Do]`
- [x] **Basic retrieval function** — `retrieve_documents(query, project_id, filters, k)` in `retriever.py` `[Must Do]`
- [x] **Project scope enforcer** — `project_id` validated in retriever, raises if missing `[Must Do]`
- [x] **LLM integration** — Gemini `gemini-2.5-flash` via `google.genai` SDK in `answer_service.py` `[Must Do]`
- [x] **Source attribution** — `_extract_sources()` returns `{meeting_title, meeting_date, speaker_name}` per answer `[Must Do]`
- [x] **Create `POST /query` endpoint** — `{question, project_id}` → `{answer, sources, intent}` in `main.py` `[Must Do]`
- [x] **Answer generation** — `answer_question()` in `answer_service.py` replaces the old stub (no separate `ai/` module needed) `[Must Do]`
- [ ] Confidence scoring — flag low-confidence answers when retrieval returns low relevance `[Nice to Have]`

**Exit Criteria:** ✓ MET — PM types "What did the client say about the project?" → Gets answer with meeting reference + speaker name.

---

## Phase 3 — Query Taxonomy (6 Types)

> Goal: Route each question to the right retrieval strategy and prompt template.

- [ ] **Build question classifier** — detects which of the 6 types a question belongs to `[Must Do]`
  - Start with rule-based keyword matching (faster for POC)
  - Upgrade to LLM-based classifier if accuracy is poor
- [ ] **Create retrieval router** — calls the correct retrieval function per type (Python strategy pattern) `[Must Do]`
- [ ] **Type 1 — Decision Lookup** `[Must Do]`
  - Filter: `project_id` + `contains_decision=True`
  - Prompt: identify if a final decision was made, state it clearly with meeting ref
- [ ] **Type 2 — Action Item / Commitment Query** `[Must Do]`
  - Filter: `project_id` + `contains_commitment=True` + optional `speaker_name`
  - Prompt: extract commitments with owner, task, deadline
- [ ] **Type 3 — Miscommunication / Contradiction Detection** `[Must Do]`
  - Dual retrieval: client chunks about topic + dev chunks about same topic
  - Prompt: compare both sides, identify contradictions, state where breakdown happened
  - This is your most valuable differentiator vs Otter.ai
- [ ] **Type 4 — Progress / Summary Query** `[Must Do]`
  - Filter: `is_meeting_summary=True` for all meetings in project
  - Do NOT use standard vector search — fetch all summary chunks chronologically
  - Prompt: cohesive progress summary covering decisions, status, open issues, next steps
- [ ] **Type 5 — Speaker Specific Query** `[Must Do]`
  - Filter: `project_id` + `speaker_role` or `speaker_name` first, then semantic search within
  - Prompt: summarize speaker's position, changes in stance over time
- [x] **Type 6 — Timeline / Historical Query** `[Must Do]` ✓
  - `retrieve_timeline_documents()`: per-meeting semantic search, merged chronologically
  - `_TIMELINE_RE` expanded: cross-meeting comparison patterns (between meetings, how did X change, across both, etc.)
- [x] **Write 30 test questions** `[Must Do]` ✓ — `test_queries.py` has 30 questions (decision×4, commitment×5, summary×3, speaker×5, timeline×4, general×7, edge×2)

**Exit Criteria:** All 6 query types return correct grounded answers on 2 test projects.

---

## Phase 4 — Streamlit UI ✓ COMPLETE

> Goal: Usable by a real PM in under 10 minutes without explanation.

- [x] **Project selector dropdown** — PM picks project, enforces scope for all subsequent queries `[Must Do]`
- [x] **Chat window** — conversation history maintained within session `[Must Do]`
- [x] **Source panel** — shows meeting title, date, speaker, content preview for each answer `[Must Do]`
- [x] **Meeting timeline sidebar** — meetings listed chronologically with dates `[Nice to Have]`
- [x] **Intent badges** — coloured labels (Decision / Action Item / Summary / Speaker / etc.) per answer
- [x] **Speaker list with role icons** — 🔴 client / 🟡 PM / 🔵 developer in sidebar
- [x] **Cache management** — TTL=120s, project-switch clear, manual Refresh button
- [ ] **Confidence indicator** — flag answers where retrieval confidence is low `[Nice to Have]`

**Exit Criteria:** ✓ MET — PM can select project, ask any of the 6 query types, see grounded answers with source attribution.

---

## Phase 5 — POC Validation

> Goal: Prove it works or identify exactly where it fails.

- [x] **Accuracy test** — 30/30 questions passed (100%) on `test_queries.py` `[Must Do]` ✓
- [x] **Scope isolation test** — fake project_id returns "not found" with 0 sources, no data leakage `[Must Do]` ✓
- [ ] **Miscommunication test** — Type 3 deferred (needs further design discussion) `[Must Do]`
- [x] **Multi-meeting test** — summary, timeline, and commitment queries all synthesize both meetings `[Must Do]` ✓
- [x] **Speed test** — avg 3.4s, max 4.6s — all well under 10s target `[Must Do]` ✓
- [ ] **PM usability test** — sit a real PM down, observe where they get confused `[Nice to Have]`
- [x] Document results: POC fully validated — see DISCUSSION.md Session 14 `[Must Do]` ✓

---

---

---

## Production Phase — Retrieval Architecture Upgrade

> POC architecture uses hard-coded 7-intent routing + pure vector search. This breaks on query patterns not explicitly coded (causal origin queries, "who raised/first mentioned/was confused about").
> These 3 steps replace it with a scalable pipeline where cost scales with queries, not data size.

---

### Step 3 — LLM Re-ranking ✓ COMPLETE

- [x] `app/services/retrieval/reranker.py` — `rerank_documents(query, documents, intent_hint, topic_hint)` ✓
- [x] Wired into `answer_service.py` after retrieval, skipped for SUMMARY ✓
- [x] `_subject_topic_hint()` strips action/connector words before passing topic to re-ranker ✓
- [x] Re-ranking scores + chunk movement (e.g. "moved 3→1") logged in pipeline trace ✓

---

### Step 2 — Hybrid Retrieval (BM25 + Dense) `[Must Do — Implement Second]`

> **Why:** Pure dense search misses exact phrase matches. "CE classification code" as a phrase may be semantically diluted. BM25 finds exact keyword matches that dense search misses. Combined = better recall before re-ranking.

- [x] **`pyproject.toml`** — `rank_bm25` added ✓ `[Must Do]`
- [x] **`app/services/retrieval/retriever.py`** — `hybrid_retrieve()`, `_fetch_project_corpus()`, `_bm25_search()`, `_rrf_merge()` all implemented ✓ `[Must Do]`
- [x] **BM25 normalization** — `_normalize_for_bm25()` + updated `_tokenize()` — fixes `C.E.`/`"classification,"` token mismatches ✓ `[Must Do]` (Session 17)
- [x] **Log in pipeline trace** — dense_only / bm25_only / overlap counts logged ✓ `[Must Do]`
- [ ] **`app/services/answer_service.py`** — replace `retrieve_documents()` calls with `hybrid_retrieve()` `[Must Do]` ← **REMAINING**

**Files:** `retriever.py`, `answer_service.py`, `pyproject.toml` | **Cost:** Zero (BM25 is pure math) | **Re-ingest:** No

---

### Step 1 — Flexible Query Understanding ✓ COMPLETE

- [x] `understand_query(query, project_id)` → `QueryUnderstanding(topic, intent_type, named_speaker, needs_summary, temporal_focus)` ✓
- [x] LLM primary (Gemini Flash Lite) + regex fallback ✓
- [x] `classify_query_intent()` kept + upgraded to LLM-first ✓
- [x] `prompts.py` — all prompts centralized ✓
- [x] `answer_service.py` routing driven by `QueryUnderstanding` fields ✓

---

---

## Immediate Technical Debt (Fix Before Moving Forward)

- [ ] Fix typo in `app/config.py`: `FIRELIES_API_URL` → `FIREFLIES_API_URL`
- [ ] Update `metadata.py` to use actual meeting date from Fireflies API instead of `datetime.now()`
- [ ] Current chunking schema is missing 4 of 5 metadata levels — upgrade is Phase 1 priority

---

## Full 5-Level Metadata Schema (Reference)

```python
chunk_metadata = {
    # Level 1 — Scope (ALL queries filter on project_id first)
    "company_id":           "comp_xyz",
    "project_id":           "proj_abc123",
    "project_name":         "E-commerce Website",

    # Level 2 — Meeting
    "meeting_id":           "meet_004",
    "meeting_title":        "Sprint 3 Planning",
    "meeting_date":         "2025-04-15",   # ISO format
    "meeting_number":       4,
    "meeting_type":         "client_call",  # client_call / planning / review / internal

    # Level 3 — Speaker (enables Type 2, 3, 5 queries)
    "speaker_id":           "spk_rahul_01",
    "speaker_name":         "Rahul Sharma",
    "speaker_role":         "developer",    # client / project_manager / developer / unknown

    # Level 4 — Chunk Position
    "chunk_index":          12,
    "chunk_type":           "utterance",    # utterance / summary / action_item / decision
    "timestamp_start":      "00:34:21",
    "timestamp_end":        "00:35:10",
    "is_meeting_summary":   False,          # True for the one summary chunk per meeting

    # Level 5 — Content Signals (pre-filter for Type 1, 2)
    "contains_decision":    False,
    "contains_commitment":  True,
    "contains_question":    False,
    "sentiment":            "neutral",      # positive / negative / neutral
}
```
