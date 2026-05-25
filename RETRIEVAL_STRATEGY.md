# Retrieval Strategy — AI Meeting Intelligence

> **Purpose:** For each routing mode, this doc explains:
> the example query → routing rule that fires → retrieval function called →
> step-by-step what happens inside → why this strategy was chosen → known gaps.

---

## How the System Works (Big Picture)

```
User Query
    │
    ▼
understand_query()          ← LLM fills semantic fields + Python fills syntactic dims
    │
    ▼
_apply_routing()            ← 3-function priority chain picks retrieval_mode
    │
    ▼
_retrieve_for_understanding()   ← dispatches to 1 of 8 retrieval functions
    │
    ├── metadata    → handle_metadata_query()
    ├── contribution → contribution_retrieve()
    ├── analytical  → analytical_retrieve()
    ├── compound    → compound_retrieve()
    ├── topic_summary → topic_summary_retrieve()
    ├── summary     → retrieve_summary_chunks()
    ├── timeline    → retrieve_timeline_documents()
    └── hybrid      → hybrid_retrieve()
         │
         ▼
    (rerank → expand context → build prompt → LLM call)
```

The routing decision is made **before** any DB call. The retrieval mode is the single
most important decision — the wrong mode means wrong chunks, and the LLM cannot
recover from bad retrieval.

---

## Mode 1 — `metadata`

### Example Query
> "What are the meeting timings?" / "How many meetings are in this project?" / "How many people attended?"

### Routing Rule That Fires
```python
_structural_route():
    if _METADATA_RE.search(q): return "metadata", "structural_metadata"
```
`_METADATA_RE` matches: `timings`, `how many meetings`, `how many people`, `how many speakers`, `attendees`, `participants`, `when did meetings start`, etc.

**Why `_structural_route` fires first:**
These are structural questions about the project itself — not about what was *said*. There is no
transcript content to retrieve. The answer lives in structured metadata (dates, attendee lists,
meeting counts). Sending this to vector search would return random transcript chunks with no
answer to the question.

### What Happens Inside
```
handle_metadata_query(query, project_id)
    │
    ├── Is it a timing query? → Read meeting_date + start_time from ChromaDB metadata
    ├── Is it a count query?  → Count unique meeting_ids or speaker_names in metadata
    └── Return structured answer directly (no LLM needed)
```

**No vector search. No LLM. Pure metadata read.**

### Why This Strategy
| Reason | Detail |
|--------|--------|
| **Questions are about the DB, not content** | "How many meetings?" → count meeting_ids. No transcript content answers this. |
| **Zero hallucination risk** | LLM has 0 chance to make up a number when you give it the exact count. |
| **Fastest path** | No embedding generation, no vector lookup, no BM25 — O(N) metadata scan. |

### Known Gaps
- Does not yet handle: "What time did the previous meeting end?" (end_time parsing not wired)
- "Who attended the April 20th meeting?" — needs date-scoped attendee lookup (currently falls back to listing all speakers)

---

## Mode 2 — `contribution`

### Example Query
> "Who spoke the most in this project?" / "Who was most active across all meetings?" / "Rank speakers by contribution"

### Routing Rule That Fires
```python
_structural_route():
    if u.dimensions.is_contribution or _CONTRIBUTION_RE.search(q):
        return "contribution", "contribution_volume"
```
`_CONTRIBUTION_RE` matches: `spoke the most`, `spoken the most`, `most active`, `contribut` (prefix).

**Why same `_structural_route`:**
Like metadata queries, this is structural — it asks about the *shape* of participation, not the
*content* of conversation. The answer is: "who has the most transcript chunks?" That's a metadata
count, not a semantic search problem.

### What Happens Inside
```python
contribution_retrieve(project_id, date_where)
    │
    ├── collection.get(project_id filter)      ← fetch ALL metadatas (no text, no vectors)
    ├── Skip is_meeting_summary chunks          ← don't count summary chunks as speaking
    ├── Group by speaker_name:
    │     chunk_count += 1 per chunk
    │     meetings.add(meeting_id) per chunk
    └── Sort by chunk_count descending
    → Returns: {ranked_speakers: [{name, chunk_count, meeting_count}, ...], total_speakers}
```

**Returns a dict (not documents) → `_handle_structured_result()` formats it.**

