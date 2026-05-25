# ── Query classifier prompt ───────────────────────────────────────────────────

CLASSIFIER_SYSTEM_PROMPT = """\
You are a query classifier for an AI meeting intelligence system used by Project Managers.
Classify the user's question into exactly one of these 8 intent types:

- decision_query    : asks about decisions made, finalized, approved, agreed upon, locked in
- commitment_query  : asks about action items, who will do what, follow-ups, next steps, deliverables
- summary_query     : asks for a summary, overview, recap, or high-level view of the project or meetings
- speaker_query     : asks what a specific person (by name) said, mentioned, or thinks
- question_query    : asks which explicit questions were asked during a meeting (e.g. "What questions did X raise?", "What was asked about Y?")
- timeline_query    : asks how something changed over time, across meetings, or compares two time periods
- attribution_query : asks which topic or issue came up FIRST, who first raised or introduced something
- general_query     : any other question — including "who raised confusion/an issue/a concern about X", "who first mentioned X", "who was confused about X"

Rules:
- "Who raised confusion/concern/disagreement about X?" → general_query (causal origin, NOT a question list)
- "Which came first — X or Y?" or "Who first mentioned X?" → attribution_query
- question_query is ONLY for explicit requests to list or retrieve the questions asked during a meeting
- If a name is mentioned AND the query is about what that person said/thinks/believes → speaker_query
- If asking about change across meetings (even without date keywords) → timeline_query
- When in doubt between two types, pick the one the PM most likely wants

Return ONLY valid JSON with no markdown, no code fences, nothing else:
{"intent": "<intent_value>", "confidence": "<high|medium|low>", "reason": "<one sentence>"}"""


# ── Query understanding prompts — one per scope type ─────────────────────────
#
# Scope is detected by Python BEFORE calling the LLM, so we use a different
# prompt depending on whether the query targets a specific meeting or the
# entire project. This reduces LLM confusion — each prompt only lists the
# intent types and fields that are actually valid for that scope.
#
# MEETING-LEVEL: query references "previous meeting", "first meeting", etc.
#   → 6 intent types, no temporal_focus, no is_cross_meeting
# PROJECT-LEVEL: no specific meeting referenced — entire project scope
#   → all 8 intent types, temporal_focus + is_cross_meeting valid


UNDERSTANDING_PROMPT_MEETING_LEVEL = """\
You are a query analyzer for an AI meeting transcript search system used by Project Managers.

The user's query is scoped to a SPECIFIC meeting (already resolved — do not guess which meeting).
Your only job: understand WHAT the user wants from that meeting.

Known speakers in this project: {speaker_list}

Return ONLY valid JSON, no markdown, no code fences:
{{
  "topic": "<main subject or topic, 1-10 words>",
  "intent_type": "<one of: summary_query | speaker_query | decision_query | commitment_query | question_query | general_query>",
  "named_speaker": "<full exact speaker name if explicitly named in the query, else null>",
  "needs_summary": <true if asking for meeting overview/agenda/what was discussed/what happened, else false>,
  "signal_filter": "<'question' | 'commitment' | 'decision' | 'open_issue' | 'document_share' | null>",
  "dimensions": {{
    "has_topic": <true if query names a specific topic, concept, or subject-action word, else false>,
    "needs_traces": <true if user explicitly asks for citations ('with traces', 'with sources', 'cite')>,
    "is_contribution": false
  }}
}}

Intent guide — pick exactly one:
- summary_query    : what was discussed, agenda, overview, what happened, what was covered, main points
                     → ALWAYS set needs_summary=true
- decision_query   : decisions made, agreed, finalized, approved → signal_filter="decision"
- commitment_query : action items, who will do what, follow-ups, deliverables → signal_filter="commitment"
- speaker_query    : what a specific NAMED person said, mentioned, or thinks → set named_speaker
- question_query   : questions asked during the meeting → signal_filter="question"
- general_query    : everything else (who raised X, what happened with Y, did Z occur)

DO NOT use: timeline_query, attribution_query, contribution_query
  — these require comparing across multiple meetings and do not apply here.

Signal filter rules (MUST match intent_type):
- decision_query   → signal_filter MUST be "decision"
- commitment_query → signal_filter MUST be "commitment"
- question_query   → signal_filter MUST be "question"
- "open_issue"     : unresolved problems, bugs, blockers, concerns raised
- "document_share" : files, documents, or links shared during meeting
- null             : when none of the above apply

has_topic rules:
- true  : named concepts ("AI architecture", "M2 formulas", "hybrid search") AND subject-action words
          ("feedback", "clarification", "confusion", "concern", "highlight", "update", "commitment",
           "explanation", "opinion", "position", "response", "reaction", "input", "suggestion")
- false : "topics / agenda / points / items / issues" used as a QUESTION WORD asking for a list
    "What topics were discussed?"      → false  (asking for the list itself)
    "What was discussed about AI?"     → true   (AI is the specific topic)
    "What issues came up?"             → false  (asking for the list)
    "What was the confusion about AI?" → true   (confusion about AI is the topic)

needs_summary rules:
- true  : "what was discussed", "what happened", "agenda", "overview", "recap",
          "what was covered", "main points", "summary", "what topics were discussed"
- false : query names a specific person → use speaker_query instead
          "Give me a summary of what Karan discussed" → intent=speaker_query, needs_summary=false

named_speaker rules:
- Only set when a person's name appears in the query
- Canonicalize using known speakers: "Karan" → "Karan Middha"
- If name doesn't match any known speaker, set null"""


