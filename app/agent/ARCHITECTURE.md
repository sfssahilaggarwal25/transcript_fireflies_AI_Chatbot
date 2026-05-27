# Production Architecture — LangGraph Agent Pipeline

> **Purpose of this file:** Design document for the production query system.
> All implementation in `production/` must follow this architecture.
> Update this file FIRST whenever a design decision changes, then update the code.

---

## 1. Why Production — Limitations of the Deterministic Pipeline

The existing pipeline in `app/` is deterministic: Python routing rules + fixed intent classifier
dispatch each query to one of 8 pre-built retrieval modes, then fill a fixed prompt template.

**This works well for known query types. It breaks for everything else.**

| Problem | Example Query | Current Behaviour |
|---|---|---|
| Fixed routing | "Compare what the client wants vs what's delivered" | Falls into `general_query` — one retrieval pass, generic answer |
| Single-hop only | "Give me a complete project status with decisions, actions, and open issues" | Picks ONE intent — misses the other two |
| Unknown intent | "What's the overall sentiment of the client across all meetings?" | Routes to `general_query` — not designed for sentiment |
| Novel composition | "Who raised the most questions AND what happened to them?" | Cannot combine `question_query` + `contribution_query` |
| Cross-meeting synthesis | "Has our team's estimate of the timeline changed across meetings?" | Single retrieval pass misses the progression |

**Root cause:** The classifier routes to exactly one path. Retrieval is a fixed k. No way to chain.

**Production solution:** Replace the classifier+router with a **LangGraph ReAct agent** that decides its own retrieval strategy, composes multiple tool calls, and stops when it has enough context.

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     PRODUCTION PIPELINE                                  │
│                                                                           │
│   query + project_id                                                     │
│         │                                                                 │
│         ▼                                                                 │
│   ┌─────────────┐                                                        │
│   │  service.py │  — public entry point, resets accumulator, builds      │
│   │  answer_    │    sources, returns dict compatible with Streamlit UI  │
│   │  query()    │                                                        │
│   └──────┬──────┘                                                        │
│          │                                                                │
│          ▼                                                                │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                    LangGraph Graph                               │   │
│   │                                                                   │   │
│   │   START                                                           │   │
│   │     │                                                             │   │
│   │     ▼                                                             │   │
│   │  ┌──────────┐   tool_calls?=YES   ┌──────────────────────────┐  │   │
│   │  │  agent   │ ──────────────────► │       ToolNode            │  │   │
│   │  │  node    │                     │  search_transcripts       │  │   │
│   │  │(LLM call)│ ◄────────────────── │  get_meeting_summaries   │  │   │
│   │  └──────────┘   ToolMessages      │  list_meetings            │  │   │
│   │     │                             │  list_speakers            │  │   │
│   │     │ tool_calls?=NO              └──────────────────────────┘  │   │
│   │     ▼                               ↑                             │   │
│   │    END                              │ InjectedState(project_id)   │   │
│   │                               (from AgentState — LLM cannot       │   │
│   │                                override this)                     │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                           │
│         │ final messages + accumulated docs                               │
│         ▼                                                                 │
│   ┌─────────────┐                                                        │
│   │  service.py │  — extracts answer, builds sources, returns result     │
│   └─────────────┘                                                        │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. File Structure

```
production/
├── ARCHITECTURE.md           ← This document (update first, then code)
├── __init__.py               ← Exports answer_query()
├── README.md                 ← Quick start + usage guide
│
├── agent/                    ← LangGraph internals
│   ├── __init__.py
│   ├── state.py              ← AgentState TypedDict
│   ├── tools.py              ← 4 tool implementations + shared doc accumulator
│   ├── prompts.py            ← System prompt (persona + rules)
│   └── graph.py              ← Graph assembly, compile, singleton
│
└── service.py                ← Public API — answer_query(query, project_id) → dict
```

**Rule:** Nothing outside `production/` is modified. The production pipeline is additive.