### Why This Strategy
| Reason | Detail |
|--------|--------|
| **chunk_count = speaking volume proxy** | Each transcript chunk = ~30–60 seconds of speech. More chunks = more speaking time. |
| **No vector search needed** | The answer is purely "who appears most in metadata" — a GROUP BY query. |
| **Consistent across meeting scopes** | `date_where` can scope to specific meetings; same logic applies whether project-wide or single-meeting. |

### Known Gaps
- Chunk count ≠ actual speaking time (some chunks are longer than others)
- Does not differentiate: did the speaker ask questions vs give answers?
- `date_where` scoping only works if the `meeting_date`/`meeting_id` filter is passed — not yet wired for all scope patterns

---

## Mode 3 — `analytical`

### Example Query
> "How many questions were raised in the previous meeting?" / "Total commitments made in the last 3 meetings?" / "How many issues did Harsh raise?"

### Routing Rule That Fires
```python
_shape_route():
    if u.dimensions.is_count:
        if u.dimensions.has_temporal: return "analytical", "scoped_count"
        if u.signal_filter and not u.dimensions.has_topic: return "analytical", "signal_count"
        if u.named_speaker: return "analytical", "named_speaker_count"
        return "analytical", "any_count_fallback"
```

**Why `_shape_route` handles counts:**
`is_count` is set by Python regex (`how many`, `total X`, `number of`, `count`). Once Python sees
a count query, it must route to a function that counts reliably. The LLM **cannot count** — it
hallucinates numbers from transcript text. Only a DB count is trustworthy.

**Sub-rules:**
- `scoped_count` = is_count + has_temporal (e.g. "in the previous meeting")
- `signal_count` = is_count + signal_filter set (e.g. "questions raised", "commitments made")
- `named_speaker_count` = is_count + named_speaker (e.g. "how many issues did Harsh raise?")
- `any_count_fallback` = is_count with nothing else specific

### What Happens Inside
```python
analytical_retrieve(project_id, signal_filter, date_where, named_speaker)
    │
    ├── collection.get(project_id + optional speaker + optional date_where)
    │       ← direct metadata fetch, NO vector search
    ├── Exclude is_meeting_summary chunks
    ├── If signal_filter: keep only chunks where contains_{signal}=True
    │       e.g. signal_filter="question" → keep only contains_question=True chunks
    └── Count:
          total_chunks, signal_count,
          meeting_count + meeting_titles,
          speaker_count + speaker_names
    → Returns: {total_chunks, signal_count, meeting_count, meetings, speakers, ...}
```

**Returns a dict (not documents) → `_handle_structured_result()` formats it.**

### Full Walk-Through Example

**Query:** `"How many questions did Bhavneet raise in the previous meeting?"`

```
Step 1 — Routing:
  is_count=True ("how many")
  has_temporal=True ("previous meeting" → parse_meeting_scope fires)
  → Rule: scoped_count → mode="analytical"

Step 2 — DB filter built:
  project_id + speaker_name="Bhavneet Mhajan" + meeting_id="<previous-meeting-id>"

Step 3 — analytical_retrieve():
  Fetch all Bhavneet's chunks from that meeting
  Keep only contains_question=True
  Count = 3

Step 4 — _handle_structured_result():
  context = "Count of question: 3\nAcross 1 meeting(s): April 22nd Meeting\nFiltered to speaker: Bhavneet Mhajan"
  → LLM formats into: "Bhavneet raised 3 questions in the previous meeting: (1)..."
```

### Why This Strategy
| Reason | Detail |
|--------|--------|
| **LLM cannot count reliably** | Give LLM 20 transcript chunks and ask "how many questions?" — it guesses 4, actual is 7. |
| **ChromaDB metadata is authoritative** | `contains_question=True` is set at ingest time by regex detection — same data, same answer every time. |
| **LLM only formats, never counts** | The count is in the context string. LLM writes a sentence around it. Count doesn't change. |

### Known Gaps
- `contains_question`, `contains_commitment`, `contains_decision` are set by regex at ingest — if a question was phrased unusually, it may not be tagged → undercounting
- "How many AI architectures were discussed?" → `has_topic=True` → falls to `semantic_count` → `topic_summary` mode (correct — no metadata flag for "AI architectures")
- Count queries with topic (`"Total questions about AI architecture?"`) are handled by `topic_summary` mode (see Mode 5), not analytical — the topic qualifier requires semantic search first

---

## Mode 4 — `compound`