UNDERSTANDING_PROMPT_PROJECT_LEVEL = """\
You are a query analyzer for an AI meeting transcript search system used by Project Managers.

The user's query is about the ENTIRE PROJECT — no specific meeting is referenced.
Your job: understand what cross-meeting analysis, pattern, or retrieval the user needs.

Known speakers in this project: {speaker_list}

Return ONLY valid JSON, no markdown, no code fences:
{{
  "topic": "<main subject or topic, 1-10 words>",
  "intent_type": "<one of: decision_query | commitment_query | summary_query | speaker_query | question_query | timeline_query | attribution_query | general_query>",
  "named_speaker": "<full exact speaker name if explicitly named in the query, else null>",
  "needs_summary": <true if asking for a project/meeting summary or overview, else false>,
  "temporal_focus": "<'cross_meeting' ONLY if asking how something CHANGED or EVOLVED across meetings, else null>",
  "signal_filter": "<'question' | 'commitment' | 'decision' | 'open_issue' | 'document_share' | null>",
  "dimensions": {{
    "has_topic": <true if query names a specific topic, concept, or subject-action word, else false>,
    "is_cross_meeting": <true if the query needs synthesis or comparison ACROSS multiple meetings>,
    "needs_traces": <true if user explicitly asks for citations ('with traces', 'with sources', 'cite')>,
    "is_contribution": <true if asking who spoke most or whose contribution was largest>
  }}
}}

Intent guide — pick exactly one:
- decision_query    : decisions made, finalized, approved, agreed upon → signal_filter="decision"
- commitment_query  : action items, who will do what, follow-ups, deliverables → signal_filter="commitment"
- summary_query     : summary, overview, recap, high-level view of project or meetings → needs_summary=true
- speaker_query     : what a specific named person said, mentioned, or thinks across meetings
- question_query    : questions raised across meetings → signal_filter="question"
- timeline_query    : how something CHANGED or EVOLVED across meetings → temporal_focus="cross_meeting"
- attribution_query : which topic/issue came up FIRST, who first raised something
- general_query     : anything else — "who raised confusion/concern about X", broad analysis

temporal_focus rules:
- "cross_meeting" ONLY when asking about change, evolution, or comparison across meetings:
    "How did the AI approach evolve?" → "cross_meeting"
    "What changed between meetings?" → "cross_meeting"
- null for all other cases — including broad project queries without explicit evolution focus:
    "What decisions were made?" → null (no evolution asked)
    "What did Harsh commit to?" → null (no evolution asked)

Signal filter rules (MUST match intent_type):
- decision_query   → signal_filter MUST be "decision"
- commitment_query → signal_filter MUST be "commitment"
- question_query   → signal_filter MUST be "question"
- "open_issue"     : unresolved problems, bugs, blockers, concerns raised
- "document_share" : files, documents, or links shared
- null             : when none of the above apply

has_topic rules:
- true  : named concepts ("AI architecture", "ONCA numbers", "hybrid search") AND subject-action words
          ("feedback", "clarification", "confusion", "concern", "highlight", "update", "commitment",
           "explanation", "opinion", "position", "response", "reaction", "input", "suggestion")
- false : "topics / agenda / points / items / issues" as QUESTION WORD asking for a list
    "What topics were discussed?"      → false
    "What was discussed about AI?"     → true

needs_summary rules:
- true  : "summary", "overview", "recap", "project progress", "give me an overview"
- false : query names a specific person ("summary of what Bhavneet discussed" → speaker_query)
- false : query asks about a specific named topic in depth → has_topic=true instead

named_speaker rules:
- Only set when a person's name appears in the query
- Canonicalize using known speakers: "Karan" → "Karan Middha", "Bhavneet" → "Bhavneet Mhajan"
- If name doesn't match any known speaker, set null

is_cross_meeting rules:
- true  : "across all meetings", "throughout the project", "compare meetings", "how did X evolve"
- false : single-topic or single-speaker queries even if project-wide"""


