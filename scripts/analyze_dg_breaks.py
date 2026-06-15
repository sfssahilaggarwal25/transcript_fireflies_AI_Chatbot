"""
analyze_dg_breaks.py — Show how many real speaker-change exchanges TF-IDF is missing.
Usage: python scripts/analyze_dg_breaks.py --meeting "Nolocode x Akili"
"""
import sys, os, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv; load_dotenv()

from app.core.storage.db import get_raw_collection
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def run(meeting_id, project_id):
    col = get_raw_collection()
    res = col.get(
        where={"$and": [
            {"project_id": {"$eq": project_id}},
            {"meeting_id": {"$eq": meeting_id}},
            {"chunk_type": {"$eq": "atomic"}},
        ]},
        include=["documents", "metadatas"],
    )

    pairs    = sorted(zip(res["documents"], res["metadatas"]),
                      key=lambda x: x[1].get("start_time", 0) or 0)
    # Use raw_text (actual transcript), NOT page_content (HQ question).
    # TF-IDF in create_dialogue_groups runs on chunk["text"] = raw transcript.
    texts    = [p[1].get("raw_text") or p[0] for p in pairs]
    speakers = [p[1].get("speaker_name", "?") for p in pairs]
    n        = len(texts)

    if n < 2:
        print("Not enough chunks."); return

    vec  = TfidfVectorizer(stop_words="english")
    mat  = vec.fit_transform(texts)
    sims = [float(cosine_similarity(mat[i:i+1], mat[i+1:i+2])[0][0])
            for i in range(n - 1)]

    # All speaker-change boundaries
    sc = [(i, speakers[i], speakers[i+1], round(sims[i], 3))
          for i in range(len(sims)) if speakers[i] != speakers[i+1]]

    merged = [(i, sf, st, s) for i, sf, st, s in sc if s >= 0.10]
    broken = [(i, sf, st, s) for i, sf, st, s in sc if s < 0.10]

    print(f"\n{'='*65}")
    print(f"  Meeting ID : {meeting_id}")
    print(f"  Atomic chunks total    : {n}")
    print(f"  Speaker-change boundaries: {len(sc)}")
    print(f"  Captured as DG (sim >= 0.10): {len(merged)}")
    print(f"  MISSED exchanges (sim <  0.10): {len(broken)}")
    print(f"  Miss rate: {100*len(broken)//max(len(sc),1)}%")
    print(f"{'='*65}")

    print(f"\n--- CAPTURED exchanges (sim >= 0.10) ---")
    for i, sf, st, s in merged:
        a = texts[i].replace("\n", " ")[:80]
        b = texts[i+1].replace("\n", " ")[:80]
        print(f"  sim={s}  [{sf[:16]}] -> [{st[:16]}]")
        print(f"    A: {a}")
        print(f"    B: {b}")
        print()

    print(f"\n--- MISSED exchanges (sim < 0.10) ---")
    for i, sf, st, s in broken:
        a = texts[i].replace("\n", " ")[:80]
        b = texts[i+1].replace("\n", " ")[:80]
        next_tokens = len(texts[i+1].split())
        print(f"  sim={s}  [{sf[:16]}] -> [{st[:16]}]  next_tokens={next_tokens}")
        print(f"    A: {a}")
        print(f"    B: {b}")
        print()


def list_meetings(project_id):
    col = get_raw_collection()
    res = col.get(where={"project_id": {"$eq": project_id}}, include=["metadatas"])
    seen = {}
    for m in res["metadatas"]:
        mid = m.get("meeting_id")
        if mid and not m.get("is_meeting_summary") and mid not in seen:
            seen[mid] = m.get("meeting_title", "?")
    return seen


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--meeting", default=None)
    parser.add_argument("--id",      default=None)
    parser.add_argument("--project", default="proj_nolocode_001")
    args = parser.parse_args()

    if args.id:
        run(args.id, args.project)
    else:
        meetings = list_meetings(args.project)
        if args.meeting:
            match = {mid: t for mid, t in meetings.items()
                     if args.meeting.lower() in t.lower()}
            if not match:
                print("No match. Available:"); [print(f"  {t}") for t in meetings.values()]
            else:
                run(next(iter(match)), args.project)
        else:
            print("Available meetings:"); [print(f"  {t}  ({mid})") for mid, t in meetings.items()]
