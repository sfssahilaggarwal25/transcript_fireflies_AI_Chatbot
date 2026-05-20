import re
import unicodedata

_DECISION_RE = re.compile(
    r"\b("
    r"we decided|"
    r"we have decided|"
    r"decision is|"
    r"final decision|"
    r"it's decided|"
    r"we agreed|"
    r"agreed to|"
    r"approved|"
    r"confirmed|"
    r"we chose|"
    r"settled on|"
    r"the plan is|"
    r"we concluded|"
    r"we'll go with|"
    r"let's go with|"
    r"going with|"
    r"move forward with|"
    r"we will use|"
    r"we will take|"
    r"we'll use|"
    r"we'll take|"
    r"use this|"
    r"stick with|"
    r"same one|"
    r"this is the approach|"
    r"this is what we'll use"
    r")\b",
    re.IGNORECASE,
)


_COMMITMENT_RE = re.compile(
    r"\b("
    r"i will|"
    r"i'll|"
    r"i can|"
    r"i'll check|"
    r"i'll confirm|"
    r"i'll send|"
    r"i'll share|"
    r"i'll update|"
    r"i'll get|"
    r"i'll make sure|"
    r"we will send|"
    r"we will share|"
    r"we will update|"
    r"we will follow up|"
    r"we will check|"
    r"we will handle|"
    r"we will deliver|"
    r"action item|"
    r"will be done|"
    r"by monday|"
    r"by tuesday|"
    r"by wednesday|"
    r"by thursday|"
    r"by friday|"
    r"tomorrow|"
    r"next week|"
    r"end of day|"
    r"end of week|"
    r"end of month"
    r")\b",
    re.IGNORECASE,
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


_FALSE_COMMITMENT_RE = re.compile(
    r"\b("
    r"we will calculate|"
    r"we will take|"
    r"we will use|"
    r"let's go to the next|"
    r"wait a second|"
    r"let's move on|"
    r"we'll come back"
    r")\b",
    re.IGNORECASE,
)


# ── Tier 2b: Confirmation/agreement signal ───────────────────────────────────
# Detects short but semantically rich responses: client confirming a decision
# ("Correct.", "Exactly.", "Agreed."), expressing doubt ("Are you sure?"),
# or disputing something ("That's wrong.", "I disagree.").
# Used only as a bypass signal — keeps these chunks from being quality-filtered.
# Not stored as a chunk metadata field (no schema change needed).

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


# ── Tier 2b: Junk detection ───────────────────────────────────────────────────

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
    """Return True if chunk text is too low quality to be indexed."""
    tokens = text.lower().split()
    if not tokens:
        return True
    # Drop repetitive text — but only if the repeated token is a filler/stopword.
    # Meaningful repetition ("no no no no" = strong disagreement) is kept.
    if len(set(tokens)) / len(tokens) < 0.4:
        most_repeated = max(set(tokens), key=tokens.count)
        if most_repeated in _STOPWORDS:
            return True
    # Drop if fewer than 2 meaningful words remain after removing stopwords/fillers.
    # Threshold lowered from 4 → 2 for meeting transcripts where short direct answers
    # ("OCA will be prepaid closed.", "Change in earnings.") carry full semantic weight.
    meaningful = [t for t in tokens if t not in _STOPWORDS and len(t) > 2]
    return len(meaningful) < 2


# ── Tier 2b: Topic-shift split ────────────────────────────────────────────────

_TOPIC_SHIFT_RE = re.compile(
    r"^(now[,\s]|next[,\s]|another point|separately[,\s]|also[,\s]|"
    r"moving on|switching to|on another|by the way)",
    re.IGNORECASE,
)


def _detect_signals(text: str) -> dict:
    """
    Detect decision / commitment / question signals from transcript chunk text.
    """

    cleaned = text.strip()

    if not cleaned:
        return {
            "contains_decision": False,
            "contains_commitment": False,
            "contains_question": False,
        }

    contains_decision = bool(_DECISION_RE.search(cleaned))

    contains_commitment = (
        bool(_COMMITMENT_RE.search(cleaned))
        and not bool(_FALSE_COMMITMENT_RE.search(cleaned))
    )

    contains_question = (
        cleaned.endswith("?")
        or bool(_QUESTION_START_RE.match(cleaned))
    )

    return {
        "contains_decision": contains_decision,
        "contains_commitment": contains_commitment,
        "contains_question": contains_question,
    }


def build_summary_chunk(summary_text: str, meeting_meta: dict, chunk_index: int) -> dict:
    return {
        "chunk_id":           f"{meeting_meta['meeting_id']}_summary",
        "meeting_id":         meeting_meta["meeting_id"],
        "meeting_title":      meeting_meta["title"],
        "meeting_date":       meeting_meta["date"],
        "meeting_number":     meeting_meta.get("meeting_number", 0),
        "meeting_type":       "unknown",
        "speaker_name":       "Meeting Summary",
        "speaker_id":         "meeting_summary",
        "speaker_role":       "unknown",
        "chunk_index":        chunk_index,
        "chunk_type":         "summary",
        "is_meeting_summary": True,
        "start_time":         None,
        "end_time":           None,
        "prev_chunk_id":      None,
        "next_chunk_id":      None,
        "contains_decision":  False,
        "contains_commitment": False,
        "contains_question":  False,
        "sentiment":          "neutral",
        "text":               summary_text,
        "text_length":        len(summary_text),
    }


def _make_speaker_id(speaker_name: str) -> str:
    normalized = unicodedata.normalize("NFKD", speaker_name)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "_", ascii_name.lower()).strip("_")


