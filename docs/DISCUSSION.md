# DISCUSSION — AI Meeting Intelligence System

> Running log of all design decisions, open questions, and next discussion topics.
> Update this file at the start/end of every session. It is our shared memory.

---

## What We Are Building

A project-scoped AI chatbot for Project Managers. PM selects a project → asks questions in natural language → gets answers sourced from Fireflies meeting transcripts with speaker attribution, decision tracking, and miscommunication detection.

**One-sentence POC goal:**
> "A Project Manager selects a project, asks any question about what was said, decided, or assigned across all meetings in that project, and gets a correct answer with the exact source — in under 10 seconds."

---

## Current Status

**Phase:** POC COMPLETE ✓ (all 5 phases done, Type 3 deferred by design)

**Last session covered (2026-05-24):**
- Medium query bank: 20 queries in `medium.json` testing 7 routing rules (compound, scoped_count, named_speaker_count, scoped_topic_summary, meeting_summary, hybrid+yesno) — all 20 route correctly
- Extended `test_runner.py` with `--difficulty` flag (`easy`/`medium`/`hard`) and `--ids`/`--tags` filter flags
- `test_retrieval.py` sys.path fix + wrong assertion fix (scoped k ≤ full k) → 46/46 PASS
- Fixed Pydantic crash (`topic: null`) with `@field_validator` coercing `None → ""`
- **Architecture refactor — decoupled `QueryIntent` from all routing decisions:**
  - Added `is_attribution: bool` to `QueryDimensions` (Python `_ATTRIBUTION_RE` regex — no LLM)
  - Attribution routing now uses `u.dimensions.is_attribution` (deterministic), not LLM-classified intent
  - Added `select_template_key(understanding) -> str` to `prompts.py` — maps `retrieval_mode + signal_filter + is_attribution` → correct template key; single source of truth
  - `build_prompt()` and `build_not_found_message()` in `builder.py` now take `template_key: str` (removed `QueryIntent` import from builder)
  - `pipeline.py` uses `select_template_key()` for prompt selection; removed manual `topic_summary` intent override; replaced intent-based speaker fallback with `signal_filter == "question"` check
  - `intent` variable kept in pipeline ONLY for: logging, API response field, reranker hint
- Fixed stale comment on `intent_type` field (was "NOT used in routing" — attribution routing used it)

**Previous session (2026-05-22):**
- Investigated Q3/Q4/Q11 test failures — root cause was Gemini API 503 overload during test run, not pipeline bugs
- Added exponential-backoff retry logic (3 attempts, 2/5/10s delays) to `call_gemini()`, `call_gemini_raw()`, and `evaluate_answer()`
- `understand_query()` now uses `call_gemini_raw` (has retry) instead of raw `genai.Client` call
- Removed unused `Config` and `_CLASSIFIER_MODEL` from `query_intent.py` after refactor
- Updated test runner to distinguish `EVAL_ERR` (evaluator API failed) from genuine `FAIL` / `LOW SCORE`
- **Test result: 12/12 PASS, avg score 8.8/10, avg confidence 0.95**

**What's working right now:**
- Full pipeline: Fireflies webhook → normalize → chunk → stamp project_id + speaker_role → embed → persist to ChromaDB
- `POST /query` endpoint answers all 6 active query types with real grounded answers + source attribution
- All 12 query intents wired: DECISION, COMMITMENT, SUMMARY, SPEAKER, QUESTION, TIMELINE, GENERAL, ANALYTICAL, TOPIC_SUMMARY, ATTRIBUTION, CONTRIBUTION, METADATA
- Scope-first architecture: meeting scope detected before LLM call, propagated to all retrieval functions
- 8-mode retrieval dispatch: hybrid, compound, summary, timeline, topic_summary, analytical, contribution, metadata
- Easy test suite: 12/12 PASS, avg score 8.8/10 (2026-05-22 run)
- Streamlit UI: project selector, chat window, intent badges, source panel, meeting timeline sidebar, speaker list
- 10 meetings in ChromaDB (1,669 chunks), multiple speakers, all metadata at full 5-level schema

---

## Design Decisions (Locked)

| Decision | Choice | Why |
|----------|---------|-----|
| Vector DB | ChromaDB (local) via LangChain Chroma | Free, no server, LangChain abstraction enables future swap |
| Embedding model | `gemini-embedding-001` via `langchain-google-genai` | Gemini API already in use, no extra key needed |
| Chunking strategy | Utterance-based | Speaker metadata stays clean, Fireflies already separates by speaker |
| Scope enforcement | Backend (not UI) | Project A data must never touch Project B — not a UI toggle |
| LLM | Gemini (`gemini-2.5-flash`) for POC | Only Gemini API available; swap to Claude when access granted |
| Classifier (Phase 3) | Rule-based first | Faster for POC, upgrade to LLM if accuracy is poor |
| UI | Streamlit | POC speed, not design |
| Storage abstraction | LangChain Documents | Separates chunk dict (internal) from vector store format (LangChain) |

---

## Open Questions

> Move to "Resolved" once decided.

1. **How does a `project_id` get assigned to a meeting?**
   - **Status: RESOLVED — Session 2**
   - **POC approach:** `projects.json` config file at project root — PM manually maps `project_id → list of meeting_ids`. We generate the `project_id`. No UI needed for POC.
   - **Production approach (Option A):** PM creates a project inside our system, system generates `project_id`, PM links meeting IDs to the project via UI/DB. Build this when scaling beyond POC.
   - Fireflies has no native project concept — Spaces are too broad (company-level), Tags are fragile (typos break grouping).

2. **Speaker role assignment — who is client vs developer vs PM?**
   - **Status: RESOLVED — Session 3**
   - **POC approach:** `speakers` map inside `projects.json` — PM maps each speaker name to role once. Same config file as project_id, zero extra infrastructure.
   - All 6 speakers in Nolocode meeting mapped. New speakers default to `"unknown"` until PM updates the file.
   - Production approach: same as project_id — dedicated UI/DB when scaling.

3. **Which embedding model?**
   - `google-generativeai` is already installed (`text-embedding-004`)
   - Alternatively: Claude does not have a dedicated embedding model → use Google
   - **Status: Lean toward Google embeddings since it's already a dependency**

4. **Where does the LLM answer come from?**
   - Claude API (`claude-sonnet-4-6`) is the current preference
   - Google Gemini (`gemini-2.0-flash`) is also available via installed dependency
   - **Status: Use Claude — confirm with team**

5. **Contradiction detection for Type 3 queries — how deep?**
   - Simple: compare client chunks vs dev chunks, let LLM find contradictions
   - Advanced: dedicated NLP contradiction scoring before sending to LLM
   - **Status: Start simple for POC**

---

## Deferred to Production / Automation Phase

> These are NOT open questions for the POC. They are known gaps that need solving before production. Captured here so they are not forgotten.

### D1 — Auto-registering new meeting IDs (IMPORTANT)

**The problem:** When a new Fireflies meeting fires the webhook in production, its `meeting_id` must already exist in `projects.json` under the right project. Currently this is a manual step — PM or developer adds the ID to the file. The pipeline aborts cleanly if the ID is missing, but that means the meeting is simply not ingested.

**Why this matters at scale:** With many meetings per day, manual `projects.json` updates are not sustainable. This breaks the "automatic" pipeline promise.

**Options to evaluate when building production:**
- A: Listen to a Fireflies "meeting created" webhook event → auto-register the ID to a default project, let PM re-assign later
- B: Build a UI where PM assigns a new meeting to a project before/after it happens
- C: Check if Fireflies Spaces/Topics API can map meeting → project automatically
- D: Unregistered meetings land in a "pending" queue — PM reviews and assigns in bulk

