# DONE — Completed Work

> Everything listed here is implemented and working in the codebase.

---

## Session 20 (2026-05-22) — Query Accuracy Improvement Plan: All 5 Phases

**Phase 1 — Scope & signal fixes:**
- [x] `app/services/answer/scope.py` — `get_scoped_meeting_ids(scope_where, project_id) -> set[str]` converts ChromaDB where-clause to meeting ID set; handles `$eq`, `$in`, `$gte` variants
- [x] `app/services/answer/scope.py` — `_THAT_MEETING_RE` ("that/this meeting" → most recent meeting); `_ORDINAL_MEETING_RE` + `_ORDINAL_INDEX` ("the second/third/fourth/fifth meeting" → sorted_meetings[-(idx+1)])
- [x] `app/services/answer/builder.py` — `retrieve_summary_chunks()` now calls `parse_meeting_scope()` first before `extract_month_day()` fallback — fixes S11 ("agenda of the previous meeting"), S16 ("summary of the last meeting")
- [x] `app/services/transcript/chunking.py` — `_DOCUMENT_SHARE_RE` (shared docs, files, links, spreadsheets); `_OPEN_ISSUE_RE` (problems, discrepancies, unresolved issues, concerns flagged). `_detect_signals()` returns 5 signals. `flush_chunk` bypass includes new signals. Fixes S12, S18 after re-ingest.
- [x] `app/services/query_intent.py` — `_METADATA_RE` expanded: timing queries ("timings of meetings", "how long was the meeting", "when did meeting start"), attendance ("how many people/participants/attendees", "who attended X meeting")
- [x] `app/services/answer/metadata.py` — `_TIMING_RE`, `_ATTENDANCE_RE`, `_ATTENDANCE_RE` patterns; `_get_meeting_timings()` aggregates max `end_time` per meeting → duration in minutes; timing branch in `handle_metadata_query()`; attendance branch now filters by `scoped_ids` (S7, S8)

**Phase 2 — 3-layer routing + compound retrieval:**
- [x] `app/services/query_intent.py` — 4 new `QueryIntent` enum values: `ANALYTICAL` ("analytical_query"), `TOPIC_SUMMARY` ("topic_summary_query"), `ATTRIBUTION` ("attribution_query"), `CONTRIBUTION` ("contribution_query")
- [x] `app/services/query_intent.py` — `QueryDimensions` Pydantic model: LLM-filled (`has_topic`, `is_cross_meeting`, `needs_traces`, `is_contribution`) + Python-filled (`is_count`, `is_yesno`, `is_ranking`, `is_list_request`, `has_temporal`)
- [x] `app/services/query_intent.py` — `QueryUnderstanding` extended with `signal_filter`, `retrieval_mode`, `output_format`, `dimensions` fields
- [x] `app/services/query_intent.py` — `_fill_syntactic_dimensions()` (deterministic regex for Python-filled fields); `RoutingRule` frozen dataclass; 13-rule `ROUTING_RULES` priority matrix (structural_metadata → contribution → attribution → scoped_count → signal_count → named_speaker_count → semantic_count → any_count_fallback → compound_any_speaker → topic_summary → meeting_summary → cross_meeting_timeline → hybrid_default); `_apply_routing()`; `_derive_output_format()`; `_post_process_understanding()` — wired into `understand_query()`
- [x] `app/services/prompts.py` — `UNDERSTANDING_PROMPT_TEMPLATE` updated: now asks LLM for `signal_filter` + `dimensions` (LLM-semantic fields only); includes `attribution_query` intent type; `has_topic` guidance for subject-action words
- [x] `app/services/retrieval/retriever.py` — `compound_retrieve(query, project_id, named_speaker, signal_filter, date_where, k_broad=40, k_final=25)` — two-pass: broad hybrid search (no speaker filter) → post-filter by normalized speaker name → signal_filter applied → fallback to broad if < 3 speaker chunks. Fixes S5, S6, S14, S19, S21, S23, S24, S30.

**Phase 3 — Analytical layer:**
- [x] `app/services/retrieval/retriever.py` — `analytical_retrieve(project_id, signal_filter, date_where, named_speaker) -> dict` — pure ChromaDB metadata count (no vector search, no LLM counting). Returns `{total_chunks, signal_count, meeting_count, meetings, speaker_count, speakers, signal_filter, named_speaker}`. Fixes S3, S4, S8, S12.
- [x] `app/services/prompts.py` — `analytical_query` template: LLM formats pre-computed numbers; strictly prohibited from inventing counts.
- [x] `app/services/answer/pipeline.py` — `_handle_structured_result()` formats analytical/contribution dicts into context strings and calls LLM; `answer_question()` detects `isinstance(raw_result, dict)` and short-circuits to this handler.

**Phase 4 — New intents:**
- [x] `app/services/retrieval/retriever.py` — `topic_summary_retrieve(topic, project_id, date_where, k_per_meeting=8)` — per-meeting `hybrid_retrieve` for the topic, merged chronologically. Fixes S22, S25.
- [x] `app/services/retrieval/retriever.py` — `contribution_retrieve(project_id, date_where) -> dict` — counts chunks per speaker, returns ranked list with `{speaker_name, chunk_count, meeting_count}`. Fixes S29.
- [x] `app/services/prompts.py` — `topic_summary_query` template (chronological topic evolution); `attribution_query` template (temporal origin identification); `contribution_query` template (ranked speaker table).

