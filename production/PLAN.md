# Plan: Production Agent — Real Query Scenario Coverage

## Context

The production LangGraph pipeline has a working graph (`query_scope_node → agent → tools`), 4 tools, and a system prompt. However, the system prompt and tool docstrings were written generically — not validated against real PM queries.

The user provided 30 real-world scenarios across 3 categories. This plan maps every scenario to the correct tool flow, identifies the 5 gaps where the current system will fail or underperform, and specifies the exact changes needed to `prompts.py`, `tools.py`, and `graph.py`.

**Core principle:** The system prompt IS the classification logic. Clearer tool guidance = better tool selection = correct retrieval.

---

## Part 0: Tool Roles — What Each Tool Does and When

There are 5 tools. Each handles a completely different type of data access.

```
┌──────────────────────────────────────────────────────────────────────┐
│  TOOL              │ WHAT IT SEARCHES       │ RETURNS               │
├──────────────────────────────────────────────────────────────────────┤
│ search_transcripts │ Chunk content (text)   │ Matching chunks with  │
│                    │ via hybrid BM25+dense  │ speaker, time, meeting│
│                    │                        │ — the workhorse       │
├──────────────────────────────────────────────────────────────────────┤
│ get_meeting_       │ Pre-built summaries    │ 1 paragraph per       │
│ summaries          │ (1 per meeting, stored │ meeting — high level  │
│                    │ at ingestion time)     │ overview only         │
├──────────────────────────────────────────────────────────────────────┤
│ list_meetings      │ Meeting metadata only  │ Title + date +        │
│                    │ (no content)           │ number for each mtg   │
├──────────────────────────────────────────────────────────────────────┤
│ list_speakers      │ Speaker metadata only  │ Name + role +         │
│                    │ (no content)           │ chunk count per person│
├──────────────────────────────────────────────────────────────────────┤
│ count_signal_      │ Signal flags only      │ Exact integer count   │
│ chunks (NEW)       │ (contains_question,    │ — no content returned │
│                    │ contains_commitment..) │                       │
└──────────────────────────────────────────────────────────────────────┘
```

**When to use which tool — decision rules:**

- "How many meetings?" → `list_meetings`
- "Who attended / how many people?" → `list_speakers`
- "How many [signal type] chunks?" → `count_signal_chunks`
- "What was discussed / what did X say / what was decided?" → `search_transcripts`
- "Give me a summary / overview of a meeting?" → `get_meeting_summaries`

**Why `search_transcripts` is the workhorse:**
It is the ONLY tool that retrieves actual spoken content. All questions about "what was said", "what was discussed", "what did X commit to", "when did Y happen" need `search_transcripts`. The other 4 tools only return metadata or counts.

---

### How `search_transcripts` Works — All Parameter Combinations

`search_transcripts` has 4 parameters the LLM can set:
```
query         — what to search for semantically
k             — how many chunks to return (1–25)
speaker_name  — restrict to one person only
signal_filter — restrict to chunks with a specific signal flag
```

Plus 3 parameters injected invisibly from state (LLM never sets these):
```
scope_where   → limits to specific meeting(s) — set by query_scope_node
project_id    → always enforced — set at service entry
recommended_k → minimum k based on scope size
```

**The 12 call patterns across all scenarios:**

