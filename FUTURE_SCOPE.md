# Future Scope — Deferred Features

> Features documented here are intentionally deferred. They are NOT part of the current POC.
> Revisit after Phase 4 (Streamlit UI) is complete and the core system is validated.

---

## 1 — Role-Based Querying

**What it is:**
Allow queries like *"What did the **client** say?"* or *"What did the **developer** raise?"* — using
a speaker's role (client / developer / project_manager) as the filter, not their name.

**Why deferred:**
Requires automatically detecting and assigning speaker roles at ingestion time, which is a
non-trivial production problem. The current POC uses name-based queries ("What did Bhavneet say?")
which cover 90% of real PM use cases without this complexity.

**Full architecture designed (ready to build when needed):**

### Data model
Add to project config:
```json
{
  "proj_nolocode_001": {
    "roles_assigned": false,
    "speakers": {
      "Bhavneet Mhajan": "client",
      "Karan Middha": "developer",
      "Project Manager SFS": "project_manager"
    }
  }
}
```

### Signal priority chain (runs at ingest for each new speaker)

1. **Speaker registry check** — speaker seen before in this project? Use saved role. Done.
2. **Organizer auto-detect** — meeting organizer from Fireflies = `project_manager` (reliable).
3. **Email domain match** — external domain = `client`, internal non-organizer = `developer`.
4. **LLM inference** — send speaker's transcript excerpt to Gemini, classify role (~80-85% accuracy).
5. **PM confirmation** — PM reviews and corrects via UI. Correction saved to registry forever.

### `roles_assigned` flag flow

```
New meeting ingested
        |
roles_assigned = false?
        |           |
      YES           NO (first time for project)
        |           |
Use registry    Store chunks with speaker_role="unknown"
for all         Notify PM: "Assign speaker roles"
speakers        PM assigns via UI
        |           |
        |       Re-embed all unknown chunks with correct role
        |       Set roles_assigned = true
        |           |
        +-----------+
                |
        Future meetings: registry lookup — fully automatic
        New unknown speaker: flag only that person, not whole project
```

### Query changes needed
- `query_intent.py` `_SPEAKER_RE`: add role keywords back (client / developer / project manager)
- `answer_service.py`: add `_detect_speaker_role(query)` alongside `_detect_speaker_name()`
- Retrieval: when role detected, filter `speaker_role=<role>` instead of `speaker_name`

### What to build
| Component | Work |
|-----------|------|
| Speaker registry (persistent per project) | Add to projects.json or real DB |
| `roles_assigned` flag per project | In same config |
| Organizer auto-detect at ingest | Read Fireflies organizer field |
| LLM role classifier | One Gemini call per new unknown speaker |
| PM assignment UI (Streamlit) | Show detected roles, allow correction |
| Re-embed on assignment | Update `speaker_role` in all affected chunks |

---

## 2 — Type 3: Miscommunication / Contradiction Detection

**What it is:**
Detect when the client and developer have conflicting understandings of the same topic across
meetings. Example: client thinks feature X will be delivered Friday, developer said it needs 2 weeks.

**Why deferred:**
Most complex query type. Requires dual retrieval (client chunks + developer chunks on same topic),
a contradiction detection prompt, and a decision on what to return when one side has no relevant chunks.

**Design (when ready to build):**
- Dual retrieval: `retrieve_documents(query, project_id, filters={"speaker_role": "client"})` +
  `retrieve_documents(query, project_id, filters={"speaker_role": "developer"})`
- Dedicated prompt: "Compare these two perspectives. Are they consistent? If not, state the contradiction."
- Depends on Role-Based Querying (Feature 1) being built first.

---

## 3 — Speaker Name Extraction Improvements

**What it is:**
Current name detection matches on first name or full name. Edge cases:
- Nicknames ("SFS" for "Project Manager SFS")
- Names with typos in query ("Bhavnit" vs "Bhavneet")
- Multiple speakers with same first name

**When to address:**
Only if real PM usage reveals these as actual problems. Not worth building speculatively.

**Approach if needed:**
- Fuzzy matching library (rapidfuzz) for typo tolerance
- Alias map in `projects.json`: `{"SFS": "Project Manager SFS", "PM": "Project Manager SFS"}`

---

## 5 — Silence-Based Topic Splitting

**What it is:**
When a gap between two consecutive sentences is ≥ 30 seconds, force a chunk boundary even if the speaker did not change. A long pause = screen share, document lookup, or natural topic transition.

**Where to implement:**
[`app/services/transcript/chunking.py`](app/services/transcript/chunking.py) — inside `create_chunks()`, after the speaker-change check and before the `_TOPIC_SHIFT_RE` check (approximately line 335). Add one condition:

```python
elif current_chunk and start_ms is not None:
    last_end = current_times[-1][1] if current_times else None
    if last_end is not None and (start_ms - last_end) >= 30.0:
        flush_chunk(force=True)
```

**Why deferred (confirmed from real transcript data):**
Checked both Nolocode transcripts. The current `_TOPIC_SHIFT_RE` handles verbal transitions ("moving on", "let's go to the next", etc.). The two real cases where silence matters are:

1. Same-speaker pause before a topic-shift phrase that does NOT start with a keyword (e.g., Bhavneet: "Okay." → 35.6s pause → "Okay, let's go to the next query." at 1180→1215s in T1). The "Okay." is < HARD_MIN so it gets dropped — no incorrect chunk merge occurs today.
2. Pre-meeting dead time (T2: 295s gap at 226→522s, 74s gap at 132→206s) — administrative wait while participants join. These short filler phrases are already dropped by junk detection.

**When to build:**
- Production: when meeting count per project exceeds 5
- Longer meetings (90+ minutes) where same-speaker pauses cover screen sharing of different documents
- When incorrect `prev_chunk_id`/`next_chunk_id` adjacency links between unrelated topics are observed in answer quality regression testing

---

## 4 — Type 6: Multi-Meeting Date Range Filtering

**What it is:**
For timeline queries across many meetings, filter by `meeting_date` range rather than fetching
all meetings and letting semantic search decide.

**Current state:**
Works fine for single-meeting projects. With multiple meetings, the semantic search already
returns the most relevant chunks but doesn't guarantee chronological coverage.

**When to address:**
After a second meeting is ingested into the same project and tested.
