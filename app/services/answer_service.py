"""
answer_service.py — backward-compatibility re-export wrapper.

All logic lives in app/services/answer/:
  scope.py    — temporal / date filtering
  builder.py  — context building, prompts, sources, expand_context
  metadata.py — metadata short-circuit handler
  pipeline.py — RAG flow + answer_question()

External callers import answer_question from here unchanged.
trace_query.py imports private functions — re-exported below with underscore names.
"""
from app.services.answer.pipeline import answer_question  # noqa: F401

# Private re-exports for trace_query.py backwards compatibility
from app.services.answer.pipeline import detect_speaker_name as _detect_speaker_name  # noqa: F401
from app.services.answer.builder import retrieve_summary_chunks as _retrieve_summary_chunks  # noqa: F401
from app.services.answer.builder import build_context as _build_context  # noqa: F401
from app.services.answer.builder import build_prompt as _build_prompt  # noqa: F401
from app.clients.gemini_client import call_gemini as _call_gemini  # noqa: F401
from app.services.answer.builder import extract_sources as _extract_sources  # noqa: F401
