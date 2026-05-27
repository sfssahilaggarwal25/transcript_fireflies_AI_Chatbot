"""
goldens.py — DeepEval EvaluationDataset for the production LangGraph agent.

Structure per Golden:
  input           → the PM's exact question
  expected_output → FACT-BASED: concrete checkable statements, not rubric language.
                    Every sentence should be answerable Yes/No by the evaluator LLM.
  additional_metadata → id, category, tags for filtering

HOW TO WRITE expected_output (fact-based rules)
-----------------------------------------------
✅ DO:   "The answer states 10 meetings."             ← evaluator can check: Yes or No
✅ DO:   "The date 2026-05-07 appears in the answer." ← evaluator can check: Yes or No
✅ DO:   "No content from 2026-05-05 or earlier appears." ← scope leak check
✅ DO:   "Each commitment includes a timestamp in MM:SS format." ← format check
❌ DON'T: "The answer clearly states..."  ← vague
❌ DON'T: "The answer should include relevant details..." ← meaningless rubric
❌ DON'T: "The answer provides a good summary..." ← not checkable

HOW TO ADD A NEW GOLDEN
-----------------------
1. Copy an existing Golden block as a template.
2. Write the real PM question in `input`.
3. Write `expected_output` as a list of concrete facts separated by spaces.
   Each fact = one thing the evaluator can verify as present or absent.
4. Set a unique id and relevant tags in additional_metadata.

KNOWN FACTS (proj_nolocode_001)
-------------------------------
Total meetings : 10
Meeting #1     : 2026-03-19  Nolocode meeting with Ashpreet  (topics: forecasting, ONCA, cash flow)
Meeting #2     : 2026-03-25
Meeting #3     : 2026-04-14  (OCA issue first raised here)
Meeting #4     : 2026-04-14
Meeting #5     : 2026-04-15  (fixed assets issue first raised here)
Meeting #6     : 2026-04-20
Meeting #7     : 2026-04-22  (AI discussion, Bhavneet questions, depreciation)
Meeting #8     : 2026-04-24
Meeting #9     : 2026-05-05
Meeting #10    : 2026-05-07  ← last / most recent (depreciation, Rhythm commitments)

Signal counts (approx, regex-detected):
  contains_question     : 238 chunks
  contains_commitment   : 179 chunks
  contains_decision     :  19 chunks
  contains_open_issue   :  74 chunks
  contains_document_share:  16 chunks
  total non-summary     : 1,659 chunks
"""

from deepeval.dataset import Golden, EvaluationDataset


# ══════════════════════════════════════════════════════════════════════
# Category A — Project-Level (no scope phrase, all 10 meetings in scope)
# ══════════════════════════════════════════════════════════════════════