**Phase 5 — Output format polish:**
- [x] `app/services/prompts.py` — `_COUNT_PREFIX` (answer MUST begin with exact count), `_YESNO_PREFIX` (answer MUST begin with YES or NO), `_LIST_PREFIX` (answer MUST be a numbered/bulleted list)
- [x] `app/services/answer/builder.py` — `build_prompt(query, context, intent, output_format="prose")` — injects `_COUNT_PREFIX`, `_YESNO_PREFIX`, or `_LIST_PREFIX` before template when `output_format` is count/yesno/list

**Pipeline wiring:**
- [x] `app/services/answer/pipeline.py` — `_retrieve_for_understanding()` rewritten as 8-mode dispatch: `summary`, `timeline`, `compound`, `analytical`, `contribution`, `topic_summary`, `metadata`, `hybrid`. Each mode calls the correct retrieval function. Hybrid branch applies `signal_filter` as `hard_filters` key. `build_prompt()` calls pass `understanding.output_format`.
- [x] `app/services/answer/pipeline.py` — chronological sort extended to `compound` and `topic_summary` modes; rerank skipped for `topic_summary` (chronological already correct)

**Re-ingestion:**
- [x] ChromaDB wiped and re-ingested in DEVELOPMENT_MODE — 1,669 chunks (1,659 transcript + 10 summary) across 10 meetings; `contains_document_share` + `contains_open_issue` present on all transcript chunks; 16 doc-share and 74 open-issue chunks flagged True

---

## Session 19 (2026-05-20) — Sprint 3: Chunking Improvements + Config Normalization

**Sprint 3 — All tiers complete:**

**Tier 2a — Schema additions:**
- [x] `app/clients/fireflies_client.py` — `rawStartTimeMs`/`rawEndTimeMs` in GraphQL sentences query (live API)
- [x] `app/services/transcript/chunking.py` — `start_time`/`end_time` stored per chunk (seconds); reads from normalized sentences
- [x] `app/services/transcript/chunking.py` — `prev_chunk_id`/`next_chunk_id` added via post-loop linking pass; first chunk `prev=None`, last chunk `next=None`

**Tier 2b — Chunking quality fixes:**
- [x] `MAX_CHARS` raised 250 → 500 — reduces semantic splits at utterance boundaries
- [x] `_is_low_quality(text)` — drops chunks if unique token ratio < 0.4 OR meaningful word count (non-stopword, len>2) < 4
- [x] `_TOPIC_SHIFT_RE` — splits same-speaker block when sentence starts with `"now"`, `"next"`, `"another point"`, `"separately"`, `"also"`, `"moving on"`, `"switching to"`, `"on another"`, `"by the way"`
- [x] `_STOPWORDS` frozenset — used by `_is_low_quality()` to determine meaningful word count

**Tier 2c — Context expansion:**
- [x] `_EXPAND_TOP_N = 5` constant in `answer_service.py`
- [x] `_expand_context(documents, n=5)` — for top-5 re-ranked docs, fetches `prev_chunk_id`/`next_chunk_id` neighbors via `collection.get(ids=[...])`; tags neighbors with `_position='before'/'after'` in metadata; prevents duplicates via `existing_ids` set; max 10 DB lookups per query
- [x] `_build_context()` updated — labels neighbor chunks as `[CONTEXT — just before/after]`
- [x] `_extract_sources()` updated — skips chunks where `meta.get("_position")` is set (neighbors not shown as sources)
- [x] Wired into `answer_service.py` pipeline: `documents = _expand_context(documents)` after rerank step (skipped for SUMMARY intent)

**Config.py field normalization:**
- [x] `app/services/transcript/normalize.py` — `dateString` parsing: splits ISO string on `"T"` → `YYYY-MM-DD`; falls back to `date` field if `dateString` absent
- [x] `app/services/transcript/normalize.py` — timestamp normalization in cleaned_sentences: detects `rawStartTimeMs`/`rawEndTimeMs` (live API, ms int) → converts to seconds; or uses `start_time`/`end_time` directly (CONSTANT_TRANSCRIPT, seconds float). Downstream always receives consistent `start_time`/`end_time` in seconds.
- [x] `app/services/transcript/chunking.py` — updated to read `s.get("start_time")` / `s.get("end_time")` (not `rawStartTimeMs`/`rawEndTimeMs`)

**Re-ingestion verified:**
- [x] ChromaDB wiped and re-ingested — 352 chunks (166 Nolocode meeting with Ashpreet 2026-03-19 + 186 Nolocode AI meeting 2026-03-25)
- [x] All chunks have correct `meeting_date`, `start_time`/`end_time` (seconds), `prev_chunk_id`/`next_chunk_id`
- [x] CE query accuracy verified — Bhavneet Mhajan correctly identified (larger chunks preserve question context)

---

## Session 18 (2026-05-20) — Automated Test Suite

**Test infrastructure (`app/tests/`):**
- [x] `app/tests/query_bank/easy.json` — 12 easy-level queries covering all 5 easy intents (summary, decision, commitment, question, general); schema includes `expected_intent`, `expected_strategy`, `tags`, `notes`, `evaluation_hints`
- [x] `app/tests/query_bank/medium.json` — 7 medium-level queries (paraphrased, date-filtered, speaker name detection, cross-meeting); LLM classifier required
- [x] `app/tests/query_bank/hard.json` — 7 hard edge-case queries (contradiction detection, relative dates, negative-space reasoning, yes/no questions that may have no answer)