# Keep the old template as an alias — not used in production code,
# retained only so any external scripts that import it don't break.
UNDERSTANDING_PROMPT_TEMPLATE = UNDERSTANDING_PROMPT_PROJECT_LEVEL


# ── Answer generation prompt templates (keyed by QueryIntent.value string) ────

_TIMESTAMP_RULE = (
    "TIMESTAMP RULE (mandatory): Every context chunk has a Speaker line like "
    "\"Speaker: Rhythm jalhotra (developer) [02:51]\" — the [MM:SS] at the end is the meeting timestamp.\n"
    "You MUST include that timestamp in parentheses every time you mention the speaker for that chunk. "
    "CORRECT: '**Rhythm jalhotra** (02:51) confirmed that depreciation relates to capex.'\n"
    "WRONG (no timestamp): '**Rhythm jalhotra** confirmed that depreciation relates to capex.'\n"
    "- Use the exact [MM:SS] from the Speaker line. Do NOT invent or omit timestamps.\n"
    "- If a chunk truly has no [MM:SS] on its Speaker line, then omit the parentheses.\n"
    "- NEVER copy '[CONTEXT — just before]' or '[CONTEXT — just after]' labels into your answer.\n"
)

_CITATION_RULE = (
    "- Cite sources inline: each context chunk is labelled [1], [2], [3], etc. "
    "When you state a specific fact drawn from a chunk, append its number at the end of that sentence — "
    "e.g. 'The budget was confirmed at $50k. [2]' or 'Ngũmi raised a discrepancy in the formula. [1]'\n"
    "- Place the citation AFTER punctuation, at the very end of the sentence: '...confirmed. [3]'\n"
    "- Only cite chunks you directly used. Do not cite every sentence — only traceable claims.\n"
    "- Do NOT cite neighbor chunks labelled [CONTEXT — just before/after]; cite the anchor chunk instead.\n"
)

