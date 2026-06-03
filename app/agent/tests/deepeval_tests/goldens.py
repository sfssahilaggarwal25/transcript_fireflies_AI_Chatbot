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
          input="What did Ashpreet say about AI architecture?",
    
          expected_output=(
              "Ashpreet Singh discussed AI architecture across "
              "Nolocode AI meeting (2026-03-25) and Nolocode AI module. "
              "Key points: multi-agent vs single agent approach, "
              "four agents with subgraphs and lang graph design, "
              "modular microservice deployment, and feedback on "
              "AI Architecture Diagram 1 with agent definitions."
          ),
          additional_metadata={
            # Retrieval layer
            "expected_meetings": [
               "Nolocode AI meeting (2026-03-25)",
               "Nolocode - AI module",
            ],
            "expected_speaker": "Ashpreet Singh",
            "must_include_timestamps": [
               "49:20",  # four agents lang graph
               "40:02",  # multi agent vs single agent
               "58:35",  # AI Architecture Diagram feedback
            ],
            "must_not_include_timestamps": [
               "49:20",  # four agents lang graph
               "40:02",  # multi agent vs single agent
               "58:35",  # AI Architecture Diagram feedback
            ],
            # Fact layer
            "must_have_facts": [
               "multi-agent vs single agent architecture",
                "four agents with subgraphs and lang graph",
                "modular microservice deployment",
               "feedback on AI Architecture Diagram",
                "agent definitions provided",
            ],
            # Hallucination layer
            "must_not_have": [
               "Redis",          # different topic
               "AWS deployment", # irrelevant meeting
               "forecasting",    # different module
                "decision not found",
            ],

            # Scoring weights
            "eval_weights": {
              "retrieval": 0.4,
              "fact_recall": 0.4,
              "hallucination_free": 0.2,
            },

            # Metadata
            "id":            "proj_speaker_ashpreet_ai_architecture",
            "scope":         "project",
            "query_type":    "speaker_attribution",
            "signal":        "general",
            "speaker":       "Ashpreet Singh",
            "expected_tool": "search_transcripts",
            "known_gap":     False,

            # Known retrieval gap
            "known_missing": [
             "Ashpreet 56:50 — hybrid search recommendation missed"
            ],
        }
        ),
        Golden(
          input="What AI approach did we decide to go with?",
    
          expected_output=(
           "Two separate decisions were made. "
           "For stress test implementation, Approach 1 "
           "(deterministic) was finalized, confirmed by "
           "Akash and referenced by PM SFS and Bhavneet. "
            "For general chatbot queries, a RAG-based approach "
           "was decided. Single agent architecture was preferred "
           "initially, with multi-agent as fallback if needed."
        ),
        additional_metadata={
           # Retrieval layer
           "expected_meetings": [
            "Nolocode meeting (2026-04-08)",      # Approach 1 finalized
            "Nolocode-M2-and-M4 (2026-04-15)",   # Bhavneet confirmation
            "Nolocode AI meeting (2026-03-25)",   # RAG + single agent decision
            ],
           "expected_speakers": [
              "Project Manager SFS",
              "Bhavneet Mhajan",
              "Harsh Vardhan Dixit",
            ],
            "must_include_timestamps": [
              "39:02",   # PM SFS — Approach 1 finalized
              "55:00",   # Bhavneet — going with approach 1
              "31:32",   # Harsh — single agent first
            ],

            # Fact layer
            "must_have_facts": [
            "Approach 1 finalized for stress test",
            "RAG based approach for general queries",
            "single agent architecture preferred initially",
            "multi agent as fallback if needed",
            "Akash confirmed the decision",
            ],

            # Hallucination layer
            "must_not_have": [
            "approach 2 finalized",
            "decision not found",
            "unclear which approach",
            "Redis",          # alag topic
            "forecasting formula",  # alag topic
            ],

            # Important note
            "known_issue": (
            "System conflates stress test approach decision "
            "with overall AI approach — two separate decisions "
            "must both appear in answer"
            ),

            "known_missing": [
            "Harsh 31:32 — single agent first, multi agent fallback",
            "Bhavneet 1:02:07 — RAG based for non-preset questions",
            "Bhavneet 1:06:33 — RAG based approach confirmed",
            ],

            # Scoring weights
            "eval_weights": {
            "retrieval": 0.4,
            "fact_recall": 0.4,
            "hallucination_free": 0.2,
            },

            # Metadata
            "id":            "proj_decision_ai_approach",
            "scope":         "project",
            "query_type":    "decision",
            "signal":        "decision",
            "speaker":       None,
            "expected_tool": "search_transcripts",
            "known_gap":     False,
        },
        ),
        Golden(
            input="Give me an overview of what Bhavneet is trying to build in this project.",
            expected_output=(
               "Bhavneet Mhajan is focused on building Modules 2 and 3 "
                "of the financial intelligence platform. Key priorities: "
               "accurate financial formulas for forecasting, dynamic stress "
               "test outputs that leverage Module 2 data for specific "
               "recommendations rather than generic outputs, RAG-based "
               "approach for general queries, and integration between "
               "modules so M3 data flows correctly from M2."
            ),
            additional_metadata={
                # Retrieval layer
               "expected_meetings": [
                  "Nolocode-AI-meeting (2026-04-22)",
                  "Nolocode-M2-and-M4 (2026-04-15)",
                  "Nolocode AI meeting (2026-03-25)",
                  "Nolocode-M2-formula-discussion (2026-04-24)",
                ],
               "expected_speaker": "Bhavneet Mhajan",  # exact stored name
        
               # Fact layer
               "must_have_facts": [
                 "Module 2 and Module 3 development",
                 "M2 must be ready before M3 testing",
                 "AI output should leverage Module 2 data",
                 "generic output not acceptable",
                 "RAG based approach for general queries",
                 "dynamic stress test output required",
                 "financial formulas and logic implementation",
                ],
        
               # Hallucination layer
                "must_not_have": [
                  "Bhavneet is building the AI module",  
                  # Bhavneet reviewer hai, builder nahi
                 "Bhavneet is developer",
                  "decision not found",
                  "Redis",
                  "architecture diagram",
                ],
        
                # Known issues
               "known_issue": (
                  "Tool call mein 'Bhavneet Mahajan' ja raha hai "
                  "but stored name 'Bhavneet Mhajan' hai — "
                  "yeh speaker filter miss kar sakta hai"
                ),
        
                "known_missing": [
                  "RAG based approach clarification — "
                   "Approach 1/2 sirf stress test ke liye, "
                  "normal queries ke liye RAG (1:02:07, 1:05:22)",
            
                  "Generic output concern — "
                  "Bhavneet ne ChatGPT comparison diya (08:23)",
                ],
        
                # Scoring weights
                "eval_weights": {
                  "retrieval": 0.4,
                  "fact_recall": 0.4,
                  "hallucination_free": 0.2,
                },
        
                # Metadata
                "id":            "proj_overview_bhavneet_role",
                "scope":         "project",
                "query_type":    "speaker_overview",
                "signal":        "general",
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
    input="What has Karan Middha contributed across all meetings?",
    
    expected_output=(
        "Karan Middha serves as the technical coordination "
        "person — bridging client requirements and the "
        "development team. Key contributions: assessing "
        "feasibility of save button feature and its cascade "
        "effect on forecast regeneration, arguing against "
        "excessive microservices citing architecture complexity, "
        "confirming Redis not being used by their team, "
        "explaining frontend vs backend forecasting split, "
        "communicating team decisions on recommended approach, "
        "and coordinating time estimations for development tasks."
    ),
    
    additional_metadata={
        # Retrieval layer
        "expected_meetings": [
            "Nolocode meeting",
            "Nolocode-catchup",
            "Nolocode AI meeting",
            "Nolocode-M2-and-M4",
        ],
        "expected_speaker": "Karan Middha",
        "must_include_timestamps": [
            "33:19",   # drivers frontend only
            "55:56",   # microservices complicate
            "44:25",   # Redis not used
            "07:37",   # agreed recommended approach
            "22:43",   # cascade concern on forecasts
        ],

        # Fact layer
        "must_have_facts": [
            "technical coordination role not developer",
            "drivers saved on frontend only not backend",
            "microservices complicate architecture",
            "Redis not being used by their team",
            "save button triggers forecast regeneration cascade",
            "agreed to recommended approach after confusion",
            "time estimation coordination",
        ],

        # Hallucination layer
        "must_not_have": [
            "Karan is primary backend developer",
            "Karan implements features himself",
            "Karan is primary developer",
            "Redis is being used",
            "microservices recommended by Karan",
            "Karan owns Module 2",
            "decision not found",
        ],

        "known_issue": (
            "Tool query 'contributed discussed' bahut generic — "
            "better query: 'backend architecture forecasting microservice'"
        ),

        "known_missing": [
            "Karan 33:19 — drivers frontend only",
            "Karan 44:25 — Redis not used",
            "Karan 55:56 — microservices complexity",
            "Karan 85/88 — save button cascade effect",
        ],

        "eval_weights": {
            "retrieval": 0.4,
            "fact_recall": 0.4,
            "hallucination_free": 0.2,
        },

        "id":            "proj_contribution_karan_middha",
        "scope":         "project",
        "query_type":    "speaker_overview",
        "signal":        "general",
        "speaker":       "Karan Middha",
        "expected_tool": "search_transcripts",
        "known_gap":     False,
    },
),
Golden(
    input="What was decided about the microservice architecture?",
    
    expected_output=(
        "No single final decision was made. Current state: "
        "AI and forecasting are already two separate microservices. "
        "Ashpreet requested a single ingestion layer microservice "
        "for Module 1. Karan argued this would complicate the "
        "architecture unnecessarily. Immediate decision: build "
        "modular code within existing microservices rather than "
        "deploying new ones. Dedicated sandbox microservice "
        "excluded from current scope. Team agreed to discuss "
        "with Ashpreet to clarify requirements before proceeding."
    ),
    
    additional_metadata={
        # Retrieval layer
        "expected_meetings": [
            "Nolocode meeting",
            "Nolocode - AI module",
        ],
        "expected_speakers": [
            "Karan Middha",
            "Ashpreet Singh",
            "Nolocode AI",
        ],
        "must_include_timestamps": [
            "55:56",    # Karan — complicates architecture
            "59:02",    # Karan — 2 microservices already exist
            "06:20",    # Ashpreet — modular code not new microservice
            "1:01:47",  # Karan — needs discussion with client
        ],

        # Fact layer
        "must_have_facts": [
            "AI and forecasting already two separate microservices",
            "Karan argued against more microservices",
            "microservices complicate architecture",
            "modular code within existing microservices decided",
            "sandbox microservice not in current scope",
            "no final decision — needs client discussion",
            "Ashpreet requested single ingestion layer",
        ],

        # Hallucination layer
        "must_not_have": [
            "microservice architecture fully decided",
            "all modules converted to microservices",
            "Redis microservice",
            "decision finalized",
            "approach 1 finalized",  # irrelevant noise chunk
            "stress test effort",    # irrelevant noise chunk
        ],

        # Known issues
        "known_issue": (
            "4 irrelevant chunks in sources — "
            "save button, approach 1, stress test — "
            "precision problem still present"
        ),

        "known_missing": [
            "Karan 55:56 — complicates architecture argument",
            "Karan 59:02 — 2 microservices already exist",
            "Nolocode AI 56:56 — decision deferred",
            "Karan 1:01:47 — needs client clarity",
        ],

        "eval_weights": {
            "retrieval": 0.4,
            "fact_recall": 0.4,
            "hallucination_free": 0.2,
        },

        "id":            "proj_decision_microservice_architecture",
        "scope":         "project",
        "query_type":    "decision",
        "signal":        "decision",
        "speaker":       None,
        "expected_tool": "search_transcripts",
        "known_gap":     False,
    },
),
Golden(
    input="How did the forecasting formula discussions evolve across meetings?",
    
    expected_output=(
        "March 19: Team lacked formulas for retained earnings "
        "forecasting — Rhythm flagged missing values for other "
        "equity, current earnings, dividends. "
        "April 24: Bhavneet standardized formula logic across "
        "all accruals for future compatibility. "
        "May 5: New updated formulas introduced for forecast "
        "financials pages — end to end calculations completed. "
        "May 7: Client requested interest from debt forecast "
        "requiring full hierarchy change (HIGH effort). "
        "Nolocode AI clarified this was formula change not "
        "forecasting rework. Forecasting pages validated complete."
    ),
    
    additional_metadata={
        # Retrieval layer
        "expected_meetings": [
            "Nolocode meeting with Ashpreet (2026-03-19)",
            "Nolocode-M2-formula-discussion (2026-04-24)",
            "Nolocode-meeting (2026-05-05)",
            "Nolocode-meeting (2026-05-07)",
        ],
        "expected_speakers": [
            "Rhythm jalhotra",
            "Bhavneet Mhajan",
            "Nolocode AI",
        ],
        "must_include_timestamps": [
            "05:24",   # Rhythm — missing formula March
            "06:22",   # Rhythm — 4 values needed
            "09:38",   # Bhavneet — standardize formulas April
            "09:09",   # Rhythm — hierarchy change HIGH effort May 7
            "19:13",   # Nolocode AI — formula change not rework
        ],

        # Fact layer
        "must_have_facts": [
            "March — team missing forecasting formulas",
            "retained earnings formula not provided",
            "April — formula logic standardized across accruals",
            "May 5 — new updated formulas introduced",
            "May 7 — hierarchy change required for interest from debt",
            "HIGH effort for hierarchy change",
            "formula change not forecasting rework",
            "forecasting pages validated complete by May 7",
        ],

        # Hallucination layer
        "must_not_have": [
            "forecasting completely reworked",
            "formulas were always correct",
            "no changes in formulas",
            "Harsh Vardhan forecasting formula",  # noise chunk
            "Redis forecasting",
        ],

        # Scoring weights
        "eval_weights": {
            "retrieval": 0.3,   # temporal query mein
            "fact_recall": 0.5, # facts zyada important
            "hallucination_free": 0.2,
        },

        # Note: temporal queries mein fact_recall 
        # zyada weight diya — chronological completeness
        # matters more than exact meeting retrieval

        "known_missing": [
            "Rhythm 09:09 — hierarchy change HIGH effort",
            "Nolocode AI 59:57 — forecasting pages validated",
        ],

        "known_issue": (
            "Noise chunk — Harsh Vardhan 10:14 irrelevant. "
            "Temporal ordering in answer good but "
            "hierarchy change concern completely missed."
        ),

        "id":            "proj_evolution_forecasting_formula",
        "scope":         "project",
        "query_type":    "temporal_evolution",
        "signal":        "general",
        "speaker":       None,
        "expected_tool": "search_transcripts",
        "known_gap":     False,
    },
),
Golden(
    input="What did Harsh Vardhan say about the stress test implementation?",
    
    expected_output=(
        "Harsh Vardhan Dixit explained two approaches. "
        "Approach 1 (previous): Query classified as stress test "
        "or general. Each stress test needed a separate Python "
        "file, manual repo change, and redeployment — taking "
        "3 days per stress test. Main con: not scalable. "
        "Approach 2 (agent-based): Document processed by agent "
        "into markdown and Python function, validated, then "
        "indexed to vector store. Search on summary, output is "
        "executable function. Single agent first, multi-agent "
        "if needed. POC took 60 seconds (double of approach 1). "
        "POC had issue returning insolvent result."
    ),
    
    additional_metadata={
        # Retrieval layer
        "expected_meetings": [
            "Nolocode AI meeting (2026-03-25)",
        ],
        "expected_speaker": "Harsh Vardhan Dixit",
        "must_include_timestamps": [
            "11:29",   # query classification
            "26:46",   # main con of approach 1
            "27:36",   # approach 2 document processing
            "45:24",   # 60 seconds latency
            "55:49",   # parent document retriever strategy
        ],

        # Fact layer
        "must_have_facts": [
            "query classified as stress test or general",
            "separate Python file per stress test approach 1",
            "3 days per stress test implementation",
            "manual repo change required for each new test",
            "scalability problem with approach 1",
            "approach 2 agent generates Python function from document",
            "function validated before indexing to vector store",
            "single agent first multi-agent if needed",
            "approach 2 POC took 60 seconds double of approach 1",
            "parent document retriever search on summary output is function",
            "POC issue returning insolvent",
        ],

        # Hallucination layer
        "must_not_have": [
            "stress test implemented in frontend",
            "no latency difference between approaches",
            "approach 2 faster than approach 1",
            "decision not found",
            "Redis stress test",
        ],

        "eval_weights": {
            "retrieval": 0.3,   # single meeting query
            "fact_recall": 0.5, # technical details important
            "hallucination_free": 0.2,
        },

        "known_missing": [
            "Harsh 26:46 — main con of approach 1 scalability",
            "Harsh 45:24 — 60 seconds POC latency",
            "Harsh 55:49 — parent document retriever strategy",
        ],

        "known_issue": (
            "Good retrieval — no noise chunks. "
            "But 3 important technical chunks missed: "
            "scalability con, latency, vector store strategy."
        ),

        "id":            "proj_speaker_harsh_stress_test",
        "scope":         "project",
        "query_type":    "speaker_attribution",
        "signal":        "general",
        "speaker":       "Harsh Vardhan Dixit",
        "expected_tool": "search_transcripts",
        "known_gap":     False,
    },
),
Golden(
    input="What were the main open issues discussed in the Nolocode AI meeting on March 25?",
    
    expected_output=(
        "6 open issues were raised. "
        "1. Harsh: Approach 1 not scalable — every stress test "
        "requires manual repo change and redeployment. "
        "2. Harsh: POC simulation function returning insolvent — "
        "bug in stress test function. "
        "3. Ashpreet: What makes approach 2 better than approach 1 "
        "given deterministic output and unit tests in approach 1. "
        "4. Ashpreet: Gemini Flash Lite not accurate — specifically "
        "SQL query formation was failing. "
        "5. Ashpreet: If document not well articulated in vector DB "
        "approach 2 will have same issues as approach 1. "
        "6. Ashpreet: Chunking strategy unclear — how to store "
        "large documents in vector DB."
    ),
    
    additional_metadata={
        # Retrieval layer
        "expected_meetings": [
            "Nolocode AI meeting (2026-03-25)",
        ],
        "expected_speakers": [
            "Harsh Vardhan Dixit",
            "Ashpreet Singh",
        ],
        "must_include_timestamps": [
            "26:46",   # scalability issue
            "36:39",   # POC insolvent bug
            "38:44",   # approach 2 vs approach 1
            "47:20",   # SQL query formation failing
            "50:38",   # document quality issue
            "54:37",   # chunking strategy
        ],

        # Fact layer
        "must_have_facts": [
            "approach 1 not scalable manual repo change",
            "POC function returning insolvent",
            "SQL query formation failing in Gemini Flash Lite",
            "document quality affects approach 2 accuracy",
            "chunking strategy unclear for large documents",
            "approach 2 vs approach 1 comparison concern",
        ],

        # Hallucination layer
        "must_not_have": [
            "no open issues",
            "issues resolved in meeting",
            "Redis issue",
            "forecasting formula issue",
            "module 2 issue",
        ],

        "eval_weights": {
            "retrieval": 0.3,
            "fact_recall": 0.5,
            "hallucination_free": 0.2,
        },

        "known_missing": [
            "Harsh 47:32 — SQL query formation specifically "
            "mentioned but not in system answer",
        ],

        "known_issue": (
            "Best performing query so far — "
            "signal_filter open_issue perfectly worked. "
            "Only minor miss: SQL query formation detail "
            "from Harsh 47:32 not captured in answer."
        ),

        "id":            "proj_open_issues_nolocode_ai_meeting",
        "scope":         "project",
        "query_type":    "specific_fact",
        "signal":        "open_issue",
        "speaker":       None,
        "expected_tool": "search_transcripts",
        "known_gap":     False,
    },
),
Golden(
    input="What was the save button feature discussion about?",
    
    expected_output=(
        "Save button feature was requested by client to persist "
        "driver changes to backend so forecasts update permanently. "
        "Currently drivers were only saved on frontend. "
        "Architecture impact: required M2 and M3 to be rebuilt "
        "from scratch. Team spent 2 days on architecture design. "
        "Final solution: click save button → JSON field updates → "
        "popup confirmation → full forecast regeneration. "
        "Reset button also added to revert to baseline. "
        "Feature was last pending item before completion."
    ),
    
    additional_metadata={
        # Retrieval layer
        "expected_meetings": [
            "Nolocode meeting (1775623200000)",   # initial request
            "Nolocode meeting (1775736600000)",   # architecture discussion
            "Nolocode meeting (1775823300000)",   # architecture focus
            "Nolocode-catchup (2026-04-20)",      # solution finalized
        ],
        "expected_speakers": [
            "Project Manager SFS",
            "Karan Middha",
            "Neha",
            "Ngũmi Gituro",
        ],
        "must_include_timestamps": [
            "24:02",   # Ngumi — initial need
            "14:29",   # Neha — drivers to backend
            "00:00",   # PM SFS — M2/M3 from scratch
            "00:54",   # Karan — JSON + function
            "09:17",   # Karan — popup on click
            "12:42",   # Nolocode AI — reset button agreed
        ],

        # Fact layer
        "must_have_facts": [
            "drivers currently saved frontend only",
            "client wants drivers saved to backend on click",
            "M2 and M3 need to be rebuilt from scratch",
            "team spent 2 days on save button architecture",
            "JSON field updates on save button click",
            "popup confirmation before DB changes",
            "full forecast regeneration triggered on save",
            "reset button added alongside save button",
            "save button was last pending item",
        ],

        # Hallucination layer
        "must_not_have": [
            "save button already implemented",
            "no architecture impact",
            "frontend only change",
            "Redis save button",
            "save button rejected",
        ],

        # Scoring — cross meeting query
        "eval_weights": {
            "retrieval": 0.4,
            "fact_recall": 0.4,
            "hallucination_free": 0.2,
        },

        "known_missing": [
            "PM SFS 25:00 — initial commitment to check possibility",
            "PM SFS 52:15 — save button last pending item status",
            "PM SFS 07:20 M2-and-M4 — except save button rest done",
            "PM SFS 17:31 — in discussion with Akash Raheel",
        ],

        "known_issue": (
            "Answer mein wrong dates assigned — "
            "2026-04-09 aur 2026-04-10 galat hain. "
            "Timestamp-based meetings ke actual dates "
            "verify karne ki zaroorat hai."
        ),

        "id":            "proj_feature_save_button",
        "scope":         "project",
        "query_type":    "cross_meeting",
        "signal":        "general",
        "speaker":       None,
        "expected_tool": "search_transcripts",
        "known_gap":     False,
    },
),
Golden(
    input="What did the team decide about quantum computing implementation in the project?",
    
    expected_output=(
        "Quantum computing was not discussed or decided upon "
        "in any project meeting. This topic is not present "
        "in the meeting transcripts."
    ),
    
    additional_metadata={
        # Retrieval layer
        "expected_meetings": [],  # koi nahi hona chahiye
        "expected_speakers":  [],

        # Fact layer
        "must_have_facts": [
            "quantum computing not discussed",
            "not present in meetings",
        ],

        # Hallucination layer — most important for known gap
        "must_not_have": [
            "quantum computing decided",
            "team discussed quantum",
            "quantum implementation planned",
            "quantum rejected",
            "quantum in scope",
        ],

        "eval_weights": {
            "retrieval":        0.1,  # koi chunks expected nahi
            "fact_recall":      0.3,  # simple — just "not found"
            "hallucination_free": 0.6, # most important for gap queries
        },

        # Note: Known gap queries mein hallucination
        # weight zyada hona chahiye — agar system
        # kuch bhi invent kare toh fail

        "known_issue": (
            "System correctly said not found but "
            "unnecessarily listed 38 project topics. "
            "Ideal response: 2-3 lines, no topic listing."
        ),

        "id":            "proj_known_gap_quantum_computing",
        "scope":         "project",
        "query_type":    "known_gap",
        "signal":        None,
        "speaker":       None,
        "expected_tool": "search_transcripts",
        "known_gap":     True,
    },
),

        # Golden(
        #     input="List all meetings in this project with their dates.",
        #     expected_output=(
        #         "Exactly 10 meetings are listed. "
        #         "The date 2026-03-19 (first meeting) appears in the list. "
        #         "The date 2026-05-07 (last meeting) appears in the list. "
        #         "All dates are in YYYY-MM-DD format. "
        #         "The list is in chronological order from earliest to latest."
        #     ),
        #     additional_metadata={
        #         "id":            "proj_list_all_meetings",
        #         "scope":         "project",
        #         "meeting_date":  None,
        #         "query_type":    "list",
        #         "signal":        None,
        #         "speaker":       None,
        #         "expected_tool": "list_meetings",
        #         "known_gap":     True,   # same root cause as proj_count_meetings
        #     },
        # ),

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

PROJECT_LEVEL_GOLDENS = PROJECT_QUERIES.goldens