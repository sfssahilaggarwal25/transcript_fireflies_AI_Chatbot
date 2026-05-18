# TODO — What's Remaining

> Ordered by phase. Start from the top — each phase depends on the one above it.

---

## Phase 1 — Foundation: Vector DB + Rich Metadata

**Blocking everything downstream. Do this first.**

**Completed this phase so far:**
- [x] `projects.json` — project_id + speaker roles config
- [x] `app/services/storage/project_store.py` — `get_project_for_meeting()`, `get_speaker_role()`
- [x] Full 5-level chunk metadata schema in `chunking.py`
- [x] `_stamp_project_and_roles()` in `webhook_handler.py` — stamps project_id + speaker_role on every chunk
- [x] Fixed `FIREFLIES_API_URL` typo in `config.py` and `fireflies_client.py`
- [x] Fixed `metadata.py` — now uses real meeting date from Fireflies API
- [x] Added `date` field to GraphQL query in `fireflies_client.py`
- [x] ChromaDB + LangChain Chroma + Gemini embeddings — full storage layer
- [x] `store_documents()` wired into `webhook_handler.py` — chunks embedded and stored via LangChain
- [x] `meeting_number` auto-computes from ChromaDB (distinct meeting count + 1)
- [x] Pipeline guard — aborts cleanly if `meeting_id` not in `projects.json`
- [x] ASR noise cleaning — regex-based filler word removal in `normalize.py` before chunking
- [x] Meeting summary chunk — `build_summary_chunk()` in `chunking.py`, Fireflies summary → Gemini fallback
- [x] `app/clients/gemini_client.py` — `generate_meeting_summary()` with Gemini 1.5 Flash
- [x] Content signal detection — `_detect_signals()` regex classifier in `chunking.py` sets `contains_decision`, `contains_commitment`, `contains_question` per chunk
- [x] `_clean_speaker_name()` in `normalize.py` — strips Fireflies platform IDs from speaker names automatically
- [x] `app/services/documents/mapper.py` — `chunks_to_documents()` converts chunk dicts to LangChain Documents
- [x] `app/services/embeddings/gemini_embeddings.py` — `gemini-embedding-001` via `langchain-google-genai`
- [x] `inspect_db.py` — CLI tool to inspect ChromaDB contents

**Remaining (Phase 1):**
- [x] ~~Re-ingest existing meeting~~ — 232 chunks stored with Gemini embeddings, signals, and summary chunk ✓

---

> **DEFERRED — Production/Automation Phase**
> Auto-registration of new meeting IDs to projects — currently manual (PM adds to `projects.json`).
> Must solve before production. See DISCUSSION.md → "Deferred to Production" for options.

---

## Phase 2 — RAG Engine ✓ COMPLETE

- [x] ~~Embedding pipeline~~ — `gemini-embedding-001` via LangChain, wired at store time
- [x] ~~`retriever.py`~~ — `retrieve_documents(query, project_id, filters, k)`, project scope enforced
- [x] ~~Project scope enforcer~~ — `project_id` validated in retriever, raises if missing
- [x] ~~`app/services/answer_service.py`~~ — fully implemented: intent → retrieval → Gemini prompt → `{answer, sources, intent}`
- [x] ~~Prompt templates~~ — 7 templates (one per `QueryIntent` type) inside `answer_service.py`
- [x] ~~Summary intent retrieval~~ — uses `get_raw_collection().get()` with `$and` filter, NOT vector search
- [x] ~~`POST /query` endpoint~~ in `main.py` — `{question, project_id}` → `{answer, sources, intent}`

---

## Phase 3 — Query Taxonomy (6 Types)

