import logging
import os
import re
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

# ── Batch configuration ───────────────────────────────────────────────────────

BATCH_SIZE = 10  # chunks per Gemini batch; tune to stay under rate limits

# ── Signal regexes ────────────────────────────────────────────────────────────

_DECISION_RE = re.compile(
    r"\b(decided|decision|agreed|approved|finalized|confirmed|going with|"
    r"let'?s go with|move forward with|stick with|chosen|selected)\b",
    re.IGNORECASE
)

_FALSE_DECISION_RE = re.compile(
    r"\b(make a decision|take a decision|come to a decision|"
    r"before (you |we |they |i )?(make|take|reach) a decision|"
    r"better decision|right decision|own decision|"
    r"need to (decide|make a decision)|"
    r"haven'?t decided|have not decided|no decision yet|"
    r"without a decision|can('?t| not) decide)\b",
    re.IGNORECASE,
)

_COMMITMENT_RE = re.compile(
    r"\b(i will|i'?ll|we will|we'?ll|going to|will make sure|committ?ed to|"
    r"take ownership|my action item|action on me)\b",
    re.IGNORECASE
)

_FALSE_COMMITMENT_RE = re.compile(
    r"\b(i will say|i'?ll say|i will note|we will see|we'?ll see|"
    r"that will|this will|it will|would be|will be able|"
    r"i'?ll be back|i will be back|i'?ll be there|i will be there)\b",
    re.IGNORECASE
)

_QUESTION_START_RE = re.compile(
    r"^(what|when|where|who|why|how|"
    r"can you|could you|would you|"
    r"is there|are there|"
    r"do you|did you|have you|"
    r"will you|"
    r"should we|can we|are we|"
    r"what if)\b",
    re.IGNORECASE,
)

_DOCUMENT_SHARE_RE = re.compile(
    r"\b("
    r"shared (a |the |this )?(document|doc|file|spreadsheet|sheet|presentation|deck|report|pdf|link|attachment)|"
    r"sending (over |you |across )?(the |a |this )?(document|doc|file|spreadsheet|sheet|presentation|deck|report|pdf)|"
    r"sent (you |over |across )?(the |a |this )?(document|doc|file|spreadsheet|sheet|presentation|deck|report|pdf)|"
    r"please find (the |a |this )?(attached|document|doc|file)|"
    r"attached (the |a |this )?(document|doc|file|spreadsheet|sheet|report)|"
    r"can you (share|send|provide) (the |a |this )?(document|doc|file|spreadsheet|sheet|report)|"
    r"share (your |the |a |this )?(screen|document|doc|file|spreadsheet|presentation|deck)|"
    r"sharing (the |a |this )?(screen|document|doc|file|spreadsheet|presentation|deck)|"
    r"i('ll| will) share (the |a |this )?(document|doc|file|spreadsheet|link)|"
    r"dropped (the |a |this )?(link|document|doc|file) in (the )?chat|"
    r"put (it |the link |the doc |the file )in (the )?chat"
    r")\b",
    re.IGNORECASE,
)

_OPEN_ISSUE_RE = re.compile(
    r"\b("
    r"issue|problem|bug|error|discrepancy|mismatch|inconsistency|"
    r"not (working|correct|right|matching|aligned|accurate)|"
    r"something('s| is) (wrong|off|broken|incorrect)|"
    r"doesn't (work|match|add up)|"
    r"that('s| is) (wrong|incorrect|not right|broken)|"
    r"concern|unclear|confusion|confused|confusing|"
    r"need(s)? (clarification|to be fixed|to be resolved|to be addressed|to be checked)|"
    r"still (open|pending|unresolved|outstanding)|"
    r"not resolved|unresolved|open question|raised (an?|the) (issue|concern|question|problem)|"
    r"flag(ged)? (this|that|an? issue|a concern)|"
    r"pointing out|raised (this|that)|brought up"
    r")\b",
    re.IGNORECASE,
)

# ── Confirmation / agreement (bypass-only signal) ─────────────────────────────

_CONFIRMATION_RE = re.compile(
    r"\b("
    r"correct|exactly|absolutely|confirmed|agreed|"
    r"that's right|that is right|sounds good|looks good|"
    r"makes sense|fair enough|go ahead|perfect|"
    r"not correct|that's wrong|i disagree|are you sure|"
    r"you sure|double check|double-check|are you certain"
    r")\b",
    re.IGNORECASE,
)

# ── Quality filter ────────────────────────────────────────────────────────────

