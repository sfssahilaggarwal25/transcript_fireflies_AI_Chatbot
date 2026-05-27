# Improvement Plan — AI Meeting Intelligence System

> Comparison baseline: Otter.ai tested on "M2 & M4 discussion (6:30pm UAE)" meeting.
> Last updated: 2026-05-21
> Status key: `[ ]` Not started · `[~]` In progress · `[x]` Done

---

## How to use this file

- Each gap has a **Priority** (P1 = most impactful, P3 = nice-to-have).
- Each fix has an **Effort** estimate and **Files to change**.
- When you start a fix, change `[ ]` → `[~]`. When done, change to `[x]` and fill the **Completed** date.
- Add new gaps you discover at the bottom under the correct section.

---

## Gap Analysis — Where We Lag Behind Otter.ai

### G1 — Answer format ignores the question shape `[P1]`

**What Otter.ai does:**
- "summarize this meeting" → numbered sections with headers + action items table
- "give me a list of X" → clean bullet list with one item per line
- "what is the conclusion on X" → short direct conclusion paragraph

**What we do:**
- Every query of the same *intent* gets the same template format (prose)
- The LLM has no instruction about whether to output bullets, tables, sections, or prose
- Format is decided by intent bucket, not by what the user actually asked

**Fix:** Add `_detect_output_format(query)` in `answer_service.py` and pass it into the prompt so the LLM formats output to match the question.

| Field | Detail |
|---|---|
| Priority | P1 |
| Effort | 1 day |
| Files | `app/services/answer_service.py`, `app/services/prompts.py` |
| Status | `[ ]` Not started |
| Completed | — |

**Implementation notes:**
```python
def _detect_output_format(query: str) -> str:
    q = query.lower()
    if any(w in q for w in ["list", "give me all", "show me all", "what are all"]):
        return "bullet_list"
    if any(w in q for w in ["table", "breakdown", "structured"]):
        return "table"
    if any(w in q for w in ["summarize", "summary", "overview", "recap"]):
        return "structured_sections"
    if any(w in q for w in ["conclusion", "outcome", "result", "what was decided", "final"]):
        return "conclusion"
    return "prose"
```
Append format instruction to every prompt before the LLM call.

---

### G2 — Speaker queries answer "what they said", not "what they were trying to explain" `[P1]`

**What Otter.ai does:**
- "What is Ngumi trying to explain" → analyses his *intent*, role in the meeting, what he was trying to achieve, references timestamps, explains how he influenced the discussion

**What we do:**
- Retrieves chunks where that speaker spoke → LLM summarises the content
- Answers "what did he say" not "what was he trying to accomplish/explain"
- No analysis of speaker's role or contribution level

**Fix:** Update `ANSWER_PROMPT_TEMPLATES["speaker_query"]` in `prompts.py` to ask the LLM to analyse speaker intent, not just content.

| Field | Detail |
|---|---|
| Priority | P1 |
| Effort | 0.5 day |
| Files | `app/services/prompts.py` |
| Status | `[x]` Done |
| Completed | 2026-05-21 |

---

### G3 — No compound speaker + topic filtering `[P1]`

**What Otter.ai does:**
- "What did Ngumi say about the save button" → retrieves *Ngumi's chunks specifically about the save button*

**What we do:**
- `hard_filters = {"speaker_name": named_speaker}` is applied as a ChromaDB pre-filter
- This means semantic scoring never runs on speaker chunks — we get all Ngumi chunks ranked by BM25 only
- Cannot answer "what did [person] say about [topic]" correctly

**Fix:** Two-pass retrieval when both `named_speaker` and a topic are present.

| Field | Detail |
|---|---|
| Priority | P1 |
| Effort | 1 day |
| Files | `app/services/answer_service.py`, `app/services/retrieval/retriever.py` |
| Status | `[ ]` Not started |
| Completed | — |

**Implementation notes:**
```
Pass 1: hybrid_retrieve(topic_query, project_id, hard_filters=None, k=40)
Pass 2: from those 40 results, filter where chunk.metadata["speaker_name"] == named_speaker
If fewer than 3 remain after filter → fall back to Pass 1 results (relax speaker constraint)
```
This lets semantic search run first, then speaker filter narrows the results.