```
PATTERN 1 — Pure topic search (no filters)
  search_transcripts(query="AI architecture")
  → Retrieves any chunk about AI architecture, any speaker, all meetings
  → Used for: A3, A5, C3, C6, C7, C22

PATTERN 2 — Topic + decision signal
  search_transcripts(query="AI approach", signal_filter="decision")
  → Only chunks flagged contains_decision=True that match the topic
  → Used for: A2, C7, C26

PATTERN 3 — Topic + question signal
  search_transcripts(query="AI architecture", signal_filter="question")
  → Only question chunks about AI architecture
  → Used for: A4, C2

PATTERN 4 — Topic + commitment signal
  search_transcripts(query="hybrid search", signal_filter="commitment")
  → Only commitment chunks about hybrid search
  → Used for: A6

PATTERN 5 — Speaker only (no topic)
  search_transcripts(query="vision goals product", speaker_name="Bhavneet Mahajan")
  → All of Bhavneet's chunks — broad scan of what she said
  → Used for: A5, B7, B14

PATTERN 6 — Speaker + topic
  search_transcripts(query="AI", speaker_name="Harsh Vardhan")
  → Harsh's chunks that mention AI
  → Used for: C4, C5

PATTERN 7 — Speaker + commitment signal
  search_transcripts(query="AI", speaker_name="Harsh Vardhan", signal_filter="commitment")
  → Harsh's commitment chunks related to AI
  → Used for: C4, C11

PATTERN 8 — Speaker + question signal
  search_transcripts(query="AI architecture", speaker_name="Harsh Vardhan", signal_filter="question")
  → Harsh's question chunks about AI architecture
  → Used for: C2

PATTERN 9 — Meeting scope + topic (scope from query_scope_node)
  search_transcripts(query="topics discussed")   [scope_where=M10 injected]
  → Chunks from last meeting only, about topics discussed
  → Used for: B2, B9, B10, B17

PATTERN 10 — Meeting scope + signal
  search_transcripts(signal_filter="commitment")   [scope_where=M10 injected]
  → All commitment chunks in the last meeting only
  → Used for: B8, B15

PATTERN 11 — Meeting scope + speaker + signal
  search_transcripts(query="feedback", speaker_name="Bhavneet Mahajan")  [scope_where=M6]
  → Bhavneet's chunks in the April 20 meeting
  → Used for: B12, B19

PATTERN 12 — Multi-call for chronological comparison

  User query: "Which issue came first — OCA or fixed assets?"
  User query: "Which unresolved issue was discussed last?"

  IS MULTI-CALL ALREADY SUPPORTED? YES — built into the LangGraph graph.
  The graph runs: agent → tools → agent → tools → agent → END
  The LLM can make as many tool calls as it needs (up to MAX_ITERATIONS=6)
  before writing its final answer. Each tool result is added to the message
  history and the LLM reads all previous results before deciding what to call next.

  WHAT IS MISSING? The system prompt does not tell the LLM HOW to do comparison.
  It currently says "call multiple times" but does not explain to:
    (a) search each topic separately
    (b) look at meeting_date + start_time fields to determine chronological order

  HOW IT WORKS IN THE GRAPH (step by step):

  Turn 1 — LLM reads query, decides it needs 2 searches:
    Calls: search_transcripts(query="OCA issue")
    Tool returns:
      [1] Bhavneet Mahajan (08:14) — Nolocode Meeting #3 (2026-04-14)
          "The OCA classification was flagged as unclear..."
      [2] Harsh Vardhan (11:30) — Nolocode Meeting #3 (2026-04-14)
          "OCA still unresolved..."

  Turn 2 — LLM reads OCA results, now calls second search:
    Calls: search_transcripts(query="fixed assets issue")
    Tool returns:
      [1] Harsh Vardhan (22:30) — Nolocode Meeting #5 (2026-04-15)
          "Fixed assets formula is broken in the current setup..."

  Turn 3 — LLM has both results in its message history. No more tool calls.
  LLM compares:
    OCA:          Meeting #3, date=2026-04-14, time=08:14
    Fixed assets: Meeting #5, date=2026-04-15, time=22:30
    → April 14 < April 15 → OCA came first

  LLM writes final answer:
    "OCA came first — Bhavneet raised it in Meeting #3 on April 14th at
     (08:14). Fixed assets appeared later in Meeting #5 on April 15th at
     (22:30) when Harsh flagged the formula issue."

  WHAT NEEDS TO BE ADDED TO SYSTEM PROMPT:
    "COMPARISON queries ('which came first?', 'which was last?'):
     Search each topic separately. Look at the meeting_date and start_time
     shown in each result — these tell you exactly when something happened.
     Compare dates first (earlier date = earlier event), then timestamps
     if same date. Report the exact meeting + time for each."

  → Used for: C8 (OCA vs fixed assets), C9 (which issue was last)
```

