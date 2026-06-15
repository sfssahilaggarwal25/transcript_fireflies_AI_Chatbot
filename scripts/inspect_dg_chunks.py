"""
inspect_dg_chunks.py — Show ALL dialogue_group chunks for one meeting, full text.

Usage:
  python scripts/inspect_dg_chunks.py                        # picks the first meeting found
  python scripts/inspect_dg_chunks.py --meeting "Nolocode AI meeting"
  python scripts/inspect_dg_chunks.py --id 01KMHQSBYB1RAGY2X4EP6DCMC9

Shows per chunk:
  - speakers (pipe field)
  - start_time
  - HQ (page_content — what was embedded)
  - RAW text (what the LLM actually reads)
  - topic_keywords if stored
"""

import sys, os, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app.core.storage.db import get_raw_collection


def list_meetings(project_id):
    col = get_raw_collection()
    res = col.get(where={"project_id": {"$eq": project_id}}, include=["metadatas"])
    seen = {}
    for m in res["metadatas"]:
        mid = m.get("meeting_id")
        if mid and not m.get("is_meeting_summary") and mid not in seen:
            seen[mid] = m.get("meeting_title", "?")
    return seen  # {id: title}


def inspect(project_id, meeting_id, meeting_title_filter):
    col = get_raw_collection()

    # ── Resolve meeting ───────────────────────────────────────────────────────
    if not meeting_id:
        meetings = list_meetings(project_id)
        if not meetings:
            print("No meetings found.")
            return
        if meeting_title_filter:
            match = {mid: t for mid, t in meetings.items()
                     if meeting_title_filter.lower() in t.lower()}
            if not match:
                print(f"No meeting matching '{meeting_title_filter}'. Available:")
                for mid, t in sorted(meetings.items(), key=lambda x: x[1]):
                    print(f"  {t!r}  ({mid})")
                return
            meeting_id = next(iter(match))
        else:
            # Pick the first alphabetically for a stable default
            meeting_id = sorted(meetings)[0]

    # ── Fetch all chunks for this meeting ─────────────────────────────────────
    res = col.get(
        where={"$and": [
            {"project_id":  {"$eq": project_id}},
            {"meeting_id":  {"$eq": meeting_id}},
        ]},
        include=["documents", "metadatas"],
    )
    metas = res["metadatas"]
    docs  = res["documents"]

    meeting_title = next((m.get("meeting_title", "?") for m in metas), "?")
    meeting_date  = next((str(m.get("meeting_date", ""))[:10] for m in metas), "?")

    # ── Split by chunk type ───────────────────────────────────────────────────
    atomic_chunks = []
    dg_chunks     = []
    summary_chunks = []

    for doc, meta in zip(docs, metas):
        if meta.get("is_meeting_summary"):
            summary_chunks.append((doc, meta))
        elif meta.get("chunk_type") == "dialogue_group":
            dg_chunks.append((doc, meta))
        else:
            atomic_chunks.append((doc, meta))

    # Sort by start_time
    dg_chunks.sort(key=lambda x: x[1].get("start_time", 0) or 0)
    atomic_chunks.sort(key=lambda x: x[1].get("start_time", 0) or 0)

    print(f"\n{'='*70}")
    print(f"  MEETING  : {meeting_title}")
    print(f"  DATE     : {meeting_date}")
    print(f"  ID       : {meeting_id}")
    print(f"  CHUNKS   : {len(atomic_chunks)} atomic  |  {len(dg_chunks)} dialogue_group  |  {len(summary_chunks)} summary")
    print(f"{'='*70}\n")

    if not dg_chunks:
        print("  No dialogue_group chunks found for this meeting.")
        print("  This could mean: meeting was not re-ingested with new strategy,")
        print("  or the meeting transcript had no multi-speaker exchanges above threshold.")
        return

    print(f"{'─'*70}")
    print(f"  DIALOGUE_GROUP CHUNKS ({len(dg_chunks)})")
    print(f"{'─'*70}\n")

    for i, (doc, m) in enumerate(dg_chunks, 1):
        ts      = m.get("start_time", 0) or 0
        mm, ss  = int(ts // 60), int(ts % 60)
        speakers  = m.get("speakers", "").replace("|", "  +  ")
        n_spk     = len([s for s in m.get("speakers","").split("|") if s.strip()])
        tokens    = m.get("group_token_count", "?")
        keywords  = m.get("topic_keywords", "")
        chunk_id  = m.get("chunk_id", "?")
        hq        = (doc or "").replace("\n", " ").strip()
        raw       = (m.get("raw_text") or "").strip()
        n_turns   = raw.count("\n") + 1 if raw else 0

        print(f"  [{i:02d}] @ {mm:02d}:{ss:02d}  |  speakers={n_spk}  turns={n_turns}  tokens={tokens}  |  id={chunk_id}")
        print(f"        SPEAKERS : {speakers}")
        if keywords:
            print(f"        KEYWORDS : {keywords}")
        print(f"        HQ       : {hq[:150]}")
        print(f"        RAW TEXT :")
        # Print raw text with indentation, full — no truncation
        for line in raw.splitlines():
            print(f"          {line}")
        print()

    # ── Sanity checks ─────────────────────────────────────────────────────────
    print(f"{'─'*70}")
    print(f"  SANITY CHECKS")
    print(f"{'─'*70}")

    # Check 1: speakers field always populated
    no_speakers = [i+1 for i, (_, m) in enumerate(dg_chunks) if not m.get("speakers")]
    print(f"  speakers field empty   : {no_speakers if no_speakers else 'none (good)'}")

    # Check 2: raw_text always populated
    no_raw = [i+1 for i, (_, m) in enumerate(dg_chunks) if not m.get("raw_text")]
    print(f"  raw_text missing       : {no_raw if no_raw else 'none (good)'}")

    # Check 3: HQ generated (page_content not blank)
    no_hq = [i+1 for i, (doc, _) in enumerate(dg_chunks) if not doc or not doc.strip()]
    print(f"  HQ (page_content) blank: {no_hq if no_hq else 'none (good)'}")

    # Check 4: single-speaker DG chunks (must not exist — DG = multi-speaker)
    single_spk = [i+1 for i, (_, m) in enumerate(dg_chunks)
                  if len([s for s in (m.get("speakers") or "").split("|") if s.strip()]) < 2]
    print(f"  single-speaker DG      : {single_spk if single_spk else 'none (good)'}")

    # Check 5: very short raw_text (under 80 chars — likely noise)
    short = [(i+1, len(m.get("raw_text","") or "")) for i, (_, m) in enumerate(dg_chunks)
             if len(m.get("raw_text","") or "") < 80]
    print(f"  raw_text < 80 chars    : {short if short else 'none (good)'}")

    # Coverage: what % of atomic chunks have a DG that overlaps?
    print(f"\n  atomic chunks          : {len(atomic_chunks)}")
    print(f"  dialogue_group chunks  : {len(dg_chunks)}")
    print(f"  DG/atomic ratio        : {len(dg_chunks)/max(len(atomic_chunks),1):.2f}  (expect 0.3-0.8 for conversational meetings)")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--meeting", default=None, help="Partial meeting title to match")
    parser.add_argument("--id",      default=None, help="Exact meeting_id")
    parser.add_argument("--project", default="proj_nolocode_001")
    args = parser.parse_args()
    inspect(args.project, args.id, args.meeting)
