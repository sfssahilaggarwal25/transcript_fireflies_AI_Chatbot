from typing import Dict, Any, List
import logging
import re
import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()
logger = logging.getLogger(__name__)

# Initialize Gemini API
try:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    genai.configure(api_key=api_key)
    GEMINI_MODEL = genai.GenerativeModel('gemini-2.5-flash')
    logger.info("Gemini API initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Gemini API: {e}")
    GEMINI_MODEL = None

# Constants for Gemini cleaning
SAFE_CONFIRMATIONS = {
    "yes",
    "no", 
    "correct",
    "approved",
    "confirmed",
    "done",
    "agreed",
    "right"
}

SYSTEM_PROMPT = """
You are cleaning meeting transcript text for an enterprise retrieval system.

Your job:
- remove filler words
- remove repeated phrases
- remove ASR transcription artifacts
- fix broken sentence flow

VERY IMPORTANT:
- preserve exact business meaning
- preserve technical terminology
- preserve calculations/formulas
- preserve approvals/confirmations
- preserve intent
- preserve conversational meaning

DO NOT:
- summarize
- paraphrase heavily
- change technical terms
- remove approvals like "yes", "approved", "correct"
- invent information

Return ONLY cleaned text.
"""


class TranscriptValidationError(Exception):
    """Custom exception for transcript validation errors"""
    pass

def _clean_speaker_name(name: str) -> str:
    """
    Fireflies sometimes appends platform user IDs to speaker names.
    Example: "Karan Middha U0438EU2CSX" → "Karan Middha"
    
    Pattern: strip any trailing token that is ALL uppercase letters + digits
    and looks like a system ID (length > 4, mixed alnum, no spaces).
    """
    parts = name.strip().split()
    if len(parts) > 1:
        last = parts[-1]
        # ID pattern: all uppercase+digits, 6+ chars, no lowercase
        if re.match(r'^[A-Z0-9]{6,}$', last):
            parts = parts[:-1]
    return " ".join(parts)


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


# ──────────────────────────────────────────────
# STEP 1: Group raw lines by speaker first
# This is a pre-step before Gemini merging
# ──────────────────────────────────────────────
def group_by_speaker(raw: List[Dict], max_words: int = 80) -> List[Dict]:
    """
    Merge consecutive same-speaker lines from Fireflies JSON.

    Production guards:
    - Skips lines with empty text or missing speaker
    - Strips platform IDs from speaker names (e.g. "Karan U0438EU2CSX")
    - Merges same-speaker lines up to max_words
    - Splits into new entry if max_words would be exceeded
    - Handles: empty input, single line, unicode names, 
                whitespace-only text, 200-word utterances,
                rapid A/B/A/B alternation

    Args:
        raw: List of {"text": str, "speaker_name": str} dicts
        max_words: Max words per grouped entry before forcing a new one

    Returns:
        Cleaned, grouped list — ready for Gemini clean step
    """
    if not raw:
        return []

    grouped: List[Dict] = []
    cut_off_count = 0

    for item in raw:
        # ── Guard: skip missing fields ──
        text = item.get("text", "").strip()
        speaker_raw = item.get("speaker_name", "").strip()

        if not text or not speaker_raw:
            logger.debug(f"Skipping empty line: {item}")
            continue

        # ── Normalize speaker name ──
        speaker = _clean_speaker_name(speaker_raw)

        # ── Detect cut-off sentences (ends without punctuation) ──
        if len(text.split()) > 8 and text[-1] not in ".?!":
            cut_off_count += 1

        # ── Merge or append ──
        if grouped and grouped[-1]["speaker_name"] == speaker:
            current_words = len(grouped[-1]["text"].split())
            new_words = len(text.split())

            if (
                current_words + new_words <= max_words
                or text[-1] not in ".?!"
            ):
                # Safe to merge — same speaker, within limit or sentence doesn't end with punctuation
                grouped[-1]["text"] += " " + text
            else:
                # Same speaker but too long — start new entry
                grouped.append({"text": text, "speaker_name": speaker})
        else:
            # New speaker — always start fresh
            grouped.append({"text": text, "speaker_name": speaker})

    if cut_off_count:
        logger.warning(
            f"group_by_speaker: {cut_off_count} cut-off sentences detected "
            f"(Fireflies mid-sentence splits). Gemini clean step will handle these."
        )

    logger.info(
        f"group_by_speaker: {len(raw)} raw → {len(grouped)} grouped lines"
    )
    return grouped



def clean_with_gemini(
    grouped_transcript: List[Dict],
    model: genai.GenerativeModel = None
) -> List[Dict]:
    """
    Clean transcript text using Gemini AI while preserving critical confirmations.
    
    Args:
        grouped_transcript: List of {"text": str, "speaker_name": str} dicts
        model: Gemini GenerativeModel instance
        
    Returns:
        List of cleaned transcript entries
    """
    # Use provided model or fall back to global instance
    effective_model = model or GEMINI_MODEL
    
    if not effective_model:
        logger.warning("Gemini model not available, returning original transcript")
        return grouped_transcript
    
    cleaned_output = []

    for item in grouped_transcript:
        text = item["text"].strip()
        speaker_name = item["speaker_name"]

        # Preserve critical confirmations without AI processing
        if text.lower() in SAFE_CONFIRMATIONS:
            cleaned_output.append({
                "speaker_name": speaker_name,
                "text": text
            })
            continue

        # Process with Gemini for non-critical text
        cleaned_text = _clean_text_with_gemini(text, effective_model)
        
        cleaned_output.append({
            "speaker_name": speaker_name,
            "text": cleaned_text
        })

    logger.info(f"clean_with_gemini: processed {len(cleaned_output)} entries")
    return cleaned_output


def _clean_text_with_gemini(text: str, model: genai.GenerativeModel) -> str:
    """
    Helper function to clean individual text with Gemini.
    
    Args:
        text: Text to clean
        model: Gemini GenerativeModel instance
        
    Returns:
        Cleaned text or original text if cleaning fails
    """
    try:
        prompt = f"""
            Clean this meeting transcript text.

            Transcript:
            {text}
        """

        response = model.generate_content(SYSTEM_PROMPT + "\n\n" + prompt)
        
        # Check if response has valid content
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            
            # Check finish reason
            if candidate.finish_reason == 1:  # STOP
                if hasattr(candidate, 'content') and candidate.content.parts:
                    cleaned_text = response.text.strip()
                    return cleaned_text if cleaned_text else text
                else:
                    logger.warning(f"Gemini returned empty content for text: {text[:50]}...")
                    return text
            elif candidate.finish_reason == 2:  # MAX_TOKENS
                logger.warning(f"Gemini response truncated for text: {text[:50]}...")
                if hasattr(candidate, 'content') and candidate.content.parts:
                    cleaned_text = response.text.strip()
                    return cleaned_text if cleaned_text else text
                return text
            elif candidate.finish_reason == 3:  # SAFETY
                logger.warning(f"Gemini safety filtered text: {text[:50]}...")
                return text
            else:
                logger.warning(f"Gemini unexpected finish reason {candidate.finish_reason} for text: {text[:50]}...")
                return text
        else:
            logger.warning(f"Gemini returned no candidates for text: {text[:50]}...")
            return text

    except Exception as e:
        logger.exception(f"Gemini cleanup failed for text: {text[:50]}... - {e}")
        return text