PROJECT_QUERIES = EvaluationDataset(
    goldens=[

        Golden(
            input="How many meetings have happened in this project?",
            expected_output=(
                "The answer states there are exactly 10 meetings. "
                "The earliest meeting date 2026-03-19 is mentioned. "
                "The latest meeting date 2026-05-07 is mentioned. "
                "The meetings are listed in chronological order. "
                "Each meeting entry includes a date in YYYY-MM-DD format."
            ),
            additional_metadata={
                "id": "A1", "category": "project",
                "tags": ["count", "meetings"],
            },
        ),

        Golden(
            input="What AI approach did we decide to go with?",
            expected_output=(
                "The answer names a specific AI approach that was decided — "
                "either hybrid search combining BM25 and dense retrieval, or another named approach. "
                "The name Harsh Vardhan appears as the person who committed to or confirmed the approach. "
                "A meeting title or number and date are referenced for when the decision was made. "
                "The answer does not say the decision was not found."
            ),
            additional_metadata={
                "id": "A2", "category": "project",
                "tags": ["decision", "AI"],
            },
        ),

        Golden(
            input="How many AI architectures were discussed across all meetings?",
            expected_output=(
                "The answer states a count that is greater than 1. "
                "At least two distinct architecture names are listed (e.g. BM25, dense vector search, "
                "hybrid search, LLM-based retrieval). "
                "The answer does not claim the count is exact — "
                "it uses language like 'about N' or lists specific named approaches it found."
            ),
            additional_metadata={
                "id": "A3", "category": "project",
                "tags": ["count", "AI", "architecture"],
            },
        ),

        Golden(
            input="How many questions about AI architecture were raised in total?",
            expected_output=(
                "The answer states a count greater than zero. "
                "The count is expressed as 'about N' or 'at least N', not as an exact number. "
                "AI architecture or a related term appears in the answer as the topic of the questions. "
                "At least one speaker name is mentioned as having raised a question."
            ),
            additional_metadata={
                "id": "A4", "category": "project",
                "tags": ["count", "AI", "question"],
            },
        ),

        Golden(
            input="Give me an overview of what Bhavneet is trying to build in this project.",
            expected_output=(
                "The name Bhavneet appears in the answer as the subject. "
                "The answer describes a product goal or vision she expressed — "
                "for example a no-code platform, financial forecasting tool, or AI-powered system. "
                "At least one meeting date or meeting number is referenced. "
                "At least one timestamp in MM:SS format is included. "
                "The answer uses attribution verbs: raised, explained, described, or wants."
            ),
            additional_metadata={
                "id": "A5", "category": "project",
                "tags": ["speaker", "vision", "Bhavneet"],
            },
        ),

        Golden(
            input="When and where did Harsh commit to using hybrid search?",
            expected_output=(
                "The name Harsh Vardhan appears as the person who committed. "
                "The term 'hybrid search' or 'hybrid' appears in the answer. "
                "A specific meeting title or meeting number is named. "
                "A date in YYYY-MM-DD format is included. "
                "A timestamp in MM:SS format is included. "
                "The answer does not say no commitment was found."
            ),
            additional_metadata={
                "id": "A6", "category": "project",
                "tags": ["commitment", "Harsh", "hybrid-search"],
            },
        ),

        Golden(
            input="List all meetings in this project with their dates.",
            expected_output=(
                "Exactly 10 meetings are listed. "
                "The date 2026-03-19 (first meeting) appears in the list. "
                "The date 2026-05-07 (last meeting) appears in the list. "
                "All dates are in YYYY-MM-DD format. "
                "The list is in chronological order from earliest to latest."
            ),
            additional_metadata={
                "id": "A7", "category": "project",
                "tags": ["meetings", "dates"],
            },
        ),

    ]
)


# ══════════════════════════════════════════════════════════════════════
# Category B — Meeting-Scoped (scope phrase in query)
# The agent must restrict results to the resolved meeting only.
# ══════════════════════════════════════════════════════════════════════

