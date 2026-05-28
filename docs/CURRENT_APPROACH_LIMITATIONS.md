# Limitations of the Current Agent-Based RAG Architecture
### AI Meeting Intelligence System — Technical Review Document

**Prepared by:** Engineering Team  
**Date:** 2026-05-28  
**Status:** Internal — For Manager Review  
**System Version:** Sprint 6 Complete (41/41 tests passing, 10 meetings, 1,669 chunks)

---

## Executive Summary

The current system successfully answers narrow, specific questions about meetings with high accuracy (41/41 test queries passing, average score 8.8/10). However, it has architectural limitations that become apparent as the query complexity and data volume increase. This document catalogs each limitation with its technical root cause, real-world impact, and a concrete example of where it breaks down.

Limitations are grouped into four severity tiers:

| Tier | Label | Meaning |
|------|-------|---------|
| 🔴 | **Critical** | Causes wrong or incomplete answers for a defined class of queries |
| 🟠 | **Significant** | Degrades answer quality noticeably; affects user trust |
| 🟡 | **Structural** | Requires architectural change before scaling to production |
| 🔵 | **Infrastructure** | Operational risk not visible in day-to-day testing |

---

## System Overview (Context for Review)

The current pipeline processes every user query through five sequential steps:

```
User Query
    │
    ▼
[1] understand_query()      ← LLM call #1 — classifies intent, extracts topic/speaker/scope
    │
    ▼
[2] _retrieve_for_understanding()  ← 8 modes: hybrid, compound, summary,
    │                                  timeline, topic_summary, analytical,
    │                                  contribution, signal_fetch, metadata
    ▼
[3] rerank_documents()      ← LLM call #2 (Gemini Flash Lite) — scores relevance
    │
    ▼
[3.5] expand_context()      ← fetches prev/next neighbor chunks for top-5 results
    │
    ▼
[4] build_prompt()          ← assembles context (max 10–25 chunks) into prompt
    │
    ▼
[5] call_gemini()           ← LLM call #3 — generates final answer
    │
    ▼
Answer + Sources
```

**What is stored:** Raw ASR transcript text, chunked by speaker turn, with rule-based metadata (decision/commitment/question signals, meeting_id, speaker_name, timestamps).

**Current scale:** 10 meetings, 1,669 chunks, 5 speakers per project.

---

## Limitation 1 — Hard Cap on Retrieved Chunks Breaks Broad Aggregation Queries 🔴

### Description
The retrieval layer fetches at most 25–40 chunks per query. After reranking and context expansion, the LLM receives a maximum of 10–25 chunks. For narrow, specific questions this is sufficient. For broad aggregation queries — questions that are genuinely answered by information distributed across many meetings — the cap means the LLM never sees most of the relevant evidence.

### Technical Detail
In `config.py`, `get_retrieval_config()` sets the following hard limits:

```python
# compound mode, project-wide
k_dense = 40, k_final = 25

# topic_summary mode, all meetings
k_per_meeting = 6   # 6 chunks per meeting × 10 meetings = 60 total
                    # then trimmed to 15 in pipeline.py
```

The pipeline then trims to:
- `topic_summary` mode: **15 chunks**
- `signal_fetch` mode: **25 chunks**
- All other modes: **10 chunks**

### Real-World Impact
A query like *"What are all the statements about the CE classification code made by Bhavneet throughout this project?"* is genuinely answered by 30–40 chunks spread across 10 meetings. With a 10–25 chunk cap, the LLM receives at most 62.5% of the relevant evidence. It cannot say "Bhavneet mentioned CE in meeting 3, 5, 7, and 9" — it can only say what appears in the top-ranked fragments it received.

### Concrete Example
```
Query: "What are all decisions made about the OCA formula across all meetings?"

Relevant chunks in ChromaDB: ~35 (spread across 8 meetings)
Chunks the LLM actually sees: 10–15
Missing evidence: ~20–25 chunks silently dropped
Result: An answer that covers 3–4 meetings and omits 4–5 where OCA was discussed
```