**Current POC behaviour:** Pipeline aborts with a clear warning. No broken data is stored. Safe to run.

**Status: Deferred — solve before production, not needed for POC**

---

## Discussion Log

### Session 23 (2026-05-24) — Prompt Quality Fixes + Mode-Check Test Runner

**Topics covered:**

**1. Gemini fallback summary quality — runaway output fixed**
- Meeting 7 (Nolocode-catchup) had a 283,504-char Gemini summary — runaway output with no token cap
- Added `_SUMMARY_MAX_OUTPUT_TOKENS = 1024` to `gemini_client.py` + passed it as `config` to `generate_content()`
- Re-generated meeting 7 summary → 3,169 chars, proper 3-section format
- ChromaDB re-ingested (1,669 chunks, 10 meetings — same count, 9 meetings with Gemini fallback summaries)

**2. Topic-absent-from-meeting fix**
- Query "What discussion about AI in the previous meeting?" (2026-05-07 meeting has no AI content) returned irrelevant formula chunks
- Fix: for single-meeting `topic_summary` mode, inject the meeting's summary chunk at position [1] so LLM has authoritative ground truth about what the meeting covered
- Added to `pipeline.py` in the `topic_summary` branch — summary chunk prepended before topic chunks
- `topic_summary_query` template updated with explicit "check if topic is present" rule: if NO → state it clearly and describe what the meeting DID cover (no timestamp blocks)

**3. Prompt formatting improvements**
- `_MEETING_SCOPE_PREFIX` rewritten: now instructs LLM to open with `**[Meeting Title] — [YYYY-MM-DD]**` on its own line before the answer (prevents meeting title becoming outer bullet)
- `summary_query` template improved: added routing rules for "What topics?" → numbered list with **Topic** / who raised it / key outcome; speaker attribution comes from Action Items/Overview text in the content (not from the chunk label "Meeting Summary (unknown)")
- `_LIST_PREFIX` clarified: do NOT nest list under meeting header, start directly with item 1
- `topic_summary_query` template: when topic IS absent, do not add timestamp blocks or quotes — stop after describing what the meeting covered

**4. Test runner + pipeline — mode-based routing verification**
- `pipeline.py`: added `retrieval_mode` to the response dict (alongside `intent`, `sources`, `answer`)
- `test_runner.py`: added `expected_mode` / `actual_mode` / `mode_match` fields; when `expected_mode` is set in the query bank, mode_match overrides intent_match for pass/fail
- Medium queries mm_011–mm_015 (topic_summary) now PASS — they route correctly to `topic_summary` mode even though the LLM labels them `general_query` or `summary_query`

**Results:**
- Medium test suite: **20/20 PASS**, avg 8.8/10, avg confidence 0.9 ✓
- Depreciation query verified: correct topic_summary routing, all 3 speakers cited, conversation traced chronologically

**Decisions made:**
- Token cap (1024) is permanent — prevents runaway output on any future long-meeting Gemini summary
- `expected_mode` check takes precedence over `expected_intent` when both are set in query bank — routing mode is more meaningful than LLM intent label after decoupling
- Summary chunk injection for single-meeting topic_summary scope: always prepend so LLM can report topic absence accurately

**What's next:**
- `run_tests.py` master runner (one command for full suite)
- Regression tracker (diff two run folders)
- `hard.json` query bank (10-15 hard queries)

---

### Session 20 (2026-05-22) — Query Accuracy Improvement Plan: All 5 Phases Implemented

**Topics covered:**

**1. Full 30-scenario accuracy analysis + plan finalised**
- Audited all query scenarios against the new architecture plan → 21/24 fixable, 3 known architectural gaps (S10 "importance ranking", S13 "Q&A pairing", S28 "unresolved tracking")
- Root causes: (a) speaker hard-filter before vector search destroys topic relevance, (b) LLM counting from transcript text hallucinates numbers, (c) "previous meeting" / "last meeting" ignored in summary retrieval

**2. Phase 1 — Scope & signal bug fixes**
- `scope.py`: Added `get_scoped_meeting_ids()`, `_THAT_MEETING_RE` ("that/this meeting" → latest), `_ORDINAL_MEETING_RE` ("the second/third meeting" → Nth chronologically)
- `builder.py`: `retrieve_summary_chunks()` calls `parse_meeting_scope()` first — fixes S11, S16
- `chunking.py`: Added `_DOCUMENT_SHARE_RE` + `_OPEN_ISSUE_RE`; `_detect_signals()` now returns 5 signals — fixes S12, S18 after re-ingest
- `query_intent.py`: Expanded `_METADATA_RE` for timing/attendance queries (S7, S8)
- `metadata.py`: Added timing branch (`_get_meeting_timings()`), scope-aware attendance handler using `scoped_ids`

**3. Phase 2 — 3-layer routing + compound retrieval**
- `query_intent.py`: 4 new `QueryIntent` values (ANALYTICAL, TOPIC_SUMMARY, ATTRIBUTION, CONTRIBUTION); `QueryDimensions` model (LLM-filled: `has_topic`, `is_cross_meeting`, `needs_traces`, `is_contribution`; Python-filled: `is_count`, `is_yesno`, `is_ranking`, `is_list_request`, `has_temporal`); 13-rule `ROUTING_RULES` priority matrix; `_post_process_understanding()` wired into `understand_query()`
- `prompts.py`: Updated `UNDERSTANDING_PROMPT_TEMPLATE` — LLM now asked for `signal_filter` + `dimensions`
- `retriever.py`: `compound_retrieve()` — two-pass broad-search → post-filter by speaker (fixes S5, S6, S14, S19, S21, S23, S24, S30)

**4. Phases 3–5 — Analytical layer, new intents, output formats**
- `retriever.py`: `analytical_retrieve()` (DB metadata count, no LLM counting), `topic_summary_retrieve()` (per-meeting topic search), `contribution_retrieve()` (speaker chunk ranking)
- `prompts.py`: 4 new templates + `_COUNT_PREFIX`, `_YESNO_PREFIX`, `_LIST_PREFIX`
- `builder.py`: `build_prompt()` gains `output_format` param — injects prefix when format is count/yesno/list
- `pipeline.py`: 8-mode dispatch in `_retrieve_for_understanding()`; `_handle_structured_result()` for analytical/contribution dict results; `output_format` passed to `build_prompt()`

**5. Re-ingestion completed**
- ChromaDB wiped and re-ingested in DEVELOPMENT_MODE — 1,669 total chunks (10 meetings)
- `contains_document_share` + `contains_open_issue` on all 1,659 transcript chunks
- 5-signal schema fully active in production DB

**Decisions made:**
- Regex-only for all binary signals — no LLM at ingest time
- `chunk_topics` field deferred — not needed for any of the 24 scenarios
- Rule 5 (`signal_count`) guards `NOT has_topic` — prevents global count when topic qualifier is present
- `compound_retrieve()` fallback: if < 3 speaker chunks found, return broad results

**What's next:**
- Run `uv run python -m app.tests.test_runner --project-id proj_nolocode_001` to get new baseline
- Manually test key scenarios: S11/S16 (scope), S5/S22/S29 (new modes)
- Complete Sprint 4: `run_tests.py`, LLM evaluator, regression tracker

---

### Session 19 (2026-05-20) — Sprint 3 Complete + Config Field Normalization

**Topics covered:**

