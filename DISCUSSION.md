# DISCUSSION — AI Meeting Intelligence System

> Running log of all design decisions, open questions, and next discussion topics.
> Update this file at the start/end of every session. It is our shared memory.

---

## What We Are Building

A project-scoped AI chatbot for Project Managers. PM selects a project → asks questions in natural language → gets answers sourced from Fireflies meeting transcripts with speaker attribution, decision tracking, and miscommunication detection.

**One-sentence POC goal:**
> "A Project Manager selects a project, asks any question about what was said, decided, or assigned across all meetings in that project, and gets a correct answer with the exact source — in under 10 seconds."

---

## Current Status

**Phase:** Phase 1 — Active (7 of 10 Must Do tasks complete)

**Last session covered:**
- ChromaDB installed and wired end to end — 232 chunks stored and verified
- `meeting_number` now auto-computes from ChromaDB (counts distinct meetings in project + 1)
- Pipeline guard added — if `meeting_id` not in `projects.json`, abort cleanly (no broken chunks stored)
- Identified production gap: new meeting IDs must be manually added to `projects.json` for POC — deferred to automation phase

**What's working right now:**
- Full pipeline: Fireflies webhook → normalize → chunk → stamp project_id + speaker_role + meeting_number → embed → persist to ChromaDB
- 232 chunks stored with full 5-level metadata — all fields correct and verified
- Re-ingestion safe (upsert — no duplicates)

---

## Design Decisions (Locked)

| Decision | Choice | Why |
|----------|---------|-----|
| Vector DB | ChromaDB (local) | Free, no server, perfect for POC |
| Chunking strategy | Utterance-based | Speaker metadata stays clean, Fireflies already separates by speaker |
| Scope enforcement | Backend (not UI) | Project A data must never touch Project B — not a UI toggle |
| LLM | Claude API (primary) | claude-sonnet-4-6, already discussed |
| Classifier (Phase 3) | Rule-based first | Faster for POC, upgrade to LLM if accuracy is poor |
| UI | Streamlit | POC speed, not design |

---

## Open Questions

> Move to "Resolved" once decided.

1. **How does a `project_id` get assigned to a meeting?**
   - **Status: RESOLVED — Session 2**
   - **POC approach:** `projects.json` config file at project root — PM manually maps `project_id → list of meeting_ids`. We generate the `project_id`. No UI needed for POC.
   - **Production approach (Option A):** PM creates a project inside our system, system generates `project_id`, PM links meeting IDs to the project via UI/DB. Build this when scaling beyond POC.
   - Fireflies has no native project concept — Spaces are too broad (company-level), Tags are fragile (typos break grouping).

2. **Speaker role assignment — who is client vs developer vs PM?**
   - **Status: RESOLVED — Session 3**
   - **POC approach:** `speakers` map inside `projects.json` — PM maps each speaker name to role once. Same config file as project_id, zero extra infrastructure.
   - All 6 speakers in Nolocode meeting mapped. New speakers default to `"unknown"` until PM updates the file.
   - Production approach: same as project_id — dedicated UI/DB when scaling.

3. **Which embedding model?**
   - `google-generativeai` is already installed (`text-embedding-004`)
   - Alternatively: Claude does not have a dedicated embedding model → use Google
   - **Status: Lean toward Google embeddings since it's already a dependency**

4. **Where does the LLM answer come from?**
   - Claude API (`claude-sonnet-4-6`) is the current preference
   - Google Gemini (`gemini-2.0-flash`) is also available via installed dependency
   - **Status: Use Claude — confirm with team**

5. **Contradiction detection for Type 3 queries — how deep?**
   - Simple: compare client chunks vs dev chunks, let LLM find contradictions
   - Advanced: dedicated NLP contradiction scoring before sending to LLM
   - **Status: Start simple for POC**

---

## Deferred to Production / Automation Phase

> These are NOT open questions for the POC. They are known gaps that need solving before production. Captured here so they are not forgotten.

### D1 — Auto-registering new meeting IDs (IMPORTANT)

**The problem:** When a new Fireflies meeting fires the webhook in production, its `meeting_id` must already exist in `projects.json` under the right project. Currently this is a manual step — PM or developer adds the ID to the file. The pipeline aborts cleanly if the ID is missing, but that means the meeting is simply not ingested.

**Why this matters at scale:** With many meetings per day, manual `projects.json` updates are not sustainable. This breaks the "automatic" pipeline promise.

**Options to evaluate when building production:**
- A: Listen to a Fireflies "meeting created" webhook event → auto-register the ID to a default project, let PM re-assign later
- B: Build a UI where PM assigns a new meeting to a project before/after it happens
- C: Check if Fireflies Spaces/Topics API can map meeting → project automatically
- D: Unregistered meetings land in a "pending" queue — PM reviews and assigns in bulk

