# OPEN QUESTIONS — AI Meeting Intelligence System

> Track unresolved design decisions, architecture gaps, and unknowns.
> Status: `[ ]` Open  `[x]` Resolved  `[~]` Deferred
> Priority: `[P1]` Blocking or high risk  `[P2]` Important but not blocking  `[P3]` Nice to know

---

## 1. Architecture

- [ ] [P1] Where does the pipeline live in production — is this a standalone FastAPI service, or does it get embedded into an existing product backend?
  > **Why it matters:** If embedded, imports and module layout may need to change. If standalone, we need auth middleware and a deployment plan.

- [ ] [P1] What happens when two users query the same project at the same time — is ChromaDB thread-safe for concurrent reads?
  > **Why it matters:** ChromaDB's local persistent mode has no built-in connection pooling. Under concurrent load it may behave unexpectedly. We may need to switch to a hosted vector DB (Pinecone, Weaviate) before production.

- [ ] [P2] Should the RAG pipeline be synchronous (blocks until answer ready) or async (queued job, answer delivered via webhook or polling)?
  > **Why it matters:** Gemini calls average 3-5s. Synchronous is fine for POC but will time out behind API gateways in production. Async requires a job queue (Celery, Redis, etc.).

- [ ] [P2] Is ChromaDB the right long-term vector store, or should we evaluate Pinecone / Qdrant / pgvector before scaling?
  > **Why it matters:** ChromaDB is file-based — it doesn't support horizontal scaling or replication. We should decide before investing in schema changes that are hard to migrate.

- [ ] [P3] Should embedding generation (Gemini `gemini-embedding-001`) be cached? If the same sentence appears in two meetings, should we re-embed or reuse?
  > **Why it matters:** Caching embeddings reduces API cost but adds complexity. Worth quantifying once we have 5+ projects.

---

## 2. Data & Storage

- [x] [P1] How does `project_id` get assigned to a meeting?
  > **Resolved (Session 2):** Manual `projects.json` — PM maps `project_id → { name, meeting_ids[] }`. Auto-registration deferred to production.

- [x] [P1] How does speaker role (client / pm / developer) get assigned?
  > **Resolved (Session 2):** Also in `projects.json` — PM manually sets role per speaker name. Regex normalization handles name variations.

- [ ] [P1] When a new meeting is ingested, what prevents the same meeting from being stored twice (duplicate chunk IDs in ChromaDB)?
  > **Why it matters:** Fireflies webhooks can fire more than once. If `store_documents()` runs twice on the same meeting, we get duplicate chunks that corrupt retrieval and summaries.

- [ ] [P1] What is the data retention policy — how long do transcripts stay in ChromaDB, and who can delete them?
  > **Why it matters:** GDPR and client confidentiality. If a client leaves, their data should be deletable. There is currently no delete endpoint or admin UI.

- [ ] [P2] Is the ChromaDB data directory (`chroma_db/`) backed up? What is the recovery plan if the server restarts and the folder is wiped?
  > **Why it matters:** All meeting intelligence is in this folder. If lost, we have to re-ingest every meeting from scratch (costs Gemini API calls + time).

- [ ] [P2] Should `projects.json` move into a database (Postgres, SQLite) before production, or stay as a file?
  > **Why it matters:** A flat file is fine for 1-3 projects. At 10+ projects, concurrent writes and search become a problem. Also, the file is checked into git — sensitive project names will appear in commit history.

- [~] [P2] Auto-registration of new meeting IDs — currently manual (`projects.json`).
  > **Deferred to production.** Options: Fireflies "meeting created" webhook → auto-register; PM assignment UI; or pending queue. See DISCUSSION.md.

---

## 3. Code Structure

- [ ] [P2] `answer_service.py` is doing too many things — query understanding, retrieval, reranking, context building, prompt selection, LLM call, source extraction. Should it be split into smaller modules?
  > **Why it matters:** The file is already 400+ lines and growing. A single change to reranking requires reading through all the other logic. Splitting now is cheaper than splitting later.

- [ ] [P2] `query_intent.py` has both `classify_query_intent()` and `understand_query()` — they partially overlap. Should they be merged into one function?
  > **Why it matters:** Two callers that do similar things creates a risk of divergence. If intent classification logic changes, it must be updated in two places.

