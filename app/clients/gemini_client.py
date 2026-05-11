import logging
import google.generativeai as genai
from app.config import Config

log = logging.getLogger(__name__)

_MODEL = "gemini-1.5-flash"


def generate_meeting_summary(chunks: list[dict], meeting_title: str) -> str | None:
    if not Config.GEMINI_API_KEY:
        log.warning("GEMINI_API_KEY not set — cannot generate fallback summary")
        return None

    try:
        genai.configure(api_key=Config.GEMINI_API_KEY)
        model = genai.GenerativeModel(_MODEL)

        transcript_text = "\n".join(
            f"{c['speaker_name']}: {c['text']}"
            for c in chunks
        )

        prompt = (
            f'Summarize this meeting titled "{meeting_title}" in 4-6 sentences. '
            f"Cover: main topics discussed, key decisions made, and any action items or commitments.\n\n"
            f"Transcript:\n{transcript_text}\n\nSummary:"
        )

        response = model.generate_content(prompt)
        summary = response.text.strip()
        log.info(f"Gemini summary generated ({len(summary)} chars)")
        return summary

    except Exception as e:
        log.error(f"Gemini summary generation failed: {e}")
        return None
