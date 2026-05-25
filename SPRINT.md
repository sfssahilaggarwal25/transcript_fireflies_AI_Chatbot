# SPRINT 6 — Query Accuracy Improvement  [COMPLETE]

> All 5 phases of the query accuracy improvement plan implemented in Session 20 (2026-05-22).
> 21 of 24 previously-failing scenarios now fixed. ChromaDB re-ingested: 1,669 chunks, 10 meetings.
> Easy test suite: **12/12 PASS, avg 8.8/10** (verified 2026-05-22 after retry logic added).
> Session 23 (2026-05-24): Prompt quality fixes + mode-check test runner. Medium suite: **20/20 PASS, avg 8.8/10**.

```
╔══════════════════════════════════════════════════════╗
║     SPRINT 6 — QUERY ACCURACY                       ║
║     "Fix the 24 failing scenarios"                  ║
╠══════════════════════════════════════════════════════╣
║  Phase 1 — Scope bug fixes      ✓ COMPLETE          ║
║  Phase 2 — Compound retrieval   ✓ COMPLETE          ║
║  Phase 3 — Analytical layer     ✓ COMPLETE          ║
║  Phase 4 — New intent types     ✓ COMPLETE          ║
║  Phase 5 — Output format polish ✓ COMPLETE          ║
║  Re-ingestion: 1,669 chunks     ✓ 10 meetings       ║
║  Scenarios fixed: 21/24                             ║
║  Known gaps: S10, S13, S28 (need design work)       ║
║  Easy test suite: 12/12 PASS    ✓ avg 8.8/10        ║
║  API retry logic added          ✓ 2026-05-22         ║
╚══════════════════════════════════════════════════════╝
```

### What was built

- `app/services/answer/scope.py` — `get_scoped_meeting_ids()`, `"that/this meeting"` + ordinal patterns
- `app/services/answer/builder.py` — scope-first summary retrieval, `output_format` param in `build_prompt()`
- `app/services/transcript/chunking.py` — 2 new signals: `contains_document_share`, `contains_open_issue`
- `app/services/query_intent.py` — `QueryDimensions` model, 4 new intents, 13-rule `ROUTING_RULES`, `_fill_syntactic_dimensions()`, `_post_process_understanding()`
- `app/services/answer/metadata.py` — timing handler, scoped attendance counts
- `app/services/retrieval/retriever.py` — `compound_retrieve()`, `analytical_retrieve()`, `topic_summary_retrieve()`, `contribution_retrieve()`
- `app/services/prompts.py` — 4 new answer templates, `_COUNT_PREFIX`, `_YESNO_PREFIX`, `_LIST_PREFIX`
- `app/services/answer/pipeline.py` — 8-mode dispatch, `_handle_structured_result()`, output_format wiring

### Known gaps (require separate design work)

| Scenario | Reason | Future path |
|----------|---------|-------------|
| S10: Which topic was most important? | "Importance" is subjective | Add mention-count as proxy |
| S13: Can we answer all of Bhavneet's questions? | Needs Q&A chunk pairing | New post-processing stage |
| S28: Which unresolved issue discussed last? | No `is_resolved` tracking | Resolution detection in reranker |

---

---

# SPRINT 5 — Agentic Tool Calling for Compound Queries  [PLANNED]

> Enables the LLM to compose metadata + semantic retrieval itself for analytical questions
> that cannot be answered by a single retrieval path.
> Prerequisite: Sprint 4 test suite must be complete so regressions are caught.

```
╔══════════════════════════════════════════════════════╗
║     SPRINT 5 — LLM TOOL CALLING                     ║
║     "Let the LLM decide how to retrieve"            ║
╠══════════════════════════════════════════════════════╣
║  Tool definitions (4 tools)     [ ] Not started     ║
║  Gemini function-calling loop   [ ] Not started     ║
║  Fallback to current pipeline   [ ] Not started     ║
║  Test suite coverage            [ ] Not started     ║
╚══════════════════════════════════════════════════════╝
```

### Why tool calling — and why NOT for simple metadata queries

Simple metadata queries (list meetings, list speakers, count meetings) are handled
by the `METADATA` intent short-circuit in `answer_question()` — 0 LLM calls, ~80ms.
Tool calling is NOT needed there.

Tool calling IS needed for **compound analytical queries** where the LLM must decide
which retrieval operations to compose:

| Query | Why the code can't pre-determine the path |
|---|---|
| "How many times did Sahil mention the budget?" | Needs speaker filter (metadata) + semantic search (budget) + count |
| "Which meeting had the most unresolved questions?" | Needs all meetings (metadata) + question density per meeting |
| "Did we discuss deployment in the May 9th meeting?" | Needs date filter (metadata) + semantic search within that meeting |

### Tools to define (Gemini function calling schema)

