import logging
import re
import time
import unicodedata
from typing import Optional

from langchain_core.documents import Document

from app.services.query_intent import (
    QueryIntent,
    QueryUnderstanding,
    understand_query,
    is_metadata_query,
)
from app.services.retrieval.retriever import (
    hybrid_retrieve,
    retrieve_timeline_documents,
    compound_retrieve,
    analytical_retrieve,
    topic_summary_retrieve,
    contribution_retrieve,
)
from app.services.retrieval.reranker import rerank_documents
from app.services.storage.project_store import get_speaker_names
from app.services.answer.builder import (
    EXPAND_TOP_N,
    retrieve_summary_chunks,
    expand_context,
    build_context,
    build_prompt,
    extract_sources,
    build_not_found_message,
)
from app.services.answer.metadata import handle_metadata_query
from app.clients.gemini_client import call_gemini

logger = logging.getLogger(__name__)

_SEP = "-" * 62


def _build_scope_filter(understanding: QueryUnderstanding) -> "dict | None":
    """
    Convert understanding.scope_meeting_ids to a ChromaDB where-clause.
    No DB call — the IDs were already resolved in _post_process_understanding().
    Returns None when scope is project-level (all meetings).
    """
    ids = understanding.scope_meeting_ids
    if not ids:
        return None
    if len(ids) == 1:
        return {"meeting_id": {"$eq": ids[0]}}
    return {"meeting_id": {"$in": ids}}

_TOPIC_ACTION_WORDS = frozenset({
    "confusion", "concern", "question", "issue", "doubt", "problem",
    "decision", "commitment", "update", "change", "summary", "raised",
    "mentioned", "said", "discussed", "asked", "expressed", "noted",
    "around", "about", "regarding", "related", "concerning",
})


def subject_topic_hint(topic: str) -> str:
    """Strip action/connector words from topic so only subject terms remain.
    'CE classification code confusion' → 'CE classification code'
    """
    words = topic.split()
    subject_words = [w for w in words if w.lower() not in _TOPIC_ACTION_WORDS]
    return " ".join(subject_words) if subject_words else topic


def _normalize(text: str) -> str:
    return unicodedata.normalize("NFD", text).encode("ascii", "ignore").decode().lower()


def detect_speaker_name(query: str, project_id: str) -> Optional[str]:
    """
    Scan query for a known speaker name from this project.
    4-level matching (most→least specific, first match wins):
      L1: Full name        "Bhavneet Mhajan"  → exact substring
      L2: First name       "Bhavneet"         → must be >2 chars to avoid false positives
      L3: Last name        "Mhajan"           → must be >3 chars (avoids common words)
      L4: Abbreviation     "B. Mhajan" / "B Mhajan" → first-initial + last-name pattern
    Returns the canonical full name as stored in projects.json, or None.
    """
    names = get_speaker_names(project_id)
    q = _normalize(query)

    # L1: full name
    for name in names:
        if _normalize(name) in q:
            return name

    # L2: first name
    for name in names:
        parts = name.split()
        first = _normalize(parts[0])
        if len(first) > 2 and first in q:
            return name

    # L3: last name (only if unique across speakers — avoids wrong match)
    last_name_map: dict[str, list[str]] = {}
    for name in names:
        parts = name.split()
        if len(parts) >= 2:
            last = _normalize(parts[-1])
            last_name_map.setdefault(last, []).append(name)

    for last, candidates in last_name_map.items():
        if len(last) > 3 and len(candidates) == 1 and last in q:
            return candidates[0]

    # L4: abbreviation "B. Mhajan" or "B Mhajan"
    for name in names:
        parts = name.split()
        if len(parts) >= 2:
            initial = _normalize(parts[0][0])
            last    = _normalize(parts[-1])
            if len(last) > 3 and re.search(
                rf"\b{initial}\.?\s+{last}\b", q
            ):
                return name

    return None