PATTERN 13 — Two speakers, combined commitment + discussion

  User query: "What did Harsh and Bhavneet both commit to regarding AI?"
  User query: "What was the discussion between the client and the developer about AI architecture?"
  User query: "Compare what the client and developer said about the scope — did they align?"

  This is a MULTI-SPEAKER + MULTI-INTENT query. The user wants BOTH:
    (a) What Speaker A said/committed → need speaker_name="Harsh Vardhan"
    (b) What Speaker B said/committed → need speaker_name="Bhavneet Mahajan"

  IS THIS SUPPORTED? YES — the LLM makes 2–3 calls:

  Option A — 3 calls (most complete):
    Call 1: search_transcripts(query="AI commitment", speaker_name="Harsh Vardhan",    signal_filter="commitment")
    Call 2: search_transcripts(query="AI commitment", speaker_name="Bhavneet Mahajan", signal_filter="commitment")
    Call 3: search_transcripts(query="AI architecture discussion")  ← broader, no speaker filter
    → LLM synthesizes: what each person committed to + what the joint discussion covered

  Option B — 2 calls (if signals needed per person):
    Call 1: search_transcripts(query="AI architecture", speaker_name="Harsh Vardhan")
    Call 2: search_transcripts(query="AI architecture", speaker_name="Bhavneet Mahajan")
    → LLM reads both sides and compares / combines

  Option C — 1 call (if no speaker breakdown needed):
    search_transcripts(query="AI architecture commitment discussion", k=25)
    → Returns top chunks from all speakers about the topic
    → LLM sees both speakers' chunks in the result and synthesizes

  WHAT THE SYSTEM PROMPT NEEDS TO SAY:
    "TWO-SPEAKER queries ('what did X and Y both say/commit to?'):
     Search each speaker separately with speaker_name filter (Pattern 7).
     Then optionally do a combined search without speaker_name for broader context.
     In your answer, present each speaker's contribution separately before synthesizing."

  WHY SEPARATE CALLS ARE BETTER THAN ONE:
    - single call returns top 25 by relevance — might get 20 chunks from one speaker + 5 from another
    - separate calls with speaker_name guarantee equal coverage from each speaker
    - if one speaker barely mentioned the topic, you still get their 1-2 relevant chunks

  → Used for: any query mentioning 2+ people, comparing stances, or checking alignment

---

**What appears in every search_transcripts result:**
```
[1] Harsh Vardhan (14:22) — Nolocode Meeting #5  (2026-04-15)
    "We should go with a hybrid search approach combining BM25 and dense..."
```
Every chunk shows: speaker name, timestamp, meeting title, meeting date, chunk text.
This is why the LLM can answer "in which meeting and at what time" questions — the answer is inside the tool output.

---

## Part 1: Scenario Analysis — All 30 Queries Mapped

### Category A — Project Level (no scope)

| # | Query | Tool Flow | Gap? |
|---|---|---|---|
| A1 | How many meetings happen in this project | `list_meetings()` → count | ✅ None |
| A2 | What AI approach we decided to go with | `search_transcripts(query="AI approach decision", signal_filter="decision")` → if sparse, retry without signal | ✅ None |
| A3 | How many AI architectures are discussed | `search_transcripts(query="AI architecture", k=25)` → LLM reads chunks and counts **distinct** named approaches | ✅ None — semantic dedup, LLM reasoning |
| A4 | Total questions raised about AI architecture | `search_transcripts(query="AI architecture", signal_filter="question")` → count results shown | ✅ count in output header |
| A5 | Overview of what Bhavneet is trying to make | `search_transcripts(query="vision goals product", speaker_name="Bhavneet Mahajan", k=20)` + `get_meeting_summaries()` | ✅ None |
| A6 | When/where did Harsh commit to hybrid search | `search_transcripts(query="hybrid search", speaker_name="Harsh Vardhan", signal_filter="commitment")` | ✅ None |
| A7 | What are the timings of meetings | `list_meetings()` → shows dates; chunks' start_time shows meeting start | ✅ None |

### Category B — Meeting Scoped (query_scope_node resolves scope)

| # | Query | Scope Resolved | Tool Flow | Gap? |
|---|---|---|---|---|
| B1 | How many persons in previous meeting | M10 | `list_speakers()` (scoped → returns M10-only speakers + count) | ⚠️ Gap 2 (fix: scope-aware list_speakers) |
| B2 | Topics discussed in previous meeting | M10 | `get_meeting_summaries()` (scope_ids=M10) ✅ + `search_transcripts()` | ✅ Fixed |
| B3 | Which topic is most important | M10 | `get_meeting_summaries()` → LLM judges | ✅ None |
| B4 | Main agenda of previous meeting | M10 | `get_meeting_summaries()` | ✅ None |
| B5 | How many issues raised in previous meeting | M10 | `count_signal_chunks(signal_filter="open_issue")` → exact count from metadata | ⚠️ Gap 6 (new tool needed) |
| B6 | Can we answer all Bhavneet's questions | M10 | `search_transcripts(speaker_name="Bhavneet", signal_filter="question")` → for each question, search again for answer | ⚠️ Gap 4 |
| B7 | Anything highlighted by Bhavneet | M10 | `search_transcripts(speaker_name="Bhavneet Mahajan")` | ✅ None |
| B8 | Any commitment in previous meeting | M10 | `search_transcripts(signal_filter="commitment")` with scope | ✅ None |
| B9 | Summary of last meeting | M10 | `get_meeting_summaries()` (scope_ids=M10) | ✅ Fixed |
| B10 | Planning for next work in previous meeting | M10 | `search_transcripts(query="next steps planning", signal_filter="commitment")` | ✅ None |
| B11 | Documents shared by client in that meeting | M10 | `search_transcripts(signal_filter="document_share")` — **MISSING from tool** | ⚠️ Gap 1 |
| B12 | Feedback by Bhavneet in 20th April meeting | M6 (date match) | `search_transcripts(query="feedback", speaker_name="Bhavneet Mahajan")` | ✅ None |

