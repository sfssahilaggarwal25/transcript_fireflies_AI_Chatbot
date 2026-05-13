# TASKS — AI Meeting Intelligence System (POC)

> Master task list derived from full POC design discussion.
> Tags: `[Must Do]` = critical path, POC breaks without it | `[Nice to Have]` = improves quality but not blocking

---

## Overall Progress

```
Phase 1 — Foundation       [█████████░]  95%  10/10 tasks      ACTIVE (3 small tasks left)
Phase 2 — RAG Engine       [█░░░░░░░░░]  15%   1/6  tasks      ACTIVE (embedding done)
Phase 3 — Query Taxonomy   [░░░░░░░░░░]   0%   0/10 tasks    🔒 LOCKED
Phase 4 — Streamlit UI     [░░░░░░░░░░]   0%   0/5  tasks    🔒 LOCKED
Phase 5 — Validation       [░░░░░░░░░░]   0%   0/6  tasks    🔒 LOCKED

TOTAL XP EARNED:  1050 / 1500 XP
```

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

## Phase 2 — Core RAG Engine

> Goal: Answer a plain English question grounded in transcript data with source attribution.

- [ ] **Embedding pipeline** — convert each chunk's `text` to a vector and store in ChromaDB `[Must Do]`
  - Use Google Generative AI (`text-embedding-004`) or Anthropic — already installed
- [ ] **Create `app/services/embeddings/` module** with `embed_text(text) → List[float]` `[Must Do]`
- [ ] **Basic retrieval function** — given `(query, project_id)` → return top-K relevant chunks `[Must Do]`
- [ ] **Project scope enforcer** — any query without `project_id` is rejected at API level, not UI level `[Must Do]`
- [ ] **LLM integration** — connect Claude API (or Gemini) for generating answers `[Must Do]`
- [ ] **Source attribution** — every answer must include meeting title, date, speaker name `[Must Do]`
- [ ] **Create `POST /query` endpoint** — accepts `{ question, project_id }`, returns `{ answer, sources }` `[Must Do]`
- [ ] **Create `app/services/ai/` module** with `generate_answer(question, chunks) → str` `[Must Do]`
- [ ] Confidence scoring — flag low-confidence answers when retrieved chunks have low relevance score `[Nice to Have]`

**Exit Criteria:** PM types "What did the client say about the homepage design?" → Gets answer with meeting reference + speaker name.

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
- [ ] **Type 6 — Timeline / Historical Query** `[Must Do]`
  - Filter: `project_id` + `meeting_date` range, run two retrievals for two periods
  - Prompt: compare status/decisions between two time periods
- [ ] **Write 30 test questions** — 5 per query type, manually find the correct answer in transcripts `[Must Do]`
  - This becomes your validation dataset for Phase 5

**Exit Criteria:** All 6 query types return correct grounded answers on 2 test projects.

---

## Phase 4 — Streamlit UI

> Goal: Usable by a real PM in under 10 minutes without explanation.

- [ ] **Project selector dropdown** — PM picks project, enforces scope for all subsequent queries `[Must Do]`
- [ ] **Chat window** — conversation history maintained within session `[Must Do]`
- [ ] **Source panel** — shows meeting title, date, speaker for each answer `[Must Do]`
- [ ] **Meeting timeline sidebar** — list of all meetings in selected project with dates `[Nice to Have]`
- [ ] **Confidence indicator** — flag answers where retrieval confidence is low `[Nice to Have]`
- [ ] Keep UI minimal — POC is about intelligence, not design

**Exit Criteria:** A PM not involved in building this can use it without any explanation.

---

## Phase 5 — POC Validation

> Goal: Prove it works or identify exactly where it fails.

- [ ] **Accuracy test** — ask 30 known questions, score correct answers `[Must Do]`
- [ ] **Scope isolation test** — ask Project A question while in Project B — must return "out of scope" `[Must Do]`
- [ ] **Miscommunication test** — plant a known contradiction, verify detection `[Must Do]`
- [ ] **Multi-meeting test** — ask question that spans 3 meetings, verify synthesis `[Must Do]`
- [ ] **Speed test** — verify response time under 10 seconds for any query `[Must Do]`
- [ ] **PM usability test** — sit a real PM down, observe where they get confused `[Nice to Have]`
- [ ] Document results: what works, what fails, recommendation on full product build

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
