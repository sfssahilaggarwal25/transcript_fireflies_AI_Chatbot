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
    Fields marked PLACEHOLDER are upgraded in later phases.
    """
    chunks = []
    current_chunk = []
    current_speaker = None
    chunk_index = 1

    MAX_CHARS = 250
    MIN_CHARS = 80
    HARD_MIN = 15

    def flush_chunk(force=False):
        nonlocal current_chunk, chunk_index

        if not current_chunk:
            return

        chunk_text = " ".join(current_chunk).strip()

        if len(chunk_text) < HARD_MIN:
            current_chunk = []
            return

        if len(chunk_text) < MIN_CHARS and not force:
            return

        chunks.append({
            # Identity
            "chunk_id": f"{meeting_meta['meeting_id']}_{chunk_index}",

            # Level 2 — Meeting
            "meeting_id":     meeting_meta["meeting_id"],
            "meeting_title":  meeting_meta["title"],
            "meeting_date":   meeting_meta["date"],
            "meeting_number": meeting_meta.get("meeting_number", 0),
            "meeting_type":   "unknown",  # PLACEHOLDER — needs config (client_call / planning / etc.)

            # Level 3 — Speaker
            "speaker_name": current_speaker,
            "speaker_id":   _make_speaker_id(current_speaker),
            "speaker_role": "unknown",    # overridden by _stamp_project_and_roles() in webhook_handler

            # Level 4 — Chunk position
            "chunk_index":       chunk_index,
            "chunk_type":        "utterance",
            "is_meeting_summary": False,  # True only for summary chunks (added in Phase 1)

            # Level 5 — Content signals
            **_detect_signals(chunk_text),
            "sentiment":           "neutral",

            # Content
            "text":        chunk_text,
            "text_length": len(chunk_text),
        })

        chunk_index += 1
        current_chunk = []

    for s in sentences:
        text = s["text"].strip()
        speaker = s["speaker_name"]

        if len(text) < 8:
            continue

        if speaker != current_speaker:
            flush_chunk(force=True)
            current_chunk = []
            current_speaker = speaker

        projected = " ".join(current_chunk + [text])
        if len(projected) > MAX_CHARS:
            flush_chunk(force=True)

        current_chunk.append(text)

    flush_chunk(force=True)

    return chunks