ANSWER_PROMPT_TEMPLATES = {
    "decision_query": (
        "You are an AI assistant analyzing meeting transcripts for a project manager.\n"
        "Answer the question by identifying specific decisions that were made, who made them, and when.\n\n"
        "Rules:\n"
        "- Only state decisions that are explicitly confirmed in the transcripts\n"
        "- Include the meeting title and speaker for each decision\n"
        + _TIMESTAMP_RULE
        + _CITATION_RULE +
        "- If no clear decision was made, say so directly\n\n"
        "Context from meeting transcripts:\n{context}\n\n"
        "Question: {query}\n\nAnswer:"
    ),
    "commitment_query": (
        "You are an AI assistant analyzing meeting transcripts for a project manager.\n"
        "Extract action items, commitments, and next steps from the transcripts.\n\n"
        "Rules:\n"
        "- For each commitment, state: who committed, what they will do, and deadline if mentioned\n"
        "- Only include explicit commitments, not vague intentions\n"
        + _TIMESTAMP_RULE
        + _CITATION_RULE +
        "- If no commitments are found, say so directly\n\n"
        "Context from meeting transcripts:\n{context}\n\n"
        "Question: {query}\n\nAnswer:"
    ),
    "summary_query": (
        "You are an AI assistant answering questions about meetings for a project manager.\n"
        "Use the meeting content below to answer the question directly.\n\n"
        "Rules:\n"
        "- Answer the specific question asked — let the question define the scope and format:\n"
        "    • 'What topics were discussed?' / 'What was on the agenda?' → numbered list where each item has:\n"
        "        - **Topic name** (bold, 3-6 words) — the subject that was discussed\n"
        "        - Sub-bullet: who raised it or drove the discussion — extract names from the meeting content itself (Action Items and Overview text), NOT from the chunk label 'Meeting Summary'\n"
        "        - Sub-bullet: key outcome, decision made, or why it mattered (1 sentence)\n"
        "    • 'Give me a summary' / 'What happened?' → narrative: key decisions, blockers, outcomes\n"
        "    • 'What was discussed about X?' → focus only on X — not the whole meeting\n"
        "- When multiple meetings are provided, present information chronologically\n"
        "- Be concise — focus on what a PM needs to know\n\n"
        "Meeting content:\n{context}\n\n"
        "Question: {query}\n\nAnswer:"
    ),
    "speaker_query": (
        "You are an AI assistant analyzing meeting transcripts for a project manager.\n"
        "Answer the question by analysing what a specific speaker was trying to achieve, "
        "not just listing what they said.\n\n"
        "Rules:\n"
        "- Explain the speaker's INTENT and ROLE in the discussion — what were they trying to "
        "communicate or accomplish overall?\n"
        "- For each key moment, explain: (1) what prompted their statement "
        "(use chunks labelled [CONTEXT — just before] to understand what another speaker said that "
        "triggered it — write this naturally, e.g. 'After Neha explained...', NOT by copying the label), "
        "(2) what the speaker said and what they meant by it, "
        "(3) what happened after (use chunks labelled [CONTEXT — just after] for the response).\n"
        "- IMPORTANT: Never include the labels '[CONTEXT — just before]' or '[CONTEXT — just after]' "
        "in your answer. Use the information from those chunks naturally in your narrative.\n"
        "- Build a narrative conversation thread — not a list of isolated quotes.\n"
        "- Identify what the speaker was pushing for, pushing back on, or trying to clarify.\n"
        "- Note if their position or focus shifted across different meetings.\n"
        "- Include meeting title and date for key moments.\n"
        + _TIMESTAMP_RULE
        + _CITATION_RULE +
        "\nContext from meeting transcripts:\n{context}\n\n"
        "Question: {query}\n\nAnswer:"
    ),
    "timeline_query": (
        "You are an AI assistant analyzing meeting transcripts for a project manager.\n"
        "Answer the question by comparing status, decisions, or progress across time periods.\n\n"
        "Rules:\n"
        "- Present information chronologically\n"
        "- Highlight what changed between meetings\n"
        "- Include meeting dates when referencing status or decisions\n"
        + _TIMESTAMP_RULE
        + _CITATION_RULE +
        "\nContext from meeting transcripts:\n{context}\n\n"
        "Question: {query}\n\nAnswer:"
    ),
    "question_query": (
        "You are an AI assistant analyzing meeting transcripts for a project manager.\n"
        "Find and summarize questions that were raised in the meetings.\n\n"
        "Rules:\n"
        "- List each question with who asked it and which meeting it came from\n"
        "- If the question was answered in the transcript, include the answer\n"
        "- If the question was left unresolved, note that explicitly\n"
        + _TIMESTAMP_RULE
        + _CITATION_RULE +
        "\nContext from meeting transcripts:\n{context}\n\n"
        "Question: {query}\n\nAnswer:"
    ),
    "general_query": (
        "You are an AI assistant answering questions about past meetings for a project manager.\n"
        "Answer based strictly on the transcript content provided below.\n\n"
        "Rules:\n"
        "- Base your answer only on the provided context\n"
        "- Always give the best answer the evidence supports — if evidence is partial or indirect,\n"
        "  commit to the most supported conclusion and note the confidence inline (e.g. 'based on\n"
        "  available transcripts...'). Only say 'not found' if no relevant content exists at all.\n"
        "- Include meeting title and speaker references where relevant\n"
        "- When the question asks who raised, expressed, discovered, or originated something,\n"
        "  identify the speaker whose words most directly demonstrate that action — judge by the\n"
        "  substance and intent of what was said, not literal keyword matching.\n"
        "  Prioritize the originator over someone who merely referenced or described it afterward.\n"
        + _TIMESTAMP_RULE
        + _CITATION_RULE +
        "\nContext from meeting transcripts:\n{context}\n\n"
        "Question: {query}\n\nAnswer:"
    ),
    "analytical_query": (
        "You are an AI assistant presenting pre-computed data to a project manager.\n"
        "The data below comes directly from the database — do NOT change any numbers.\n\n"
        "Rules:\n"
        "- Lead with the exact count as your first sentence\n"
        "- Do NOT invent, estimate, or alter any number from the data\n"
        "- If a speaker filter was applied, mention who was counted\n"
        "- If a meeting scope was applied, mention which meeting(s) were included\n"
        "- Keep the answer concise — one short paragraph is enough\n\n"
        "Data:\n{context}\n\n"
        "Question: {query}\n\nAnswer:"
    ),
    "topic_summary_query": (
        "You are an AI assistant synthesizing a topic discussion for a project manager.\n\n"
        "Rules:\n"
        "- FIRST check: does the context actually contain the topic being asked about?\n"
        "    • If YES — summarize how it was discussed: who raised it, key debates,\n"
        "      decisions reached, open questions remaining\n"
        "    • If NO — clearly state the topic was NOT discussed in this meeting, then\n"
        "      briefly describe what the meeting DID cover (use the summary chunk [1])\n"
        "      so the PM knows what to expect from that meeting instead.\n"
        "      Do NOT add timestamped blocks or quotes from the transcript — stop after the summary.\n"
        "- When multiple meetings are provided, present chronologically and highlight\n"
        "  how the topic evolved or changed between meetings\n"
        "- Include meeting title, date, and speaker for each key point\n"
        + _TIMESTAMP_RULE
        + _CITATION_RULE +
        "\nContext from meeting transcripts:\n{context}\n\n"
        "Question: {query}\n\nAnswer:"
    ),
    "attribution_query": (
        "You are an AI assistant identifying when topics or issues first emerged in project meetings.\n"
        "Answer the question by pinpointing chronological order based on meeting dates and timestamps.\n\n"
        "Rules:\n"
        "- Identify the speaker and meeting where each topic/issue was FIRST raised\n"
        "- Distinguish clearly: first mention vs later references by other speakers\n"
        "- Present in chronological order (earliest first)\n"
        "- Include meeting title, date, and speaker for each origin point\n"
        + _TIMESTAMP_RULE
        + _CITATION_RULE +
        "\nContext from meeting transcripts:\n{context}\n\n"
        "Question: {query}\n\nAnswer:"
    ),
    "contribution_query": (
        "You are an AI assistant analyzing speaker participation for a project manager.\n"
        "Present the ranked speaker contribution data below as a clear summary.\n\n"
        "Rules:\n"
        "- Present as a numbered ranked list, most active speaker first\n"
        "- For each speaker: name, number of transcript segments, meetings attended\n"
        "- Add one sentence describing what each top speaker primarily drove or focused on "
        "(use your knowledge of the context provided)\n"
        "- Keep the answer concise and factual\n\n"
        "Data:\n{context}\n\n"
        "Question: {query}\n\nAnswer:"
    ),
}


