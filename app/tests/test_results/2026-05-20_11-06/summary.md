# Test Report — Easy Level

**Project:** `proj_nolocode_001`  
**Run timestamp:** 2026-05-20T11:08:11.898034  
**Report generated:** 2026-05-20 11:11  

---

## Summary

Pass rate: `[█████████████████░░░]` **83.3%**

| Metric | Value |
|---|---|
| Total queries | 12 |
| Passed | 10 |
| Failed | 2 |
| Errors | 0 |
| Avg response time | 7,777ms |
| Total run time | 95.5s |

---

## Results

| ID | Query | Status | Expected Intent | Actual Intent | Time |
|---|---|---|---|---|---|
| easy_001 | Give me a summary of the last meeting | PASS | summary_query | summary_query | 8,049ms |
| easy_002 | What decisions were made in the meetings? | PASS | decision_query | decision_query | 8,266ms |
| easy_003 | What are the action items from our meetings? | PASS | commitment_query | commitment_query | 8,397ms |
| easy_004 | What questions did the client ask in the meetings? | PASS | question_query | question_query | 9,303ms |
| easy_005 | What was discussed in the project meetings? | FAIL — wrong intent | general_query | **summary_query** | 3,969ms |
| easy_006 | What follow-up tasks were assigned? | PASS | commitment_query | commitment_query | 8,150ms |
| easy_007 | Give me an overview of the project progress | PASS | summary_query | summary_query | 6,322ms |
| easy_008 | What was agreed upon in the latest sprint planning meet… | PASS | decision_query | decision_query | 8,075ms |
| easy_009 | Can you give me a high level summary of the Q3 roadmap … | PASS | summary_query | summary_query | 5,919ms |
| easy_010 | Who committed to delivering the marketing assets? | PASS | commitment_query | commitment_query | 12,292ms |
| easy_011 | What were the main discussion points in the last projec… | FAIL — wrong intent | general_query | **summary_query** | 6,423ms |
| easy_012 | What questions did we have about the new feature propos… | PASS | question_query | question_query | 8,156ms |

---

## Intent Breakdown

Pass rate per intent type — useful for spotting which classifier path is weakest:

| Intent | Passed | Total | Pass Rate |
|---|---|---|---|
| commitment_query | 3 | 3 | 100% |
| decision_query | 2 | 2 | 100% |
| general_query | 0 | 2 | 0% |
| question_query | 2 | 2 | 100% |
| summary_query | 3 | 3 | 100% |

---

## Failed Queries

### easy_005 — FAIL — wrong intent

**Query:** "What was discussed in the project meetings?"

**Expected intent:** `general_query`  
**Actual intent:** `summary_query`

> The classifier routed this query to the wrong retrieval path. Check the pipeline trace below — look at the `[1/5] UNDERSTAND QUERY` step to see why the LLM or regex chose the wrong intent.

**Pipeline trace:**
```
INFO      app.services.answer_service  --------------------------------------------------------------
INFO      app.services.answer_service  PIPELINE START
INFO      app.services.answer_service    query      : What was discussed in the project meetings?
INFO      app.services.answer_service    project    : proj_nolocode_001
INFO      app.services.answer_service  --------------------------------------------------------------
INFO      app.services.answer_service  [1/5] UNDERSTAND QUERY
INFO      app.services.query_intent    understand : topic="project meetings discussions" | intent=summary_query | speaker=none | summary=True | temporal=none
INFO      app.services.answer_service  [2/5] RETRIEVE  (summary_query)
INFO      app.services.answer_service    strategy   : raw collection get — summary chunks chronologically (no vector search)
INFO      app.services.answer_service    summary    : 1 chunks found for project
INFO      app.services.answer_service  [3/5] RERANK   skipped (summary — chronological order preserved)
INFO      app.services.answer_service  [4/5] BUILD PROMPT
INFO      app.services.answer_service    docs used  : 1
INFO      app.services.answer_service    context    : 818 chars
INFO      app.services.answer_service    prompt     : "You are an AI assistant summarizing project progress for a project manager. Synthesize the following meeting summaries i..."
INFO      app.services.answer_service  [5/5] LLM CALL  (model: gemini-2.5-flash-lite)
INFO      app.services.answer_service  --------------------------------------------------------------
INFO      app.services.answer_service  PIPELINE DONE  (4.0s)
INFO      app.services.answer_service    intent     : summary_query
INFO      app.services.answer_service    sources    : 1 unique
INFO      app.services.answer_service      -> Nolocode meeting with Ashpreet (2026-05-08) | Meeting Summary
INFO      app.services.answer_service    answer     : "Here's a synthesized project overview based on the meeting summaries:  **Project Progress Overview**  **May 8, 2026 (Nolocode Meeting with Ashpreet)**..."
INFO      app.services.answer_service  --------------------------------------------------------------
```

### easy_011 — FAIL — wrong intent

**Query:** "What were the main discussion points in the last project sync?"

**Expected intent:** `general_query`  
**Actual intent:** `summary_query`

> The classifier routed this query to the wrong retrieval path. Check the pipeline trace below — look at the `[1/5] UNDERSTAND QUERY` step to see why the LLM or regex chose the wrong intent.

**Pipeline trace:**
```
INFO      app.services.answer_service  --------------------------------------------------------------
INFO      app.services.answer_service  PIPELINE START
INFO      app.services.answer_service    query      : What were the main discussion points in the last project sync?
INFO      app.services.answer_service    project    : proj_nolocode_001
INFO      app.services.answer_service  --------------------------------------------------------------
INFO      app.services.answer_service  [1/5] UNDERSTAND QUERY
INFO      app.services.query_intent    understand : topic="main discussion points in last project sync" | intent=summary_query | speaker=none | summary=True | temporal=none
INFO      app.services.answer_service  [2/5] RETRIEVE  (summary_query)
INFO      app.services.answer_service    strategy   : raw collection get — summary chunks chronologically (no vector search)
INFO      app.services.answer_service    summary    : 1 chunks found for project
INFO      app.services.answer_service  [3/5] RERANK   skipped (summary — chronological order preserved)
INFO      app.services.answer_service  [4/5] BUILD PROMPT
INFO      app.services.answer_service    docs used  : 1
INFO      app.services.answer_service    context    : 818 chars
INFO      app.services.answer_service    prompt     : "You are an AI assistant summarizing project progress for a project manager. Synthesize the following meeting summaries i..."
INFO      app.services.answer_service  [5/5] LLM CALL  (model: gemini-2.5-flash-lite)
INFO      app.services.answer_service  --------------------------------------------------------------
INFO      app.services.answer_service  PIPELINE DONE  (6.4s)
INFO      app.services.answer_service    intent     : summary_query
INFO      app.services.answer_service    sources    : 1 unique
INFO      app.services.answer_service      -> Nolocode meeting with Ashpreet (2026-05-08) | Meeting Summary
INFO      app.services.answer_service    answer     : "Here's a synthesized project overview based on the provided meeting summaries:  **Project Overview**  **Key Decisions Made:**  *   **Forecasting Formu..."
INFO      app.services.answer_service  --------------------------------------------------------------
```


---

## Sources Referenced

How often each meeting was used to answer queries:

| Meeting | Times referenced |
|---|---|
| Nolocode meeting with Ashpreet (2026-05-08) | 16 |
| Nolocode AI meeting (2026-05-19) | 10 |
