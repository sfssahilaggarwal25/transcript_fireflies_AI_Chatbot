"""
goldens.py — DeepEval EvaluationDataset for the production LangGraph agent.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GOLDEN STRUCTURE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  input             → the PM's exact question
  expected_output   → FACT-BASED: every sentence must be answerable Yes/No
                      by the evaluator LLM. No vague rubric language.
  additional_metadata → structured fields for filtering + debugging

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
METADATA SCHEMA  (every field explained)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  id            Unique string. Used with --ids flag to run specific goldens.
                Format: "A1", "B8", "C3" etc.

  scope         What portion of the project the agent should search.
                  "project"       → all 10 meetings in scope
                  "meeting"       → scoped to one specific meeting
                  "multi-meeting" → scoped to N recent meetings (e.g. last 2)

  meeting_date  ISO date (YYYY-MM-DD) of the target meeting.
                null for project-scoped and multi-meeting queries.

  query_type    Shape of the expected answer. Used with --query-type flag.
                  "count"       → expects a number ("how many X?")
                  "yesno"       → expects Yes/No as first word
                  "list"        → expects a list of items
                  "summary"     → expects an overview paragraph
                  "attribution" → expects specific speaker + what they said/did
                  "comparison"  → expects a comparison between two things

  signal        The signal type the query targets. null if not signal-specific.
                  "commitment" | "decision" | "question"
                  "open_issue" | "document_share" | null
                Used with --signal flag to run all queries of one signal type.

  speaker       Exact stored speaker name if named in the query. null otherwise.
                Must match the name in ChromaDB exactly — use verify_chunks
                speakers command to confirm before setting this field.
                Used with --speaker flag.

  expected_tool The primary tool the agent MUST call to answer this query.
                  "search_transcripts" | "get_meeting_summaries"
                  "list_meetings" | "list_speakers" | "count_signal_chunks"
                Documentation only — not auto-asserted, but useful for debugging.
                If the agent called a different tool and still answered correctly,
                check if the tool routing logic needs tightening.

  known_gap     True if this golden is EXPECTED to fail right now due to a known
                agent bug or retrieval gap. Used with --skip-gaps flag to get a
                clean baseline run excluding known failures.
                False for all goldens that should currently pass.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
KNOWN FACTS (proj_nolocode_001)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Total meetings : 10

  #   Date         Title                         Chunks  commit  dec  quest  issue  doc
  1   2026-03-19   Nolocode meeting with Ashpreet   191      18    2     45      4    4
  2   2026-03-25   Nolocode AI meeting              211      33    4     59      6    2
  9   2026-04-14   Nolocode-M1                      155      23    1     34     15    1
  10  2026-04-14   Nolocode-AWS-deployment          127      10    0     17      8    1
  8   2026-04-15   Nolocode-M2-and-M4               257      38    3     79     12    5
  7   2026-04-20   Nolocode-catchup                 176      47    4     28     10    0
  6   2026-04-22   Nolocode-AI-meeting               45      13    0     21      0    0
  3   2026-04-24   Nolocode-M2-formula-discussion   240      42    1     65      7    1
  5   2026-05-05   Nolocode-meeting                  53      10    0      7      3    2
  4   2026-05-07   Nolocode-meeting (LAST)          204      44    5     28      9    0

  Known speakers (exact stored names):
    "Bhavneet Mhajan"        [client]
    "Rhythm jalhotra"        [developer]
    "Karan Middha"           [developer]
    "Project Manager SFS"    [project_manager]
    "Nolocode AI"            [developer]
    "Simarjot Kaur"          [developer]   ← verify existence with verify_chunks
    "Harsh Vardhan"          [developer]   ← verify exact name with verify_chunks
"""

from deepeval.dataset import Golden, EvaluationDataset


