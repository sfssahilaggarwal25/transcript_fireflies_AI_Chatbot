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

## Test Suite — Next Steps

> Easy-level automated testing is working. These are the next improvements in priority order.

- [ ] **`run_tests.py`** — one master command that chains: query_generator → test_runner → report_generator. Accepts `--project-id` and `--count`. Opens `summary.md` automatically on finish.
- [ ] **LLM answer evaluator** — add `llm_evaluation: {score, verdict, reason}` field to each result JSON. Gemini reads query + answer + pipeline logs and scores answer quality 1–10. Currently only intent match and "has answer" are checked — does not verify if the answer is actually correct.
- [ ] **Regression tracker** — `compare.py` that diffs two run folders side by side: what improved, what regressed, what stayed the same. Useful after pipeline changes.
- [ ] **Extend runner to medium and hard** — `test_runner.py` currently only loads `easy.json`. Add `--difficulty` flag to support `medium` and `hard` query banks.
- [ ] **Fix easy_005 + easy_011 failures** — `general_query` queries about "project meetings" and "last project sync" are being misclassified as `summary_query` by the LLM classifier. Either add clearer phrasing to the query or update the `UNDERSTANDING_PROMPT_TEMPLATE` to handle this case.

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

## Sprint 3 — Chunking Improvements ✓ COMPLETE (Session 19)

### Tier 2a — Schema additions ✓
- [x] `app/clients/fireflies_client.py` — `rawStartTimeMs`/`rawEndTimeMs` in GraphQL sentences query
- [x] `app/services/transcript/chunking.py` — `start_time`/`end_time` per chunk (seconds, normalized via normalize.py)
- [x] `app/services/transcript/chunking.py` — `prev_chunk_id`/`next_chunk_id` via post-loop linking pass

### Tier 2b — Chunking quality fixes ✓
- [x] `MAX_CHARS` raised 250 → 500
- [x] `_is_low_quality(text)` — unique token ratio + meaningful word count
- [x] `_TOPIC_SHIFT_RE` — same-speaker topic-shift split

### Tier 2c — Context expansion ✓
- [x] `_expand_context(docs, top_n=5)` in `answer_service.py`
- [x] Neighbors labeled `[CONTEXT — just before/after]`, excluded from sources

### Re-ingestion ✓
- [x] ChromaDB wiped and re-ingested — 352 chunks, correct dates, timestamps, adjacency links
- [x] CE query verified correct after re-ingest — Bhavneet Mhajan correctly attributed