The answer is not wrong — it is incomplete, and the user has no way to know it is incomplete.

---

## Limitation 2 — Single LLM Context Window Cannot Synthesize Cross-Meeting Patterns 🔴

### Description
The LLM receives a flat list of 10–25 chunks and must synthesize an answer from them in a single call. For questions that require comparing how a discussion evolved across multiple meetings (e.g., "how did the team's understanding of fixed assets change from meeting 1 to meeting 6?"), this single-pass design is structurally insufficient.

### Technical Detail
`build_context()` in `builder.py` concatenates all retrieved chunks into one string, labelled `[1]`, `[2]`, ... `[N]`, and passes this to a single LLM call. There is no intermediate summarisation or grouping step. The LLM must hold all cross-meeting reasoning in a single generation pass.

### Real-World Impact
- The model exhibits "lost in the middle" behaviour — it reliably cites chunks at the beginning and end of the context, but frequently misses evidence in the middle when context is long.
- For evolution/comparison queries ("how has X changed across meetings?"), the model tends to pick the most recently discussed version and present it as the definitive answer, silently ignoring earlier contradictory statements.

### Concrete Example
```
Query: "How did the discussion about accumulated depreciation evolve 
        across the Nolocode meetings?"

What actually happened across meetings:
  Meeting 3 → Team asked Bhavneet about DEP code for accumulated depreciation
  Meeting 5 → Bhavneet said it should not appear in the balance sheet
  Meeting 7 → Accumulated depreciation row confirmed to be removed from UI

With a flat 15-chunk context window, the LLM sees fragments from all three
meetings mixed together with no structural grouping. It typically synthesises
the most dominant signal (Meeting 7 outcome) and under-represents the journey.
```

---

## Limitation 3 — Query Understanding Failure Propagates to All Downstream Steps 🔴

### Description
Every query passes through `understand_query()`, which makes an LLM call to classify intent, extract the topic, identify the speaker name, and determine the retrieval scope. If this LLM call returns an incorrect classification — wrong intent, wrong scope, missed speaker — the entire pipeline routes to the wrong retrieval mode and returns an answer from the wrong set of chunks. There is no recovery path once routing happens.

### Technical Detail
`understand_query()` calls `call_gemini_raw()` with a structured prompt that expects a JSON response. The function has a regex fallback, but the fallback only covers 6 basic intents and cannot detect:
- Meeting scope ("this meeting", "the second meeting", "the last Nolocode call")
- Compound queries (speaker + topic + signal, e.g. "What questions did Rhythm ask about OCA?")
- Named speaker extraction when the name is spelled differently than in `projects.json`

When the LLM misclassifies, `retrieval_mode` is wrong, and the 8-mode dispatch in `_retrieve_for_understanding()` executes the wrong retrieval strategy.

### Real-World Impact
Observed failure modes from the test suite build process:
- Gemini returning `topic: null` caused a Pydantic crash (fixed with `@field_validator`) — a sign the LLM regularly returns malformed output
- `understand_query()` missing `is_attribution=True` on ordering queries was fixed by adding a separate Python regex override
- Queries like "What did we discuss about CE codes?" were misclassified as GENERAL instead of TOPIC_SUMMARY, returning 3 generic chunks instead of meeting-by-meeting CE code discussion

### Concrete Example
```
Query: "What questions did Rhythm ask Bhavneet about OCA in the last meeting?"

Correct routing: compound mode, speaker=Rhythm, signal_filter=question, scope=last_meeting
Misclassified as: SPEAKER mode, speaker=Rhythm, no signal, no scope

Result: Returns all Rhythm statements across all meetings instead of just 
        OCA-related questions from the last meeting. The answer is 
        confidently wrong.
```

---

## Limitation 4 — Raw ASR Text in Embeddings Produces Weak Semantic Signals 🟠

### Description
The system stores raw ASR transcript text directly in ChromaDB. ASR output from tools like Fireflies contains micro-fragments ("So.", "Am.", "Right.", "Yeah."), speaker crosstalk, and incomplete sentences. These become the documents that get embedded and searched against. Embedding a fragment like *"Right."* or *"26 2."* generates a near-meaningless vector that weakens the retrieval quality for every nearby chunk.

