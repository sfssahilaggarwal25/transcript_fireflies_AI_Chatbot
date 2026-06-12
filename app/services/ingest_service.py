"""
ingest_service.py — On-demand ingestion from a Fireflies meeting URL.

Called by:
  POST /ingest  in main.py           (FastAPI endpoint)
  Streamlit "Ingest New Meeting" UI  (direct Python call — no HTTP)

Flow
----
  1. Parse transcript_id from the Fireflies URL (split on "::")
  2. Check ChromaDB — skip if already ingested
  3. Verify project_id exists in projects.json
  4. Auto-register meeting_id in projects.json if not already present
  5. Fetch transcript from Fireflies GraphQL API (3 retries)
  6. Poll for Fireflies summary (up to 30 s)
  7. normalize → build_meeting_metadata → create_chunks
     → summary_chunk → stamp_project_and_roles
     → chunks_to_documents → store_documents → reset_vectorstore
  8. Return result dict
"""

import json
import logging
import os
import re
import time

from app.clients.fireflies_client import fetch_transcript, FirefliesAPIError
from app.clients.gemini_client import generate_meeting_summary
from app.core.documents.mapper import chunks_to_documents
from app.core.storage.chunk_store import store_documents, get_distinct_meeting_ids
from app.core.storage.db import reset_vectorstore
from app.core.storage.project_store import (
    get_project_for_meeting,
    get_speaker_role,
    reload_projects_cache,
)
from app.core.transcript.chunking import (
    create_chunks,
    build_summary_chunk,
    create_dialogue_groups,
    generate_hypothetical_questions_batch,
)
from app.core.transcript.metadata import build_meeting_metadata
from app.core.transcript.normalize import normalize_transcript

logger = logging.getLogger(__name__)

# projects.json lives two levels up from app/services/
_PROJECTS_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../projects.json")
)


class IngestError(Exception):
    """Raised when ingestion cannot proceed due to a known, recoverable condition."""


# ── URL parsing ───────────────────────────────────────────────────────────────

def parse_fireflies_url(url: str) -> str:
    """
    Extract transcript_id from a Fireflies meeting URL.

    Expected format:
      https://app.fireflies.ai/view/<slug>::<TRANSCRIPT_ID>

    Returns the transcript ID (e.g. "01KP8S4ZFHR6CGHJVK62931CC6").
    Raises IngestError on unrecognised format.
    """
    url = url.strip().rstrip("/")

    if "::" not in url:
        raise IngestError(
            f"Not a valid Fireflies meeting URL — expected '::' separator.\n"
            f"Example: https://app.fireflies.ai/view/Meeting-Title::01KP8S4ZFHR6CGHJVK62931CC6\n"
            f"Got: {url!r}"
        )

    transcript_id = url.split("::")[-1].strip()

    if not transcript_id:
        raise IngestError(f"Could not extract transcript ID from URL: {url!r}")

    # Fireflies IDs are uppercase alphanumeric, typically 26 characters (ULID format)
    if not re.match(r"^[A-Z0-9]{10,}$", transcript_id):
        raise IngestError(
            f"Parsed ID {transcript_id!r} looks invalid — expected uppercase alphanumeric "
            f"(e.g. '01KP8S4ZFHR6CGHJVK62931CC6'). Check the URL."
        )

    return transcript_id


# ── projects.json helpers ─────────────────────────────────────────────────────

