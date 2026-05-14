import logging
import unicodedata
from typing import Optional

from google import genai
from langchain_core.documents import Document

from app.config import Config
from app.services.query_intent import QueryIntent, classify_query_intent
from app.services.retrieval.retriever import (
    retrieve_commitment_documents,
    retrieve_decision_candidates,
    retrieve_documents,
    retrieve_timeline_documents,
)
from app.services.storage.db import get_raw_collection
from app.services.storage.project_store import get_speaker_names

logger = logging.getLogger(__name__)

_MODEL = "gemini-2.5-flash-lite"


def _normalize(text: str) -> str:
    """Lowercase and strip diacritics so 'Ngumi' matches 'Ngũmi'."""
    return unicodedata.normalize("NFD", text).encode("ascii", "ignore").decode().lower()


def _detect_speaker_name(query: str, project_id: str) -> Optional[str]:
    """
    Scan query for a known speaker name from this project.
    Tries full name first, then first name (handles 'Bhavneet' -> 'Bhavneet Mhajan').
    Returns the canonical full name as stored in projects.json, or None.
    """
    names = get_speaker_names(project_id)
    q = _normalize(query)
    for name in names:
        if _normalize(name) in q:
            return name
        first = _normalize(name.split()[0])
        if len(first) > 2 and first in q:
            return name
    return None


def _retrieve_summary_chunks(project_id: str) -> list[Document]:
    """
    Fetch all summary chunks for the project chronologically.
    Uses raw ChromaDB — NOT vector search — because we want all summaries,
    not the semantically closest one.
    """
    try:
        collection = get_raw_collection()
        results = collection.get(
            where={
                "$and": [
                    {"project_id": {"$eq": project_id}},
                    {"is_meeting_summary": {"$eq": True}},
                ]
            },
            include=["documents", "metadatas"],
        )

        docs = []
        for i in range(len(results.get("ids", []))):
            text = results["documents"][i]
            metadata = results["metadatas"][i]
            docs.append(Document(page_content=text, metadata=metadata))

        docs.sort(key=lambda d: d.metadata.get("meeting_date", ""))
        logger.info("Retrieved %s summary chunks for project_id=%s", len(docs), project_id)
        return docs

    except Exception as e:
        logger.exception("Summary chunk retrieval failed: %s", e)
        return []


def _retrieve_for_intent(
    query: str,
    project_id: str,
    intent: QueryIntent,
) -> list[Document]:
    if intent == QueryIntent.SUMMARY:
        return _retrieve_summary_chunks(project_id)

    if intent == QueryIntent.DECISION:
        return retrieve_decision_candidates(query, project_id, k=10)

    if intent == QueryIntent.COMMITMENT:
        return retrieve_commitment_documents(query, project_id, k=10)

    if intent == QueryIntent.QUESTION:
        name = _detect_speaker_name(query, project_id)
        filters: dict = {"contains_question": True}
        if name:
            filters["speaker_name"] = name
        return retrieve_documents(query, project_id, filters=filters, k=10)

    if intent == QueryIntent.SPEAKER:
        name = _detect_speaker_name(query, project_id)
        filters = {"speaker_name": name} if name else None
        return retrieve_documents(query, project_id, filters=filters, k=10)

    if intent == QueryIntent.TIMELINE:
        return retrieve_timeline_documents(query, project_id, k_per_meeting=6)

    return retrieve_documents(query, project_id, k=10)


def _build_context(documents: list[Document]) -> str:
    parts = []
    for i, doc in enumerate(documents, 1):
        meta = doc.metadata
        meeting = meta.get("meeting_title", "Unknown Meeting")
        date = meta.get("meeting_date", "")
        speaker = meta.get("speaker_name", "Unknown Speaker")
        role = meta.get("speaker_role", "")
        speaker_line = f"{speaker} ({role})" if role else speaker
        parts.append(
            f"[{i}] Meeting: {meeting} ({date})\n"
            f"Speaker: {speaker_line}\n"
            f"Content: {doc.page_content}"
        )
    return "\n\n".join(parts)