**1. Sprint 3 — All tiers implemented and re-ingested**
- Tier 2a: `start_time`/`end_time` (seconds) + `prev_chunk_id`/`next_chunk_id` added to every chunk
- Tier 2b: `MAX_CHARS` raised 250→500, `_is_low_quality()` junk filter (unique token ratio + meaningful word count), `_TOPIC_SHIFT_RE` topic-shift split for same-speaker blocks
- Tier 2c: `_expand_context()` in `answer_service.py` — fetches prev/next neighbors for top-5 re-ranked docs; neighbors labeled `[CONTEXT — just before/after]`; excluded from `_extract_sources()`
- Re-ingestion: 352 chunks (166 + 186 across 2 meetings), adjacency links all valid

**2. Config.py updated by user — CONSTANT_TRANSCRIPT field format changes**
- `date` field renamed to `dateString` with ISO format (`"2026-03-19T06:44:26.000Z"`)
- Sentence timestamps: `rawStartTimeMs`/`rawEndTimeMs` (int, ms) → `start_time`/`end_time` (float, seconds)
- Second transcript summary: `"summary": "null"` (already handled by `isinstance(summary_raw, dict)` check)

**3. normalize.py updated — unified timestamp + date normalization**
- `dateString` parsed by splitting on `"T"` to get `YYYY-MM-DD` — falls back to `date` field if absent
- Sentence timestamp normalization: detects `rawStartTimeMs`/`rawEndTimeMs` (live Fireflies API) → converts ms → seconds; or uses `start_time`/`end_time` directly (CONSTANT_TRANSCRIPT). Downstream code always sees consistent `start_time`/`end_time` in seconds regardless of source.

**4. chunking.py updated — reads normalized field names**
- `s.get("rawStartTimeMs")` → `s.get("start_time")`
- `s.get("rawEndTimeMs")` → `s.get("end_time")`

**5. CE query accuracy improved**
- After Sprint 3 re-ingestion with larger chunks (MAX_CHARS=500), CE query now correctly attributes to **Bhavneet Mhajan** — no longer Ngũmi Gituro
- Root cause of previous failure: smaller chunks (250 chars) broke Bhavneet's "Is it CE or re?" statement into a decontextualized fragment; larger chunks preserve the full question context

**Decisions made:**
- `normalize.py` is the canonical place for timestamp normalization — chunking.py never reads raw API field names directly, always reads normalized `start_time`/`end_time`
- `fireflies_client.py` GraphQL query keeps `rawStartTimeMs`/`rawEndTimeMs` (correct Fireflies API field names); `normalize.py` converts on the way through

**What's next:**
- Sprint 3 is COMPLETE — all chunking improvements done and verified
- Sprint 4 (automated test suite) is still in progress — `run_tests.py`, LLM evaluator, regression tracker remain

---

### Session 18 (2026-05-20) — Automated Test Suite Built

**Topics covered:**

**1. Hook system deep-dive**
- Explained the two-layer system: CLAUDE.md (instructions to Claude) + `.claude/settings.json` hooks (shell commands at lifecycle events)
- Hooks cannot make Claude write files — they inject `systemMessage` into Claude's context; only CLAUDE.md instructions trigger actual file updates
- Current hooks: `SessionStart` (quest board status), `Stop` (reminder to type "update files")
- Available hook events: `SessionStart`, `Stop`, `PreToolCall`, `PostToolCall`, `UserPromptSubmit`

**2. Automated test suite designed and built**
- Full 6-step pipeline: query bank → query generator → test runner → report generator → summary.md
- Scope: easy-level only for now (medium and hard query banks defined but runner not extended to them yet)

**3. Query bank created (`app/tests/query_bank/`)**
- `easy.json` — 12 queries covering all 5 easy intents; must contain regex-trigger keywords; Gemini-generated queries are grounded in real ChromaDB summary chunks via `--project-id` flag
- `medium.json` — 7 queries requiring LLM intent classification (paraphrased, date-filtered, speaker-name detection)
- `hard.json` — 7 edge-case queries testing graceful degradation, contradiction detection, negative-space reasoning

**4. `query_generator.py` built**
- Reads existing `easy.json` as few-shot examples
- Fetches `is_meeting_summary=True` chunks from ChromaDB via `fetch_meeting_summaries(project_id)` to ground Gemini in real meeting content (not generic hallucinated topics)
- Calls Gemini Flash Lite to generate N new queries matching the schema and difficulty
- Validates schema + deduplicates + re-assigns sequential IDs + merges into `easy.json`
- `--dry-run` flag previews without saving; `--project-id` flag required for grounded generation

**5. `test_runner.py` built**
- Calls `answer_question(query, project_id)` directly (no HTTP, no mocking — real pipeline)
- Captures full pipeline logs using `_LogCapture` handler attached directly to each pipeline logger
- Critical fix: `logging_config.py` sets `propagate=False` on all 4 pipeline loggers — had to attach capture handler directly to each logger, not to the parent `"app"` logger
- Pass criteria: `intent_match=True` AND `has_answer=True` (not a "not found" response)
- Saves `easy_NNN_result.json` per query + `run_metadata.json` aggregate
- Live progress table printed during run with intent mismatch shown inline

**6. `report_generator.py` built**
- Reads latest (or specified) run folder automatically
- Generates `summary.md` with: ASCII progress bar, results table, intent breakdown by type, failed query details with full pipeline trace in code blocks, sources coverage table
- `--run` flag targets a specific run folder

**7. `TESTING_GUIDE.md` created**
- Quick Start (3 commands at the top)
- Mermaid flowchart of the full system
- Folder structure, script reference, pass/fail rules, how to read results
- Manual query addition schema with valid field values
- Project ID reference table

**8. First real test run results (project: proj_nolocode_001)**
- 10/12 passed (83.3%)
- 2 failures: `easy_005` and `easy_011` — both `general_query` misclassified as `summary_query`
- Root cause: queries about "project meetings" and "last project sync" trigger summary intent in the LLM classifier even without explicit summary keywords

**Decisions made:**
- Query generator uses Gemini (not Claude API) — consistent with rest of project stack, no new API key needed
- Log capture attaches to specific loggers directly, not parent — required because of `propagate=False` in `logging_config.py`
- Test results stored in timestamped folders — never overwritten, runs accumulate for future regression comparison

**Open questions from this session:**
- None

**What's next:**
- Option A: `run_tests.py` — one command chains query_generator → test_runner → report_generator
- Option B: LLM answer evaluator — score answer quality 1–10 using Gemini, not just intent match
- Option C: Regression tracker — compare two runs to detect improvements or regressions

---

### Session 17 (2026-05-19) — BM25 Fixes + Full Pipeline Audit

**Topics covered:**

**1. BM25 normalization fix**
- `_tokenize()` in `retriever.py` only did `.lower().split()` — no punctuation removal, no abbreviation handling
- `"C.E."` → token `"c.e."` never matched query token `"ce"` — exact phrase matching was broken
- Fix: Added `_normalize_for_bm25(text)`: lowercase → collapse abbreviations → remove punctuation → collapse whitespace
- `_tokenize()` updated to call it — both corpus and query go through same function, always in sync
- `import re` added to `retriever.py`

**2. Acronym canonicalization fix (Issue 3 — P1)**
- Initial regex `(?<=[a-z])\.(?=[a-z])` only handled dot-between-letters. Failed for `C. E.` (dot+space), `C-E` (dash), `C/E` (slash)
- Replaced with general pattern: `(?<!\w)[a-z](?:\s*[.\-\/]+\s*[a-z])+[.\-\/]*(?!\w)` using lambda to strip non-letters from match
- Handles: `C.E.→ce`, `P.M.→pm`, `U.S.A.→usa`, `C-E→ce`, `C. E.→ce` — all acronym variants, not just CE
- Requires at least one dot/dash/slash — plain `"c e"` (space only) is NOT merged (safe)

