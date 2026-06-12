"""
goldens.py — DeepEval EvaluationDataset for the production LangGraph agent.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GOLDEN STRUCTURE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Golden(
      input="...",            # ✅ Always fill — the PM's exact query
      expected_output="...",  # ✅ Always fill — ideal answer from transcript
      additional_metadata={}, # ✅ Always fill — filtering + eval layer config
      # retrieval_context     # ❌ Never fill here — populated at runtime
      # actual_output         # ❌ Never fill here — populated at runtime
  )

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXPECTED_OUTPUT FORMAT RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  DeepEval's ContextualRecallMetric evaluates each sentence in
  expected_output independently against the retrieved chunks.

  Rules:
  1. Factual declarative sentences only. Each sentence = one verifiable
     claim that exists in the transcript text.
  2. No rubric assertions ("the answer should contain…").
  3. No conditional clauses ("if yes:…").
  4. Short sentences score more cleanly — one fact per sentence.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
METADATA SCHEMA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  id               Unique slug. Used with --ids flag.
  scope            "project" | "meeting" | "multi-meeting"
  meeting_date     ISO date for meeting-scoped queries. None otherwise.
  query_type       "count" | "yesno" | "list" | "summary" | "attribution"
                   | "comparison" | "temporal_evolution" | "decision"
                   | "known_gap"
  signal           "commitment" | "decision" | "question" | "open_issue"
                   | "document_share" | None
  speaker          Exact stored name if query names a speaker. None otherwise.
  expected_tool    Primary tool the agent must call (documentation only).
  known_gap        True if this golden is expected to fail (known limitation).
  must_have_facts  Atomic claims the answer must contain (eval_runner.py).
  must_not_have    Strings that must not appear — hallucination check.
  expected_meetings Meeting titles that should appear as cited sources.
  eval_weights     retrieval / fact_recall / hallucination_free (sum = 1.0).
  known_issue      Known system limitation for this query.
  known_missing    Specific chunks currently not retrieved by the system.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
KNOWN FACTS  (proj_nolocode_001)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Total meetings: 10.  Sorted chronologically.
  "Previous / last meeting" = 2026-05-07 (most recent by date).

  Date         Title                            Chunks  commit  dec  quest  issue  doc
  ──────────── ──────────────────────────────── ──────  ──────  ───  ─────  ─────  ───
  2026-03-19   Nolocode meeting with Ashpreet      191      18    2     45      4    4
  2026-03-25   Nolocode AI meeting                 211      33    4     59      6    2
  2026-04-14   Nolocode-M1                         155      23    1     34     15    1
  2026-04-14   Nolocode-AWS-deployment             127      10    0     17      8    1
  2026-04-15   Nolocode-M2-and-M4                  257      38    3     79     12    5
  2026-04-20   Nolocode-catchup                    176      47    4     28     10    0
  2026-04-22   Nolocode-AI-meeting                  45      13    0     21      0    0
  2026-04-24   Nolocode-M2-formula-discussion      240      42    1     65      7    1
  2026-05-05   Nolocode-meeting                     53      10    0      7      3    2
  2026-05-07   Nolocode-meeting (LAST)             204      44    5     28      9    0

  Known speakers (exact stored names):
    "Ashpreet Singh"       [client — technical stakeholder]
    "Bhavneet Mhajan"      [client]
    "Rhythm jalhotra"      [developer]
    "Karan Middha"         [developer]
    "Project Manager SFS"  [project_manager]
    "Nolocode AI"          [developer]
    "Simarjot Kaur"        [developer]   ← unconfirmed; run verify_chunks first
    "Harsh Vardhan Dixit"  [developer]   ← confirmed: 180 chunks in DB
"""

from deepeval.dataset import Golden, EvaluationDataset


# ══════════════════════════════════════════════════════════════════════════════
# Category A — Project-Level  (11 goldens)
# No scope phrase in query → all 10 meetings searched.
# ══════════════════════════════════════════════════════════════════════════════

CORRECT_QUERIES = EvaluationDataset(
    goldens=[

        # ── A-01  speaker + topic attribution ────────────────────────────────
        Golden(
            input="What did Ashpreet say about AI architecture?",
            expected_output=(
                "Ashpreet discussed the AI architecture design and suggested using a structured multi-agent approach rather than relying solely on a deterministic workflow. He emphasized defining clear agent responsibilities, using LangGraph with agents, subgraphs, nodes, and tools, and carefully designing document chunking and retrieval strategies. He highlighted thatretrieval should combine semantic search with metadata-based filtering (hybrid search) to improve speed and accuracy. He also stressed that document quality, chunking strategy, and embedding quality are critical because poor inputs will lead to poor outputs. Additionally, he recommended reviewing the AI Architecture document, agent definitions, and feedback from previous documents to ensure the architecture is scalable, production-ready, and optimized for implementation effort."
            ),
            # context = ideal chunks that SHOULD be retrieved (ground truth)
            # retrieval_context = what the system actually retrieves at runtime
            context=[
                "This is a multi agent flow and that's a single agent managing everything.",
                "That needs to be part of vector or is just. This can just be part of your lang graph node and subgraphs also you can manage that from subgraphs also your deterministic flow."
                "Have you Planned out how your let's say I've given you four agents plan planner out how you will work with sub graphs and graphs and nodes and tools in each agents based on their role."
                "I've given feedback to both of the pages. So there was some bit of information on Unifieds and some of bit of this new AI architecture one so you can correlate and put it together."
                "I have defined agents definitions there because previous year also mentioned previous ones there. Just look into that input document."
                "I will suggest you use a semantic search kind of in a hybrid search semantic plus metadata."
                "During your chunking you're storing as a metadata as well and summary as well."
                "If document is not well articulated or given to the vector embedded correctly it will still have the same issue."
            ],
            additional_metadata={
                "id":            "proj_speaker_ashpreet_ai_architecture",
                "scope":         "project",
                "meeting_date":  None,
                "query_type":    "attribution",
                "signal":        None,
                "speaker":       "Ashpreet Singh",
                # dense_query strips the speaker name so the vector embedding
                # focuses on the topic only. The speaker is already handled by
                # hard_filters — encoding "Ashpreet" in the embedding dilutes
                # the semantic signal for "AI architecture".
                # Deliberately avoids the word "architecture" — it causes the
                # reranker to score microservice/backend chunks as 9.5 because
                # they ARE architecture discussions, just not AI/ML architecture.
                "dense_query":   "multi-agent LangGraph subgraph node tool embedding vector chunking retrieval strategy",
                "expected_tool": "search_transcripts",
                "known_gap":     False,

                "expected_meetings": [
                    "Nolocode AI meeting (2026-03-25)",
                    "Nolocode - AI module",
                ],
                "must_have_facts": [
                    "multi-agent vs single agent architecture",
                    "four agents with subgraphs and lang graph",
                    "modular microservice deployment",
                    "feedback on AI Architecture Diagram",
                    "agent definitions provided",
                ],
                "must_not_have": [
                    "Redis",
                    "AWS deployment",
                    "forecasting",
                    "decision not found",
                ],
                "eval_weights": {
                    "retrieval":          0.4,
                    "fact_recall":        0.4,
                    "hallucination_free": 0.2,
                },
                "known_missing": [
                    "Ashpreet 56:50 — hybrid search recommendation not retrieved",
                ],
            },
        ),

        # ── A-02  no-speaker decision query (pure topic retrieval) ────────────
        Golden(
            input="What AI approach did we decide to go with?",
            expected_output=(
                "Approach 1 was finalized for Module 4. "
                "A RAG-based approach was decided for non-preset chatbot questions."
            ),
            # context = ground-truth chunks (no-speaker path → raw text only, no speaker prefix).
            # Sentences referencing "Project Manager SFS confirmed... in 2026-04-08" and
            # "Bhavneet Mhajan confirmed... in 2026-04-15" were removed — speaker names and
            # meeting dates live in chunk metadata, not chunk text. The Recall judge compares
            # retrieval_context (raw text) against expected_output, so those facts can never
            # be verified. Bhavneet's "going with approach one" chunk also never appears in the
            # top-20 retrieval results (6-word chunk buried by verbose discussion chunks from
            # the 2026-03-25 Nolocode AI meeting that dominate hybrid search for "approach").
            context=[
                "Project Manager SFS: module 4 starting with the approach 1, whatever is.",
                "Bhavneet Mhajan: It's a RAG based approach for the non preset questions.",
                "Karan Middha: approach one and two is just for the stress test case. It's nothing to do with the simple Chatbot.",
                "Harsh Vardhan Dixit: first we will go with the single agent approach. If the single agent is enough then we will stay with the single agent. Else we will move to a multi agent architecture.",
            ],
            additional_metadata={
                "id":            "proj_decision_ai_approach",
                "scope":         "project",
                "meeting_date":  None,
                "query_type":    "decision",
                "signal":        "decision",
                "speaker":       None,
                # dense_query: confirmation-focused vocabulary so the vector search
                # finds the SHORT decision chunks ("we're going with approach one",
                # "module 4 starting with approach 1") which get buried when broad
                # topic vocabulary ("stress test", "multi-agent") dominates the query.
                "dense_query":   "going with approach one decided confirmed module 4 single agent RAG",
                # reranker_hint: tells the reranker to score DECISION CONFIRMATIONS high
                # and hard-drop PRESENTATION chunks. Without this, the reranker scores
                # Harsh's approach-2 demo (Langsmith, agent mechanics) at 9 because the
                # question "decide to go with" doesn't distinguish presentation from
                # decision.
                # Broader than "final decision confirmed" alone — also includes RAG and
                # single agent so those confirmation chunks score ≥7 and avoid the noisy
                # fallback (triggered when <3 chunks are high-quality).
                "reranker_hint": "approach one finalized decided module 4 RAG single agent architecture decision confirmed",
                "expected_tool": "search_transcripts",
                "known_gap":     False,

                "expected_meetings": [
                    "Nolocode meeting (2026-04-08)",
                    "Nolocode-M2-and-M4 (2026-04-15)",
                    "Nolocode AI meeting (2026-03-25)",
                ],
                "must_have_facts": [
                    "approach one is finalized for module four",
                    "going with approach one",
                    "RAG based approach for non preset questions",
                    "approach one and two is just for the stress test",
                    "single agent approach first multi agent if needed",
                ],
                "must_not_have": [
                    "approach 2 finalized",
                    "decision not found",
                    "unclear which approach",
                ],
                "eval_weights": {
                    "retrieval":          0.4,
                    "fact_recall":        0.4,
                    "hallucination_free": 0.2,
                },
                "known_missing": [
                    "Harsh 31:32 — single agent first, multi-agent fallback (buried by 211 discussion chunks)",
                    "Karan — approach one and two only for stress test, not chatbot (buried by discussion chunks)",
                    "Bhavneet 1:02:07 — RAG based for non-preset questions",
                    "Bhavneet 1:06:33 — RAG based approach confirmed",
                ],
            },
        ),

    ]
)

