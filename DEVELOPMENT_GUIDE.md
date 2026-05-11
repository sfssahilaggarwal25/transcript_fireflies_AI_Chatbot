# Fireflies AI Chatbot — Development Guide

A living reference for understanding what's built and what comes next.

---

## Project Overview

This project turns raw Fireflies.ai meeting recordings into a queryable AI chatbot. When a meeting ends, Fireflies sends a webhook to this service. The service fetches the full transcript via GraphQL, normalizes it, splits it into speaker-aware chunks, and (next step) stores those chunks so an AI model can answer questions about past meetings.

---

## Current Architecture

```
Fireflies.ai
    │
    │  POST /webhook/fireflies  (webhook notification)
    ▼
┌─────────────────────────────────────────────────────┐
│  FastAPI App  (main.py)                             │
│                                                     │
│  ┌──────────────────────────────────────────────┐   │
│  │  Webhook Handler  (handlers/webhook_handler) │   │
│  │                                              │   │
│  │  1. Extract transcript_id from payload       │   │
│  │  2. Fetch full transcript via GraphQL        │   │
│  │  3. Wait for summary to be ready             │   │
│  │  4. Normalize → Metadata → Chunks            │   │
│  │  5. [TODO] Store chunks                      │   │
│  └──────────────────────────────────────────────┘   │
│                                                     │
│  ┌─────────────────┐   ┌───────────────────────┐   │
│  │ Fireflies Client│   │  Transcript Services   │   │
│  │ (GraphQL API)   │   │  normalize.py          │   │
│  │                 │   │  metadata.py           │   │
│  │                 │   │  chunking.py           │   │
│  └─────────────────┘   └───────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

### Tech Stack

| Layer         | Tool / Library            | Version   |
|---------------|---------------------------|-----------|
| Web Framework | FastAPI                   | >=0.136.1 |
| ASGI Server   | Uvicorn                   | >=0.46.0  |
| HTTP Client   | Requests                  | latest    |
| AI (planned)  | Google Generative AI      | >=0.8.6   |
| Embeddings    | NumPy                     | >=2.4.4   |
| Config        | python-dotenv             | latest    |
| Python        | 3.12+                     |           |
| Package Mgr   | uv                        |           |

---

## Data Flow

```
Fireflies webhook payload
    ↓
Extract transcript_id
    ↓  (retry 3x / 10s if missing)
fetch_transcript(id)  ←── GraphQL: https://api.fireflies.ai/graphql
    ↓  (retry 3x / 10s for API consistency)
wait_for_summary()    ←── poll 6x / 5s until summary.overview exists
    ↓
normalize_transcript()   → { meeting_id, title, sentences[], summary }
    ↓
build_meeting_metadata() → { meeting_id, title, date }
    ↓
create_chunks()          → [ { chunk_id, speaker, text, sequence, ... } ]
    ↓
[TODO] Store chunks to database
```

**Dev mode shortcut:** Set `DEVELOPMENT_MODE=true` to skip the API and use `CONSTANT_TRANSCRIPT` from `app/config.py` directly.

---

## Key Files Reference

| File | Purpose | Key Functions |
|------|---------|---------------|
| `main.py` | FastAPI app + route registration | `POST /webhook/fireflies` |
| `app/config.py` | API config, dev-mode toggle, constant test transcript | `FIREFLIES_API_KEY`, `DEVELOPMENT_MODE`, `CONSTANT_TRANSCRIPT` |
| `app/clients/fireflies_client.py` | GraphQL client for Fireflies API | `fetch_transcript(id)`, `validate_api_config()` |
| `app/handlers/webhook_handler.py` | Main orchestration + retry logic | `handle_fireflies_webhook(payload)`, `wait_for_summary()` |
| `app/services/transcript/normalize.py` | Flatten + validate raw API response | `normalize_transcript(raw_data)` |
| `app/services/transcript/metadata.py` | Extract meeting-level metadata | `build_meeting_metadata(transcript)` |
| `app/services/transcript/chunking.py` | Speaker-aware text chunking | `create_chunks(sentences, meeting_meta)` |
| `test_fireflies.py` | Unit + integration tests | `test_create_chunks()`, `test_webhook_development_mode()` |

---

## Environment Setup

```bash
# 1. Install dependencies
uv sync

# 2. Configure environment
cp .env.example .env   # or create .env manually
# Add: FIREFLIES_API_KEY=your_key_here

# 3. Run in development mode (no Fireflies API needed)
DEVELOPMENT_MODE=true uvicorn main:app --reload

# 4. Run in production mode
uvicorn main:app --reload

# 5. Run tests
uv run python test_fireflies.py
```

**Required `.env` keys:**
```
FIREFLIES_API_KEY=<your Fireflies API key>
DEVELOPMENT_MODE=false   # set to true for local dev without real webhooks
```

---

## What's Done

- [x] `POST /webhook/fireflies` endpoint
- [x] Fireflies GraphQL API client with retries and error handling
- [x] Transcript ID extraction from multiple payload field names
- [x] Polling for transcript + summary availability
- [x] Transcript normalization with field validation
- [x] Meeting metadata extraction (id, title, date)
- [x] Speaker-aware chunking engine (size limits + garbage filtering)
- [x] Dev mode with constant test transcript
- [x] Test suite with JSON output (`chunks_output.json`)

---

## What's Next (Roadmap)

### Phase 1 — Database Storage
**Goal:** Persist processed chunks so they can be retrieved later.

- Choose a database:
  - **PostgreSQL** — for structured metadata + text
  - **ChromaDB / Pinecone / pgvector** — for vector search (recommended for chatbot use)
- Create `app/services/storage/` with a `store_chunks(chunks)` function
- Replace the `# TODO: Store chunks` comment in `webhook_handler.py:126`
- Add DB connection config to `app/config.py`