**`app/tests/query_generator.py`:**
- [x] `fetch_meeting_summaries(project_id)` — fetches `is_meeting_summary=True` chunks from ChromaDB to ground Gemini in real meeting content (prevents hallucinated off-topic queries)
- [x] `_build_prompt(existing_queries, count, summaries)` — injects real meeting summaries + regex keyword map + JSON schema + existing queries as few-shot examples
- [x] `call_gemini(prompt)` — Gemini Flash Lite via `google.genai`, same pattern as `answer_service.py`
- [x] `validate_queries()` — schema check + intent check + deduplication against existing queries
- [x] `save_merged()` — auto-increments IDs, merges with existing, updates count in `_metadata`
- [x] CLI: `--project-id` (grounds queries in real ChromaDB data), `--count`, `--dry-run`

**`app/tests/test_runner.py`:**
- [x] `_LogCapture` handler — collects formatted log lines into a list; attached directly to each of the 4 pipeline loggers (bypasses `propagate=False` in `logging_config.py`)
- [x] `_PIPELINE_LOGGERS` — list of all 4 loggers that need direct attachment
- [x] `run_single_query()` — calls real `answer_question()`, measures time, compares intent, detects "not found" responses, captures pipeline logs in `finally` block
- [x] `create_run_folder()` — timestamped `test_results/YYYY-MM-DD_HH-MM/easy/`
- [x] `save_result()` — individual `easy_NNN_result.json` per query with full pipeline trace
- [x] `save_run_metadata()` — aggregate `run_metadata.json` (pass rate, avg time, intent mismatches)
- [x] `print_progress()` — live table during run, intent mismatch shown inline
- [x] `print_summary()` — final pass/fail/error counts with failure details
- [x] CLI: `--project-id` (required), `--dry-run`

**`app/tests/report_generator.py`:**
- [x] `find_run_folder()` — auto-picks latest run or accepts `--run` flag for specific folder
- [x] `_section_summary()` — ASCII progress bar + stats table
- [x] `_section_results_table()` — every query as one row, failed rows bold actual intent
- [x] `_section_intent_breakdown()` — pass rate per intent type (spots which classifier path is weakest)
- [x] `_section_failures()` — per-failure: what failed, why, full pipeline trace in code block
- [x] `_section_sources()` — which meetings were referenced and how often
- [x] Writes `summary.md` into the run folder
- [x] CLI: `--run` (optional, defaults to latest)

**`app/tests/TESTING_GUIDE.md`:**
- [x] Quick Start (3 commands)
- [x] Mermaid flowchart of the full test system
- [x] Folder structure diagram
- [x] Script reference with all CLI flags and when to run each
- [x] Pass/fail rules table
- [x] How to read result files and `summary.md`
- [x] Manual query addition schema
- [x] Project ID reference table

**First real test run:**
- [x] Ran `test_runner.py` against `proj_nolocode_001` — 10/12 passed (83.3%)
- [x] 2 failures: `easy_005` + `easy_011` — `general_query` misclassified as `summary_query` by LLM classifier
- [x] Pipeline logs captured correctly in all result files after `propagate=False` fix

---

## Session 17 (2026-05-19) — BM25 Fixes + Full Pipeline Audit

**BM25 normalization (`app/services/retrieval/retriever.py`):**
- [x] `_normalize_for_bm25(text)` — general acronym canonicalization + punctuation removal
  - Pattern: `(?<!\w)[a-z](?:\s*[.\-\/]+\s*[a-z])+[.\-\/]*(?!\w)` with lambda strip — handles `C.E.→ce`, `P.M.→pm`, `U.S.A.→usa`, `C-E→ce`, `C. E.→ce`
  - Requires at least one dot/dash/slash — plain `"c e"` never merged (safe)
  - Then removes remaining punctuation, collapses whitespace
- [x] `_tokenize(text)` updated to call `_normalize_for_bm25` — applies to both corpus and query
- [x] `import re` added

**Full chunk logging (`app/services/retrieval/retriever.py`):**
- [x] `_log_chunk_list(label, docs)` — logs each doc with full TEXT, speaker, meeting, chunk_id, signals
- [x] `_DIV` / `_SEP` constants for visual separation in logs
- [x] `hybrid_retrieve()` now logs 3 stages: `STAGE 1a — DENSE`, `STAGE 1b — BM25`, `STAGE 2 — HYBRID (after RRF, top k)`
- [x] `retrieve_documents()` updated to use `_log_chunk_list` — removed old 90-char preview loop

**Production pipeline audit — all 3 steps confirmed complete:**
- [x] **Step 1 — Flexible Query Understanding** (`app/services/query_intent.py`)
  - `understand_query(query, project_id)` → `QueryUnderstanding(topic, intent_type, named_speaker, needs_summary, temporal_focus)`
  - LLM (Gemini Flash Lite) primary with `UNDERSTANDING_PROMPT_TEMPLATE`; regex fallback on LLM failure
  - `classify_query_intent()` also upgraded: LLM-first with `CLASSIFIER_SYSTEM_PROMPT`, regex fallback
- [x] **`app/services/prompts.py`** — new file created
  - `CLASSIFIER_SYSTEM_PROMPT` — 7-intent classification with causal-origin rules
  - `UNDERSTANDING_PROMPT_TEMPLATE` — structured JSON extraction with speaker canonicalization
  - `ANSWER_PROMPT_TEMPLATES` — 7 templates moved here from `answer_service.py`
- [x] **Step 2 — Hybrid Retrieval** (`app/services/retrieval/retriever.py`) — confirmed wired
  - `hybrid_retrieve()` called from `_retrieve_for_understanding()` in `answer_service.py`
  - `hard_filters` passed for speaker queries; `k=25` candidates
