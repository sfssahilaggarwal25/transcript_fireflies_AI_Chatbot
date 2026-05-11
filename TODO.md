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
- [x] ChromaDB installed + `db.py` + `chunk_store.py` — full storage layer
- [x] `store_chunks()` wired into `webhook_handler.py` — TODO replaced
- [x] `meeting_number` auto-computes from ChromaDB (distinct meeting count + 1)
- [x] Pipeline guard — aborts cleanly if `meeting_id` not in `projects.json`
- [x] ASR noise cleaning — regex-based filler word removal in `normalize.py` before chunking
- [x] Meeting summary chunk — `build_summary_chunk()` in `chunking.py`, Fireflies summary → Gemini fallback
- [x] `app/clients/gemini_client.py` — `generate_meeting_summary()` with Gemini 1.5 Flash
- [x] Content signal detection — `_detect_signals()` regex classifier in `chunking.py` sets `contains_decision`, `contains_commitment`, `contains_question` per chunk

**Remaining (Phase 1):**
- [ ] Speaker normalization — verify `speaker_id` slug is consistent across multiple meetings

---

> **DEFERRED — Production/Automation Phase**
> Auto-registration of new meeting IDs to projects — currently manual (PM adds to `projects.json`).
> Must solve before production. See DISCUSSION.md → "Deferred to Production" for options.

---

## Phase 2 — RAG Engine

- [ ] Create `app/services/embeddings/embedder.py` — `embed_text(text) → List[float]`
- [ ] Add embeddings to `store_chunks()` — embed before storing in ChromaDB
- [ ] Create `app/services/retrieval/retriever.py` — `retrieve(query, project_id, filters) → List[Chunk]`
- [ ] Project scope enforcer — reject any query where `project_id` is missing (API-level check)
- [ ] Create `app/services/ai/chat_model.py` — `generate_answer(question, chunks) → str`
- [ ] LLM integration — Claude API (`claude-sonnet-4-6`)
- [ ] Source attribution — attach meeting title, date, speaker to every generated answer
- [ ] Create `POST /query` endpoint in `main.py` — accepts `{ question, project_id }`, returns `{ answer, sources }`

---

## Phase 3 — Query Taxonomy (6 Types)

- [ ] Create `app/services/retrieval/classifier.py` — rule-based question type detector
- [ ] Create `app/services/retrieval/router.py` — routes question type to correct retrieval strategy
- [ ] Type 1 — Decision Lookup: retrieval + prompt template
- [ ] Type 2 — Action Item Query: retrieval + prompt template
- [ ] Type 3 — Miscommunication Detection: dual retrieval + prompt template
- [ ] Type 4 — Progress Summary: summary-chunk-only retrieval + prompt template
- [ ] Type 5 — Speaker Specific: speaker-filtered retrieval + prompt template
- [ ] Type 6 — Timeline Query: date-range retrieval + prompt template
- [ ] Create `app/services/prompts/templates.py` — one prompt template per query type
- [ ] Write 30 test questions (5 per type) with known correct answers — validation dataset

---

## Phase 4 — Streamlit UI

- [ ] Create `streamlit_app.py` at project root
- [ ] Project selector dropdown (enforces scope)
- [ ] Chat window with session history
- [ ] Source panel (meeting + speaker per answer)
- [ ] Meeting timeline sidebar
- [ ] Confidence indicator for low-relevance answers

---

## Phase 5 — Validation

- [ ] Accuracy test: 30 known questions → score correct answers
- [ ] Scope isolation test: cross-project query must fail cleanly
- [ ] Miscommunication test: planted contradiction must be detected
- [ ] Multi-meeting synthesis test
- [ ] Speed test: < 10 seconds per query
- [ ] Document results + recommendation

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
