# DONE — Completed Work

> Everything listed here is implemented and working in the codebase.

---

## Fireflies Webhook Integration

- [x] `POST /webhook/fireflies` endpoint receives Fireflies.ai notifications
- [x] Flexible payload parsing — handles `transcript_id`, `meetingId`, `meeting_id`, `data.transcript_id`
- [x] Retry logic for early webhooks (3 attempts × 10s) when transcript ID is not immediately available

## Fireflies API Client

- [x] GraphQL client (`app/clients/fireflies_client.py`) — fetches transcript with `id`, `title`, `sentences`, `summary`
- [x] Bearer token authentication via `FIREFLIES_API_KEY`
- [x] Retry logic (3 attempts × 10s) for API eventual consistency
- [x] Summary polling — waits up to 6 attempts × 5s for `summary.overview` to appear
- [x] Custom `FirefliesAPIError` exception with proper error messages
- [x] `validate_api_config()` check on startup

## Transcript Processing Pipeline

- [x] **Normalization** (`app/services/transcript/normalize.py`) — flattens nested API response, validates required fields, raises `TranscriptValidationError` on bad data
- [x] **Metadata builder** (`app/services/transcript/metadata.py`) — extracts `meeting_id`, `title`, `date`
- [x] **Speaker-aware chunking** (`app/services/transcript/chunking.py`)
  - Hard speaker boundary (one chunk = one speaker)
  - `MAX_CHARS=250`, `MIN_CHARS=80`, `HARD_MIN=15`
  - Garbage filter for utterances < 8 characters
  - Size check before adding (no overflow)
  - Clean reset between chunks (no overlap)

## Development Tooling

- [x] Development mode (`DEVELOPMENT_MODE=true`) — uses `CONSTANT_TRANSCRIPT` from config, no API calls needed
- [x] Test suite (`test_fireflies.py`) — covers normalization, metadata, chunking, dev-mode pipeline
- [x] `chunks_output.json` — sample output from real transcript (50+ chunks)
- [x] `DEVELOPMENT_GUIDE.md` — full architecture doc with 5-phase roadmap

## Phase 1 — Foundation (Sessions 2, 3 & 4)

- [x] **`projects.json`** — config file at project root mapping `project_id → { name, company, meeting_ids, speakers }`
- [x] **`app/services/storage/__init__.py`** — module init
- [x] **`app/services/storage/project_store.py`**
  - `get_project_for_meeting(meeting_id)` — returns project scope fields for a meeting
  - `get_speaker_role(meeting_id, speaker_name)` — returns role from projects.json speakers map
  - UTF-8 encoding fix for unicode speaker names on Windows
- [x] **Full 5-level chunk metadata schema** (`chunking.py` upgraded)
  - Renamed: `date → meeting_date`, `speaker → speaker_name`, `sequence → chunk_index`
  - Added: `speaker_id` (slug), `speaker_role`, `chunk_type`, `is_meeting_summary`
  - Added: `contains_decision`, `contains_commitment`, `contains_question`, `sentiment` (placeholders)
  - Added: `meeting_number`, `meeting_type` (placeholders)
- [x] **`_stamp_project_and_roles()`** in `webhook_handler.py` — stamps `project_id`, `company_id`, `project_name`, `company_name`, `speaker_role` on every chunk after creation
- [x] **ChromaDB storage layer** (`app/services/storage/db.py` + `chunk_store.py`)
  - `db.py` — PersistentClient, `meeting_chunks` collection, cosine similarity space
  - `chunk_store.py` — `store_chunks()` (upsert, re-ingestion safe), `get_chunks_by_meeting()`, `get_chunk_count()`, `get_distinct_meeting_ids()`
  - Storage wired into `webhook_handler.py` — `# TODO` replaced with real `store_chunks(chunks)` call
