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

### Step 3 — LLM Re-ranking ✓ COMPLETE

- [x] `app/services/retrieval/reranker.py` — `rerank_documents(query, documents, intent_hint, topic_hint)` ✓
- [x] Wired into `answer_service.py` after `_retrieve_for_understanding()` ✓
- [x] Skipped for SUMMARY intent (chronological order correct) ✓
- [x] Re-ranking scores + chunk movement logged in pipeline trace ✓
- [x] `_subject_topic_hint()` strips action words so re-ranker gets clean subject terms ✓

---

### Step 2 — Hybrid Retrieval (BM25 + Dense) ✓ COMPLETE

- [x] `rank_bm25` in `pyproject.toml` ✓
- [x] `hybrid_retrieve()`, `_fetch_project_corpus()`, `_bm25_search()`, `_rrf_merge()` in `retriever.py` ✓
- [x] BM25 normalization: `_normalize_for_bm25()` — general acronym canonicalization + punctuation removal ✓ (Session 17)
- [x] Full 3-stage logging: DENSE / BM25 / HYBRID with complete chunk text ✓ (Session 17)
- [x] Wired into `answer_service.py` via `_retrieve_for_understanding()` ✓

---

### Step 1 — Flexible Query Understanding ✓ COMPLETE

- [x] `understand_query(query, project_id)` in `query_intent.py` — returns `QueryUnderstanding(topic, intent_type, named_speaker, needs_summary, temporal_focus)` ✓
- [x] LLM primary (Gemini Flash Lite) + regex fallback when LLM fails ✓
- [x] `classify_query_intent()` kept and upgraded to LLM-first with regex fallback ✓
- [x] `prompts.py` — `CLASSIFIER_SYSTEM_PROMPT` + `UNDERSTANDING_PROMPT_TEMPLATE` + 7 answer templates ✓
- [x] `answer_service.py` routing uses `QueryUnderstanding` fields directly ✓
- [x] Pipeline trace logs: topic, intent, speaker, summary flag, temporal focus per query ✓

---

---

## Sprint 3 — Chunking Improvements (Single Re-ingestion Pass)

> All 3 production pipeline steps are complete. Next focus: fix chunking quality so the pipeline gets better raw material.
> **Do all of these together in one re-ingestion pass** — re-ingestion costs Gemini embedding API calls (521 docs), so batch all fixes.

### Tier 2a — Schema additions (Fireflies API + metadata)

- [ ] **`app/clients/fireflies_client.py`** — add `rawStartTimeMs`, `rawEndTimeMs` to GraphQL sentences query
- [ ] **`app/services/transcript/chunking.py`** — store `start_time` / `end_time` per chunk (ms from API)
- [ ] **`app/services/transcript/chunking.py`** — add `prev_chunk_id` / `next_chunk_id` after all chunks built (post-loop linking pass)
  - Link by `chunk_index` within same meeting: chunk N's `next_chunk_id` = chunk N+1's `chunk_id`
  - First chunk: `prev_chunk_id = None`. Last chunk: `next_chunk_id = None`

### Tier 2b — Chunking quality fixes

- [ ] **Soft char limit** — raise `MAX_CHARS` from 250 → 500 (reduces split-at-boundary semantic breaks)
- [ ] **Junk detection** — add `_is_low_quality(text)` check in `create_chunks()` before appending
  - Drop if unique token ratio < 0.4 (`len(set(tokens)) / len(tokens)`)
  - Drop if meaningful word count < 4 (after removing stopwords/fillers)
- [ ] **Topic-shift split** — split same-speaker block if sentence starts with topic-change marker
  - Keywords: `"now"`, `"another point"`, `"next"`, `"separately"`, `"also"`, `"moving on"`, `"switching to"`

### Tier 2c — Context expansion (post-rerank)

- [ ] **`app/services/answer_service.py`** — add `_expand_context(docs, top_n=5)` after re-rank step
  - For each of top 5 docs: fetch `prev_chunk_id` + `next_chunk_id` via `collection.get(ids=[...])`
  - Attach neighbor text to `_build_context()` call: `[BEFORE] ... [CHUNK] ... [AFTER] ...`
  - 10 DB lookups max per query, constant cost regardless of project size

### Re-ingestion checklist (do once, all Tier 2 fixes applied)
- [ ] Wipe `chroma_db/` folder
- [ ] Run dev mode pipeline — re-ingest both meetings with new schema
- [ ] Verify: `chunk_index`, `prev_chunk_id`, `next_chunk_id`, `start_time`, `end_time` present on sample chunks via `inspect_db.py`
- [ ] Re-run 30 test questions — all should still pass