- [ ] [P3] All prompts are in `prompts.py` — but the retrieval strategies are hard-coded in `answer_service.py`. Should retrieval strategy be part of the prompt config or stay separate?
  > **Why it matters:** If we want to A/B test different retrieval strategies per intent, having them in the same config makes that easier.

- [ ] [P3] There is no `__init__.py` documentation convention — should every module's public API be declared in its `__init__.py`?
  > **Why it matters:** When a new developer imports from `app.services.retrieval`, it's not obvious which functions are "public API" vs internal helpers. This affects maintainability.

---

## 4. Testing & Quality

- [ ] [P1] `easy_005` + `easy_011` failing — `general_query` misclassified as `summary_query`.
  > **Why it matters:** 83.3% pass rate on easy queries is below acceptable threshold. Root cause: "project meetings" and "last project sync" trigger summary intent. Fix: rephrase query or tighten `UNDERSTANDING_PROMPT_TEMPLATE`. See TODO.md.

- [ ] [P1] `run_tests.py` is not yet built — running the full test suite requires 3 separate commands.
  > **Why it matters:** Friction in the test process means developers skip it. One command = more likely to be run before every commit.

- [ ] [P2] The test runner only checks `intent_match` and `has_answer` — it does not verify if the answer content is actually correct.
  > **Why it matters:** A query can get the right intent and a non-empty answer, but the answer might be hallucinated or about the wrong meeting. An LLM evaluator (score 1–10) is needed for real quality assurance.

- [ ] [P2] There is no CI pipeline — tests are only run manually. Should we add GitHub Actions to run `run_tests.py` on every pull request?
  > **Why it matters:** Without CI, a breaking change can go undetected until someone runs the tests manually. This is especially risky once Sprint 3 re-ingestion changes the chunk schema.

- [ ] [P3] The query banks (easy/medium/hard) were generated by Gemini — they reflect the style of our current meetings. Should we add hand-written queries that reflect actual PM pain points?
  > **Why it matters:** Real PMs ask questions in ways an LLM wouldn't predict. Hand-written queries would catch more realistic failure modes.

---

## 5. Security

- [ ] [P1] There is no authentication on the `/query` FastAPI endpoint — anyone who knows the URL can query any project.
  > **Why it matters:** In production, PMs should only see data from their own projects. Without auth, any caller can pass any `project_id` and retrieve another project's meeting data.

- [ ] [P1] The Gemini API key is stored in `.env` — is this file excluded from git? Verify `.gitignore` includes `.env`.
  > **Why it matters:** If `.env` is accidentally committed, the API key leaks. A leaked Gemini key costs money and can be abused.

- [ ] [P2] `projects.json` contains project names and meeting IDs — is this sensitive data that should not be in a flat file on disk?
  > **Why it matters:** If the server is compromised, an attacker gets the full list of all projects and meetings. Consider encrypting at rest or moving to a secrets manager.

- [ ] [P2] Fireflies webhook does not validate the webhook signature — any POST to the endpoint is accepted.
  > **Why it matters:** An attacker could POST fake transcript data. Fireflies sends an HMAC signature in the request headers — we should verify it before processing.

- [ ] [P3] Are there any PII risks in the transcript chunks stored in ChromaDB (phone numbers, email addresses, personal names)?
  > **Why it matters:** If the system is used with client-facing meetings, personal data may end up in the vector DB. GDPR and data minimization principles apply.

---

## 6. Deployment

- [ ] [P1] Where does this run in production — local machine, VPS, container, cloud function?
  > **Why it matters:** ChromaDB local mode does not work in serverless (Lambda, Cloud Run) — stateless containers reset the file system. We need to decide on the deployment model before scaling.

- [ ] [P2] Is there a Dockerfile or deployment script? What does the production startup sequence look like?
  > **Why it matters:** Currently the app starts with `uvicorn main:app`. In production, we need process supervision, environment variable injection, health checks, and log forwarding.

- [ ] [P2] How does `chroma_db/` persist across container restarts? Is there a volume mount or external storage solution?
  > **Why it matters:** If ChromaDB is in the container filesystem, every restart wipes all embeddings. We need a persistent volume or hosted vector DB.