### Technical Detail
In `chunking.py`, the minimum chunk length is enforced by `HARD_MIN = 15` characters, but many chunks that pass this threshold are still semantically empty. The `_is_low_quality()` filter drops chunks with fewer than 2 meaningful words, but it only applies at flush time — short utterances that get concatenated into a longer chunk (e.g., `"Right. 26 2. You have the AR balance..."`) carry the noise into the final stored text.

The current workaround (context expansion via `prev_chunk_id`/`next_chunk_id`) partially compensates, but it adds 10 extra DB lookups per query and does not improve the embedding quality itself.

### Real-World Impact
When a user asks about "OCA prepaid close formula," the vector search must overcome the noise of fragments like:
```
Bhavneet: OCA will be prepaid closed. Right. That is telling you the 
calculation of how to get there from open to close. So it's pretty paid.
```
The phrase "So it's pretty paid." is an ASR misrecognition of "So it's prepaid." These errors appear verbatim in the stored text and affect both embedding quality and the LLM's reading of the context.

### Concrete Example
```
Stored chunk text (as-is in ChromaDB):
  "Bhavneet: 26 2. You have the AR balance, inventory balance, AP balance. 
   Yeah, we've added all that in here. I think we like we have to 
   only take this sub account value."

Problem: "26 2." is an ASR artifact (probably "2026 2025" or a cell reference).
         It is embedded and searched as meaningful text.
         When users ask about "balance sheet values", this chunk scores 
         artificially high on "balance" matches but contains no usable answer.
```

---

## Limitation 5 — One Chunk = One Speaker Loses Conversational Context 🟠

### Description
The chunking strategy in `chunking.py` creates one chunk per speaker turn. A back-and-forth exchange between two speakers about the same topic is stored as 4–8 separate chunks, each attributed to one speaker. When the retrieval system fetches "what did Bhavneet say about OCA?", it returns only Bhavneet's turns — but Bhavneet's statements are often direct responses to Rhythm's questions, and without the question, the answer is incomplete or confusing.

### Technical Detail
In `create_chunks()`:
```python
if speaker != current_speaker:
    flush_chunk(force=True)   # split at every speaker change
```

This means a 12-turn dialogue about OCA (6 Bhavneet turns, 6 Rhythm turns) becomes 12 separate chunks. The pipeline fetches Bhavneet's 6 chunks, which contain statements like:
- *"OCA will be prepaid closed."*
- *"That is telling you the calculation..."*
- *"Change in OCA it will be what your prepaid close is from the previous month."*

Without the interleaved Rhythm questions, these read as a monologue, not a Q&A, and the LLM cannot determine what question each statement is answering.

### Real-World Impact
- Attribution queries ("What did Bhavneet say about X?") return answers without the context of *why* Bhavneet said it
- The `expand_context()` step (fetches prev/next chunks) partially compensates, but adds latency and still only retrieves ±1 neighbor per chunk, not the full conversational thread

### Concrete Example
```
User: "What was Bhavneet's explanation of the OCA calculation?"

Retrieved chunk (Bhavneet turn only):
  "Change in OCA it will be what your prepaid close is from the previous 
   month. So if you're looking at March 2026, you're comparing your 
   March 2026 prepaid close number to February 2026 prepaid close."

Missing (Rhythm's prior question that prompted this explanation):
  "So how will we calculate it — prepaid close minus prepaid open 
   for change in OCA?"

Without the question, the LLM presents Bhavneet's answer as a standalone 
statement rather than a direct answer to a specific calculation query.
```

---

## Limitation 6 — Reranker Adds Latency Without Guaranteed Improvement 🟠

### Description
The reranking step (Step 3 in the pipeline) makes a third LLM call using Gemini Flash Lite to score retrieved chunks for relevance. This adds 1.5–3 seconds of latency per query and uses a smaller, less capable model than the answer generation step. In practice, the reranker is skipped for `summary`, `topic_summary`, and `signal_fetch` modes — meaning it runs only for `hybrid` and `compound` modes, which are the most common.