- [x] ~~Question classifier~~ — `query_intent.py` with `QueryIntent` enum (7 types) covers all 6 query types
- [x] ~~Router~~ — `answer_service.py` wires `classify_query_intent()` → correct retrieval strategy per intent
- [x] ~~Verify Types 1, 2, 4, 5, 6~~ — all validated end-to-end against real data ✓
- [x] ~~QUESTION intent speaker filter~~ — name-based: `contains_question=True + speaker_name=<detected name>` ✓
- [x] ~~Type 5 improvement~~ — name-based speaker detection fully implemented with diacritic normalization ✓
- [x] ~~Type 6 improvement~~ — `retrieve_timeline_documents()` runs per-meeting semantic search, merges chronologically; `_TIMELINE_RE` expanded with 8 cross-meeting comparison patterns ✓
- [x] ~~Write 30 test questions~~ — `test_queries.py` now has 30 questions across all 7 types ✓

> **DEFERRED — Type 3 (Miscommunication Detection)**
> Dual retrieval (client + dev, same topic) + contradiction prompt. Most complex, biggest differentiator.
> Design decision pending: what to return when one side has no chunks about the topic.
> Build after all other types verified + Streamlit UI complete.

---

## Phase 4 — Streamlit UI ✓ COMPLETE

- [x] ~~Create `streamlit_app.py` at project root~~ ✓
- [x] ~~Project selector dropdown (enforces scope)~~ ✓
- [x] ~~Chat window with session history~~ ✓
- [x] ~~Source panel (meeting + speaker per answer)~~ ✓
- [x] ~~Meeting timeline sidebar~~ ✓ (in sidebar)
- [x] ~~Intent badges per answer~~ ✓
- [x] ~~Example questions empty state~~ ✓
- [x] ~~Cache refresh (TTL=120, project-switch clear, Refresh button)~~ ✓

---

## Phase 5 — Validation ✓ COMPLETE

- [x] ~~Accuracy test~~ — 30/30 (100%) on `test_queries.py` ✓
- [x] ~~Scope isolation test~~ — fake project_id returns "not found", 0 sources, no leakage ✓
- [ ] Miscommunication test — **DEFERRED** (Type 3 needs design discussion)
- [x] ~~Multi-meeting synthesis test~~ — summary + timeline + commitment all span both meetings ✓
- [x] ~~Speed test~~ — avg 3.4s, max 4.6s (target was <10s) ✓
- [x] ~~Document results~~ — full session log in DISCUSSION.md ✓

---

---

## Post-POC — Next Steps (Production Readiness)

> POC is complete. The following are the recommended next steps before a real production build.

- [ ] **Type 3 — Miscommunication / Contradiction Detection** — most valuable differentiator vs Otter.ai. Needs design decision on what to return when one side has no chunks. Build first among post-POC features.
- [ ] **D1 — Auto-registration of new meeting IDs** — currently manual (`projects.json`). Must solve before production. Options: Fireflies "meeting created" webhook → auto-register; PM assignment UI; or pending queue.
- [ ] **Role-based speaker queries** — "What did the client say?" (not just names). Full design in `FUTURE_SCOPE.md`. Build when PM feedback shows it's needed.
- [ ] **Add more projects / meetings** — currently 1 project, 2 meetings. Test with 3+ projects and 5+ meetings to verify scope isolation and timeline queries at scale.
- [ ] **Confidence scoring** — flag low-confidence answers when retrieval returns low relevance docs.
- [ ] **PM usability test** — sit a real PM down, observe where they get confused, iterate on UI.

---

---

## Production Phase — Retrieval Architecture Upgrade

> POC architecture uses hard-coded 7-intent routing + pure vector search. This breaks on any query pattern not explicitly coded (origin queries, causal queries, confusion queries, etc.).
> Production pipeline replaces this with a 3-component scalable architecture.
> POC code stays untouched — these are additive changes in new functions/modules.

### Why This Is Needed

Current failure example: "Who raised confusion about CE classification code?"
- System returned Karan (wrong) — his chunk had more keyword matches
- Correct answer was Rhythm Jalhotra — she introduced the confusion
- Root cause: vector similarity ranks by topic density, not causal origin
- This class of failure affects all "who raised / who first mentioned / who was confused about" queries
- Fix requires re-ranking, not adding more intents

---

### Step 3 — LLM Re-ranking `[Must Do — Implement First]`

**Why first:** Highest impact. Fixes the ranking accuracy problem for ALL query types without schema changes or re-ingestion. The right chunk is already in the DB — it's just not ranked #1.