### Example Query
> "What did Bhavneet say about AI architecture?" / "What commitments did Harsh make?" / "What was Simarjot's feedback in the April 20th meeting?"

### Routing Rule That Fires
```python
_content_route():
    if u.named_speaker: return "compound", "compound_any_speaker"
```

This fires for **any query with a named speaker that isn't a count query** — the widest and
most important fix in the new architecture.

**Why the old approach was wrong:**
Old system applied speaker filter BEFORE vector search:
```
hybrid_retrieve(query, hard_filters={"speaker_name": "Bhavneet"})
    → Vector search can only see Bhavneet's chunks
    → "AI architecture" query scores Bhavneet's off-topic chunks high
    → Topic relevance is meaningless — you're ranking irrelevant chunks
```

**Why the new approach is right:**
```
compound_retrieve():
    Pass 1: Get ALL of Bhavneet's chunks from DB (guaranteed corpus)
    Pass 2: BM25 keyword search within those chunks → topic-relevant ones float up
    Pass 3: Dense vector search filtered to Bhavneet → semantic match
    RRF merge: combine Pass 2 + Pass 3 → best chunks from both signals
```

### What Happens Inside (3-Pass Detail)

```python
compound_retrieve(query, project_id, named_speaker, signal_filter, date_where)
    │
    ├── Pass 1: _fetch_project_corpus(project_id, {speaker_name: "Bhavneet"}, date_where)
    │       ← Direct DB fetch of ALL Bhavneet's chunks (no vector search)
    │       ← If date_where set: only from scoped meeting(s)
    │       ← If 0 chunks found: FALLBACK to broad hybrid_retrieve
    │
    ├── Pass 2: _bm25_search(query, speaker_corpus, k=25)
    │       ← BM25Okapi keyword search within Bhavneet's chunks only
    │       ← Good for: exact terms ("AI architecture", "hybrid search")
    │       ← Tokenization: lowercase + acronym normalization + punctuation removal
    │
    ├── Pass 3: vectorstore.similarity_search(query, filter={speaker_name:"Bhavneet"}, k=25)
    │       ← Dense vector search scoped to Bhavneet + date_where
    │       ← Good for: semantic meaning ("building the system" matches "AI architecture")
    │
    ├── RRF merge: combine BM25 ranks + dense ranks
    │       ← score = 1/(60+rank_bm25) + 1/(60+rank_dense)
    │       ← Chunks appearing in both lists get highest score (double boost)
    │
    ├── Apply signal_filter (if set):
    │       ← signal_filter="commitment" → keep only contains_commitment=True chunks
    │       ← If 0 signal chunks found: return unfiltered speaker chunks
    │
    └── Return top-25 speaker chunks, topic-ranked
```

### Full Walk-Through Example

**Query:** `"What did Bhavneet say about hybrid search in the last meeting?"`

```
Step 1 — Routing:
  named_speaker = "Bhavneet Mhajan" (LLM extracted)
  is_count = False
  has_temporal = True ("last meeting" → scope resolved to meeting_id=X)
  → Rule: compound_any_speaker → mode="compound"

Step 2 — compound_retrieve():
  Pass 1: Fetch all Bhavneet's chunks from meeting X → 12 chunks
  Pass 2: BM25 over 12 chunks for "hybrid search" → top 5: chunks about hybrid, retrieval, dense+BM25
  Pass 3: Dense search scoped to Bhavneet + meeting X → top 5: semantic matches
  RRF: Chunk about "we should use hybrid search for this" scores highest (in both BM25 and dense top-3)

Step 3 — pipeline:
  Rerank 8 results → top 5 most relevant
  Build context → LLM answers with Bhavneet's exact words about hybrid search
```

### Why This Strategy
| Reason | Detail |
|--------|--------|
| **Speaker corpus is guaranteed** | Pass 1 fetches ALL speaker chunks — nothing falls outside the top-40 window |
| **Topic scoring is now meaningful** | BM25 + dense search within speaker corpus finds the most topic-relevant chunks |
| **Both keyword and semantic signals used** | BM25 catches "hybrid search" literally; dense catches "search strategy" semantically |
| **Signal filter applied LAST** | Only filter for commitments/questions after finding the right chunks — otherwise you miss relevant context |
| **Fallback prevents empty responses** | If speaker isn't in the project, broad hybrid search runs so LLM can say "they weren't found" |

