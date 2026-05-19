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

# SPRINT 3 — Chunking Improvements  [NEXT]

> Pipeline accuracy is limited by chunk quality. Single re-ingestion pass applies all fixes at once.
> Cost: 521 docs × Gemini embedding API call.

```
╔══════════════════════════════════════════════════════╗
║     SPRINT 3 — CHUNKING + CONTEXT EXPANSION         ║
║     "Better raw material for the pipeline"          ║
╠══════════════════════════════════════════════════════╣
║  Re-ingest: YES — do all fixes in ONE pass          ║
║  Status:    Not started                             ║
╚══════════════════════════════════════════════════════╝
```

---

## Tier 2a — Schema additions

**`app/clients/fireflies_client.py`** — add `rawStartTimeMs`, `rawEndTimeMs` to sentences query

**`app/services/transcript/chunking.py`:**
- Store `start_time` / `end_time` per chunk (ms from API)
- Add `prev_chunk_id` / `next_chunk_id` in a post-loop linking pass after all chunks are built

```
STATUS:   [ ] Not started
RE-INGEST: Yes
```

---

## Tier 2b — Chunking quality

**`app/services/transcript/chunking.py`:**
- Raise `MAX_CHARS` 250 → 500 (soft limit — reduces semantic splits at boundaries)
- Add `_is_low_quality(text)` — drop if unique token ratio < 0.4 or meaningful words < 4
- Topic-shift split — split same-speaker block when sentence starts with `"now"`, `"next"`, `"separately"`, etc.

```
STATUS:   [ ] Not started
RE-INGEST: Yes
```

---

## Tier 2c — Context expansion (post-rerank)

**`app/services/answer_service.py`** — add `_expand_context(top_docs)` after re-rank step:
- Fetch `prev_chunk_id` + `next_chunk_id` for top 5 docs via `collection.get(ids=[...])`
- Inject `[BEFORE]` / `[AFTER]` neighbor text into `_build_context()`
- 10 DB lookups max per query — constant cost at any scale

```
STATUS:   [ ] Not started
RE-INGEST: No (uses IDs already stored in Tier 2a)
DEPENDS ON: Tier 2a complete + re-ingested
```

---

## Sprint 3 Progress

```
Tier 2a — Schema additions        [          ]   0%   Not started
Tier 2b — Chunking quality        [          ]   0%   Not started
Tier 2c — Context expansion       [          ]   0%   Not started  (depends on 2a)

OVERALL                           [          ]   0%
```

> Do Tier 2a + 2b together (same re-ingestion). Then Tier 2c (no re-ingest).
> Update this file manually as steps complete, OR say "update files" at session end.