_STOPWORDS = frozenset({
    "the", "a", "an", "and", "or", "of", "in", "on", "at", "to", "for",
    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "will", "would", "could", "should", "may", "might",
    "it", "its", "this", "that", "these", "those", "i", "we", "you", "he",
    "she", "they", "my", "our", "your", "his", "her", "their", "what", "how",
    "just", "very", "so", "as", "if", "but", "not", "um", "uh",
    "like", "okay", "ok", "yeah", "hmm", "actually",
})


def _is_low_quality(text: str) -> bool:
    tokens = text.lower().split()
    if not tokens:
        return True
    if len(set(tokens)) / len(tokens) < 0.4:
        most_repeated = max(set(tokens), key=tokens.count)
        if most_repeated in _STOPWORDS:
            return True
    meaningful = [t for t in tokens if t not in _STOPWORDS and len(t) > 2]
    return len(meaningful) < 2


# ── Topic-shift split ─────────────────────────────────────────────────────────

_TOPIC_SHIFT_RE = re.compile(
    r"^(now[,\s]|next[,\s]|another point|separately[,\s]|also[,\s]|"
    r"moving on|switching to|on another|by the way)",
    re.IGNORECASE,
)


def _detect_signals(text: str) -> dict:
    cleaned = text.strip()
    if not cleaned:
        return {
            "contains_decision": False,
            "contains_commitment": False,
            "contains_question": False,
            "contains_document_share": False,
            "contains_open_issue": False,
        }
    return {
        "contains_decision": (
            bool(_DECISION_RE.search(cleaned))
            and not bool(_FALSE_DECISION_RE.search(cleaned))
        ),
        "contains_commitment": (
            bool(_COMMITMENT_RE.search(cleaned))
            and not bool(_FALSE_COMMITMENT_RE.search(cleaned))
        ),
        "contains_question": (
            "?" in cleaned
            or bool(_QUESTION_START_RE.match(cleaned))
        ),
        "contains_document_share": bool(_DOCUMENT_SHARE_RE.search(cleaned)),
        "contains_open_issue": bool(_OPEN_ISSUE_RE.search(cleaned)),
    }


# ── Summary chunk builder ─────────────────────────────────────────────────────

def build_summary_chunk(summary_text: str, meeting_meta: dict, chunk_index: int) -> dict:
    return {
        "chunk_id":                f"{meeting_meta['meeting_id']}_summary",
        "meeting_id":              meeting_meta["meeting_id"],
        "meeting_title":           meeting_meta["title"],
        "meeting_date":            meeting_meta["date"],
        "meeting_number":          meeting_meta.get("meeting_number", 0),
        "meeting_type":            "unknown",
        "speaker_name":            "Meeting Summary",
        "speaker_id":              "meeting_summary",
        "speaker_role":            "unknown",
        "chunk_index":             chunk_index,
        "chunk_type":              "summary",
        "is_meeting_summary":      True,
        "segment_type":            "summary",
        "start_time":              None,
        "end_time":                None,
        "prev_chunk_id":           None,
        "next_chunk_id":           None,
        "contains_decision":       False,
        "contains_commitment":     False,
        "contains_question":       False,
        "contains_document_share": False,
        "contains_open_issue":     False,
        "sentiment":               "neutral",
        "text":                    summary_text,
        "text_length":             len(summary_text),
    }


def _make_speaker_id(speaker_name: str) -> str:
    normalized = unicodedata.normalize("NFKD", speaker_name)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "_", ascii_name.lower()).strip("_")


# ── Pass 1 — Atomic chunks ────────────────────────────────────────────────────

