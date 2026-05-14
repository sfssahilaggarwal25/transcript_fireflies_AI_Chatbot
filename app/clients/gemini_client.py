import logging
from google import genai
from app.config import Config

log = logging.getLogger(__name__)

_MODEL = "gemini-2.5-flash-lite"


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
