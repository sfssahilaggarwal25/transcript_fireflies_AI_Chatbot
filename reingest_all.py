"""
reingest_all.py — Re-ingest all meetings with the updated chunking strategy.

WHY THIS EXISTS
--------------
After changing create_chunks() in app/core/transcript/chunking.py, all existing
ChromaDB chunks were produced by the OLD strategy. This script re-processes
every meeting so the new chunking applies.

TWO PATHS (cache first, API fallback)
--------------------------------------
  1. Local cache exists (data/transcripts/MEETING_ID.json)
       → Load from file — zero Fireflies API calls, takes ~3 min total
  2. No local cache
       → Fetch from Fireflies API — subject to daily rate limit

Run fetch_and_cache.py ONCE to build the local cache, then reingest_all.py
never needs the Fireflies API again.

USAGE
-----
    python reingest_all.py              # re-ingest all 19 meetings
    python reingest_all.py --dry-run    # show what would happen, no changes
    python reingest_all.py --ids 01KM2DD6MXGSZ4F1QW0BNJE16N  # specific meeting(s)
"""

import argparse
import json
import os
import sys
import time
sys.path.insert(0, ".")

from dotenv import load_dotenv
load_dotenv(dotenv_path=".env")

from app.core.storage.db import get_raw_collection, reset_vectorstore
from app.services.ingest_service import ingest_from_url, ingest_from_data

PROJECT_ID = "proj_nolocode_001"
CACHE_DIR  = "data/transcripts"

ALL_MEETING_IDS = [
    "01KM2DD6MXGSZ4F1QW0BNJE16N",
    "01KMHQSBYB1RAGY2X4EP6DCMC9",
    "01KPZQM8QJV019CTG2YBHBNKJB",
    "01KR18Q6AJM5GZX7Q66VHZXZP3",
    "01KQVP85XVSYDGBXDMCPD4BB6A",
    "01KPSSB8Z5D7C70WJ11YFFFY2Z",
    "01KPN0G7JN7B3SR8HXR0PVFPSZ",
    "01KP8S4ZFHR6CGHJVK62931CC6",
    "01KP5V2WV2YFKWZSA1E4Y3SE18",
    "01KP5NPHRKEK81SCWMBH64172Q",
    "01KJQ6XEQ535KTFNCQ5JSNYSYP",
    "01KM2NAB4W0G0H9YET0EEFZVDT",
    "01KMD9V4A64EXRA4WJVKBDV0W7",
    "01KN4EQFKRPWCSNAVS5BV7QK9F",
    "01KN6TSNFE4MHP1FCCGJH9WX8R",
    "01KNHBEVGV5YK17CDHER3D2NXB",
    "01KNNPB1705JMXDKCMCXC5ESP4",
    "01KNS2DKRQFB33BZZCJZYTKD5K",
    "01KNVN05TF8TS9BVAMMHMV276T",
]


def cache_path(meeting_id: str) -> str:
    return os.path.join(CACHE_DIR, f"{meeting_id}.json")


def load_from_cache(meeting_id: str) -> dict | None:
    path = cache_path(meeting_id)
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        sentences = data.get("data", {}).get("transcript", {}).get("sentences", [])
        if not sentences:
            return None
        return data
    except Exception:
        return None


def get_chunk_count(meeting_id: str) -> int:
    col = get_raw_collection()
    result = col.get(where={"meeting_id": {"$eq": meeting_id}}, include=[])
    return len(result["ids"])


def delete_meeting_chunks(meeting_id: str) -> int:
    col = get_raw_collection()
    result = col.get(where={"meeting_id": {"$eq": meeting_id}}, include=[])
    count = len(result["ids"])
    if count > 0:
        col.delete(where={"meeting_id": {"$eq": meeting_id}})
    return count


def print_before_stats(meeting_ids: list[str]) -> dict:
    print("\n── BEFORE ──────────────────────────────────────────────")
    col = get_raw_collection()
    all_docs = col.get(include=["documents"])["documents"]
    total = len(all_docs)
    if total:
        u80  = sum(1 for d in all_docs if len(d) < 80)
        u200 = sum(1 for d in all_docs if len(d) < 200)
        o200 = sum(1 for d in all_docs if len(d) >= 200)
        print(f"  Total chunks  : {total}")
        print(f"  Under 80 chars: {u80} ({u80/total*100:.1f}%)  ← noise")
        print(f"  Under 200     : {u200} ({u200/total*100:.1f}%)")
        print(f"  Over 200      : {o200} ({o200/total*100:.1f}%)  ← good size")
    else:
        print("  No chunks in DB yet.")
    print()

    # Cache status per meeting
    cached    = [m for m in meeting_ids if load_from_cache(m) is not None]
    not_cached = [m for m in meeting_ids if load_from_cache(m) is None]
    print(f"  Local cache: {len(cached)}/{len(meeting_ids)} meetings ready")
    if not_cached:
        print(f"  No cache (will hit API): {not_cached}")
    print()

    return {m: get_chunk_count(m) for m in meeting_ids}