_PROMPT_TEMPLATES = {
    QueryIntent.DECISION: (
        "You are an AI assistant analyzing meeting transcripts for a project manager.\n"
        "Answer the question by identifying specific decisions that were made, who made them, and when.\n\n"
        "Rules:\n"
        "- Only state decisions that are explicitly confirmed in the transcripts\n"
        "- Include the meeting title and speaker for each decision\n"
        "- If no clear decision was made, say so directly\n\n"
        "Context from meeting transcripts:\n{context}\n\n"
        "Question: {query}\n\nAnswer:"
    ),
    QueryIntent.COMMITMENT: (
        "You are an AI assistant analyzing meeting transcripts for a project manager.\n"
        "Extract action items, commitments, and next steps from the transcripts.\n\n"
        "Rules:\n"
        "- For each commitment, state: who committed, what they will do, and deadline if mentioned\n"
        "- Only include explicit commitments, not vague intentions\n"
        "- If no commitments are found, say so directly\n\n"
        "Context from meeting transcripts:\n{context}\n\n"
        "Question: {query}\n\nAnswer:"
    ),
    QueryIntent.SUMMARY: (
        "You are an AI assistant summarizing project progress for a project manager.\n"
        "Synthesize the following meeting summaries into a cohesive project overview.\n\n"
        "Rules:\n"
        "- Cover: key decisions made, current status, open issues, and next steps\n"
        "- Present information chronologically (earliest meeting first)\n"
        "- Be concise — focus on what a PM needs to know\n\n"
        "Meeting summaries (in chronological order):\n{context}\n\n"
        "Question: {query}\n\nAnswer:"
    ),
    QueryIntent.SPEAKER: (
        "You are an AI assistant analyzing meeting transcripts for a project manager.\n"
        "Answer the question based on what a specific speaker said across meetings.\n\n"
        "Rules:\n"
        "- Attribute statements to the correct speaker by name\n"
        "- Note if their position changed across different meetings\n"
        "- Include meeting title and date for key statements\n\n"
        "Context from meeting transcripts:\n{context}\n\n"
        "Question: {query}\n\nAnswer:"
    ),
    QueryIntent.TIMELINE: (
        "You are an AI assistant analyzing meeting transcripts for a project manager.\n"
        "Answer the question by comparing status, decisions, or progress across time periods.\n\n"
        "Rules:\n"
        "- Present information chronologically\n"
        "- Highlight what changed between meetings\n"
        "- Include meeting dates when referencing status or decisions\n\n"
        "Context from meeting transcripts:\n{context}\n\n"
        "Question: {query}\n\nAnswer:"
    ),
    QueryIntent.QUESTION: (
        "You are an AI assistant analyzing meeting transcripts for a project manager.\n"
        "Find and summarize questions that were raised in the meetings.\n\n"
        "Rules:\n"
        "- List each question with who asked it and which meeting it came from\n"
        "- If the question was answered in the transcript, include the answer\n"
        "- If the question was left unresolved, note that explicitly\n\n"
        "Context from meeting transcripts:\n{context}\n\n"
        "Question: {query}\n\nAnswer:"
    ),
    QueryIntent.GENERAL: (
        "You are an AI assistant answering questions about past meetings for a project manager.\n"
        "Answer based strictly on the transcript content provided below.\n\n"
        "Rules:\n"
        "- Base your answer only on the provided context\n"
        "- If the context does not contain enough information, say so clearly\n"
        "- Include meeting title and speaker references where relevant\n\n"
        "Context from meeting transcripts:\n{context}\n\n"
        "Question: {query}\n\nAnswer:"
    ),
}


def _build_prompt(query: str, context: str, intent: QueryIntent) -> str:
    template = _PROMPT_TEMPLATES.get(intent, _PROMPT_TEMPLATES[QueryIntent.GENERAL])
    return template.format(query=query, context=context)


def _call_gemini(prompt: str) -> str:
    if not Config.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set — cannot generate answer")

    client = genai.Client(api_key=Config.GEMINI_API_KEY)
    response = client.models.generate_content(model=_MODEL, contents=prompt)
    return response.text.strip()