**3. Full chunk text logging added to retriever.py**
- Previous logging: 90-char preview only — impossible to debug accuracy issues
- Added `_log_chunk_list(label, docs)` — logs each doc with full TEXT, speaker, meeting, chunk_id, signals
- `hybrid_retrieve()` now logs three separate stages: `STAGE 1a — DENSE`, `STAGE 1b — BM25`, `STAGE 2 — HYBRID (after RRF)`
- `retrieve_documents()` also updated to use `_log_chunk_list`
- Watch with: `Get-Content pipeline.log -Wait -Encoding utf8`

**4. Full pipeline audit — all 3 production steps already complete**
- Discovered that tracking files (SPRINT.md, TODO.md, TASKS.md) were stale — all 3 steps are fully implemented
- `query_intent.py`: `understand_query()` + `QueryUnderstanding` (topic, intent_type, named_speaker, needs_summary, temporal_focus) — LLM primary, regex fallback ✓
- `prompts.py` (new file): `CLASSIFIER_SYSTEM_PROMPT` + `UNDERSTANDING_PROMPT_TEMPLATE` + `ANSWER_PROMPT_TEMPLATES` (7 templates) ✓
- `reranker.py`: `rerank_documents()` with origin-vs-discussion scoring, Gemini Flash Lite, fallback to original order ✓
- `answer_service.py`: full 5-step pipeline — understand → hybrid_retrieve(k=25) → rerank → top 10 → LLM answer ✓

**5. Chunking issues identified (7 issues researched)**
- Issue 1: Hard char split (MAX_CHARS=250) can split semantically connected sentences — MEDIUM impact
- Issue 2: No `prev_chunk_id`/`next_chunk_id` — retriever gets decontextualized chunks — HIGH impact
- Issue 3: Weak junk detection (`len >= 8` only) — MEDIUM impact on BM25 corpus quality
- Issue 4: No ASR corruption detection (abrupt sentence endings) — LOW-MEDIUM for this dataset
- Issue 5: No speaker confidence — depends on Fireflies API plan
- Issue 6: No topic-shift detection (same speaker, different topic merged) — MEDIUM for BM25
- Issue 7: No timestamps (`rawStartTimeMs`/`rawEndTimeMs` not fetched) — HIGH for temporal queries

**6. Adjacency linking design decision**
- Question: store `prev/next` IDs only, or inline the text too?
- Decision: **IDs only** — text already in DB, `collection.get(ids=[...])` is O(1) free lookup. Inline text = 3× storage duplication, ChromaDB metadata size limits.
- Expansion strategy: **post-rerank, top 5 only** — NOT on all 25 candidates
  - Re-ranker scores clean 25-chunk list → picks top 5 → expand context only for those 5 = 10 DB lookups max
  - Expanding all 25 before re-ranking = 50 DB calls + bloated re-ranker input = wrong approach
  - At any data scale, always exactly 10 extra lookups per query (constant cost)
- Implementation: `expand_context()` function added after re-rank step in `answer_service.py` — Tier 2

**What's next:**
- All 3 production steps complete — Sprint 2 is done
- Tier 2 re-ingestion pass: `prev_chunk_id`/`next_chunk_id`, timestamps from Fireflies API, soft char limits, junk detection — all chunking fixes in one re-ingestion

---

### Session 16 (2026-05-18) — Production Architecture: Retrieval Accuracy Problem + Plan

**Topics covered:**

**1. Pipeline logging fixed**
- `pipeline.log` file handler confirmed working — logs captured correctly
- Terminal display was broken because `─` (U+2500) and `↳` (U+21B3) in log messages are not in Windows cp1252 encoding, causing `StreamHandler.emit()` to fail silently
- Fix: replaced `_SEP = "─" * 62` with `_SEP = "-" * 62` and `"    ↳ %s"` with `"    -> %s"` in `answer_service.py` — all ASCII now, displays cleanly everywhere
- Watching logs: `Get-Content pipeline.log -Wait -Encoding utf8` in a second terminal

**2. Retrieval accuracy problem identified**
- Example query: "Which team member raised the confusion around CE classification code?"
- System returned: Karan (wrong) — his chunk had strong keyword matches ("CE", "code", "query")
- Correct answer: Rhythm Jalhotra — she introduced the confusion, but her chunk had fewer keyword matches
- Root cause: vector similarity search ranks by topic mention density, not by causal origin. Karan was responding to the confusion; Rhythm was the one who raised it.
- This is a broader problem class: "who raised X", "who was confused about Y", "who first mentioned Z", "who disagreed with W" — all fail the same way

**3. Production architecture designed**
- Problem with current architecture: hard-coded 7-intent routing means every new query pattern requires new code (new intent + new retrieval function + new prompt)
- Three-component production pipeline agreed:
  - **Step 1: Flexible Query Understanding** — replace fixed 7-intent classifier with LLM JSON extraction: `{topic, intent_type, named_speaker, needs_summary}`. New query patterns handled by LLM automatically, no code changes.
  - **Step 2: Hybrid Retrieval (BM25 + Dense)** — current pure vector search misses exact phrases. BM25 handles "CE classification code" exact match; dense handles semantic similarity. Combined via Reciprocal Rank Fusion, k=25 candidates.
  - **Step 3: LLM Re-ranking** — after broad retrieval, one Gemini Flash Lite call scores all 25 chunks against the true query intent. Re-ranker reads both query AND chunk simultaneously — understands "raised confusion" ≠ "mentioned topic". Promotes Rhythm's chunk (expressing confusion) over Karan's (discussing topic). Fixes ALL current and future query patterns without special-casing.

**4. Decisions: what NOT to build right now**
- **Meeting index (fast-path lookup)**: deferred. One LLM call per meeting to extract structured topics/confusion/decisions. Not needed since re-ranking handles these queries. Can add later for meta queries like "how many topics were discussed?"
- **`contains_confusion` signal in chunking**: deferred. Would be free (regex), but re-ranking handles confusion queries already without it.
- **Per-chunk LLM enrichment at ingestion**: explicitly rejected. 200 chunks per meeting × LLM call = unacceptable cost. Wrong direction entirely. Cost should scale with queries, not with data size.

**Implementation order decided:**
1. Step 3 (LLM Re-ranking) first — highest impact, zero schema changes, no re-ingestion
2. Step 2 (BM25 Hybrid) second
3. Step 1 (Flexible Query Understanding) last — replaces current classifier

**What's next:**
- Start implementing Step 3: LLM re-ranker after current retrieval

---

### Session 15 (2026-05-18) — Pipeline Logging + Dev Mode Bug Fix

**Topics covered:**
- User noticed terminal showed no pipeline activity when submitting Streamlit queries
- Built a full pipeline trace logger: every query now prints a 4-step trace to stderr in the terminal where `streamlit run` was launched
- Diagnosed root cause of "DB shows zero / pipeline not running": `DEVELOPMENT_MODE` was missing from `.env`, defaulting to `false`. Production path requires a live Fireflies webhook payload — empty `{}` → 3 retries → drops. Nothing stored.
- Fixed by adding `DEVELOPMENT_MODE=true` to `.env`
- Confirmed 521 docs already in ChromaDB from previous session are intact; skip-check correctly prevents re-ingestion

**What was built:**
- `app/logging_config.py` — new: `setup_pipeline_logging()` wires a clean stderr handler
- `streamlit_app.py` — calls `setup_pipeline_logging()` at startup
- `answer_service.py` — 4-step trace: CLASSIFY → RETRIEVE (each doc shown) → BUILD PROMPT → LLM CALL → DONE
- `query_intent.py` — logs matched regex pattern per classification
- `retriever.py` — logs each retrieved doc with meeting/date/speaker/content preview; removed old noisy log line
- `.env` — `DEVELOPMENT_MODE=true` added

