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

## 4 — Type 6: Multi-Meeting Date Range Filtering

**What it is:**
For timeline queries across many meetings, filter by `meeting_date` range rather than fetching
all meetings and letting semantic search decide.

**Current state:**
Works fine for single-meeting projects. With multiple meetings, the semantic search already
returns the most relevant chunks but doesn't guarantee chronological coverage.

**When to address:**
After a second meeting is ingested into the same project and tested.
