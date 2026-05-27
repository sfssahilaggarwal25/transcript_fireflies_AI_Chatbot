# Scope-First Architecture Plan
**Goal:** Fix meeting-level queries before tackling project-level queries.

---

## 1. What's Actually Broken Today

### Problem A — `parse_meeting_scope()` Called Twice

```
_fill_syntactic_dimensions()      → calls parse_meeting_scope() → sets has_temporal (bool only)
_retrieve_for_understanding()     → calls parse_meeting_scope() → gets date_where (used for retrieval)
```

Same DB query, twice, every request. More importantly — routing decisions happen
**without knowing which meetings are in scope**. The scope is only resolved *after* routing.

### Problem B — `compound_retrieve()` Fallback Discards Valid Speaker Chunks

```python
if len(speaker_docs) >= 3:
    return speaker_docs       # ← threshold is 3
return broad_docs             # ← fallback: all speakers, all topics
```

Query: "What did Harsh discuss about AI in previous 2 meetings?"

If Harsh said 2 things about AI in those meetings → threshold not met → fallback fires
→ LLM gets 25 chunks from *all speakers*, not Harsh's 2 chunks
→ Answer attributes wrong speaker's words to Harsh

### Problem C — Routing Doesn't Consider Scope

When a query is scoped to 1 meeting, the routing matrix doesn't know that.
So a query like "What are the topics in the previous meeting?" might route to
`topic_summary` (searches all meetings for a topic) instead of `summary`
(fetches that one meeting's summary chunk). Wrong engine for the scope.

### Problem D — `topic_summary_retrieve()` Scope Handling Is Brittle

```python
for mid in meeting_ids:              # iterates ALL project meetings
    scoped = get_scoped_meeting_ids(date_where, project_id)  # DB call per iteration
    if scoped and mid not in scoped:
        continue
```

This calls `get_scoped_meeting_ids()` inside a loop — one DB call per meeting.
Also calls `parse_meeting_scope()` a 3rd time (via pipeline → topic_summary route).

---

## 2. The Core Design Change — Scope Detected Once, Propagated Everywhere

### Old Flow
```
Query
  ↓
understand_query()
  ↓ parse_meeting_scope() call #1 → has_temporal (bool)
  ↓ routing rules
  ↓
pipeline._retrieve_for_understanding()
  ↓ parse_meeting_scope() call #2 → date_where dict
  ↓ pass date_where to retrieval function
  ↓
retrieval function uses date_where
```

### New Flow
```
Query
  ↓
understand_query()
  ↓ parse_meeting_scope() call — ONE time only
  ↓ resolve meeting_ids → store in QueryUnderstanding.scope_meeting_ids
  ↓ routing rules (now CAN see scope type)
  ↓
pipeline._retrieve_for_understanding()
  ↓ build date_where FROM understanding.scope_meeting_ids (no DB call)
  ↓ pass date_where to retrieval function
  ↓
retrieval function uses date_where (same as before — no change)
```

**What changes:** Where scope is detected.
**What stays the same:** How scope is applied in retrieval (date_where format unchanged).

---

## 3. Two Scopes — Two Query Classes

### Meeting-Level (Phase 1 — do first)

A query is meeting-level when `scope_meeting_ids` is non-empty — it references
specific meeting(s) by temporal phrase.

| Phrase | Resolves to |
|--------|------------|
| "previous meeting" / "last meeting" | 1 meeting (most recent) |
| "first meeting" / "earliest meeting" | 1 meeting (oldest) |
| "last 2 meetings" / "previous 3 meetings" | N most recent meetings |
| "that meeting" / "this meeting" | 1 meeting (most recent) |
| "the second meeting" | 1 meeting (2nd chronologically) |
| "April 20th" / "9th of May" | 1 meeting (by date match) |

**Key property:** You know EXACTLY which chunks can appear in the answer.
All retrieval must be locked to those chunk IDs.

### Project-Level (Phase 2 — do second)

A query is project-level when `scope_meeting_ids` is empty — no temporal reference.

| Example | Scope |
|---------|-------|
| "What did Harsh commit across all meetings?" | All meetings |
| "How has AI architecture evolved?" | All meetings |
| "Who spoke most?" | All meetings |
| "What decisions were made?" | All meetings |

**Key property:** Cross-meeting synthesis. Different retrieval strategies needed.

---

## 4. Data Model Changes — `QueryUnderstanding`

```python
class QueryUnderstanding(BaseModel):
    topic:             str
    intent_type:       QueryIntent
    named_speaker:     Optional[str] = None
    needs_summary:     bool = False
    temporal_focus:    Optional[str] = None
    signal_filter:     Optional[str] = None
    retrieval_mode:    str = "hybrid"
    output_format:     str = "prose"
    dimensions:        QueryDimensions = QueryDimensions()

    # NEW — populated by _post_process_understanding(), never by LLM
    scope_meeting_ids: list[str] = []        # empty = project-level (all meetings)
    scope_type:        str = "project"       # "meeting" | "project"
```

`scope_meeting_ids` is the ground truth for scope. Every retrieval function reads it.
`scope_type` is a convenience label for routing and logging.

---

## 5. File-by-File Changes

### File 1: `app/services/query_intent.py`

**Change 1a — `_fill_syntactic_dimensions()` returns `scope_where`**

Currently: calls `parse_meeting_scope()`, sets `has_temporal`, returns nothing.
After:  returns the `scope_where` dict (or None) so it can be reused.

```python
def _fill_syntactic_dimensions(
    u: QueryUnderstanding, query: str, project_id: str
) -> dict | None:
    ...
    scope_where = parse_meeting_scope(query, project_id)
    u.dimensions.has_temporal = scope_where is not None
    return scope_where          # ← NEW: return for reuse (avoid 2nd DB call)
```

**Change 1b — `_post_process_understanding()` resolves meeting IDs**

```python
def _post_process_understanding(
    u: QueryUnderstanding, query: str, project_id: str
) -> QueryUnderstanding:
    scope_where = _fill_syntactic_dimensions(u, query, project_id)  # one call

    # Resolve meeting IDs from scope — store in understanding
    if scope_where:
        from app.services.answer.scope import get_scoped_meeting_ids
        ids = list(get_scoped_meeting_ids(scope_where, project_id))
        if ids:
            u.scope_meeting_ids = ids
            u.scope_type = "meeting"

    mode, label = _apply_routing(u, query)
    u.retrieval_mode = mode
    u.output_format  = _derive_output_format(u)
    logger.info(
        "  routing    : mode=%s | rule=%s | output_format=%s | scope=%s (%d meetings)",
        mode, label, u.output_format, u.scope_type, len(u.scope_meeting_ids),
    )
    return u
```

**No routing rule changes needed.** `has_temporal` is still set correctly.
The routing matrix is unchanged — it continues to use `has_temporal` as before.

---

### File 2: `app/services/answer/pipeline.py`

**Change 2a — Build `date_where` from stored `scope_meeting_ids`**

Remove the `parse_meeting_scope()` call from `_retrieve_for_understanding()`.
Replace with a helper that converts `scope_meeting_ids` back to a ChromaDB where-clause.

```python
def _build_scope_filter(understanding: QueryUnderstanding) -> dict | None:
    """Convert scope_meeting_ids to a ChromaDB where-clause. No DB call needed."""
    ids = understanding.scope_meeting_ids
    if not ids:
        return None
    if len(ids) == 1:
        return {"meeting_id": {"$eq": ids[0]}}
    return {"meeting_id": {"$in": ids}}
```

Then in `_retrieve_for_understanding()`:

```python
def _retrieve_for_understanding(query, project_id, understanding):
    # BEFORE: date_where = parse_meeting_scope(query, project_id)
    # AFTER:
    date_where = _build_scope_filter(understanding)   # no DB call — already resolved

    if date_where:
        logger.info("  scope      : %s (%d meeting(s))", understanding.scope_type,
                    len(understanding.scope_meeting_ids))

    # Rest of dispatch logic unchanged — date_where passed exactly as before
    ...
```

**What doesn't change:** Every retrieval function still receives `date_where` in the
same format as before. `hybrid_retrieve()`, `compound_retrieve()`,
`analytical_retrieve()`, `topic_summary_retrieve()`, `contribution_retrieve()`
all work unchanged.

---

### File 3: `app/services/retrieval/retriever.py`

**Change 3a — Fix `compound_retrieve()` fallback threshold**

The fallback threshold of 3 is wrong for meeting-scoped queries.
If Harsh said 2 things about AI in the previous meeting, we should return
those 2 things — not fall back to all speakers.

```python
def compound_retrieve(
    query: str, project_id: str, named_speaker: str,
    signal_filter: Optional[str] = None,
    date_where: Optional[dict] = None,
    k_broad: int = 40, k_final: int = 25,
) -> list[Document]:
    # Pass 1: broad search (scoped via date_where if present)
    broad_docs = hybrid_retrieve(query, project_id, hard_filters=None,
                                 date_where=date_where, k=k_broad)

    # Pass 2: post-filter by speaker
    target = _norm_name(named_speaker)
    speaker_docs = [
        d for d in broad_docs
        if _norm_name(d.metadata.get("speaker_name", "")) == target
    ]

    if signal_filter:
        speaker_docs = [
            d for d in speaker_docs
            if d.metadata.get(f"contains_{signal_filter}", False)
        ]

    # OLD: if len(speaker_docs) >= 3: return speaker_docs
    # NEW: return speaker docs if ANY found — threshold was wrong
    if speaker_docs:
        logger.info(
            "  compound   : %d/%d speaker docs kept (speaker=%s, signal=%s)",
            len(speaker_docs), len(broad_docs), named_speaker, signal_filter,
        )
        return speaker_docs[:k_final]

    # Fallback only when ZERO speaker chunks found in scope
    logger.info(
        "  compound   : 0 speaker docs found for %s — returning broad results",
        named_speaker,
    )
    return broad_docs[:k_final]
```

**Change 3b — Fix `topic_summary_retrieve()` scope handling**

Currently calls `get_scoped_meeting_ids()` inside the meeting loop (DB call per iteration).
After: receive `scope_meeting_ids` directly, filter the loop upfront.

```python
def topic_summary_retrieve(
    topic: str,
    project_id: str,
    scope_meeting_ids: Optional[list[str]] = None,   # ← replaces date_where
    k_per_meeting: int = 8,
) -> list[Document]:
    all_project_meetings = get_meeting_ids_for_project(project_id)
    if not all_project_meetings:
        return hybrid_retrieve(topic, project_id, k=k_per_meeting * 3)

    # If scoped: only iterate relevant meetings — no per-iteration DB call
    meetings_to_search = (
        [mid for mid in all_project_meetings if mid in scope_meeting_ids]
        if scope_meeting_ids
        else all_project_meetings
    )

    all_docs: list[Document] = []
    for mid in meetings_to_search:
        try:
            docs = hybrid_retrieve(
                topic, project_id,
                hard_filters={"meeting_id": mid},
                date_where=None,
                k=k_per_meeting,
            )
            all_docs.extend(docs)
        except Exception as e:
            logger.warning("topic_summary_retrieve skipped meeting_id=%s: %s", mid, e)

    all_docs.sort(key=lambda d: (
        d.metadata.get("meeting_date", ""), d.metadata.get("start_time") or 0,
    ))
    logger.info(
        "  topic_sum  : %d docs for topic=%r across %d/%d meetings",
        len(all_docs), topic, len(meetings_to_search), len(all_project_meetings),
    )
    return all_docs
```

Also update the call in `pipeline.py`:
```python
# Before:
topic_summary_retrieve(topic, project_id, date_where=date_where)

# After:
topic_summary_retrieve(topic, project_id, scope_meeting_ids=understanding.scope_meeting_ids or None)
```

---

### File 4: `app/services/answer/builder.py`

**Change 4a — `retrieve_summary_chunks()` uses scope directly**

Currently: re-calls `parse_meeting_scope()` and `get_scoped_meeting_ids()` inside this function.
After: receives `scope_meeting_ids` as a parameter — no extra DB call.

```python
def retrieve_summary_chunks(
    project_id: str,
    query: str = "",
    scope_meeting_ids: Optional[list[str]] = None,   # ← NEW parameter
) -> tuple[list[Document], str | None]:

    # ... fetch all summary docs ...

    # NEW: if scope is already resolved, filter directly — no re-detection
    if scope_meeting_ids:
        scoped = [d for d in docs if d.metadata.get("meeting_id") in scope_meeting_ids]
        if scoped:
            logger.info("  scope      : filtered to %d meeting(s) via scope_meeting_ids", len(scoped))
            return scoped, None

    # EXISTING fallback: extract_month_day() for date phrases (kept unchanged)
    ...
```

Update the call in `pipeline.py`:
```python
# Before:
retrieve_summary_chunks(project_id, query)

# After:
retrieve_summary_chunks(project_id, query, scope_meeting_ids=understanding.scope_meeting_ids or None)
```

---

## 6. What Does NOT Change

| Component | Why it stays the same |
|-----------|----------------------|
| `scope.py` | Correct already — `parse_meeting_scope()` works fine |
| `_build_filter()` in retriever | Takes `date_where` format — no changes |
| `hybrid_retrieve()` internals | Already applies `date_where` to both dense and BM25 |
| `analytical_retrieve()` | Already takes `date_where` — pass `_build_scope_filter()` output |
| `contribution_retrieve()` | Already takes `date_where` — same |
| All routing rules (ROUTING_RULES) | Logic unchanged — `has_temporal` still works correctly |
| All prompt templates | Unchanged |
| `reranker.py` | Unchanged |
| ChromaDB schema | No re-ingestion needed |

---

## 7. Implementation Order (Meeting-Level First)

### Step 1 — Data model + scope detection (query_intent.py)
- Add `scope_meeting_ids`, `scope_type` to `QueryUnderstanding`
- `_fill_syntactic_dimensions()` returns `scope_where`
- `_post_process_understanding()` resolves and stores meeting IDs
- **Test:** `understand_query("What did Harsh discuss in previous meeting?", project_id)` → `scope_meeting_ids` has 1 ID

### Step 2 — Pipeline scope propagation (pipeline.py)
- Add `_build_scope_filter()` helper
- Replace `parse_meeting_scope()` call with `_build_scope_filter(understanding)`
- Update `retrieve_summary_chunks()` call to pass `scope_meeting_ids`
- Update `topic_summary_retrieve()` call to pass `scope_meeting_ids`
- **Test:** Pipeline logs show `scope=meeting (1 meetings)` for scoped queries

### Step 3 — Compound fallback fix (retriever.py)
- Change threshold from 3 to 0 in `compound_retrieve()`
- **Test:** "What did Harsh say about AI in previous meeting?" returns Harsh's chunks only,
  even if he said only 1 thing

### Step 4 — `topic_summary_retrieve()` signature change (retriever.py + pipeline.py)
- Add `scope_meeting_ids` param, remove `date_where` param
- Update pipeline.py call site
- **Test:** "What was the overall AI discussion in the previous meeting?" fetches
  only previous meeting's chunks, not all meetings

---

## 8. Queries to Test After Each Step

### Meeting-Level (must all work after Phase 1)

```
"What was discussed in the previous meeting?"
→ scope=meeting (1 meeting) | mode=summary | chunks only from that meeting

"What did Harsh discuss about AI in previous 2 meetings?"
→ scope=meeting (2 meetings) | mode=compound | Harsh's chunks from those 2 meetings only

"How many questions were raised in the last meeting?"
→ scope=meeting (1 meeting) | mode=analytical | count from that meeting only

"What did Bhavneet commit to in the first meeting?"
→ scope=meeting (1 meeting) | mode=compound | Bhavneet's commitment chunks from meeting 1 only

"Which topic is most important in the previous meeting?"
→ scope=meeting (1 meeting) | mode=hybrid | diverse chunks from that meeting only

"What was the AI architecture discussion in the last meeting?"
→ scope=meeting (1 meeting) | mode=topic_summary | AI chunks from that meeting only
```

### Project-Level (must still work after Phase 1 — regression check)

```
"What decisions were made across all meetings?"
→ scope=project | mode=hybrid | all meetings searched

"Who spoke the most in this project?"
→ scope=project | mode=contribution | all meetings counted

"How has AI architecture evolved?"
→ scope=project | mode=timeline | per-meeting search

"What did Simarjot commit to, with traces?"
→ scope=project | mode=compound | all Simarjot commitment chunks
```

---

## 9. What Phase 2 (Project-Level) Will Cover

Phase 2 is NOT part of this plan — document it here to avoid scope creep.

| Query Type | What Needs Work |
|-----------|----------------|
| Cross-meeting synthesis | timeline_retrieve needs better context merging |
| Contribution analysis | Already works via contribution_retrieve() |
| Project-wide topic summary | Already works via topic_summary_retrieve() |
| "All decisions across project" | Already works via hybrid + decision intent |
| "Bhavneet across all meetings" | Already works via compound (no scope) |

Phase 2 main challenge: LLM synthesis quality when context spans many meetings —
not a retrieval problem, a prompt engineering problem.

---

## 10. Summary of Changes

| File | Lines Changed | Risk |
|------|--------------|------|
| `query_intent.py` | ~15 lines | Low — adds fields, modifies return of one function |
| `pipeline.py` | ~10 lines | Low — removes one call, adds helper, updates 2 call sites |
| `retriever.py` | ~15 lines | Low — compound threshold change + topic_summary signature |
| `builder.py` | ~10 lines | Low — adds optional param with backward-compatible default |

Total: ~50 lines of changes across 4 files.
No schema changes. No re-ingestion. No new dependencies.