def _load_projects() -> dict:
    with open(_PROJECTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_projects(data: dict) -> None:
    with open(_PROJECTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def register_meeting_in_project(project_id: str, meeting_id: str) -> bool:
    """
    Append meeting_id to projects.json under project_id if not already present.

    Returns True if the file was updated, False if meeting was already registered.
    Raises IngestError if project_id does not exist in projects.json.
    """
    data = _load_projects()

    if project_id not in data:
        raise IngestError(
            f"project_id '{project_id}' not found in projects.json. "
            f"Available: {list(data.keys())}"
        )

    existing = data[project_id].get("meeting_ids", [])
    if meeting_id in existing:
        logger.info("Meeting %s already in projects.json — skipping write", meeting_id)
        return False

    data[project_id].setdefault("meeting_ids", []).append(meeting_id)
    _save_projects(data)
    reload_projects_cache()

    logger.info(
        "Auto-registered meeting_id=%s → project_id=%s in projects.json",
        meeting_id, project_id,
    )
    return True


# ── Pipeline helpers ──────────────────────────────────────────────────────────

def _poll_summary(transcript_id: str, max_attempts: int = 6) -> dict | None:
    """Poll Fireflies until summary.overview is populated (up to 30 s)."""
    for attempt in range(max_attempts):
        try:
            data = fetch_transcript(transcript_id)
        except FirefliesAPIError as e:
            logger.warning("Summary poll %d/%d — API error: %s", attempt + 1, max_attempts, e)
            break
        transcript = (data or {}).get("data", {}).get("transcript")
        if transcript:
            summary = transcript.get("summary")
            if summary and summary.get("overview"):
                logger.info("Summary ready after %d poll(s)", attempt + 1)
                return summary
        logger.info("Summary poll %d/%d — not ready, retrying in 5 s", attempt + 1, max_attempts)
        time.sleep(5)
    logger.warning("Summary not available after %d polls — proceeding without", max_attempts)
    return None


def _resolve_summary(normalized_data: dict, chunks: list, meeting_title: str) -> str | None:
    fireflies_summary = normalized_data.get("summary", {})
    if fireflies_summary and fireflies_summary.get("overview"):
        logger.info("Summary source: Fireflies")
        return fireflies_summary["overview"]
    logger.info("Fireflies summary absent — generating via Gemini fallback")
    return generate_meeting_summary(chunks, meeting_title)


def _stamp_project_and_roles(chunks: list, meeting_id: str) -> bool:
    """Write project_id and speaker_role onto every chunk. Returns False on failure."""
    project_info = get_project_for_meeting(meeting_id)
    if not project_info:
        logger.error(
            "meeting_id '%s' not found in projects.json after registration — aborting", meeting_id
        )
        return False
    for chunk in chunks:
        chunk.update(project_info)
        # dialogue_group chunks have speaker_name="" (placeholder); get_speaker_role
        # returns "unknown" for empty/missing names — safe to call regardless.
        speaker = chunk.get("speaker_name", "")
        chunk["speaker_role"] = get_speaker_role(meeting_id, speaker) if speaker else "unknown"
    logger.info("Stamped → project_id=%s", project_info["project_id"])
    return True


def _ms(start: float) -> str:
    return f"{int((time.time() - start) * 1000)}ms"


# ── Public entry point ────────────────────────────────────────────────────────

def ingest_from_data(transcript_data: dict, project_id: str, meeting_number: int) -> dict:
    """
    Run the full ingest pipeline from already-fetched transcript data.

    Used by reingest_all.py when data is loaded from local cache — no Fireflies
    API call needed. The caller is responsible for deleting old ChromaDB chunks
    before calling this so the duplicate check passes.

    transcript_data: raw dict in the same shape fetch_transcript() returns, i.e.
        {"data": {"transcript": {id, title, date, sentences, summary}}}
    """
    t_start = time.time()

    raw = transcript_data.get("data", {}).get("transcript", {})
    meeting_id = raw.get("id", "unknown")

    logger.info("ingest_from_data | meeting_id=%s | project=%s", meeting_id, project_id)

    # Register in projects.json if not already present
    register_meeting_in_project(project_id, meeting_id)

    normalized_data = normalize_transcript(transcript_data)
    logger.info("Normalize → %d sentences", len(normalized_data["sentences"]))

    meeting_metadata = build_meeting_metadata(normalized_data)
    meeting_metadata["meeting_number"] = meeting_number

    # Pass 1 — atomic chunks (speaker-boundary accumulation)
    atomic_chunks = create_chunks(normalized_data["sentences"], meeting_metadata)
    logger.info("Atomic chunks → %d", len(atomic_chunks))

    # Resolve summary from atomic chunks BEFORE HQ generation overwrites text context
    summary_text = _resolve_summary(normalized_data, atomic_chunks, meeting_metadata["title"])

    # Pass 2 — dialogue group chunks (TF-IDF + rule-based merging)
    dialogue_chunks = create_dialogue_groups(atomic_chunks, meeting_metadata)
    logger.info("Dialogue groups → %d", len(dialogue_chunks))

    # HQ batch — all atomic + dialogue chunks in one pass (LLM call #1)
    all_content_chunks = atomic_chunks + dialogue_chunks
    generate_hypothetical_questions_batch(all_content_chunks)

    # Append summary chunk AFTER HQ generation (summary has no hypothetical_q)
    if summary_text:
        all_content_chunks.append(
            build_summary_chunk(summary_text, meeting_metadata, len(all_content_chunks) + 1)
        )

    if not _stamp_project_and_roles(all_content_chunks, meeting_id):
        raise IngestError(f"Project stamping failed for {meeting_id}")

    documents = chunks_to_documents(all_content_chunks)
    if not documents:
        raise IngestError("No valid documents produced")

    stored = store_documents(documents)
    reset_vectorstore()

    return {
        "status":         "success",
        "meeting_id":     meeting_id,
        "meeting_title":  meeting_metadata["title"],
        "meeting_number": meeting_number,
        "chunks_stored":  stored,
        "project_id":     project_id,
        "elapsed_ms":     int((time.time() - t_start) * 1000),
    }


def ingest_from_url(url: str, project_id: str) -> dict:
    """
    Full ingestion pipeline triggered by a Fireflies meeting URL.

    Parameters
    ----------
    url        : Fireflies meeting URL containing the transcript ID after "::"
    project_id : Target project (must exist in projects.json)

    Returns
    -------
    dict with keys:
      status          "success" | "already_ingested"
      meeting_id      Fireflies transcript ID
      meeting_title   Human-readable title from Fireflies API
      meeting_number  Ordinal within the project (1-indexed)
      chunks_stored   Number of chunks written to ChromaDB
      project_id      Project the meeting was stored under
      elapsed_ms      Total wall-clock time in milliseconds
    """
    t_start = time.time()

    # ── Step 1: Parse URL ─────────────────────────────────────────────────────
    meeting_id = parse_fireflies_url(url)
    logger.info("ingest_from_url | meeting_id=%s | project=%s", meeting_id, project_id)

    # ── Step 2: Duplicate check ───────────────────────────────────────────────
    already_stored = get_distinct_meeting_ids(project_id)
    if meeting_id in already_stored:
        logger.info("Meeting %s already in ChromaDB — skipping ingestion", meeting_id)
        return {
            "status":     "already_ingested",
            "meeting_id": meeting_id,
            "project_id": project_id,
            "elapsed_ms": int((time.time() - t_start) * 1000),
        }

    # ── Step 3: Register meeting in projects.json ─────────────────────────────
    register_meeting_in_project(project_id, meeting_id)

    # ── Step 4: Fetch transcript ───────────────────────────────────────────────
    # Two distinct failure modes handled separately:
    #   FirefliesAPIError (HTTP 4xx/5xx) → stop immediately, surface the real error
    #   Empty transcript (API returns 200 but data is null) → retry — meeting still processing
    t = time.time()
    logger.info("[1/6] Fetching transcript from Fireflies API...")
    transcript_data = None
    try:
        for attempt in range(3):
            data = fetch_transcript(meeting_id)
            if data and data.get("data", {}).get("transcript"):
                transcript_data = data
                logger.info("[1/6] Transcript fetched ✓  (%s, attempt %d)", _ms(t), attempt + 1)
                break
            logger.warning("[1/6] Transcript not ready (attempt %d/3) — retrying in 10 s", attempt + 1)
            if attempt < 2:
                time.sleep(10)
    except FirefliesAPIError as e:
        raise IngestError(str(e))

    if not transcript_data:
        raise IngestError(
            f"Fireflies API returned no transcript for '{meeting_id}' after 3 attempts. "
            f"The meeting may still be processing — try again in a few minutes."
        )

    # ── Step 5: Poll for summary ──────────────────────────────────────────────
    logger.info("[2/6] Polling for transcript summary...")
    summary = _poll_summary(meeting_id)
    if summary:
        transcript_data["data"]["transcript"]["summary"] = summary

    # ── Step 6: Normalize ─────────────────────────────────────────────────────
    t = time.time()
    normalized_data = normalize_transcript(transcript_data)
    logger.info(
        "[3/6] Normalize   → %d sentences  (%s)",
        len(normalized_data["sentences"]), _ms(t),
    )

    # ── Step 7: Metadata ──────────────────────────────────────────────────────
    t = time.time()
    meeting_metadata = build_meeting_metadata(normalized_data)
    # meeting_number = meetings already in ChromaDB + 1 (this one isn't stored yet)
    meeting_metadata["meeting_number"] = len(already_stored) + 1
    logger.info(
        "[4/6] Metadata    → date=%s  meeting_number=%d  (%s)",
        meeting_metadata["date"], meeting_metadata["meeting_number"], _ms(t),
    )

    # ── Step 8: Pass 1 — atomic chunks ───────────────────────────────────────
    t = time.time()
    atomic_chunks = create_chunks(normalized_data["sentences"], meeting_metadata)
    speakers = {c["speaker_name"] for c in atomic_chunks}
    logger.info(
        "[4/6] Atomic      → %d chunks  %d speakers  (%s)",
        len(atomic_chunks), len(speakers), _ms(t),
    )

    # ── Step 9: Resolve summary from atomic chunks ────────────────────────────
    # Called here — before HQ generation — because generate_meeting_summary()
    # reads chunk["text"] which must still contain the original transcript text.
    t = time.time()
    summary_text = _resolve_summary(normalized_data, atomic_chunks, meeting_metadata["title"])

    # ── Step 10: Pass 2 — dialogue group chunks ───────────────────────────────
    t = time.time()
    dialogue_chunks = create_dialogue_groups(atomic_chunks, meeting_metadata)
    logger.info("[4/6] Dialogue    → %d groups  (%s)", len(dialogue_chunks), _ms(t))

    # ── Step 11: Hypothetical question batch (LLM call #1) ───────────────────
    # One batch call for ALL atomic + dialogue chunks. Summary chunk excluded.
    t = time.time()
    all_content_chunks = atomic_chunks + dialogue_chunks
    generate_hypothetical_questions_batch(all_content_chunks)
    logger.info(
        "[4/6] HQ batch    → %d chunks annotated  (%s)",
        len(all_content_chunks), _ms(t),
    )

    # ── Step 12: Append summary chunk ─────────────────────────────────────────
    if summary_text:
        all_content_chunks.append(
            build_summary_chunk(summary_text, meeting_metadata, len(all_content_chunks) + 1)
        )
        logger.info("[4/6] Summary chunk added")
    else:
        logger.warning("[4/6] No summary — meeting stored without summary chunk")

    # ── Step 13: Stamp project + roles ────────────────────────────────────────
    t = time.time()
    if not _stamp_project_and_roles(all_content_chunks, meeting_id):
        raise IngestError(
            f"Project stamping failed for meeting {meeting_id} — check projects.json"
        )
    logger.info("[5/6] Stamp roles  (%s)", _ms(t))

    # ── Step 14: Embed + store ────────────────────────────────────────────────
    t = time.time()
    documents = chunks_to_documents(all_content_chunks)
    if not documents:
        raise IngestError("No valid documents produced from chunks — pipeline aborted")

    stored = store_documents(documents)
    logger.info("[6/6] ChromaDB    → %d documents stored  (%s)", stored, _ms(t))

    reset_vectorstore()

    elapsed_ms = int((time.time() - t_start) * 1000)
    logger.info(
        "ingest_from_url complete ✓  elapsed=%dms  chunks=%d  (atomic=%d  dialogue=%d)",
        elapsed_ms, stored, len(atomic_chunks), len(dialogue_chunks),
    )

    return {
        "status":          "success",
        "meeting_id":      meeting_id,
        "meeting_title":   meeting_metadata["title"],
        "meeting_number":  meeting_metadata["meeting_number"],
        "chunks_stored":   stored,
        "atomic_chunks":   len(atomic_chunks),
        "dialogue_groups": len(dialogue_chunks),
        "project_id":      project_id,
        "elapsed_ms":      elapsed_ms,
    }