### Known Gaps
- If speaker name has unusual spelling ("Bhavnit" vs "Bhavneet"), LLM extraction may miss it → falls to `_python_detect_speaker()` fallback (2-level: full name, first name)
- Very short speaker corpus (<3 chunks) may give poor BM25 results — needs minimum corpus size handling
- Date scoping: if `date_where` is wrong (wrong meeting resolved), all 3 passes search the wrong meeting

---

## Mode 5 — `topic_summary`

### Example Query
> "Summarize the AI architecture discussion" / "What was the overall conversation about hybrid search?" / "How many AI architectures were discussed?" (semantic count)

### Routing Rule That Fires
```python
_content_route():
    if u.dimensions.has_topic:
        if u.signal_filter: return "hybrid", "signal_with_topic"  # KEY: signal queries stay in hybrid
        if u.dimensions.has_temporal: return "topic_summary", "scoped_topic_summary"
        if u.dimensions.is_cross_meeting: return "topic_summary", "cross_meeting_topic_summary"
        return "topic_summary", "topic_only_summary"
```

Also fires from `_shape_route` when `is_count=True and has_topic=True`:
```python
_shape_route():
    if u.dimensions.is_count and u.dimensions.has_topic: return "topic_summary", "semantic_count"
```

**Why not just use hybrid_retrieve for topic queries?**
```
Problem with project-wide hybrid for topic queries:
    hybrid_retrieve("AI architecture", project_id)
    → Searches ALL chunks across ALL meetings
    → Meeting 3 has 50 AI architecture chunks (it was the main topic)
    → Meeting 1 has 5 AI architecture chunks (brief mention)
    → RRF scores Meeting 3 chunks highest, Meeting 1 is drowned out
    → You get a deep-dive on Meeting 3, barely anything from Meeting 1
    → PM asks "summarize AI architecture discussion" and gets only Meeting 3's view
```

**The fix: per-meeting search, then merge:**
```
topic_summary_retrieve():
    For each meeting:
        hybrid_retrieve(topic, hard_filters={meeting_id: X}, k=8)
    Merge all results chronologically
    → Each meeting contributes up to 8 chunks equally
    → PM gets the full evolution across all meetings
```

### What Happens Inside

```python
topic_summary_retrieve(topic, project_id, scope_meeting_ids, k_per_meeting=8)
    │
    ├── Get all meeting_ids for project (from project_store)
    ├── Filter to scope_meeting_ids if provided
    │
    ├── For each meeting_id:
    │     hybrid_retrieve(topic, project_id, hard_filters={meeting_id: mid}, k=8)
    │         ← BM25 + dense search, but ONLY within this one meeting's chunks
    │         ← Returns up to 8 most relevant chunks about the topic from this meeting
    │
    ├── Collect all results (N meetings × up to 8 chunks each)
    └── Sort by (meeting_date, start_time) → chronological order
    → Returns: all topic-relevant chunks, sorted by time, all meetings represented
```

### Full Walk-Through Example

**Query:** `"What was the overall conversation about AI architecture?"`

```
Step 1 — Routing:
  intent_type = "summary_query" (LLM classifies as summary)
  has_topic = True ("AI architecture" detected)
  is_count = False
  named_speaker = None
  → Rule: topic_only_summary → mode="topic_summary"

Step 2 — topic_summary_retrieve():
  Project has 3 meetings: April 10, April 17, April 22
  Meeting 1 (Apr 10): hybrid_retrieve("AI architecture", {meeting_id: M1}, k=8)
    → 4 chunks: "we discussed using LLMs", "transformer vs traditional NLP", ...
  Meeting 2 (Apr 17): hybrid_retrieve("AI architecture", {meeting_id: M2}, k=8)
    → 6 chunks: "Bhavneet proposed hybrid approach", "team debated RAG vs fine-tuning", ...
  Meeting 3 (Apr 22): hybrid_retrieve("AI architecture", {meeting_id: M3}, k=8)
    → 7 chunks: "final decision: RAG with Gemini", "Harsh committed to implementation", ...
  
  Merge + sort: 17 chunks in chronological order
  
Step 3 — pipeline:
  Skip rerank (mode=topic_summary → rerank disabled, preserves chronological order)
  Build context (17 chunks → trimmed to top 10 after expand_context)
  → LLM writes: "The AI architecture discussion evolved across 3 meetings:
     Initially (Apr 10), the team explored LLMs and traditional NLP...
     By Apr 17, Bhavneet proposed hybrid search...
     Final decision (Apr 22): RAG with Gemini..."
```