- [x] **Step 3 — LLM Re-ranking** (`app/services/retrieval/reranker.py`) — confirmed wired
  - `rerank_documents(query, documents, intent_hint, topic_hint)` called after retrieval
  - `_subject_topic_hint()` strips action words from topic before passing to re-ranker
  - Skipped for SUMMARY intent (chronological order already correct)
- [x] **`app/services/answer_service.py`** — full 5-step pipeline
  - Step 1: `understand_query()` → Step 2: `_retrieve_for_understanding()` → Step 3: `rerank_documents()` → Step 4: trim to top 10 + build context → Step 5: `_call_gemini()`
  - Date filtering for SUMMARY queries with `_extract_month_day()` + ±1 day tolerance
  - `_build_not_found_message()` lists available meeting dates when date query has no match
  - `_log_retrieval_strategy()` logs retrieval path in pipeline trace

**Design decisions locked this session:**
- [x] Adjacency linking: store `prev_chunk_id`/`next_chunk_id` as IDs only (not inline text) — text fetched at retrieval time via `collection.get(ids=[...])`
- [x] Context expansion: post-rerank, top 5 only — 10 DB lookups max, constant cost regardless of data size
- [x] BM25 normalization: query-time (not metadata-stored) — accuracy fix, latency optimization deferred

---

## Session 16 (2026-05-18) — Logging ASCII Fix + Production Architecture Design

**Logging ASCII fix (`app/services/answer_service.py`):**
- [x] `_SEP = "─" * 62` → `_SEP = "-" * 62` — box-drawing char U+2500 caused garbled output (`â"€â"€`) when pipeline.log was read on Windows (UTF-8 file read as cp1252)
- [x] `"    ↳ %s (%s) | %s"` → `"    -> %s (%s) | %s"` — same encoding issue with arrow char U+21B3
- [x] `app/logging_config.py` — confirmed `sys.__stderr__` + `log.handlers.clear()` pattern; `pipeline.log` FileHandler (UTF-8) is the reliable log output path on Windows/Streamlit

**Production architecture design (no code changes — design only):**
- [x] Root cause identified: dense vector similarity ranks by topic keyword density, not causal origin. "Who raised confusion about X?" returns the person who discussed X most, not who originated the confusion.
- [x] 3-component production pipeline designed and documented:
  - **Step 3 (implement first):** LLM Re-ranking — `rerank_documents(query, docs, intent_hint)` in `retriever.py`; post-retrieval Gemini Flash Lite call scores each chunk against true query intent; fixes ranking accuracy for ALL query types
  - **Step 2 (implement second):** BM25 Hybrid Retrieval — `hybrid_retrieve()` with `rank_bm25`; RRF merge of dense + keyword results; improves recall before re-ranking
  - **Step 1 (implement last):** Flexible Query Understanding — `understand_query()` returning structured JSON; replaces fixed 7-intent enum with LLM extraction; handles arbitrary query patterns
- [x] Implementation order locked: Step 3 → Step 2 → Step 1 (re-ranking highest impact, no schema change; query understanding replaces existing classifier last)
- [x] Per-chunk LLM enrichment at ingestion rejected — cost scales with data size, not query volume; wrong cost model for production
- [x] Meeting index step deferred — adds latency and one more Gemini call per query; low marginal value when re-ranking already handles causal origin queries
- [x] `DISCUSSION.md` updated — Session 16 log + new "Production Architecture (Post-POC)" section added
- [x] `TODO.md` updated — new "Production Phase — Retrieval Architecture Upgrade" section added with full task breakdown (Steps 1/2/3)

---

## Session 15 (2026-05-18) — Pipeline Logging + Dev Mode Bug Fix

- [x] **`app/logging_config.py`** — new file: `setup_pipeline_logging()` configures a stderr handler for our app modules at DEBUG level. Noisy libraries (httpx, google, langchain, chromadb, tenacity) suppressed to WARNING. Call once at startup.
- [x] **`streamlit_app.py`** — `setup_pipeline_logging()` called at import time so every Streamlit query prints a full pipeline trace to the terminal where `streamlit run` was launched.
- [x] **`app/services/answer_service.py`** — full 4-step trace added to `answer_question()`: PIPELINE START (query + project), [1/4] CLASSIFY INTENT, [2/4] RETRIEVE (strategy + filter + every doc with meeting/speaker/content preview), [3/4] BUILD PROMPT (doc count + context chars + prompt preview), [4/4] LLM CALL, PIPELINE DONE (timing + unique sources + answer preview).
- [x] **`app/services/query_intent.py`** — logs which regex (`_DECISION_RE`, `_SPEAKER_RE`, etc.) matched and the resulting intent on every classification.
- [x] **`app/services/retrieval/retriever.py`** — logs each retrieved document: meeting title, date, speaker, and first 90 chars of content. Removed old verbose "Retrieving documents | query=..." line; kept filter as DEBUG so it only shows when debug level is active.
- [x] **`.env` bug fix** — `DEVELOPMENT_MODE=true` was missing from `.env`. Without it `Config.DEVELOPMENT_MODE` defaulted to `false`, running the production webhook path which requires a live Fireflies payload and dropped every call. Added the key so the hardcoded `CONSTANT_TRANSCRIPT` pipeline runs correctly.

---

## Session 14 (2026-05-14) — Phase 5 Validation: POC COMPLETE

**Accuracy test — 30/30 (100%):**
- [x] `test_queries.py` — 30 questions across all 7 intent types, 100% pass rate, 0 errors, avg 3.8s per question
- [x] Fixed 4 fragile must_contain keywords (year/word-form variants replaced with stable terms)
- [x] Added 1-second sleep between questions to prevent Windows proxy SSL rate-throttling on rapid consecutive embedding calls