- [x] **`meeting_number` auto-computation** — counts distinct meeting_ids already in ChromaDB for the project, assigns next number automatically
- [x] **Pipeline guard** — if `meeting_id` not in `projects.json`, pipeline aborts before storing (no broken chunks without `project_id`)
- [x] **Bug fixes (Session 4)**
  - `FIREFLIES_API_URL` typo fixed in `config.py` and `fireflies_client.py`
  - `date` field added to GraphQL query — real meeting date now used instead of `datetime.now()`
  - `meeting_number` reads from `meeting_meta` in `chunking.py` (was hardcoded `0`)
  - Dev mode now returns chunks (was returning `None`)

## Session 5 — ASR Cleaning + Summary Chunk + Content Signals

- [x] **ASR noise cleaning** (`normalize.py`) — `_clean_sentence()` with 5 compiled regex patterns
  - Removes: `um`, `uh`, `hmm`, `hm`, `er`, `erm`, `you know`
  - Removes repeated consecutive words (`"the the"` → `"the"`)
  - Drops sentences that reduce to < 8 chars after cleaning
  - Runs before chunking — cleaner text into embeddings
- [x] **Meeting summary chunk** (`chunking.py` + `webhook_handler.py`)
  - `build_summary_chunk()` creates one chunk per meeting with `is_meeting_summary=True`, `chunk_type="summary"`
  - `_resolve_summary()` in webhook_handler: uses Fireflies `summary.overview` first, Gemini 1.5 Flash fallback when Fireflies doesn't provide one
  - Summary chunk goes through `_stamp_project_and_roles()` — gets full project metadata like all other chunks
  - If both sources fail, pipeline continues without summary chunk (warning logged)
- [x] **`app/clients/gemini_client.py`** — `generate_meeting_summary(chunks, title)` via `gemini-1.5-flash`
  - Cost: ~$0.001 per 1-hour meeting — effectively free at POC scale
  - `GEMINI_API_KEY` added to `Config` and `.env`
- [x] **Content signal detection** (`chunking.py`) — `_detect_signals(text)` replaces `False` placeholders
  - `contains_decision`: matches "we decided", "confirmed", "going with", "agreed to", etc.
  - `contains_commitment`: matches "I will", "I'll", "action item", "by Friday", etc.
  - `contains_question`: ends with `?` OR starts with question word
  - Rule-based regex — zero cost, zero latency, runs inline during chunking

## Design Decisions (Locked)

- [x] **project_id assignment** — POC: `projects.json`. Production: Option A (PM creates projects in system)
- [x] **Speaker role assignment** — POC: `speakers` map inside `projects.json`. Same file, same pattern.

## Current Chunk Output Schema (Full — Session 3)

```python
{
    # Level 2 — Meeting
    "chunk_id":           "01KM2DD6MXGSZ4F1QW0BNJE16N_1",
    "meeting_id":         "01KM2DD6MXGSZ4F1QW0BNJE16N",
    "meeting_title":      "Nolocode meeting with Ashpreet",
    "meeting_date":       "2026-05-10",
    "meeting_number":     None,           # placeholder
    "meeting_type":       "unknown",      # placeholder

    # Level 3 — Speaker
    "speaker_name":       "Ngũmi Gituro",
    "speaker_id":         "ngumi_gituro",
    "speaker_role":       "client",       # real value from projects.json

    # Level 4 — Chunk position
    "chunk_index":        1,
    "chunk_type":         "utterance",
    "is_meeting_summary": False,          # placeholder

    # Level 5 — Content signals
    "contains_decision":   False,         # placeholder — needs classifier
    "contains_commitment": False,         # placeholder — needs classifier
    "contains_question":   False,         # placeholder
    "sentiment":           "neutral",     # placeholder

    # Level 1 — Scope (stamped by project_store)
    "project_id":         "proj_nolocode_001",
    "project_name":       "Nolocode",
    "company_id":         "comp_001",
    "company_name":       "Nolocode",

    # Content
    "text":               "We should finalize...",
    "text_length":        162,
}
```