### Category C — Specific Topic / Cross-Meeting

| # | Query | Scope Resolved | Tool Flow | Gap? |
|---|---|---|---|---|
| C1 | AI discussion in previous 2 meetings | M10+M9 | `search_transcripts(query="AI", k=20)` + `get_meeting_summaries()` | ✅ None |
| C2 | Harsh raised question about AI architecture | Project | `search_transcripts(query="AI architecture", speaker_name="Harsh Vardhan", signal_filter="question")` | ✅ None |
| C3 | Overall AI architecture conversation | Project | `search_transcripts(query="AI architecture", k=25)` × 2 passes + `get_meeting_summaries()` | ✅ None |
| C4 | Harsh commitment re: AI in last 5 meetings | M10–M6 | `search_transcripts(query="AI", speaker_name="Harsh Vardhan", signal_filter="commitment")` with scope | ✅ None |
| C5 | Clarity given by Bhavneet about AI | Project | `search_transcripts(query="AI clarification explanation", speaker_name="Bhavneet Mahajan")` | ✅ None |
| C6 | Summarize AI architecture discussion | Project | `search_transcripts(query="AI architecture", k=25)` + `get_meeting_summaries()` | ✅ None |
| C7 | Exact approach for building AI system | Project | `search_transcripts(query="AI system approach", signal_filter="decision")` → retry without filter | ✅ None |
| C8 | Which issue came first: OCA or fixed assets | Project | `search_transcripts("OCA issue")` + `search_transcripts("fixed assets issue")` → compare meeting_date + timestamp | ✅ None |
| C9 | Which unresolved issue discussed last | Project | `search_transcripts(signal_filter="open_issue", k=25)` → find latest by meeting_date + start_time | ✅ None |
| C10 | Who spoken most in this project | Project | `list_speakers()` → output includes chunk count per speaker, LLM ranks | ⚠️ Gap 3 (fix: add counts to list_speakers) |
| C11 | Simarjot Kaur's commitments with traces | Project | `search_transcripts(query="commitment", speaker_name="Simarjot Kaur", signal_filter="commitment", k=25)` | ✅ None |

---

## Part 2: Gaps Identified

### Gap 1 — `document_share` signal not exposed in tool
- **Affected query:** B11 — "documents shared by client"
- **Problem:** `contains_document_share` exists in ChromaDB (added Sprint 3) but `_SIGNAL_MAP` in `tools.py` only has: decision, commitment, question, open_issue
- **Fix:** Add `"document_share": "contains_document_share"` to `_SIGNAL_MAP`. Add to docstring + system prompt.

### Gap 2 — `list_speakers` not scope-aware
- **Affected query:** B1 — "how many persons in previous meeting"
- **Problem:** `list_speakers()` returns ALL speakers project-wide. With `scope_ids=[M10]` in state, it should only return speakers who appear in M10's chunks.
- **Fix:** In `list_speakers`, read `scope_ids` from state. If set, add a `meeting_id` filter when scanning metadatas.

### Gap 3 — No chunk count in `list_speakers` output
- **Affected query:** C10 — "who spoken most"
- **Problem:** `list_speakers()` shows name + role but no indication of how much each person spoke.
- **Fix:** Count chunks per speaker while scanning metadatas. Add `(N chunks)` to each speaker line. LLM can then rank.

### Gap 4 — Multi-hop Q&A matching not guided
- **Affected query:** B6 — "are we able to give all answers to Bhavneet's questions"
- **Problem:** Requires 2 passes — first find questions, then for each question check if answer exists. System prompt doesn't guide this pattern.
- **Fix:** Add explicit multi-hop guidance to system prompt: "For Q&A matching queries, first search for questions by speaker + signal_filter='question', then for each question found, do a second search_transcripts call to find if an answer was given."

### Gap 6 — Count queries have two types — only one is handled correctly