**Current POC behaviour:** Pipeline aborts with a clear warning. No broken data is stored. Safe to run.

**Status: Deferred — solve before production, not needed for POC**

---

## Discussion Log

### Session 1 (2026-05-08) — Full POC Design

**Topics covered:**
- POC definition — what we're building and why (gap vs Otter.ai)
- System architecture: Fireflies → Ingestion → ChromaDB → RAG → LLM → Streamlit
- Hierarchy rule: Company → Project → Meetings → Speakers (project_id filter is backend law)
- 5-phase POC timeline
- Query taxonomy — 6 types, why each needs different handling
- Metadata schema — 5 levels, each field mapped to which query types it enables
- Chunking strategy confirmed: utterance-based

**Decisions made:** See "Design Decisions" table above.

**Left for next session:** How project_id gets assigned (Open Question 1), speaker role mapping (Open Question 2), start Phase 1 implementation.

---

### Session 2 (2026-05-09) — project_id Design Decision

**Topics covered:**
- Investigated whether Fireflies can provide a native `project_id` — confirmed it cannot (no project concept, Spaces are company-level, Tags are fragile)
- Evaluated 3 options for project_id assignment
- Decided POC approach: `projects.json` config file (PM maps meeting IDs to project manually)
- Decided production/scale approach: Option A — PM creates projects in our system, we generate `project_id`, PM links meetings via UI/DB

**Decisions made:**
- POC uses `projects.json` — simple, no UI required, correct and reliable
- Option A is the target architecture for production — documented in TASKS.md for when we build at scale

**Open questions resolved:** Q1 (project_id assignment) ✓

**Left for next session:** Resolve Open Question 2 (speaker role assignment), then start Phase 1 implementation

---

### Session 3 (2026-05-10) — Phase 1 Metadata + project_store

**Topics covered:**
- Resolved Q2: speaker roles added to `projects.json`, `get_speaker_role()` in project_store.py
- Upgraded `chunking.py` to full 5-level schema — all fields present (placeholders for classifier fields)
- Created `app/services/storage/` module — `project_store.py` with project + role lookup
- Wired `_stamp_project_and_roles()` into webhook_handler — every chunk gets project_id + speaker_role
- Fixed UTF-8 encoding bug in project_store.py (Windows cp1252 default broke unicode speaker names)
- Renamed fields: `date→meeting_date`, `speaker→speaker_name`, `sequence→chunk_index`

**Decisions made:**
- Speaker roles stored in `projects.json` alongside project_id — same file, same pattern, no extra infra

**Open questions resolved:** Q2 (speaker role assignment) ✓

**What's next:** ChromaDB install + db.py + chunk_store.py — then the storage TODO in webhook_handler can be replaced

---

### Session 4 (2026-05-10) — ChromaDB Live + Pipeline Verified

**Topics covered:**
- ChromaDB installed, `db.py` and `chunk_store.py` built — full storage layer complete
- `store_chunks()` uses upsert — re-ingestion safe, no duplicates
- Verified full pipeline end to end: 232 chunks stored and retrieved with all metadata correct
- Fixed `meeting_number` — now auto-computes from ChromaDB (counts distinct meetings for project + 1)
- Fixed pipeline guard — if `meeting_id` not in `projects.json`, pipeline aborts cleanly before storing
- Fixed `chunking.py` to read `meeting_number` from `meeting_meta` instead of hardcoding `0`
- Identified and documented D1 (auto-registration of new meeting IDs) as deferred production problem

**Decisions made:**
- POC requires manual `meeting_id` registration in `projects.json` — acceptable for now
- D1 documented in "Deferred to Production" section — will need a proper solution before production launch
- ChromaDB uses default `all-MiniLM-L6-v2` embeddings for POC — Phase 2 will evaluate switching to Google `text-embedding-004`

**Open questions resolved:** None this session (all POC questions resolved)

**What's next:** Content signal detection (`contains_decision`, `contains_commitment`) + meeting summary chunk — last 2 remaining Phase 1 tasks

---

### Session 6 (2026-05-13) — Git Setup + Merge Conflicts + DB Inspection

**Topics covered:**
- Fixed git global config — `user.name = "Sahil Aggarwal"`, `user.email = "sfs.sahilaggarwal25@gmail.com"`
- Fixed GitHub authentication — switched from password to classic PAT (token with `repo` scope)
- Resolved merge conflicts between local and remote `sahil_fireflies_poc` branch:
  - Remote had `clean_with_gemini()` per-sentence Gemini approach in `normalize.py` — dropped (decided against it)
  - Remote had `create_chunks()` commented out — kept our full implementation
  - Remote had `webhook_handler.py` pipeline commented out — kept our complete 5-step pipeline
  - Took `_clean_speaker_name()` from remote — strips Fireflies platform IDs e.g. "Karan Middha U0438EU2CSX" → "Karan Middha". Now applied in `normalize_transcript()` so all speaker names are clean before chunking.
  - Took `group_by_speaker()` utility from remote — kept as utility, not wired into main pipeline