---

## 4. AgentState

```python
class AgentState(TypedDict):
    messages:   Annotated[list[AnyMessage], add_messages]
    project_id: str
```

**`messages`** — The full conversation thread. Every graph step appends to it:
- `HumanMessage` — the original query (set at entry)
- `AIMessage` — LLM response (may include `tool_calls` list)
- `ToolMessage` — result returned by a tool execution

The `add_messages` reducer handles the list accumulation across graph steps.

**`project_id`** — Set ONCE at `graph.invoke()` time in `service.py`. Never written to by
any node or tool. Tools read it via `InjectedState` — they cannot receive it from the LLM.

---

## 5. LangGraph Graph Design

### Nodes

| Node | Type | Responsibility |
|---|---|---|
| `agent` | Custom function | Calls LLM (with tools bound). Returns AIMessage. |
| `tools` | `ToolNode` (prebuilt) | Executes tool calls from last AIMessage. Handles InjectedState. Returns ToolMessages. |

### Edges

```
START → agent
agent → should_continue(state):
    - last AIMessage has tool_calls AND iteration < MAX  →  tools
    - last AIMessage has NO tool_calls                   →  END
    - iteration >= MAX_ITERATIONS                        →  END  (safety guard)
tools → agent
```

### Iteration Guard

Max tool-calling rounds: **6**. After 6 `ToolMessage` rounds, `should_continue` forces
END regardless of whether the LLM wants more tools. This prevents infinite loops on
ambiguous or unanswerable queries.

**Why 6?**
- Complex queries like "full project status" may need: decisions search + commitments search
  + open issues search + summary fetch = 4 calls minimum.
- Buffer of 2 for retries or follow-up refinements.
- Beyond 6, cost-to-quality ratio degrades.

### Model

**`gemini-2.5-flash`** via `langchain_google_genai.ChatGoogleGenerativeAI`.

Why `gemini-2.5-flash` over `gemini-2.5-flash-lite`:
- Better multi-step reasoning (critical for "when to stop calling tools" decisions)
- Better at composing tool results into coherent answers
- Required for reliable function calling with multiple tool schemas

The model is bound to all 4 tools via `llm.bind_tools(TOOLS)` so it knows
the full schema of every tool and can choose when and how to call them.

---

## 6. Tools — Design Rationale

The 8 retrieval modes in the deterministic pipeline map to 4 composable tools here.

### Why 4 tools instead of 8?

In the deterministic pipeline, the 8 modes exist because the classifier routes to exactly
one mode — each mode is narrowly scoped so it doesn't overfetch.

In the agent pipeline, the LLM **composes** multiple tool calls. So:
- `search_transcripts` with `signal_filter` = decisions → covers `decision_query` mode
- `search_transcripts` with `signal_filter` = commitment → covers `commitment_query` mode
- `search_transcripts` with `speaker_name` → covers `compound_retrieve` (speaker-first)
- `get_meeting_summaries` → covers `summary_query` and `topic_summary_query`
- `list_meetings` + `list_speakers` → covers `metadata_query`, `analytical_retrieve`, `contribution_retrieve`

The agent LLM decides the composition. The tools are **general** and **orthogonal**.

### Tool Schemas (what the LLM sees)

#### Tool 1: `search_transcripts`
```
Parameters:
  query         (str, required)    — natural language search query
  k             (int, default=15)  — number of chunks to return (max 25)
  speaker_name  (str, optional)    — restrict to this speaker's contributions
  signal_filter (str, optional)    — one of: decision | commitment | question | open_issue

NOT in schema (injected from state):
  project_id    — enforced backend-side, LLM never sees or sets this
```

**Maps to existing infra:** `hybrid_retrieve(query, project_id, hard_filters, k)`
`hard_filters` is built from `speaker_name` and `signal_filter` before calling.

