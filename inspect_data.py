import sys
sys.path.insert(0, '.')

from app.services.storage.project_store import get_meeting_ids_for_project
from app.services.storage.db import get_raw_collection

PROJECT = 'proj_nolocode_001'

meeting_ids = get_meeting_ids_for_project(PROJECT)
print(f'Meeting IDs found: {len(meeting_ids)}')
print()

col = get_raw_collection()

for mid in meeting_ids:
    r = col.get(
        where={"$and": [{"project_id": {"$eq": PROJECT}}, {"meeting_id": {"$eq": mid}}]},
        include=["metadatas", "documents"],
    )
    metas = r.get("metadatas", [])
    docs  = r.get("documents", [])
    if not metas:
        continue

    title    = metas[0].get("meeting_title", "?")
    date     = metas[0].get("meeting_date", "?")
    speakers = set()
    dec = com = que = summary_text = ""
    dec_count = com_count = que_count = 0

    for i, m in enumerate(metas):
        if m.get("is_meeting_summary"):
            summary_text = docs[i][:400] if docs else ""
            continue
        spk = m.get("speaker_name", "")
        if spk:
            speakers.add(spk)
        if m.get("contains_decision"):    dec_count += 1
        if m.get("contains_commitment"):  com_count += 1
        if m.get("contains_question"):    que_count += 1

    transcript_chunks = sum(1 for m in metas if not m.get("is_meeting_summary"))

    print(f"{'='*60}")
    print(f"Meeting : {title}")
    print(f"Date    : {date}")
    print(f"Chunks  : {transcript_chunks} transcript")
    print(f"Signals : decisions={dec_count} | commitments={com_count} | questions={que_count}")
    print("Speakers: " + str(sorted(speakers)).encode('ascii', 'replace').decode())
    if summary_text:
        safe = summary_text.encode('ascii', 'replace').decode()
        print("Summary : " + safe + "...")
    print()