**Classifier fix:**
- [x] `query_intent.py` — SPEAKER check moved before QUESTION in `classify_query_intent()`. Root cause: "What did Ngumi say about the **questions**?" was matching QUESTION intent because `_QUESTION_RE` was checked first. Now SPEAKER (speech-act pattern with name) takes priority over QUESTION keyword matching.

**Scope isolation test — PASS:**
- [x] `validate_poc.py` — 3 queries against non-existent `proj_fake_999` → all returned "not found" with 0 sources, no Nolocode data leaked

**Multi-meeting synthesis test — PASS:**
- [x] Summary query → covers both meetings (2026-05-08 and 2026-05-14) in one cohesive answer
- [x] Timeline query → correctly compares "on hold" (May 8) vs "two approaches being evaluated" (May 14)
- [x] Commitment query → lists action items from both meetings

**Speed test — PASS:**
- [x] All 6 query types under 10s — avg 3.4s, max 4.6s (TIMELINE is slowest — 2× embedding calls)

---

## Session 13 (2026-05-14) — Type 6 Timeline Query + 30 Test Questions

- [x] **`project_store.py`** — `get_meeting_ids_for_project(project_id)` added; returns all meeting IDs registered to a project
- [x] **`retriever.py`** — `retrieve_timeline_documents(query, project_id, k_per_meeting=6)` added; runs one semantic search per meeting, merges results sorted by `meeting_date` ascending. Ensures every meeting in the project contributes equally regardless of semantic distance.
- [x] **`answer_service.py`** — TIMELINE intent now routes to `retrieve_timeline_documents()` (previously fell through to plain `retrieve_documents()`). Import added.
- [x] **`query_intent.py` `_TIMELINE_RE` expanded** — old regex only matched explicit schedule/deadline words. Added 8 new patterns: `between.*meetings`, `how did/has.*changed`, `across both/all meetings`, `compared to the first/second/previous meeting`, `evolved`, `first/second meeting`, `changed since`. All 4 test timeline questions now correctly classify as `timeline_query`.
- [x] **`test_queries.py`** — 4 new questions added to reach 30 total: decision (meeting 2 — AI approach), timeline (cross-meeting x2), speaker (Harsh Vardhan), commitment (Harsh Vardhan meeting 2). Distribution: decision×4, commitment×5, summary×3, speaker×5, timeline×4, general×7, edge×2.
- [x] **`check_timeline.py`** — verification script created and run; confirmed 2 meetings (2026-05-08 and 2026-05-14), 5 shared topics (AI module, scenario modeling, timeline, module, approach), data sufficient for Type 6 queries.

**Verified end-to-end:**
- "How did the discussion about the AI module change between the two meetings?" → `timeline_query`, sources from both meetings, answer correctly shows May 8 status ("on hold, awaiting approach decision") vs May 14 status ("actively comparing two approaches for stress testing")

---

## Session 12 (2026-05-14) — Second Transcript + Streamlit UI Complete

**Multi-transcript ingestion pipeline:**
- [x] **`webhook_handler.py` dev mode** — loops over all transcripts in `CONSTANT_TRANSCRIPT["data"]["transcript"]` list (previously only processed first item). Each transcript is wrapped individually and passed to `normalize_transcript()`. Skip check: meetings already in ChromaDB are skipped automatically — re-runs are safe.
- [x] **`normalize.py` null-summary guard** — `"summary": "null"` (literal string from Fireflies) now coerced to `{}` via `isinstance(summary_raw, dict)` check. Prevents `_resolve_summary()` from crashing on `.get("overview")` call.
- [x] **`projects.json` updated** — second meeting `01KMHQSBYB1RAGY2X4EP6DCMC9` added to `meeting_ids`. Three new speakers added: `Ashpreet Singh (client)`, `Nolocode AI (client)`, `Harsh Vardhan Dixit (developer)`.
- [x] **ChromaDB clean re-ingest** — wiped corrupted HNSW index (caused by partial write), re-ingested both meetings fresh. Meeting 1: 232 docs (Fireflies summary). Meeting 2: 289 docs (Gemini fallback summary, 992 chars). Total: 521 docs.
- [x] **Gemini fallback verified** — `generate_meeting_summary()` in `gemini_client.py` correctly generates summary when Fireflies returns `"null"`. Feeds all transcript chunks, produces accurate 4-6 sentence summary.

**Streamlit UI — `streamlit_app.py` complete:**
- [x] **Sidebar** — project selector (enforces scope), 3-metric stats bar (meetings/speakers/chunks), meeting list with dates, speaker list with role icons (🔴 client / 🟡 PM / 🔵 developer), "What can I ask?" query guide expander
- [x] **Chat window** — `st.chat_message` for user + assistant, renders full conversation history on every rerun
- [x] **Intent badges** — coloured pill HTML (`🔵 Decision`, `🟠 Action Item`, `🟢 Summary`, `🟣 Questions`, `🔷 Speaker`, `🟡 Timeline`, `⚫ General`) displayed above each answer
- [x] **Source panel** — collapsible expander showing speaker, meeting title, date, and 200-char content preview per source
- [x] **Empty state** — 6 example question buttons (3-column grid) shown when no chat history
- [x] **`st.cache_data(ttl=120)`** on `load_projects()` and `get_project_stats()` — auto-refreshes every 2 minutes; cache cleared on project switch
- [x] **Refresh button** — `st.cache_data.clear()` + rerun, alongside Clear Chat button

---

## Session 11 (2026-05-14) — Name-Based Speaker Architecture

**Architecture change: role-based querying → name-based querying**

