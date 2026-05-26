import re
import unicodedata

_DECISION_RE = re.compile(
    r"\b(decided|decision|agreed|approved|finalized|confirmed|going with|"
    r"let'?s go with|move forward with|stick with|chosen|selected)\b",
    re.IGNORECASE
)


_COMMITMENT_RE = re.compile(
    r"\b(i will|i'?ll|we will|we'?ll|going to|will make sure|committ?ed to|"
    r"take ownership|my action item|action on me)\b",
    re.IGNORECASE
)
# Keep _FALSE_COMMITMENT_RE but add more exclusions:
_FALSE_COMMITMENT_RE = re.compile(
    r"\b(i will say|i'?ll say|i will note|we will see|we'?ll see|"
    r"that will|this will|it will|would be|will be able)\b",
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
    Detect decision / commitment / question / document_share / open_issue signals from chunk text.
    """

    cleaned = text.strip()

    if not cleaned:
        return {
            "contains_decision": False,
            "contains_commitment": False,
            "contains_question": False,
            "contains_document_share": False,
            "contains_open_issue": False,
        }

    contains_decision = bool(_DECISION_RE.search(cleaned))

    contains_commitment = (
        bool(_COMMITMENT_RE.search(cleaned))
        and not bool(_FALSE_COMMITMENT_RE.search(cleaned))
    )

    contains_question = (
        "?" in cleaned                          # ? anywhere in text, not just at end
        or bool(_QUESTION_START_RE.match(cleaned))
    )

    contains_document_share = bool(_DOCUMENT_SHARE_RE.search(cleaned))

    contains_open_issue = bool(_OPEN_ISSUE_RE.search(cleaned))

    return {
        "contains_decision": contains_decision,
        "contains_commitment": contains_commitment,
        "contains_question": contains_question,
        "contains_document_share": contains_document_share,
        "contains_open_issue": contains_open_issue,
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
        "contains_decision":       False,
        "contains_commitment":      False,
        "contains_question":        False,
        "contains_document_share":  False,
        "contains_open_issue":      False,
        "sentiment":                "neutral",
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

    Tier 2a additions: start_time / end_time (seconds, pre-converted by normalize.py),
    prev_chunk_id / next_chunk_id.
    Tier 2b additions: MAX_CHARS raised to 500, junk detection, topic-shift splits.
    """
    chunks = []
    current_chunk = []
    current_times = []   # list of (start_sec, end_sec) per sentence
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
            or signals["contains_document_share"]
            or signals["contains_open_issue"]
            or bool(_CONFIRMATION_RE.search(chunk_text))
        )

        if not has_signal and _is_low_quality(chunk_text):
            current_chunk = []
            current_times = []
            return

        valid_starts = [s for s, _ in current_times if s is not None]
        valid_ends   = [e for _, e in current_times if e is not None]
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
        text       = s["text"].strip()
        speaker    = s["speaker_name"]
        start_sec  = s.get("start_time")
        end_sec    = s.get("end_time")

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
        current_times.append((start_sec, end_sec))

    flush_chunk(force=True)

    # ── Post-loop adjacency linking pass ──────────────────────────────────────
    # Only utterance chunks are linked — summary chunk is separate.
    for i, chunk in enumerate(chunks):
        chunk["prev_chunk_id"] = chunks[i - 1]["chunk_id"] if i > 0 else None
        chunk["next_chunk_id"] = chunks[i + 1]["chunk_id"] if i < len(chunks) - 1 else None

    return chunks