### Technical Detail
`rerank_documents()` in `reranker.py` calls Gemini Flash Lite with a scoring prompt for each candidate document. The reranker uses an `intent_hint` and `topic_hint` to guide scoring, but the model used (`gemini-2.0-flash-lite`) has significantly reduced reasoning capability compared to `gemini-2.5-flash` used for answer generation. In cases where relevance is semantically nuanced, the reranker may deprioritise a genuinely relevant chunk because the phrasing is indirect.

### Real-World Impact
- Average query time increases by 1.5–3 seconds for hybrid/compound queries
- The reranker operates on at most 25–40 candidates, so its effectiveness ceiling is bounded by whatever `hybrid_retrieve()` returns. If the most relevant chunk was not in the top 40 by vector similarity, the reranker never sees it.
- When the reranker fails or times out, the fallback is original vector-similarity order — which may be worse than a simple BM25 ranking for keyword-heavy queries.

---

## Limitation 7 — Three Known Query Scenarios Have No Implementation Path 🟠

### Description
Sprint 6 testing identified three specific query types that the current architecture cannot correctly answer. These are not edge cases — they represent a common category of PM question (topic importance, Q&A pairing, issue resolution tracking).

### The Three Known Gaps

**Gap 1 — Topic Importance (S10)**
> *"Which topic was most important in this project?"*

**Problem:** "Importance" requires a subjective judgement. The system has no proxy metric (mention count, time spent, number of questions raised). The current `analytical` mode only counts by signal type (decisions, commitments, questions) — it cannot rank topics by a composite importance score.

**Gap 2 — Q&A Pairing (S13)**
> *"Can we answer all of Bhavneet's questions from the first meeting?"*

**Problem:** This requires pairing question chunks with answer chunks across speakers. Questions are stored as individual speaker chunks; their answers are stored in separate speaker chunks. No chunk currently carries a "this answers question X" link. The system cannot determine whether a question received an answer.

**Gap 3 — Resolution Tracking (S28)**
> *"Which unresolved issue was discussed most recently?"*

**Problem:** The `contains_open_issue` signal flags chunks that mention an issue. But there is no `is_resolved` counterpart signal. The system cannot distinguish an issue that was raised and then resolved in a later meeting from an issue that remains open.

---

## Limitation 8 — No Deduplication of Ingested Meetings 🟡

### Description
There is no idempotency check when ingesting a meeting. If a Fireflies webhook fires twice for the same meeting (which Fireflies does in practice — it sends one event when the transcript is ready and another when the summary is ready), all chunks for that meeting are stored twice in ChromaDB.

### Technical Detail
`store_documents()` in the storage layer calls ChromaDB's `.add()` directly with generated chunk IDs like `{meeting_id}_{chunk_index}`. ChromaDB does not enforce uniqueness on document IDs added via LangChain's `.add_documents()` by default — duplicate IDs result in two separate records rather than an upsert.

### Real-World Impact
- **Retrieval corruption:** A duplicated meeting appears twice as often in similarity search results, effectively doubling its weight in any project-level query. A query about "all decisions" in a project would report double the number of decisions from the duplicated meeting.
- **Analytical count errors:** `analytical_retrieve()` counts chunks by metadata filter. A duplicated meeting returns double counts: *"There were 4 decisions"* would show *"There were 8 decisions"* for the duplicated meeting.
- **Silent corruption:** There is no log warning or error. The duplication is invisible until manually inspecting ChromaDB.

### Concrete Example
```
Fireflies sends two webhooks for meeting "01KM2DD6MXGSZ4F1QW0BNJE16N":
  - Event 1 (transcript ready): 167 chunks stored
  - Event 2 (summary ready): 167 chunks stored again

ChromaDB now has 334 chunks for this meeting instead of 167.

User query: "How many decisions were made in the Nolocode meeting?"
Actual decisions: 4
Reported decisions: 8 (each decision chunk counted twice)
```

---

## Limitation 9 — projects.json is Not Production-Safe 🟡