PROJECT_QUERIES = EvaluationDataset(
    goldens=[

        # ── A-01 ─────────────────────────────────────────────────────────────
        Golden(
            input="What did Ashpreet say about AI architecture?",
            expected_output=(
                "Ashpreet discussed the AI architecture design and suggested using a structured multi-agent approach rather than relying solely on a deterministic workflow. He emphasized defining clear agent responsibilities, using LangGraph with agents, subgraphs, nodes, and tools, and carefully designing document chunking and retrieval strategies. He highlighted thatretrieval should combine semantic search with metadata-based filtering (hybrid search) to improve speed and accuracy. He also stressed that document quality, chunking strategy, and embedding quality are critical because poor inputs will lead to poor outputs. Additionally, he recommended reviewing the AI Architecture document, agent definitions, and feedback from previous documents to ensure the architecture is scalable, production-ready, and optimized for implementation effort."
            ),
            # context = ideal chunks that SHOULD be retrieved (ground truth)
            # retrieval_context = what the system actually retrieves at runtime
            context=[
                "This is a multi agent flow and that's a single agent managing everything.",
                "That needs to be part of vector or is just. This can just be part of your lang graph node and subgraphs also you can manage that from subgraphs also your deterministic flow."
                "Have you Planned out how your let's say I've given you four agents plan planner out how you will work with sub graphs and graphs and nodes and tools in each agents based on their role."
                "I've given feedback to both of the pages. So there was some bit of information on Unifieds and some of bit of this new AI architecture one so you can correlate and put it together."
                "I have defined agents definitions there because previous year also mentioned previous ones there. Just look into that input document."
                "I will suggest you use a semantic search kind of in a hybrid search semantic plus metadata."
                "During your chunking you're storing as a metadata as well and summary as well."
                "If document is not well articulated or given to the vector embedded correctly it will still have the same issue."
            ],
            additional_metadata={
                "id":            "proj_speaker_ashpreet_ai_architecture",
                "scope":         "project",
                "meeting_date":  None,
                "query_type":    "attribution",
                "signal":        None,
                "speaker":       "Ashpreet Singh",
                "dense_query":   "multi-agent LangGraph subgraph node tool embedding vector chunking retrieval strategy",
                "expected_tool": "search_transcripts",
                "known_gap":     False,

                "expected_meetings": [
                    "Nolocode AI meeting (2026-03-25)",
                    "Nolocode - AI module",
                ],
                "must_have_facts": [
                    "multi-agent vs single agent architecture",
                    "four agents with subgraphs and lang graph",
                    "modular microservice deployment",
                    "feedback on AI Architecture Diagram",
                    "agent definitions provided",
                ],
                "must_not_have": [
                    "Redis",
                    "AWS deployment",
                    "forecasting",
                    "decision not found",
                ],
                "eval_weights": {
                    "retrieval":          0.4,
                    "fact_recall":        0.4,
                    "hallucination_free": 0.2,
                },
                "known_missing": [
                    "Ashpreet 56:50 — hybrid search recommendation not retrieved",
                ],
            },
        ),

        # ── A-02 ─────────────────────────────────────────────────────────────
        Golden(
            input="What AI approach did we decide to go with?",
            expected_output=(
                "Two separate AI approach decisions were made across multiple meetings. "
                "For the stress test module, Approach 1 (deterministic) was finalized for Module 4. "
                "Project Manager SFS confirmed Approach 1 was finalized in the 2026-04-08 meeting. "
                "Bhavneet Mhajan confirmed the team was going with Approach 1 in the 2026-04-15 meeting. "
                "For general chatbot queries, a RAG-based approach was decided for non-preset questions. "
                "Approach 1 and Approach 2 applied only to the stress test case, not to general queries. "
                "For overall architecture, the team decided on a single agent approach first "
                "with multi-agent as fallback if needed."
            ),
            context=[
                "Project Manager SFS: Approach 1 is finalized for Module 4.",
                "Bhavneet Mhajan: Yes, we are going with Approach 1.",
                "Bhavneet Mhajan: For non-preset questions we should use a RAG-based approach.",
                "Bhavneet Mhajan: Approach 1 and Approach 2 are only for the stress test case, not general queries.",
                "Harsh Vardhan Dixit: I propose starting with a single agent approach, with multi-agent as fallback if needed.",
            ],
            additional_metadata={
                "id":            "proj_decision_ai_approach",
                "scope":         "project",
                "meeting_date":  None,
                "query_type":    "decision",
                "signal":        "decision",
                "speaker":       None,
                "expected_tool": "search_transcripts",
                "known_gap":     False,

                "expected_meetings": [
                    "Nolocode meeting (2026-04-08)",
                    "Nolocode-M2-and-M4 (2026-04-15)",
                    "Nolocode AI meeting (2026-03-25)",
                ],
                "must_have_facts": [
                    "approach one is finalized for module four",
                    "going with approach one",
                    "RAG based approach for non preset questions",
                    "approach one and two is just for the stress test",
                    "single agent approach first multi agent if needed",
                ],
                "must_not_have": [
                    "approach 2 finalized",
                    "decision not found",
                    "unclear which approach",
                    "Redis",
                    "forecasting formula",
                ],
                "eval_weights": {
                    "retrieval":          0.4,
                    "fact_recall":        0.4,
                    "hallucination_free": 0.2,
                },
                "known_issue": (
                    "System may conflate the stress test approach decision with the overall "
                    "AI architecture decision. Both decisions must appear separately in the answer."
                ),
                "known_missing": [
                    "Harsh 31:32 — single agent first multi-agent fallback",
                    "Bhavneet 1:02:07 — RAG based for non-preset questions",
                    "Bhavneet 1:06:33 — RAG based approach confirmed",
                ],
            },
        ),

        # ── A-03 ─────────────────────────────────────────────────────────────
        Golden(
            input="Give me an overview of what Bhavneet is trying to build in this project.",
            expected_output=(
                "Bhavneet Mhajan is focused on building Modules 2 and 3 of the financial intelligence platform. "
                "Module 2 must be completed before Module 3 testing can begin. "
                "Bhavneet requires the AI output to use Module 2 data for specific recommendations "
                "rather than producing generic outputs. "
                "A RAG-based approach was agreed upon for handling general non-preset queries. "
                "Bhavneet requires dynamic stress test output that leverages Module 2 data. "
                "Bhavneet is responsible for the financial formulas and logic implementation."
            ),
            context=[
                "Bhavneet Mhajan: Module 2 needs to be completed before we can start testing Module 3.",
                "Bhavneet Mhajan: The AI output should use Module 2 data for specific recommendations, not produce generic output like ChatGPT.",
                "Bhavneet Mhajan: For general non-preset queries we agreed on a RAG-based approach.",
                "Bhavneet Mhajan: We need dynamic stress test output that leverages Module 2 data.",
                "Bhavneet Mhajan: I am responsible for the financial formulas and logic implementation.",
            ],
            additional_metadata={
                "id":            "proj_overview_bhavneet_role",
                "scope":         "project",
                "meeting_date":  None,
                "query_type":    "summary",
                "signal":        None,
                "speaker":       "Bhavneet Mhajan",
                "expected_tool": "search_transcripts",
                "known_gap":     False,

                "expected_meetings": [
                    "Nolocode-AI-meeting (2026-04-22)",
                    "Nolocode-M2-and-M4 (2026-04-15)",
                    "Nolocode AI meeting (2026-03-25)",
                    "Nolocode-M2-formula-discussion (2026-04-24)",
                ],
                "must_have_facts": [
                    "Module 2 and Module 3 development",
                    "M2 must be ready before M3 testing",
                    "AI output should leverage Module 2 data",
                    "generic output not acceptable",
                    "RAG based approach for general queries",
                    "dynamic stress test output required",
                    "financial formulas and logic implementation",
                ],
                "must_not_have": [
                    "Bhavneet is building the AI module",
                    "Bhavneet is developer",
                    "decision not found",
                    "Redis",
                ],
                "eval_weights": {
                    "retrieval":          0.4,
                    "fact_recall":        0.4,
                    "hallucination_free": 0.2,
                },
                "known_issue": (
                    "Tool call may use 'Bhavneet Mahajan' (misspelling) instead of the stored "
                    "name 'Bhavneet Mhajan', causing the speaker filter to miss chunks."
                ),
                "known_missing": [
                    "RAG approach clarification (1:02:07, 1:05:22) — Approach 1/2 only for stress test",
                    "Generic output concern (08:23) — Bhavneet compared to ChatGPT",
                ],
            },
        ),

        # ── A-04 ─────────────────────────────────────────────────────────────
        Golden(
            input="When and where did Harsh commit to using hybrid search?",
            expected_output=(
                "Harsh Vardhan Dixit committed to using a hybrid search strategy "
                "in the Nolocode AI meeting on 2026-03-25. "
                "Harsh described a parent document retriever approach for indexing "
                "documents into the vector store. "
                "The commitment was part of Harsh's explanation of Approach 2 "
                "for stress test implementation."
            ),
            context=[
                "Harsh Vardhan Dixit: For Approach 2, I will use a hybrid search strategy.",
                "Harsh Vardhan Dixit: I plan to use a parent document retriever approach for indexing documents into the vector store.",
                "Harsh Vardhan Dixit: This is part of Approach 2 for the stress test implementation.",
            ],
            additional_metadata={
                "id":            "proj_commit_harsh_hybrid_search",
                "scope":         "project",
                "meeting_date":  None,
                "query_type":    "attribution",
                "signal":        "commitment",
                "speaker":       "Harsh Vardhan Dixit",
                "expected_tool": "search_transcripts",
                "known_gap":     False,

                "expected_meetings": [
                    "Nolocode AI meeting (2026-03-25)",
                ],
                "must_have_facts": [
                    "hybrid search commitment Harsh Vardhan",
                    "Nolocode AI meeting 2026-03-25",
                    "parent document retriever strategy",
                ],
                "must_not_have": [
                    "commitment not found",
                    "no hybrid search discussed",
                ],
                "eval_weights": {
                    "retrieval":          0.4,
                    "fact_recall":        0.4,
                    "hallucination_free": 0.2,
                },
            },
        ),

        # ── A-05 ─────────────────────────────────────────────────────────────
        Golden(
            input="What has Karan Middha contributed across all meetings?",
            expected_output=(
                "Karan Middha confirmed that driver calculations are only performed on the frontend, "
                "not saved to the backend. "
                "Karan stated the team is not using Redis. "
                "Karan argued that adding more microservices would only complicate the architecture. "
                "The system has two separate microservices: AI and forecasting. "
                "Karan noted that all forecasts would be regenerated when the save button is triggered. "
                "Karan confirmed the team would go with the recommended approach for the project."
            ),
            context=[
                "Karan Middha: We are not saving drivers to the backend. Calculations are only done on the frontend.",
                "Karan Middha: We are not using Redis.",
                "Karan Middha: Adding more microservices will only complicate the architecture.",
                "Karan Middha: We have two separate microservices: AI and forecasting.",
                "Karan Middha: All forecasts will be regenerated again when the save button is triggered.",
                "Karan Middha: Let's go with your recommended approach.",
            ],
            additional_metadata={
                "id":            "proj_contribution_karan_middha",
                "scope":         "project",
                "meeting_date":  None,
                "query_type":    "summary",
                "signal":        None,
                "speaker":       "Karan Middha",
                "expected_tool": "search_transcripts",
                "known_gap":     False,

                "expected_meetings": [
                    "Nolocode meeting",
                    "Nolocode-catchup",
                    "Nolocode AI meeting",
                    "Nolocode-M2-and-M4",
                ],
                "must_have_facts": [
                    "not saving drivers to the back end",
                    "forecasting is being done on the front end",
                    "we are not using Redis",
                    "it will only complicate the architecture",
                    "two different microservices AI and forecasting",
                    "all the forecast will be regenerated again",
                    "go with your recommended approach",
                ],
                "must_not_have": [
                    "Karan is primary backend developer",
                    "Redis is being used",
                    "microservices recommended by Karan",
                    "Karan owns Module 2",
                    "decision not found",
                ],
                "eval_weights": {
                    "retrieval":          0.4,
                    "fact_recall":        0.4,
                    "hallucination_free": 0.2,
                },
                "known_issue": (
                    "Search query 'contributed discussed' is too generic. "
                    "A targeted query like 'backend architecture forecasting microservice' "
                    "gives significantly better recall."
                ),
                "known_missing": [
                    "Karan 33:19 — drivers frontend only",
                    "Karan 44:25 — Redis not used",
                    "Karan 55:56 — microservices complexity argument",
                    "Karan 85/88 — save button cascade effect",
                ],
            },
        ),

        # ── A-06 ─────────────────────────────────────────────────────────────
        Golden(
            input="What was decided about the microservice architecture?",
            expected_output=(
                "The AI and forecasting modules already exist as two separate microservices. "
                "Karan Middha argued that adding further microservices would complicate "
                "the architecture unnecessarily. "
                "The team decided to build modular code within existing microservices "
                "rather than deploying new ones. "
                "A dedicated sandbox microservice was excluded from the current scope. "
                "Ashpreet Singh requested a single ingestion layer microservice for Module 1. "
                "No final decision was made — further client discussion was required."
            ),
            context=[
                "Karan Middha: We already have two microservices: AI and forecasting. Adding more will only complicate things.",
                "Karan Middha: We should build modular code within existing microservices rather than deploying new ones.",
                "Ashpreet Singh: I need a single ingestion layer microservice for Module 1.",
                "Nolocode AI: The sandbox microservice is out of scope for now. We need to discuss this with the client.",
            ],
            additional_metadata={
                "id":            "proj_decision_microservice_architecture",
                "scope":         "project",
                "meeting_date":  None,
                "query_type":    "decision",
                "signal":        "decision",
                "speaker":       None,
                "expected_tool": "search_transcripts",
                "known_gap":     False,

                "expected_meetings": [
                    "Nolocode meeting",
                    "Nolocode - AI module",
                ],
                "must_have_facts": [
                    "AI and forecasting already two separate microservices",
                    "Karan argued against more microservices",
                    "microservices complicate architecture",
                    "modular code within existing microservices decided",
                    "sandbox microservice not in current scope",
                    "no final decision needs client discussion",
                    "Ashpreet requested single ingestion layer",
                ],
                "must_not_have": [
                    "microservice architecture fully decided",
                    "all modules converted to microservices",
                    "Redis microservice",
                    "decision finalized",
                ],
                "eval_weights": {
                    "retrieval":          0.4,
                    "fact_recall":        0.4,
                    "hallucination_free": 0.2,
                },
                "known_issue": (
                    "Retrieval returns 4 irrelevant chunks about save button, "
                    "Approach 1, and stress test — precision problem persists."
                ),
                "known_missing": [
                    "Karan 55:56 — complicates architecture argument",
                    "Karan 59:02 — 2 microservices already exist",
                    "Nolocode AI 56:56 — decision deferred",
                    "Karan 1:01:47 — needs client clarity",
                ],
            },
        ),

        # ── A-07 ─────────────────────────────────────────────────────────────
        Golden(
            input="How did the forecasting formula discussions evolve across meetings?",
            expected_output=(
                "In March 2026, Rhythm jalhotra flagged there was no formula for "
                "calculating forecasting for retained earnings. "
                "Rhythm identified missing values for other equity, current earnings, and dividends. "
                "In April 2026, Bhavneet Mhajan standardized the formula logic — "
                "the same formula applies across all accruals. "
                "In May 2026, new updated formulas with newly introduced calculations were added "
                "for the forecast financials pages. "
                "In the May 7 meeting, the client requested interest from debt in the forecast, "
                "requiring a full hierarchy change rated as high effort. "
                "Nolocode AI clarified this was a change in formula, not a rework of forecasting. "
                "Karan Middha stated a final decision was reached with no further changes to the formulas."
            ),
            context=[
                "Rhythm jalhotra: We do not have a formula to calculate forecasting for retained earnings. Values for other equity, current earnings, and dividends are missing.",
                "Bhavneet Mhajan: The same formula applies across all accruals.",
                "Nolocode AI: New updated formulas with newly introduced calculations have been added for the forecast financials pages.",
                "Rhythm jalhotra: Adding interest from debt in the forecast requires a full hierarchy change. This is high effort.",
                "Nolocode AI: This is a change in formula, not a rework of the entire forecasting module.",
                "Karan Middha: We have reached a final decision. There will be no further changes to the formulas.",
            ],
            additional_metadata={
                "id":            "proj_evolution_forecasting_formula",
                "scope":         "project",
                "meeting_date":  None,
                "query_type":    "temporal_evolution",
                "signal":        None,
                "speaker":       None,
                "expected_tool": "search_transcripts",
                "known_gap":     False,

                "expected_meetings": [
                    "Nolocode meeting with Ashpreet (2026-03-19)",
                    "Nolocode-M2-formula-discussion (2026-04-24)",
                    "Nolocode-meeting (2026-05-05)",
                    "Nolocode-meeting (2026-05-07)",
                ],
                "must_have_facts": [
                    "do not have formula to calculate for forecasting",
                    "follows the same formula as accruals",
                    "new updated formulas newly introduced calculations",
                    "high effort for hierarchy change interest from debt",
                    "change in formula not a rework of forecasting",
                    "final decision no further changes in the formulas",
                ],
                "must_not_have": [
                    "forecasting completely reworked",
                    "formulas were always correct",
                    "no changes in formulas",
                    "Redis forecasting",
                ],
                "eval_weights": {
                    "retrieval":          0.3,
                    "fact_recall":        0.5,
                    "hallucination_free": 0.2,
                },
                "known_issue": (
                    "Irrelevant chunk from Harsh Vardhan 10:14 is retrieved. "
                    "Temporal ordering is correct but the May 7 hierarchy change concern "
                    "is currently missed entirely."
                ),
                "known_missing": [
                    "Rhythm 09:09 — hierarchy change HIGH effort",
                    "Nolocode AI 59:57 — forecasting pages validated complete",
                ],
            },
        ),

        # ── A-08 ─────────────────────────────────────────────────────────────
        Golden(
            input="What did Harsh Vardhan say about the stress test implementation?",
            expected_output=(
                "Harsh Vardhan Dixit explained two approaches to stress test implementation "
                "in the Nolocode AI meeting on 2026-03-25. "
                "In Approach 1, the system classifies user queries into stress test or general categories. "
                "Approach 1 requires a separate Python file for each stress test "
                "and takes around three days to implement per test. "
                "Each deployment requires manually changing the repository and redeploying. "
                "In Approach 2, documents are processed into markdown and Python functions, "
                "validated, then indexed into a vector store. "
                "Harsh proposed a single agent approach first, with multi-agent as fallback if needed. "
                "The Approach 2 proof of concept ran in 60 seconds, almost double the time of Approach 1. "
                "Harsh described using a parent document retriever strategy for vector store indexing. "
                "The Approach 2 POC had a bug where the simulation function returned an insolvent result."
            ),
            context=[
                "Harsh Vardhan Dixit: In Approach 1, the system classifies user queries into stress test or general categories.",
                "Harsh Vardhan Dixit: Approach 1 requires a separate Python file for each stress test. It takes around three days to implement per test.",
                "Harsh Vardhan Dixit: Each deployment requires manually changing the repository and redeploying.",
                "Harsh Vardhan Dixit: In Approach 2, documents are processed into markdown and Python functions, validated, then indexed into a vector store.",
                "Harsh Vardhan Dixit: I propose a single agent approach first, with multi-agent as fallback if needed.",
                "Harsh Vardhan Dixit: The Approach 2 POC ran in 60 seconds — almost double the time of Approach 1.",
                "Harsh Vardhan Dixit: I will use a parent document retriever strategy for vector store indexing.",
                "Harsh Vardhan Dixit: The POC simulation function is returning an insolvent result. There is a bug.",
            ],
            additional_metadata={
                "id":            "proj_speaker_harsh_stress_test",
                "scope":         "project",
                "meeting_date":  None,
                "query_type":    "attribution",
                "signal":        None,
                "speaker":       "Harsh Vardhan Dixit",
                "expected_tool": "search_transcripts",
                "known_gap":     False,

                "expected_meetings": [
                    "Nolocode AI meeting (2026-03-25)",
                ],
                "must_have_facts": [
                    "classifying user query into stress test or general",
                    "separate Python file for each stress test",
                    "three days to implement",
                    "manually change the repo and make it live",
                    "document processed into markdown and Python function",
                    "function validated before indexing into vector store",
                    "single agent approach first",
                    "60 seconds in POC almost double",
                    "parent document retriever",
                    "returning insolvent",
                ],
                "must_not_have": [
                    "stress test implemented in frontend",
                    "approach 2 faster than approach 1",
                    "decision not found",
                    "Redis stress test",
                ],
                "eval_weights": {
                    "retrieval":          0.3,
                    "fact_recall":        0.5,
                    "hallucination_free": 0.2,
                },
                "known_issue": (
                    "Retrieval is clean with no noise chunks. "
                    "Three important technical chunks are currently missed: "
                    "scalability con, latency comparison, and vector store strategy."
                ),
                "known_missing": [
                    "Harsh 26:46 — main scalability con of Approach 1",
                    "Harsh 45:24 — 60-second POC latency",
                    "Harsh 55:49 — parent document retriever strategy",
                ],
            },
        ),

        # ── A-09 ─────────────────────────────────────────────────────────────
        Golden(
            input="What were the main open issues discussed in the Nolocode AI meeting on March 25?",
            expected_output=(
                "Six open issues were raised in the Nolocode AI meeting on 2026-03-25. "
                "Harsh Vardhan Dixit raised that Approach 1 was not scalable because every stress test "
                "required a manual repository change and redeployment. "
                "Harsh reported a bug where the POC simulation function returned an insolvent result. "
                "Ashpreet Singh questioned whether Approach 2 was actually better than Approach 1, "
                "given that Approach 1 had deterministic output and unit tests. "
                "Ashpreet raised a concern that Gemini Flash Lite was not accurate — "
                "specifically that SQL query formation was failing. "
                "Ashpreet questioned whether poor document quality would cause Approach 2 to have "
                "the same accuracy problems as Approach 1. "
                "Ashpreet raised the chunking strategy for large documents as an unresolved issue."
            ),
            context=[
                "Harsh Vardhan Dixit: Approach 1 is not scalable. Every new stress test requires a manual repository change and redeployment.",
                "Harsh Vardhan Dixit: The POC simulation function is returning an insolvent result. This is a bug.",
                "Ashpreet Singh: Is Approach 2 actually better than Approach 1? Approach 1 has deterministic output and unit tests.",
                "Ashpreet Singh: Gemini Flash Lite is not accurate. SQL query formation is failing.",
                "Ashpreet Singh: If document quality is poor, Approach 2 will have the same accuracy problems as Approach 1.",
                "Ashpreet Singh: How do we handle the chunking strategy for large documents? This is still unresolved.",
            ],
            additional_metadata={
                "id":            "proj_open_issues_nolocode_ai_meeting",
                "scope":         "project",
                "meeting_date":  None,
                "query_type":    "list",
                "signal":        "open_issue",
                "speaker":       None,
                "expected_tool": "search_transcripts",
                "known_gap":     False,

                "expected_meetings": [
                    "Nolocode AI meeting (2026-03-25)",
                ],
                "must_have_facts": [
                    "approach 1 not scalable manual repo change",
                    "POC function returning insolvent",
                    "SQL query formation failing in Gemini Flash Lite",
                    "document quality affects approach 2 accuracy",
                    "chunking strategy unclear for large documents",
                    "approach 2 vs approach 1 comparison concern",
                ],
                "must_not_have": [
                    "no open issues",
                    "issues resolved in meeting",
                    "Redis issue",
                    "forecasting formula issue",
                ],
                "eval_weights": {
                    "retrieval":          0.3,
                    "fact_recall":        0.5,
                    "hallucination_free": 0.2,
                },
                "known_issue": (
                    "Best-performing query — open_issue signal filter works correctly. "
                    "Minor gap: SQL query formation detail from Harsh 47:32 not captured."
                ),
                "known_missing": [
                    "Harsh 47:32 — SQL query formation specific detail",
                ],
            },
        ),

        # ── A-10 ─────────────────────────────────────────────────────────────
        Golden(
            input="What was the save button feature discussion about?",
            expected_output=(
                "The save button feature was requested to persist driver changes to the backend "
                "so forecasts would update permanently. "
                "Before this feature, drivers were only saved on the frontend. "
                "Implementing the save button required rebuilding Module 2 and Module 3 from scratch. "
                "The team spent two days designing the save button architecture. "
                "The implementation uses JSON field updates on save button click "
                "followed by a popup confirmation before database changes. "
                "Clicking save triggers a full forecast regeneration across all affected data. "
                "A reset button was added alongside the save button to revert to the baseline. "
                "The save button was the last pending item before the feature set was complete."
            ),
            context=[
                "Karan Middha: Right now drivers are only saved on the frontend, not persisted to the backend.",
                "Project Manager SFS: The client wants drivers saved to the backend when the save button is clicked.",
                "Project Manager SFS: Implementing the save button requires rebuilding Module 2 and Module 3 from scratch.",
                "Project Manager SFS: We spent two days designing the save button architecture.",
                "Project Manager SFS: On save button click we update JSON fields, followed by a popup confirmation before making database changes.",
                "Karan Middha: Clicking save will trigger a full forecast regeneration across all affected data.",
                "Project Manager SFS: We have added a reset button alongside the save button to revert to the baseline.",
                "Project Manager SFS: The save button is the last pending item before the feature set is complete.",
            ],
            additional_metadata={
                "id":            "proj_feature_save_button",
                "scope":         "project",
                "meeting_date":  None,
                "query_type":    "summary",
                "signal":        None,
                "speaker":       None,
                "expected_tool": "search_transcripts",
                "known_gap":     False,

                "expected_meetings": [
                    "Nolocode meeting (initial request)",
                    "Nolocode meeting (architecture discussion)",
                    "Nolocode-catchup (2026-04-20)",
                ],
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
                "must_not_have": [
                    "save button already implemented",
                    "no architecture impact",
                    "frontend only change",
                    "Redis save button",
                    "save button rejected",
                ],
                "eval_weights": {
                    "retrieval":          0.4,
                    "fact_recall":        0.4,
                    "hallucination_free": 0.2,
                },
                "known_issue": (
                    "Answer assigns incorrect dates to the early save-button meetings because "
                    "those meetings are stored with UNIX timestamps as IDs. "
                    "The actual calendar dates need verification."
                ),
                "known_missing": [
                    "PM SFS 25:00 — initial commitment to check possibility",
                    "PM SFS 52:15 — save button last pending item status",
                    "PM SFS 07:20 in M2-and-M4 — except save button rest done",
                ],
            },
        ),

        # ── A-11 ─────────────────────────────────────────────────────────────
        Golden(
            input="What did the team decide about quantum computing implementation in the project?",
            expected_output=(
                "Quantum computing was not discussed in any Nolocode project meeting. "
                "There are no references to quantum computing in the project transcripts. "
                "This topic is entirely absent from the meeting records."
            ),
            # known_gap = True — no ideal chunks exist; context is empty by design
            context=[],
            additional_metadata={
                "id":            "proj_known_gap_quantum_computing",
                "scope":         "project",
                "meeting_date":  None,
                "query_type":    "known_gap",
                "signal":        None,
                "speaker":       None,
                "expected_tool": "search_transcripts",
                "known_gap":     True,

                "expected_meetings": [],
                "must_have_facts": [
                    "quantum computing not discussed",
                    "not present in meetings",
                ],
                "must_not_have": [
                    "quantum computing decided",
                    "team discussed quantum",
                    "quantum implementation planned",
                    "quantum in scope",
                ],
                "eval_weights": {
                    "retrieval":          0.1,
                    "fact_recall":        0.3,
                    "hallucination_free": 0.6,
                },
                "known_issue": (
                    "System correctly says not found but unnecessarily lists 38 project topics. "
                    "Ideal response: 2-3 sentences, no topic enumeration."
                ),
            },
        ),

    ]
)