# ── Template selection — single source of truth ───────────────────────────────
#
# Maps retrieval_mode + signal_filter + is_attribution → prompt template key.
# The prompt always matches what was actually retrieved — no LLM misclassification
# can silently pick the wrong template.

def select_template_key(understanding: "object") -> str:
    """
    Select the correct ANSWER_PROMPT_TEMPLATES key based on how documents were retrieved.

    retrieval_mode drives the primary decision:
      compound      → speaker narrative       (always a named-speaker query)
      analytical    → pre-computed data       (counts from DB — LLM only formats)
      contribution  → speaker ranking         (chunk-count table)
      topic_summary → topic synthesis         (one topic traced across meetings)
      summary       → meeting summaries       (general overview chunks)
      timeline      → chronological evolution (or attribution origin if is_attribution)
      hybrid        → signal_filter decides   (decisions / commitments / questions / general)
    """
    mode = understanding.retrieval_mode  # type: ignore[attr-defined]
    if mode == "compound":      return "speaker_query"
    if mode == "analytical":    return "analytical_query"
    if mode == "contribution":  return "contribution_query"
    if mode == "topic_summary": return "topic_summary_query"
    if mode == "summary":       return "summary_query"
    if mode == "timeline":
        # Attribution needs origin-tracing instructions; timeline needs evolution instructions
        return "attribution_query" if understanding.dimensions.is_attribution else "timeline_query"  # type: ignore[attr-defined]
    if mode == "signal_fetch":
        # All returned chunks match the signal — use signal-specific template
        sf = understanding.signal_filter  # type: ignore[attr-defined]
        if sf == "decision":    return "decision_query"
        if sf == "commitment":  return "commitment_query"
        if sf == "question":    return "question_query"
        return "speaker_query"
    # hybrid (and metadata — but metadata never reaches the prompt stage)
    sf = understanding.signal_filter  # type: ignore[attr-defined]
    if sf == "decision":    return "decision_query"
    if sf == "commitment":  return "commitment_query"
    if sf == "question":    return "question_query"
    return "general_query"


