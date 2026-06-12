"""
fetch_and_cache.py — Download all Fireflies transcripts and save locally.

WHY THIS EXISTS
--------------
The Fireflies API has a daily rate limit. Re-ingesting 19 meetings one-by-one
hits that limit. This script fetches ALL meetings in a single bulk API call
and saves each to data/transcripts/MEETING_ID.json.

After running this once, reingest_all.py reads from local files — zero API
calls needed for future re-ingestions.

USAGE
-----
    python fetch_and_cache.py           # fetch all, skip already-cached
    python fetch_and_cache.py --force   # re-download even if already cached

OUTPUT
------
    data/transcripts/01KM2DD6MXGSZ4F1QW0BNJE16N.json
    data/transcripts/01KMHQSBYB1RAGY2X4EP6DCMC9.json
    ...
"""

import argparse
import json
import os
import sys
sys.path.insert(0, ".")

from dotenv import load_dotenv
load_dotenv(dotenv_path=".env")

from app.clients.fireflies_client import fetch_all_transcripts, FirefliesAPIError

CACHE_DIR = "data/transcripts"

# Only cache these 19 meetings (our project's meetings)
TARGET_IDS = {
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
}


def cache_path(meeting_id: str) -> str:
    return os.path.join(CACHE_DIR, f"{meeting_id}.json")


def is_cached(meeting_id: str) -> bool:
    path = cache_path(meeting_id)
    if not os.path.exists(path):
        return False
    # Verify file has actual sentences (not an empty/broken file)
    try:
        with open(path) as f:
            data = json.load(f)
        sentences = data.get("data", {}).get("transcript", {}).get("sentences", [])
        return len(sentences) > 0
    except Exception:
        return False


def save_transcript(transcript: dict) -> str:
    """Wrap raw transcript in the same shape fetch_transcript() returns."""
    meeting_id = transcript["id"]
    wrapped = {"data": {"transcript": transcript}}
    path = cache_path(meeting_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(wrapped, f, ensure_ascii=False, indent=2)
    return path


def main():
    parser = argparse.ArgumentParser(description="Fetch and cache all Fireflies transcripts locally")
    parser.add_argument("--force", action="store_true", help="Re-download even if already cached")
    args = parser.parse_args()

    os.makedirs(CACHE_DIR, exist_ok=True)

    # Check what's already cached
    already_cached = {mid for mid in TARGET_IDS if is_cached(mid)} if not args.force else set()
    to_fetch = TARGET_IDS - already_cached

    print(f"Target meetings : {len(TARGET_IDS)}")
    print(f"Already cached  : {len(already_cached)}")
    print(f"Need to fetch   : {len(to_fetch)}")

    if not to_fetch:
        print("\n✅ All meetings already cached. Nothing to do.")
        print(f"   Cache location: {os.path.abspath(CACHE_DIR)}/")
        return

    print(f"\nFetching all transcripts in one bulk API call...")

    try:
        all_transcripts = fetch_all_transcripts(limit=100)
    except FirefliesAPIError as e:
        print(f"\n❌ Fireflies API error: {e}")
        if "Too many requests" in str(e):
            print("   Rate limit active. Try again after midnight UTC.")
        sys.exit(1)

    print(f"API returned {len(all_transcripts)} transcripts total\n")

    saved    = []
    skipped  = []
    not_found = list(to_fetch)  # will remove as we find them

    for transcript in all_transcripts:
        mid = transcript.get("id", "")
        title = transcript.get("title", "?")[:50]
        sentences = len(transcript.get("sentences") or [])

        if mid not in TARGET_IDS:
            continue  # not our project's meeting

        not_found = [m for m in not_found if m != mid]

        if mid in already_cached and not args.force:
            skipped.append(mid)
            print(f"  ⏭  {mid}  (already cached)")
            continue

        path = save_transcript(transcript)
        saved.append(mid)
        print(f"  💾 {mid}  {sentences:4d} sentences  {title}")

    print(f"\n── SUMMARY ─────────────────────────────────────────────")
    print(f"  💾 Saved    : {len(saved)}")
    print(f"  ⏭  Skipped  : {len(skipped)} (already cached)")

    if not_found:
        print(f"  ⚠️  Not found in API response: {len(not_found)}")
        for mid in not_found:
            print(f"      {mid}")
        print("  These meetings may have been deleted from your Fireflies account.")

    print(f"\n  Cache location: {os.path.abspath(CACHE_DIR)}/")

    if saved:
        print(f"\nNext step: re-ingest using local cache (no API calls):")
        print(f"  python reingest_all.py")


if __name__ == "__main__":
    main()