---

### G4 — Commitments not extracted as structured tasks `[P1]`

**What Otter.ai does:**
```
Task: Provide breakdown for forecasted statements
Assignee: Project Manager SFS
Timeline: this week
Source: agreed in meeting
```

**What we do:**
- Returns raw transcript chunks where `contains_commitment=True`
- LLM generates prose about what commitments exist
- No structured Task → Assignee → Timeline extraction

**Fix:** Update `ANSWER_PROMPT_TEMPLATES["commitment_query"]` to output a markdown table.

| Field | Detail |
|---|---|
| Priority | P1 |
| Effort | 0.5 day |
| Files | `app/services/prompts.py` |
| Status | `[ ]` Not started |
| Completed | — |

**New output format instruction:**
> "Extract all action items and commitments. Format as a table:
> | Task | Owner | Timeline | Meeting |
> For each row, use only information explicitly stated in the transcript.
> If owner or timeline is not mentioned, write 'Not specified'."

---

### G5 — No "conclusion on X" capability `[P2]`

**What Otter.ai does:**
- "What is the conclusion on the save button" → finds the *final state* of that topic: what was NOT decided, what was clarified, what the next step is

**What we do:**
- Hybrid retrieval ranks by *relevance*, not by *temporal order*
- We return the most semantically central chunks, not the final-state chunks
- No concept of "what was said last about this topic"

**Fix:** New `conclusion_query` intent + time-sorted retrieval strategy.

| Field | Detail |
|---|---|
| Priority | P2 |
| Effort | 1 day |
| Files | `app/services/query_intent.py`, `app/services/answer_service.py`, `app/services/prompts.py` |
| Status | `[ ]` Not started |
| Completed | — |

**Implementation notes:**
- Trigger: keywords like "conclusion", "outcome", "result", "what was decided on", "what was agreed on", "final answer on"
- Retrieval: hybrid search → sort results by `start_time` descending (most recent first) → take top 10
- Prompt: "Based on the transcript, what was the final outcome or conclusion reached about [topic]? Focus on the last thing said about it, not the earlier discussion."

---

### G6 — Financial formula / calculation queries not handled `[P2]`

**What Otter.ai does:**
- "What financial formulas were discussed" → extracts mathematical relationships with actual numbers, inputs, outputs, step-by-step logic

**What we do:**
- Falls into `general_query` intent
- LLM has no instruction to look for or format mathematical/formula content
- Returns random semantic matches, not targeted formula extraction

**Fix:** Add `formula_query` intent.

| Field | Detail |
|---|---|
| Priority | P2 |
| Effort | 1 day |
| Files | `app/services/query_intent.py`, `app/services/prompts.py` |
| Status | `[ ]` Not started |
| Completed | — |

**Trigger keywords:** "formula", "calculation", "how is X calculated", "what's the math", "how do you derive", "what formula", "what equation"

**Prompt instruction:**
> "Extract all formulas, calculations, and mathematical relationships discussed.
> For each: (1) Name/label of the formula (2) Inputs (3) Output (4) Step-by-step calculation (5) Any example numbers given.
> Use only what is explicitly stated in the transcript."

---

### G7 — Participant/contributor analysis is a flat list `[P2]`

**What Otter.ai does:**
- "Who are the main contributors" → categorised as Main Contributors vs Other Participants, with 3-4 bullet summary per person of *what they drove*

**What we do:**
- METADATA intent lists speaker names and roles
- No analysis of contribution level, what each person discussed, or who drove which topics

**Fix:** Improve METADATA handling for participant/contributor queries to include summary chunks per speaker.

| Field | Detail |
|---|---|
| Priority | P2 |
| Effort | 0.5 day |
| Files | `app/services/answer_service.py` |
| Status | `[ ]` Not started |
| Completed | — |

**Implementation notes:**
- When query contains "contributor", "who drove", "who discussed", "main participant" → fetch summary chunks + speaker chunk counts
- Pass to LLM with prompt: "Categorise speakers by contribution level. For each major contributor, describe what they discussed and what they drove."

