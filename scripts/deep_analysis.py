"""
deep_analysis.py — Full meeting walkthrough: atomic sequence, DG grouping, HQ quality.

Shows every atomic chunk in order, marks where DG groups form and where topic
breaks happen, and for each DG prints the full dialogue + its HQ question.

Usage:
  python scripts/deep_analysis.py --meeting "Akili x Sfs Standup"
  python scripts/deep_analysis.py --id 01KTH2FHQHN0ACXXD4C7Z76R28
"""

import sys, os, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv; load_dotenv()

from app.core.storage.db import get_raw_collection
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

PROJECT_ID = "proj_nolocode_001"
TFIDF_THRESHOLD = 0.10
SHORT_RESPONSE  = 30   # tokens — bypass threshold when speaker changes + short


def resolve(name, mid):
    col = get_raw_collection()
    res = col.get(where={"project_id": {"$eq": PROJECT_ID}}, include=["metadatas"])
    seen = {}
    for m in res["metadatas"]:
        i = m.get("meeting_id")
        if i and not m.get("is_meeting_summary") and i not in seen:
            seen[i] = m.get("meeting_title", "?")
    if mid:
        return mid, seen.get(mid, mid)
    matches = [(i, t) for i, t in seen.items() if name.lower() in t.lower()]
    if not matches:
        print(f"No match for '{name}'. Available:"); [print(f"  {t}") for t in seen.values()]; sys.exit(1)
    if len(matches) > 1:
        print(f"Multiple matches:"); [print(f"  {t} ({i})") for i,t in matches]
        print("Use --id"); sys.exit(1)
    return matches[0]