**Decisions made:**
- Pipeline logging writes to stderr (not stdout) so Streamlit doesn't swallow it
- Noisy third-party libraries suppressed to WARNING level — only our modules at DEBUG

**What's next:**
- POC is complete. Post-POC roadmap: Type 3 Miscommunication Detection (highest value), D1 auto-registration, role-based speaker queries, multi-project scale test

---

### Session 14 (2026-05-14) — Phase 5 Validation Complete: POC DONE

**Topics covered:**
- Ran full 30-question accuracy test — initial run: 28/30 (2 logic failures, 13 SSL errors from Windows proxy rate-throttling)
- Fixed logic failure 1: `_SPEAKER_RE` was checked AFTER `_QUESTION_RE` in classifier — "What did Ngumi say about the **questions**?" routed to QUESTION intent instead of SPEAKER. Fix: moved SPEAKER check before QUESTION in `classify_query_intent()`.
- Fixed logic failure 2: Q13 must_contain `["property"]` was too strict — answer covered fixed assets correctly without that specific word
- Added 1-second sleep between test questions to prevent SSL rate-throttling on rapid consecutive embedding API calls
- Re-ran full test after fixes: 30/30 (100% accuracy, 0 errors)
- Ran scope isolation test: fake `project_id` returns "not found" with 0 sources on all 3 test queries — no data leakage across project boundary
- Ran multi-meeting synthesis test: summary, timeline, and commitment queries all correctly span both meetings
- Ran speed test: avg 3.4s, max 4.6s — all 6 query types well under the 10s target

**Results:**

| Test | Result |
|------|--------|
| Accuracy (30 questions) | 30/30 — 100% |
| Scope isolation | PASS — 0 data leakage |
| Multi-meeting synthesis | PASS — all 3 queries span both meetings |
| Speed | PASS — avg 3.4s, max 4.6s (target <10s) |
| Miscommunication (Type 3) | DEFERRED — needs design discussion |
| PM usability | Not run (Nice to Have) |

**What was built/fixed:**
- `query_intent.py`: SPEAKER check moved before QUESTION check — prevents speech-act patterns with "questions" in them from being misrouted
- `test_queries.py`: 4 must_contain keywords fixed (fragile year/word matches replaced with more stable keywords); 1-second sleep added between questions
- `validate_poc.py`: created — scope isolation, multi-meeting synthesis, speed tests in one script

**Recommendation for full product build:**
- Core RAG pipeline is production-ready for the implemented query types
- Type 3 (Miscommunication Detection) is the highest-value feature not yet built — design needed
- Role-based speaker queries documented in `FUTURE_SCOPE.md` — build when PM feedback shows it's needed
- Auto-registration of new meeting IDs (D1 in Deferred section) must be solved before production — current manual `projects.json` approach won't scale
- SSL/proxy issue on Windows dev machine is environment-specific; production server won't have this problem

**POC STATUS: COMPLETE** — all 5 phases done (Type 3 deferred by design)

---

### Session 13 (2026-05-14) — Type 6 Timeline Query Complete + 30 Test Questions

**Topics covered:**
- Verified the 2-meeting dataset supports Type 6 before implementing (`check_timeline.py`)
- Confirmed: meetings dated 2026-05-08 (231 chunks) and 2026-05-14 (288 chunks); 5 topics span both (AI module, scenario modeling, timeline, module, approach)
- Implemented `retrieve_timeline_documents()` in `retriever.py` — runs one semantic search per meeting, merges results sorted chronologically. This ensures both meetings contribute equally rather than the query skewing toward one.
- Added `get_meeting_ids_for_project()` to `project_store.py` — used by the timeline retriever
- Expanded `_TIMELINE_RE` in `query_intent.py` — old version only matched explicit timeline keywords (`deadline`, `schedule`). Added cross-meeting comparison patterns: `between.*meetings`, `how did.*change`, `across both`, `compared to the first/second meeting`, `evolved`, etc.
- Verified: all 4 test timeline questions correctly classified as `timeline_query` and return sources from both meetings
- Verified answer quality: "How did the AI module discussion change between meetings?" → correct chronological answer highlighting the shift from "on hold" (May 8) to "actively comparing two approaches" (May 14)
- Added 4 new test questions to `test_queries.py` (now 30 total, 5 per type)

**What was built:**
- `project_store.py`: `get_meeting_ids_for_project()` added
- `retriever.py`: `retrieve_timeline_documents()` added — per-meeting semantic search, sorted by date
- `answer_service.py`: TIMELINE intent now routes to `retrieve_timeline_documents()` instead of plain `retrieve_documents()`
- `query_intent.py`: `_TIMELINE_RE` expanded with 8 new patterns
- `test_queries.py`: 4 new questions added (decision meeting 2, timeline cross-meeting x2, speaker Harsh Vardhan, commitment meeting 2) — total now 30

**Decisions made:**
- Timeline retrieval: k=6 per meeting (not k=10 globally). With N meetings, total docs = N*6. For 2 meetings = 12 docs, sufficient for a 2-period comparison prompt. If meetings grow, k can be tuned.
- Timeline prompt already had the right instruction ("present chronologically, highlight what changed between meetings") — no prompt change needed.

**What's next:**
- Phase 5 Validation: run all 30 test questions, scope isolation test, speed test
- Type 3 Miscommunication Detection: deferred, needs further design discussion

---

### Session 12 (2026-05-14) — Second Transcript + Streamlit UI Complete

**Topics covered:**
- User added a second transcript ("Nolocode AI meeting", id: `01KMHQSBYB1RAGY2X4EP6DCMC9`) to `app/config.py`
- Identified that `CONSTANT_TRANSCRIPT` was already a list — but `normalize_transcript()` and dev mode only processed one item
- Fixed `normalize.py` to handle `"summary": "null"` (string null) — now coerces any non-dict summary to `{}`
- Updated dev mode in `webhook_handler.py` to loop over all transcripts in the list, with skip-if-already-ingested check
- Updated `projects.json` — new meeting ID added, 3 new speakers added (Ashpreet Singh=client, Nolocode AI=client, Harsh Vardhan Dixit=developer)
- Diagnosed and fixed ChromaDB HNSW index corruption — was caused by partial write; fix was wipe + clean re-ingest
- Verified Gemini fallback summary generation for meeting 2 (no Fireflies summary → Gemini generated 992-char accurate summary)
- Completed Streamlit UI: sidebar (project selector, metrics, meeting list, speaker list with role icons, query guide), chat window, intent badges, source panel, example questions
- Added `ttl=120` to `@st.cache_data` decorators, cache-clear on project switch, Refresh button in sidebar

**What was built:**
- `streamlit_app.py` — full Streamlit UI, now complete
- `webhook_handler.py` dev mode — loops over all transcripts in list (not just first)
- `normalize.py` — string null summary guard
- `projects.json` — 2 meetings, 9 speakers

**Current ChromaDB state:**
- 2 meetings: "Nolocode meeting with Ashpreet" (2026-05-08, 232 docs) + "Nolocode AI meeting" (2026-05-14, 289 docs)
- 521 total documents (519 transcript chunks + 2 summary chunks)
- 9 speakers: Ngũmi Gituro, Project Manager SFS, Karan Middha, Bhavneet Mhajan, Rhythm jalhotra, Neha, Ashpreet Singh, Nolocode AI, Harsh Vardhan Dixit

