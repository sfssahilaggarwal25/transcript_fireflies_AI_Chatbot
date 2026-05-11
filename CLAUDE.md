# Claude Code Instructions — AI Meeting Intelligence System

## Session Start Protocol (ALWAYS do this first)

At the start of EVERY conversation, before doing anything else, read these 3 files in order:

1. `DISCUSSION.md` — current phase, open questions, design decisions, last session log
2. `TODO.md` — what's remaining, ordered by phase
3. `DONE.md` — what's already implemented (so you don't suggest re-doing it)

Then give the user a 3-line status summary:
- Current phase we're in
- What was last worked on
- What's the next task to pick up

Do this even if the user doesn't ask. It ensures every session starts with full context.

---

## End-of-Session Protocol

When the user says **"update files"** or **"session done"**, immediately update all 4 tracking files:

1. **DISCUSSION.md** — add a new session log entry with: date, topics covered, decisions made, open questions resolved or added, what's next
2. **DONE.md** — move any tasks completed this session from TODO to DONE
3. **TODO.md** — remove completed tasks, add any new tasks discovered
4. **TASKS.md** — update task status if any `[Must Do]` items were completed

---

## Project Overview

This is an AI Meeting Intelligence POC for Project Managers. It answers questions about past meetings by searching Fireflies.ai transcripts using RAG.

**Stack:** FastAPI + ChromaDB + Claude API + Streamlit  
**Current phase:** Phase 1 — ChromaDB setup + metadata schema upgrade

**Critical rule:** Every query must be filtered by `project_id` at the backend. This is not a UI feature — it is a backend enforcement rule.

---

## Key Files

| File | Purpose |
|------|---------|
| `TASKS.md` | Master task list with `[Must Do]` tags |
| `DONE.md` | Completed work |
| `TODO.md` | Remaining work, ordered by phase |
| `DISCUSSION.md` | Design decisions, open questions, session log |
| `DEVELOPMENT_GUIDE.md` | Architecture, data flow, env setup |
| `app/handlers/webhook_handler.py` | Main pipeline — storage TODO at line 126 |
| `app/services/transcript/chunking.py` | Chunking — needs metadata upgrade (Phase 1) |

---

## Open Questions (Resolve Before Phase 1 Coding)

1. How does `project_id` get assigned to a meeting? (manual config / Fireflies API / PM labels it)
2. How does speaker role (client / pm / developer) get assigned? (config file / PM labels / LLM inference)

---

## Coding Conventions

- No unnecessary comments — only add when the WHY is non-obvious
- No mock databases in tests — use real ChromaDB for integration tests
- All queries must include `project_id` filter — no exceptions
- Chunk metadata must follow the 5-level schema defined in `TASKS.md`