When to call:
- Any question about what was said, discussed, decided, committed, or questioned
- Speaker-specific queries (use `speaker_name`)
- Signal-type queries (use `signal_filter`)
- Call MULTIPLE TIMES with different queries/filters for comprehensive answers

#### Tool 2: `get_meeting_summaries`
```
Parameters:
  meeting_title (str, optional) — filter to a specific meeting by title substring

NOT in schema (injected):
  project_id
```

**Maps to existing infra:** `get_raw_collection().get(where={is_meeting_summary: True, ...})`

When to call:
- "What happened in meeting X?"
- "Give me a project overview"
- "What was covered in the last 3 meetings?"
- Summary-type questions where chunk-level detail is less important than the overall narrative

#### Tool 3: `list_meetings`
```
Parameters:
  (none visible to LLM — only project_id injected from state)
```

**Maps to existing infra:** ChromaDB `.get()` scan with distinct meeting_id deduplication.

When to call:
- "How many meetings have we had?"
- "When was the last meeting?"
- "Show me all meetings in order"
- Any query needing meeting metadata (dates, count, order)

#### Tool 4: `list_speakers`
```
Parameters:
  (none visible to LLM — only project_id injected from state)
```

When to call:
- "Who attended the meetings?"
- "Who is the client?"
- "List all developers on the team"
- Any query about participants and roles

### project_id Enforcement (Critical)

`InjectedState` from `langgraph.prebuilt` tells `ToolNode` to inject the current
graph state into the `state` parameter of each tool:

```python
@tool
def search_transcripts(
    query: str,
    k: int = 15,
    speaker_name: Optional[str] = None,
    signal_filter: Optional[str] = None,
    state: Annotated[dict, InjectedState] = None,   # ← injected, not from LLM
) -> str:
    project_id = state["project_id"]   # ← always from state, never from LLM args
```

`ToolNode` strips `InjectedState` parameters from the schema it sends to the LLM.
The LLM's tool call JSON never contains `project_id`. The backend injects it.

**This is non-negotiable.** Every tool must read `project_id` this way.

---

## 7. Document Accumulator

**Problem:** Tools return strings (ToolMessages). But `service.py` needs the raw
`Document` objects to build a sources list for the Streamlit UI.

**Solution:** Module-level mutable list. In-place mutations (`.clear()`, `.extend()`)
are visible to all threads that hold a reference to the same list object.

```
production/agent/tools.py:
  _accumulated_docs: list[Document] = []       ← module-level mutable list

  reset_doc_accumulator() → _accumulated_docs.clear()
  _append_docs(docs)      → _accumulated_docs.extend(docs)
  get_accumulated_docs()  → list(_accumulated_docs)   ← copy for safety

service.py:
  reset_doc_accumulator()          ← call BEFORE graph.invoke()
  result = graph.invoke(state)
  docs = get_accumulated_docs()    ← call AFTER graph.invoke()
  sources = _build_sources(docs)
```

**Why not ContextVar?**
`ToolNode` uses a thread pool. Python `ContextVar.set()` inside a thread only updates
the thread's context copy — the parent thread never sees the changes. In-place
`.extend()` on a shared object IS visible across all threads that reference the same list.

**Concurrency limitation:** Not safe for concurrent multi-user requests. Acceptable for
single-user Streamlit demo. For multi-user production: use a per-request-id dict
keyed by `uuid4()` that is passed through the state.

---

## 8. Source Extraction

After `graph.invoke()`, `service.py` reads the accumulated docs and builds sources:

```
Accumulated docs → deduplicate by (speaker_name, meeting_id) → source entries
```

Source entry schema (compatible with existing Streamlit `render_sources()`):
```python
{
    "chunk_num":       int,   # sequential 1..N for display
    "speaker_name":    str,   # "Meeting Summary" for summary chunks
    "meeting_title":   str,
    "meeting_date":    str,
    "timestamp":       str,   # "MM:SS" or None
    "content_preview": str,   # first 200 chars of chunk
    "is_summary":      bool,
}
```

