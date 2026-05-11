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


class TranscriptValidationError(Exception):
    """Custom exception for transcript validation errors"""
    pass


def normalize_transcript(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize transcript data for both development and production
    
    Args:
        raw_data: Raw transcript data from API or constant
        
    Returns:
        Normalized transcript data with consistent structure
        
    Raises:
        TranscriptValidationError: If input data is invalid
    """
    if not raw_data:
        raise TranscriptValidationError("Raw data cannot be empty")
    
    if "data" not in raw_data:
        raise TranscriptValidationError("Invalid data structure: missing 'data' field")
    
    transcript = raw_data.get("data", {}).get("transcript")
    if not transcript:
        raise TranscriptValidationError("Invalid data structure: missing 'transcript' field")
    
    # Validate required fields
    required_fields = ["id", "title", "sentences"]
    for field in required_fields:
        if field not in transcript:
            raise TranscriptValidationError(f"Missing required field: {field}")
    
    # Validate sentences structure
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
            cleaned_sentences.append({**s, "text": cleaned})

    normalized = {
        "meeting_id": transcript["id"],
        "title": transcript["title"],
        "date": transcript.get("date"),
        "sentences": cleaned_sentences,
        "summary": transcript.get("summary", {})
    }
    
    dropped = len(sentences) - len(cleaned_sentences)
    logger.info(f"Normalized {len(sentences)} sentences → {len(cleaned_sentences)} after cleaning ({dropped} dropped as too short)")
    return normalized


def validate_transcript_data(transcript_data: Dict[str, Any]) -> bool:
    """Validate normalized transcript data structure"""
    try:
        required_keys = ["meeting_id", "title", "sentences", "summary"]
        return all(key in transcript_data for key in required_keys)
    except Exception:
        return False