```python
tools = [
    {
        "name": "search_transcripts",
        "description": "Semantic search over transcript chunks for a topic",
        "parameters": {
            "query": str,          # semantic search string
            "project_id": str,     # required — scope enforcement
            "speaker_name": str,   # optional filter
            "meeting_date": str,   # optional ISO date filter
            "k": int,              # number of results
        }
    },
    {
        "name": "list_meetings",
        "description": "List all meetings in the project with dates",
        "parameters": {"project_id": str}
    },
    {
        "name": "list_speakers",
        "description": "List all speakers and their roles in the project",
        "parameters": {"project_id": str}
    },
    {
        "name": "count_chunks_matching",
        "description": "Count transcript chunks matching a speaker + keyword filter",
        "parameters": {
            "project_id": str,
            "speaker_name": str,   # optional
            "keyword": str,        # BM25 keyword to match
        }
    },
]
```

### Implementation plan

1. Define tool schemas as dicts matching Gemini function-calling format
2. Pass tools to `client.models.generate_content()` with `tools=` parameter
3. If response contains `function_call`: execute the named function, send result back as `function_response`
4. Loop until LLM returns a text answer (max 3 tool calls per query)
5. If no tool call in first response: fall back to current `answer_question()` pipeline
6. Every tool call must enforce `project_id` — no exceptions

### Critical constraint

`project_id` must be injected server-side into every tool call argument — never
trusted from the LLM's output. The LLM receives it as context but the backend
validates and re-applies it on every tool execution.

---

---

# SPRINT 1 — POC: Foundation through Validation  [COMPLETE]

> Phases 1–5 complete. POC validated 2026-05-14.

```
╔══════════════════════════════════════════════════════╗
║           POC — ALL PHASES                          ║
║           Phases 1 → 5 Complete                     ║
╠══════════════════════════════════════════════════════╣
║  XP Earned:  1500 / 1500 XP   COMPLETE              ║
║  Accuracy:   30/30 (100%)                           ║
║  Speed:      avg 3.4s (target <10s)                 ║
╚══════════════════════════════════════════════════════╝
```

### What was built
- ChromaDB + Gemini embeddings storage pipeline
- Full 5-level chunk metadata schema
- 7-intent query classifier + per-intent retrieval strategies
- Gemini-powered answer generation with source attribution
- Streamlit UI — project selector, chat history, intent badges, source panel
- 30-question test suite — 100% pass rate

### What was deferred
- Type 3 Miscommunication Detection — needs design discussion
- Auto-registration of new meeting IDs — manual `projects.json` for now

---

---

# SPRINT 2 — Production: Retrieval Architecture Upgrade  [COMPLETE]

> All 3 steps implemented and wired. Full 5-step pipeline running:
> understand_query → hybrid_retrieve(k=25) → rerank_documents → top 10 → LLM answer

```
╔══════════════════════════════════════════════════════╗
║     PRODUCTION — RETRIEVAL UPGRADE                  ║
╠══════════════════════════════════════════════════════╣
║  Step 3 — LLM Re-ranking        ✓ COMPLETE          ║
║  Step 2 — BM25 Hybrid           ✓ COMPLETE          ║
║  Step 1 — Flexible Query        ✓ COMPLETE          ║
║  BM25 Normalization fix         ✓ Session 17        ║
║  Acronym canonicalization       ✓ Session 17        ║
║  Full chunk text logging        ✓ Session 17        ║
╚══════════════════════════════════════════════════════╝
```

### What was built

- `app/services/retrieval/reranker.py` — `rerank_documents()` with origin-vs-discussion scoring, Gemini Flash Lite, fallback to original order
- `app/services/retrieval/retriever.py` — `hybrid_retrieve()`, `_fetch_project_corpus()`, `_bm25_search()`, `_rrf_merge()` + BM25 normalization + 3-stage full-text logging
- `app/services/query_intent.py` — `understand_query()` returning `QueryUnderstanding`; LLM-first + regex fallback; `classify_query_intent()` upgraded
- `app/services/prompts.py` — new file: classifier prompt + understanding prompt + 7 answer templates
- `app/services/answer_service.py` — full 5-step pipeline; date filtering; `_subject_topic_hint()`

---

---

# SPRINT 4 — Test Suite & Evaluation Infrastructure  [IN PROGRESS]

> Automated testing pipeline so any pipeline change can be verified quickly.
> New developers and testers can run the full suite in 3 commands.
> Started Session 18 (2026-05-20). Latest run (Session 23): **21/21 easy PASS, 20/20 medium PASS**.

```
╔══════════════════════════════════════════════════════╗
║     SPRINT 4 — AUTOMATED TEST SUITE                 ║
║     "Verify pipeline quality after every change"    ║
╠══════════════════════════════════════════════════════╣
║  Query bank (easy)              ✓ 21 queries        ║
║  Query bank (medium)            ✓ 20 queries        ║
║  Query bank (hard)              [ ] Not written     ║
║  query_generator.py             ✓ COMPLETE          ║
║  test_runner.py + flags         ✓ --difficulty      ║
║                                   --ids --tags      ║
║                                   mode-check        ║
║  report_generator.py            ✓ COMPLETE          ║
║  TESTING_GUIDE.md               ✓ COMPLETE          ║
║  test_retrieval.py (no-LLM)     ✓ 46/46 PASS        ║
║  Easy suite: 21/21 PASS         ✓ avg 9.0/10        ║
║  Medium suite: 20/20 PASS       ✓ avg 8.8/10        ║
║  run_tests.py (master runner)   ✓ COMPLETE          ║
║  Regression tracker             [ ] Not started     ║
╚══════════════════════════════════════════════════════╝
```