- [ ] [P3] Is there a staging environment? How do we test pipeline changes without touching production data?
  > **Why it matters:** Sprint 3 (re-ingestion) will wipe `chroma_db/` — if that's also production data, a staging environment is critical.

---

## 7. Performance & Scale

- [ ] [P2] How many projects and meetings can the system handle before ChromaDB query performance degrades?
  > **Why it matters:** Currently 1 project, 2 meetings, 521 chunks. BM25 loads the full project corpus into memory on every query — this scales poorly past 10,000 chunks.

- [ ] [P2] BM25 (`_fetch_project_corpus()`) loads ALL project chunks into memory on every query — is this cached between requests?
  > **Why it matters:** At 5,000+ chunks per project, re-loading the corpus for every query adds hundreds of milliseconds. A project-level cache with TTL would fix this.

- [ ] [P3] Gemini `gemini-2.5-flash` is used for answer generation — is there a fallback model if the API is unavailable or rate-limited?
  > **Why it matters:** If Gemini is down, the entire system returns errors. A fallback to a smaller/cheaper model or a cached "try again later" response improves resilience.

- [ ] [P3] Re-ranking calls Gemini Flash Lite once per query — what's the latency impact on p95? Is it acceptable?
  > **Why it matters:** Current avg response time is 3.4s. If re-ranking adds 1-2s on slow queries, we may exceed the 10s UX threshold on edge cases.

---

## 8. API & Integration

- [ ] [P1] Fireflies GraphQL API returns limited fields — are `rawStartTimeMs` and `rawEndTimeMs` available for all meeting types, or only for certain subscription tiers?
  > **Why it matters:** Sprint 3 (Tier 2a) depends on timestamp fields from the API. If they're not available on our current plan, the schema addition is blocked.

- [ ] [P2] What happens if the Fireflies API is down during webhook ingestion — does the pipeline retry, or is the meeting lost?
  > **Why it matters:** If ingestion fails silently, the meeting never makes it into ChromaDB. The PM would not know their last meeting is missing from the system.

- [ ] [P2] Is there a way to backfill historical meetings from Fireflies without triggering webhooks?
  > **Why it matters:** New projects need all past meetings ingested. Currently we manually call the API — there's no automated backfill script.

- [ ] [P3] The Fireflies API has rate limits — are we tracking our request count, and do we have retry logic with exponential backoff?
  > **Why it matters:** During re-ingestion (Sprint 3) we call the API for every meeting. If we hit the rate limit, ingestion stops mid-way with no clear error.

---

## 9. Process & Workflow

- [ ] [P2] Who reviews and approves changes before they go to production — is there a pull request process?
  > **Why it matters:** Currently one developer (you). As the team grows, a PR review process prevents breaking changes from reaching production.

- [ ] [P2] How will new meeting IDs be added to `projects.json` once the team grows — is there a documented process for the PM?
  > **Why it matters:** The PM can't edit JSON files. We need either a simple UI or a documented hand-off process before handing the system to a real PM.

- [ ] [P3] Is there a rollback plan if Sprint 3 re-ingestion (wipe + re-embed) produces worse results than the current pipeline?
  > **Why it matters:** Re-ingestion is destructive — it wipes `chroma_db/`. If the new chunking schema produces worse retrieval, we need a way to go back. Consider snapshotting `chroma_db/` before wiping.

- [ ] [P3] Should `DISCUSSION.md` be split into per-sprint files once it gets too large to read quickly?
  > **Why it matters:** DISCUSSION.md is already long. At Session 30+ it will take 20+ seconds to load. Per-sprint files with a summary index would keep context load fast.

---

## Resolved Questions Archive

| Question | Resolved In | Decision |
|----------|-------------|----------|
| How does `project_id` get assigned? | Session 2 | Manual `projects.json` — PM maps project_id → meeting_ids[] |
| How is speaker role set per project? | Session 2 | Manual in `projects.json` — PM sets role per speaker name |
| Which LLM for query understanding? | Session 10 | Gemini Flash Lite (LLM-first + regex fallback) |
| Where do prompts live? | Session 14 | `app/services/prompts.py` — all templates centralized |
| BM25 normalization for acronyms? | Session 17 | `_normalize_for_bm25()` — general acronym + punctuation pass |
| pipeline_logs empty in test results? | Session 18 | `propagate=False` — attach `_LogCapture` directly to each named logger |
