import json
import logging
import unicodedata
from typing import Optional

from google import genai
from google.genai import types as genai_types
from langchain_core.documents import Document

from app.config import Config

logger = logging.getLogger(__name__)

_RERANK_MODEL = "gemini-2.5-flash"
_MAX_PREVIEW_CHARS = 450  # 300 was too short — key statements mid-chunk were cut off


def rerank_documents(
    query: str,
    documents: list[Document],
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

    # topic_section: fires only when a clean keyword topic is provided.
    # Adds the modifier-aware rule — "AI Architecture" means BOTH "AI" AND "architecture"
    # must be the chunk's subject, not just either word in isolation.
    topic_section = (
        f"SEARCH TOPIC: \"{topic_hint}\"\n"
        f"This is the specific subject to find. "
        f"When the topic has a qualifier (e.g. 'AI', 'payment', 'frontend', a person's name), "
        f"the chunk must address BOTH the qualifier AND the noun to score 7+. "
        f"A chunk about the same noun in a completely different context scores 3 or lower.\n\n"
    ) if topic_hint else ""

    # speaker_section: fires only when a named speaker is being searched.
    speaker_section = (
        f"TARGET SPEAKER: \"{speaker_hint}\"\n"
        f"The question is specifically about what this speaker said. "
        f"Prioritize chunks where this speaker is directly speaking.\n\n"
    ) if speaker_hint else ""

    prompt = (
        f"You are a relevance scorer for a meeting transcript retrieval system.\n\n"
        f"USER'S QUESTION: \"{query}\"\n"
        f"{topic_section}"
        f"{speaker_section}"
        f"Score each of the {len(documents)} chunks below from 0-10 based on how directly "
        f"the chunk answers the user's question.\n\n"
        f"--- SCORING SCALE ---\n"
        f"9-10 : Chunk's PRIMARY content directly and specifically answers the question. No doubt.\n"
        f"7-8  : Chunk is clearly about the same subject. Confident it belongs in the answer.\n"
        f"5-6  : Uncertain fit — chunk relates to or affects the topic but is not specifically about it.\n"
        f"3-4  : Topic appears as a passing mention. Chunk is mainly about something else.\n"
        f"0-2  : Not relevant. Keyword overlap only, used in a different meaning or context.\n\n"
        f"--- RULE 1: SCORE BY SUBJECT, NOT KEYWORDS ---\n"
        f"Score based on whether the chunk's MAIN SUBJECT matches the question's intent. "
        f"A chunk that contains a query keyword but uses it in a different context must score 0-2. "
        f"A chunk where the topic is a side mention (not the main point) must score 3-4.\n\n"
        f"--- RULE 2: CONFIDENCE THRESHOLD ---\n"
        f"Score 7+ only when you are CONFIDENT the chunk belongs in a focused answer. "
        f"If uncertain — if the chunk is about something that merely AFFECTS or REFERENCES "
        f"the topic rather than IS the topic — score it 5-6, not 7. "
        f"Ask: 'Is this chunk primarily ABOUT the question subject, or about something else "
        f"that happens to mention or impact it?' If the latter, cap at 6.\n\n"
        f"--- RULE 3: ATTRIBUTION ---\n"
        f"For questions asking who raised / first mentioned / expressed something: "
        f"score highest the chunk where the speaker states it directly themselves, "
        f"not a chunk where someone else later references or describes what they said.\n\n"
        f"Chunks:\n{chunks_text}\n\n"
        f"Respond with ONLY a JSON array, one object per chunk, no explanation:\n"
        f'[{{"index": 0, "score": 7}}, {{"index": 1, "score": 3}}, ...]\n\n'
        f"Include all {len(documents)} chunks in the array."
    )

    try:
        if not Config.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY not set")

        client = genai.Client(api_key=Config.GEMINI_API_KEY)
        response = client.models.generate_content(
            model=_RERANK_MODEL,
            contents=prompt,
            config=genai_types.GenerateContentConfig(temperature=0.0),
        )
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

        # 3-tier score filter
        # 0-2  → hard drop : irrelevant, never reaches LLM
        # 3-6  → soft pass : tangential/borderline, reaches LLM with _relevance="low" tag
        # 7-10 → direct pass: clearly relevant, reaches LLM with _relevance="high" tag
        #
        # Threshold at 7 (not 6): score=6 means "relevant context" but not
        # specifically about the query subject. Keeping 6s as soft forces the
        # LLM to treat them as background only (rule 11 in system prompt),
        # preventing feature-level chunks from polluting component-specific answers.
        hard_drop   = [(i, doc, s) for i, doc, s in indexed if s <= 2]
        soft_pass   = [(i, doc, s) for i, doc, s in indexed if 3 <= s <= 6]
        direct_pass = [(i, doc, s) for i, doc, s in indexed if s >= 7]

        for _, doc, _ in soft_pass:
            doc.metadata["_relevance"] = "low"
        for _, doc, _ in direct_pass:
            doc.metadata["_relevance"] = "high"

        logger.info(
            "  rerank_tiers: hard_drop=%d | soft_pass=%d | direct_pass=%d",
            len(hard_drop), len(soft_pass), len(direct_pass),
        )

        for rank, (orig_idx, doc, score) in enumerate(direct_pass, 1):
            m = doc.metadata
            logger.info(
                "  direct_pass[%d]: score=%.1f | orig_pos=%d | speaker=%s | meeting=%s | \"%s\"",
                rank, score, orig_idx + 1,
                m.get("speaker_name", "?"),
                m.get("meeting_title", "?")[:40],
                doc.page_content.replace("\n", " "),
            )

        for rank, (orig_idx, doc, score) in enumerate(indexed, 1):
            m      = doc.metadata
            tier   = "DROP" if score <= 2 else ("LOW" if score <= 6 else "HIGH")
            moved  = f"moved {orig_idx + 1}->{rank}" if orig_idx + 1 != rank else f"stayed #{rank}"
            logger.info(
                "  rerank[%d]  : score=%.1f | tier=%-4s | %s | %s | \"%s...\"",
                rank, score, tier, moved,
                m.get("speaker_name", "?"),
                doc.page_content[:60].replace("\n", " "),
            )

        # direct_pass first (score 7-10), then soft_pass (score 3-6), hard_drop excluded
        # We are applying the limit of 2 for the direct_pass tier to ensure we only feed the most relevant chunks to the LLM when top_n is set. If there are fewer than 2 direct_pass chunks, we fill the remaining slots with soft_pass chunks, which are still relevant but less directly on point. This way, we maintain a high relevance threshold while also providing enough context for the LLM to work with.
        passing = direct_pass if len(direct_pass) >= 2 else direct_pass + soft_pass
        reranked = [doc for _, doc, _ in passing]
        return reranked[:top_n] if top_n else reranked

    except Exception as e:
        logger.warning("Re-ranking failed (%s) — returning original order", e)
        return documents