def print_after_stats(before_counts: dict) -> None:
    print("\n── AFTER ───────────────────────────────────────────────")
    col = get_raw_collection()
    all_docs = col.get(include=["documents"])["documents"]
    total = len(all_docs)
    if not total:
        print("  No chunks found — something went wrong.")
        return

    u80  = sum(1 for d in all_docs if len(d) < 80)
    u200 = sum(1 for d in all_docs if len(d) < 200)
    o200 = sum(1 for d in all_docs if len(d) >= 200)

    print(f"  Total chunks  : {total}")
    print(f"  Under 80 chars: {u80} ({u80/total*100:.1f}%)")
    print(f"  Under 200     : {u200} ({u200/total*100:.1f}%)")
    print(f"  Over 200      : {o200} ({o200/total*100:.1f}%)  ← good size")
    print()

    print(f"  {'Meeting ID':<45} {'Before':>7} {'After':>7} {'Change':>8}")
    print(f"  {'-'*72}")
    for mid, before in before_counts.items():
        after = get_chunk_count(mid)
        diff = after - before
        symbol = "▲" if diff > 0 else ("▼" if diff < 0 else "=")
        print(f"  {mid:<45} {before:>7} {after:>7} {symbol}{abs(diff):>7}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--ids", nargs="+", metavar="MEETING_ID")
    args = parser.parse_args()

    meeting_ids = args.ids if args.ids else ALL_MEETING_IDS
    invalid = [m for m in meeting_ids if m not in ALL_MEETING_IDS]
    if invalid:
        print(f"ERROR: Unknown meeting IDs: {invalid}")
        sys.exit(1)

    print(f"Re-ingesting {len(meeting_ids)} meeting(s) | project: {PROJECT_ID}")
    if args.dry_run:
        print("DRY RUN — no changes\n")

    before_counts = print_before_stats(meeting_ids)

    if args.dry_run:
        print("Dry run complete. Run without --dry-run to apply.")
        return

    print("── RE-INGESTING ────────────────────────────────────────")
    t_total = time.time()
    results = {"success": 0, "failed": 0}

    for i, meeting_id in enumerate(meeting_ids, 1):
        print(f"\n[{i:02d}/{len(meeting_ids)}] {meeting_id}")

        cached_data = load_from_cache(meeting_id)
        source = "cache" if cached_data else "API"
        before = before_counts[meeting_id]

        deleted = delete_meeting_chunks(meeting_id)
        print(f"  Deleted {deleted} old chunks  |  source: {source}")

        t = time.time()
        try:
            if cached_data:
                result = ingest_from_data(cached_data, PROJECT_ID, meeting_number=i)
            else:
                url = f"https://app.fireflies.ai/view/meeting::{meeting_id}"
                result = ingest_from_url(url, PROJECT_ID)

            elapsed = int((time.time() - t) * 1000)
            title = result.get("meeting_title", "?")[:45]
            new_count = result.get("chunks_stored", 0)
            print(f"  ✅ {title}")
            print(f"     chunks: {before} → {new_count}  |  {elapsed}ms  ({source})")
            results["success"] += 1

        except Exception as e:
            elapsed = int((time.time() - t) * 1000)
            print(f"  ❌ FAILED ({elapsed}ms): {e}")
            if "Too many requests" in str(e):
                print(f"     Rate limit hit. Run fetch_and_cache.py after midnight UTC,")
                print(f"     then re-run: python reingest_all.py --ids {meeting_id}")
            results["failed"] += 1

        if source == "API" and i < len(meeting_ids):
            time.sleep(2)

    elapsed_total = int(time.time() - t_total)
    print(f"\n── SUMMARY ─────────────────────────────────────────────")
    print(f"  ✅ Success : {results['success']}")
    print(f"  ❌ Failed  : {results['failed']}")
    print(f"  Total time : {elapsed_total}s")

    print_after_stats(before_counts)
    reset_vectorstore()
    print("\nVectorstore cache reset. System ready.")
    if results["success"] > 0:
        print("\nNext: run DeepEval to measure accuracy:")
        print("  python -m app.agent.tests.deepeval_tests.run_deepeval")


if __name__ == "__main__":
    main()