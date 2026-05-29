# Meeting Diversity Cap — Design & Implementation

> **Branch:** `feat/retrieval-accuracy`
> **Files changed:** `app/agent/_tool_utils.py`, `app/agent/tools.py`, `app/agent/prompts.py`
> **Tests:** `app/agent/tests/test_diversity_cap.py` — 9/9 PASS

---

## 1. The Problem

When the LangGraph agent calls `search_transcripts` for a project-wide query, the retrieval pipeline runs `hybrid_retrieve(k=25)` — fetching 25 chunks ranked by BM25 + dense vector + RRF merge.

With 19 meetings in the corpus, this works well for focused queries. But for topics that were heavily discussed in one dedicated meeting, a single problem emerges:

**One meeting fills all slots.**

```
Query: "What decisions were made about the mobile module?"

hybrid_retrieve returns 25 chunks (RRF ranked):
  Rank  1:  Meeting #7  — "we decided to delay mobile module to Q3"
  Rank  2:  Meeting #7  — "Harsh confirmed the mobile delay"
  Rank  3:  Meeting #7  — "mobile scope was pushed back"
  Rank  4:  Meeting #7  — "action item: update mobile timeline"
  Rank  5:  Meeting #7  — "mobile module timeline discussion"
  Rank  6:  Meeting #9  — "revisiting the mobile decision"
  Rank  7:  Meeting #7  — "mobile module was discussed again"   ← still Meeting #7
  Rank  8:  Meeting #11 — "mobile module still delayed"
  Rank  9:  Meeting #7  — "Harsh said mobile timeline..."       ← still Meeting #7
  Rank 10:  Meeting #14 — "mobile decision updated"
  ...

After rerank → top 10 → LLM sees mostly Meeting #7

Missed entirely:
  Meeting #3  — first time mobile was raised (origin of the decision)
  Meeting #12 — decision was reversed
  Meeting #15 — final confirmed date
```

Meeting #7 had the most detailed discussion, so its chunks scored highest by RRF. But the PM needed the full story across all meetings. Three meetings with critical information were never seen by the LLM.

This gets worse as the project grows. With 19 meetings and 2,600 chunks, one verbose meeting can dominate every project-wide query.

---

## 2. Why a Static Cap Is Not Enough

The first instinct is a hard cap: "allow at most 3 chunks per meeting." This solves the domination problem but creates a new one.

```
Query: "Give the AI architecture overview"

Corpus:
  Meeting #9 "AI Architecture Deep Dive" — 20 chunks, ALL about architecture
  Other 18 meetings — 0–2 architecture mentions each

After hard cap of 3:
  Meeting #9 → only 3 chunks pass  ← loses 17 relevant chunks!
  Other meetings → 1–2 each (weak matches)

LLM sees: 3 deep architecture chunks + noise from other meetings
Answer: shallow overview — the dedicated meeting was penalised
```

A hard cap cannot distinguish between:
- A **mediocre** meeting dominating because it has many verbose chunks on general topics
- A **dedicated** meeting dominating because it is the authoritative source

Both get cut to 3. That is wrong.

---

## 3. The Solution — Proportional Cap with Dynamic Ceiling

Instead of a fixed maximum, each meeting's cap scales with how much of the retrieved pool it naturally contributed.

**Core idea:** A meeting that contributed 50% of retrieved chunks earned those slots through retrieval relevance. Give it half its natural count, but cap at 25% of the total pool so no single meeting ever dominates.

### Formula

```python
cap_ceiling = max(_DIVERSITY_CAP_FLOOR, round(total * _DIVERSITY_MAX_MEETING_FRACTION))
cap         = max(_DIVERSITY_CAP_FLOOR, min(cap_ceiling, round(count * _DIVERSITY_PASS_RATE)))
```

### Constants

| Constant | Value | Meaning |
|---|---|---|
| `_DIVERSITY_CAP_FLOOR` | 3 | Every meeting is guaranteed at least 3 slots |
| `_DIVERSITY_PASS_RATE` | 0.5 | Each meeting passes half its retrieved docs |
| `_DIVERSITY_MAX_MEETING_FRACTION` | 0.25 | No meeting exceeds 25% of the reranker pool |