### Description
All project configuration — project names, meeting-to-project mappings, and speaker role assignments — is stored in a flat JSON file (`projects.json`) that is checked into the git repository. This is the right choice for a POC but is a blocker before any production deployment.

### Technical Detail
`project_store.py` reads `projects.json` on every call to `get_project_for_meeting()` and `get_speaker_names()`. There is no caching, no concurrent-write protection, and no delete capability.

### Specific Production Risks

| Risk | Detail |
|------|--------|
| **Sensitive data in git** | Client names, project names, and speaker names are committed to version control. If this repository is shared or the git history is visible, client confidentiality is compromised. |
| **No delete endpoint** | There is no way to remove a project or meeting from the system. If a client offboards, their data remains in ChromaDB and `projects.json` permanently. This is likely a GDPR violation. |
| **No concurrent write safety** | If two meetings are ingested simultaneously, both processes may read the file at the same time and one write may overwrite the other's changes. |
| **Manual speaker role assignment** | Every new speaker must be manually added to `projects.json` with their role. There is no auto-detection or UI for this. |

---

## Limitation 10 — ChromaDB Local Mode Has No Concurrency or Redundancy 🔵

### Description
The system uses ChromaDB in local persistent mode — data is stored in a directory on the filesystem (`chroma_db/`). This works perfectly for a single-instance POC but has hard operational limits for production deployment.

### Technical Detail
ChromaDB's local persistent client does not support:
- Multiple simultaneous read connections from parallel API requests
- Horizontal scaling (cannot run on two servers sharing the same data)
- Replication or failover
- Point-in-time backup or restore

### Specific Production Risks

| Risk | Detail |
|------|--------|
| **Concurrent query failures** | Two simultaneous user queries may cause ChromaDB contention. This is not tested and the behaviour under load is unknown. |
| **Data loss on server restart** | If the server's `chroma_db/` directory is wiped (container restart, accidental `rm`, disk failure), all 1,669 chunks and embeddings are permanently lost. Re-ingesting 10 meetings costs API calls and time; at 100+ meetings this becomes a significant recovery event. |
| **No horizontal scaling** | Cannot deploy the system across multiple API server instances without a shared, networked vector store (Pinecone, Qdrant, Weaviate). |

---

## Limitation 11 — Synchronous Pipeline Blocks on Gemini API Latency 🔵

### Description
Every query executes synchronously — the HTTP response does not return until all three LLM calls (understand → rerank → answer) complete. Gemini API calls average 1.5–3 seconds each, giving a typical total latency of 3–7 seconds per query. Under production load with API rate limiting or 503 errors, this blocks the request thread indefinitely.

### Technical Detail
The pipeline calls `call_gemini()` three times per query:
1. `understand_query()` — intent classification + scope detection
2. `rerank_documents()` — relevance scoring (skipped for 3 of 8 modes)
3. Final answer generation

These calls are sequential (each depends on the prior result). Exponential backoff retry logic was added (3 attempts: 2s, 5s, 10s delays), meaning a single Gemini 503 error can add up to 17 extra seconds before the fallback fires.

### Real-World Impact
- An API gateway with a 30-second timeout will surface this as a user-visible error during any Gemini overload period
- There is currently no queue or async job system — a surge of simultaneous queries will exhaust available threads and produce timeouts for all users

---

## Limitation 12 — No Enriched Context: LLM Sees Fragmented ASR, Not Reconstructed Facts 🟠

### Description
The chunks stored in ChromaDB contain raw ASR text exactly as Fireflies transcribed it. This means the LLM generating the final answer reads fragments like *"So it's pretty paid."* (ASR error for "prepaid"), *"Cediv."*, *"26 2."* — and must infer correct meaning from degraded input. Additionally, each chunk lacks surrounding conversational context: without knowing what question a statement is answering, short statements like *"Correct."* or *"That is right."* are ambiguous.