def create_chunks(sentences, meeting_meta):
    """
    Production-level chunking: accumulate same-speaker sentences until MIN_CHARS.

    Key properties:
    - Speaker change → hard flush (force=True).
    - Topic-shift phrase within same speaker → soft flush (force=False); only
      splits if buffer is already >= MIN_CHARS.
    - MAX_CHARS hard ceiling prevents excessively long chunks.
    - Low-quality chunks are dropped unless they carry a semantic signal.
    - chunk_type is "atomic" for all utterance chunks produced here.
    """
    chunks = []
    current_chunk = []
    current_times = []
    current_speaker = None
    chunk_index = 1

    MAX_CHARS = 500
    MIN_CHARS = 200
    HARD_MIN  = 15

    def flush_chunk(force=False):
        nonlocal current_chunk, current_times, chunk_index

        if not current_chunk:
            return

        chunk_text = " ".join(current_chunk).strip()

        if len(chunk_text) < HARD_MIN:
            current_chunk = []
            current_times = []
            return

        if len(chunk_text) < MIN_CHARS and not force:
            return

        signals = _detect_signals(chunk_text)

        has_signal = (
            any(signals.values())
            or bool(_CONFIRMATION_RE.search(chunk_text))
        )

        if not has_signal and _is_low_quality(chunk_text):
            current_chunk = []
            current_times = []
            return

        valid_starts = [s for s, _ in current_times if s is not None]
        valid_ends   = [e for _, e in current_times if e is not None]

        chunks.append({
            "chunk_id":                f"{meeting_meta['meeting_id']}_{chunk_index}",
            "meeting_id":              meeting_meta["meeting_id"],
            "meeting_title":           meeting_meta["title"],
            "meeting_date":            meeting_meta["date"],
            "meeting_number":          meeting_meta.get("meeting_number", 0),
            "meeting_type":            "unknown",
            "speaker_name":            current_speaker,
            "speaker_id":              _make_speaker_id(current_speaker),
            "speaker_role":            "unknown",
            "chunk_index":             chunk_index,
            "chunk_type":              "atomic",
            "is_meeting_summary":      False,
            "segment_type":            "content",
            "start_time":              min(valid_starts) if valid_starts else None,
            "end_time":                max(valid_ends)   if valid_ends   else None,
            "prev_chunk_id":           None,
            "next_chunk_id":           None,
            **signals,
            "sentiment":               "neutral",
            "text":                    chunk_text,
            "text_length":             len(chunk_text),
        })

        chunk_index += 1
        current_chunk = []
        current_times = []

    for s in sentences:
        text      = s["text"].strip()
        speaker   = s["speaker_name"]
        start_sec = s.get("start_time")
        end_sec   = s.get("end_time")

        if len(text) < 8:
            continue

        if speaker != current_speaker:
            flush_chunk(force=True)
            current_chunk = []
            current_times = []
            current_speaker = speaker
        elif current_chunk and _TOPIC_SHIFT_RE.match(text):
            flush_chunk(force=False)

        projected = " ".join(current_chunk + [text])
        if len(projected) > MAX_CHARS:
            flush_chunk(force=True)

        current_chunk.append(text)
        current_times.append((start_sec, end_sec))

    flush_chunk(force=True)

    for i, chunk in enumerate(chunks):
        chunk["prev_chunk_id"] = chunks[i - 1]["chunk_id"] if i > 0 else None
        chunk["next_chunk_id"] = chunks[i + 1]["chunk_id"] if i < len(chunks) - 1 else None

    return chunks


# ── Pass 2 — Dialogue group chunks ────────────────────────────────────────────

# Only strong, unambiguous continuation signals.
# Common fillers (so, and, but, right, yeah, exactly, correct, actually)
# are excluded — they appear at turn starts regardless of topic and cause
# wrong merges. Those short turns are already caught by Condition A (< 30 tokens).
_CONTINUATION_WORDS = (
    "because",          # almost always extends the previous reason
    "i mean",           # almost always clarifies the previous point
    "what i'm saying",  # always rephrases the previous point
    "to add to that",   # always extends the previous point
    "no no",            # always corrects the previous point
)

_TFIDF_BREAK_THRESHOLD = 0.10  # cosine sim below this → hard topic break
                               # 0.15 was too strict for Q→A exchanges where
                               # "Is it going to LLM?" / "Yes, documents go to LLM"
                               # share almost no TF-IDF tokens despite being one dialogue
_GROUP_MAX_TOKENS      = 350   # hard token cap per dialogue group