**No [N] inline citations in the production path.** The LLM attributes by speaker name
and timestamp directly in the answer text. The sources panel shows the backing evidence.

---

## 9. Answer Content Extraction

`gemini-2.5-flash` with extended thinking returns `AIMessage.content` as a list of
content blocks, not a plain string:

```python
# Extended thinking format (gemini-2.5-flash)
[{"type": "text", "text": "Here are the decisions...", "extras": {"signature": "..."}}]

# Plain string format (gemini-2.0-flash, others)
"Here are the decisions..."
```

`service.py` handles both:
```python
raw = msg.content
if isinstance(raw, str):
    answer = raw
elif isinstance(raw, list):
    answer = "\n".join(b["text"] for b in raw if b.get("type") == "text")
```

---

## 10. System Prompt Design

The system prompt sets:
1. **Persona** — PM Meeting Intelligence assistant
2. **Tool selection guide** — when to call each tool, how to combine them
3. **Attribution rules** — speaker name (timestamp) verb form
4. **Negative case rules** — state what WAS covered when topic is missing
5. **Format rules** — structured topics for broad questions, bullet lists for decisions/actions

**Key difference from deterministic prompts:**
- No template per intent — one universal prompt
- LLM decides format based on query type
- Attribution is by speaker name, not [N] chunk number

> **Most important tuning lever in the entire pipeline:**
> `production/agent/prompts.py` is where classification quality is controlled.
> The LLM has no separate classifier — it reads the tool docstrings and system prompt,
> then selects a tool and arguments. That selection IS the classification AND the
> retrieval strategy in one decision.
>
> Clearer tool descriptions = more accurate tool selection = better retrieval.
>
> **When accuracy is poor on a query type, fix the system prompt or tool docstring
> in `tools.py` BEFORE changing any retrieval logic.**
>
> Example: if the agent misses decisions on "we agreed to...", the fix is adding
> "Use signal_filter='decision' also when you see 'agreed', 'approved', 'confirmed'"
> to the `search_transcripts` docstring — not changing the retrieval code.

---

## 11. Return Format — Compatibility with Streamlit UI

`service.py` returns the same dict keys as `app.services.answer_service.answer_question()`:

```python
{
    "answer":             str,         # LLM-generated answer
    "sources":            list[dict],  # source entries (chunk_num, speaker_name, ...)
    "intent":             "production_agent",   # fixed — for UI intent badge
    "notice":             None,        # no date-scoping notice in production path
    "num_context_chunks": int,         # total docs retrieved (for linkification ceiling)
    "tool_calls":         list[dict],  # [{tool, args}, ...] — reasoning trace
    "model":              str,         # "gemini-2.5-flash (agent)"
    "error":              str | None,  # exception message if failed
}
```

The Streamlit UI can display `tool_calls` in a new "Reasoning" expander to show
the PM how the answer was built (what tools were called, with what arguments).

---

## 12. What Is NOT Changed

| Component | File | Status |
|---|---|---|
| Ingestion pipeline | `app/services/transcript/` | **Unchanged** |
| Chunking + signals | `app/services/transcript/chunking.py` | **Unchanged** |
| ChromaDB storage | `app/services/storage/` | **Unchanged — shared** |
| Embedding model | `app/services/embeddings/` | **Unchanged — shared** |
| Deterministic pipeline | `app/services/answer/` | **Unchanged — still works** |
| projects.json config | `projects.json` | **Unchanged — shared** |
| Streamlit UI | `streamlit_app.py` | **Unchanged for deterministic** |
| Test suite | `app/tests/` | **Unchanged** |

The production pipeline reuses ChromaDB, embeddings, and the retrieval functions
(`hybrid_retrieve`, `get_raw_collection`). It adds NO new storage or data.

---

## 13. Data Flow — Step by Step