**Real signal counts in ChromaDB (proj_nolocode_001):**
```
contains_question:       238 chunks  (14.3%)
contains_commitment:     179 chunks  (10.8%)
contains_decision:        19 chunks   (1.1%)
contains_open_issue:      74 chunks   (4.5%)
contains_document_share:  16 chunks   (1.0%)
total non-summary:     1,659 chunks
```

**Two fundamentally different count query types:**

| Type | Example | Current approach | Problem |
|---|---|---|---|
| **Metadata count** | "How many commitments in this meeting?" | `search_transcripts(signal_filter='commitment')` → LLM counts returned chunks | k=25 cap means real count (e.g. 179) is NOT shown to LLM — LLM sees 25 and guesses |
| **Semantic count** | "How many AI architectures are discussed?" | `search_transcripts(query='AI architecture')` → LLM counts distinct items | No metadata count possible — LLM must deduplicate from content |

**Type 1 fix (metadata counts):** Add a new `count_signal_chunks` tool that queries ChromaDB metadata directly — returns the **exact count** without any k limit.

**Type 2 (semantic counts):** No tool fix needed — LLM reads chunks and counts/deduplicates. Guide via system prompt.

**New Tool 5: `count_signal_chunks`**

```python
@tool
def count_signal_chunks(
    signal_filter: str,
    speaker_name: Optional[str] = None,
    state: Annotated[dict, InjectedState] = None,
) -> str:
    """Return the EXACT count of chunks containing a specific signal type.

    Use for:
    - "How many commitments were made?" → count_signal_chunks(signal_filter='commitment')
    - "How many questions did Bhavneet raise?" → count_signal_chunks(signal_filter='question', speaker_name='Bhavneet Mahajan')
    - "How many issues in the previous meeting?" → count_signal_chunks(signal_filter='open_issue') [scope auto-applied]
    - "How many decisions were made in this project?" → count_signal_chunks(signal_filter='decision')

    Returns exact count from ChromaDB metadata — not approximate, no k limit.
    Scope (meeting / date range) is automatically applied from context.

    For "how many X about [topic]" (e.g., "questions about AI architecture"),
    use search_transcripts(query=topic, signal_filter=signal) and count returned results.
    """
    # Build filter: project_id + signal + optional speaker + scope
    and_clauses = [
        {"project_id": {"$eq": project_id}},
        {_SIGNAL_MAP[signal_filter]: {"$eq": True}},
    ]
    if speaker_name: and_clauses.append({"speaker_name": {"$eq": speaker_name}})
    if scope_ids:    and_clauses.append(scope_id_clause)   # meeting_id $eq or $in

    results = collection.get(where={"$and": and_clauses}, include=[])  # no content fetch
    count   = len(results["ids"])

    return f"Exact count: {count} '{signal_filter}' chunks{speaker_desc}{scope_desc}."
```

This tool costs zero embedding calls — pure ChromaDB metadata scan, ~50ms.

---

### Gap 5 — Scope context not visible to LLM
- **Affected queries:** All Category B — LLM may call `list_meetings` unnecessarily to figure out which meeting "last meeting" refers to, wasting a tool call.
- **Problem:** `query_scope_node` resolves scope but the resolved scope is not injected into the LLM's context.
- **Fix:** In `graph.py → call_llm()`, append scope context to system message before calling LLM.

---

## Part 3: Changes Required

### File 1: `production/agent/tools.py`

**Change A — Add `document_share` to `_SIGNAL_MAP`:**
```python
_SIGNAL_MAP = {
    "decision":       "contains_decision",
    "commitment":     "contains_commitment",
    "question":       "contains_question",
    "open_issue":     "contains_open_issue",
    "document_share": "contains_document_share",   # ← ADD
}
```

**Change B — Update `search_transcripts` docstring:**
```
signal_filter : str, optional
    One of: 'decision', 'commitment', 'question', 'open_issue', 'document_share'.
    Add 'document_share' line: "Use 'document_share' when asked about files, links,
    or documents shared by any participant."
```

**Change C — Make `list_speakers` scope-aware + add chunk counts:**
```python
def list_speakers(state=None):
    project_id = state["project_id"]
    scope_ids  = state.get("scope_ids")   # None = all meetings

    # When scanning metadatas, add meeting_id filter if scope_ids set:
    where = {"project_id": {"$eq": project_id}}
    if scope_ids:
        if len(scope_ids) == 1:
            where = {"$and": [where, {"meeting_id": {"$eq": scope_ids[0]}}]}
        else:
            where = {"$and": [where, {"meeting_id": {"$in": scope_ids}}]}

    # While counting, track chunk count per speaker:
    speakers: dict[str, dict] = {}  # name → {role, count}
    for m in metas:
        name = m.get("speaker_name")
        if name and not m.get("is_meeting_summary"):
            if name not in speakers:
                speakers[name] = {"role": m.get("speaker_role","unknown"), "count": 0}
            speakers[name]["count"] += 1

    # Output line: "  - Name  [Role]  (47 chunks)"
```

