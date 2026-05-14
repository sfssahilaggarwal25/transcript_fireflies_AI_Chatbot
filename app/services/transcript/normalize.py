from typing import Dict, Any, List
import logging
import re

logger = logging.getLogger(__name__)

_FILLER_PATTERNS = [
    (re.compile(r'\b(um+|uh+|hmm+|hm+|er|erm)\b', re.IGNORECASE), ''),
    (re.compile(r'\byou know\b,?', re.IGNORECASE), ''),
    (re.compile(r'\b(\w+)\s+\1\b', re.IGNORECASE), r'\1'),  # "the the" → "the"
    (re.compile(r'\s{2,}'), ' '),
    (re.compile(r'\s+([,\.?!])'), r'\1'),
]


def _clean_sentence(text: str) -> str:
    for pattern, replacement in _FILLER_PATTERNS:
        text = pattern.sub(replacement, text)
    return text.strip()


def _clean_speaker_name(name: str) -> str:
    """Strip Fireflies platform IDs appended to speaker names.
    Example: 'Karan Middha U0438EU2CSX' → 'Karan Middha'
    """
    parts = name.strip().split()
    if len(parts) > 1:
        last = parts[-1]
        if re.match(r'^[A-Z0-9]{6,}$', last):
            parts = parts[:-1]
    return " ".join(parts)


class TranscriptValidationError(Exception):
    pass


def normalize_transcript(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    if not raw_data:
        raise TranscriptValidationError("Raw data cannot be empty")

    if "data" not in raw_data:
        raise TranscriptValidationError("Invalid data structure: missing 'data' field")

    transcript = raw_data.get("data", {}).get("transcript")
    if not transcript:
        raise TranscriptValidationError("Invalid data structure: missing 'transcript' field")

    required_fields = ["id", "title", "sentences"]
    for field in required_fields:
        if field not in transcript:
            raise TranscriptValidationError(f"Missing required field: {field}")

    sentences = transcript.get("sentences", [])
    if not isinstance(sentences, list):
        raise TranscriptValidationError("Sentences must be a list")

    for i, sentence in enumerate(sentences):
        if not isinstance(sentence, dict):
            raise TranscriptValidationError(f"Sentence {i} must be a dictionary")
        if "text" not in sentence:
            raise TranscriptValidationError(f"Sentence {i} missing 'text' field")
        if "speaker_name" not in sentence:
            raise TranscriptValidationError(f"Sentence {i} missing 'speaker_name' field")

    cleaned_sentences = []
    for s in sentences:
        cleaned = _clean_sentence(s["text"])
        if len(cleaned) >= 8:
            cleaned_sentences.append({
                **s,
                "text": cleaned,
                "speaker_name": _clean_speaker_name(s["speaker_name"]),
            })

    summary_raw = transcript.get("summary")
    normalized = {
        "meeting_id": transcript["id"],
        "title": transcript["title"],
        "date": transcript.get("date"),
        "sentences": cleaned_sentences,
        "summary": summary_raw if isinstance(summary_raw, dict) else {},
    }

    dropped = len(sentences) - len(cleaned_sentences)
    logger.info(f"Normalized {len(sentences)} sentences → {len(cleaned_sentences)} after cleaning ({dropped} dropped as too short)")
    return normalized


def validate_transcript_data(transcript_data: Dict[str, Any]) -> bool:
    try:
        required_keys = ["meeting_id", "title", "sentences", "summary"]
        return all(key in transcript_data for key in required_keys)
    except Exception:
        return False


def group_by_speaker(raw: List[Dict], max_words: int = 80) -> List[Dict]:
    """Merge consecutive same-speaker lines from Fireflies JSON."""
    if not raw:
        return []

    grouped: List[Dict] = []

    for item in raw:
        text = str(item.get("text") or "").strip()
        speaker_raw = str(item.get("speaker_name") or "").strip()

        if not text or not speaker_raw:
            continue

        speaker = _clean_speaker_name(speaker_raw)

        if grouped and grouped[-1]["speaker_name"] == speaker:
            current_words = len(grouped[-1]["text"].split())
            new_words = len(text.split())
            if current_words + new_words <= max_words:
                grouped[-1]["text"] += " " + text
            else:
                grouped.append({"text": text, "speaker_name": speaker})
        else:
            grouped.append({"text": text, "speaker_name": speaker})

    logger.info(f"group_by_speaker: {len(raw)} raw → {len(grouped)} grouped lines")
    return grouped
