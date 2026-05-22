import json
import logging
import unicodedata
from typing import Optional

from google import genai
from langchain_core.documents import Document

from app.config import Config

logger = logging.getLogger(__name__)

_RERANK_MODEL = "gemini-2.5-flash-lite"
_MAX_PREVIEW_CHARS = 300


def rerank_documents(
    query: str,
    documents: list[Document],
    intent_hint: str = "",
    topic_hint: str = "",
    speaker_hint: str = "",
    top_n: Optional[int] = None,
) -> list[Document]:
    """
    Re-rank retrieved documents by true relevance to query intent.

    Uses a single Gemini Flash Lite call to score each chunk, then applies
    a post-score speaker boost (+1.5) when speaker_hint is set — this ensures
    the named speaker's chunks surface even if they scored slightly lower than
    context chunks from other speakers.

    Falls back to original order on any error so the pipeline never breaks.
    """
    if len(documents) <= 1:
        return documents

    chunk_previews = []
    for i, doc in enumerate(documents):
        m = doc.metadata
        speaker = m.get("speaker_name", "Unknown")
        meeting = m.get("meeting_title", "")[:40]
        date_str = m.get("meeting_date", "")
        content = doc.page_content[:_MAX_PREVIEW_CHARS].replace("\n", " ")
        chunk_previews.append(
            f"[{i}] Speaker: {speaker} | Meeting: {meeting} ({date_str})\n"
            f"    Content: {content}"
        )

    chunks_text = "\n\n".join(chunk_previews)

    topic_line = (
        f"Specific topic to find in chunks: \"{topic_hint}\"\n"
        f"A chunk scores 7+ ONLY if its content is directly about this specific topic. "
        f"If the chunk discusses a different subject — even if it shares a keyword with the query — "
        f"it scores 0-3.\n\n"
    ) if topic_hint else ""

    speaker_line = (
        f"Target speaker: \"{speaker_hint}\"\n"
        f"The query is specifically about what this speaker said. "
        f"Prioritize chunks where this speaker is the one speaking.\n\n"
    ) if speaker_hint else ""

    prompt = (
        f"You are a relevance scorer for a meeting transcript search system.\n\n"
        f"Query: \"{query}\"\n"
        f"Query intent: {intent_hint}\n"
        f"{topic_line}"
        f"{speaker_line}"
        f"Below are {len(documents)} transcript chunks. Score each one 0-10 based on "
        f"how directly it answers the query.\n\n"
        f"Scoring rules:\n"
        f"- 9-10: directly and specifically answers the query\n"
        f"- 6-8: relevant and useful context\n"
        f"- 3-5: tangentially related to the topic\n"
        f"- 0-2: not relevant\n\n"
        f"Origin vs. discussion rule:\n"
        f"For queries asking 'who raised / who first mentioned / who expressed X about Y', "
        f"prioritize the chunk where the speaker directly originates or expresses that, "
        f"not where someone else references or describes the event afterward.\n\n"
        f"Chunks:\n{chunks_text}\n\n"
        f"Respond with ONLY a JSON array, one object per chunk:\n"
        f'[{{"index": 0, "score": 7}}, {{"index": 1, "score": 3}}, ...]\n\n'
        f"Include all {len(documents)} chunks in the array."
    )

    try:
        if not Config.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY not set")

        client = genai.Client(api_key=Config.GEMINI_API_KEY)
        response = client.models.generate_content(model=_RERANK_MODEL, contents=prompt)
        raw = response.text.strip()

        # Strip markdown code fence if Gemini wraps the JSON
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        scores_list = json.loads(raw)
        score_map = {item["index"]: item["score"] for item in scores_list}

        # Post-score speaker boost: chunks from the named speaker get +1.5
        # Applied AFTER LLM scoring so LLM still scores on content quality alone.
        if speaker_hint:
            def _norm(s: str) -> str:
                return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode().lower()
            target = _norm(speaker_hint)
            for i, doc in enumerate(documents):
                chunk_speaker = _norm(doc.metadata.get("speaker_name", ""))
                if chunk_speaker == target:
                    score_map[i] = score_map.get(i, 0) + 1.5

        logger.info(
            "  rerank     : raw scores %s",
            {i: score_map.get(i, 0) for i in range(len(documents))},
        )

        indexed = [
            (i, documents[i], score_map.get(i, 0))
            for i in range(len(documents))
        ]
        indexed.sort(key=lambda x: x[2], reverse=True)

        for rank, (orig_idx, doc, score) in enumerate(indexed, 1):
            m = doc.metadata
            moved = f"moved {orig_idx + 1}->{rank}" if orig_idx + 1 != rank else f"stayed #{rank}"
            logger.info(
                "  rerank[%d]  : score=%.1f | %s | %s | \"%s...\"",
                rank,
                score,
                moved,
                m.get("speaker_name", "?"),
                doc.page_content[:60].replace("\n", " "),
            )

        reranked = [doc for _, doc, _ in indexed]
        return reranked[:top_n] if top_n else reranked

    except Exception as e:
        logger.warning("Re-ranking failed (%s) — returning original order", e)
        return documents
