import json
import logging
import unicodedata
from typing import Optional

from google import genai
from google.genai import types as genai_types
from langchain_core.documents import Document

from app.config import Config
from .base import _fmt_date

logger = logging.getLogger(__name__)

_RERANK_MODEL      = "gemini-2.5-flash"
_MAX_PREVIEW_CHARS = 450


# ── Per-query rejected-doc accumulator ───────────────────────────────────────
# Stores hard-dropped chunks (score ≤ 2) across all rerank calls in one query.
# Reset by service.py before each new query via reset_rejected_docs().
# Deduplicated by chunk_id so multi-tool-call queries don't repeat the same chunk.

_rejected_docs: list[Document] = []
_rejected_cids: set[str]       = set()


def reset_rejected_docs() -> None:
    """Clear per-request rejected-doc state. Called by service.py before graph.invoke()."""
    _rejected_docs.clear()
    _rejected_cids.clear()


def get_rejected_docs() -> list[Document]:
    """Return all hard-dropped docs accumulated across all rerank calls this query."""
    return list(_rejected_docs)


def rerank_documents(
    query:        str,
    documents:    list[Document],
    topic_hint:   str = "",
    speaker_hint: str = "",
    top_n:        Optional[int] = None,
) -> list[Document]:
    """
    Re-rank retrieved documents by true relevance to query intent.

    Uses a single Gemini Flash call to score each chunk 0-10, then applies
    a post-score speaker boost (+1.5) when speaker_hint is set — ensures the
    named speaker's chunks surface even if they scored slightly lower than
    context chunks from other speakers.

    Tier logic (Gemini explicit 0-10 scale):
      7-10 → 🟢 direct pass — clearly relevant, tagged _relevance="high"
      3-6  → 🟡 soft pass  — tangential, tagged _relevance="low"
      0-2  → 🔴 hard drop  — irrelevant, never reaches LLM

    Falls back to original order on any error so the pipeline never breaks.
    """
    if len(documents) <= 1:
        return documents

    chunk_previews = []
    for i, doc in enumerate(documents):
        m       = doc.metadata
        speaker = m.get("speaker_name", "Unknown")
        meeting = m.get("meeting_title", "")[:40]
        date    = m.get("meeting_date", "")
        content = doc.page_content[:_MAX_PREVIEW_CHARS].replace("\n", " ")
        chunk_previews.append(
            f"[{i}] Speaker: {speaker} | Meeting: {meeting} ({date})\n"
            f"    Content: {content}"
        )

    chunks_text = "\n\n".join(chunk_previews)

    topic_section = (
        f"SEARCH TOPIC: \"{topic_hint}\"\n"
        f"This is the specific subject to find. "
        f"When the topic has a qualifier (e.g. 'AI', 'payment', 'frontend', a person's name), "
        f"the chunk must address BOTH the qualifier AND the noun to score 7+. "
        f"A chunk about the same noun in a completely different context scores 3 or lower.\n\n"
    ) if topic_hint else ""

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
        f"If uncertain — score it 5-6, not 7. "
        f"Ask: 'Is this chunk primarily ABOUT the question subject, or about something else "
        f"that happens to mention or impact it?' If the latter, cap at 6.\n\n"
        f"--- RULE 3: ATTRIBUTION ---\n"
        f"For questions asking who raised / first mentioned / expressed something: "
        f"score highest the chunk where the speaker states it directly themselves.\n\n"
        f"--- RULE 4: ANSWER TYPE MATCH ---\n"
        f"Read the question and determine what kind of answer it seeks — a confirmed outcome, "
        f"a description of how something works, a commitment someone made, a summary, etc.\n"
        f"Score 7+ ONLY for chunks that provide THAT TYPE of content.\n"
        f"Example: if the question asks what was DECIDED or CHOSEN, a chunk that describes or "
        f"explains an option scores 3-4 even if the topic keyword matches perfectly — "
        f"unless the chunk also states the final outcome or confirmation.\n\n"
        f"Chunks:\n{chunks_text}\n\n"
        f"Respond with ONLY a JSON array, one object per chunk, no explanation:\n"
        f'[{{"index": 0, "score": 7}}, {{"index": 1, "score": 3}}, ...]\n\n'
        f"Include all {len(documents)} chunks in the array."
    )

    try:
        if not Config.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY not set")

        client   = genai.Client(api_key=Config.GEMINI_API_KEY)
        response = client.models.generate_content(
            model=_RERANK_MODEL,
            contents=prompt,
            config=genai_types.GenerateContentConfig(temperature=0.0),
        )
        raw = response.text.strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        scores_list = json.loads(raw)
        score_map   = {item["index"]: item["score"] for item in scores_list}

        # Post-score speaker boost: +1.5 for the named speaker's chunks.
        # Applied AFTER LLM scoring so the model scores on content quality alone.
        if speaker_hint:
            def _norm(s: str) -> str:
                return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode().lower()
            target = _norm(speaker_hint)
            for i, doc in enumerate(documents):
                if _norm(doc.metadata.get("speaker_name", "")) == target:
                    score_map[i] = score_map.get(i, 0) + 1.5

        indexed = [
            (i, documents[i], score_map.get(i, 0))
            for i in range(len(documents))
        ]
        indexed.sort(key=lambda x: x[2], reverse=True)

        # Stamp score into every doc's metadata (used by RESULT log in service.py)
        for _, doc, s in indexed:
            doc.metadata["_rerank_score"] = s

        # Similarity threshold: if no chunk scores ≥ 5, the query topic is not
        # in the transcripts. Returning soft-pass chunks (score 3-4 = "passing
        # mention") would cause the LLM to hallucinate an answer from unrelated
        # context. Return empty so the agent reports "no information found."
        max_score = indexed[0][2] if indexed else 0
        if max_score < 5:
            logger.info(
                "  reranker: max_score=%.1f < 5 — topic not in transcripts, returning empty",
                max_score,
            )
            return []

        # 3-tier filter
        hard_drop   = [(i, doc, s) for i, doc, s in indexed if s <= 2]
        soft_pass   = [(i, doc, s) for i, doc, s in indexed if 3 <= s < 7]
        direct_pass = [(i, doc, s) for i, doc, s in indexed if s >= 7]

        for _, doc, _ in soft_pass:
            doc.metadata["_relevance"] = "low"
        for _, doc, _ in direct_pass:
            doc.metadata["_relevance"] = "high"

        # Accumulate hard-dropped docs for the RESULT log
        for _, doc, _ in hard_drop:
            cid = doc.metadata.get("chunk_id", str(id(doc)))
            if cid not in _rejected_cids:
                _rejected_cids.add(cid)
                _rejected_docs.append(doc)

        logger.info(
            "🎯 RERANK  %d scored  |  🟢 direct=%d (7-10)  🟡 soft=%d (3-6)  🔴 drop=%d (0-2)",
            len(indexed), len(direct_pass), len(soft_pass), len(hard_drop),
        )
        logger.info("   " + "─" * 65)
        for rank, (orig_idx, doc, score) in enumerate(indexed, 1):
            m       = doc.metadata
            speaker = m.get("speaker_name", "?")
            date    = _fmt_date(m.get("meeting_date"))
            meeting = m.get("meeting_title", "?")[:35]
            preview = doc.page_content.replace("\n", " ").strip()[:130]
            move    = f"{orig_idx + 1}→{rank}" if orig_idx + 1 != rank else f"#{rank} (no change)"
            if score >= 7:
                icon, tier = "🟢", "PASS"
            elif score >= 3:
                icon, tier = "🟡", "SOFT"
            else:
                icon, tier = "🔴", "DROP"
            logger.info(
                "   %s [%2d] score=%-4.1f %-4s  pos %s  |  👤 %-22s  📅 %s  🏢 %s",
                icon, rank, score, tier, move, speaker, date, meeting,
            )
            logger.info("         💬 %s", preview)

        # Passing strategy: keep all direct_pass; soft_pass fills remaining slots.
        # MAX_CHUNKS=20 hard ceiling. Fallback: <2 direct → include at least 3 soft.
        MAX_CHUNKS = 20
        soft_slots = max(0, (top_n or MAX_CHUNKS) - len(direct_pass))

        if len(direct_pass) < 2:
            fill = soft_pass[:max(soft_slots, 3)]
        else:
            fill = soft_pass[:soft_slots]

        passing  = direct_pass + fill
        reranked = [doc for _, doc, _ in passing]
        return reranked[:MAX_CHUNKS]

    except Exception as e:
        logger.warning("Re-ranking failed (%s) — returning original order", e)
        return documents