def run(meeting_id, title):
    col = get_raw_collection()

    # ── Fetch atomic chunks ───────────────────────────────────────────────────
    res_a = col.get(
        where={"$and": [
            {"project_id": {"$eq": PROJECT_ID}},
            {"meeting_id": {"$eq": meeting_id}},
            {"chunk_type": {"$eq": "atomic"}},
        ]},
        include=["documents", "metadatas"],
    )
    atomic_pairs = sorted(
        zip(res_a["documents"], res_a["metadatas"]),
        key=lambda x: x[1].get("start_time", 0) or 0,
    )
    atomic_docs  = [p[0] for p in atomic_pairs]   # HQ questions (page_content)
    atomic_metas = [p[1] for p in atomic_pairs]
    raw_texts    = [m.get("raw_text", "") for m in atomic_metas]
    n = len(atomic_metas)

    # ── Fetch DG chunks ───────────────────────────────────────────────────────
    res_d = col.get(
        where={"$and": [
            {"project_id": {"$eq": PROJECT_ID}},
            {"meeting_id": {"$eq": meeting_id}},
            {"chunk_type": {"$eq": "dialogue_group"}},
        ]},
        include=["documents", "metadatas"],
    )
    dg_by_id = {}   # chunk_id → (hq, meta)
    for doc, m in zip(res_d["documents"], res_d["metadatas"]):
        for tid in (m.get("turn_ids") or "").split("|"):
            tid = tid.strip()
            if tid:
                dg_by_id.setdefault(tid, []).append((doc, m))

    # ── TF-IDF similarities on raw text (same as create_dialogue_groups) ──────
    sims = []
    if n >= 2:
        try:
            vec = TfidfVectorizer(stop_words="english")
            mat = vec.fit_transform(raw_texts)
            sims = [
                float(cosine_similarity(mat[i:i+1], mat[i+1:i+2])[0][0])
                for i in range(n - 1)
            ]
        except Exception:
            sims = [0.0] * (n - 1)

    # ── Print header ──────────────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"  MEETING  : {title}")
    print(f"  ID       : {meeting_id}")
    print(f"  Atomic   : {n}   |   DG groups : {len(res_d['metadatas'])}")
    print(f"  TF-IDF threshold: {TFIDF_THRESHOLD}  |  short-response bypass: <{SHORT_RESPONSE} tokens")
    print(f"{'='*70}\n")

    # ── Walk through every atomic chunk ───────────────────────────────────────
    printed_dg_ids = set()

    for i, (hq, meta, raw) in enumerate(zip(atomic_docs, atomic_metas, raw_texts)):
        ts      = meta.get("start_time", 0) or 0
        mm, ss  = int(ts // 60), int(ts % 60)
        spk     = meta.get("speaker_name", "?")
        cid     = meta.get("chunk_id", "")
        tokens  = len(raw.split())
        raw_preview = raw.replace("\n", " ").strip()

        # ── Transition label before this chunk ───────────────────────────────
        if i > 0:
            sim = sims[i - 1]
            prev_spk = atomic_metas[i - 1].get("speaker_name", "")
            spk_changed = prev_spk != spk
            short_bypass = spk_changed and tokens < SHORT_RESPONSE

            if sim < TFIDF_THRESHOLD and not short_bypass:
                label = f"--- TOPIC BREAK (sim={sim:.3f}) ---"
            elif sim < TFIDF_THRESHOLD and short_bypass:
                label = f"... short-response bypass (sim={sim:.3f}, {tokens}tok) ..."
            else:
                label = f"    ~ continues (sim={sim:.3f}) ~"

            print(f"  {label}")

        # ── Atomic chunk ──────────────────────────────────────────────────────
        in_dg   = cid in dg_by_id
        dg_mark = "[DG]" if in_dg else "    "
        print(f"  {dg_mark} [{i+1:03d}] @{mm:02d}:{ss:02d}  {spk[:22]}  ({tokens} tok)")
        print(f"         HQ : {hq.replace(chr(10),' ')[:100]}")
        print(f"        RAW : {raw_preview[:160]}")

        # ── Print the DG group this chunk belongs to (first time only) ───────
        if in_dg:
            for dg_hq, dg_meta in dg_by_id[cid]:
                dg_id = dg_meta.get("chunk_id", "")
                if dg_id in printed_dg_ids:
                    continue
                printed_dg_ids.add(dg_id)

                dg_spk    = dg_meta.get("speakers", "").replace("|", " + ")
                n_turns   = len([t for t in (dg_meta.get("turn_ids") or "").split("|") if t.strip()])
                dg_raw    = (dg_meta.get("raw_text") or "").strip()
                dg_tokens = dg_meta.get("group_token_count", "?")

                print()
                print(f"  ╔══ DG GROUP  {dg_id.split('_dg_')[-1] if '_dg_' in dg_id else dg_id}")
                print(f"  ║  speakers : {dg_spk}")
                print(f"  ║  turns    : {n_turns}   tokens: {dg_tokens}")
                print(f"  ║")
                print(f"  ║  HQ (what retrieval searches on):")
                print(f"  ║    >> {dg_hq.replace(chr(10),' ')[:140]}")
                print(f"  ║")
                print(f"  ║  FULL DIALOGUE (what LLM reads):")
                for line in dg_raw.splitlines():
                    print(f"  ║    {line}")
                print(f"  ╚{'═'*60}")
                print()

    # ── Final summary ─────────────────────────────────────────────────────────
    covered = {cid for cid in [m.get("chunk_id") for m in atomic_metas] if cid in dg_by_id}
    topic_breaks       = sum(1 for i, s in enumerate(sims)
                             if s < TFIDF_THRESHOLD
                             and not (atomic_metas[i].get("speaker_name") != atomic_metas[i+1].get("speaker_name")
                                      and len(raw_texts[i+1].split()) < SHORT_RESPONSE))
    short_bypasses     = sum(1 for i, s in enumerate(sims)
                             if s < TFIDF_THRESHOLD
                             and atomic_metas[i].get("speaker_name") != atomic_metas[i+1].get("speaker_name")
                             and len(raw_texts[i+1].split()) < SHORT_RESPONSE)

    print(f"\n{'='*70}")
    print(f"  SUMMARY")
    print(f"{'─'*70}")
    print(f"  Atomic chunks          : {n}")
    print(f"  DG groups formed       : {len(res_d['metadatas'])}")
    print(f"  Atomic inside a DG     : {len(covered)}  ({100*len(covered)//max(n,1)}%)")
    print(f"  Topic breaks (TF-IDF)  : {topic_breaks}")
    print(f"  Short-response bypasses: {short_bypasses}  (exchanges merged despite low sim)")
    print(f"  Single-speaker DGs     : ", end="")
    bad = [m for m in res_d["metadatas"]
           if len([s for s in (m.get("speakers","")).split("|") if s.strip()]) < 2]
    print(f"{len(bad)}  {'(GOOD — none)' if not bad else 'BUG'}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--meeting", default=None)
    parser.add_argument("--id",      default=None)
    args = parser.parse_args()
    if not args.meeting and not args.id:
        print("Provide --meeting or --id"); sys.exit(1)
    mid, title = resolve(args.meeting, args.id)
    run(mid, title)
