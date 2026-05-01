from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


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
    
    normalized = {
        "meeting_id": transcript["id"],
        "title": transcript["title"],
        "sentences": sentences,
        "summary": transcript.get("summary", {})
    }
    
    logger.info(f"Normalized transcript with {len(sentences)} sentences")
    return normalized


def validate_transcript_data(transcript_data: Dict[str, Any]) -> bool:
    """Validate normalized transcript data structure"""
    try:
        required_keys = ["meeting_id", "title", "sentences", "summary"]
        return all(key in transcript_data for key in required_keys)
    except Exception:
        return False