# ══════════════════════════════════════════════════════════════════════
# Category A — Project-Level
# No scope phrase in query → all 10 meetings in scope.
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
                "id":            "proj_count_meetings",
                "scope":         "project",
                "meeting_date":  None,
                "query_type":    "count",
                "signal":        None,
                "speaker":       None,
                "expected_tool": "list_meetings",
                "known_gap":     True,   # agent returned empty — list_meetings not firing
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
                "id":            "proj_decision_ai_approach",
                "scope":         "project",
                "meeting_date":  None,
                "query_type":    "attribution",
                "signal":        "decision",
                "speaker":       None,
                "expected_tool": "search_transcripts",
                "known_gap":     False,
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
                "id":            "proj_count_ai_architectures",
                "scope":         "project",
                "meeting_date":  None,
                "query_type":    "count",
                "signal":        None,
                "speaker":       None,
                "expected_tool": "search_transcripts",
                "known_gap":     False,
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
                "id":            "proj_count_ai_questions",
                "scope":         "project",
                "meeting_date":  None,
                "query_type":    "count",
                "signal":        "question",
                "speaker":       None,
                "expected_tool": "count_signal_chunks",
                "known_gap":     False,
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
                "id":            "proj_summary_bhavneet_vision",
                "scope":         "project",
                "meeting_date":  None,
                "query_type":    "summary",
                "signal":        None,
                "speaker":       "Bhavneet Mhajan",
                "expected_tool": "search_transcripts",
                "known_gap":     False,
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
                "id":            "proj_commit_harsh_hybrid_search",
                "scope":         "project",
                "meeting_date":  None,
                "query_type":    "attribution",
                "signal":        "commitment",
                "speaker":       "Harsh Vardhan",
                "expected_tool": "search_transcripts",
                "known_gap":     False,
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
                "id":            "proj_list_all_meetings",
                "scope":         "project",
                "meeting_date":  None,
                "query_type":    "list",
                "signal":        None,
                "speaker":       None,
                "expected_tool": "list_meetings",
                "known_gap":     True,   # same root cause as proj_count_meetings
            },
        ),

    ]
)


# ══════════════════════════════════════════════════════════════════════
# Category B — Meeting-Scoped
# Scope phrase in query → agent must restrict to that one meeting.
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
                "id":            "meet_count_attendance_last",
                "scope":         "meeting",
                "meeting_date":  "2026-05-07",
                "query_type":    "count",
                "signal":        None,
                "speaker":       None,
                "expected_tool": "list_speakers",
                "known_gap":     False,
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
                "id":            "meet_list_topics_last",
                "scope":         "meeting",
                "meeting_date":  "2026-05-07",
                "query_type":    "list",
                "signal":        None,
                "speaker":       None,
                "expected_tool": "get_meeting_summaries",
                "known_gap":     False,
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
                "id":            "meet_attr_topic_importance_last",
                "scope":         "meeting",
                "meeting_date":  "2026-05-07",
                "query_type":    "attribution",
                "signal":        None,
                "speaker":       None,
                "expected_tool": "get_meeting_summaries",
                "known_gap":     False,
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
                "id":            "meet_summary_agenda_last",
                "scope":         "meeting",
                "meeting_date":  "2026-05-07",
                "query_type":    "summary",
                "signal":        None,
                "speaker":       None,
                "expected_tool": "get_meeting_summaries",
                "known_gap":     False,
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
                "id":            "meet_count_issues_last",
                "scope":         "meeting",
                "meeting_date":  "2026-05-07",
                "query_type":    "count",
                "signal":        "open_issue",
                "speaker":       None,
                "expected_tool": "count_signal_chunks",
                "known_gap":     False,
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
                "id":            "meet_yesno_bhavneet_questions_last",
                "scope":         "meeting",
                "meeting_date":  "2026-05-07",
                "query_type":    "yesno",
                "signal":        "question",
                "speaker":       "Bhavneet Mhajan",
                "expected_tool": "search_transcripts",
                "known_gap":     False,
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
                "id":            "meet_attr_bhavneet_highlights_last",
                "scope":         "meeting",
                "meeting_date":  "2026-05-07",
                "query_type":    "attribution",
                "signal":        None,       # 'highlight' is a general verb, not a signal type
                "speaker":       "Bhavneet Mhajan",
                "expected_tool": "search_transcripts",
                "known_gap":     False,
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
                "id":            "meet_yesno_commitments_last",
                "scope":         "meeting",
                "meeting_date":  "2026-05-07",
                "query_type":    "yesno",
                "signal":        "commitment",
                "speaker":       None,
                "expected_tool": "search_transcripts",
                "known_gap":     False,
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
                "id":            "meet_summary_last",
                "scope":         "meeting",
                "meeting_date":  "2026-05-07",
                "query_type":    "summary",
                "signal":        None,
                "speaker":       None,
                "expected_tool": "get_meeting_summaries",
                "known_gap":     False,
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
                "id":            "meet_list_nextsteps_last",
                "scope":         "meeting",
                "meeting_date":  "2026-05-07",
                "query_type":    "list",
                "signal":        "commitment",   # next steps = commitment chunks
                "speaker":       None,
                "expected_tool": "search_transcripts",
                "known_gap":     False,
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
                "id":            "meet_list_documents_last",
                "scope":         "meeting",
                "meeting_date":  "2026-05-07",
                "query_type":    "list",
                "signal":        "document_share",
                "speaker":       None,
                "expected_tool": "search_transcripts",
                "known_gap":     False,
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
                "id":            "meet_attr_bhavneet_feedback_apr20",
                "scope":         "meeting",
                "meeting_date":  "2026-04-20",
                "query_type":    "attribution",
                "signal":        None,       # 'feedback' is a general verb, not a signal type
                "speaker":       "Bhavneet Mhajan",
                "expected_tool": "search_transcripts",
                "known_gap":     False,
            },
        ),

    ]
)