**Decisions made:**
- When `"summary"` field is a string (Fireflies returns "null" as a literal string for some meetings), treat it as missing — Gemini fallback runs automatically
- Dev mode ingest is idempotent: skip check prevents duplicate storage on re-runs; wipe `chroma_db/` folder for a clean re-ingest
- Cache TTL of 120s is sufficient for POC — no real-time ingestion happening

**What's next:**
- Phase 3 remaining: Type 6 real date-range filtering (now testable with 2 meetings), 4 more test questions to reach 30
- Phase 5 Validation: all prerequisites met — can start accuracy testing

---

### Session 1 (2026-05-08) — Full POC Design

**Topics covered:**
- POC definition — what we're building and why (gap vs Otter.ai)
- System architecture: Fireflies → Ingestion → ChromaDB → RAG → LLM → Streamlit
- Hierarchy rule: Company → Project → Meetings → Speakers (project_id filter is backend law)
- 5-phase POC timeline
- Query taxonomy — 6 types, why each needs different handling
- Metadata schema — 5 levels, each field mapped to which query types it enables
- Chunking strategy confirmed: utterance-based

**Decisions made:** See "Design Decisions" table above.

**Left for next session:** How project_id gets assigned (Open Question 1), speaker role mapping (Open Question 2), start Phase 1 implementation.

---

### Session 2 (2026-05-09) — project_id Design Decision

**Topics covered:**
- Investigated whether Fireflies can provide a native `project_id` — confirmed it cannot (no project concept, Spaces are company-level, Tags are fragile)
- Evaluated 3 options for project_id assignment
- Decided POC approach: `projects.json` config file (PM maps meeting IDs to project manually)
- Decided production/scale approach: Option A — PM creates projects in our system, we generate `project_id`, PM links meetings via UI/DB

**Decisions made:**
- POC uses `projects.json` — simple, no UI required, correct and reliable
- Option A is the target architecture for production — documented in TASKS.md for when we build at scale

**Open questions resolved:** Q1 (project_id assignment) ✓

**Left for next session:** Resolve Open Question 2 (speaker role assignment), then start Phase 1 implementation

---

### Session 3 (2026-05-10) — Phase 1 Metadata + project_store

**Topics covered:**
- Resolved Q2: speaker roles added to `projects.json`, `get_speaker_role()` in project_store.py
- Upgraded `chunking.py` to full 5-level schema — all fields present (placeholders for classifier fields)
- Created `app/services/storage/` module — `project_store.py` with project + role lookup
- Wired `_stamp_project_and_roles()` into webhook_handler — every chunk gets project_id + speaker_role
- Fixed UTF-8 encoding bug in project_store.py (Windows cp1252 default broke unicode speaker names)
- Renamed fields: `date→meeting_date`, `speaker→speaker_name`, `sequence→chunk_index`

**Decisions made:**
- Speaker roles stored in `projects.json` alongside project_id — same file, same pattern, no extra infra

**Open questions resolved:** Q2 (speaker role assignment) ✓

**What's next:** ChromaDB install + db.py + chunk_store.py — then the storage TODO in webhook_handler can be replaced

---

### Session 4 (2026-05-10) — ChromaDB Live + Pipeline Verified

**Topics covered:**
- ChromaDB installed, `db.py` and `chunk_store.py` built — full storage layer complete
- `store_chunks()` uses upsert — re-ingestion safe, no duplicates
- Verified full pipeline end to end: 232 chunks stored and retrieved with all metadata correct
- Fixed `meeting_number` — now auto-computes from ChromaDB (counts distinct meetings for project + 1)
- Fixed pipeline guard — if `meeting_id` not in `projects.json`, pipeline aborts cleanly before storing
- Fixed `chunking.py` to read `meeting_number` from `meeting_meta` instead of hardcoding `0`
- Identified and documented D1 (auto-registration of new meeting IDs) as deferred production problem

**Decisions made:**
- POC requires manual `meeting_id` registration in `projects.json` — acceptable for now
- D1 documented in "Deferred to Production" section — will need a proper solution before production launch
- ChromaDB uses default `all-MiniLM-L6-v2` embeddings for POC — Phase 2 will evaluate switching to Google `text-embedding-004`

**Open questions resolved:** None this session (all POC questions resolved)

**What's next:** Content signal detection (`contains_decision`, `contains_commitment`) + meeting summary chunk — last 2 remaining Phase 1 tasks

---

### Session 8 (2026-05-13) — Retriever + Query Intent + Architecture Review

**Topics covered:**
- Reviewed full codebase — significant Phase 2 + Phase 3 progress built
- `retriever.py` complete: `retrieve_documents()` enforces `project_id` scope on every call, dedicated helpers for commitment/question/decision retrieval
- `query_intent.py` complete: `classify_query_intent()` maps query → 7 `QueryIntent` enum values, covers all 6 query taxonomy types
- `answer_service.py` is a stub — hardcoded dummy values, needs full implementation
- `pipeline.py` and `chroma_store.py` are empty files — can be deleted or used later
- `main.py` has no `/query` endpoint yet — cannot answer questions
- `projects.json` speaker keys already cleaned ("Karan Middha" ✓)
- `inspect_db.py` already updated to use `get_raw_collection()`
- `chunking.py` signals improved with `_FALSE_COMMITMENT_RE` to reduce false positives

**Architectural issues identified:**
1. `answer_service.py` is not connected to retriever or query_intent — the 3 pieces exist in isolation
2. SUMMARY intent must use `is_meeting_summary=True` raw collection filter, not vector search (LLM gets confused by semantic search for summaries)
3. `get_chunks_by_meeting()` uses dummy query `"meeting transcript"` for similarity search — functional workaround but semantically wrong; use raw collection instead for exact metadata lookups
4. No prompt templates exist yet — all 6 query types need different prompts for quality answers

**Decisions made:**
- `retrieve_decision_candidates()` intentionally does NOT filter `contains_decision=True` — decision signals are weak hints, semantic search is more reliable. LLM validates from full context. This is correct.
- `query_intent.py` is the Phase 3 classifier — already done, moves Phase 3 forward
- Next build target: `answer_service.py` complete implementation + `/query` endpoint

**What's next:** Implement `answer_service.py` (wire query_intent → retriever → Gemini LLM → sources) + `/query` endpoint → Phase 2 complete

---

### Session 11 (2026-05-14) — Name-Based Speaker Architecture

**Topics covered:**
- Decided to simplify architecture: remove role-based querying entirely for now
- Queries now use speaker names ("What did Bhavneet say?") not roles ("What did the client say?")
- Role-based querying documented in `FUTURE_SCOPE.md` with full design for when it's needed

**What changed:**
- `_SPEAKER_RE` in `query_intent.py`: replaced role keywords with speech-act patterns (`what did [name] say/mention/discuss`). Negative lookahead prevents "we/they/the/you" from triggering SPEAKER intent.
- `answer_service.py`: removed `_detect_speaker_role()` entirely. New `_detect_speaker_name(query, project_id)` scans the project's speaker list, matches full name then first name, handles diacritics (Ngumi → Ngũmi Gituro).
- SPEAKER and QUESTION intents both now filter by `speaker_name` (not `speaker_role`)
- `trace_query.py`: fixed stale import, added QUESTION branch, updated all descriptions
- `FUTURE_SCOPE.md`: created — documents role-based querying, Type 3, name fuzzy matching, Type 6 date filter

**Verified:**
- "What questions did Bhavneet Mahajan raise?" (note: typo in last name) → correctly resolved to "Bhavneet Mhajan" via first-name match → `contains_question=True + speaker_name=Bhavneet Mhajan` → 1 source only (Bhavneet), no PM/dev leakage