---

### File 2: `production/agent/prompts.py`

Full rewrite of the TOOLS section and add a new QUERY PATTERNS section. Key additions:

**Updated TOOLS section** — more specific guidance per tool:

```
search_transcripts
  For: specific topics, technical decisions, what someone said, blockers,
       action items, questions raised, any discussion content.
  signal_filter options:
    'decision'       — what was decided, agreed, confirmed, approved
    'commitment'     — action items, what someone will do, ownership taken
    'question'       — questions raised, clarifications asked
    'open_issue'     — unresolved problems, blockers, concerns
    'document_share' — files, links, documents shared by participants
  speaker_name: scope to one person's contributions
  CALL MULTIPLE TIMES with different queries/filters for comprehensive answers.
  If signal_filter gives 0 results, retry WITHOUT the filter.

list_speakers
  For: who attended, who is the client, list the team.
  NOTE: when a meeting scope is active, shows only speakers from that meeting.
  Output includes chunk count per speaker — use this to answer "who spoke most".

get_meeting_summaries
  For: project overview, what happened in a specific meeting, agenda topics.
  NOTE: automatically scoped to the resolved meeting(s) when scope is active.

list_meetings
  For: meeting count, meeting dates, meeting order.
  Do NOT call this to find out which meeting is "last" — that is already resolved.
```

**New QUERY PATTERNS section:**

```
QUERY PATTERNS — how to handle specific query types
═══════════════════════════════════════════════════

COUNT queries — TWO types, different tools:

  TYPE 1 — Signal counts (exact, no topic filter needed):
    "How many commitments were made?" → count_signal_chunks(signal_filter='commitment')
    "How many issues in this meeting?" → count_signal_chunks(signal_filter='open_issue')
    "How many questions did Bhavneet raise?" → count_signal_chunks(signal_filter='question', speaker_name='Bhavneet Mahajan')
    "How many meetings?" → list_meetings()
    "How many people attended?" → list_speakers() [chunk counts included]
    ↳ These return EXACT numbers from metadata — no k limit.

  TYPE 2 — Semantic counts (topic-filtered, approximate):
    "How many questions about AI architecture?" → search_transcripts(query='AI architecture', signal_filter='question') → count results shown in header
    "How many distinct AI architectures discussed?" → search_transcripts(query='AI architecture', k=25) → read chunks, identify and count unique named approaches
    ↳ These are inherently approximate — the header "Found N chunks" is your count.

YES/NO queries ("is any X...?", "is anything...?", "are we able to...?")
  • Search first with the relevant query + signal_filter
  • Answer: "Yes — [name] (MM:SS) [verb] [detail] in [meeting]."
  • If nothing found: "No, no [X] was found. The meeting covered [what WAS there]."

DOCUMENT queries ("what documents/files/links were shared?")
  • Use signal_filter='document_share'
  • Include sharer name + timestamp + meeting in answer

SPEAKER CONTRIBUTION queries ("summarize X's commitments / questions / contributions")
  • Always set speaker_name=<full name>
  • Combine with signal_filter if specific type requested
  • For "with traces": include every result with (MM:SS) and meeting name

CHRONOLOGICAL COMPARISON ("which came first?", "which was last?")
  • Search both topics separately
  • Compare meeting_date field + start_time (timestamp) from results
  • Report: "[X] was first raised in Meeting #N ([date]) at ([MM:SS])"
  • For "which was last": find highest meeting_date, then latest timestamp in that meeting

MULTI-HOP Q&A ("are we able to answer Bhavneet's questions?")
  • Step 1: search_transcripts(speaker_name=<client>, signal_filter='question') to find their questions
  • Step 2: for each question found, call search_transcripts(query=<question_text>) to find if answered
  • Summarize which questions got answers and which did not

WHO SPOKE MOST
  • Call list_speakers() — output includes chunk count per speaker
  • Rank by count, report top speakers

WHEN + WHERE queries ("in which meeting and at what time did X happen?")
  • Use search_transcripts — output already includes meeting_title, meeting_date, (MM:SS)
  • Add speaker_name and/or signal_filter to narrow down
  • Report the exact meeting and timestamp from the result
```

---

### File 3: `production/agent/graph.py`

**Change — Inject scope context into LLM system message in `call_llm()`:**