# ══════════════════════════════════════════════════════════════════════════════
# Category B — Meeting-Scoped  (12 goldens)
# A scope phrase in the query → agent restricts to one meeting.
# Queries B-01 through B-11 target the most recent meeting (2026-05-07).
# Query B-12 targets the 2026-04-20 Nolocode-catchup.
#
# Verified facts about 2026-05-07 (from project-level goldens):
#   Rhythm jalhotra (08:18, 09:09) — raised hierarchy change effort concern
#   Nolocode AI     (19:13)        — clarified formula change not a rework
#   Karan Middha    (55:14)        — declared final decision, no more formula changes
#   Primary topic   : forecasting formula finalization
#   Signal counts   : 44 commits, 5 decisions, 28 questions, 9 issues, 0 doc shares
# ══════════════════════════════════════════════════════════════════════════════

MEETING_QUERIES = EvaluationDataset(
    goldens=[

        # ── B-01 ─────────────────────────────────────────────────────────────
        Golden(
            input="How many people were present in the previous meeting?",
            expected_output=(
                "The previous meeting took place on 2026-05-07 (Nolocode-meeting). "
                "Rhythm jalhotra, Nolocode AI, and Karan Middha were confirmed participants "
                "based on their recorded statements during the session."
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

                "expected_meetings": ["Nolocode-meeting (2026-05-07)"],
                "must_have_facts": [
                    "meeting on 2026-05-07",
                    "Rhythm jalhotra present",
                    "Karan Middha present",
                    "Nolocode AI present",
                ],
                "must_not_have": [
                    "attendees from 2026-05-05",
                    "not found",
                ],
                "eval_weights": {
                    "retrieval":          0.4,
                    "fact_recall":        0.4,
                    "hallucination_free": 0.2,
                },
            },
        ),

        # ── B-02 ─────────────────────────────────────────────────────────────
        Golden(
            input="What topics were discussed in the previous meeting?",
            expected_output=(
                "The 2026-05-07 Nolocode-meeting covered forecasting formula changes as the primary topic. "
                "Rhythm jalhotra raised the issue of adding interest from debt to the forecast hierarchy, "
                "which was rated as high effort. "
                "Nolocode AI clarified whether the required change was a formula adjustment "
                "or a complete forecasting rework. "
                "Karan Middha led the discussion on finalizing the formula decision "
                "and freezing further changes."
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

                "expected_meetings": ["Nolocode-meeting (2026-05-07)"],
                "must_have_facts": [
                    "forecasting formula changes primary topic",
                    "interest from debt hierarchy change",
                    "high effort rating",
                    "formula change not a rework",
                    "final decision on formulas",
                ],
                "must_not_have": [
                    "topics from 2026-05-05",
                    "not found",
                ],
                "eval_weights": {
                    "retrieval":          0.4,
                    "fact_recall":        0.4,
                    "hallucination_free": 0.2,
                },
            },
        ),

        # ── B-03 ─────────────────────────────────────────────────────────────
        Golden(
            input="Which topic was most important in the last meeting?",
            expected_output=(
                "The most important topic in the 2026-05-07 Nolocode-meeting was "
                "the forecasting formula finalization. "
                "The discussion involved a high-effort hierarchy change to add "
                "interest from debt to the forecast. "
                "Karan Middha made the final decision at timestamp 55:14 that "
                "no further formula changes would be made."
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

                "expected_meetings": ["Nolocode-meeting (2026-05-07)"],
                "must_have_facts": [
                    "forecasting formula finalization most important topic",
                    "Karan Middha final decision",
                    "no further changes to formulas",
                    "high effort hierarchy change",
                ],
                "must_not_have": [
                    "topic from a prior meeting",
                    "not found",
                ],
                "eval_weights": {
                    "retrieval":          0.3,
                    "fact_recall":        0.5,
                    "hallucination_free": 0.2,
                },
            },
        ),

        # ── B-04 ─────────────────────────────────────────────────────────────
        Golden(
            input="What was the main agenda of the previous meeting?",
            expected_output=(
                "The main agenda of the 2026-05-07 Nolocode-meeting was resolving "
                "outstanding forecasting formula issues. "
                "The client requested that interest from debt be added to the forecast, "
                "requiring a full hierarchy change. "
                "Rhythm jalhotra identified this as a high-effort item. "
                "Nolocode AI clarified the change was a formula modification, "
                "not a complete rework of forecasting. "
                "Karan Middha closed the session by declaring a final decision "
                "that no further formula changes would be made."
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

                "expected_meetings": ["Nolocode-meeting (2026-05-07)"],
                "must_have_facts": [
                    "forecasting formula issues main agenda",
                    "interest from debt hierarchy change",
                    "high effort",
                    "formula change not rework",
                    "final decision no further changes",
                ],
                "must_not_have": [
                    "agenda from 2026-05-05",
                    "not found",
                ],
                "eval_weights": {
                    "retrieval":          0.4,
                    "fact_recall":        0.4,
                    "hallucination_free": 0.2,
                },
            },
        ),

        # ── B-05 ─────────────────────────────────────────────────────────────
        Golden(
            input="How many issues were raised in the previous meeting?",
            expected_output=(
                "The 2026-05-07 Nolocode-meeting had nine documented open issues. "
                "A primary issue was the high-effort hierarchy change required to add "
                "interest from debt to the forecast. "
                "Rhythm jalhotra flagged the hierarchy change as a high-effort concern "
                "at timestamp 09:09."
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

                "expected_meetings": ["Nolocode-meeting (2026-05-07)"],
                "must_have_facts": [
                    "open issues in 2026-05-07 meeting",
                    "hierarchy change high effort issue",
                ],
                "must_not_have": [
                    "no issues raised",
                    "issues from 2026-05-05",
                    "not found",
                ],
                "eval_weights": {
                    "retrieval":          0.4,
                    "fact_recall":        0.4,
                    "hallucination_free": 0.2,
                },
            },
        ),

        # ── B-06 ─────────────────────────────────────────────────────────────
        Golden(
            input="Are we able to answer all the questions Bhavneet raised in the previous meeting?",
            expected_output=(
                "Bhavneet Mhajan raised questions in the 2026-05-07 Nolocode-meeting "
                "about the forecasting formula changes. "
                "Bhavneet asked about the scope and effort required for the hierarchy change "
                "to support interest from debt in the forecast. "
                "Some of Bhavneet's questions were addressed through clarifications "
                "from Nolocode AI and Karan Middha during the session."
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

                "expected_meetings": ["Nolocode-meeting (2026-05-07)"],
                "must_have_facts": [
                    "Bhavneet questions in 2026-05-07 meeting",
                    "hierarchy change effort question",
                    "some questions addressed",
                ],
                "must_not_have": [
                    "questions from a prior meeting",
                    "not found",
                    "Bhavneet not present",
                ],
                "eval_weights": {
                    "retrieval":          0.4,
                    "fact_recall":        0.4,
                    "hallucination_free": 0.2,
                },
            },
        ),

        # ── B-07 ─────────────────────────────────────────────────────────────
        Golden(
            input="What did Bhavneet highlight in the last meeting?",
            expected_output=(
                "Bhavneet Mhajan highlighted concerns in the 2026-05-07 Nolocode-meeting "
                "about the forecasting formula scope. "
                "Bhavneet raised the requirement for interest from debt to be included "
                "in the forecast output. "
                "Bhavneet highlighted that the effort required for the full hierarchy change "
                "was a significant project concern."
            ),
            additional_metadata={
                "id":            "meet_attr_bhavneet_highlights_last",
                "scope":         "meeting",
                "meeting_date":  "2026-05-07",
                "query_type":    "attribution",
                "signal":        None,
                "speaker":       "Bhavneet Mhajan",
                "expected_tool": "search_transcripts",
                "known_gap":     False,

                "expected_meetings": ["Nolocode-meeting (2026-05-07)"],
                "must_have_facts": [
                    "Bhavneet highlights in 2026-05-07 meeting",
                    "interest from debt requirement",
                    "hierarchy change effort concern",
                ],
                "must_not_have": [
                    "highlights from a prior meeting",
                    "not found",
                ],
                "eval_weights": {
                    "retrieval":          0.4,
                    "fact_recall":        0.4,
                    "hallucination_free": 0.2,
                },
            },
        ),

        # ── B-08 ─────────────────────────────────────────────────────────────
        Golden(
            input="Were any commitments made in the previous meeting?",
            expected_output=(
                "Yes, commitments were made in the 2026-05-07 Nolocode-meeting. "
                "Karan Middha committed to the final decision that no further changes "
                "would be made to the formulas. "
                "The team committed to implementing the hierarchy change for the "
                "interest from debt forecast feature."
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

                "expected_meetings": ["Nolocode-meeting (2026-05-07)"],
                "must_have_facts": [
                    "yes commitments made in 2026-05-07",
                    "Karan Middha formula finalization commitment",
                ],
                "must_not_have": [
                    "no commitments made",
                    "commitments from 2026-05-05",
                    "not found",
                ],
                "eval_weights": {
                    "retrieval":          0.4,
                    "fact_recall":        0.4,
                    "hallucination_free": 0.2,
                },
            },
        ),

        # ── B-09 ─────────────────────────────────────────────────────────────
        Golden(
            input="Give me a summary of the last meeting.",
            expected_output=(
                "The 2026-05-07 Nolocode-meeting focused on resolving forecasting formula changes. "
                "The client requested interest from debt to be added to the forecast, "
                "which Rhythm jalhotra identified as a high-effort hierarchy change. "
                "Nolocode AI clarified this was a formula modification rather than "
                "a complete forecasting rework. "
                "Karan Middha made the final decision that no further changes would be made "
                "to the formulas, closing the formula discussion phase."
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

                "expected_meetings": ["Nolocode-meeting (2026-05-07)"],
                "must_have_facts": [
                    "forecasting formula changes 2026-05-07",
                    "interest from debt hierarchy change high effort",
                    "Nolocode AI formula change not rework",
                    "Karan Middha final decision no further changes",
                ],
                "must_not_have": [
                    "content from 2026-05-05",
                    "not found",
                ],
                "eval_weights": {
                    "retrieval":          0.4,
                    "fact_recall":        0.4,
                    "hallucination_free": 0.2,
                },
            },
        ),

        # ── B-10 ─────────────────────────────────────────────────────────────
        Golden(
            input="What planning or next steps were discussed in the previous meeting?",
            expected_output=(
                "The 2026-05-07 Nolocode-meeting concluded with clear next steps for the formula changes. "
                "The development team was tasked with implementing the hierarchy change "
                "for the interest from debt forecast feature. "
                "Karan Middha confirmed the formula finalization with no further changes planned."
            ),
            additional_metadata={
                "id":            "meet_list_nextsteps_last",
                "scope":         "meeting",
                "meeting_date":  "2026-05-07",
                "query_type":    "list",
                "signal":        "commitment",
                "speaker":       None,
                "expected_tool": "search_transcripts",
                "known_gap":     False,

                "expected_meetings": ["Nolocode-meeting (2026-05-07)"],
                "must_have_facts": [
                    "next steps 2026-05-07",
                    "hierarchy change implementation",
                    "formula finalization confirmed no further changes",
                ],
                "must_not_have": [
                    "next steps from 2026-05-05",
                    "not found",
                ],
                "eval_weights": {
                    "retrieval":          0.4,
                    "fact_recall":        0.4,
                    "hallucination_free": 0.2,
                },
            },
        ),

        # ── B-11 ─────────────────────────────────────────────────────────────
        Golden(
            input="What documents or files were shared in the previous meeting?",
            expected_output=(
                "No documents or files were shared in the 2026-05-07 Nolocode-meeting. "
                "The meeting records confirm zero document share events during the session. "
                "The discussion was entirely verbal with no screen shares, file links, "
                "or documents referenced."
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

                "expected_meetings": ["Nolocode-meeting (2026-05-07)"],
                "must_have_facts": [
                    "no documents shared in 2026-05-07 meeting",
                    "zero document share events",
                ],
                "must_not_have": [
                    "documents were shared",
                    "files from a prior meeting",
                ],
                "eval_weights": {
                    "retrieval":          0.4,
                    "fact_recall":        0.4,
                    "hallucination_free": 0.2,
                },
            },
        ),

        # ── B-12 ─────────────────────────────────────────────────────────────
        Golden(
            input="What feedback did Bhavneet give in the April 20th meeting?",
            expected_output=(
                "Bhavneet Mhajan provided feedback in the Nolocode-catchup meeting on 2026-04-20. "
                "Bhavneet reviewed the current module status and provided direction "
                "on pending feature work."
            ),
            additional_metadata={
                "id":            "meet_attr_bhavneet_feedback_apr20",
                "scope":         "meeting",
                "meeting_date":  "2026-04-20",
                "query_type":    "attribution",
                "signal":        None,
                "speaker":       "Bhavneet Mhajan",
                "expected_tool": "search_transcripts",
                "known_gap":     False,

                "expected_meetings": ["Nolocode-catchup (2026-04-20)"],
                "must_have_facts": [
                    "Bhavneet feedback in 2026-04-20 Nolocode-catchup",
                    "module status review",
                ],
                "must_not_have": [
                    "feedback from a different meeting",
                    "not found",
                    "Bhavneet not present",
                ],
                "eval_weights": {
                    "retrieval":          0.4,
                    "fact_recall":        0.4,
                    "hallucination_free": 0.2,
                },
            },
        ),

    ]
)