### Why These Values

**Floor = 3**
Three chunks per meeting provides: one anchor + the sentence before + the sentence after (matching exactly what `_expand_context` fetches as neighbors). It is enough context for the reranker to make a fair assessment of the meeting's relevance.

**Pass rate = 0.5**
Each meeting passes half what it naturally retrieved. A meeting with 10 chunks passes 5. This halves the redundancy within each meeting while still giving it meaningful representation.

**Fraction = 0.25 (ceiling)**
No single meeting contributes more than one-quarter of the reranker pool. At k=25, ceiling=6 (24%). At k=40 (overview boost), ceiling=10 (25%). The fraction stays consistent regardless of k — the system is scale-invariant.

### Ceiling Scales with k

This is the key generalisation. The ceiling is not hardcoded:

```
k=25 (normal query):    ceiling = round(25 × 0.25) = 6
k=40 (overview boost):  ceiling = round(40 × 0.25) = 10
k=15 (single meeting):  ceiling = round(15 × 0.25) = 4, but cap bypassed anyway
```

When an overview query triggers the k-boost (k→40), the ceiling opens up to 10 — allowing the dedicated meeting to contribute more depth. The cap and the boost work together, not against each other.

---

## 4. Where It Sits in the Pipeline

```
search_transcripts() call
        │
        ▼
[k-boost detection]
  "overview" in query AND scope_ids=None?
  → effective_k = min(effective_k × 2, 40)
        │
        ▼
hybrid_retrieve(k=effective_k)
  → BM25 + dense vector + RRF merge
  → Returns ranked chunks, no diversity enforcement
        │
        ▼
[_apply_diversity_cap(docs)]         ← NEW (skipped when scope_ids set)
  → Count chunks per meeting_id
  → Compute ceiling = round(total × 0.25)
  → Walk ranked list, apply per-meeting cap
  → Return filtered list, original order preserved
        │
        ▼
rerank_documents(top_n=10)
  → Gemini scores each chunk 0-10
  → Trims to best 10
        │
        ▼
_expand_context(top_n=5)
  → Fetch prev/next neighbors for top 5 ranked chunks
        │
        ▼
LLM generates answer
```

**Important:** The diversity cap is applied **before** reranking, not after. This matters because:
- The reranker's job is to pick the best 10 from a **diverse** candidate pool
- If the pool is not diverse before reranking, the reranker cannot fix it — it can only rank what it receives

---

## 5. The k-Boost for Overview Queries

Certain queries signal that the PM wants broad cross-meeting coverage:

```python
_OVERVIEW_SIGNALS = frozenset({
    "overview", "all", "across", "throughout",
    "explain", "describe", "complete", "full", "entire",
    "summarize", "summary", "detail", "everything",
})
```

When these words appear in a project-wide query, `effective_k` is doubled (capped at 40). This gives more candidates to the diversity cap and reranker, improving coverage for synthesis queries.

**Only fires for project-wide queries** (`scope_ids=None`). Single-meeting queries do not benefit from a k-boost and skip this entirely.

---

## 6. Single-Meeting Scope Bypass

When the user scopes a query to a specific meeting ("What happened in meeting #9?"), `scope_ids` is set. In this case:

- All retrieved chunks come from one meeting by design
- Applying a cap would cut relevant content from that meeting
- The cap is **completely bypassed**

```python
if not scope_ids:
    docs = _apply_diversity_cap(docs)
```

---

## 7. Detailed Example — "Give the AI Architecture Overview"

**Setup:**
- 19 meetings in corpus, 2,600 total chunks
- Meeting #9 "AI Architecture Deep Dive" — 20 chunks, fully dedicated to architecture
- Meeting #3 "Sprint Planning" — 2 chunks briefly mention architecture
- Meeting #7 "Client Review" — 1 chunk references the architecture plan
- Meeting #12 "Technical Review" — 4 chunks discuss architectural updates
- 15 other meetings — 0 architecture content

---

### Step 1 — k-boost detection