---

### G8 — No timestamp references in answers (implemented but accuracy unverified) `[P3]`

**What Otter.ai does:**
- Cites [00:07:49] timestamps when attributing what someone said

**What we do:**
- `start_time` / `end_time` are stored in chunk metadata
- Never surfaced in the answer text or sources

**Fix:** Include `start_time` formatted as MM:SS in `_build_context()` and instruct prompt to reference it when quoting.

| Field | Detail |
|---|---|
| Priority | P3 |
| Effort | 0.5 day |
| Files | `app/services/answer_service.py`, `app/services/prompts.py` |
| Status | `[x]` Done |
| Completed | 2026-05-21 |

---

### G19 — Speaker answers ignore the conversation thread `[P1]`

**What Otter.ai does:**
- "After Neha explains that the principal repaid value is static... Ngũmi translates this for everyone"
- Shows WHAT prompted the speaker's statement (what another speaker said right before)
- Shows HOW others responded (Bhavneet connects it to formulas)
- The answer reads as a narrative conversation, not isolated chunks

**What we do:**
- `_expand_context()` already fetches `prev_chunk_id` / `next_chunk_id` neighbors (which CAN be from other speakers)
- BUT the `speaker_query` prompt says "attribute statements to the correct speaker by name" → LLM ignores the `[CONTEXT — just before/after]` blocks entirely
- Result: 3 isolated "Ngũmi said X" blocks with no surrounding conversation

**Root cause:** The prompt does not instruct the LLM to use the context blocks to explain what triggered each statement or how others responded to it.

**Fix:** Update `ANSWER_PROMPT_TEMPLATES["speaker_query"]` to explicitly use the `[CONTEXT — just before/after]` blocks from `_build_context()`.

| Field | Detail |
|---|---|
| Priority | P1 |
| Effort | 0.5 day |
| Files | `app/services/prompts.py` |
| Status | `[x]` Done |
| Completed | 2026-05-21 |

**Prompt addition for `speaker_query`:**
```
- Context chunks labelled [CONTEXT — just before] show what another speaker said immediately
  before the named speaker's statement — use this to explain what prompted or triggered it.
- Context chunks labelled [CONTEXT — just after] show how others responded — use this to
  explain what effect the speaker's statement had on the discussion.
- Build a narrative conversation thread, not just a list of isolated quotes.
- For each key moment: explain (1) what prompted it, (2) what the speaker said and meant,
  (3) what happened after.
```

---

### G20 — Timestamps showing `[00:00]` — accuracy issue `[P2]`

**What we observed:**
- Our response for "What did Ngũmi say about principal repaid formula?" shows `[00:00]` for ALL 3 source chunks from 3 different meetings
- Otter.ai shows the same content at `[00:09:03]`–`[00:10:31]` in the same meeting
- Either `start_time` is being stored as `0` (ms) for these chunks, or the chunks retrieved are genuinely from the start of the meeting

**What to investigate:**
1. Run `collection.get(where={"meeting_id": {"$eq": "<M2_and_M4_id>"}}, include=["metadatas"])` and check `start_time` values
2. If `start_time=0` for most chunks → the API is not returning timing data for this meeting
3. If timing data IS present in the raw API response → check `normalize.py` to see if `start_time` is being passed through correctly

**Expected impact:** If timing data exists but isn't stored, G8 (timestamp display) gives no value. If timing is genuinely 0 for API-sourced meetings, then timestamps are a no-op for real data.

| Field | Detail |
|---|---|
| Priority | P2 |
| Effort | 0.5 day (investigation) |
| Files | `app/services/answer_service.py`, `app/services/transcript/chunking.py` |
| Status | `[x]` Done |
| Completed | 2026-05-21 |

---

### G9 — No follow-up question suggestions `[P3]`

**What Otter.ai does:**
- Ends every response with "Would you like me to..." suggestions based on the answer

**What we do:**
- Answer ends with just the answer text

