import time
from app.config import Config, CONSTANT_TRANSCRIPT
from app.logger import get_logger

from app.core.documents.mapper import chunks_to_documents
from app.core.storage.chunk_store import store_documents
from app.core.transcript.metadata import build_meeting_metadata
from app.core.transcript.chunking import create_chunks, build_summary_chunk
from app.core.transcript.normalize import normalize_transcript
from app.clients.fireflies_client import fetch_transcript
from app.clients.gemini_client import generate_meeting_summary
from app.core.storage.project_store import get_project_for_meeting, get_speaker_role
from app.core.storage.chunk_store import get_distinct_meeting_ids
from app.core.storage.db import reset_vectorstore

log = get_logger("webhook_handler")


def _resolve_meeting_number(project_id: str, meeting_id: str) -> int:
    """Return meeting number for this meeting — 1-indexed, based on meetings already stored."""
    existing = get_distinct_meeting_ids(project_id)
    if meeting_id in existing:
        ordered = sorted(existing)
        return ordered.index(meeting_id) + 1
    return len(existing) + 1


def _stamp_project_and_roles(chunks, meeting_id) -> bool:
    """Stamp project_id, company fields, and speaker_role onto every chunk.
    Returns False if meeting is not mapped in projects.json — caller must not store.
    """
    project_info = get_project_for_meeting(meeting_id)
    if not project_info:
        log.warning(f"meeting_id '{meeting_id}' not found in projects.json — add it before re-triggering")
        log.warning("Chunks will NOT be stored. Pipeline aborted.")
        return False

    for chunk in chunks:
        chunk.update(project_info)
        chunk["speaker_role"] = get_speaker_role(meeting_id, chunk["speaker_name"])

    log.info(f"Stamped → project_id={project_info['project_id']}  company={project_info['company_name']}")
    return True


def wait_for_summary(transcript_id):
    for attempt in range(6):
        data = fetch_transcript(transcript_id)

        if not data or "data" not in data:
            log.warning(f"Summary poll {attempt+1}/6 — no data yet, retrying in 5s")
            time.sleep(5)
            continue

        transcript = data.get("data", {}).get("transcript")
        if not transcript:
            log.warning(f"Summary poll {attempt+1}/6 — transcript not ready, retrying in 5s")
            time.sleep(5)
            continue

        summary = transcript.get("summary")
        if summary and summary.get("overview"):
            log.info(f"Summary available after {attempt+1} poll(s)")
            return summary

        time.sleep(5)

    log.warning("Summary not available after 6 polls — continuing without it")
    return None


def _resolve_summary(normalized_data: dict, chunks: list[dict], meeting_title: str) -> str | None:
    """Return summary text — Fireflies overview first, Gemini fallback if missing."""
    fireflies_summary = normalized_data.get("summary", {})
    if fireflies_summary and fireflies_summary.get("overview"):
        log.info("Summary source: Fireflies")
        return fireflies_summary["overview"]

    log.info("Fireflies summary not available — generating via Gemini")
    return generate_meeting_summary(chunks, meeting_title)


