# LangGraph Agent Architecture
### AI Meeting Intelligence System — Production Documentation

**Prepared by:** Engineering Team  
**Date:** 2026-05-28  
**System Status:** Production-ready POC — Sprint 6 complete  
**Test Coverage:** 41/41 queries passing, average score 8.8/10  
**Scale:** 10 meetings · 1,669 chunks · 5 speakers per project

> **Note:** This document covers the LangGraph-based agentic pipeline located in `app/agent/`.  
> It uses **tools + a ReAct loop** — the LLM dynamically decides which tools to call.  
> This is different from the deterministic 8-mode RAG pipeline in `app/rag/`.

---

## Table of Contents

1. [What Makes This an Agent System](#1-what-makes-this-an-agent-system)
2. [High-Level Architecture](#2-high-level-architecture)
3. [Graph Structure (LangGraph)](#3-graph-structure-langgraph)
4. [State Model (AgentState)](#4-state-model-agentstate)
5. [Node 1 — query_scope (Python-Only)](#5-node-1--query_scope-python-only)
6. [Node 2 — agent (LLM + Tools Bound)](#6-node-2--agent-llm--tools-bound)
7. [Node 3 — tools (ToolNode)](#7-node-3--tools-toolnode)
8. [The Five Tools](#8-the-five-tools)
9. [Security Enforcement (project_id and scope_where)](#9-security-enforcement-project_id-and-scope_where)
10. [Doc Accumulator & Citations](#10-doc-accumulator--citations)
11. [System Prompt Design](#11-system-prompt-design)
12. [Service Layer (answer_query)](#12-service-layer-answer_query)
13. [Data Flow: End-to-End Request Trace](#13-data-flow-end-to-end-request-trace)
14. [Tech Stack](#14-tech-stack)
15. [Comparison: Agent vs Deterministic RAG Pipeline](#15-comparison-agent-vs-deterministic-rag-pipeline)

---

## 1. What Makes This an Agent System

The core difference between this pipeline and a standard RAG pipeline is **who decides what to retrieve**.

| Aspect | Standard RAG pipeline (`app/rag/`) | Agent pipeline (`app/agent/`) |
|--------|-----------------------------------|-------------------------------|
| Routing | Python rules classify intent → fixed mode | LLM reads query + tools → decides dynamically |
| Retrieval | One retrieval call, one path | LLM can call 1–6 tools in any sequence |
| Flexibility | 8 hardcoded modes cover known query types | Handles novel query types without code changes |
| Tool calls | Zero — one call to a composite pipeline function | LLM issues `tool_calls` in each response |
| Multi-hop | Not supported natively | Built-in — LLM issues follow-up tool calls |
| Loop control | Not applicable | Max 6 iterations, iteration guard enforced |

In the agent pipeline, the LLM is **both the reasoner and the retrieval planner**. It reads the system prompt (which explains 5 tools and when to use each), then issues tool calls, reads results, and continues calling tools until it has enough context to answer — or until the 6-iteration guard forces it to stop.

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          INGESTION PATH                             │
│                                                                     │
│                                                                     │
│  Fireflies Webhook → normalize.py → chunking.py → stamp_project()   │
│    → Gemini Embeddings (gemini-embedding-001) → ChromaDB            │
│                                                                     │
│  Result: 1,669 chunks across 10 meetings                            │
│  Each chunk has: speaker, timestamps, 5 signal flags, project_id    │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                          AGENT QUERY PATH                           │
│                                                                     │
│  PM types question in Streamlit UI                                  │
│       │                                                             │
│       ▼                                                             │
│  answer_query(query, project_id)    ← service.py                    │
│       │                                                             │
│       │  reset_doc_accumulator()    ← clears per-request state      │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────────────────────────────────────────────┐               │
│  │           LangGraph StateGraph                  │               │
│  │                                                 │               │
│  │  START                                          │               │
│  │    │                                            │               │
│  │    ▼                                            │               │
│  │  query_scope node    ← Python-only, ~50ms       │               │
│  │    │  Resolves "last meeting", "May 9th" etc.   │               │
│  │    │  Writes: scope_where, scope_ids,           │               │
│  │    │          scope_type, recommended_k         │               │
│  │    │                                            │               │
│  │    ▼                                            │               │
│  │  agent node ◄──────────────────────┐           │               │
│  │    │  LLM call (gemini-2.5-flash)  │           │               │
│  │    │  Tools bound                  │           │               │
│  │    │                               │           │               │
│  │    ├── has tool_calls?             │           │               │
│  │    │    YES → tools node ──────────┘           │               │
│  │    │    NO  → END                              │               │
│  │    │    MAX ITERATIONS (6) → force END         │               │
│  │                                                │               │
│  │  tools node                                    │               │
│  │    Executes tool call(s) from AIMessage        │               │
│  │    Returns ToolMessages                        │               │
│  │    (InjectedState: project_id, scope_where)    │               │
│  │                                                │               │
│  └─────────────────────────────────────────────────┘               │
│       │                                                             │
│       ▼                                                             │
│  Extract final AIMessage content                                    │
│  Build sources from doc accumulator                                 │
│  Return: {answer, sources, tool_calls, intent, model}              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Graph Structure (LangGraph)

**File:** `app/agent/graph.py`

The graph is a `StateGraph[AgentState]` with 3 nodes and a conditional edge that creates the ReAct loop.

### Nodes

```
START → query_scope → agent ⇄ tools → END
```

| Node | Type | Purpose |
|------|------|---------|
| `query_scope` | Python function | Resolves meeting scope deterministically. Zero LLM cost. |
| `agent` | LLM call | Reads state + system prompt, decides what tools to call or produces final answer |
| `tools` | `ToolNode` (prebuilt LangGraph) | Executes all tool calls in the last `AIMessage`. Injects `project_id` and `scope_where` via `InjectedState`. |

### Edges

```python
START  ──►  query_scope
query_scope ──►  agent
agent  ──►  tools        (when last AIMessage has tool_calls AND iteration < 6)
agent  ──►  END          (when last AIMessage has no tool_calls OR iterations ≥ 6)
tools  ──►  agent        (always — ToolMessages feed back into the LLM)
```

### Iteration Guard

The conditional edge `_should_continue()` counts `ToolMessage` objects already in state. If there are 6 or more (meaning 6 full tool-call rounds have happened), it forces `END` regardless of whether the LLM wants more tool calls. This prevents infinite loops on unanswerable queries.

```python
_MAX_ITERATIONS = 6
```

### Singleton Graph

The graph is built once per process via `@lru_cache(maxsize=1)`. Every call to `answer_query()` re-uses the same compiled graph — no re-initialization overhead per request.

---

## 4. State Model (AgentState)

**File:** `app/agent/state.py`

```python
class AgentState(TypedDict):
    messages:      Annotated[list[AnyMessage], add_messages]
    project_id:    str
    scope_where:   Optional[dict]
    scope_ids:     Optional[List[str]]
    scope_type:    str
    recommended_k: int
```

### Field Descriptions

| Field | Set by | Read by | Purpose |
|-------|--------|---------|---------|
| `messages` | `service.py` (initial HumanMessage), then every node appends | LLM in `agent` node | Full conversation thread — `HumanMessage`, `AIMessage`, `ToolMessage` |
| `project_id` | `service.py` at entry — NEVER changed | All 5 tools via `InjectedState` | Hard backend enforcement — LLM has no way to override this |
| `scope_where` | `query_scope_node` — set once | `search_transcripts`, `count_signal_chunks` via `InjectedState` | ChromaDB `date_where` clause passed directly to `hybrid_retrieve()` |
| `scope_ids` | `query_scope_node` — set once | `get_meeting_summaries`, `list_speakers`, `count_signal_chunks`, `search_transcripts` (exhaustive path) | Flat list of resolved meeting IDs for metadata filtering |
| `scope_type` | `query_scope_node` — set once | `agent` node (scope note injected into system prompt), `count_signal_chunks` | `"project"` / `"meeting"` / `"date_range"` |
| `recommended_k` | `query_scope_node` — set once | `search_transcripts` via `InjectedState` | Prevents the LLM from under-fetching on project-wide queries |

### Message Accumulation

LangGraph's `add_messages` reducer **appends** — it never replaces the messages list. After a full 3-tool-call exchange, the state contains:
1. `HumanMessage` — original query
2. `AIMessage` — tool call(s) from round 1
3. `ToolMessage` × N — results from round 1 tools
4. `AIMessage` — tool call(s) from round 2 (or final answer)
5. ...

The LLM sees this full thread on every iteration, which enables multi-hop reasoning across tool results.

---

## 5. Node 1 — query_scope (Python-Only)

**File:** `app/agent/query_scope.py`  
**Function:** `query_scope_node(state: AgentState) -> dict`  
**Cost:** ~50ms, zero LLM calls, zero API cost

This node runs exactly once — before the LLM ever sees the query. It uses `parse_meeting_scope()` (from `app/core/scope`) to apply regex patterns to the user's query and resolve any temporal/ordinal meeting reference to concrete ChromaDB filter clauses.

### What It Resolves

| Query phrase            | scope_type | scope_where |
|-------------------------|-----------|-------------|
| `"last meeting"`        | `"meeting"` | `{"meeting_id": {"$eq": "<most_recent_id>"}}` |
| `"previous 3 meetings"` | `"meeting"` | `{"meeting_id": {"$in": ["<id1>","<id2>","<id3>"]}}` |
| `"the third meeting"`   | `"meeting"` | `{"meeting_id": {"$eq": "<third_meeting_id>"}}` |
| `"May 9th"`             | `"meeting"` | `{"meeting_id": {"$eq": "<meeting_on_may_9>"}}` |
| `"last 2 weeks"`        | `"date_range"` | `{"meeting_date": {"$gte": "<cutoff_date>"}}` |
| (no scope phrase)       | `"project"` | `None` |

### Why Scope Resolution Happens Before the LLM

If scope were left to the LLM, it would need to call `list_meetings()` first on almost every query just to discover which meeting is "last". This adds a full tool-call round (and one LLM iteration) to every request. By resolving scope deterministically in Python first and injecting it into state, the LLM can call `search_transcripts` directly without a discovery step.

The agent node communicates this to the LLM by injecting a plain-English `scope_note` into the system message:
> *"SCOPE ALREADY RESOLVED: The meeting reference in this query has been automatically resolved to 'Nolocode Meeting #8' (2026-04-23). Do NOT call list_meetings."*

### Recommended k Computation

```
scope_type == "project"    → recommended_k = 25  (max, broad coverage)
1 meeting in scope         → recommended_k = 15
2 meetings in scope        → recommended_k = 20
3+ meetings in scope       → recommended_k = 25
scope_type == "date_range" → recommended_k = 20
```

`search_transcripts` enforces: `effective_k = max(LLM-supplied k, recommended_k)`. This prevents the LLM from setting `k=5` on a project-wide query where that covers less than 0.3% of the corpus.

---

## 6. Node 2 — agent (LLM + Tools Bound)

**File:** `app/agent/graph.py` — `_make_call_llm()`  
**Model:** `gemini-2.5-flash` (temperature=0)

This node calls the LLM with all 5 tools bound via `llm.bind_tools(TOOLS)`. The LLM receives:
1. A `SystemMessage` containing the full system prompt + scope note
2. All messages in `state["messages"]` (HumanMessage + any prior AIMessage/ToolMessage rounds)

The LLM returns either:
- An `AIMessage` with `tool_calls` set → graph routes to `tools` node
- An `AIMessage` with content only (no `tool_calls`) → graph routes to `END`

### What the LLM Decides

The LLM autonomously decides:
- Which tool(s) to call (from the 5 available)
- What arguments to pass each tool (query text, k, speaker_name, signal_filter)
- Whether one tool call is enough or multiple calls are needed
- When it has sufficient context to write the final answer

The LLM does **not** decide:
- `project_id` — injected server-side, not a tool argument the LLM can set
- `scope_where` — injected server-side, scope is already resolved
- Which meetings to search — the scope filter enforces this automatically

### Scope Note Injection

Before every `agent` node invocation, the node reads `scope_type` and `scope_ids` from state and builds a plain-English scope note that is appended to the system prompt. This:
- Prevents redundant `list_meetings()` calls on scoped queries
- Tells the LLM the human-readable meeting name (`'Nolocode Meeting #7' (2026-04-22)`) rather than raw IDs
- Explicitly says "do NOT call list_meetings — your job is to search within this meeting"

---

## 7. Node 3 — tools (ToolNode)

**File:** `app/agent/graph.py` — `tools_node = ToolNode(TOOLS)`

LangGraph's prebuilt `ToolNode` handles this automatically:
- Extracts all `tool_calls` from the last `AIMessage`
- Calls each tool function with its arguments
- Handles `InjectedState` — reads `project_id` and `scope_where` from the graph state and passes them to tools as the `state` parameter (the LLM never supplies these)
- Wraps each tool's return value in a `ToolMessage`
- Appends all `ToolMessage` objects to state

Multiple tool calls in one `AIMessage` are executed in parallel by `ToolNode`.

---

## 8. The Five Tools

**File:** `app/agent/tools.py`

All 5 tools use `InjectedState` to read `project_id`, `scope_where`, `scope_ids`, `scope_type`, and `recommended_k` from graph state. These are invisible to the LLM — it never sees them in the tool argument schema.

### Tool 1 — `search_transcripts` (Main Workhorse)

```python
def search_transcripts(
    query: str,
    k: int = 15,
    speaker_name: Optional[str] = None,
    signal_filter: Optional[str] = None,
    state: Annotated[dict, InjectedState] = None,
) -> str
```

**Purpose:** Hybrid BM25 + dense vector search over transcript chunks. Used for any question about what was said, decided, committed, asked, or shared.

**Two execution paths depending on inputs:**

**Path A — Exhaustive Signal Scan (when `signal_filter` + `scope_ids` both set):**
- Calls `_exhaustive_signal_search()` — pure metadata fetch from ChromaDB using `collection.get()` with no `k` limit
- Returns **every** chunk with that signal flag in the scoped meeting(s), sorted chronologically
- Result header reads: `"Found N 'decision' chunks (complete scan of 1 meeting(s) — all matches returned)"`
- Why: `hybrid_retrieve` caps at `k=25`. A meeting with 28 question chunks would silently miss 3. Exhaustive scan prevents this.

**Path B — Hybrid Retrieval (all other cases):**
- Calls `hybrid_retrieve(query, project_id, hard_filters, date_where, k)` — BM25 + dense + RRF
- `effective_k = max(LLM-requested k, recommended_k, min 25)`

**Signal filter behaviour (hard vs soft):**

| Signal type      | Category | DB behaviour |
|------------------|----------|-------------|
| `decision`       | HARD | Applied as ChromaDB metadata gate before retrieval |
| `commitment`     | HARD | Applied as ChromaDB metadata gate before retrieval |
| `document_share` | HARD | Applied as ChromaDB metadata gate before retrieval |
| `question`       | SOFT | Injected into query text: `"questions and clarifications raised about {query}"` |
| `open_issue`     | SOFT | Injected into query text: `"unresolved issues problems and blockers about {query}"` |

Soft signals are not gated because questions can be asked without a `?` and issues can be phrased as observations — hard-gating would silently miss them before retrieval starts.

**Speaker name resolution:**
The LLM often guesses speaker names slightly wrong (e.g. `"Bhavneet Mahajan"` vs the stored `"Bhavneet Mhajan"`). ChromaDB `$eq` is exact-match — a wrong name returns 0 results silently.

`_resolve_speaker_name()` resolves approximate names in 4 steps:
1. Exact match
2. Case-insensitive exact match
3. All words in the partial name appear in the candidate name
4. First name only — if uniquely matching one stored name

Falls back to unfiltered search if no match is found.

---

### Tool 2 — `get_meeting_summaries`

```python
def get_meeting_summaries(
    meeting_title: Optional[str] = None,
    state: Annotated[dict, InjectedState] = None,
) -> str
```

**Purpose:** Fetches pre-written meeting summary chunks (`is_meeting_summary=True`) from ChromaDB — no vector search, no BM25. Used for project overviews, meeting recaps, and agenda topics.

Scope is applied automatically: if `scope_ids` is set in state, only summaries from those meetings are returned. LLM can optionally filter further by `meeting_title` (partial match).

Output is sorted chronologically and formatted with `[N]` citation numbers so the LLM can write `[N]` inline in the answer.

---

### Tool 3 — `list_meetings`

```python
def list_meetings(state: Annotated[dict, InjectedState] = None) -> str
```

**Purpose:** Returns meeting titles, dates, and ordinal numbers for all meetings in the project. Used for "how many meetings?", "when was the last meeting?", "which meetings were in April?" queries.

Note: The `query_scope_node` typically prevents the LLM from calling this for "last meeting" style queries. `list_meetings` is only used when the user genuinely asks about the meeting list itself (not as a discovery step for scoping).

---

### Tool 4 — `list_speakers`

```python
def list_speakers(state: Annotated[dict, InjectedState] = None) -> str
```

**Purpose:** Lists all speakers with their roles (`client`, `project_manager`, `developer`) and chunk counts (most talkative first). When `scope_ids` is set, shows only speakers from those meetings.

Used for: "who attended?", "who is the client?", "who spoke most?", "how many people were in the last meeting?"

---

### Tool 5 — `count_signal_chunks`

```python
def count_signal_chunks(
    signal_filter: str,
    speaker_name: Optional[str] = None,
    state: Annotated[dict, InjectedState] = None,
) -> str
```

**Purpose:** Returns the exact count of chunks matching a signal type — no content, no ranking, pure metadata aggregation. Used when the PM asks "how many X?" and does not need to read the actual items.

Signal filter options: `decision`, `commitment`, `question`, `open_issue`, `document_share`.

Scope is applied automatically from state (meeting IDs for `scope_type=="meeting"`, date cutoff for `date_range`).

Returns a hedged count: `"Detected count: 7 'commitment' chunks across all meetings. (Signal detection is regex-based — this is a comprehensive estimate.)"` — the system prompt instructs the LLM to report this as "About 7" not "Exactly 7".

Also accumulates the retrieved docs into the doc accumulator for the citations panel.

---

## 9. Security Enforcement (project_id and scope_where)

The two critical enforcement points are hardened against LLM manipulation via `InjectedState`:

### project_id Enforcement

```
service.py:
  initial_state = {
    "project_id": project_id,  ← from authenticated API call
    ...
  }

tools.py (every tool):
  project_id = state["project_id"]  ← read from state, NOT from LLM arguments
```

The LLM's tool argument schema does not include `project_id`. There is no way for the LLM to supply, override, or influence which project is searched. The `project_id` flows from the API call → graph state → tool functions, entirely server-side.

### scope_where Enforcement

```
query_scope_node:
  scope_where = parse_meeting_scope(query, project_id)
  → writes to state["scope_where"]

tools.py:
  date_where = state.get("scope_where")
  → passed directly to hybrid_retrieve(date_where=date_where)
```

The LLM cannot choose which meetings are searched. Scope is resolved once, deterministically, before the LLM runs. All subsequent tool calls automatically respect this scope — the LLM does not even know the raw meeting IDs (it sees human-readable names in the scope note).

---

## 10. Doc Accumulator & Citations

**File:** `app/agent/tools.py` — `_accumulated_docs`, `_append_docs()`, `reset_doc_accumulator()`, `get_accumulated_docs()`

Because the agent calls tools multiple times in a single request, chunks are retrieved across multiple tool calls. The doc accumulator collects all retrieved chunks across the full ReAct loop into a single list, assigning globally unique `[N]` numbers.

### How It Works

```
Per-request lifecycle:
  1. service.py calls reset_doc_accumulator()  ← clears all state
  2. Each tool call that returns chunks calls _append_docs(docs)
  3. Each chunk gets a globally unique [N] = _chunk_counter++
  4. Deduplication: if chunk_id already seen → return existing [N], skip re-appending
  5. Tools format their output with [N] at the start of each chunk line
  6. LLM writes [N] inline in the answer ("Bhavneet Mahajan (02:34) raised ... [3].")
  7. After graph.invoke(), service.py calls get_accumulated_docs() → builds sources panel
```

### Why Global Numbering Matters

If tool call 1 returns chunks `[1]–[8]` and tool call 2 returns chunks `[9]–[12]`, the LLM sees consistent numbers across its full context. The `[N]` in the LLM's answer maps directly to a source card in the Streamlit UI — no post-processing alignment needed.

### Deduplication

If `search_transcripts` and `get_meeting_summaries` both return the same chunk (e.g. a summary chunk is retrieved by both tools), `_chunk_id_to_num` ensures it appears once in the sources panel with its first-assigned `[N]`.

The accumulator uses in-place mutations (`.clear()`, `.append()`) rather than reassignment (`= []`) to ensure `ToolNode`'s parallel executions all reference the same object.

---

## 11. System Prompt Design

**File:** `app/agent/prompts.py` — `SYSTEM_PROMPT`

The system prompt is the agent's "reasoning manual". It has 4 major sections:

### Section 1 — Tools (When to Use Each)

Describes all 5 tools with:
- What query types each tool handles
- Parameter details (`query`, `k`, `speaker_name`, `signal_filter`)
- When **not** to use a tool (e.g. "Do NOT call list_meetings to find which meeting is 'last' — that is already resolved")
- Notes on special paths (exhaustive scan, soft signals, k limits)

### Section 2 — Query Patterns

Explicit step-by-step instructions for 10+ query patterns:

| Pattern | Instructions |
|---------|-------------|
| COUNT queries | 3 sub-types (signal count only, signal list+count, metadata count, semantic count) |
| When 0 results | 4-step retry protocol: drop signal_filter → drop speaker_name → simplify query → call get_meeting_summaries |
| YES/NO queries | 2-step: summaries first, then search — prevents hallucination |
| Signal filter usage | When to use (explicit type word in query), when NOT to use (general verbs like "highlighted", "mentioned") |
| Document queries | Use `signal_filter='document_share'` |
| Multi-hop Q&A | Step 1: find questions; Step 2: search for each answer |
| Two-speaker queries | Search each separately, then synthesize |
| Chronological comparison | Search both topics, compare `meeting_date` + `start_time` |

### Section 3 — Answer Format Rules

10 mandatory formatting rules:
1. **Attribution** — always full speaker name (no pronouns ever)
2. **Timestamps** — `(MM:SS)` after every speaker name in every bullet
3. **Attribution verbs** — use natural verbs (raised, confirmed, committed to, flagged)
4. **Negative case** — one sentence saying not found + 2–3 sentences on what WAS discussed
5. **Structured topics** — numbered bold headers + attributed sub-bullets
6. **Action items** — bullet list format with owner, timestamp, meeting reference
7. **Decisions** — `Decision: [what] — agreed by [full name] in [meeting]`
8. **Signal counts** — report as "About N" or "At least N" (never "Exactly N")
9. **Anti-hallucination** — only from tool results; say so if absent
10. **Unknown speakers** — use "The team" or "The discussion" (never "Unknown speaker")

### Section 4 — Citation Rules

How to embed `[N]` numbers from tool output inline in the answer:
- Every chunk in tool output has `[N]` at line start (e.g. `[3] Bhavneet Mahajan (02:34) — AI Discussion (2025-04-15)`)
- The LLM must place `[N]` immediately after the factual statement it supports
- Complete format: `Full Speaker Name (MM:SS) [verb] [detail] [N].`
- Multiple citations for same point: `[2][5]`
- No invented `[N]` numbers — only use numbers seen in tool output

---

## 12. Service Layer (answer_query)

**File:** `app/agent/service.py`  
**Function:** `answer_query(query: str, project_id: str) -> dict`

This is the single public entry point for the agent pipeline. It handles:

1. Clears the per-request doc accumulator (`reset_doc_accumulator()`)
2. Builds `initial_state` with `project_id` and default scope fields
3. Invokes the compiled graph: `graph.invoke(initial_state)`
4. Extracts the final answer from the last `AIMessage` in the result (handles both plain string and extended-thinking content block formats from Gemini)
5. Builds sources from accumulated docs via `_build_sources()`
6. Extracts tool call trace via `_extract_tool_calls()` (strips `state` arg — the injected backend fields)
7. Returns structured dict

### Return Schema

```json
{
  "answer":             "LLM-generated answer string",
  "sources":            [
    {
      "chunk_num":       1,
      "speaker_name":    "Bhavneet Mahajan",
      "meeting_title":   "Nolocode Meeting #8",
      "meeting_date":    "2026-04-23",
      "timestamp":       "02:34",
      "content_preview": "First 200 chars of chunk text...",
      "is_summary":      false
    }
  ],
  "tool_calls":         [{"tool": "search_transcripts", "args": {"query": "...", "k": 15}}],
  "intent":             "production_agent",
  "notice":             null,
  "num_context_chunks": 12,
  "model":              "gemini-2.5-flash (agent)",
  "error":              null
}
```

The `intent` field is always `"production_agent"` — the existing Streamlit UI uses this to detect the agent path vs the deterministic RAG path without requiring UI code changes.

### Source Building

`_build_sources()` converts each `Document` in the accumulator into a source card. Key field: `chunk_num` = `_global_chunk_num` set by `_append_docs()` in tools.py — this matches the `[N]` citation numbers the LLM embedded in the answer text, enabling the UI to link inline citations to source cards.

---

## 13. Data Flow: End-to-End Request Trace

### Example: "What questions did Bhavneet raise in the last meeting?"

```
1. service.py
   reset_doc_accumulator()
   initial_state = {messages: [HumanMessage("What questions did Bhavneet raise in the last meeting?")],
                    project_id: "proj_nolocode_001", scope_type: "project", recommended_k: 15}

2. query_scope_node  [~50ms, no LLM]
   parse_meeting_scope("...last meeting...", "proj_nolocode_001")
   → scope_where = {"meeting_id": {"$eq": "meeting_id_10"}}
   → scope_ids   = ["meeting_id_10"]
   → scope_type  = "meeting"
   → recommended_k = 15
   Writes all 4 fields to state.

3. agent node  [LLM call #1]
   System message includes scope_note:
     "SCOPE ALREADY RESOLVED: 'Nolocode Meeting #8' (2026-04-23). Do NOT call list_meetings."
   LLM decides: call search_transcripts
   Issues tool_call: search_transcripts(query="questions raised", signal_filter="question",
                                        speaker_name="Bhavneet Mahajan", k=15)

4. tools node
   InjectedState provides: project_id, scope_where, scope_ids, recommended_k
   search_transcripts executes:
     signal_filter="question" AND scope_ids set → exhaustive path
     _exhaustive_signal_search(project_id="proj_nolocode_001", signal_filter="question",
                                scope_ids=["meeting_id_10"], speaker_name="Bhavneet Mhajan")
     → [speaker resolved: "Bhavneet Mahajan" → "Bhavneet Mhajan" via word-match]
     → collection.get() with AND clauses (project + question=True + meeting_id + speaker)
     → returns 7 chunks, sorted chronologically
     → _append_docs() assigns [1]–[7]
   Returns ToolMessage with formatted 7-chunk result.

5. agent node  [LLM call #2]
   LLM reads ToolMessage with 7 chunks labeled [1]–[7]
   Decides: has enough context, no more tool calls needed
   Writes final answer with full attribution:
     "Bhavneet Mhajan raised 7 questions in Meeting #8 (2026-04-23):
      - Bhavneet Mhajan (03:12) asked about the OCA prepaid formula [1].
      ..."

6. service.py
   Extracts AIMessage content → answer string
   get_accumulated_docs() → 7 Documents
   _build_sources() → 7 source cards with chunk_num matching [1]–[7]
   Returns {answer, sources=[7 cards], tool_calls=[{tool:"search_transcripts",args:{...}}],
            intent:"production_agent", num_context_chunks: 7}
```

---

## 14. Tech Stack

| Component | Technology | Role in Agent Pipeline |
|-----------|-----------|------------------------|
| Agent framework | LangGraph (`langgraph`) | StateGraph, ToolNode, InjectedState, add_messages reducer |
| LLM integration | `langchain-google-genai` | `ChatGoogleGenerativeAI`, `bind_tools()` |
| LLM model | `gemini-2.5-flash` (temperature=0) | Reasoning, tool selection, answer generation |
| Vector database | ChromaDB (local persistent) | Transcript chunk storage + retrieval |
| Embedding model | `gemini-embedding-001` (768-dim) | Dense retrieval in `hybrid_retrieve()` |
| Hybrid search | BM25Okapi + ChromaDB cosine + RRF | `search_transcripts` tool calls this |
| Scope resolution | `app/core/scope.parse_meeting_scope` | Python regex → ChromaDB clauses |
| Speaker resolution | `_resolve_speaker_name()` in `tools.py` | Approximate name → exact stored name |
| API layer | FastAPI | Routes `POST /agent/query` to `answer_query()` |
| UI | Streamlit | Project selector, chat interface, source panel, tool call trace |
| Config | `projects.json` | Project-to-meeting mapping, speaker role assignment |

---

## 15. Comparison: Agent vs Deterministic RAG Pipeline

| Aspect | Deterministic RAG (`app/rag/`) | Agent (`app/agent/`) |
|--------|-------------------------------|----------------------|
| **Routing** | Python classifies intent → 8 hardcoded modes | LLM decides which tools to call |
| **LLM calls per query** | 3 (understanding + rerank + answer) | 1–7 (1 per ReAct iteration; typical = 2) |
| **Multi-hop** | Not supported | Built-in — LLM can issue follow-up calls |
| **Novel query types** | Must add a new retrieval mode | Handled automatically by LLM reasoning |
| **Signal filtering** | Hard-coded in routing rules | LLM decides based on query semantics |
| **Speaker handling** | `compound` mode (3-pass retrieval) | `search_transcripts(speaker_name=...)` |
| **Exhaustive signal scan** | `signal_fetch` mode (mode 8) | Triggered automatically inside `search_transcripts` |
| **Scope resolution** | `understand_query()` (Python before LLM call) | `query_scope_node` (Python before LLM call) |
| **project_id enforcement** | `_build_scope_filter()` in pipeline | `InjectedState` in all 5 tools |
| **Citation numbering** | `extract_sources()` parses answer text | Global `[N]` counter assigned at retrieval time |
| **Reranking** | Gemini Flash Lite reranker (separate step) | Not a separate step — relevance handled by tool design |
| **Context expansion** | Fetches prev/next neighbor chunks | Not implemented — tool results used as-is |
| **Predictability** | High — same query → same mode → same result | Lower — LLM choices can vary |
| **Debuggability** | `retrieval_mode` field shows which path ran | `tool_calls` trace shows which tools ran with what args |
| **Failure mode** | Wrong routing → wrong retrieval mode | Infinite loop (prevented by 6-iteration guard) |

---

*Document based on code review of: `app/agent/graph.py` · `app/agent/tools.py` · `app/agent/state.py` · `app/agent/query_scope.py` · `app/agent/service.py` · `app/agent/prompts.py`*