**Fix:** Add optional follow-up suggestion generation as a post-processing step (only for certain intents: summary, speaker, conclusion).

| Field | Detail |
|---|---|
| Priority | P3 |
| Effort | 0.5 day |
| Files | `app/services/answer_service.py`, `app/services/prompts.py` |
| Status | `[ ]` Not started |
| Completed | — |

---

## Implementation Order (Recommended)

```
Week 1 — P1 gaps (close the most visible gap first)
  Day 0.5 G2  Speaker intent prompt rewrite (PLANNED 4 sessions ago, never coded — do this first)
  Day 1   G19 Conversation thread for speaker answers (prompt-only, quick win)
  Day 2   G1  Answer format detection + prompt format injection
  Day 3   G4  Commitment structured table output
  Day 4   G3  Compound speaker+topic two-pass retrieval

Week 2 — P2 gaps + investigation
  Day 0.5 G20 Timestamp accuracy investigation (check start_time stored in ChromaDB)
  Day 1   G5  Conclusion intent + time-sorted retrieval
  Day 2   G6  Formula intent + extraction prompt
  Day 2.5 G7  Contributor analysis in metadata queries

Week 3 — P3 gaps (polish)
  Day 1   G9  Follow-up question suggestions
  Day 1.5 G18 Limited data notice + G11 confidence signaling
```

---

## New Gaps — Add Below

> When you discover a new gap, add it here in the same format.
> Assign it a number continuing from G9 (G10, G11, ...).

---

## Section 2 — User-Friendly Output & Graceful Failure

### G10 — "Unable to answer" response is robotic and unhelpful `[P1]`

**What the current response looks like:**
```
"I couldn't find relevant information in the meeting transcripts for this project.
Make sure the project has been ingested and that the project_id is correct."
```

**Problems:**
- Blames the user ("make sure project has been ingested") even when data exists
- Same message for every failure regardless of what was asked
- No explanation of WHY it couldn't find it
- No suggestion of what to try instead

**What it should look like (example):**
```
"I wasn't able to find any discussions about 'principal repaid formula' in the
10 meetings I have for this project. This topic may not have come up in the
meetings ingested so far, or it may have been phrased differently.

You could try:
  • Asking about 'loan repayment' or 'debt schedule'
  • Requesting a summary of all meetings to see what was covered
  • Checking which meetings are available with 'list all meetings'"
```

**Fix:** Rewrite `_build_not_found_message()` in `answer_service.py` to be:
- Intent-aware (different message for DECISION vs COMMITMENT vs SPEAKER)
- Context-aware (mention the topic from the query and how many meetings were searched)
- Actionable (suggest 2–3 alternative queries the user can try)

| Field | Detail |
|---|---|
| Priority | P1 |
| Effort | 1 day |
| Files | `app/services/answer_service.py` |
| Status | `[ ]` Not started |
| Completed | — |

**Intent-specific not-found messages:**
```python
_NOT_FOUND_BY_INTENT = {
    "decision_query":    "I couldn't find any decisions or agreements about '{topic}' in this project's meetings.",
    "commitment_query":  "I couldn't find any action items or commitments related to '{topic}'.",
    "summary_query":     "I couldn't find a summary for the meeting you mentioned.",
    "speaker_query":     "I couldn't find any statements from '{speaker}' about '{topic}'.",
    "question_query":    "I couldn't find any questions raised about '{topic}' in the meetings.",
    "general_query":     "I wasn't able to find relevant information about '{topic}' in the meetings.",
}
```
Then append: number of meetings searched + 2–3 suggested rephrasing alternatives.

---

### G11 — No partial answer / low-confidence signaling `[P1]`

**What we do:**
- If we find 1–2 weak chunks, we still generate a full answer as if we're confident
- User has no idea whether the answer is backed by rich discussion or a single brief mention
- Binary: either "here's the answer" or "not found" — nothing in between

**What it should look like:**
```
"I found limited information on this topic — only 1 relevant chunk from
1 meeting. Here's what was mentioned, though it may not be the full picture:

[answer]

For more detail, you might try asking about this in a broader context."
```