def create_dialogue_groups(atomic_chunks: list, meeting_metadata: dict) -> list:
    """
    Second pass over atomic chunks to produce dialogue_group chunks.

    Merging rules (applied in strict priority order):
      Rule 1 (HARD) — TF-IDF cosine sim between consecutive turns < 0.15 → break.
                      Always checked first; Rule 2 is never reached on a break.
      Rule 2        — Merge if ANY condition holds (only reached after Rule 1 passes):
                        A: next turn token count < 30
                        B: next turn starts with a strong continuation word
                        C: previous turn < 30 tokens AND same speaker resumes
      Rule 3 (HARD) — Merging would push the group past 300 tokens → break instead.
      Rule 4        — Last turn of the completed group becomes the first turn of
                      the next group (one-turn overlap at dialogue-turn level).

    TF-IDF is fit ONLY on this meeting's turns — never globally across meetings.
    Groups with < 2 turns are discarded.

    Multi-value fields (speakers, turn_ids) are pipe-separated strings because
    ChromaDB metadata does not support Python lists.
    """
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    content_chunks = [c for c in atomic_chunks if not c.get("is_meeting_summary")]
    n = len(content_chunks)
    if n < 2:
        return []

    texts = [c["text"] for c in content_chunks]

    try:
        vectorizer   = TfidfVectorizer(stop_words="english")
        tfidf_matrix = vectorizer.fit_transform(texts)
    except ValueError:
        # Empty vocabulary after stop-word removal (very short or all-filler meeting)
        logger.warning("create_dialogue_groups: empty TF-IDF vocabulary — skipping")
        return []

    # sims[i] = cosine similarity between turn i and turn i+1
    sims = [
        float(cosine_similarity(tfidf_matrix[i : i + 1], tfidf_matrix[i + 1 : i + 2])[0][0])
        for i in range(n - 1)
    ]

    groups: list[list[dict]] = []
    current_group: list[dict] = [content_chunks[0]]

    for i in range(1, n):
        next_chunk   = content_chunks[i]
        sim          = sims[i - 1]
        next_tokens  = len(next_chunk["text"].split())
        group_tokens = sum(len(c["text"].split()) for c in current_group)

        # Rule 1 — hard topic boundary (TF-IDF break)
        # Exception: when the speaker changes AND the next turn is short
        # (< 30 tokens), bypass this rule entirely. Short responses at a
        # speaker-change boundary are almost always reactions/answers to the
        # previous turn, not topic jumps — even when TF-IDF sees zero overlap.
        # Example: "Okay, I will document it." (4 tokens) has sim=0.0 with the
        # preceding explanation but is a direct reply and a commitment.
        speaker_changed = current_group[-1].get("speaker_name") != next_chunk.get("speaker_name")
        short_response  = next_tokens < 30

        if sim < _TFIDF_BREAK_THRESHOLD and not (speaker_changed and short_response):
            if len(current_group) > 1:
                groups.append(current_group)
            current_group = [next_chunk]
            continue

        # Rule 3 — size cap (evaluated before merge decision)
        if group_tokens + next_tokens > _GROUP_MAX_TOKENS:
            if len(current_group) > 1:
                groups.append(current_group)
            # Rule 4 — one-turn overlap starts the new group
            current_group = [current_group[-1], next_chunk]
            continue

        # Rule 2 — any one condition triggers a merge
        next_text_lower = next_chunk["text"].strip().lower()
        prev_tokens     = len(current_group[-1]["text"].split())
        prev_speaker    = current_group[-1].get("speaker_name", "")

        should_merge = (
            next_tokens < 30                                                              # A
            or any(next_text_lower.startswith(w) for w in _CONTINUATION_WORDS)           # B
            or (prev_tokens < 30 and prev_speaker == next_chunk.get("speaker_name", "")) # C
            or (speaker_changed and sim >= _TFIDF_BREAK_THRESHOLD)                       # D: same topic + speaker change = dialogue reply
        )

        if should_merge:
            current_group.append(next_chunk)
        else:
            if len(current_group) > 1:
                groups.append(current_group)
            current_group = [next_chunk]

    if len(current_group) > 1:
        groups.append(current_group)

    meeting_id      = meeting_metadata["meeting_id"]
    dialogue_chunks = []

    for g_idx, turns in enumerate(groups):
        seen: set[str] = set()
        unique_speakers: list[str] = []
        for t in turns:
            sp = t.get("speaker_name", "")
            if sp and sp not in seen:
                unique_speakers.append(sp)
                seen.add(sp)

        # Dialogue groups require at least 2 different speakers.
        # Single-speaker groups are same-speaker merges from Rule 2C and should
        # remain as atomic chunks — not labelled as dialogue_group.
        if len(unique_speakers) < 2:
            continue

        raw_text = "\n".join(
            f"{t.get('speaker_name', 'Unknown')}: {t['text']}"
            for t in turns
        )

        turn_ids     = [t["chunk_id"] for t in turns]
        group_tokens = sum(len(t["text"].split()) for t in turns)

        valid_starts = [t["start_time"] for t in turns if t.get("start_time") is not None]
        valid_ends   = [t["end_time"]   for t in turns if t.get("end_time")   is not None]

        dialogue_chunks.append({
            "chunk_id":           f"{meeting_id}_dg_{g_idx + 1}",
            "meeting_id":         meeting_id,
            "meeting_title":      meeting_metadata["title"],
            "meeting_date":       meeting_metadata["date"],
            "meeting_number":     meeting_metadata.get("meeting_number", 0),
            "chunk_type":         "dialogue_group",
            "is_meeting_summary": False,
            # pipe-separated strings — ChromaDB does not allow list values
            "speakers":           "|".join(unique_speakers),
            "turn_ids":           "|".join(turn_ids),
            "group_token_count":  group_tokens,
            # empty speaker_name so _stamp_project_and_roles doesn't crash;
            # get_speaker_role("") safely returns "unknown"
            "speaker_name":       "",
            "text":               raw_text,
            "start_time":         min(valid_starts) if valid_starts else None,
            "end_time":           max(valid_ends)   if valid_ends   else None,
        })

    logger.info(
        "create_dialogue_groups: %d content turns → %d dialogue groups",
        n, len(dialogue_chunks),
    )
    return dialogue_chunks