**Decisions made:**
- Name-based querying is the POC approach — covers 90% of real PM queries without role assignment complexity
- Role-based querying deferred to `FUTURE_SCOPE.md` — will build after Streamlit UI is complete if needed
- `speaker_role` field kept in chunk metadata (dormant) — future scope can use it without re-ingesting

**What's next:**
- Phase 3 remaining: Type 6 date range filtering (multi-meeting), complete test questions to 30
- Phase 4: Streamlit UI

---

### Session 10 (2026-05-14) — Speaker Role Fix + QUESTION Intent Bug

**Topics covered:**
- Found that Bhavneet Mhajan was stored as `speaker_role="developer"` in both `projects.json` and ChromaDB — confirmed he is a client
- Fixed `projects.json` → re-ingested 232 chunks in dev mode → verified all 3 Bhavneet chunks now show `speaker_role="client"` in ChromaDB
- Identified root cause of PM chunks appearing in "What questions did the client raise?" results:
  - `query_intent.py` checks `_QUESTION_RE` before `_SPEAKER_RE` (line 132 vs 139)
  - Query matched QUESTION intent → retrieved all `contains_question=True` chunks regardless of speaker
  - Fix: `_retrieve_for_intent()` in `answer_service.py` now calls `_detect_speaker_role()` for QUESTION intent and appends `speaker_role` to the filter dict when a role keyword is found
  - `_build_filter()` in `retriever.py` handles multiple filters via `$and` — no changes needed there

**Decisions made:**
- QUESTION intent with a speaker role keyword → applies BOTH `contains_question=True` AND `speaker_role=<role>` filters. Correct behavior: "What questions did the client raise?" should only return client chunks.
- QUESTION intent without a speaker keyword → fetches `contains_question=True` from any speaker (unchanged behavior)

**Bugs fixed:**
- Bhavneet Mhajan: wrong role in `projects.json` + ChromaDB — corrected and re-ingested
- QUESTION intent ignoring speaker role in query — fixed in `_retrieve_for_intent()`

**What's next:**
- Phase 3 remaining: Type 5 speaker name extraction (currently role-only), Type 6 date range filtering (multi-meeting), complete test questions to 30

---

### Session 9 (2026-05-13) — Phase 2 Complete: answer_service + /query endpoint

**Topics covered:**
- Implemented `app/services/answer_service.py` in full — was a stub with hardcoded dummy values
- Added `POST /query` endpoint to `main.py`
- Re-ingested meeting in dev mode — 232 chunks now stored with Gemini embeddings, correct signals, summary chunk
- Fixed ChromaDB 1.5 multi-condition filter bug (flat dict → `$and` operator)
- Migrated both Gemini files from deprecated `google.generativeai` → `google.genai` SDK
- Updated Gemini model: `gemini-1.5-flash` → `gemini-2.5-flash` (older versions removed from API)
- Added missing `langchain-chroma` and `langchain-google-genai` to `pyproject.toml`
- Validated all 6 query types end-to-end — all return real answers with sources

**What was built in `answer_service.py`:**
- `classify_query_intent(query)` → routes to correct retrieval strategy per intent
- SUMMARY intent: uses `get_raw_collection().get()` with `$and` filter — NOT vector search (fetches all summary chunks chronologically)
- DECISION intent: broad semantic search (no `contains_decision` filter — weak signal design, confirmed correct)
- COMMITMENT intent: `retrieve_commitment_documents()` with `contains_commitment=True` filter
- SPEAKER intent: detects `client`/`developer`/`project_manager` from query text, adds `speaker_role` filter
- TIMELINE/GENERAL/QUESTION: standard `retrieve_documents()` with intent-specific prompt
- 7 prompt templates — one per `QueryIntent` type, each with rules tailored to what the LLM must focus on
- `_extract_sources()` deduplicates `{meeting_title, meeting_date, speaker_name}` across retrieved docs
- Returns `{answer: str, sources: list, intent: str}`

**Bugs found and fixed:**
- ChromaDB 1.5+ rejects flat dicts with >1 key in `where` — must use `{"$and": [{"field": {"$eq": val}}, ...]}` syntax. Fixed in both `retriever.py` (`_build_filter()`) and `answer_service.py` (`_retrieve_summary_chunks()`)
- `google.generativeai` package deprecated and removed — migrated to `google.genai`, model updated to `gemini-2.5-flash`
- `langchain-chroma` and `langchain-google-genai` were installed but not in `pyproject.toml` — added via `uv add`

**Decisions made:**
- Gemini LLM for answer generation: `gemini-2.5-flash` — most capable available model on this API key
- SUMMARY query skips vector search entirely by design — fetching the summary chunk by metadata is faster and more accurate than trying to semantically match it
- `retrieve_decision_candidates()` still has NO `contains_decision` filter — intentional, decision signals are weak

**Open questions resolved:** Q4 (LLM for answer generation → Gemini `gemini-2.5-flash`) ✓

**What's next:** Phase 3 Type 3 (Miscommunication Detection) + Phase 4 Streamlit UI

---

### Session 7 (2026-05-13) — LangChain + Gemini Embeddings Architecture

**Topics covered:**
- Adopted LangChain as the abstraction layer for ChromaDB — `langchain-chroma`, `langchain-google-genai`, `langchain-core`
- Replaced raw ChromaDB client with LangChain `Chroma` vector store — embeddings now happen automatically at store time
- Embedding model: `gemini-embedding-001` via `GoogleGenerativeAIEmbeddings` (stored in `app/services/embeddings/gemini_embeddings.py`)
- Added `app/services/documents/mapper.py` — converts internal chunk dicts → LangChain `Document(page_content, metadata)` before storage
- Rewrote `db.py` — `get_vectorstore()` (LangChain Chroma singleton) + `get_raw_collection()` (raw ChromaDB for metadata-only ops like `get_distinct_meeting_ids()`)
- Rewrote `chunk_store.py` — `store_documents()` replaces `store_chunks()`
- Pipeline now has 6 steps (added step 5: convert to Documents, step 6: store + embed)
- **Key insight:** Phase 2 embedding task is now complete as a side effect — embeddings are wired end-to-end

**Decisions made:**
- LangChain adopted as the abstraction layer — enables swapping embedding model or vector DB later without changing pipeline logic
- `gemini-embedding-001` is the embedding model for POC (Gemini API key already in `.env`)
- `get_distinct_meeting_ids()` bypasses LangChain and hits raw ChromaDB directly — avoids unnecessary embedding call for a pure metadata lookup
- `get_chunks_by_meeting()` uses `similarity_search(query="meeting transcript", filter=...)` as a workaround since LangChain Chroma has no pure "get by metadata" without vector search

**What's next:** Fix `inspect_db.py` for new architecture → update `projects.json` speaker keys → re-ingest → Phase 1 complete → Phase 2 retriever + chat_model + /query endpoint

---

### Session 6 (2026-05-13) — Git Setup + Merge Conflicts + DB Inspection

**Topics covered:**
- Fixed git global config — `user.name = "Sahil Aggarwal"`, `user.email = "sfs.sahilaggarwal25@gmail.com"`
- Fixed GitHub authentication — switched from password to classic PAT (token with `repo` scope)
- Resolved merge conflicts between local and remote `sahil_fireflies_poc` branch:
  - Remote had `clean_with_gemini()` per-sentence Gemini approach in `normalize.py` — dropped (decided against it)
  - Remote had `create_chunks()` commented out — kept our full implementation
  - Remote had `webhook_handler.py` pipeline commented out — kept our complete 5-step pipeline
  - Took `_clean_speaker_name()` from remote — strips Fireflies platform IDs e.g. "Karan Middha U0438EU2CSX" → "Karan Middha". Now applied in `normalize_transcript()` so all speaker names are clean before chunking.
  - Took `group_by_speaker()` utility from remote — kept as utility, not wired into main pipeline