- [x] **`query_intent.py` `_SPEAKER_RE` rewritten** — removed role keywords (client/developer/PM). Now triggers on speech-act patterns: `"what did [name] say/mention/discuss"`, `"what has [name] said"`, `"according to"`, `"who said"`. Negative lookahead prevents `"what did we/they/the discuss"` from triggering SPEAKER intent.
- [x] **`answer_service.py` refactored** — removed `_detect_speaker_role()` + all role regexes (`_CLIENT_RE`, `_DEV_RE`, `_PM_RE`). Added `_normalize()` (strips diacritics so "Ngumi" matches "Ngũmi") + `_detect_speaker_name(query, project_id)` (scans project speaker list, matches full name then first name). Both SPEAKER and QUESTION intents now filter by `speaker_name` instead of `speaker_role`.
- [x] **`project_store.py`** — added `get_speaker_names(project_id)` returning list of speaker names for a project
- [x] **`test_queries.py` SPEAKER tests updated** — 4 role-based questions replaced with name-based: Ngumi, Karan, Bhavneet, Project Manager SFS
- [x] **`trace_query.py` fixed** — imported `_detect_speaker_name` (was importing removed `_detect_speaker_role`), added QUESTION intent branch with name filter, updated all SPEAKER descriptions
- [x] **`FUTURE_SCOPE.md` created** — documents role-based querying (full architecture: flag + registry + signal chain), Type 3 miscommunication, name fuzzy matching improvements, Type 6 date range filtering
- [x] **Verified end-to-end** — `"What questions did Bhavneet Mahajan raise?"` → intent=question_query, `contains_question=True + speaker_name=Bhavneet Mhajan` filter applied, 1 source (Bhavneet only), correct answer

---

## Session 10 (2026-05-14) — Speaker Role Fix + QUESTION Intent Bug Fix

- [x] **`projects.json` corrected** — `"Bhavneet Mhajan": "developer"` → `"Bhavneet Mhajan": "client"` (was mislabeled; Bhavneet is a client, not a developer)
- [x] **ChromaDB re-ingested** — 232 chunks upserted via dev mode pipeline; all Bhavneet Mhajan chunks now have `speaker_role = "client"` confirmed
- [x] **QUESTION intent speaker filter fix** in `answer_service.py` — query "What questions did the client raise?" was returning PM chunks because QUESTION intent was checked before SPEAKER intent in the classifier. Fix: `_retrieve_for_intent` now detects speaker role for QUESTION intent and adds `speaker_role` filter alongside `contains_question=True`. Both filters apply when a role keyword is present in the query.

---

## Session 9 — Phase 2 Complete: RAG Answer Engine

- [x] **`app/services/answer_service.py`** — full implementation replacing the stub
  - `answer_question(query, project_id)` → `{answer, sources, intent}`
  - Routes via `classify_query_intent()` → 7 intent-specific retrieval strategies
  - SUMMARY intent: `get_raw_collection().get()` with `$and` filter — chronological, NOT vector search
  - DECISION intent: broad semantic search (no hard filter — weak signal design, confirmed correct)
  - COMMITMENT/QUESTION: `retrieve_commitment_documents()` / standard retrieval with signal filters
  - SPEAKER intent: detects `client`/`developer`/`project_manager` from query text, adds `speaker_role` filter
  - 7 prompt templates (one per `QueryIntent`) — each with rules tailored to what the LLM must focus on
  - `_extract_sources()` — deduplicates `{meeting_title, meeting_date, speaker_name}` across retrieved docs
- [x] **`POST /query` endpoint** in `main.py` — `{question, project_id}` → `{answer, sources, intent}`, HTTP 400/500 errors
- [x] **ChromaDB `$and` filter fix** in `retriever.py` + `answer_service.py` — ChromaDB 1.5 rejects flat multi-key dicts, requires `{"$and": [{"field": {"$eq": val}}]}` syntax
- [x] **Gemini SDK migration** — both `gemini_client.py` and `answer_service.py` migrated from deprecated `google.generativeai` → `google.genai`
- [x] **Model updated** — `gemini-1.5-flash` → `gemini-2.5-flash` (older versions removed from API)
- [x] **`langchain-chroma` + `langchain-google-genai` added to `pyproject.toml`** — were installed but untracked
- [x] **Meeting re-ingested** — 232 chunks stored with Gemini embeddings, correct signals, and 1 summary chunk via dev mode pipeline
- [x] **All 6 query types validated end-to-end** — decision, commitment, summary, speaker, timeline, general all return real grounded answers with sources

---

## Fireflies Webhook Integration

- [x] `POST /webhook/fireflies` endpoint receives Fireflies.ai notifications
- [x] Flexible payload parsing — handles `transcript_id`, `meetingId`, `meeting_id`, `data.transcript_id`
- [x] Retry logic for early webhooks (3 attempts × 10s) when transcript ID is not immediately available

## Fireflies API Client

- [x] GraphQL client (`app/clients/fireflies_client.py`) — fetches transcript with `id`, `title`, `sentences`, `summary`
- [x] Bearer token authentication via `FIREFLIES_API_KEY`
- [x] Retry logic (3 attempts × 10s) for API eventual consistency
- [x] Summary polling — waits up to 6 attempts × 5s for `summary.overview` to appear
- [x] Custom `FirefliesAPIError` exception with proper error messages
- [x] `validate_api_config()` check on startup

## Transcript Processing Pipeline