# ── Hypothetical question generation ─────────────────────────────────────────

_HQ_PROMPT = (
    "Given this meeting transcript segment, write ONE specific question "
    "that this segment directly answers. The question should use domain "
    "terms from the text itself. Return only the question, nothing else.\n\n"
    "Segment: {raw_text}"
)


def _generate_hq_single(chunk: dict, client) -> str:
    """
    Generate a hypothetical question for one chunk via Gemini.
    Retries once on any failure; uses a deterministic fallback so ingestion
    never crashes regardless of API availability.
    """
    raw_text = chunk["text"]
    prompt   = _HQ_PROMPT.format(raw_text=raw_text)

    for attempt in range(2):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            result = (response.text or "").strip()
            if result:
                return result
        except Exception as exc:
            logger.log(
                logging.WARNING if attempt == 0 else logging.ERROR,
                "HQ attempt %d failed for chunk %s: %s",
                attempt + 1, chunk.get("chunk_id"), exc,
            )

    title   = chunk.get("meeting_title", "")
    speaker = chunk.get("speaker_name") or chunk.get("speakers", "")
    return f"{title} | {speaker} | {raw_text[:100]}"


def generate_hypothetical_questions_batch(all_chunks: list) -> None:
    """
    Generate hypothetical_q in-place for every chunk in all_chunks.

    Caller must pass atomic + dialogue_group chunks in one flat list.
    Summary chunks must NOT be included — they keep their own text as page_content.

    Processing flow:
      1. Split all_chunks into batches of BATCH_SIZE.
      2. Each batch runs concurrently via ThreadPoolExecutor.
      3. Sleep 4 s between batches to respect Gemini rate limits.
      4. Retry logic lives in _generate_hq_single (one automatic retry per chunk).
      5. Fallback ensures every chunk gets a non-empty hypothetical_q.
      6. After all batches complete, results are mapped back by index order.
      7. Only then is each chunk["hypothetical_q"] set.
    """
    from google import genai as _genai

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        from app.config import Config
        api_key = getattr(Config, "GEMINI_API_KEY", "") or ""

    if not api_key:
        logger.warning("GEMINI_API_KEY not set — using text fallback for all hypothetical_q")
        for chunk in all_chunks:
            title   = chunk.get("meeting_title", "")
            speaker = chunk.get("speaker_name") or chunk.get("speakers", "")
            chunk["hypothetical_q"] = f"{title} | {speaker} | {chunk['text'][:100]}"
        return

    client = _genai.Client(api_key=api_key)
    total  = len(all_chunks)
    results: list = [None] * total

    for batch_start in range(0, total, BATCH_SIZE):
        batch_end     = min(batch_start + BATCH_SIZE, total)
        batch_indices = list(range(batch_start, batch_end))
        batch_chunks  = [all_chunks[i] for i in batch_indices]

        logger.info("HQ batch %d–%d / %d", batch_start + 1, batch_end, total)

        future_to_global: dict = {}
        with ThreadPoolExecutor(max_workers=len(batch_chunks)) as pool:
            for local_idx, chunk in enumerate(batch_chunks):
                fut = pool.submit(_generate_hq_single, chunk, client)
                future_to_global[fut] = batch_indices[local_idx]

            for future in as_completed(future_to_global, timeout=120):
                global_idx = future_to_global[future]
                try:
                    results[global_idx] = future.result(timeout=90)
                except Exception as exc:
                    # Covers TimeoutError, API errors, executor failures.
                    chunk   = all_chunks[global_idx]
                    title   = chunk.get("meeting_title", "")
                    speaker = chunk.get("speaker_name") or chunk.get("speakers", "")
                    results[global_idx] = f"{title} | {speaker} | {chunk['text'][:100]}"
                    logger.error("Executor error for chunk index %d: %s", global_idx, exc)

        if batch_end < total:
            time.sleep(4)

    # Map results back in index order — all batches must complete before any
    # chunk is written to ChromaDB (caller's responsibility).
    for chunk, hq in zip(all_chunks, results):
        chunk["hypothetical_q"] = hq or ""

    logger.info("HQ generation complete: %d chunks annotated", total)