**Fix:** Count retrieved chunks and source meetings before LLM call. Inject confidence framing into the prompt.

| Field | Detail |
|---|---|
| Priority | P1 |
| Effort | 0.5 day |
| Files | `app/services/answer_service.py`, `app/services/prompts.py` |
| Status | `[ ]` Not started |
| Completed | — |

**Implementation notes:**
```python
def _confidence_label(doc_count: int, meeting_count: int) -> str:
    if doc_count >= 5 and meeting_count >= 2:  return "high"
    if doc_count >= 2:                          return "medium"
    return "low"
```
Pass `confidence_label` to prompt template. When `low`, LLM prepends a caveat. When `high`, no caveat needed.

---

### G12 — Out-of-scope queries get silently mishandled `[P1]`

**What we do:**
- If user asks "what is the weather?" or "write me a poem", our pipeline runs a full RAG search, finds irrelevant chunks, and the LLM generates a hallucinated or confused answer
- No check for whether the question is related to meetings at all

**What it should do:**
```
"This question doesn't seem to be about your project meetings. I'm designed to
help you search and analyse what was discussed, decided, or committed to in your
Nolocode project meetings.

Try asking something like:
  • 'What decisions were made about the AI module?'
  • 'What did Bhavneet say in the last meeting?'
  • 'Give me a summary of all meetings'"
```

**Fix:** Add an out-of-scope pre-check in `answer_question()` before the pipeline runs.

| Field | Detail |
|---|---|
| Priority | P1 |
| Effort | 0.5 day |
| Files | `app/services/answer_service.py` |
| Status | `[ ]` Not started |
| Completed | — |

**Implementation notes:**
```python
_OUT_OF_SCOPE_RE = re.compile(
    r"\b(weather|recipe|poem|joke|translate|define|wikipedia|news|"
    r"stock price|sports|movie|song|code for me|write a|generate a)\b",
    re.IGNORECASE,
)

def _is_out_of_scope(query: str) -> bool:
    return bool(_OUT_OF_SCOPE_RE.search(query))
```
If out of scope → return a polite redirect immediately, skip the pipeline entirely.

---

### G13 — Answer never tells user how many meetings were searched `[P2]`

**What we do:**
- "What decisions were made?" → answer lists decisions, no context about scope
- User doesn't know if this covers 2 meetings or 10 meetings

**What it should include (optional footer):**
```
"[Based on 10 meetings in the Nolocode project]"
```

**Fix:** Append a one-line scope note at the end of every non-metadata answer. The project's total meeting count is already available from `get_distinct_meeting_ids()`.

| Field | Detail |
|---|---|
| Priority | P2 |
| Effort | 0.5 day |
| Files | `app/services/answer_service.py` |
| Status | `[ ]` Not started |
| Completed | — |

---

### G14 — Long answers have no TL;DR `[P2]`

**What Otter.ai does:**
- "Bottom line: The meeting's conclusion on the Save button was: we need a separate call..."
- Every long answer ends with a crisp 1–2 line summary

**What we do:**
- Answer is full length with no summary at top or bottom
- For decision/commitment/summary intents that produce long output, user must read the whole thing

**Fix:** For `summary_query`, `decision_query`, `commitment_query` — instruct the LLM to start the answer with a **1-line TL;DR** before the detailed content.

| Field | Detail |
|---|---|
| Priority | P2 |
| Effort | 0.5 day |
| Files | `app/services/prompts.py` |
| Status | `[ ]` Not started |
| Completed | — |

**Prompt addition for relevant intents:**
> "Start your answer with a single bold line: **TL;DR:** [1-sentence summary of the key finding]. Then provide the full detailed answer below."

---

### G15 — Pipeline errors surface as technical crashes, not friendly messages `[P2]`

**What we do:**
- Any exception in the pipeline raises `RuntimeError("Answer generation failed: ...")`
- The FastAPI endpoint returns HTTP 500 with the raw error string
- In Streamlit, this shows as a red crash box

**What it should look like:**
```
"I ran into a problem while searching your meetings. This is likely a
temporary issue. Please try again in a moment.

If this keeps happening, check that the project has been ingested correctly."
```