- [x] **Normalization** (`app/services/transcript/normalize.py`) — flattens nested API response, validates required fields, raises `TranscriptValidationError` on bad data
- [x] **Metadata builder** (`app/services/transcript/metadata.py`) — extracts `meeting_id`, `title`, `date`
- [x] **Speaker-aware chunking** (`app/services/transcript/chunking.py`)
  - Hard speaker boundary (one chunk = one speaker)
  - `MAX_CHARS=250`, `MIN_CHARS=80`, `HARD_MIN=15`
  - Garbage filter for utterances < 8 characters
  - Size check before adding (no overflow)
  - Clean reset between chunks (no overlap)

## Development Tooling

- [x] Development mode (`DEVELOPMENT_MODE=true`) — uses `CONSTANT_TRANSCRIPT` from config, no API calls needed
- [x] Test suite (`test_fireflies.py`) — covers normalization, metadata, chunking, dev-mode pipeline
- [x] `chunks_output.json` — sample output from real transcript (50+ chunks)
- [x] `DEVELOPMENT_GUIDE.md` — full architecture doc with 5-phase roadmap

## Phase 1 — Foundation (Sessions 2, 3 & 4)

- [x] **`projects.json`** — config file at project root mapping `project_id → { name, company, meeting_ids, speakers }`
- [x] **`app/services/storage/__init__.py`** — module init
- [x] **`app/services/storage/project_store.py`**
  - `get_project_for_meeting(meeting_id)` — returns project scope fields for a meeting
  - `get_speaker_role(meeting_id, speaker_name)` — returns role from projects.json speakers map
  - UTF-8 encoding fix for unicode speaker names on Windows
- [x] **Full 5-level chunk metadata schema** (`chunking.py` upgraded)
  - Renamed: `date → meeting_date`, `speaker → speaker_name`, `sequence → chunk_index`
  - Added: `speaker_id` (slug), `speaker_role`, `chunk_type`, `is_meeting_summary`
  - Added: `contains_decision`, `contains_commitment`, `contains_question`, `sentiment` (placeholders)
  - Added: `meeting_number`, `meeting_type` (placeholders)
- [x] **`_stamp_project_and_roles()`** in `webhook_handler.py` — stamps `project_id`, `company_id`, `project_name`, `company_name`, `speaker_role` on every chunk after creation
- [x] **ChromaDB storage layer** (`app/services/storage/db.py` + `chunk_store.py`)
  - `db.py` — PersistentClient, `meeting_chunks` collection, cosine similarity space
  - `chunk_store.py` — `store_chunks()` (upsert, re-ingestion safe), `get_chunks_by_meeting()`, `get_chunk_count()`, `get_distinct_meeting_ids()`
  - Storage wired into `webhook_handler.py` — `# TODO` replaced with real `store_chunks(chunks)` call
- [x] **`meeting_number` auto-computation** — counts distinct meeting_ids already in ChromaDB for the project, assigns next number automatically
- [x] **Pipeline guard** — if `meeting_id` not in `projects.json`, pipeline aborts before storing (no broken chunks without `project_id`)
- [x] **Bug fixes (Session 4)**
  - `FIREFLIES_API_URL` typo fixed in `config.py` and `fireflies_client.py`
  - `date` field added to GraphQL query — real meeting date now used instead of `datetime.now()`
  - `meeting_number` reads from `meeting_meta` in `chunking.py` (was hardcoded `0`)
  - Dev mode now returns chunks (was returning `None`)

## Session 8 — Retriever + Query Intent Classifier

- [x] **`app/services/retrieval/retriever.py`** — `retrieve_documents(query, project_id, filters, k)` with project scope enforcement; dedicated helpers: `retrieve_commitment_documents()`, `retrieve_question_documents()`, `retrieve_decision_candidates()` (broad semantic — no hard decision filter, smart design)
- [x] **`app/services/query_intent.py`** — `classify_query_intent(query) → QueryIntent` enum (GENERAL / DECISION / COMMITMENT / QUESTION / SUMMARY / SPEAKER / TIMELINE); rule-based regex, 7 types covering all 6 query taxonomy types + catch-all
- [x] **`chunking.py` signals improved** — `_FALSE_COMMITMENT_RE` added to exclude false positives ("we will calculate", "let's move on", "we'll come back")
- [x] **`projects.json` speaker keys fixed** — "Karan Middha" (stripped platform ID) ✓
- [x] **`inspect_db.py` updated** — now uses `get_raw_collection()` from new LangChain-based `db.py`

## Session 7 — LangChain + Gemini Embeddings Integration

- [x] **`app/services/embeddings/gemini_embeddings.py`** — `get_embedding_model()` returns singleton `GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")` via `langchain-google-genai`
- [x] **`app/services/documents/mapper.py`** — `chunk_to_document()` + `chunks_to_documents()` convert internal chunk dicts to LangChain `Document(page_content=text, metadata={...})`; skips invalid chunks, sanitizes metadata types
- [x] **`app/services/storage/db.py`** — fully rewritten: `get_vectorstore()` returns singleton `langchain_chroma.Chroma` (persisted, Gemini embeddings, `meeting_chunks` collection); `get_raw_collection()` exposes underlying ChromaDB collection for metadata-only operations
- [x] **`app/services/storage/chunk_store.py`** — rewritten: `store_documents()` uses LangChain Chroma `add_documents()` with stable `chunk_id` as document ID; `get_distinct_meeting_ids()` uses raw collection for efficiency; `get_chunks_by_meeting()` / `get_chunk_count()` use vector similarity search with metadata filter
- [x] **Pipeline upgraded to 6 steps** in `webhook_handler.py`:
  - Step 5: `chunks_to_documents()` — converts chunk dicts to LangChain Documents
  - Step 6: `store_documents()` — embeds with Gemini and stores in ChromaDB via LangChain
