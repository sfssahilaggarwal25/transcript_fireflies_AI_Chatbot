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


# Max transcript chars sent to the model (~20k tokens — well within gemini-flash context window).
# Transcripts beyond this are truncated; a warning is logged so long meetings are visible in logs.
_SUMMARY_MAX_TRANSCRIPT_CHARS = 80_000

# Low temperature → consistent, predictable formatting across runs.
# High temperature would produce creative prose but unpredictable section structure.
_SUMMARY_TEMPERATURE = 0.1

# Hard cap on summary output length (~800 tokens covers 6 bullets + action items + key topics).
# Without this, Flash Lite can produce runaway output for long meetings (observed: 283k chars).
_SUMMARY_MAX_OUTPUT_TOKENS = 1024


def generate_meeting_summary(chunks: list[dict], meeting_title: str) -> str | None:
    """
    Fallback summary generator used when Fireflies does not provide one.
    Produces the same three sections Fireflies generates:
      - Overview    : 4-6 bullet points with bold topic headers
      - Action Items : grouped by speaker with (MM:SS) timestamps
      - Key Topics  : 5-8 comma-separated technical terms
    """
    if not Config.GEMINI_API_KEY:
        log.warning("GEMINI_API_KEY not set — cannot generate fallback summary")
        return None

    try:
        client = genai.Client(api_key=Config.GEMINI_API_KEY)

        # ── Build transcript text with timestamps ──────────────────────────
        def _fmt_ts(seconds) -> str:
            if seconds is None:
                return ""
            m, s = divmod(int(seconds), 60)
            return f"({m:02d}:{s:02d})"

        transcript_text = "\n".join(
            f"{_fmt_ts(c.get('start_time'))} {c['speaker_name']}: {c['text']}"
            for c in chunks
            if not c.get("is_meeting_summary")
        )

        # Fix 1 — Transcript length guard
        # Truncate before sending; log clearly so long meetings are visible in ops logs.
        if len(transcript_text) > _SUMMARY_MAX_TRANSCRIPT_CHARS:
            transcript_text = transcript_text[:_SUMMARY_MAX_TRANSCRIPT_CHARS]
            log.warning(
                "Summary prompt: transcript truncated to %d chars (original meeting may be very long)",
                _SUMMARY_MAX_TRANSCRIPT_CHARS,
            )

        # ── Prompt ────────────────────────────────────────────────────────
        prompt = f"""\
You are summarizing a project meeting transcript for a project manager.
Produce exactly three sections — Overview, Action Items, Key Topics — in that order.

OUTPUT FORMAT RULES (read carefully before generating):
- Fix 2: Start your response DIRECTLY with "## Overview" — no introduction, no preamble, no "Sure!" or "Here is the summary:".
- Fix 3: Use EXACTLY these section headers, nothing else: "## Overview", "## Action Items", "## Key Topics". Do NOT use # (H1), bold (**Overview**), or any other variation.
- Fix 5: In Action Items, every item must be grouped under the EXACT speaker name from the transcript. Never use generic labels like "Team", "Everyone", or "All".

Study both examples below, then apply the same format to the real transcript.

════════════════════════════════════════════
EXAMPLE 1 — meeting with action items:
════════════════════════════════════════════
INPUT:
(00:30) Priya Sharma: We need to decide whether to use Redis pub/sub or a double queue for messaging.
(01:10) Rohan Mehta: I reviewed both options. Redis is simpler and handles our load. Estimated two days to implement.
(02:00) Priya Sharma: Agreed. Rohan, please implement Redis and share a test report by Friday.
(02:45) Rohan Mehta: Will do. I also noticed the login module throws a 403 error on token refresh. Should I fix that too?
(03:20) Priya Sharma: Yes, fix it and document the root cause. We will review the deploy checklist next meeting.

OUTPUT:
## Overview
- **Messaging Architecture Decided:** Team selected Redis pub/sub over a double queue system based on simplicity and load capacity.
- **Implementation Timeline Set:** Redis integration is estimated at two days, with a test report due by Friday.
- **Login Bug Identified:** A 403 error on token refresh was flagged and will be fixed alongside Redis work.
- **Deploy Checklist Deferred:** Review of the deployment checklist is scheduled for the next meeting.

## Action Items
**Rohan Mehta**
Implement Redis pub/sub for messaging and share test report by Friday (02:00)
Fix 403 error on token refresh and document the root cause (02:45)

**Priya Sharma**
Review deploy checklist in the next meeting (03:20)

## Key Topics
Redis pub/sub, double queue, login module, token refresh, deploy checklist

════════════════════════════════════════════
EXAMPLE 2 — Fix 4: meeting with NO action items:
════════════════════════════════════════════
INPUT:
(00:15) Aisha Khan: Let us do a quick catch-up on where the mobile team stands.
(00:45) Dev Patel: The iOS build is stable. We shipped the hotfix last night. Nothing pending.
(01:20) Aisha Khan: Great. Android?
(01:35) Dev Patel: Android is also green. No blockers. We are waiting on the design team for the next sprint assets.
(02:10) Aisha Khan: Understood. Design will share assets by end of week. That is all for today.

OUTPUT:
## Overview
- **iOS Release Stable:** The hotfix was shipped successfully last night with no outstanding issues.
- **Android Build Green:** Android has no blockers and is waiting on design assets for the next sprint.
- **Design Assets Incoming:** The design team will deliver next sprint assets by end of week.

## Action Items
None

## Key Topics
iOS build, Android build, hotfix, design assets, mobile team, sprint planning
════════════════════════════════════════════

Now summarize the real meeting below. Follow all OUTPUT FORMAT RULES above.
Meeting title: "{meeting_title}"

Additional rules:
- Overview: 4-6 bullets, bold topic header + exactly one sentence, focus on decisions/outcomes/blockers/progress
- Action Items: every concrete task or commitment, grouped under the exact speaker name, each ending with (MM:SS); write "None" if there are truly no action items
- Key Topics: 5-8 specific technical terms, module names, or project-specific concepts — NOT generic words like "meeting", "team", or "discussion"

Transcript:
{transcript_text}
"""

        # Fix 6 — Low temperature + max_output_tokens cap (prevents runaway output on long meetings)
        response = client.models.generate_content(
            model=_MODEL,
            contents=prompt,
            config={
                "temperature": _SUMMARY_TEMPERATURE,
                "max_output_tokens": _SUMMARY_MAX_OUTPUT_TOKENS,
            },
        )
        summary = response.text.strip()
        log.info("Gemini summary generated (%d chars)", len(summary))
        return summary

    except Exception as e:
        log.error("Gemini summary generation failed: %s", e)
        return None
