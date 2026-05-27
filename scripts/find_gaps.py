import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from app.config import CONSTANT_TRANSCRIPT

transcripts = CONSTANT_TRANSCRIPT["data"]["transcript"]

for t_idx, transcript in enumerate(transcripts):
    title = transcript["title"]
    print(f"=== Transcript {t_idx+1}: {title} ===")
    sentences = transcript.get("sentences", [])
    print(f"Total sentences: {len(sentences)}")

    gaps = []
    for i in range(1, len(sentences)):
        prev_end = sentences[i-1].get("end_time")
        curr_start = sentences[i].get("start_time")
        if prev_end is not None and curr_start is not None:
            gap = round(curr_start - prev_end, 2)
            if gap >= 3.0:
                gaps.append({
                    "gap": gap,
                    "prev_speaker": sentences[i-1]["speaker_name"],
                    "prev_text": sentences[i-1]["text"][:80],
                    "prev_end": prev_end,
                    "curr_start": curr_start,
                    "curr_speaker": sentences[i]["speaker_name"],
                    "curr_text": sentences[i]["text"][:80],
                })

    gaps.sort(key=lambda x: x["gap"], reverse=True)
    print(f"Gaps >= 3s: {len(gaps)}")
    print("Top 10 largest gaps:")
    for g in gaps[:10]:
        print(f"  {g['gap']:6.1f}s  |  {g['prev_end']:.1f}s -> {g['curr_start']:.1f}s")
        print(f"    BEFORE [{g['prev_speaker']}]: {g['prev_text']}")
        print(f"    AFTER  [{g['curr_speaker']}]: {g['curr_text']}")
    print()