- Created `inspect_db.py` — one-command tool to inspect ChromaDB state (chunk count, projects, signals, sample)
- Ran inspection: 232 chunks stored, all signals False, 0 summary chunks — because these were ingested before signal detection and summary chunk were built
- **Finding:** existing chunks need re-ingestion to pick up `contains_decision`, `contains_commitment`, `contains_question`, and summary chunk. Pipeline uses upsert so it's safe.

**Decisions made:**
- `_clean_speaker_name()` is now applied during `normalize_transcript()` — speaker names are cleaned before reaching the chunker or ChromaDB
- `projects.json` speaker keys like "Karan Middha U0438EU2CSX" should be updated to cleaned names ("Karan Middha") to match what normalize now outputs

**What's next:** Re-ingest existing meeting (trigger dev mode pipeline) to update all 232 chunks with signals + add summary chunk → then Phase 1 is complete → Phase 2 (RAG engine)

---

### Session 5 (2026-05-10) — ASR Cleaning + Summary Chunk + Content Signals

**Topics covered:**
- Researched Otter.ai chunking strategy — not publicly documented, inferred as speaker-based (same as ours). One confirmed thing: they strip filler words programmatically before indexing.
- Evaluated semantic chunking — concluded it is the WRONG direction. Destroys speaker attribution which is required for Type 3, 5, 2 queries. ArXiv paper confirms: not worth the cost for meeting transcripts.
- Implemented regex-based ASR noise cleaning in `normalize.py` — removes fillers before chunking, drops sentences that collapse below 8 chars.
- Implemented meeting summary chunk — uses Fireflies `summary.overview` when available, Gemini 1.5 Flash fallback when not. Cost ~$0.001/meeting.
- Created `app/clients/gemini_client.py` — Gemini is the only LLM available for POC development (no Claude API access yet).
- Implemented content signal detection (`contains_decision`, `contains_commitment`, `contains_question`) — rule-based regex in `chunking.py`. Chose regex over LLM: meeting language is explicit, signals are pre-filters not main retrieval, and 200+ API calls per meeting adds unacceptable latency.

**Decisions made:**
- Gemini (not Claude) is used for POC LLM calls — POC only has Gemini API access
- Content signals: regex for POC, upgrade to LLM-based classifier in Phase 3 only if accuracy is poor on real transcripts
- Semantic chunking is NOT being pursued — utterance-based is correct for speaker-filtered queries

**Phase 1 status after this session:** 9/10 Must Do tasks complete. One remaining: speaker normalization verification.

**What's next:** Verify speaker_id slug consistency across multiple meetings → Phase 1 complete → start Phase 2 (RAG engine)

---

---

## Production Architecture (Post-POC)

> POC is complete and validated. The section below documents the agreed production-level retrieval architecture. POC code is NOT removed — production changes are additive.

### Problem With POC Architecture (Why It Doesn't Scale)

Current pipeline is a hard-coded decision tree:
```
Query → fixed 7-bucket intent → pre-wired retrieval per bucket → LLM answer
```
Every new query pattern (origin, disagreement, confusion, first-mention) requires:
1. New intent value in the enum
2. New retrieval function
3. New prompt template
4. New regex fallback
This will never stop. There are infinite query patterns.

Also: pure vector search ranks by keyword/semantic similarity, not by causal relevance.
"Who raised confusion about CE code?" → Karan (wrong, more keywords) instead of Rhythm (correct, fewer keywords).

### Production Pipeline — 3 Components

```
Query
  │
  ▼
Step 1 — Flexible Query Understanding    (1 LLM call — replaces 7 fixed intents)
  │       LLM extracts JSON:
  │       {topic, intent_type, named_speaker, needs_summary, temporal_focus}
  │       New query patterns handled automatically — no code changes needed
  │
  ▼
Step 2 — Hybrid Retrieval                (zero LLM cost — pure math)
  │       BM25 keyword search + Dense vector search
  │       Combined via Reciprocal Rank Fusion → k=25 candidates
  │       Better recall: exact phrases (BM25) + semantic meaning (dense)
  │
  ▼
Step 3 — LLM Re-ranking                  (1 LLM call — core accuracy fix)
  │       Scores all 25 chunks against the true query intent
  │       Understands "raised confusion" ≠ "mentioned topic"
  │       Works for ANY query type without new code
  │       Returns top 8-10 chunks
  │
  ▼
Step 4 — Answer Generation               (1 LLM call — same as POC)
```

### What Each Step Fixes

| Step | Problem it solves |
|---|---|
| Query Understanding | Stops "add new intent for every pattern" cycle |
| Hybrid Retrieval | Exact phrases like "CE code" missed by pure embeddings |
| Re-ranking | Wrong chunk ranked #1 (Karan vs Rhythm) — fixes ALL future cases |

### Decisions Locked for Production

| Decision | Choice | Why |
|---|---|---|
| Re-ranking model | Gemini Flash Lite (already in stack) | 1 call per query, ~$0.001, no new dependency |
| BM25 library | `rank_bm25` Python library | No new database needed, works alongside ChromaDB |
| Query understanding | LLM JSON extraction | Flexible, no fixed taxonomy, handles any pattern |
| Meeting index | **Deferred** | Re-ranking handles origin/causal queries; add later only for meta queries |
| Per-chunk LLM enrichment | **Rejected** | Scales with data size, not queries — wrong cost model |
| `contains_confusion` signal | **Deferred** | Re-ranking makes it unnecessary for now |

### Implementation Order

1. **Step 3 (Re-ranking)** — implement first. Highest impact, no schema changes, no re-ingestion.
2. **Step 2 (BM25 Hybrid)** — implement second. Improves recall for exact phrases.
3. **Step 1 (Flexible Query Understanding)** — implement last. Replaces current 7-intent classifier.

---

## Phase Progress Tracker

| Phase | Status | Blocking On |
|-------|--------|-------------|
| Phase 1 — Foundation (ChromaDB + Metadata) | ✓ 100% COMPLETE | — |
| Phase 2 — RAG Engine | ✓ 100% COMPLETE | — |
| Phase 3 — Query Taxonomy | 80% ACTIVE | Type 6 real date-range filter, 4 more test questions |
| Phase 4 — Streamlit UI | ✓ 100% COMPLETE | — |
| Phase 5 — Validation | 0% READY | Phase 3 complete |

---

## What Otter.ai Does vs What We Do

| Feature | Otter.ai | Our System |
|---------|----------|------------|
| Auto transcription | Yes | Via Fireflies |
| Speaker identification | Yes | Yes |
| Keyword search | Yes | Yes + semantic |
| AI summary per meeting | Yes | Yes |
| Cross-meeting intelligence | **No** | **Yes** |
| Project-scoped isolation | **No** | **Yes** |
| Miscommunication detection | **No** | **Yes** |
| Decision tracking across meetings | **No** | **Yes** |
| Action item tracking with owner | **No** | **Yes** |

---

## Quick Reference Links

| File | What's in it |
|------|-------------|
| `TASKS.md` | Full task list with Must Do tags, metadata schema reference |
| `DONE.md` | Everything already implemented in codebase |
| `TODO.md` | Ordered remaining tasks + new folder structure to create |
| `DEVELOPMENT_GUIDE.md` | Architecture diagram, key files, env setup, data flow |
| `app/handlers/webhook_handler.py` | Main pipeline — full 5-step pipeline, storage + summary chunk wired |
| `app/services/transcript/chunking.py` | Utterance chunking + signal detection + summary chunk builder |
| `app/clients/gemini_client.py` | Gemini 1.5 Flash — meeting summary fallback |