```
1. PM types query in Streamlit
   ↓
2. production/service.py: answer_query(query, project_id)
   - reset_doc_accumulator()           ← clear previous request's docs
   - initial_state = {
       messages:   [HumanMessage(query)],
       project_id: project_id,          ← set once here, never changes
     }
   ↓
3. graph.invoke(initial_state)
   ↓
4. agent node: call_llm(state)
   - Prepend SystemMessage(SYSTEM_PROMPT) to messages
   - Call ChatGoogleGenerativeAI(gemini-2.5-flash).bind_tools(TOOLS).invoke(messages)
   - LLM reads the query and decides which tools to call
   - Returns AIMessage (with tool_calls if retrieval needed)
   ↓
5. should_continue(state):
   - AIMessage has tool_calls → go to tools node
   - AIMessage has no tool_calls → go to END
   ↓
6. tools node: ToolNode(TOOLS).invoke(state)
   - For each tool_call in last AIMessage:
     a. Look up the tool function by name
     b. Inject state["project_id"] into the tool's state parameter (InjectedState)
     c. Call the tool function with LLM-provided args + injected project_id
     d. Inside the tool: calls hybrid_retrieve() or get_raw_collection()
     e. Appends retrieved Document objects to _accumulated_docs (module-level)
     f. Returns formatted string (chunk list or metadata)
   - Wraps each result in a ToolMessage
   - Returns {messages: [ToolMessage, ToolMessage, ...]}
   ↓
7. Back to agent node (loop)
   - LLM reads tool results in ToolMessages
   - Decides: need more retrieval? or ready to answer?
   - If more retrieval: returns another AIMessage with tool_calls → step 6
   - If ready: returns AIMessage with final answer text, no tool_calls
   ↓
8. should_continue: no tool_calls → END
   ↓
9. service.py: extract answer from last AIMessage
   - Handle string vs list content (extended thinking)
   ↓
10. service.py: get_accumulated_docs()
    - Read all Document objects collected across all tool calls
    ↓
11. service.py: _build_sources(docs)
    - Deduplicate by (speaker_name, meeting_id)
    - Build source entry dicts
    ↓
12. service.py: _extract_tool_calls(messages)
    - Walk AIMessages, collect tool name + args for reasoning trace
    ↓
13. Return dict → Streamlit renders answer + sources + tool call trace
```

---

## 14. Comparison: Deterministic vs Production

| Dimension | Deterministic (`app/`) | Production (`production/`) |
|---|---|---|
| **Query scope** | 12 fixed intents | Any query |
| **Routing** | Python regex → LLM classifier → 8 modes | LLM decides dynamically |
| **Retrieval passes** | Always 1 | 1 to 6 (LLM decides) |
| **Multi-type queries** | Cannot combine intents | Calls multiple tools |
| **Answer format** | Fixed template per intent | LLM decides based on query |
| **Citations** | `[N]` inline chunk numbers | Speaker name + (MM:SS) |
| **Latency** | ~3–6s | ~8–20s |
| **API cost** | ~2 LLM calls | ~3–8 LLM calls |
| **Failure mode** | Silent wrong routing | "I couldn't find" (explicit) |
| **Novel queries** | Falls to `general_query` | Handles naturally |
| **Best for** | Known PM question types | Open-ended, complex, analytical |

**When to use which:**
- Use **deterministic** for a fast, cheap, predictable answer on common questions
- Use **production** for complex, open-ended, cross-meeting, or comparative questions

---

## 15. Planned Streamlit Integration

A separate `production_streamlit_app.py` (does not replace `streamlit_app.py`):

```
Sidebar additions:
  - Mode toggle: [Deterministic | Production Agent]
  - Shows tool call trace when production mode is active
  
Chat message additions (production mode):
  - Intent badge: "🤖 Agent" instead of intent-specific badge
  - "Reasoning" expander: shows which tools were called + args
  - Sources panel: same as deterministic (compatible format)
```