# ══════════════════════════════════════════════════════════════════════
# Category C — Topic / Cross-Meeting
# Agent must trace a topic across multiple meetings or compare things.
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
                "id":            "multi_summary_ai_last2",
                "scope":         "multi-meeting",   # last-2-meetings scope
                "meeting_date":  None,
                "query_type":    "summary",
                "signal":        None,
                "speaker":       None,
                "expected_tool": "search_transcripts",
                "known_gap":     False,
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
                "id":            "proj_yesno_harsh_ai_questions",
                "scope":         "project",
                "meeting_date":  None,
                "query_type":    "yesno",
                "signal":        "question",
                "speaker":       "Harsh Vardhan",
                "expected_tool": "search_transcripts",
                "known_gap":     False,
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
                "id":            "proj_summary_ai_architecture_overall",
                "scope":         "project",
                "meeting_date":  None,
                "query_type":    "summary",
                "signal":        None,
                "speaker":       None,
                "expected_tool": "search_transcripts",
                "known_gap":     False,
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
                "id":            "multi_list_harsh_ai_commits_last5",
                "scope":         "multi-meeting",   # last-5-meetings scope
                "meeting_date":  None,
                "query_type":    "list",
                "signal":        "commitment",
                "speaker":       "Harsh Vardhan",
                "expected_tool": "search_transcripts",
                "known_gap":     False,
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
                "id":            "proj_attr_bhavneet_ai_clarity",
                "scope":         "project",
                "meeting_date":  None,
                "query_type":    "attribution",
                "signal":        None,
                "speaker":       "Bhavneet Mhajan",
                "expected_tool": "search_transcripts",
                "known_gap":     False,
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
                "id":            "proj_summary_ai_architecture_full",
                "scope":         "project",
                "meeting_date":  None,
                "query_type":    "summary",
                "signal":        None,
                "speaker":       None,
                "expected_tool": "search_transcripts",
                "known_gap":     False,
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
                "id":            "proj_decision_ai_exact_approach",
                "scope":         "project",
                "meeting_date":  None,
                "query_type":    "attribution",
                "signal":        "decision",
                "speaker":       None,
                "expected_tool": "search_transcripts",
                "known_gap":     False,
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
                "id":            "proj_cmp_oca_vs_fixedassets",
                "scope":         "project",
                "meeting_date":  None,
                "query_type":    "comparison",
                "signal":        "open_issue",
                "speaker":       None,
                "expected_tool": "search_transcripts",
                "known_gap":     True,   # agent got 0 results — hybrid search misses short acronym "OCA"
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
                "id":            "proj_cmp_latest_open_issue",
                "scope":         "project",
                "meeting_date":  None,
                "query_type":    "comparison",
                "signal":        "open_issue",
                "speaker":       None,
                "expected_tool": "search_transcripts",
                "known_gap":     False,
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
                "id":            "proj_attr_speaker_ranking",
                "scope":         "project",
                "meeting_date":  None,
                "query_type":    "attribution",
                "signal":        None,
                "speaker":       None,
                "expected_tool": "list_speakers",
                "known_gap":     False,
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
                "id":            "proj_list_simarjot_commits",
                "scope":         "project",
                "meeting_date":  None,
                "query_type":    "list",
                "signal":        "commitment",
                "speaker":       "Simarjot Kaur",
                "expected_tool": "search_transcripts",
                "known_gap":     False,
            },
        ),

    ]
)


# ══════════════════════════════════════════════════════════════════════
# ALL_QUERIES — combined dataset (A + B + C)
# ══════════════════════════════════════════════════════════════════════

ALL_QUERIES = EvaluationDataset(
    goldens=(
        PROJECT_QUERIES.goldens
        + MEETING_QUERIES.goldens
        + TOPIC_QUERIES.goldens
    )
)