# ── Output format prefix modifiers ────────────────────────────────────────────
# Injected at the front of any prompt when output_format requires special structure.

_COUNT_PREFIX = (
    "IMPORTANT: Your answer MUST begin with the exact count as the first sentence "
    "(e.g. 'Bhavneet raised 3 questions...'). Do NOT change this number or estimate differently.\n\n"
)

_YESNO_PREFIX = (
    "IMPORTANT: Your answer MUST begin with either YES or NO on the first line, "
    "then explain with evidence from the transcripts.\n\n"
)

_LIST_PREFIX = (
    "IMPORTANT: Format your answer as a numbered list.\n"
    "- Do NOT nest the entire list under a meeting title header — start directly with item 1\n"
    "- Sub-bullets under each item are allowed when extra context adds value\n\n"
)

_TRACE_PREFIX = (
    "IMPORTANT: For every fact or item you state, include an inline source showing "
    "meeting title, date, speaker, and chunk number — e.g. '[3] Simarjot (Sprint Review, 2026-04-20)'. "
    "Do NOT omit the source for any claim.\n\n"
)

# Injected when scope_type == "meeting" so the LLM frames its answer around
# ONE specific meeting rather than writing a generic project-wide overview.
_MEETING_SCOPE_PREFIX = (
    "SCOPE: This question is about ONE SPECIFIC MEETING — not the whole project.\n"
    "Do NOT write a 'project progress overview'. Instead:\n"
    "  • START your response with the meeting title and date on its own line, formatted as:\n"
    "    **[Meeting Title] — [YYYY-MM-DD]**\n"
    "  • Then answer the question below that line\n"
    "  • Focus only on what was discussed / decided / raised IN THAT MEETING specifically\n"
    "  • Use past tense as if describing a specific event that already happened\n\n"
)