def _retrieve_for_understanding(
    query: str,
    project_id: str,
    understanding: QueryUnderstanding,
) -> tuple[list[Document] | dict, str | None]:
    """
    8-mode dispatch driven by understanding.retrieval_mode (set by ROUTING_RULES).

    Returns (documents_or_structured_dict, notice).
    Modes "analytical" and "contribution" return a dict — pipeline handles them specially.
    All other modes return list[Document].
    """
    mode = understanding.retrieval_mode

    # Scope already resolved in understand_query() — one DB call total, no re-detection.
    date_where = _build_scope_filter(understanding)
    if date_where:
        logger.info(
            "  scope      : %s (%d meeting(s))",
            understanding.scope_type, len(understanding.scope_meeting_ids),
        )

    if mode == "summary":
        return retrieve_summary_chunks(
            project_id, query,
            scope_meeting_ids=understanding.scope_meeting_ids or None,
        )

    if mode == "timeline":
        return retrieve_timeline_documents(
            query, project_id,
            k_per_meeting=6,
            scope_meeting_ids=understanding.scope_meeting_ids or None,
        ), None

    if mode == "compound":
        named_speaker = understanding.named_speaker or detect_speaker_name(query, project_id)
        if not named_speaker:
            return hybrid_retrieve(query, project_id, date_where=date_where, k=25), None
        return compound_retrieve(
            query, project_id,
            named_speaker=named_speaker,
            signal_filter=understanding.signal_filter,
            date_where=date_where,
        ), None

    if mode == "analytical":
        result = analytical_retrieve(
            project_id,
            signal_filter=understanding.signal_filter,
            date_where=date_where,
            named_speaker=understanding.named_speaker,
        )
        return result, None  # dict — handled by _handle_structured_result()

    if mode == "contribution":
        result = contribution_retrieve(project_id, date_where=date_where)
        return result, None  # dict — handled by _handle_structured_result()

    if mode == "topic_summary":
      topic = subject_topic_hint(understanding.topic)
      return topic_summary_retrieve(
        topic, project_id,
        scope_meeting_ids=understanding.scope_meeting_ids or None,  # ← yeh pass ho raha hai?
      ), None

    if mode == "metadata":
        return [], None

    # Default: hybrid
    named_speaker = understanding.named_speaker
    if not named_speaker and understanding.intent_type in (
        QueryIntent.SPEAKER, QueryIntent.QUESTION
    ):
        named_speaker = detect_speaker_name(query, project_id)

    hard_filters: dict = {}
    if named_speaker:
        hard_filters["speaker_name"] = named_speaker
    if understanding.signal_filter:
        hard_filters[f"contains_{understanding.signal_filter}"] = True

    return hybrid_retrieve(
        query, project_id,
        hard_filters=hard_filters or None,
        date_where=date_where,
        k=25,
    ), None


def _handle_structured_result(
    result: dict,
    query: str,
    understanding: QueryUnderstanding,
) -> dict:
    """Build a final answer dict from analytical_retrieve() or contribution_retrieve() results."""
    mode = understanding.retrieval_mode

    if mode == "analytical":
        signal    = result.get("signal_filter")
        speaker   = result.get("named_speaker")
        count     = result["signal_count"] if signal else result["total_chunks"]
        meetings  = result.get("meetings", [])
        speakers  = result.get("speakers", [])
        signal_label = signal or "chunks"

        context_lines = [
            f"Count of {signal_label}: {count}",
            f"Across {result['meeting_count']} meeting(s): {', '.join(meetings[:5])}",
        ]
        if speaker:
            context_lines.append(f"Filtered to speaker: {speaker}")
        if speakers and not speaker:
            context_lines.append(f"Speakers involved: {', '.join(speakers[:8])}")
        context = "\n".join(context_lines)
        intent  = QueryIntent.ANALYTICAL

    else:  # contribution
        ranked = result.get("ranked_speakers", [])
        lines  = [
            f"{i + 1}. {r['speaker_name']} — {r['chunk_count']} segments, "
            f"{r['meeting_count']} meeting(s)"
            for i, r in enumerate(ranked)
        ]
        context = f"Total speakers: {result['total_speakers']}\n" + "\n".join(lines)
        intent  = QueryIntent.CONTRIBUTION

    prompt = build_prompt(query, context, intent, understanding.output_format)
    answer = call_gemini(prompt)

    return {
        "answer":  answer,
        "sources": [],
        "intent":  intent.value,
        "notice":  None,
    }


def _log_retrieval_strategy(understanding: QueryUnderstanding) -> None:
    mode = understanding.retrieval_mode
    logger.info("  strategy   : mode=%s | output_format=%s", mode, understanding.output_format)
    if understanding.named_speaker:
        logger.info("  speaker    : \"%s\" (LLM-canonicalized)", understanding.named_speaker)
    if understanding.signal_filter:
        logger.info("  signal     : %s", understanding.signal_filter)