### Why This Strategy
| Reason | Detail |
|--------|--------|
| **Per-meeting search = equal representation** | Each meeting contributes equally, no matter how much of its content is about the topic |
| **Chronological merge = narrative coherence** | Chunks sorted by time → LLM can tell the story of how the topic evolved |
| **Rerank disabled** | Reranker would sort by relevance, breaking the timeline. For topic summaries, time order is the right order. |
| **Scoped variant works too** | `scope_meeting_ids` filters which meetings to search — same strategy, smaller scope |

### Known Gaps
- k_per_meeting=8 is fixed — topics discussed very briefly (2 chunks/meeting) and topics discussed extensively (30 chunks) both get 8. May miss dense topics or over-include sparse ones.
- "How many AI architectures were discussed?" routes here (semantic_count). LLM then counts from focused context — more accurate than analytical, but still LLM-counted (imprecise if context is ambiguous)
- No rerank means some irrelevant chunks within a meeting may survive if hybrid_retrieve's top-8 includes off-topic results

---

## Mode 6 — `summary`

### Example Query
> "Give me the summary of the previous meeting" / "What was discussed in the last meeting?" / "What was the agenda for the April 22nd meeting?"

### Routing Rule That Fires
```python
_content_route():
    if u.needs_summary: return "summary", "meeting_summary"
    if u.dimensions.is_list_request: return "summary", "list_request_summary"
    if u.dimensions.has_temporal and _CONTENT_RE.search(q): return "summary", "meeting_content_request"
```

`needs_summary` is set by `_python_infer_needs_summary()` (Python, not LLM):
- Fires when: query contains "summary", "summarize", "overview", "recap", "what happened", "what was discussed"
- **Blocked when**: `has_topic=True` (those go to topic_summary) or `named_speaker` set (those go to compound)

`is_list_request` fires on: "What topics were discussed?" / "What points were covered?"

`_CONTENT_RE` catches: "what was discussed/covered/happened in that meeting?" even when `needs_summary` is False.

### What Happens Inside

```python
retrieve_summary_chunks(project_id, query, scope_meeting_ids)
    │
    ├── collection.get(project_id + is_meeting_summary=True)
    │       ← Fetches ONLY pre-written summary chunks
    │       ← These were generated by Fireflies.ai and ingested separately
    │       ← NOT transcript content — pre-written overviews
    │
    ├── Sort by meeting_date chronologically
    │
    ├── Fast path: scope_meeting_ids provided?
    │     ← Filter to requested meetings directly (no extra DB call)
    │     ← scope_meeting_ids comes from QueryUnderstanding, resolved before LLM call
    │
    └── Fallback: extract_month_day(query)
          ← If query has "April 22nd", find meeting within ±1 day
          ← Returns notice if approximate match (e.g. "No meeting on 22nd, showing 21st")
    → Returns: (list[Document], notice_string | None)
```

### Full Walk-Through Example

**Query:** `"What was the agenda for the previous meeting?"`

```
Step 1 — scope resolution (before LLM call):
  parse_meeting_scope("previous meeting") → meeting_id = "M3" (most recent)
  scope_meeting_ids = ["M3"]

Step 2 — Routing:
  needs_summary = True (Python detects "agenda" → not in explicit regex, but LLM sets needs_summary)
  has_topic = False (no specific topic)
  named_speaker = None
  → Rule: meeting_summary → mode="summary"

Step 3 — retrieve_summary_chunks():
  Fetch all summary chunks for project → 3 summary docs (one per meeting)
  scope_meeting_ids = ["M3"] → filter to M3's summary chunk only
  Return: [summary chunk for April 22nd meeting]

Step 4 — pipeline:
  Skip rerank (mode=summary)
  Build context (1 summary chunk)
  → LLM answers: "The agenda for the previous meeting (April 22nd) covered:
     1. Finalizing AI architecture decision
     2. Harsh's hybrid search implementation plan
     3. Next sprint planning"
```

### Why This Strategy
| Reason | Detail |
|--------|--------|
| **Pre-written summaries are more coherent** | Fireflies.ai summary chunks are structured overviews, not raw transcript fragments |
| **Scope is pre-resolved** | `scope_meeting_ids` from QueryUnderstanding means no extra DB call to figure out "previous meeting" |
| **Faster than transcript retrieval** | Summary chunks are 1 per meeting vs 100s of transcript chunks per meeting |
| **No rerank needed** | Summary chunks are already high-quality signals — no need to reorder |