### What was built

- `app/tests/query_bank/easy.json` — 21 queries, 7 easy intents, schema: `expected_intent`, `expected_mode`, `tags`, `notes`, `evaluation_hints`
- `app/tests/query_bank/medium.json` — 20 meeting-scoped queries testing 7 routing rules (compound, scoped_count, named_speaker_count, scoped_topic_summary, meeting_summary, hybrid+yesno) — Session 22
- `app/tests/query_generator.py` — Gemini-powered query generation grounded in real ChromaDB summary chunks; `--project-id`, `--count`, `--dry-run` flags
- `app/tests/test_runner.py` — calls real `answer_question()` directly; `_LogCapture` per logger; live progress table; per-query JSON results + `run_metadata.json`; `--ids`, `--tags`, `--difficulty` flags; mode-check support (`expected_mode` / `actual_mode`) — Session 23
- `app/tests/report_generator.py` — `summary.md` with ASCII progress bar, results table, intent breakdown, failed query traces
- `app/tests/TESTING_GUIDE.md` — Mermaid flowchart, 3-command quick start, full script reference
- `app/tests/test_retrieval.py` — 46-assertion no-LLM retrieval test (BM25 tokenizer, adaptive k, hybrid, compound, analytical, topic_summary) — Session 21

### Also done this sprint (Session 22) — QueryIntent decoupled from routing

- `query_intent.py` — `is_attribution` dim + `_ATTRIBUTION_RE` regex; attribution routing uses dimension not intent
- `prompts.py` — `select_template_key()` — single source of truth for template selection
- `builder.py` — `build_prompt(template_key: str)` — no longer depends on `QueryIntent`
- `pipeline.py` — uses `select_template_key()`; removed manual topic_summary intent override; speaker fallback scoped to `signal_filter == "question"`

### What's remaining in Sprint 4

- [ ] `run_tests.py` — one command: query_generator → test_runner → report_generator → open summary.md
- [ ] Regression tracker — diff two run folders to detect improvements/regressions
- [ ] `hard.json` — write 10-15 hard queries (cross-meeting synthesis, contradiction, negative-space)

---

## Sprint 4 Progress

```
Query bank (easy)                 [██████████] 100%  ✓ 21 queries
Query bank (medium)               [██████████] 100%  ✓ 20 queries
Query bank (hard)                 [          ]   0%  Not written
query_generator.py                [██████████] 100%  ✓ COMPLETE
test_runner.py + flags            [██████████] 100%  ✓ --difficulty --ids --tags + mode-check
report_generator.py               [██████████] 100%  ✓ COMPLETE
TESTING_GUIDE.md                  [██████████] 100%  ✓ COMPLETE
test_retrieval.py (no-LLM)        [██████████] 100%  ✓ 46/46 PASS
Easy suite green                  [██████████] 100%  ✓ 21/21 PASS avg 9.0/10
Medium suite green                [██████████] 100%  ✓ 20/20 PASS avg 8.8/10
run_tests.py                      [██████████] 100%  ✓ COMPLETE
Regression tracker                [          ]   0%  Not started

OVERALL                           [█████████░]  88%
```

---

---

# SPRINT 3 — Chunking Improvements  [COMPLETE]

> Completed Session 19 (2026-05-20). All tiers done in one re-ingestion pass.

```
╔══════════════════════════════════════════════════════╗
║     SPRINT 3 — CHUNKING + CONTEXT EXPANSION         ║
║     "Better raw material for the pipeline"          ║
╠══════════════════════════════════════════════════════╣
║  Tier 2a — Schema additions     ✓ COMPLETE          ║
║  Tier 2b — Chunking quality     ✓ COMPLETE          ║
║  Tier 2c — Context expansion    ✓ COMPLETE          ║
║  Re-ingestion: 352 chunks       ✓ COMPLETE          ║
║  CE query accuracy verified     ✓ Bhavneet correct  ║
╚══════════════════════════════════════════════════════╝
```

## Sprint 3 Progress

```
Tier 2a — Schema additions        [██████████] 100%  ✓ COMPLETE
Tier 2b — Chunking quality        [██████████] 100%  ✓ COMPLETE
Tier 2c — Context expansion       [██████████] 100%  ✓ COMPLETE

OVERALL                           [██████████] 100%  ✓ COMPLETE
```

### What was built

- `chunking.py` — `MAX_CHARS=500`, `_is_low_quality()`, `_TOPIC_SHIFT_RE`, `start_time`/`end_time`, `prev_chunk_id`/`next_chunk_id`
- `normalize.py` — `dateString` ISO parsing; unified `start_time`/`end_time` normalization (handles both API ms format and CONSTANT_TRANSCRIPT seconds format)
- `answer_service.py` — `_expand_context()` fetches prev/next neighbors for top-5 re-ranked docs
- Re-ingested: 352 chunks (2 meetings), all adjacency links valid, timestamps in seconds