OR: Single Streamlit app with a mode selector per query.
Decision to be made during Streamlit integration sprint.

---

## 16. Production Streamlit App Plan

**File:** `production_streamlit_app.py` (new file, sibling of `streamlit_app.py`)

**Key differences from `streamlit_app.py`:**

```python
# Import from production pipeline instead of deterministic
from production.service import answer_query   # instead of app.services.answer_service

# Tool call trace expander (new component)
def render_tool_trace(tool_calls: list[dict]):
    if not tool_calls:
        return
    with st.expander(f"🔍 Reasoning — {len(tool_calls)} tool call(s)"):
        for tc in tool_calls:
            args_display = {k: v for k, v in tc['args'].items()}
            st.markdown(f"**`{tc['tool']}`** → `{args_display}`")

# Intent badge is always "🤖 Agent"
# Sources rendering is identical (compatible format)
# Everything else identical to streamlit_app.py
```

---

## 17. Known Limitations and Future Work

### Current Limitations

| Limitation | Impact | Mitigation |
|---|---|---|
| Single-user accumulator | Concurrent requests mix sources | Use per-request-id dict in state |
| No source chunk numbers | Cannot hyperlink [N] in answer | Use speaker/meeting attribution |
| Higher latency (8–20s) | PM may perceive as slow | Show "thinking..." with tool call stream |
| Model cost | ~3–8 LLM calls vs ~2 | Cache frequent compound queries |
| No streaming | Answer appears all at once | Add `graph.astream()` with SSE |

### Future Extensions

1. **Streaming responses** — Use `graph.astream_events()` to stream tokens as LLM generates
2. **Conversation memory** — Add `checkpointer=MemorySaver()` to persist session history
3. **Confidence scoring** — Add a validation node that rates answer completeness
4. **Cross-project queries** — Add a `project_id` list to state for multi-project PMs
5. **Structured output** — Use Gemini structured output for decisions/action items JSON

---

## 18. Implementation Order

Build in this sequence — each step depends on the one above:

```
Phase 1 — Core agent (DONE in current partial implementation)
  [x] state.py         — AgentState
  [x] tools.py         — 4 tools + accumulator
  [x] prompts.py       — system prompt
  [x] graph.py         — LangGraph graph
  [x] service.py       — public API

Phase 2 — Fix and validate
  [ ] Verify all tool signatures match existing retrieval infra
  [ ] Verify source accumulator works across ToolNode threads
  [ ] Verify content extraction handles extended thinking format
  [ ] End-to-end test: all 4 tools called, sources populated

Phase 3 — Production Streamlit app
  [ ] production_streamlit_app.py — tool trace expander + agent badge
  [ ] Test with real queries from streamlit UI
  [ ] Verify sources panel renders correctly

Phase 4 — Edge cases and hardening
  [ ] Test with queries that get 0 results from all tools
  [ ] Test with queries needing 5+ tool calls
  [ ] Test project_id cannot be overridden from LLM
  [ ] Latency measurement: avg tool calls per query type

Phase 5 — Future (post-POC)
  [ ] Streaming via graph.astream_events()
  [ ] Per-request-id accumulator for concurrency
  [ ] Conversation memory with checkpointer
```

---

## 19. How to Update This Document

When you change any file in `production/`, update the matching section here:

| Changed file | Update section |
|---|---|
| `agent/state.py` | Section 4 (AgentState) |
| `agent/tools.py` | Sections 6 (tools), 7 (accumulator) |
| `agent/prompts.py` | Section 10 (system prompt) |
| `agent/graph.py` | Sections 5 (graph design), 5 (model) |
| `service.py` | Sections 9 (content extraction), 11 (return format), 13 (data flow) |
| Adding a new tool | Sections 6 (tool rationale), 14 (comparison) |
| Changing model | Section 5 (model), Section 9 (content extraction), Section 11 |
| Adding Streamlit | Sections 15, 16 |