### Known Gaps
- Summary chunks are generated by Fireflies.ai — if a meeting has no AI-generated summary, this mode returns 0 docs
- Summary quality depends on Fireflies — may miss nuances present in raw transcript
- "What topics were discussed?" routes here and works fine; but "What were the detailed discussions about X?" should go to topic_summary (covered by `has_topic` guard)
- `_MEETING_SCOPE_PREFIX` is injected when `scope_type="meeting"` — tells LLM "this is ONE meeting, don't summarize the whole project"

---

## Mode 7 — `timeline`

### Example Query
> "How has the AI approach evolved across meetings?" / "Which came first — OCA issue or fixed assets issue?" / "Show me the progression of the hybrid search decision"

### Routing Rule That Fires
```python
_shape_route():
    if u.intent_type.value == "attribution_query": return "timeline", "attribution_origin"

_content_route():
    if u.temporal_focus == "cross_meeting" or u.dimensions.is_cross_meeting:
        return "timeline", "cross_meeting_timeline"
```

`attribution_query` is the LLM's intent when the question is about temporal origin: "which came first?", "who first raised?", "when was X first mentioned?"

`is_cross_meeting` / `temporal_focus="cross_meeting"` is set by LLM when it detects the user wants to track something evolving across meetings (e.g. "across all meetings", "over time", "evolution of").

### What Happens Inside

```python
retrieve_timeline_documents(query, project_id, k_per_meeting=6, scope_meeting_ids)
    │
    ├── Get all meeting_ids for project (from project_store)
    ├── Filter to scope_meeting_ids if provided
    │
    ├── For each meeting_id:
    │     retrieve_documents(query, project_id, filters={meeting_id: mid}, k=6)
    │         ← DENSE-ONLY search (no BM25) within each meeting
    │         ← Returns up to 6 semantic matches per meeting
    │
    ├── Collect all results (N meetings × up to 6 chunks each)
    └── Sort by meeting_date ascending → chronological timeline
    → Returns: list[Document] in chronological order
```

**Key difference from topic_summary_retrieve:** Uses `retrieve_documents()` (dense-only, no BM25) vs `hybrid_retrieve()` (dense + BM25).

### Full Walk-Through Example

**Query:** `"How has the AI architecture approach evolved across meetings?"`

```
Step 1 — Routing:
  temporal_focus = "cross_meeting" (LLM detects "across meetings" + "evolved")
  → Rule: cross_meeting_timeline → mode="timeline"

Step 2 — retrieve_timeline_documents():
  For meeting Apr 10: dense search "AI architecture evolution" → 6 chunks
  For meeting Apr 17: dense search "AI architecture evolution" → 6 chunks
  For meeting Apr 22: dense search "AI architecture evolution" → 6 chunks
  Sort chronologically: Apr 10 → Apr 17 → Apr 22 (18 chunks total)

Step 3 — pipeline:
  Rerank 18 results → top 10 most relevant (but chronological sort applied after rerank)
  → LLM tells the story: "AI architecture evolved:
     Apr 10: Team discussed LLM options, no decision made
     Apr 17: Bhavneet proposed hybrid RAG approach
     Apr 22: Final decision — RAG with Gemini 2.5 Flash"
```

### Why This Strategy
| Reason | Detail |
|--------|--------|
| **Per-meeting search = equal timeline coverage** | Same reason as topic_summary — project-wide search would over-represent the most similar meeting |
| **Sorted by date = readable narrative** | Timeline questions need a story arc. Relevance-ranked order would jumble the timeline. |
| **Dense-only (no BM25)** | Timeline queries tend to be semantically complex ("evolved", "progression", "over time") — BM25 would fail on these semantic phrases |