def create_chunks(sentences, meeting_meta):
    """
    Utterance-based chunking: one chunk = one speaker block.
    Chunk metadata follows the full 5-level schema.

    Tier 2a additions: start_time / end_time (ms from API), prev_chunk_id / next_chunk_id.
    Tier 2b additions: MAX_CHARS raised to 500, junk detection, topic-shift splits.
    """
    chunks = []
    current_chunk = []
    current_times = []   # list of (rawStartTimeMs, rawEndTimeMs) per sentence
    current_speaker = None
    chunk_index = 1

    MAX_CHARS = 500   # raised from 250 — reduces semantic splits at utterance boundaries
    MIN_CHARS = 80
    HARD_MIN = 15

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

        # Detect signals first — chunks containing a decision, commitment, or question
        # bypass the quality filter entirely. A short commitment like "I'll do it."
        # must survive even if it has few meaningful words.
        signals = _detect_signals(chunk_text)
        has_signal = (
            signals["contains_decision"]
            or signals["contains_commitment"]
            or signals["contains_question"]
            or bool(_CONFIRMATION_RE.search(chunk_text))
        )

        if not has_signal and _is_low_quality(chunk_text):
            current_chunk = []
            current_times = []
            return

        valid_starts = [ms for ms, _ in current_times if ms is not None]
        valid_ends   = [ms for _, ms in current_times if ms is not None]
        start_time = min(valid_starts) if valid_starts else None
        end_time   = max(valid_ends)   if valid_ends   else None

        chunks.append({
            # Identity
            "chunk_id": f"{meeting_meta['meeting_id']}_{chunk_index}",

            # Level 2 — Meeting
            "meeting_id":     meeting_meta["meeting_id"],
            "meeting_title":  meeting_meta["title"],
            "meeting_date":   meeting_meta["date"],
            "meeting_number": meeting_meta.get("meeting_number", 0),
            "meeting_type":   "unknown",

            # Level 3 — Speaker
            "speaker_name": current_speaker,
            "speaker_id":   _make_speaker_id(current_speaker),
            "speaker_role": "unknown",    # overridden by _stamp_project_and_roles()

            # Level 4 — Chunk position
            "chunk_index":        chunk_index,
            "chunk_type":         "utterance",
            "is_meeting_summary": False,

            # Tier 2a: timing (ms from meeting start; None when API doesn't provide it)
            "start_time": start_time,
            "end_time":   end_time,

            # Tier 2a: adjacency links (filled in post-loop pass below)
            "prev_chunk_id": None,
            "next_chunk_id": None,

            # Level 5 — Content signals (pre-computed above)
            **signals,
            "sentiment": "neutral",

            # Content
            "text":        chunk_text,
            "text_length": len(chunk_text),
        })

        chunk_index += 1
        current_chunk = []
        current_times = []

    for s in sentences:
        text      = s["text"].strip()
        speaker   = s["speaker_name"]
        start_ms  = s.get("start_time")
        end_ms    = s.get("end_time")

        if len(text) < 8:
            continue

        if speaker != current_speaker:
            flush_chunk(force=True)
            current_chunk = []
            current_times = []
            current_speaker = speaker
        elif current_chunk and _TOPIC_SHIFT_RE.match(text):
            # Same speaker but sentence opens a new topic — split here
            flush_chunk(force=True)

        projected = " ".join(current_chunk + [text])
        if len(projected) > MAX_CHARS:
            flush_chunk(force=True)

        current_chunk.append(text)
        current_times.append((start_ms, end_ms))

    flush_chunk(force=True)

    # ── Post-loop adjacency linking pass ──────────────────────────────────────
    # Only utterance chunks are linked — summary chunk is separate.
    for i, chunk in enumerate(chunks):
        chunk["prev_chunk_id"] = chunks[i - 1]["chunk_id"] if i > 0 else None
        chunk["next_chunk_id"] = chunks[i + 1]["chunk_id"] if i < len(chunks) - 1 else None

    return chunks