**Fix:** Catch specific error types in `answer_question()` and return structured user-friendly messages instead of raising.

| Field | Detail |
|---|---|
| Priority | P2 |
| Effort | 0.5 day |
| Files | `app/services/answer_service.py`, `main.py` |
| Status | `[ ]` Not started |
| Completed | — |

**Error type mapping:**
```python
_ERROR_MESSAGES = {
    "ChromaDB":     "I had trouble searching the meeting database. Please try again.",
    "GEMINI_API":   "The AI model is temporarily unavailable. Please try again in a moment.",
    "ValueError":   "Your question couldn't be processed. Try rephrasing it.",
    "default":      "Something went wrong. Please try again or contact support.",
}
```

---

### G16 — Ambiguous / very short queries are guessed silently `[P2]`

**What we do:**
- Query "what happened?" → pipeline guesses intent, retrieves random chunks, generates a vague answer
- User has no idea what assumption we made
- No suggestion to be more specific

**What it should do:**
```
"Your question is quite broad. I've searched for general discussion topics,
but you'll get better results if you're more specific.

For example:
  • 'What happened in the May 8th meeting?'
  • 'What happened regarding the save button?'
  • 'What happened with the principal repaid formula?'"
```

**Fix:** Detect very short or vague queries (< 5 words, no topic keywords) and either ask for clarification OR state the assumption being made before answering.

| Field | Detail |
|---|---|
| Priority | P2 |
| Effort | 0.5 day |
| Files | `app/services/answer_service.py` |
| Status | `[ ]` Not started |
| Completed | — |

**Detection:**
```python
def _is_vague_query(query: str) -> bool:
    words = [w for w in query.strip().split() if len(w) > 2]
    return len(words) < 4
```
If vague → prepend assumption note: "I'll search across all topics since your question is broad. For a more focused answer, try including a specific topic or person."

---

### G17 — No graceful handling when speaker name is not found in project `[P3]`

**What we do:**
- User asks "What did John say?" — John is not in this project
- System does a semantic search that returns irrelevant chunks
- LLM either hallucinates or says "I couldn't find John" buried in the answer

**What it should do:**
```
"I don't have a speaker named 'John' in the Nolocode project meetings.

The speakers I know about are:
  • Bhavneet Mhajan (client)
  • Ngũmi Gituro (client)
  • Project Manager SFS (project_manager)
  • [...]

Did you mean one of these?"
```

**Fix:** In `_detect_speaker_name()`, if no match found AND query contains a person-like name, return an early response listing known speakers.

| Field | Detail |
|---|---|
| Priority | P3 |
| Effort | 0.5 day |
| Files | `app/services/answer_service.py` |
| Status | `[ ]` Not started |
| Completed | — |

---

### G18 — No polite acknowledgement when query is answered from limited data `[P3]`

**What we do:**
- Answer is always stated with full confidence even if only 1 source chunk backed it

**What it should include:**
- When `sources` count = 1: "Note: This answer is based on a single mention in one meeting. It may not reflect the full picture."
- When sources are all from 1 meeting only: "Note: I only found this in one meeting — it may not be representative of the whole project."

**Fix:** Post-process `sources` list before returning. Add a `notice` field when source coverage is thin.

| Field | Detail |
|---|---|
| Priority | P3 |
| Effort | 0.5 day |
| Files | `app/services/answer_service.py` |
| Status | `[ ]` Not started |
| Completed | — |

---

## Resolved Gaps

| Gap | Description | Fixed in | Date |
|---|---|---|---|
| G8  | Timestamp references in answers | `answer_service.py`, `prompts.py` | 2026-05-21 |
| G2  | Speaker intent analysis prompt | `prompts.py` | 2026-05-21 |
| G19 | Conversation thread for speaker answers | `prompts.py` | 2026-05-21 |
| G20 | Timestamp `[00:00]` bug — double division by 1000 | `answer_service.py`, `chunking.py` | 2026-05-21 |

---

*Last reviewed: 2026-05-21*