```
Query: "Give the AI architecture overview"
"overview" in query → YES
scope_ids → None (project-wide)
effective_k: 25 → min(25 × 2, 40) = 40
```

---

### Step 2 — hybrid_retrieve(k=40)

BM25 and dense search across all 2,600 chunks. Returned pool:

```
Rank 1-20:  Meeting #9  (20 high-scoring architecture chunks)
Rank 21-24: Meeting #12 (4 chunks about architectural updates)
Rank 25-26: Meeting #3  (2 brief architecture mentions)
Rank 27:    Meeting #7  (1 architecture reference)
Rank 28-40: Other meetings (13 weak/noise matches from unrelated content)

total = 40
```

---

### Step 3 — _apply_diversity_cap

```
counts per meeting:
  Meeting #9:   20 docs  →  20/40 = 50%
  Meeting #12:   4 docs  →   4/40 = 10%
  Meeting #3:    2 docs  →   2/40 =  5%
  Meeting #7:    1 doc   →   1/40 =  2.5%
  Others (13):   1 each  →   1/40 =  2.5% each

cap_ceiling = max(3, round(40 × 0.25)) = max(3, 10) = 10

Per-meeting caps:
  Meeting #9:   cap = max(3, min(10, round(20 × 0.5))) = max(3, min(10, 10)) = 10  ← dedicated
  Meeting #12:  cap = max(3, min(10, round(4  × 0.5))) = max(3, min(10, 2))  =  3  ← floor
  Meeting #3:   cap = max(3, min(10, round(2  × 0.5))) = max(3, min(10, 1))  =  3  ← floor
  Meeting #7:   cap = max(3, min(10, round(1  × 0.5))) = max(3, min(10, 0))  =  3  ← floor, has 1 → 1 passes
  Others:       cap = 3 each, have 1 each → 1 each passes

After cap:
  Meeting #9:   10 chunks pass  (14 of 20 are kept, 6 noise cut by ceiling... wait)
```

Wait — let me recalculate correctly:

```
Meeting #9: 20 docs → cap=10 → 10 pass, 10 cut
Meeting #12: 4 docs → cap=3  → 3 pass, 1 cut
Meeting #3:  2 docs → cap=3  → 2 pass (only has 2, floor ≥ actual)
Meeting #7:  1 doc  → cap=3  → 1 passes (only has 1)
Others (13 meetings, 1 each): 1 each → 13 pass

Total to reranker: 10 + 3 + 2 + 1 + 13 = 29 chunks
```

---

### Step 4 — rerank_documents(top_n=10)

Gemini scores all 29 chunks by relevance to "Give the AI architecture overview":

```
Meeting #9  chunks: score 8.5–9.5/10  (deep architecture content)
Meeting #12 chunks: score 6.5–7.5/10  (architectural updates)
Meeting #3  chunks: score 3.0–4.0/10  (brief mentions)
Meeting #7  chunk:  score 2.5/10      (passing reference)
Others:             score 0.5–1.5/10  (noise — not about architecture)

Top 10 after reranking:
  [1] Meeting #9  — microservices API gateway...          9.5
  [2] Meeting #9  — auth service JWT-based...             9.2
  [3] Meeting #9  — frontend connects via REST/GraphQL... 9.0
  [4] Meeting #9  — GCP Cloud Run deployment...           8.8
  [5] Meeting #9  — Pub/Sub event bus for async flows...  8.7
  [6] Meeting #9  — database layer PostgreSQL...          8.5
  [7] Meeting #12 — architecture confirmed unchanged...   7.5
  [8] Meeting #12 — API performance metrics reviewed...   7.2
  [9] Meeting #12 — deployment pipeline updated...        6.8
  [10] Meeting #9 — AI layer uses Gemini embeddings...    8.6 ← reranker keeps this over #12
```

---

### Step 5 — _expand_context(top_n=5)