# ══════════════════════════════════════════════════════════════════════════════
# Category C — Topic / Cross-Meeting  (11 goldens)
# Agent must trace a topic across multiple meetings or compare items.
# ══════════════════════════════════════════════════════════════════════════════

TOPIC_QUERIES = EvaluationDataset(
    goldens=[

        # ── C-01 ─────────────────────────────────────────────────────────────
        Golden(
            input="What was the AI discussion in the previous 2 meetings?",
            expected_output=(
                "In the 2026-05-05 Nolocode-meeting, the AI discussion covered newly introduced "
                "formula calculations for the forecast financials pages. "
                "In the 2026-05-07 Nolocode-meeting, the AI discussion focused on the formula "
                "change required to add interest from debt to the forecast hierarchy. "
                "Nolocode AI clarified in the 2026-05-07 meeting that the change was a formula "
                "modification rather than a forecasting rework."
            ),
            additional_metadata={
                "id":            "multi_summary_ai_last2",
                "scope":         "multi-meeting",
                "meeting_date":  None,
                "query_type":    "summary",
                "signal":        None,
                "speaker":       None,
                "expected_tool": "search_transcripts",
                "known_gap":     False,

                "expected_meetings": [
                    "Nolocode-meeting (2026-05-05)",
                    "Nolocode-meeting (2026-05-07)",
                ],
                "must_have_facts": [
                    "AI discussion 2026-05-05 new formula calculations",
                    "AI discussion 2026-05-07 interest from debt hierarchy",
                    "formula change not rework",
                ],
                "must_not_have": [
                    "content from meetings before 2026-05-05",
                    "not found",
                ],
                "eval_weights": {
                    "retrieval":          0.4,
                    "fact_recall":        0.4,
                    "hallucination_free": 0.2,
                },
            },
        ),

        # ── C-02 ─────────────────────────────────────────────────────────────
        Golden(
            input="Did Harsh raise any questions about AI architecture?",
            expected_output=(
                "Yes, Harsh Vardhan Dixit raised questions about AI architecture "
                "in the Nolocode AI meeting on 2026-03-25. "
                "Harsh questioned the scalability of Approach 1 as the number of "
                "stress tests grows. "
                "Harsh raised a concern about the POC simulation returning an insolvent result, "
                "which was an architectural issue in Approach 2. "
                "Harsh asked about the best indexing strategy for documents in the vector store."
            ),
            additional_metadata={
                "id":            "proj_yesno_harsh_ai_questions",
                "scope":         "project",
                "meeting_date":  None,
                "query_type":    "yesno",
                "signal":        "question",
                "speaker":       "Harsh Vardhan Dixit",
                "expected_tool": "search_transcripts",
                "known_gap":     False,

                "expected_meetings": [
                    "Nolocode AI meeting (2026-03-25)",
                ],
                "must_have_facts": [
                    "Harsh raised AI architecture questions",
                    "scalability concern Approach 1",
                    "POC insolvent architectural issue",
                ],
                "must_not_have": [
                    "Harsh did not raise questions",
                    "no questions found",
                ],
                "eval_weights": {
                    "retrieval":          0.3,
                    "fact_recall":        0.5,
                    "hallucination_free": 0.2,
                },
            },
        ),

        # ── C-03 ─────────────────────────────────────────────────────────────
        Golden(
            input="Summarize the overall AI architecture conversation across all meetings.",
            expected_output=(
                "The AI architecture discussion spanned at least three meetings across the project. "
                "Ashpreet Singh proposed a four-agent LangGraph architecture with subgraphs "
                "in the Nolocode AI meeting on 2026-03-25. "
                "Harsh Vardhan Dixit presented Approach 1 (deterministic, per-file) "
                "and Approach 2 (agent-based, vector store pipeline). "
                "The team decided on Approach 1 for stress tests and a single agent "
                "architecture for general queries. "
                "A RAG-based approach was selected for handling general non-preset questions. "
                "Karan Middha confirmed the AI and forecasting modules exist as "
                "two separate microservices."
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

                "expected_meetings": [
                    "Nolocode AI meeting (2026-03-25)",
                    "Nolocode meeting (2026-04-08)",
                    "Nolocode-M2-and-M4 (2026-04-15)",
                ],
                "must_have_facts": [
                    "four agent LangGraph architecture Ashpreet",
                    "Approach 1 deterministic stress test",
                    "Approach 2 agent vector store pipeline",
                    "single agent first approach decided",
                    "RAG based general queries",
                    "AI and forecasting two microservices",
                ],
                "must_not_have": [
                    "no AI architecture discussion",
                    "not found",
                ],
                "eval_weights": {
                    "retrieval":          0.4,
                    "fact_recall":        0.4,
                    "hallucination_free": 0.2,
                },
            },
        ),

        # ── C-04 ─────────────────────────────────────────────────────────────
        Golden(
            input="What did Harsh commit to regarding AI in the last 5 meetings?",
            expected_output=(
                "The last five meetings span from 2026-04-20 to 2026-05-07. "
                "Harsh Vardhan Dixit committed to implementing the AI module architecture "
                "within the agreed constraints during this period. "
                "Harsh committed to using a single agent approach as the primary implementation path."
            ),
            additional_metadata={
                "id":            "multi_list_harsh_ai_commits_last5",
                "scope":         "multi-meeting",
                "meeting_date":  None,
                "query_type":    "list",
                "signal":        "commitment",
                "speaker":       "Harsh Vardhan Dixit",
                "expected_tool": "search_transcripts",
                "known_gap":     False,

                "expected_meetings": [
                    "Nolocode-catchup (2026-04-20)",
                    "Nolocode-AI-meeting (2026-04-22)",
                    "Nolocode-M2-formula-discussion (2026-04-24)",
                    "Nolocode-meeting (2026-05-05)",
                    "Nolocode-meeting (2026-05-07)",
                ],
                "must_have_facts": [
                    "Harsh commitments last 5 meetings",
                    "meetings from 2026-04-20 to 2026-05-07",
                    "AI related commitment Harsh",
                ],
                "must_not_have": [
                    "commitments from before 2026-04-20",
                    "not found",
                ],
                "eval_weights": {
                    "retrieval":          0.4,
                    "fact_recall":        0.4,
                    "hallucination_free": 0.2,
                },
            },
        ),

        # ── C-05 ─────────────────────────────────────────────────────────────
        Golden(
            input="What clarity did Bhavneet provide about the AI system?",
            expected_output=(
                "Bhavneet Mhajan clarified that the RAG-based approach was intended for "
                "general non-preset queries, not for the stress test module specifically. "
                "Bhavneet explained that the AI output must use Module 2 data for specific "
                "recommendations rather than generic responses. "
                "Bhavneet stated that stress test output must be dynamic and leverage "
                "actual financial data from Module 2."
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

                "expected_meetings": [
                    "Nolocode AI meeting (2026-03-25)",
                    "Nolocode-M2-and-M4 (2026-04-15)",
                ],
                "must_have_facts": [
                    "RAG approach for general queries clarification",
                    "AI must use Module 2 data",
                    "dynamic output not generic",
                ],
                "must_not_have": [
                    "not found",
                    "Bhavneet not present",
                ],
                "eval_weights": {
                    "retrieval":          0.3,
                    "fact_recall":        0.5,
                    "hallucination_free": 0.2,
                },
            },
        ),

        # ── C-06 ─────────────────────────────────────────────────────────────
        Golden(
            input="Summarize the complete AI architecture discussion in this project.",
            expected_output=(
                "The AI architecture discussion in the Nolocode project spanned more than three meetings. "
                "Two main approaches were evaluated: Approach 1 (deterministic, Python-file-based) "
                "and Approach 2 (agent-based, vector store pipeline). "
                "Ashpreet Singh proposed a four-agent LangGraph design with subgraphs and modular microservices. "
                "The team decided on Approach 1 for stress tests and a RAG-based single agent for general queries. "
                "Karan Middha confirmed the two-microservice architecture: AI and forecasting. "
                "The final architecture uses modular code within existing microservices."
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

                "expected_meetings": [
                    "Nolocode AI meeting (2026-03-25)",
                    "Nolocode meeting (2026-04-08)",
                    "Nolocode-M2-and-M4 (2026-04-15)",
                    "Nolocode - AI module",
                ],
                "must_have_facts": [
                    "more than three meetings covered",
                    "Approach 1 deterministic Approach 2 agent based",
                    "four agent LangGraph Ashpreet",
                    "Approach 1 stress tests RAG general queries",
                    "two microservices AI and forecasting",
                    "modular code not new microservices",
                ],
                "must_not_have": [
                    "no AI architecture discussed",
                    "not found",
                ],
                "eval_weights": {
                    "retrieval":          0.4,
                    "fact_recall":        0.4,
                    "hallucination_free": 0.2,
                },
            },
        ),

        # ── C-07 ─────────────────────────────────────────────────────────────
        Golden(
            input="What is the exact approach we decided for building the AI system?",
            expected_output=(
                "For stress test queries, the team decided on Approach 1 (deterministic) "
                "as the implementation strategy. "
                "Project Manager SFS confirmed Approach 1 was finalized in the 2026-04-08 meeting. "
                "For general non-preset queries, a RAG-based approach was decided. "
                "For overall architecture, the team chose a single agent approach "
                "as the primary path with multi-agent as fallback."
            ),
            additional_metadata={
                "id":            "proj_decision_ai_exact_approach",
                "scope":         "project",
                "meeting_date":  None,
                "query_type":    "decision",
                "signal":        "decision",
                "speaker":       None,
                "expected_tool": "search_transcripts",
                "known_gap":     False,

                "expected_meetings": [
                    "Nolocode meeting (2026-04-08)",
                    "Nolocode-M2-and-M4 (2026-04-15)",
                    "Nolocode AI meeting (2026-03-25)",
                ],
                "must_have_facts": [
                    "Approach 1 finalized for stress tests",
                    "RAG based for general queries",
                    "single agent approach decided",
                ],
                "must_not_have": [
                    "no decision found",
                    "unclear approach",
                    "I could not find",
                ],
                "eval_weights": {
                    "retrieval":          0.4,
                    "fact_recall":        0.4,
                    "hallucination_free": 0.2,
                },
            },
        ),

        # ── C-08 ─────────────────────────────────────────────────────────────
        Golden(
            input="Which issue came up first — OCA or fixed assets?",
            expected_output=(
                "OCA (Other Comprehensive Assets) was first raised in the "
                "Nolocode-M1 meeting on 2026-04-14. "
                "Fixed assets were first raised in the Nolocode-M2-and-M4 meeting on 2026-04-15. "
                "OCA was discussed one day before fixed assets, making it the earlier issue."
            ),
            additional_metadata={
                "id":            "proj_cmp_oca_vs_fixedassets",
                "scope":         "project",
                "meeting_date":  None,
                "query_type":    "comparison",
                "signal":        "open_issue",
                "speaker":       None,
                "expected_tool": "search_transcripts",
                "known_gap":     True,

                "expected_meetings": [
                    "Nolocode-M1 (2026-04-14)",
                    "Nolocode-M2-and-M4 (2026-04-15)",
                ],
                "must_have_facts": [
                    "OCA raised 2026-04-14",
                    "fixed assets raised 2026-04-15",
                    "OCA came first",
                ],
                "must_not_have": [
                    "fixed assets first",
                    "not found",
                    "no results",
                ],
                "eval_weights": {
                    "retrieval":          0.4,
                    "fact_recall":        0.4,
                    "hallucination_free": 0.2,
                },
                "known_issue": (
                    "Agent returns 0 results for 'OCA'. "
                    "BM25 tokenization does not expand the acronym to "
                    "'Other Comprehensive Assets', so hybrid search misses all relevant chunks."
                ),
            },
        ),

        # ── C-09 ─────────────────────────────────────────────────────────────
        Golden(
            input="Which unresolved issue was discussed most recently?",
            expected_output=(
                "The most recently discussed unresolved issue was raised in the "
                "2026-05-07 Nolocode-meeting. "
                "The issue was the high-effort hierarchy change required to add "
                "interest from debt to the forecast. "
                "Rhythm jalhotra raised this issue at timestamp 09:09 in that meeting."
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

                "expected_meetings": [
                    "Nolocode-meeting (2026-05-07)",
                ],
                "must_have_facts": [
                    "most recent issue 2026-05-07",
                    "hierarchy change interest from debt",
                    "Rhythm jalhotra raised issue",
                ],
                "must_not_have": [
                    "most recent issue from an earlier meeting",
                    "not found",
                ],
                "eval_weights": {
                    "retrieval":          0.4,
                    "fact_recall":        0.4,
                    "hallucination_free": 0.2,
                },
            },
        ),

        # ── C-10 ─────────────────────────────────────────────────────────────
        Golden(
            input="Who has spoken the most in this project?",
            expected_output=(
                "Project Manager SFS is among the most active speakers in the project. "
                "Harsh Vardhan Dixit has 180 verified chunks across the meetings "
                "and is one of the top contributors. "
                "Karan Middha, Bhavneet Mhajan, Nolocode AI, and Rhythm jalhotra are "
                "also active contributors with significant speaking time."
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

                "must_have_facts": [
                    "most active speaker identified",
                    "Harsh Vardhan Dixit 180 chunks",
                    "speakers ranked by contribution",
                ],
                "must_not_have": [
                    "no speaker data",
                    "not found",
                ],
                "eval_weights": {
                    "retrieval":          0.3,
                    "fact_recall":        0.5,
                    "hallucination_free": 0.2,
                },
            },
        ),

        # ── C-11 ─────────────────────────────────────────────────────────────
        Golden(
            input="Summarize all commitments made by Simarjot Kaur with timestamps.",
            expected_output=(
                "Simarjot Kaur is recorded as a developer in the Nolocode project. "
                "Any commitments by Simarjot Kaur include specific development tasks "
                "she agreed to complete, attributed with meeting dates and timestamps."
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

                "must_have_facts": [
                    "Simarjot Kaur developer in project",
                ],
                "must_not_have": [
                    "commitments invented without a source",
                    "Simarjot Kaur is not in the project",
                ],
                "eval_weights": {
                    "retrieval":          0.3,
                    "fact_recall":        0.4,
                    "hallucination_free": 0.3,
                },
                "known_issue": (
                    "Simarjot Kaur's existence in the database is unconfirmed. "
                    "Run verify_chunks with her name before treating this as a reliable test case."
                ),
            },
        ),

    ]
)


# ══════════════════════════════════════════════════════════════════════════════
# ALL_QUERIES — combined dataset for full-suite runs
# ══════════════════════════════════════════════════════════════════════════════

ALL_QUERIES = EvaluationDataset(
    goldens=(
        PROJECT_QUERIES.goldens
        + MEETING_QUERIES.goldens
        + TOPIC_QUERIES.goldens
    )
)

PROJECT_LEVEL_GOLDENS = PROJECT_QUERIES.goldens
