# Claude Code Instructions — AI Meeting Intelligence System

## Session Start Protocol (ALWAYS do this first)

At the start of EVERY conversation, before doing anything else, read these 4 files in order:

1. `docs/DISCUSSION.md` — current phase, open questions, design decisions, last session log
2. `docs/TODO.md` — what's remaining, ordered by phase
3. `docs/DONE.md` — what's already implemented (so you don't suggest re-doing it)
4. `docs/SPRINT.md` — active sprint, progress bars, what's in progress vs paused vs complete

Then give the user a 3-line status summary:
- Which sprint is active and its current completion percentage
- What was last worked on
- What's the next task to pick up

Do this even if the user doesn't ask. It ensures every session starts with full context.

---

## End-of-Session Protocol

When the user says **"update files"** or **"session done"**, immediately update all 5 tracking files:

1. **docs/DISCUSSION.md** — add a new session log entry with: date, topics covered, decisions made, open questions resolved or added, what's next
2. **docs/DONE.md** — move any tasks completed this session from TODO to DONE
3. **docs/TODO.md** — remove completed tasks, add any new tasks discovered
4. **docs/TASKS.md** — update task status if any `[Must Do]` items were completed
5. **docs/SPRINT.md** — update the active sprint's status box and progress bars; if a sprint completes, mark it `[COMPLETE]` and set the next sprint to `[IN PROGRESS]`

---

## Project Overview

This is an AI Meeting Intelligence POC for Project Managers. It answers questions about past meetings by searching Fireflies.ai transcripts using RAG.

**Stack:** FastAPI + ChromaDB + Gemini API + Streamlit  
**Current sprint:** Sprint 4 — Automated Test Suite (60% complete)

**Critical rule:** Every query must be filtered by `project_id` at the backend. This is not a UI feature — it is a backend enforcement rule.

---

## Key Files

| File | Purpose |
|------|---------|
| `docs/SPRINT.md` | Active sprint status, progress bars, what's in progress vs paused |
| `docs/OPEN_QUESTIONS.md` | All unresolved design questions (9 categories, P1/P2/P3 priority) |
| `docs/TASKS.md` | Master task list with `[Must Do]` tags |
| `docs/DONE.md` | Completed work |
| `docs/TODO.md` | Remaining work, ordered by phase |
| `docs/DISCUSSION.md` | Design decisions, open questions, session log |
| `docs/DEVELOPMENT_GUIDE.md` | Architecture, data flow, env setup |
| `app/rag/tests/TESTING_GUIDE.md` | Test suite commands, Mermaid flowchart, how to read reports |
| `app/rag/tests/query_bank/easy.json` | Easy-level test queries (12 queries, 5 intents) |
| `app/rag/answer/pipeline.py` | Full 5-step RAG pipeline — understand → retrieve → rerank → prompt → LLM |
| `app/core/retrieval/retriever.py` | Hybrid retrieval (dense + BM25 + RRF) compat shim |

---

## Open Questions

All open questions are tracked in `docs/OPEN_QUESTIONS.md` (9 categories, P1/P2/P3 priority).  
The SessionStart hook runs `.claude/scripts/open_questions.py` at every session start to show the count and all P1 items automatically.

To resolve a question: change `[ ]` → `[x]` in `docs/OPEN_QUESTIONS.md` and add a row to the Resolved Archive table.  
To add a question: pick the right category section, add `- [ ] [P1/P2/P3] Question text` with a `> **Why it matters:**` line below it.

---

## Coding Conventions

- No unnecessary comments — only add when the WHY is non-obvious
- No mock databases in tests — use real ChromaDB for integration tests
- All queries must include `project_id` filter — no exceptions
- Chunk metadata must follow the 5-level schema defined in `docs/TASKS.md`
