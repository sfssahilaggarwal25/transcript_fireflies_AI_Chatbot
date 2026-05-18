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

# SPRINT 2 — Production: Retrieval Architecture Upgrade  [IN PROGRESS]

> Problem: POC dense search ranks by keyword density, not causal origin. "Who raised confusion about X?" returns the wrong person.
> Fix: 3-component pipeline. Cost scales with queries, not data size.

```
╔══════════════════════════════════════════════════════╗
║     PRODUCTION — RETRIEVAL UPGRADE                  ║
║     "Fix ranking accuracy + scalable pipeline"      ║
╠══════════════════════════════════════════════════════╣
║  Steps:     3 (implement in order: 3 → 2 → 1)      ║
║  Re-ingest: Not required for any step               ║
║  Status:    Not started                             ║
╚══════════════════════════════════════════════════════╝
```

---

## Step 3 — LLM Re-ranking  `[Implement First]`

**Why:** Highest impact fix. The right chunk is already in ChromaDB — it just isn't ranked first.
One Gemini Flash Lite call after retrieval re-scores chunks by true query intent.

**What changes:**
- New file `app/services/retrieval/reranker.py` — `rerank_documents(query, documents, intent_hint)`
- `app/services/answer_service.py` — call `rerank_documents()` after `_retrieve_for_intent()`

**Validates when:** "Who raised confusion about CE classification code?" returns Rhythm Jalhotra (not Karan)

```
STATUS:   [ ] Not started
COST:     +1 Gemini Flash Lite call per query (~$0.001)
RE-INGEST: No
```

---

## Step 2 — Hybrid Retrieval (BM25 + Dense)  `[Implement Second]`

**Why:** Dense search misses exact phrase matches. BM25 keyword search catches them. Merge both with Reciprocal Rank Fusion before re-ranking.

**What changes:**
- `pyproject.toml` — add `rank_bm25`
- `app/services/retrieval/retriever.py` — add `hybrid_retrieve(query, project_id, filters, k=25)`
- `app/services/answer_service.py` — swap `retrieve_documents()` for `hybrid_retrieve()`

```
STATUS:   [ ] Not started
COST:     Zero (BM25 is pure math)
RE-INGEST: No
```

---

## Step 1 — Flexible Query Understanding  `[Implement Last]`

**Why:** Current 7-intent enum requires new code per query pattern. LLM JSON extraction handles any pattern with zero code changes.

**What changes:**
- `app/services/query_intent.py` — add `understand_query()` returning `{topic, intent_type, named_speaker, needs_summary, temporal_focus}`; keep old `classify_query_intent()` as fallback
- `app/services/answer_service.py` — update routing to use flexible output

```
STATUS:   [ ] Not started
COST:     Neutral (replaces existing classifier call)
RE-INGEST: No
```

---

## Sprint 2 Progress

```
Step 3 — LLM Re-ranking         [          ]   0%   Not started
Step 2 — BM25 Hybrid Retrieval  [          ]   0%   Not started
Step 1 — Flexible Query         [          ]   0%   Not started

OVERALL                         [          ]   0%
```

> Update this file manually as steps complete, OR say "update files" at session end.