def _extract_sources(documents: list[Document]) -> list[dict]:
    seen: set[tuple] = set()
    sources = []

    for doc in documents:
        meta = doc.metadata

        # Skip synthesized summary chunks — they are not real conversation turns
        if meta.get("is_meeting_summary"):
            continue

        meeting_title = meta.get("meeting_title", "Unknown Meeting")
        meeting_date = meta.get("meeting_date", "")
        speaker_name = meta.get("speaker_name", "")
        content = doc.page_content

        key = (meeting_title, meeting_date, speaker_name)
        if key not in seen:
            seen.add(key)
            sources.append(
                {
                    "meeting_title": meeting_title,
                    "meeting_date": meeting_date,
                    "speaker_name": speaker_name,
                    "content_preview": content[:200].strip(),
                }
            )

    return sources


_SEP = "─" * 62


def answer_question(query: str, project_id: str) -> dict:
    """
    Answer a question using the RAG pipeline.

    Returns:
        {
            "answer": str,
            "sources": list[{meeting_title, meeting_date, speaker_name}],
            "intent": str
        }
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")
    if not project_id or not project_id.strip():
        raise ValueError("project_id is required.")

    import time
    t_start = time.time()

    logger.info(_SEP)
    logger.info("PIPELINE START")
    logger.info("  query      : %s", query)
    logger.info("  project    : %s", project_id)
    logger.info(_SEP)

    try:
        # ── STEP 1: classify intent ──────────────────────────────────────
        logger.info("[1/4] CLASSIFY INTENT")
        intent = classify_query_intent(query)

        # ── STEP 2: retrieve documents ───────────────────────────────────
        logger.info("[2/4] RETRIEVE  (%s)", intent.value)
        _log_retrieval_strategy(intent, query, project_id)
        documents = _retrieve_for_intent(query, project_id, intent)

        if not documents:
            logger.info("  result     : no documents found — returning not-found message")
            logger.info(_SEP)
            return {
                "answer": (
                    "I couldn't find relevant information in the meeting transcripts for this project. "
                    "Make sure the project has been ingested and that the project_id is correct."
                ),
                "sources": [],
                "intent": intent.value,
            }

        # ── STEP 3: build context + prompt ───────────────────────────────
        logger.info("[3/4] BUILD PROMPT")
        context = _build_context(documents)
        prompt = _build_prompt(query, context, intent)
        logger.info("  docs used  : %d", len(documents))
        logger.info("  context    : %d chars", len(context))
        logger.info("  prompt     : \"%s...\"", prompt[:120].replace("\n", " "))

        # ── STEP 4: call LLM ─────────────────────────────────────────────
        logger.info("[4/4] LLM CALL  (model: %s)", _MODEL)
        answer = _call_gemini(prompt)
        sources = _extract_sources(documents)

        elapsed = time.time() - t_start
        logger.info(_SEP)
        logger.info("PIPELINE DONE  (%.1fs)", elapsed)
        logger.info("  intent     : %s", intent.value)
        logger.info("  sources    : %d unique", len(sources))
        for s in sources:
            logger.info(
                "    ↳ %s (%s) | %s",
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
        }

    except Exception as e:
        logger.exception("Answer generation failed | query='%s'", query)
        raise RuntimeError(f"Answer generation failed: {str(e)}") from e


def _log_retrieval_strategy(intent: QueryIntent, query: str, project_id: str) -> None:
    """Log what retrieval strategy will be used and why."""
    strategies = {
        QueryIntent.SUMMARY:    "raw collection get — all summary chunks chronologically (no vector search)",
        QueryIntent.DECISION:   "semantic search k=10 — no signal filter (decision hints are weak)",
        QueryIntent.COMMITMENT: "semantic search k=10 — filter: contains_commitment=True",
        QueryIntent.QUESTION:   "semantic search k=10 — filter: contains_question=True [+ speaker_name if detected]",
        QueryIntent.SPEAKER:    "semantic search k=10 — filter: speaker_name=<detected name>",
        QueryIntent.TIMELINE:   "per-meeting semantic search k=6 — one call per meeting, merged chronologically",
        QueryIntent.GENERAL:    "semantic search k=10 — project scope only",
    }
    strategy = strategies.get(intent, "semantic search")
    logger.info("  strategy   : %s", strategy)

    name = _detect_speaker_name(query, project_id)
    if name and intent in (QueryIntent.SPEAKER, QueryIntent.QUESTION):
        logger.info("  speaker    : detected \"%s\" in query", name)
