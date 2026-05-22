import logging
import time
from google import genai
from app.config import Config

log = logging.getLogger(__name__)

_MODEL = "gemini-2.5-flash-lite"

# Retry settings for transient API errors (503 overload, 429 rate-limit)
_MAX_RETRIES   = 3
_RETRY_DELAYS  = [2, 5, 10]   # seconds between attempts


def _is_retryable(exc: Exception) -> bool:
    """Return True for 503 / 429 HTTP errors that warrant a retry."""
    msg = str(exc).lower()
    return "503" in msg or "429" in msg or "unavailable" in msg or "rate limit" in msg


def call_gemini(prompt: str) -> str:
    """
    General-purpose LLM call with automatic retry on transient errors.
    Retries up to 3 times on 503 (overloaded) / 429 (rate-limited) responses.
    Raises RuntimeError if the API key is missing or all retries are exhausted.
    """
    if not Config.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set — cannot generate answer")
    client = genai.Client(api_key=Config.GEMINI_API_KEY)

    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES):
        try:
            response = client.models.generate_content(model=_MODEL, contents=prompt)
            return response.text.strip()
        except Exception as exc:
            last_exc = exc
            if _is_retryable(exc) and attempt < _MAX_RETRIES - 1:
                delay = _RETRY_DELAYS[attempt]
                log.warning(
                    "Gemini API transient error (attempt %d/%d) — retrying in %ds: %s",
                    attempt + 1, _MAX_RETRIES, delay, exc,
                )
                time.sleep(delay)
            else:
                raise

    raise RuntimeError(f"Gemini API failed after {_MAX_RETRIES} attempts") from last_exc


def call_gemini_raw(prompt: str) -> str:
    """
    Same as call_gemini() but re-raises exceptions without RuntimeError wrapping.
    Used by understand_query() which catches and falls back to regex on failure.
    """
    if not Config.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set")
    client = genai.Client(api_key=Config.GEMINI_API_KEY)

    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES):
        try:
            response = client.models.generate_content(model=_MODEL, contents=prompt)
            return response.text.strip()
        except Exception as exc:
            last_exc = exc
            if _is_retryable(exc) and attempt < _MAX_RETRIES - 1:
                delay = _RETRY_DELAYS[attempt]
                log.warning(
                    "Gemini API transient error (attempt %d/%d) — retrying in %ds: %s",
                    attempt + 1, _MAX_RETRIES, delay, exc,
                )
                time.sleep(delay)
            else:
                raise

    raise last_exc  # type: ignore[misc]


def generate_meeting_summary(chunks: list[dict], meeting_title: str) -> str | None:
    if not Config.GEMINI_API_KEY:
        log.warning("GEMINI_API_KEY not set — cannot generate fallback summary")
        return None

    try:
        client = genai.Client(api_key=Config.GEMINI_API_KEY)

        transcript_text = "\n".join(
            f"{c['speaker_name']}: {c['text']}"
            for c in chunks
        )

        prompt = (
            f'Summarize this meeting titled "{meeting_title}" in 4-6 sentences. '
            f"Cover: main topics discussed, key decisions made, and any action items or commitments.\n\n"
            f"Transcript:\n{transcript_text}\n\nSummary:"
        )

        response = client.models.generate_content(model=_MODEL, contents=prompt)
        summary = response.text.strip()
        log.info(f"Gemini summary generated ({len(summary)} chars)")
        return summary

    except Exception as e:
        log.error(f"Gemini summary generation failed: {e}")
        return None