Fetches prev/next neighbors for top 5 ranked chunks (all from Meeting #9):

```
[1] Meeting #9 chunk → fetches prev + next (2 extra context chunks)
[2] Meeting #9 chunk → fetches prev + next
[3] Meeting #9 chunk → fetches prev + next
[4] Meeting #9 chunk → fetches prev + next
[5] Meeting #9 chunk → fetches prev + next

LLM receives: 10 anchor chunks + up to 10 neighbor chunks = up to 20 chunks
```

---

### Step 6 — LLM Answer (with Rule 11 cross-meeting synthesis)

```
This topic was discussed across 3 meetings.
The primary discussion took place in AI Architecture Deep Dive (2026-04-15).

**AI Architecture Deep Dive (2026-04-15)**
Harsh Vardhan Dixit (05:00) explained the microservices approach: an API gateway
routes all traffic to auth, database, and feature services [1].
Harsh Vardhan Dixit (07:00) confirmed authentication uses JWT with refresh tokens [2].
Harsh Vardhan Dixit (09:00) detailed the frontend connecting via REST and GraphQL [3].
Harsh Vardhan Dixit (11:00) described deployment on GCP Cloud Run with Pub/Sub for
async event flows [4].

**Technical Review (2026-05-01)**
Harsh Vardhan Dixit (10:00) confirmed the architecture remains unchanged from April.
API performance metrics were reviewed and passed [7].

Also mentioned in: Sprint Planning (2026-03-10) [11].

The AI architecture was fully defined in April and confirmed stable through May. The
microservices design with GCP deployment is the current production approach.
```

---

## 8. Before vs After — Side by Side

```
BEFORE diversity cap               AFTER diversity cap + k-boost
──────────────────────────────     ──────────────────────────────
hybrid_retrieve: k=25              hybrid_retrieve: k=40
  Meeting #9: 15 chunks               Meeting #9: 20 chunks

After retrieval (no cap):          After diversity cap:
  Meeting #9: 15/25 = 60%            Meeting #9:  10/40 = 25% (ceiling)
  Meeting #12: 4/25 = 16%            Meeting #12:  3/40 (floor)
  Others: 6/25 = 24%                 Meeting #3:   2/40 (all pass)
                                     Others:       13 pass (1 each)

Reranker input: 25 chunks          Reranker input: 29 diverse chunks
Top 10 → LLM:                      Top 10 → LLM:
  8 from Meeting #9                   7 from Meeting #9
  1 from Meeting #12                  2 from Meeting #12
  1 from other                        1 from Meeting #9 (via reranker score)

LLM answer: mostly Meeting #9,     LLM answer: architecture overview with
missing technical review updates   updates from Technical Review included
```

---

## 9. Limitations

**The cap cannot redistribute unused slots.**
If Meeting #3 has 1 chunk and a cap of 3, the 2 unused slots do not go to Meeting #9. The cap is a ceiling, not a target. The total going to the reranker may be less than k. This is intentional — giving unused slots back to the dominant meeting defeats the purpose.

**Overview signal detection is keyword-based.**
A query like "walk me through everything about the database design" would not trigger the k-boost (no signal word matched). The PM would need to include "overview", "all", "describe", etc. for the boost to fire.

**Cap cannot know when a topic genuinely exists in only one meeting.**
If architecture is only in Meeting #9 and other meetings return pure noise, the cap still limits Meeting #9 to ceiling=10 and passes noise from other meetings to the reranker. The reranker handles this correctly — noise chunks score 0.5–1.5/10 and are dropped. But the cap itself does not detect the "one meeting only" case.

---

## 10. Test Coverage

| Test | What it verifies |
|---|---|
| Non-dominant meeting capped at floor | Meeting with 20% density gets cap=3 |
| Dominant meeting proportional cap | Meeting with 48% density gets cap=6 |
| Two dominant meetings independent | Both 44% meetings get cap=6 without affecting each other |
| RRF order preserved | Kept chunks maintain original rank order |
| Single-chunk meeting passes all | Floor ≥ actual count → all docs pass |
| Empty docs no crash | `_apply_diversity_cap([])` returns `[]` |
| Overview k-boost fires | Project-wide "overview" query → k > 25 |
| k-boost skipped for single meeting | scope_ids set → k stays ≤ 25 |
| k-boost skipped for focused query | No signal word → k stays ≤ 25 |