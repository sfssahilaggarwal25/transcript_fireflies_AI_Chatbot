# SPRINT 1 — Level 1: Foundation

> One sprint = one focused week. Only 3 objectives. Finish these before touching anything else.

---

```
╔══════════════════════════════════════════════════════╗
║           LEVEL 1  —  FOUNDATION                    ║
║           "Get chunks into ChromaDB"                ║
╠══════════════════════════════════════════════════════╣
║  XP Available:  300 XP                              ║
║  Difficulty:    ★★☆☆☆                               ║
║  Unlocks:       Level 2 — RAG Engine                ║
╚══════════════════════════════════════════════════════╝
```

---

## Current Phase: Phase 1

## Objective: ChromaDB + Full Metadata Schema

---

## This Sprint's Objectives

### OBJECTIVE 1 — Resolve the 2 Open Questions   `[  ]`  +50 XP
> These block ALL coding. Answer these first in DISCUSSION.md.

- [ ] Decide: how does `project_id` get assigned to a meeting?
- [ ] Decide: how does `speaker_role` get set per project?

---

### OBJECTIVE 2 — ChromaDB Setup + Storage Layer   `[  ]`  +100 XP
> Replace the `# TODO: Store chunks` with real storage.

- [ ] Install ChromaDB (`uv add chromadb`)
- [ ] Create `app/services/storage/db.py` — ChromaDB client + collection init
- [ ] Create `app/services/storage/chunk_store.py` — `store_chunks()`, `get_chunks_by_meeting()`
- [ ] Wire into `webhook_handler.py:126` — replace TODO comment

---

### OBJECTIVE 3 — Upgrade Chunk Metadata to Full 5-Level Schema   `[  ]`  +150 XP
> Current chunks are missing 4 of 5 metadata levels. This is what makes the 6 query types possible.

- [ ] Add Level 1 fields: `company_id`, `project_id`, `project_name`
- [ ] Add Level 2 fields: `meeting_number`, `meeting_type`
- [ ] Add Level 3 fields: `speaker_id`, `speaker_role`
- [ ] Add Level 4 fields: `chunk_index`, `chunk_type`, `is_meeting_summary`
- [ ] Add Level 5 fields: `contains_decision`, `contains_commitment`, `sentiment`
- [ ] Speaker normalization — consistent `speaker_id` across meetings
- [ ] Content signal detection — auto-set Level 5 flags per chunk

---

## Sprint Rewards

```
Complete all 3 objectives →  LEVEL UP to Phase 2 (RAG Engine)
Complete Objective 1      →  Open Questions resolved badge
Complete Objective 2      →  "First Blood" — first data in DB
Complete Objective 3      →  "Schema Lord" — full metadata working
```

---

## Sprint Progress

```
OBJECTIVE 1   [░░░░░░░░░░]   0%   Open Questions
OBJECTIVE 2   [░░░░░░░░░░]   0%   ChromaDB Setup
OBJECTIVE 3   [░░░░░░░░░░]   0%   Metadata Upgrade

OVERALL       [░░░░░░░░░░]   0%   Level 1 Complete
```

> Update this file manually as tasks complete, OR say "update files" to have Claude sync everything.

---

## Next Level Preview (Locked)

```
╔══════════════════════════════════════════════════════╗
║    LEVEL 2  —  RAG ENGINE              🔒 LOCKED    ║
║    "Answer questions from transcript data"          ║
║    Requires: Level 1 complete                       ║
╚══════════════════════════════════════════════════════╝
```
