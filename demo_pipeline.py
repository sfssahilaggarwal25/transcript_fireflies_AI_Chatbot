"""
Pipeline demo — shows exactly what happens at each step and why.
Run: python demo_pipeline.py
"""
import json
from app.config import CONSTANT_TRANSCRIPT
from app.services.transcript.normalize import normalize_transcript
from app.services.transcript.metadata import build_meeting_metadata
from app.services.transcript.chunking import create_chunks
from app.services.storage.project_store import get_project_for_meeting, get_speaker_role

DIVIDER = "\n" + "=" * 65

# ── STEP 0: Raw Fireflies data ────────────────────────────────────
print(DIVIDER)
print("STEP 0 — What Fireflies sends us (raw webhook payload)")
print(DIVIDER)

raw = CONSTANT_TRANSCRIPT["data"]["transcript"]

print(f"  meeting id    : {raw['id']}")
print(f"  title         : {raw['title']}")
print(f"  total sentences: {len(raw['sentences'])}")
print(f"  has summary   : {bool(raw.get('summary', {}).get('overview'))}")
print()
print("  WHY: Fireflies gives us flat sentences — no project, no roles,")
print("  no structure for retrieval. Everything below is us adding that.")

# ── STEP 1: Normalize ─────────────────────────────────────────────
print(DIVIDER)
print("STEP 1 — Normalize (flatten + validate)")
print(DIVIDER)

normalized = normalize_transcript(CONSTANT_TRANSCRIPT)
print(f"  meeting_id  : {normalized['meeting_id']}")
print(f"  title       : {normalized['title']}")
print(f"  sentences   : {len(normalized['sentences'])}")
print(f"  has summary : {bool(normalized.get('summary', {}).get('overview'))}")
print()
print("  WHY: The Fireflies API wraps everything in data.transcript.")
print("  Normalize strips that nesting so every downstream function")
print("  works with a flat, validated dict — no KeyErrors in prod.")

# ── STEP 2: Build meeting metadata ───────────────────────────────
print(DIVIDER)
print("STEP 2 — Build meeting metadata")
print(DIVIDER)

meta = build_meeting_metadata(normalized)
print(f"  meeting_id : {meta['meeting_id']}")
print(f"  title      : {meta['title']}")
print(f"  date       : {meta['date']}")
print()
print("  WHY: Chunking needs meeting-level fields (id, title, date)")
print("  available as a clean dict — not re-parsed per sentence.")
print("  NOTE: Uses real meeting date from Fireflies API (falls back to today if missing).")

# ── STEP 3: Chunking ──────────────────────────────────────────────
print(DIVIDER)
print("STEP 3 — Speaker-aware chunking")
print(DIVIDER)

chunks = create_chunks(normalized["sentences"], meta)

# Speaker distribution
from collections import Counter
role_counts = Counter(c["speaker_name"] for c in chunks)

print(f"  Total chunks created : {len(chunks)}")
print(f"  Sentences in          : {len(normalized['sentences'])}")
print(f"  Compression ratio     : {len(normalized['sentences'])/len(chunks):.1f} sentences per chunk")
print()
print("  Chunks per speaker:")
for speaker, count in role_counts.most_common():
    print(f"    {speaker:35} {count} chunks")
print()
print("  WHY utterance-based chunking:")
print("  - One chunk = one speaker block (never mixes speakers)")
print("  - Keeps speaker attribution clean for every chunk")
print("  - MAX_CHARS=250 keeps chunks small enough to embed accurately")
print("  - HARD_MIN=15 filters garbage ('Ok.', 'Sa.', single words)")
print()
print("  Sample chunk BEFORE metadata stamping:")
sample = chunks[0]
preview_fields = ["chunk_id", "meeting_id", "meeting_title", "meeting_date",
                  "speaker_name", "chunk_index", "chunk_type",
                  "is_meeting_summary", "text_length"]
for k in preview_fields:
    print(f"    {k:22}: {sample[k]}")
print(f"    {'text':22}: \"{sample['text'][:60]}...\"")

# ── STEP 4: Stamp project_id ─────────────────────────────────────
print(DIVIDER)
print("STEP 4 — Stamp project_id + company fields (from projects.json)")
print(DIVIDER)

meeting_id = normalized["meeting_id"]
project_info = get_project_for_meeting(meeting_id)

if project_info:
    for chunk in chunks:
        chunk.update(project_info)
    print(f"  project_id   : {project_info['project_id']}")
    print(f"  project_name : {project_info['project_name']}")
    print(f"  company_id   : {project_info['company_id']}")
    print(f"  company_name : {project_info['company_name']}")
else:
    print("  WARNING: meeting not mapped in projects.json")
print()
print("  WHY: project_id is stamped at ingestion, not query time.")
print("  Every ChromaDB query will filter on project_id first —")
print("  this is the isolation guarantee that makes the system safe.")

# ── STEP 5: Stamp speaker_role ────────────────────────────────────
print(DIVIDER)
print("STEP 5 — Stamp speaker_role (from projects.json speakers map)")
print(DIVIDER)

for chunk in chunks:
    chunk["speaker_role"] = get_speaker_role(meeting_id, chunk["speaker_name"])

role_distribution = Counter(c["speaker_role"] for c in chunks)
print("  Role distribution across all chunks:")
for role, count in role_distribution.most_common():
    print(f"    {role:20} {count} chunks")
print()
print("  WHY: speaker_role enables Type 3 (miscommunication detection)")
print("  and Type 5 (speaker-specific) queries. Without it we cannot")
print("  fetch 'what did the CLIENT say vs what did DEVS say'.")

# ── STEP 6: Final chunk — full schema ────────────────────────────
print(DIVIDER)
print("STEP 6 — Final chunk schema (ready for ChromaDB)")
print(DIVIDER)

print("  Full schema of one chunk after all 5 steps:")
print()
final = chunks[0]
groups = {
    "Level 1 — Scope": ["project_id", "project_name", "company_id", "company_name"],
    "Level 2 — Meeting": ["meeting_id", "meeting_title", "meeting_date", "meeting_number", "meeting_type"],
    "Level 3 — Speaker": ["speaker_name", "speaker_id", "speaker_role"],
    "Level 4 — Position": ["chunk_index", "chunk_type", "is_meeting_summary"],
    "Level 5 — Signals (placeholder)": ["contains_decision", "contains_commitment", "contains_question", "sentiment"],
    "Content": ["chunk_id", "text_length"],
}
for group, keys in groups.items():
    print(f"  [{group}]")
    for k in keys:
        print(f"    {k:26}: {final.get(k)}")
    print()

# ── STEP 7: What's next ───────────────────────────────────────────
print(DIVIDER)
print("WHAT'S NEXT — ChromaDB storage (Phase 1 remaining)")
print(DIVIDER)
print()
print("  These chunks are ready to store. Missing pieces:")
print("  1. ChromaDB installed + collection created  (db.py)")
print("  2. store_chunks() — embed text + write to ChromaDB  (chunk_store.py)")
print("  3. Replace TODO in webhook_handler.py with store_chunks(chunks)")
print("  4. Content signal classifier — set contains_decision/commitment")
print("  5. Meeting summary chunk — one per meeting, is_meeting_summary=True")
print()
print(f"  {len(chunks)} chunks from this meeting — all ready, waiting for the DB.")
print(DIVIDER)