- Created `inspect_db.py` — one-command tool to inspect ChromaDB state (chunk count, projects, signals, sample)
- Ran inspection: 232 chunks stored, all signals False, 0 summary chunks — because these were ingested before signal detection and summary chunk were built
- **Finding:** existing chunks need re-ingestion to pick up `contains_decision`, `contains_commitment`, `contains_question`, and summary chunk. Pipeline uses upsert so it's safe.

**Decisions made:**
- `_clean_speaker_name()` is now applied during `normalize_transcript()` — speaker names are cleaned before reaching the chunker or ChromaDB
- `projects.json` speaker keys like "Karan Middha U0438EU2CSX" should be updated to cleaned names ("Karan Middha") to match what normalize now outputs

**What's next:** Re-ingest existing meeting (trigger dev mode pipeline) to update all 232 chunks with signals + add summary chunk → then Phase 1 is complete → Phase 2 (RAG engine)

---

### Session 5 (2026-05-10) — ASR Cleaning + Summary Chunk + Content Signals

**Topics covered:**
- Researched Otter.ai chunking strategy — not publicly documented, inferred as speaker-based (same as ours). One confirmed thing: they strip filler words programmatically before indexing.
- Evaluated semantic chunking — concluded it is the WRONG direction. Destroys speaker attribution which is required for Type 3, 5, 2 queries. ArXiv paper confirms: not worth the cost for meeting transcripts.
- Implemented regex-based ASR noise cleaning in `normalize.py` — removes fillers before chunking, drops sentences that collapse below 8 chars.
- Implemented meeting summary chunk — uses Fireflies `summary.overview` when available, Gemini 1.5 Flash fallback when not. Cost ~$0.001/meeting.
- Created `app/clients/gemini_client.py` — Gemini is the only LLM available for POC development (no Claude API access yet).
- Implemented content signal detection (`contains_decision`, `contains_commitment`, `contains_question`) — rule-based regex in `chunking.py`. Chose regex over LLM: meeting language is explicit, signals are pre-filters not main retrieval, and 200+ API calls per meeting adds unacceptable latency.

**Decisions made:**
- Gemini (not Claude) is used for POC LLM calls — POC only has Gemini API access
- Content signals: regex for POC, upgrade to LLM-based classifier in Phase 3 only if accuracy is poor on real transcripts
- Semantic chunking is NOT being pursued — utterance-based is correct for speaker-filtered queries

**Phase 1 status after this session:** 9/10 Must Do tasks complete. One remaining: speaker normalization verification.

**What's next:** Verify speaker_id slug consistency across multiple meetings → Phase 1 complete → start Phase 2 (RAG engine)

---

## Phase Progress Tracker

| Phase | Status | Blocking On |
|-------|--------|-------------|
| Phase 1 — Foundation (ChromaDB + Metadata) | 95% — re-ingest + speaker slug check | Re-trigger pipeline in dev mode |
| Phase 2 — RAG Engine | Not started | Phase 1 complete |
| Phase 3 — Query Taxonomy | Not started | Phase 2 complete |
| Phase 4 — Streamlit UI | Not started | Phase 3 complete |
| Phase 5 — Validation | Not started | Phase 4 complete |

---

## What Otter.ai Does vs What We Do

| Feature | Otter.ai | Our System |
|---------|----------|------------|
| Auto transcription | Yes | Via Fireflies |
| Speaker identification | Yes | Yes |
| Keyword search | Yes | Yes + semantic |
| AI summary per meeting | Yes | Yes |
| Cross-meeting intelligence | **No** | **Yes** |
| Project-scoped isolation | **No** | **Yes** |
| Miscommunication detection | **No** | **Yes** |
| Decision tracking across meetings | **No** | **Yes** |
| Action item tracking with owner | **No** | **Yes** |

---

## Quick Reference Links

| File | What's in it |
|------|-------------|
| `TASKS.md` | Full task list with Must Do tags, metadata schema reference |
| `DONE.md` | Everything already implemented in codebase |
| `TODO.md` | Ordered remaining tasks + new folder structure to create |
| `DEVELOPMENT_GUIDE.md` | Architecture diagram, key files, env setup, data flow |
| `app/handlers/webhook_handler.py` | Main pipeline — full 5-step pipeline, storage + summary chunk wired |
| `app/services/transcript/chunking.py` | Utterance chunking + signal detection + summary chunk builder |
| `app/clients/gemini_client.py` | Gemini 1.5 Flash — meeting summary fallback |