- [x] **Embedding now happens automatically** at storage time — `page_content` is embedded by Gemini before every `add_documents()` call

## Session 6 — Git Setup + Merge Resolution + DB Inspection

- [x] **Git configured** — `user.name = "Sahil Aggarwal"`, `user.email = "sfs.sahilaggarwal25@gmail.com"` set globally
- [x] **GitHub authentication** — classic PAT with `repo` scope; token embedded in remote URL
- [x] **Merge conflicts resolved** — `normalize.py`, `chunking.py`, `webhook_handler.py`, `test_fireflies.py`
  - Kept: full utterance chunking pipeline, signal detection, summary chunk, regex cleaner
  - Dropped: `clean_with_gemini()` per-sentence approach (decided against it in Session 5)
  - Kept from remote: `_clean_speaker_name()` — strips Fireflies platform IDs (e.g. "Karan Middha U0438EU2CSX" → "Karan Middha")
  - Kept from remote: `group_by_speaker()` — available as utility
- [x] **`_clean_speaker_name()` wired into `normalize_transcript()`** — speaker names are cleaned before chunking
- [x] **`inspect_db.py`** — CLI inspection tool (`uv run python inspect_db.py`)
  - Shows: total chunks, projects, meetings, signal counts, summary chunks, 3-chunk sample

## Session 5 — ASR Cleaning + Summary Chunk + Content Signals

- [x] **ASR noise cleaning** (`normalize.py`) — `_clean_sentence()` with 5 compiled regex patterns
  - Removes: `um`, `uh`, `hmm`, `hm`, `er`, `erm`, `you know`
  - Removes repeated consecutive words (`"the the"` → `"the"`)
  - Drops sentences that reduce to < 8 chars after cleaning
  - Runs before chunking — cleaner text into embeddings
- [x] **Meeting summary chunk** (`chunking.py` + `webhook_handler.py`)
  - `build_summary_chunk()` creates one chunk per meeting with `is_meeting_summary=True`, `chunk_type="summary"`
  - `_resolve_summary()` in webhook_handler: uses Fireflies `summary.overview` first, Gemini 1.5 Flash fallback when Fireflies doesn't provide one
  - Summary chunk goes through `_stamp_project_and_roles()` — gets full project metadata like all other chunks
  - If both sources fail, pipeline continues without summary chunk (warning logged)
- [x] **`app/clients/gemini_client.py`** — `generate_meeting_summary(chunks, title)` via `gemini-1.5-flash`
  - Cost: ~$0.001 per 1-hour meeting — effectively free at POC scale
  - `GEMINI_API_KEY` added to `Config` and `.env`
- [x] **Content signal detection** (`chunking.py`) — `_detect_signals(text)` replaces `False` placeholders
  - `contains_decision`: matches "we decided", "confirmed", "going with", "agreed to", etc.
  - `contains_commitment`: matches "I will", "I'll", "action item", "by Friday", etc.
  - `contains_question`: ends with `?` OR starts with question word
  - Rule-based regex — zero cost, zero latency, runs inline during chunking

## Design Decisions (Locked)

- [x] **project_id assignment** — POC: `projects.json`. Production: Option A (PM creates projects in system)
- [x] **Speaker role assignment** — POC: `speakers` map inside `projects.json`. Same file, same pattern.

## Current Chunk Output Schema (Full — Session 19, Sprint 3)

```python
{
    # Identity
    "chunk_id":           "01KM2DD6MXGSZ4F1QW0BNJE16N_1",   # meeting_id + "_" + chunk_index

    # Level 1 — Scope (stamped by webhook_handler via project_store)
    "project_id":         "proj_nolocode_001",
    "project_name":       "Nolocode",
    "company_id":         "comp_001",
    "company_name":       "Nolocode",

    # Level 2 — Meeting
    "meeting_id":         "01KM2DD6MXGSZ4F1QW0BNJE16N",
    "meeting_title":      "Nolocode meeting with Ashpreet",
    "meeting_date":       "2026-05-08",                       # ISO date, from Fireflies dateString
    "meeting_number":     1,                                  # real — 1-indexed order within project
    "meeting_type":       "unknown",                          # placeholder, not yet classified

    # Level 3 — Speaker
    "speaker_name":       "Ngũmi Gituro",
    "speaker_id":         "ngumi_gituro",                     # slugified, ASCII-safe
    "speaker_role":       "client",                           # real — stamped from projects.json speakers map

    # Level 4 — Chunk position
    "chunk_index":        1,
    "chunk_type":         "utterance",                        # "utterance" | "summary"
    "is_meeting_summary": False,                              # True only for the summary chunk

    # Tier 2a — Timing (seconds from recording start; None if API didn't provide)
    "start_time":         14.96,
    "end_time":           33.26,

    # Tier 2a — Adjacency links (filled in post-loop pass in create_chunks)
    "prev_chunk_id":      None,                               # chunk_id of previous utterance, None if first
    "next_chunk_id":      "01KM2DD6MXGSZ4F1QW0BNJE16N_2",   # chunk_id of next utterance, None if last

    # Level 5 — Content signals (pre-computed by regex classifiers in chunking.py)
    "contains_decision":   False,                             # real — _DECISION_RE match
    "contains_commitment": True,                              # real — _COMMITMENT_RE match (excl. false positives)
    "contains_question":   False,                             # real — ends with "?" or _QUESTION_START_RE match
    "sentiment":           "neutral",                         # placeholder — no LLM sentiment yet

    # Content
    "text":               "We should finalize...",
    "text_length":        162,
}
```