**Files to create:**
```
app/services/storage/
    __init__.py
    db.py          # DB connection setup
    chunk_store.py # store_chunks(), get_chunks_by_meeting()
```

---

### Phase 2 — Embedding Service
**Goal:** Convert text chunks into vector embeddings for semantic search.

- Use `google-generativeai` (already installed) or a local model
- Embed each chunk's `text` field when storing
- Store embedding alongside chunk in the vector DB

**Files to create:**
```
app/services/embeddings/
    __init__.py
    embedder.py    # embed_text(text) → List[float]
```

**Hook into pipeline:** Call `embedder.embed_text(chunk["text"])` inside `store_chunks()`.

---

### Phase 3 — Chat API Endpoint
**Goal:** Accept a user question and return an AI-generated answer.

- New endpoint: `POST /chat`
- Request: `{ "question": "What was discussed about pricing?" }`
- Response: `{ "answer": "...", "sources": [...] }`
- Flow: embed question → vector search chunks → pass context to AI model

**Files to create:**
```
app/handlers/chat_handler.py   # handle_chat_query(question)
app/routes/                    # optional: split routes from main.py
```

**Add to `main.py`:**
```python
@app.post("/chat")
async def chat(request: Request):
    body = await request.json()
    return await handle_chat_query(body["question"])
```

---

### Phase 4 — AI Integration
**Goal:** Use an LLM to generate answers from retrieved chunks.

- **Option A (Google):** Use `google-generativeai` already installed — `gemini-1.5-pro` or `gemini-2.0-flash`
- **Option B (Anthropic):** Use Claude API (`claude-sonnet-4-6`) for higher quality answers

**Prompt pattern:**
```
You are a meeting assistant. Use the transcript excerpts below to answer the question.

Meeting: {title} on {date}

Excerpts:
{chunk_1_text}  [Speaker: {speaker}]
{chunk_2_text}  [Speaker: {speaker}]
...

Question: {user_question}

Answer:
```

**Files to create:**
```
app/services/ai/
    __init__.py
    chat_model.py   # generate_answer(question, chunks) → str
```

---

### Phase 5 — Auth + Production Hardening
**Goal:** Secure the API and prepare for deployment.

- Validate Fireflies webhook signature (HMAC) to prevent spoofed webhooks
- Add API key auth for `POST /chat`
- Add rate limiting
- Add structured logging (JSON format for log aggregation)
- Docker + deployment config

---

## Chunk Data Schema

Each processed chunk has this structure:

```json
{
  "chunk_id": "01KM2DD6MXGSZ4F1QW0BNJE16N_1",
  "meeting_id": "01KM2DD6MXGSZ4F1QW0BNJE16N",
  "meeting_title": "Nolocode meeting with Ashpreet",
  "date": "2026-05-08",
  "speaker": "John Doe",
  "sequence": 1,
  "text": "Would have been great to discuss the pricing model earlier...",
  "text_length": 162
}
```

**Chunking rules (in `chunking.py`):**
- `MAX_CHARS = 250` — flush chunk before exceeding this
- `MIN_CHARS = 80` — don't save unless at least this long
- `HARD_MIN = 15` — absolute discard floor
- Utterances under 8 chars are discarded (e.g., "Ok.", "Sa.")
- Each chunk belongs to exactly one speaker — hard boundary at speaker change

---

## GraphQL Query Reference

Query used in `app/clients/fireflies_client.py`:

```graphql
query Transcript($id: String!) {
  transcript(id: $id) {
    id
    title
    sentences {
      text
      speaker_name
    }
    summary {
      overview
      action_items
    }
  }
}
```

**Endpoint:** `https://api.fireflies.ai/graphql`  
**Auth:** `Authorization: Bearer <FIREFLIES_API_KEY>`

---

## Testing

```bash
# Run all tests
uv run python test_fireflies.py

# Inspect chunk output
cat chunks_output.json
```

| Test | What it verifies |
|------|-----------------|
| `test_normalize_transcript()` | Normalization preserves data, rejects invalid input |
| `test_build_meeting_metadata()` | Metadata fields map correctly |
| `test_create_chunks()` | Chunks are well-formed, size limits respected, output saved to `chunks_output.json` |
| `test_webhook_development_mode()` | Full dev-mode pipeline runs end-to-end |
| `test_webhook_production_mode()` | Production mode structure (expects API failure in test env) |

---

## Known Issues / Quirks

- `app/config.py` has a typo: `FIRELIES_API_URL` (missing an `f`) — harmless but worth fixing
- `metadata.py` uses `datetime.now()` for the date field instead of the actual meeting date — Fireflies API does have a `date` field that could be used
- `app/services/transcript/pipeline.py` exists but is empty — placeholder for future orchestration logic