def answer_question(query: str, project_id: str) -> dict:
    """
    Answer a question using the RAG pipeline.

    Returns:
        {
            "answer": str,
            "sources": list[{meeting_title, meeting_date, speaker_name, timestamp}],
            "intent": str,
            "notice": str | None,
        }
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")
    if not project_id or not project_id.strip():
        raise ValueError("project_id is required.")

    if is_metadata_query(query):
        logger.info("PIPELINE SHORT-CIRCUIT: metadata_query — skipping embedding + LLM")
        return handle_metadata_query(query, project_id)

    t_start = time.time()

    logger.info(_SEP)
    logger.info("PIPELINE START")
    logger.info("  query      : %s", query)
    logger.info("  project    : %s", project_id)
    logger.info(_SEP)

    try:
        # ── STEP 1: understand query ─────────────────────────────────────
        logger.info("[1/5] UNDERSTAND QUERY")
        understanding = understand_query(query, project_id)
        logger.info("  intent     : %s", understanding.intent_type.value)
        intent = understanding.intent_type

        # ── STEP 2: retrieve documents ───────────────────────────────────
        logger.info("[2/5] RETRIEVE  (mode=%s)", understanding.retrieval_mode)
        _log_retrieval_strategy(understanding)
        raw_result, notice = _retrieve_for_understanding(query, project_id, understanding)

        # Structured result (analytical / contribution) — skip RAG steps, answer directly
        if isinstance(raw_result, dict):
            logger.info("  result     : structured dict — routing to _handle_structured_result")
            return _handle_structured_result(raw_result, query, understanding)

        documents: list[Document] = raw_result

        # Use the dedicated template when topic_summary retrieval was used.
        # The LLM returns "summary_query" (not in its options list), so we override here.
        if understanding.retrieval_mode == "topic_summary":
            intent = QueryIntent.TOPIC_SUMMARY

        if not documents:
            logger.info("  result     : no documents found — returning not-found message")
            logger.info(_SEP)
            not_found_msg = build_not_found_message(intent, query, project_id)
            return {
                "answer": not_found_msg,
                "sources": [],
                "intent": intent.value,
                "notice": None,
            }

        # ── STEP 3: re-rank documents ─────────────────────────────────────
        skip_rerank = understanding.retrieval_mode in ("summary", "topic_summary")
        if not skip_rerank:
            logger.info("[3/5] RERANK   (%d candidates)", len(documents))
            documents = rerank_documents(
                query, documents,
                intent_hint=intent.value,
                topic_hint=subject_topic_hint(understanding.topic),
                speaker_hint=understanding.named_speaker or "",
            )
        else:
            logger.info("[3/5] RERANK   skipped (mode=%s — chronological order preserved)",
                        understanding.retrieval_mode)

        # ── STEP 3.5: context expansion ──────────────────────────────────
        # Fetch prev/next neighbors for top-5 re-ranked docs — 10 DB lookups max.
        # Must happen BEFORE the trim so neighbors count toward the final window.
        if not skip_rerank:
            pre_expand = len(documents)
            documents = expand_context(documents, n=EXPAND_TOP_N)
            logger.info(
                "  expanded   : %d → %d docs (neighbors added for top %d)",
                pre_expand, len(documents), EXPAND_TOP_N,
            )

        # ── STEP 3.6: chronological sort for speaker/timeline intents ────
        # Reranker orders by relevance; for speaker/timeline we want the
        # conversation to read in time order so the LLM can build a narrative.
        chrono_modes = (QueryIntent.SPEAKER, QueryIntent.TIMELINE,
                        QueryIntent.TOPIC_SUMMARY, QueryIntent.ATTRIBUTION)
        if intent in chrono_modes or understanding.retrieval_mode in ("compound", "topic_summary", "timeline"):
            documents.sort(key=lambda d: (
                d.metadata.get("meeting_date", ""),
                d.metadata.get("start_time") or 0,
            ))
            logger.info("  sorted     : chronological order for mode=%s", understanding.retrieval_mode)

        # ── STEP 4: build context + prompt ───────────────────────────────
        # Trim to top 10 after expansion. We retrieve 25 candidates so the
        # re-ranker has options; the LLM gets only the most relevant ones.
        _CONTEXT_TOP_N = 10
        if len(documents) > _CONTEXT_TOP_N:
            documents = documents[:_CONTEXT_TOP_N]
            logger.info("  trimmed    : context limited to top %d", _CONTEXT_TOP_N)

        logger.info("[4/5] BUILD PROMPT")
        context = build_context(documents)
        prompt = build_prompt(query, context, intent, understanding.output_format,
                              scope_type=understanding.scope_type)
        logger.info("  docs used  : %d", len(documents))
        logger.info("  context    : %d chars", len(context))
        logger.info("  prompt     : \"%s...\"", prompt[:120].replace("\n", " "))

        # ── STEP 5: call LLM ─────────────────────────────────────────────
        logger.info("[5/5] LLM CALL  (model: gemini-2.5-flash-lite)")
        answer = call_gemini(prompt)
        sources = extract_sources(documents)

        elapsed = time.time() - t_start
        logger.info(_SEP)
        logger.info("PIPELINE DONE  (%.1fs)", elapsed)
        logger.info("  intent     : %s", intent.value)
        logger.info("  sources    : %d unique", len(sources))
        for s in sources:
            logger.info(
                "    -> %s (%s) | %s",
                s["meeting_title"][:40],
                s["meeting_date"],
                s["speaker_name"],
            )
        logger.info("  answer     : \"%s...\"", answer[:150].replace("\n", " "))
        logger.info(_SEP)

        return {
            "answer": answer,
            "sources": sources,
            "intent": intent.value,
            "notice": notice,
        }

    except Exception as e:
        logger.exception("Answer generation failed | query='%s'", query)
        raise RuntimeError(f"Answer generation failed: {str(e)}") from e
