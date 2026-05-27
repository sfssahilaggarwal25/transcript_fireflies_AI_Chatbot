"""app.rag — Deterministic RAG pipeline (Approach 1).

Contains:
  answer/        — Full 5-step pipeline: scope → retrieve → rerank → prompt → LLM
    pipeline.py  — answer_question() entry point
    builder.py   — Context building, prompts, source extraction, context expansion
    metadata.py  — Metadata short-circuit handler (0 LLM calls for simple queries)
  query_intent.py — LLM-first query understanding + 13-rule deterministic routing
  prompts.py      — All answer templates, classifier prompt, understanding prompt
  tests/          — Test suite: test_runner, report_generator, query_bank/

For the agentic pipeline (Approach 2), see app.agent.
"""
