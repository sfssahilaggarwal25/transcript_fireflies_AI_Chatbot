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

## New File/Folder Structure to Create

```
app/
├── services/
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── db.py             # ChromaDB init
│   │   └── chunk_store.py    # store/retrieve chunks
│   ├── embeddings/
│   │   ├── __init__.py
│   │   └── embedder.py       # embed_text()
│   ├── retrieval/
│   │   ├── __init__.py
│   │   ├── retriever.py      # retrieve(query, project_id, filters)
│   │   ├── classifier.py     # question type classifier
│   │   └── router.py         # routes to correct strategy
│   ├── prompts/
│   │   ├── __init__.py
│   │   └── templates.py      # 6 prompt templates
│   └── ai/
│       ├── __init__.py
│       └── chat_model.py     # generate_answer()
streamlit_app.py
```