MEETING_QUERIES = EvaluationDataset(
    goldens=[

        Golden(
            input="How many people were present in the previous meeting?",
            expected_output=(
                "The answer is scoped to the date 2026-05-07 (Meeting #10). "
                "A count of speakers is stated — a positive integer. "
                "Each speaker's name and role are listed. "
                "No speaker from a meeting dated 2026-05-05 or earlier is included in the count."
            ),
            additional_metadata={
                "id": "B1", "category": "meeting",
                "tags": ["count", "attendance", "last-meeting"],
            },
        ),

        Golden(
            input="What topics were discussed in the previous meeting?",
            expected_output=(
                "The answer is scoped to Meeting #10 (2026-05-07). "
                "At least two specific topics are listed with bold or numbered headings. "
                "At least one speaker name and one timestamp in MM:SS format are included. "
                "No topics from Meeting #9 (2026-05-05) or earlier appear as if they happened in this meeting."
            ),
            additional_metadata={
                "id": "B2", "category": "meeting",
                "tags": ["summary", "last-meeting"],
            },
        ),

        Golden(
            input="Which topic was most important in the last meeting?",
            expected_output=(
                "The answer names one specific topic from Meeting #10 (2026-05-07). "
                "A reason is given for why it was most important "
                "(e.g. a decision was reached, it was a blocker, the most time was spent on it). "
                "At least one speaker name and one timestamp in MM:SS format are included. "
                "The date 2026-05-07 or the phrase 'last meeting' is referenced."
            ),
            additional_metadata={
                "id": "B3", "category": "meeting",
                "tags": ["importance", "last-meeting"],
            },
        ),

        Golden(
            input="What was the main agenda of the previous meeting?",
            expected_output=(
                "The answer is scoped to Meeting #10 (2026-05-07). "
                "At least two main discussion areas or agenda items are named. "
                "The meeting date 2026-05-07 or the phrase 'previous meeting' is referenced. "
                "No agenda items from Meeting #9 (2026-05-05) or earlier appear."
            ),
            additional_metadata={
                "id": "B4", "category": "meeting",
                "tags": ["agenda", "summary", "last-meeting"],
            },
        ),

        Golden(
            input="How many issues were raised in the previous meeting?",
            expected_output=(
                "The answer is scoped to Meeting #10 (2026-05-07). "
                "A count of issues is stated as 'about N' or 'at least N' — not as exact. "
                "The count is a positive integer greater than zero. "
                "At least one specific issue is named as an example."
            ),
            additional_metadata={
                "id": "B5", "category": "meeting",
                "tags": ["count", "issues", "last-meeting"],
            },
        ),

        Golden(
            input="Are we able to answer all the questions Bhavneet raised in the previous meeting?",
            expected_output=(
                "The answer is scoped to Meeting #10 (2026-05-07). "
                "The name Bhavneet appears as the person who raised the questions. "
                "At least one specific question she asked is named. "
                "For each question, the answer states whether it was answered or remains open. "
                "No questions from Meeting #9 or earlier are presented as part of this meeting."
            ),
            additional_metadata={
                "id": "B6", "category": "meeting",
                "tags": ["QA", "Bhavneet", "last-meeting"],
            },
        ),

        Golden(
            input="What did Bhavneet highlight in the last meeting?",
            expected_output=(
                "The answer is scoped to Meeting #10 (2026-05-07). "
                "The name Bhavneet appears as the speaker. "
                "At least two specific points she raised or highlighted are described. "
                "At least one timestamp in MM:SS format is included. "
                "Attribution verbs are used: raised, highlighted, noted, explained, or asked. "
                "No statements from Bhavneet in earlier meetings are presented as from this meeting."
            ),
            additional_metadata={
                "id": "B7", "category": "meeting",
                "tags": ["speaker", "Bhavneet", "last-meeting"],
            },
        ),

        Golden(
            input="Were any commitments made in the previous meeting?",
            expected_output=(
                "The answer begins with Yes. "
                "The answer is scoped to Meeting #10 (2026-05-07). "
                "At least one specific commitment is listed with the owner's name and what they committed to. "
                "At least one timestamp in MM:SS format is included. "
                "No commitments from Meeting #9 (2026-05-05) or earlier are included."
            ),
            additional_metadata={
                "id": "B8", "category": "meeting",
                "tags": ["commitment", "last-meeting"],
            },
        ),

        Golden(
            input="Give me a summary of the last meeting.",
            expected_output=(
                "The date 2026-05-07 or the phrase 'Meeting #10' appears in the answer. "
                "At least two specific topics discussed in that meeting are named. "
                "At least one decision or action item from that meeting is mentioned. "
                "No topics from Meeting #9 (2026-05-05) or earlier appear as if they happened in this meeting."
            ),
            additional_metadata={
                "id": "B9", "category": "meeting",
                "tags": ["summary", "last-meeting"],
            },
        ),

        Golden(
            input="What planning or next steps were discussed in the previous meeting?",
            expected_output=(
                "The answer is scoped to Meeting #10 (2026-05-07). "
                "At least one person is named as responsible for a next step. "
                "What that person will do is described. "
                "At least one timestamp in MM:SS format is included. "
                "No next steps from Meeting #9 or earlier are presented as from this meeting."
            ),
            additional_metadata={
                "id": "B10", "category": "meeting",
                "tags": ["next-steps", "planning", "last-meeting"],
            },
        ),

        Golden(
            input="What documents or files were shared in the previous meeting?",
            expected_output=(
                "The answer is scoped to Meeting #10 (2026-05-07). "
                "Either: a specific document, file, link, or spreadsheet is named with the person who shared it "
                "and a timestamp in MM:SS format. "
                "Or: the answer clearly states 'no documents were shared' in Meeting #10. "
                "Documents from Meeting #9 or earlier do not appear."
            ),
            additional_metadata={
                "id": "B11", "category": "meeting",
                "tags": ["document-share", "last-meeting"],
            },
        ),

        Golden(
            input="What feedback did Bhavneet give in the April 20th meeting?",
            expected_output=(
                "The answer is scoped to the meeting dated 2026-04-20 (Meeting #6). "
                "The name Bhavneet appears as the person giving feedback. "
                "At least one specific piece of feedback she gave is described. "
                "At least one timestamp in MM:SS format is included. "
                "No feedback from Meeting #7 (2026-04-22) or any other meeting appears."
            ),
            additional_metadata={
                "id": "B12", "category": "meeting",
                "tags": ["feedback", "Bhavneet", "april-20"],
            },
        ),

    ]
)


