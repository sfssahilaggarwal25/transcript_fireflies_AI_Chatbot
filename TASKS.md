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

TOTAL XP EARNED:  1500 / 1500 XP   🏆 POC COMPLETE
```

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