### Technical Detail
There is no enrichment step at ingestion time. What Fireflies transcribes is what gets embedded and stored verbatim. The system has no mechanism to:
- Reconstruct what a confirmation ("Correct.") refers to
- Replace ASR errors with corrected text
- Add the question context to a short answer statement
- Generate a self-contained description of what happened in a chunk

### Real-World Impact
For questions requiring precise facts (exact formulas, exact numbers, exact decisions), the LLM must reason through ASR noise and context gaps to reconstruct meaning. This increases hallucination risk for detail-heavy queries compared to a system that stores enriched, reconstructed text.

---

## Summary Table

| # | Limitation | Tier | Affected Query Types | Can Fix Without Re-architecture? |
|---|------------|------|---------------------|----------------------------------|
| 1 | Hard cap on retrieved chunks | 🔴 Critical | Broad aggregation queries | No — requires map-reduce path |
| 2 | Single LLM pass for cross-meeting synthesis | 🔴 Critical | Evolution/comparison queries | No — requires multi-pass synthesis |
| 3 | Query understanding failure cascades | 🔴 Critical | Any misclassified query | Partially — add more fallbacks |
| 4 | Raw ASR noise in embeddings | 🟠 Significant | All retrieval-based queries | No — requires enriched ingestion |
| 5 | One-speaker-per-chunk loses dialogue context | 🟠 Significant | Attribution, speaker queries | Partially — widen context expansion |
| 6 | Reranker adds latency without full guarantee | 🟠 Significant | Hybrid, compound modes | Yes — tune or replace reranker |
| 7 | Three known unanswerable scenario types | 🟠 Significant | S10, S13, S28 scenario types | Requires new signals + new modes |
| 8 | No deduplication on ingestion | 🟡 Structural | All queries against duplicated meeting | Yes — add upsert logic to store |
| 9 | projects.json not production-safe | 🟡 Structural | All projects | Yes — migrate to DB |
| 10 | ChromaDB local mode, no redundancy | 🔵 Infrastructure | All queries under load | Yes — switch to hosted vector DB |
| 11 | Synchronous pipeline blocks on API latency | 🔵 Infrastructure | All queries during API instability | Yes — add async queue |
| 12 | No enriched context at ingestion | 🟠 Significant | Detail-heavy fact queries | No — requires ingestion redesign |

---

## What the Current System Does Well

To provide balanced context, the following capabilities are working correctly and should be preserved in any architectural evolution:

- **Narrow specific queries:** "What did Bhavneet say about prepaid close?" — correctly retrieves and answers with 8.8/10 average score
- **Signal-based exhaustive retrieval:** "What questions did Rhythm ask?" — `signal_fetch` mode exhaustively fetches all question chunks, guaranteed no omissions
- **Counting queries:** "How many decisions were made?" — `analytical` mode returns exact metadata count without vector search
- **Meeting scope detection:** "What happened in the last meeting?" — correctly resolves scope from ordinal phrases and meeting metadata
- **Speaker name resolution:** 4-level fuzzy matching (full name → first name → last name → initial+last) handles name variations
- **Fast metadata queries:** "List all meetings" — zero LLM calls, pure metadata lookup, sub-100ms response

---

## Recommended Priority Order for Addressing Limitations

1. **Immediate (before adding more meetings):** Fix deduplication on ingestion (#8) — currently causes silent data corruption with zero detection
2. **Short-term (before PM demos):** Add map-reduce retrieval path for broad aggregation queries (#1, #2) — this is the gap most likely to be hit in real PM usage
3. **Medium-term (before production):** Migrate `projects.json` to a database (#9), switch to hosted ChromaDB or Qdrant (#10), add async query processing (#11)
4. **Long-term (next architecture iteration):** Enrich chunks at ingestion time (#4, #12), redesign chunking to preserve conversational dialogue (#5), implement Q&A pairing and resolution tracking (#7)

---

*Document prepared from code review of `app/rag/answer/pipeline.py`, `app/rag/query_intent.py`, `app/core/retrieval/config.py`, `app/core/retrieval/hybrid.py`, `app/core/transcript/chunking.py`, `docs/SPRINT.md`, and `docs/OPEN_QUESTIONS.md`.*