async def handle_fireflies_webhook(payload):
    pipeline_start = time.time()

    # ── DEVELOPMENT MODE ──────────────────────────────────────────
    if Config.DEVELOPMENT_MODE:
        log.info("[DEV MODE] Using hardcoded CONSTANT_TRANSCRIPT")

        transcript_list = CONSTANT_TRANSCRIPT.get("data", {}).get("transcript", [])
        if not isinstance(transcript_list, list):
            transcript_list = [transcript_list]

        all_chunks = []
        for idx, transcript_item in enumerate(transcript_list, 1):
            meeting_id_raw = transcript_item.get("id", f"unknown_{idx}")
            log.info(f"[DEV] ── Transcript {idx}/{len(transcript_list)}: id={meeting_id_raw} ──")

            t = time.time()
            wrapped = {"data": {"transcript": transcript_item}}
            normalized_data = normalize_transcript(wrapped)
            log.info(f"[1/6] Normalize   → {len(normalized_data['sentences'])} sentences  ({_ms(t)})")

            t = time.time()
            meeting_metadata = build_meeting_metadata(normalized_data)

            project_info = get_project_for_meeting(normalized_data["meeting_id"])
            if not project_info:
                log.warning(f"[DEV] meeting_id '{normalized_data['meeting_id']}' not in projects.json — skipping")
                continue

            existing_ids = get_distinct_meeting_ids(project_info["project_id"])
            if normalized_data["meeting_id"] in existing_ids:
                log.info(f"[DEV] meeting_id '{normalized_data['meeting_id']}' already in ChromaDB — skipping")
                continue

            meeting_metadata["meeting_number"] = _resolve_meeting_number(
                project_info["project_id"], normalized_data["meeting_id"]
            )
            log.info(f"[2/6] Metadata    → meeting_id={meeting_metadata['meeting_id']}  date={meeting_metadata['date']}  meeting_number={meeting_metadata['meeting_number']}  ({_ms(t)})")

            t = time.time()
            chunks = create_chunks(normalized_data["sentences"], meeting_metadata)
            speakers = set(c["speaker_name"] for c in chunks)
            log.info(f"[3/6] Chunking    → {len(chunks)} chunks  {len(speakers)} speakers  ({_ms(t)})")

            t = time.time()
            summary_text = _resolve_summary(normalized_data, chunks, meeting_metadata["title"])
            if summary_text:
                chunks.append(build_summary_chunk(summary_text, meeting_metadata, len(chunks) + 1))
                log.info(f"[3/6] Summary chunk added  ({_ms(t)})")
            else:
                log.warning("[3/6] No summary available — meeting stored without summary chunk")

            t = time.time()
            if not _stamp_project_and_roles(chunks, normalized_data["meeting_id"]):
                continue
            log.info(f"[4/6] Stamp roles → project_id={project_info['project_id']}  meeting_number={meeting_metadata['meeting_number']}  ({_ms(t)})")

            documents = chunks_to_documents(chunks)
            log.info(f"[5/6] langchain documents is created → {len(documents)}")

            if not documents:
                log.error("No valid documents generated from chunks. Skipping transcript.")
                continue

            stored = store_documents(documents)
            log.info(f"[6/6] ChromaDB    → {stored} documents stored  ({_ms(t)})")

            all_chunks.extend(chunks)

        reset_vectorstore()
        log.info(f"Pipeline complete ✓  total={_ms(pipeline_start)}  transcripts_processed={len(all_chunks) > 0}")
        return all_chunks

    # ── PRODUCTION MODE ───────────────────────────────────────────
    log.info("Production mode — resolving transcript ID from payload")

    transcript_id = None
    for attempt in range(3):
        transcript_id = (
            payload.get("transcript_id")
            or payload.get("meetingId")
            or payload.get("meeting_id")
            or payload.get("data", {}).get("transcript_id")
        )
        if transcript_id:
            log.info(f"Transcript ID resolved: {transcript_id}")
            break
        log.warning(f"Transcript ID not in payload yet (attempt {attempt+1}/3) — waiting 10s")
        time.sleep(10)

    if not transcript_id:
        log.error("Transcript ID not found after 3 attempts — dropping webhook")
        return None

    # Step 1 — Fetch transcript
    log.info(f"[1/6] Fetching transcript from Fireflies API...")
    transcript_data = None
    for attempt in range(3):
        transcript_data = fetch_transcript(transcript_id)
        if transcript_data and "data" in transcript_data and transcript_data["data"].get("transcript"):
            log.info(f"[1/6] Transcript fetched ✓  (attempt {attempt+1})")
            break
        log.warning(f"[1/6] Transcript not ready (attempt {attempt+1}/3) — waiting 10s")
        time.sleep(10)

    if not transcript_data or not transcript_data["data"].get("transcript"):
        log.error("[1/6] Failed to fetch transcript after 3 attempts — dropping")
        return None

    # Step 2 — Wait for summary
    log.info("[2/6] Polling for transcript summary...")
    summary = wait_for_summary(transcript_id)
    if summary:
        transcript_data["data"]["transcript"]["summary"] = summary
    else:
        log.warning("[2/6] Proceeding without summary")

    # Step 3 — Normalize
    t = time.time()
    normalized_data = normalize_transcript(transcript_data)
    log.info(f"[3/6] Normalize   → {len(normalized_data['sentences'])} sentences  meeting_id={normalized_data['meeting_id']}  ({_ms(t)})")

    # Step 4 — Metadata + chunk
    t = time.time()
    meeting_metadata = build_meeting_metadata(normalized_data)
    project_info = get_project_for_meeting(normalized_data["meeting_id"])
    if not project_info:
        log.warning(f"meeting_id '{normalized_data['meeting_id']}' not in projects.json — add it and re-trigger")
        return None
    meeting_metadata["meeting_number"] = _resolve_meeting_number(
        project_info["project_id"], normalized_data["meeting_id"]
    )
    log.info(f"[4/6] Metadata    → date={meeting_metadata['date']}  meeting_number={meeting_metadata['meeting_number']}  ({_ms(t)})")

    t = time.time()
    chunks = create_chunks(normalized_data["sentences"], meeting_metadata)
    speakers = set(c["speaker_name"] for c in chunks)
    log.info(f"[4/6] Chunking    → {len(chunks)} chunks  {len(speakers)} speakers  ({_ms(t)})")

    t = time.time()
    summary_text = _resolve_summary(normalized_data, chunks, meeting_metadata["title"])
    if summary_text:
        chunks.append(build_summary_chunk(summary_text, meeting_metadata, len(chunks) + 1))
        log.info(f"[4/6] Summary chunk added  ({_ms(t)})")
    else:
        log.warning("[4/6] No summary available — meeting stored without summary chunk")

    # Step 5 — Stamp + store
    t = time.time()
    if not _stamp_project_and_roles(chunks, normalized_data["meeting_id"]):
        log.error("Project stamping failed. Pipeline aborted.")
        return None

    documents = chunks_to_documents(chunks)
    log.info(f"[5/6] langchain documents is created → {len(documents)}")

    if not documents:
        log.error("No valid documents generated from chunks. Pipeline aborted.")
        return None

    stored = store_documents(documents)
    log.info(f"[6/6] ChromaDB    → {stored} documents stored  ({_ms(t)})")

    reset_vectorstore()
    log.info(f"Pipeline complete ✓  total={_ms(pipeline_start)}")
    return chunks


def _ms(start: float) -> str:
    return f"{(time.time() - start) * 1000:.0f}ms"
