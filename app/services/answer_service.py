"""
answer_service.py — backward-compatibility re-export wrapper.

All logic now lives in app/rag/:
  app/rag/answer/pipeline.py  — RAG flow + answer_question()
  app/rag/answer/builder.py   — context building, prompts, sources, expand_context
  app/rag/answer/metadata.py  — metadata short-circuit handler
  app/core/scope.py           — temporal / date filtering (shared with agent)

External callers (main.py, root scripts) import answer_question from here unchanged.
trace_query.py imports private functions — re-exported below with underscore names.
"""
from app.rag.answer.pipeline import answer_question  # noqa: F401

# Private re-exports for trace_query.py backwards compatibility
from app.rag.answer.pipeline import detect_speaker_name as _detect_speaker_name  # noqa: F401
from app.rag.answer.builder import retrieve_summary_chunks as _retrieve_summary_chunks  # noqa: F401
from app.rag.answer.builder import build_context as _build_context  # noqa: F401
from app.rag.answer.builder import build_prompt as _build_prompt  # noqa: F401
from app.clients.gemini_client import call_gemini as _call_gemini  # noqa: F401
from app.rag.answer.builder import extract_sources as _extract_sources  # noqa: F401