```python
def call_llm(state: AgentState) -> dict:
    system = SystemMessage(content=SYSTEM_PROMPT)

    # Append scope context so LLM doesn't waste a tool call figuring it out
    scope_type = state.get("scope_type", "project")
    scope_ids  = state.get("scope_ids")

    if scope_type == "meeting" and scope_ids:
        # Resolve IDs to readable labels via list in state (or just show IDs)
        scope_note = (
            f"\n\nSCOPE ALREADY RESOLVED: This query is limited to meeting(s): {scope_ids}. "
            f"Do NOT call list_meetings to find the scope — it is already applied. "
            f"Tools will automatically restrict to these meetings."
        )
        system = SystemMessage(content=SYSTEM_PROMPT + scope_note)
    elif scope_type == "date_range":
        scope_note = (
            "\n\nSCOPE ALREADY RESOLVED: A date-range filter is active. "
            "Tools will automatically restrict results to meetings within that date range."
        )
        system = SystemMessage(content=SYSTEM_PROMPT + scope_note)

    messages = [system] + list(state["messages"])
    response = llm_with_tools.invoke(messages)
    ...
```

---

### File 4: `app/services/answer/scope.py`

**Change — Add cardinal meeting number pattern ("meeting 3", "meeting #5"):**

Add before the date pattern in `parse_meeting_scope()`:
```python
_MEETING_NUMBER_RE = re.compile(r"\bmeeting\s*#?\s*(\d+)\b", re.IGNORECASE)

# In parse_meeting_scope(), add before date handling:
mn = _MEETING_NUMBER_RE.search(query)
if mn:
    n = int(mn.group(1))
    sorted_meetings = get_project_meetings_sorted(project_id)
    # sorted is newest-first; meeting #1 = oldest = sorted_meetings[-1]
    if 1 <= n <= len(sorted_meetings):
        chron_idx = len(sorted_meetings) - n
        clause = {"meeting_id": {"$eq": sorted_meetings[chron_idx][0]}}
        _log_scope_result(f"meeting_number_{n}", clause, sorted_meetings)
        return clause
```

---

## Part 3b: Scope-Aware Top-K Strategy

### Why k must differ between meeting scope and project scope

| Scope | Corpus size | k=15 gives you | Problem |
|---|---|---|---|
| Project-wide | ~1,659 chunks across 10 meetings | 0.9% of content | Miss information spread across meetings |
| Single meeting | ~150 chunks | 10% of content | Sufficient; higher k brings noise |
| Last 2 meetings | ~300 chunks | 5% | Need more than 15 for good coverage |
| Last 5 meetings | ~750 chunks | 2% | Need max k |

**Core problem:** A project-wide query with k=15 may retrieve 15 chunks from the same 2-3 meetings, completely missing the other 7 meetings. The LLM thinks it has full coverage but does not.

### Solution: `recommended_k` in state, computed by `query_scope_node`

**`recommended_k` formula:**
```
scope_type = "project"           → recommended_k = 25  (max, need broad coverage)
scope_type = "meeting", 1 mtg    → recommended_k = 15  (sufficient for ~150 chunks)
scope_type = "meeting", 2 mtgs   → recommended_k = 20
scope_type = "meeting", 3+ mtgs  → recommended_k = 25
scope_type = "date_range"        → recommended_k = 20  (unknown size, medium coverage)
```

**Helper function in `query_scope.py`:**
```python
def _compute_recommended_k(scope_type: str, scope_ids: Optional[list]) -> int:
    if scope_type == "project":
        return 25
    elif scope_type == "meeting":
        n = len(scope_ids) if scope_ids else 1
        return min(15 + (n - 1) * 5, 25)   # 1→15, 2→20, 3+→25
    elif scope_type == "date_range":
        return 20
    return 15
```

**Changes required:**

1. **`state.py`** — add `recommended_k: int` field
2. **`query_scope_node`** — compute and return `recommended_k` alongside the 3 scope fields
3. **`service.py` initial_state** — add `"recommended_k": 15` as default
4. **`search_transcripts` tool body:**
   ```python
   recommended_k = state.get("recommended_k", 15)
   # Use the larger of: LLM-requested k OR scope-recommended k (never exceed 25)
   effective_k = min(max(int(k), recommended_k), 25)
   ```
   This means: if LLM says k=15 (default) but scope is project-wide (recommended=25), we use 25. If LLM explicitly says k=20 and recommended is 25, we use 25. Never lets LLM request less than the scope recommends.