### Known Gaps
- Dense-only misses exact term matches (BM25 advantage) — "OCA issue evolution" might miss early mentions if they used different phrasing
- No attribution analysis yet — "which came first?" requires scanning all chunks chronologically and finding the FIRST mention. Current pipeline just retrieves relevant chunks, not necessarily the earliest one.
- k_per_meeting=6 (less than topic_summary's 8) — may miss important chunks in meetings with many relevant chunks

---

## Mode 8 — `hybrid`

### Example Query
> "What decisions were made about the database?" / "Did Harsh commit to finishing by Friday?" (with signal_filter) / "What did the team discuss about authentication?" (general)

### Routing Rule That Fires
```python
_content_route():
    if u.dimensions.has_topic:
        if u.signal_filter: return "hybrid", "signal_with_topic"  # signal + topic
    # ...
    return "hybrid", "hybrid_default"    # fallback when nothing else matches
```

Hybrid is the **default mode** — it fires when:
1. A topic query has a signal_filter set (e.g. "questions about AI architecture?" → has_topic=True + signal_filter="question" → hybrid with hard_filter)
2. Nothing else matched (general queries, yes/no questions without speaker, etc.)

**Why signal+topic queries stay in hybrid (not topic_summary):**
```
topic_summary_retrieve does NOT apply metadata filters (contains_question, contains_commitment).
It does hybrid_retrieve per meeting but never passes hard_filters for signal types.
If you route "What questions were raised about AI?" to topic_summary:
    → You get AI architecture chunks (correct topic)
    → But they include non-question chunks too (Bhavneet's explanations, decisions, etc.)
    → LLM then has to figure out which ones were questions → imprecise

Correct approach: route to hybrid with signal hard_filter:
    hard_filters = {"contains_question": True}
    → Only question chunks are retrieved
    → Then filtered further by topic relevance via BM25 + dense
    → LLM gets only question chunks about AI architecture
```

### What Happens Inside

```python
hybrid_retrieve(query, project_id, hard_filters, date_where, k=25)
    │
    ├── Stage 1a: Dense search
    │     filter = project_id + hard_filters + date_where
    │     vectorstore.similarity_search(query, k=25, filter=filter)
    │     → Up to 25 semantic matches, within constraints
    │
    ├── Stage 1b: BM25 search
    │     corpus = _fetch_project_corpus(project_id, hard_filters, date_where)
    │     ← Fetch ALL chunks matching hard_filters (no vector search)
    │     ← Build in-memory BM25 index from these chunks
    │     bm25_docs = _bm25_search(query, corpus, k=25)
    │     → Up to 25 keyword matches
    │
    ├── Stage 2: RRF merge
    │     score = 1/(60+rank_dense) + 1/(60+rank_bm25)
    │     Chunks in BOTH lists → highest combined score
    │     → Ranked list of all unique chunks
    │
    └── Return top-25 after merge
```

### Full Walk-Through Example

**Query:** `"What questions were raised about AI architecture?"`

```
Step 1 — Routing:
  has_topic = True ("AI architecture")
  signal_filter = "question" (LLM detected "questions were raised")
  → Rule: signal_with_topic → mode="hybrid"

Step 2 — pipeline builds hard_filters:
  hard_filters = {"contains_question": True}
  date_where = None (no temporal scope)

Step 3 — hybrid_retrieve():
  Stage 1a Dense:
    filter = {project_id=X AND contains_question=True}
    → 25 question chunks, semantically closest to "AI architecture questions"
  Stage 1b BM25:
    corpus = ALL question chunks (contains_question=True) in project
    BM25 search "AI architecture questions" over corpus
    → 25 keyword matches (chunks with "AI", "architecture", "question" words)
  Stage 2 RRF:
    Chunk "Bhavneet asked: should we use transformer-based or retrieval-based AI?" → in both top-5
    → Highest combined score → top result

Step 4 — rerank + LLM:
  Top 10 chunks, all are question chunks about AI architecture
  → LLM answers: "3 questions were raised about AI architecture:
     1. Bhavneet asked about transformer vs retrieval approach...
     2. Harsh questioned the latency impact...
     3. Team asked about fine-tuning costs..."
```

### Why This Strategy (Default)
| Reason | Detail |
|--------|--------|
| **BM25 catches exact terms** | "hybrid search", "OCA code", "CE classification" — these specific terms score high in BM25 even if semantically distant |
| **Dense catches meaning** | "What was the system design decision?" matches "we chose RAG over fine-tuning" semantically |
| **RRF combines both signals** | A chunk appearing in both top-25 lists gets double boost — highest confidence retrieval |
| **hard_filters narrow before scoring** | For signal queries, only eligible chunks are searched — BM25 index and dense filter both see the same pre-filtered corpus |

### Known Gaps
- For queries without any hard_filters, the entire project corpus is the BM25 space — memory scales with project size
- `date_where` scoping works for both stages, but BM25 corpus must be re-built per query (no caching)
- When `hard_filters` + `date_where` return 0 docs: dense stage fails silently, BM25 returns empty → LLM gets no context → wrong answer

---

## Summary Table — All 8 Modes

| Mode | Routing Trigger | Retrieval Function | Vector Search? | BM25? | DB Count? | Returns |
|------|----------------|-------------------|----------------|-------|-----------|---------|
| `metadata` | timing/count-of-meetings phrases | `handle_metadata_query()` | ❌ | ❌ | ✅ | Direct answer |
| `contribution` | "spoke most", is_contribution | `contribution_retrieve()` | ❌ | ❌ | ✅ | Ranked dict |
| `analytical` | is_count + (temporal/signal/speaker) | `analytical_retrieve()` | ❌ | ❌ | ✅ | Count dict |
| `compound` | named_speaker + not is_count | `compound_retrieve()` | ✅ (dense) | ✅ (BM25) | ❌ | Documents |
| `topic_summary` | has_topic + no signal_filter | `topic_summary_retrieve()` | ✅ per-meeting | ✅ per-meeting | ❌ | Documents |
| `summary` | needs_summary OR list_request | `retrieve_summary_chunks()` | ❌ | ❌ | ❌ | Summary docs |
| `timeline` | is_cross_meeting OR attribution | `retrieve_timeline_documents()` | ✅ per-meeting | ❌ | ❌ | Documents |
| `hybrid` | signal+topic OR default | `hybrid_retrieve()` | ✅ (dense) | ✅ (BM25) | ❌ | Documents |

---

## Post-Retrieval Steps (Applies to document-returning modes)

Once documents are returned, the pipeline applies these steps before the LLM call:

```
1. Rerank        → rerank_documents() — scores by (intent, topic_hint, speaker_hint)
                   SKIPPED for: summary, topic_summary (chronological order must be preserved)

2. Expand context → expand_context() — fetches prev/next neighboring chunks for top-5 docs
                   SKIPPED for: summary, topic_summary

3. Chrono sort   → sort by (meeting_date, start_time)
                   APPLIED for: compound, topic_summary, timeline modes

4. Trim          → take top 10 documents (after expansion)

5. build_context() → format chunks into numbered context string

6. build_prompt() → inject output_format prefix (COUNT/YESNO/LIST/PROSE) + template

7. call_gemini() → LLM generates answer from context + prompt
```

---

## Why Meeting Scope Is Resolved Before Routing

One architectural decision worth explaining: `scope_meeting_ids` is resolved **before** the LLM call, not inside the retrieval function.

```
Old flow (slow + duplicated):
    understand_query() → (LLM call)
    _retrieve_for_understanding():
        summary mode calls extract_month_day() to figure out "previous meeting"
        topic_summary mode makes its own DB call to get meeting list
        analytical mode has its own scope resolution
    → 3 different functions all re-solving "which meeting is the previous meeting?"

New flow (fast + single source of truth):
    parse_meeting_scope(query, project_id)  ← ONE call, result stored in understanding
    understand_query() → LLM call (scope_meeting_ids already in QueryUnderstanding)
    _retrieve_for_understanding():
        All functions receive scope_meeting_ids already resolved
    → 1 DB call total for scope resolution, result shared across all retrieval modes
```

This is why `scope_meeting_ids: Optional[list[str]]` appears in every retrieval function signature — it's the pre-resolved scope passed from routing, not computed inside the function.

---

## Current Focus: Meeting-Scope Retrieval Quality

Routing is now solid (21/21 queries route correctly). The next question is:
**"Are the RIGHT CHUNKS being retrieved within the correctly-scoped meeting?"**

Key areas to investigate:

| Issue | Question | Mode |
|-------|----------|------|
| Signal tag accuracy | Is `contains_commitment=True` set on all commitment chunks? Or does regex miss phrasing variants? | compound, analytical |
| k_per_meeting sizing | Is k=8 enough per meeting for topic_summary? What if topic spans 20 chunks? | topic_summary |
| BM25 corpus size | For compound mode, if speaker has 50 chunks, does BM25 find the right 10? | compound |
| Rerank quality | After retrieval, does the reranker promote the most answer-relevant chunks to top-5? | compound, hybrid |
| Context window | Do expand_context() neighbors add signal or noise? When do they hurt? | compound, hybrid |