# ══════════════════════════════════════════════════════════════════════
# Category C — Specific Topic / Cross-Meeting
# The agent must trace a topic across multiple meetings.
# ══════════════════════════════════════════════════════════════════════

TOPIC_QUERIES = EvaluationDataset(
    goldens=[

        Golden(
            input="What was the AI discussion in the previous 2 meetings?",
            expected_output=(
                "The date 2026-05-05 (Meeting #9) appears in the answer. "
                "The date 2026-05-07 (Meeting #10) appears in the answer. "
                "AI discussion content from both meetings is presented separately. "
                "At least one speaker name and timestamp from each meeting are included. "
                "No AI discussion from Meeting #8 (2026-04-24) or earlier appears."
            ),
            additional_metadata={
                "id": "C1", "category": "topic",
                "tags": ["AI", "multi-meeting", "last-2"],
            },
        ),

        Golden(
            input="Did Harsh raise any questions about AI architecture?",
            expected_output=(
                "The answer begins with Yes or No. "
                "If Yes: the name Harsh Vardhan appears as the person who raised questions. "
                "If Yes: at least one specific question about AI architecture is stated. "
                "If Yes: a meeting name or number and a timestamp in MM:SS format are included. "
                "If No: the answer states clearly that no such questions were found in the transcripts."
            ),
            additional_metadata={
                "id": "C2", "category": "topic",
                "tags": ["AI", "question", "Harsh"],
            },
        ),

        Golden(
            input="Summarize the overall AI architecture conversation across all meetings.",
            expected_output=(
                "At least three different meeting dates are referenced. "
                "The answer names at least two distinct AI approaches or architecture options discussed. "
                "A final decision or chosen approach is stated. "
                "At least one speaker name is attributed to a key development or decision. "
                "The answer is organised by theme or decision point, not just by meeting."
            ),
            additional_metadata={
                "id": "C3", "category": "topic",
                "tags": ["AI", "architecture", "cross-meeting"],
            },
        ),

        Golden(
            input="What did Harsh commit to regarding AI in the last 5 meetings?",
            expected_output=(
                "The answer covers meetings from 2026-04-20 (Meeting #6) to 2026-05-07 (Meeting #10). "
                "The name Harsh Vardhan appears as the person making commitments. "
                "At least one specific AI-related commitment is stated. "
                "Each commitment includes a meeting date or number and a timestamp in MM:SS format. "
                "No commitments from Meeting #5 (2026-04-15) or earlier are included."
            ),
            additional_metadata={
                "id": "C4", "category": "topic",
                "tags": ["AI", "commitment", "Harsh", "last-5"],
            },
        ),

        Golden(
            input="What clarity did Bhavneet provide about the AI system?",
            expected_output=(
                "The name Bhavneet appears as the speaker providing clarification. "
                "At least one specific explanation or clarification about the AI system is described. "
                "A meeting name or number is referenced. "
                "At least one timestamp in MM:SS format is included. "
                "Attribution verbs are used: explained, clarified, described, or stated."
            ),
            additional_metadata={
                "id": "C5", "category": "topic",
                "tags": ["AI", "clarity", "Bhavneet"],
            },
        ),

        Golden(
            input="Summarize the complete AI architecture discussion in this project.",
            expected_output=(
                "More than three different meeting dates or numbers are referenced. "
                "At least two distinct AI architecture approaches are named. "
                "A final decision or chosen approach is mentioned. "
                "The answer is organised by themes or key decisions, not just listing meetings. "
                "Speaker names with timestamps appear for key statements."
            ),
            additional_metadata={
                "id": "C6", "category": "topic",
                "tags": ["AI", "architecture", "summary", "cross-meeting"],
            },
        ),

        Golden(
            input="What is the exact approach we decided for building the AI system?",
            expected_output=(
                "The answer names a specific technical approach — "
                "for example hybrid search, BM25 combined with dense retrieval, or a named architecture. "
                "A person who confirmed or decided the approach is named. "
                "A meeting number or date is referenced for when the decision was made. "
                "The answer does not say 'no decision was found' or 'I could not find'."
            ),
            additional_metadata={
                "id": "C7", "category": "topic",
                "tags": ["AI", "decision", "approach"],
            },
        ),

        Golden(
            input="Which issue came up first — OCA or fixed assets?",
            expected_output=(
                "The answer states that OCA came first. "
                "The date 2026-04-14 (Meeting #3) is referenced for OCA. "
                "The date 2026-04-15 (Meeting #5) is referenced for fixed assets. "
                "A speaker name and timestamp in MM:SS format are given for each issue. "
                "The answer explains that April 14 is earlier than April 15."
            ),
            additional_metadata={
                "id": "C8", "category": "topic",
                "tags": ["chronological", "comparison", "OCA", "fixed-assets"],
            },
        ),

        Golden(
            input="Which unresolved issue was discussed most recently?",
            expected_output=(
                "The answer names one specific unresolved issue. "
                "A meeting date is given — it must be the latest date among meetings that had open issues. "
                "A speaker name and timestamp in MM:SS format are included. "
                "The answer does not list multiple issues as equally 'most recent'."
            ),
            additional_metadata={
                "id": "C9", "category": "topic",
                "tags": ["open-issue", "chronological", "last"],
            },
        ),

        Golden(
            input="Who has spoken the most in this project?",
            expected_output=(
                "The answer names the most active speaker first. "
                "A chunk count or segment count is given for at least the top speaker. "
                "At least three speakers are listed with their names and roles. "
                "Counts are expressed as numbers (e.g. 47 chunks or 47 segments). "
                "The list is ordered from most to least active."
            ),
            additional_metadata={
                "id": "C10", "category": "topic",
                "tags": ["speaker", "contribution", "ranking"],
            },
        ),

        Golden(
            input="Summarize all commitments made by Simarjot Kaur with timestamps.",
            expected_output=(
                "The name Simarjot Kaur appears in the answer. "
                "Either: at least one commitment she made is listed with a meeting name, date, "
                "and timestamp in MM:SS format. "
                "Or: the answer clearly states no commitments by Simarjot Kaur were found "
                "and does not invent commitments. "
                "Attribution verbs are used: committed to, will do, agreed to, or responsible for."
            ),
            additional_metadata={
                "id": "C11", "category": "topic",
                "tags": ["commitment", "Simarjot", "traces"],
            },
        ),

    ]
)


# ══════════════════════════════════════════════════════════════════════
# ALL_QUERIES — combined dataset (A + B + C)
# Use this for a full test run across all categories.
# ══════════════════════════════════════════════════════════════════════

ALL_QUERIES = EvaluationDataset(
    goldens=(
        PROJECT_QUERIES.goldens
        + MEETING_QUERIES.goldens
        + TOPIC_QUERIES.goldens
    )
)