5. **System prompt — add k guidance:**
   ```
   k values — the system auto-adjusts k based on scope. You do not need to set k manually
   for standard queries. Only override k when you need more results than default:
     • "give me ALL commitments" → set k=25
     • "find any single example" → set k=10
   ```

**Result table after fix:**

| Query | Scope | recommended_k | effective_k |
|---|---|---|---|
| "What AI decisions were made?" | project | 25 | 25 |
| "What was discussed in previous meeting?" | 1 meeting | 15 | 15 |
| "AI discussion in last 2 meetings" | 2 meetings | 20 | 20 |
| "Harsh's commitments in last 5 meetings" | 5 meetings | 25 | 25 |
| "Issues in last 30 days" | date_range | 20 | 20 |

---

## Part 4: File Summary

| File | Change | Affects Scenarios |
|---|---|---|
| `production/agent/state.py` | Add `recommended_k: int` field | All search queries |
| `production/agent/query_scope.py` | Compute + return `recommended_k` | All search queries |
| `production/agent/tools.py` | Add `document_share` to `_SIGNAL_MAP` | B11 |
| `production/agent/tools.py` | `list_speakers` scope-aware + chunk counts per speaker | B1, C10 |
| `production/agent/tools.py` | `search_transcripts` use `effective_k = max(k, recommended_k)` | All search queries |
| `production/agent/tools.py` | **NEW** `count_signal_chunks` tool — exact metadata count | A4, B5, B8, B12, C4, C9 |
| `production/agent/prompts.py` | Full rewrite — add QUERY PATTERNS + k guidance + count guidance | All 30 |
| `production/agent/graph.py` | Inject scope context into LLM system message | All Category B |
| `production/service.py` | Add `recommended_k: 15` to `initial_state` | All queries |
| `app/services/answer/scope.py` | Add `meeting_number` regex pattern | Any "meeting 3" query |

---

## Part 5: Verification

**After implementation, test these 5 representative queries:**

```bash
# 1. Count query (Gap 3 fixed)
python -c "
from production.service import answer_query
r = answer_query('Who spoken most in this project', 'proj_nolocode_001')
print(r['answer'][:300])
print('tool_calls:', [t['tool'] for t in r['tool_calls']])
"
# Expected: list_speakers() called once, answer ranks speakers by count

# 2. Document share query (Gap 1 fixed)
python -c "
from production.service import answer_query
r = answer_query('What are the documents shared by the client in the previous meeting', 'proj_nolocode_001')
print(r['answer'][:300])
print('tool_calls:', r['tool_calls'])
"
# Expected: search_transcripts with signal_filter=document_share, scoped to M10

# 3. Scope-aware attendance (Gap 2 fixed)
python -c "
from production.service import answer_query
r = answer_query('How many persons are present in the previous meeting', 'proj_nolocode_001')
print(r['answer'][:300])
print('tool_calls:', r['tool_calls'])
"
# Expected: list_speakers() called, returns only speakers from M10 with count

# 4. Scope context injection (Gap 5 fixed)
# Verify list_meetings is NOT called for "last meeting" queries
python -c "
from production.service import answer_query
r = answer_query('What was the main agenda in the previous meeting', 'proj_nolocode_001')
print('tool_calls:', r['tool_calls'])  # Must NOT include list_meetings
"
# Expected: only get_meeting_summaries called, no list_meetings

# 5. Commitment trace query (already works, verify format)
python -c "
from production.service import answer_query
r = answer_query('Summarize points committed by Harsh Vardhan throughout the project along with traces', 'proj_nolocode_001')
print(r['answer'][:500])
"
# Expected: each commitment with speaker name + (MM:SS) + meeting title
```

**Run the scope node test suite to confirm no regressions:**
```bash
python production/tests/test_query_scope.py
# Expected: 30/30 passed
```

**Test exact count tool:**
```bash
python -c "
from production.service import answer_query
# Should return exact number from metadata (no k limit)
r = answer_query('How many issues were raised in the previous meeting?', 'proj_nolocode_001')
print(r['answer'][:200])
print('tool_calls:', r['tool_calls'])
# Expected: count_signal_chunks called, returns exact number
"
```

**Add new test cases to `test_query_scope.py` Level 1:**
```python
# meeting_number pattern
result = parse_meeting_scope("What was decided in meeting 3?", PROJECT_ID)
check("'meeting 3' → meeting #3", result == {"meeting_id": {"$eq": M3}})

result = parse_meeting_scope("Show me meeting #5", PROJECT_ID)
check("'meeting #5' → meeting #5", result == {"meeting_id": {"$eq": M5}})
```