**What it does:** After existing retrieval gets top-k candidates, one Gemini Flash Lite call scores each chunk against the true query intent. A chunk expressing confusion ranks higher than one merely mentioning the topic.

- [ ] Create `app/services/retrieval/reranker.py` — new file: `rerank_documents(query, documents, intent_hint)`
  - Input: query string + list of retrieved Documents + intent hint from query understanding
  - Sends query + all chunk previews to `gemini-2.5-flash-lite`
  - Prompt instructs: score by true relevance to query intent, not keyword overlap
  - Returns documents re-sorted by score, top 8-10
- [ ] Wire re-ranker into `answer_service.py` after `_retrieve_for_intent()` call
  - All intents go through re-ranking except SUMMARY (fetches by metadata, no ranking needed)
- [ ] Log re-ranking scores in pipeline trace (which chunks moved up/down)
- [ ] Test with the CE code query — verify Rhythm's chunk ranks above Karan's

**Files changed:** new `app/services/retrieval/reranker.py`, `app/services/answer_service.py`
**Cost:** +1 Gemini Flash Lite call per query (~$0.001)
**Re-ingestion needed:** No

---

### Step 2 — Hybrid Retrieval (BM25 + Dense) `[Must Do — Implement Second]`

**Why:** Pure vector/dense search misses exact phrase matches. "CE classification code" as a phrase may be semantically diluted by the embedding. BM25 finds exact keyword matches that dense search misses. Combined = better recall before re-ranking.

**What it does:** Run BM25 keyword search alongside existing dense search. Merge both result sets using Reciprocal Rank Fusion → top 25 candidates → pass to re-ranker.

- [ ] Add `rank_bm25` to `pyproject.toml` dependencies
- [ ] Build BM25 index from existing ChromaDB documents at query time
  - Fetch all chunks for the project from raw collection
  - Build BM25 index over `page_content` fields
  - Run keyword search, get scored results
- [ ] Add `hybrid_retrieve(query, project_id, filters, k=25)` to `retriever.py`
  - Stage 1a: existing dense `similarity_search` → top 25
  - Stage 1b: BM25 keyword search → top 25
  - Stage 2: Reciprocal Rank Fusion to merge both lists → deduplicated top 25
- [ ] Replace `retrieve_documents()` calls in `answer_service.py` with `hybrid_retrieve()`
- [ ] Log in pipeline trace: how many unique docs from dense-only vs BM25-only vs overlap

**Files changed:** `app/services/retrieval/retriever.py`, `app/services/answer_service.py`, `pyproject.toml`
**Cost:** Zero — BM25 is pure math
**Re-ingestion needed:** No

---

### Step 1 — Flexible Query Understanding `[Must Do — Implement Last]`

**Why last:** Steps 2 and 3 work with existing intent routing. This step replaces the 7-intent classifier entirely. Do it after re-ranking and hybrid retrieval are validated.

**Why needed:** Current 7-intent hard-coded routing requires new code for every new query pattern. Flexible JSON extraction handles any pattern via LLM understanding — no code changes for new query types.

**What it does:** Replace `classify_query_intent()` returning a fixed enum with an LLM call returning structured JSON: `{topic, intent_type, named_speaker, needs_summary, temporal_focus}`. Retrieval parameters derived dynamically from this JSON.

- [ ] Add `understand_query(query, project_id)` to `query_intent.py`
  - Returns structured dict, not a fixed enum value
  - Only 2 genuine routing decisions remain: `needs_summary=true` → summary collection; `named_speaker` → add speaker filter
  - Everything else → hybrid retrieval + re-ranking
- [ ] Keep old `classify_query_intent()` as fallback (regex) if LLM call fails
- [ ] Update `answer_service.py` routing to use flexible understanding output
- [ ] Update pipeline trace logging to show extracted JSON fields
- [ ] Validate: run existing 30 test questions — all should still pass

**Files changed:** `app/services/query_intent.py`, `app/services/answer_service.py`
**Cost:** Neutral — replaces existing classifier LLM call
**Re-ingestion needed:** No
