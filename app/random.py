"""
Meeting Transcript Chunker
==========================
Converts raw ASR transcript sentences into meaningful chunks.

Pipeline:
  1. Preprocess  — merge micro-fragments, handle cross-speaker completions,
                   tag confirmations, drop pure ASR garbage
  2. Chunk       — hybrid rules (hard gap / soft gap / transition phrase /
                   token limit)
  3. Post-process — merge tiny leftover chunks (< MIN_CHUNK_WORDS)
  4. Print       — show every chunk with its metadata
"""

import re
import json
from dataclasses import dataclass, field
from typing import List, Optional


# ─────────────────────────────────────────────────────────────────────────────
# CONFIG  (tune these for your use-case)
# ─────────────────────────────────────────────────────────────────────────────
MERGE_GAP_SECONDS   = 2.0    # same-speaker fragments closer than this → merge
SHORT_WORD_THRESH   = 4      # utterances with fewer words are candidates for merge
ARTIFACT_ISOLATION  = 20.0   # pure noise isolated by this gap on both sides → drop
HARD_GAP            = 15.0   # seconds — always start a new chunk
SOFT_GAP            = 8.0    # seconds + speaker change → start a new chunk
MAX_CHUNK_WORDS     = 300    # word-count ceiling per chunk
MIN_CHUNK_WORDS     = 30     # chunks below this get merged into their neighbor


# ─────────────────────────────────────────────────────────────────────────────
# DATA MODEL
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class Utterance:
    text:             str
    speaker_name:     str
    start_time:       float
    end_time:         float
    speakers:         set  = field(default_factory=set)
    is_continuation:  bool = False          # cross-speaker sentence completion
    confirmation_type: Optional[str] = None # "agreement" | "disagreement"
    is_asr_artifact:  bool = False


@dataclass
class Chunk:
    utterances:   List[Utterance]
    split_reason: str
    speakers:     List[str]
    word_count:   int

    @property
    def start_time(self):  return self.utterances[0].start_time
    @property
    def end_time(self):    return self.utterances[-1].end_time
    @property
    def text(self):
        lines = []
        for u in self.utterances:
            if u.is_continuation and lines:
                lines[-1] += " " + u.text
            else:
                lines.append(f"{u.speaker_name}: {u.text}")
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — PRE-PROCESSING
# ─────────────────────────────────────────────────────────────────────────────

# Words/phrases that confirm or deny something
AGREEMENT_SIGNALS    = {'yeah','yes','correct','right','exactly','agreed',
                        'sure','yep','got it','okay','ok'}
DISAGREEMENT_SIGNALS = {'no','nope','not really'}

# Single-word / meaningless ASR artifacts
# Only dropped when isolated by 20+ seconds on BOTH sides
ASR_ARTIFACT_RE = re.compile(
    r"^(\d+\s*\d*\.?|[a-z]{1,3}\.|ma'?am\.?|it\.|am\.|cediv\.?)$",
    re.IGNORECASE
)


def tag_confirmation(text: str) -> Optional[str]:
    t = text.strip().lower().rstrip(".,?!")
    if t in AGREEMENT_SIGNALS:    return "agreement"
    if t in DISAGREEMENT_SIGNALS: return "disagreement"
    return None


def preprocess_transcript(raw_sentences: list) -> List[Utterance]:
    """
    Three passes:
      A) Raw dicts  →  Utterance objects
      B) Micro-fragment merging  (same-speaker, small gap, short text)
         Short confirmations ("Yeah.", "Right.") get merged too — NOT dropped.
         Pure ASR noise isolated by 20 s on both sides → dropped.
      C) Cross-speaker completion detection
    """

    # ── A: raw dict → Utterance ───────────────────────────────────────────────
    utts: List[Utterance] = []
    for s in raw_sentences:
        utts.append(Utterance(
            text         = s["text"].strip(),
            speaker_name = s["speaker_name"],
            start_time   = s["start_time"],
            end_time     = s["end_time"],
            speakers     = {s["speaker_name"]},
        ))

    # ── B: merge short / confirmation / artifact utterances ──────────────────
    result: List[Utterance] = []
    i = 0
    while i < len(utts):
        curr  = utts[i]
        words = len(curr.text.split())
        conf  = tag_confirmation(curr.text)

        # Check if pure artifact
        is_artifact = bool(ASR_ARTIFACT_RE.match(curr.text.strip()))
        if is_artifact:
            prev_gap = (curr.start_time - utts[i-1].end_time) if i > 0       else 999
            next_gap = (utts[i+1].start_time - curr.end_time) if i+1<len(utts) else 999
            if prev_gap > ARTIFACT_ISOLATION and next_gap > ARTIFACT_ISOLATION:
                i += 1
                continue  # truly isolated garbage — drop

        # Short utterance or confirmation — merge with context
        if words < SHORT_WORD_THRESH or conf:
            merged = False

            # Try merging with PREVIOUS utterance (gap < MERGE_GAP)
            if result:
                gap_prev = curr.start_time - result[-1].end_time
                if gap_prev < MERGE_GAP_SECONDS:
                    result[-1].text       += " " + curr.text
                    result[-1].end_time    = curr.end_time
                    result[-1].speakers.add(curr.speaker_name)
                    if conf:
                        result[-1].confirmation_type = conf
                    merged = True

            # Try merging with NEXT utterance
            if not merged and i + 1 < len(utts):
                gap_next = utts[i+1].start_time - curr.end_time
                if gap_next < MERGE_GAP_SECONDS:
                    utts[i+1].text        = curr.text + " " + utts[i+1].text
                    utts[i+1].start_time  = curr.start_time
                    utts[i+1].speakers.add(curr.speaker_name)
                    if conf:
                        utts[i+1].confirmation_type = conf
                    i += 1
                    continue

            # Too isolated to merge — keep as-is (still not dropped)
            if not merged:
                if conf:
                    curr.confirmation_type = conf
                result.append(curr)
        else:
            if conf:
                curr.confirmation_type = conf
            result.append(curr)

        i += 1

    # ── C: cross-speaker completion tagging ──────────────────────────────────
    for j in range(len(result) - 1):
        gap        = result[j+1].start_time - result[j].end_time
        ends_clean = result[j].text.strip().endswith(('.', '?', '!'))
        words_j    = len(result[j].text.split())
        if gap < 1.5 and words_j < 10 and not ends_clean:
            result[j+1].is_continuation = True

    return result


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — HYBRID CHUNKER
# ─────────────────────────────────────────────────────────────────────────────

# Explicit topic-transition phrases → always force a new chunk
TRANSITION_RE = re.compile(
    r"(okay[\s,]+let'?s go to|let'?s go to the next|"
    r"my (next|last) quer|shall we proceed|"
    r"next quer|and for my next|moving on|"
    r"okay,?\s+let'?s proceed)",
    re.IGNORECASE
)


def hybrid_chunk(utterances: List[Utterance]) -> List[Chunk]:
    """
    Four split signals (priority order):
      1. Hard time gap  ≥ HARD_GAP  seconds          → forced split
      2. Explicit transition phrase in utterance text → forced split
      3. Word count of buffer > MAX_CHUNK_WORDS       → forced split
      4. Soft gap ≥ SOFT_GAP + speaker change         → split
    """
    if not utterances:
        return []

    chunks: List[Chunk] = []
    buf:    List[Utterance] = [utterances[0]]
    buf_words = len(utterances[0].text.split())

    def flush(reason: str):
        nonlocal buf, buf_words
        speakers = list(dict.fromkeys(u.speaker_name for u in buf))
        chunks.append(Chunk(
            utterances   = buf,
            split_reason = reason,
            speakers     = speakers,
            word_count   = buf_words,
        ))
        buf       = []
        buf_words = 0

    for i in range(1, len(utterances)):
        curr      = utterances[i]
        prev      = utterances[i - 1]
        gap       = curr.start_time - prev.end_time
        curr_words = len(curr.text.split())

        # ── Rule 1: hard gap ─────────────────────────────────────────────────
        if gap >= HARD_GAP:
            flush(f"HARD GAP [{gap:.0f}s]")
            buf       = [curr]
            buf_words = curr_words
            continue

        # ── Rule 2: explicit transition phrase ───────────────────────────────
        if TRANSITION_RE.search(curr.text):
            flush(f"TRANSITION PHRASE")
            buf       = [curr]
            buf_words = curr_words
            continue

        # ── Rule 3: token-limit overflow ─────────────────────────────────────
        if buf_words + curr_words > MAX_CHUNK_WORDS:
            flush(f"TOKEN LIMIT [{buf_words}+{curr_words}>{MAX_CHUNK_WORDS}]")
            buf       = [curr]
            buf_words = curr_words
            continue

        # ── Rule 4: soft gap + speaker change ────────────────────────────────
        if gap >= SOFT_GAP and curr.speaker_name != buf[-1].speaker_name:
            flush(f"SOFT GAP+SPEAKER [{gap:.0f}s]")
            buf       = [curr]
            buf_words = curr_words
            continue

        # No split — append to buffer
        buf.append(curr)
        buf_words += curr_words

    if buf:
        flush("END")

    return chunks


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — POST-PROCESS: merge tiny chunks
# ─────────────────────────────────────────────────────────────────────────────

def merge_tiny_chunks(chunks: List[Chunk], min_words: int = MIN_CHUNK_WORDS) -> List[Chunk]:
    """
    Chunks with fewer than min_words get merged into their neighbor.
    Prefer merging with NEXT chunk; fall back to PREVIOUS.
    """
    if not chunks:
        return chunks

    result: List[Chunk] = []
    i = 0
    while i < len(chunks):
        c = chunks[i]
        if c.word_count < min_words:
            if i + 1 < len(chunks):
                # merge into next
                nxt = chunks[i + 1]
                merged_utts = c.utterances + nxt.utterances
                merged_words = c.word_count + nxt.word_count
                merged_speakers = list(dict.fromkeys(
                    u.speaker_name for u in merged_utts
                ))
                chunks[i + 1] = Chunk(
                    utterances   = merged_utts,
                    split_reason = nxt.split_reason,
                    speakers     = merged_speakers,
                    word_count   = merged_words,
                )
                i += 1   # skip current (it's been absorbed into next)
                continue
            elif result:
                # merge into previous (last item in result)
                prev = result[-1]
                merged_utts = prev.utterances + c.utterances
                merged_words = prev.word_count + c.word_count
                merged_speakers = list(dict.fromkeys(
                    u.speaker_name for u in merged_utts
                ))
                result[-1] = Chunk(
                    utterances   = merged_utts,
                    split_reason = prev.split_reason,
                    speakers     = merged_speakers,
                    word_count   = merged_words,
                )
                i += 1
                continue
        result.append(c)
        i += 1
    return result


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — BUILD FINAL METADATA DICT (ready to store in vector DB)
# ─────────────────────────────────────────────────────────────────────────────

def build_chunk_metadata(chunk: Chunk, chunk_index: int,
                          meeting_id: str, project_id: str,
                          company_id: str) -> dict:
    """
    Static metadata that doesn't need an LLM call.
    LLM fields (topic, chunk_type, hypothetical_q, etc.)
    are added in the next pipeline stage via batch LLM call.
    """
    def fmt_time(secs: float) -> str:
        m, s = divmod(int(secs), 60)
        return f"{m:02d}:{s:02d}"

    has_question   = any('?' in u.text for u in chunk.utterances)
    q_speakers     = list(dict.fromkeys(
        u.speaker_name for u in chunk.utterances if '?' in u.text
    ))
    has_agreement  = any(u.confirmation_type == "agreement"
                         for u in chunk.utterances)
    has_disagreement = any(u.confirmation_type == "disagreement"
                           for u in chunk.utterances)

    return {
        # scope
        "company_id":       company_id,
        "project_id":       project_id,
        "meeting_id":       meeting_id,
        # position
        "chunk_index":      chunk_index,
        "level":            "L0",
        # timing
        "timestamp_start":  fmt_time(chunk.start_time),
        "timestamp_end":    fmt_time(chunk.end_time),
        "start_seconds":    chunk.start_time,
        "end_seconds":      chunk.end_time,
        # speakers
        "speakers":         chunk.speakers,
        "speaker_count":    len(chunk.speakers),
        # content signals (rule-based — reliable for these simple cases)
        "has_question":     has_question,
        "question_speakers": q_speakers,
        "has_agreement":    has_agreement,
        "has_disagreement": has_disagreement,
        # chunk stats
        "word_count":       chunk.word_count,
        "utterance_count":  len(chunk.utterances),
        "split_reason":     chunk.split_reason,
        # LLM fields — to be filled by batch metadata extraction
        "topic":            None,
        "chunk_type":       None,
        "hypothetical_q":   None,
        "decision_made":    None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# MAIN — run everything and print results
# ─────────────────────────────────────────────────────────────────────────────

def run_pipeline(transcript: dict,
                 project_id: str = "proj_001",
                 company_id: str = "comp_001") -> list:

    meeting_id = transcript.get("id", "meet_unknown")
    sentences  = transcript["sentences"]

    print(f"\n{'='*65}")
    print(f" Meeting : {transcript.get('title', meeting_id)}")
    print(f" Date    : {transcript.get('dateString', 'N/A')[:10]}")
    print(f"{'='*65}\n")

    # ── Step 1: preprocess ────────────────────────────────────────────────────
    utterances = preprocess_transcript(sentences)
    print(f"[1] Raw sentences      : {len(sentences)}")
    print(f"[1] After preprocessing: {len(utterances)} utterances\n")

    # ── Step 2: chunk ─────────────────────────────────────────────────────────
    raw_chunks = hybrid_chunk(utterances)
    print(f"[2] Chunks after hybrid chunker : {len(raw_chunks)}")

    tiny = sum(1 for c in raw_chunks if c.word_count < MIN_CHUNK_WORDS)
    print(f"    of which tiny (<{MIN_CHUNK_WORDS} words) : {tiny}\n")

    # ── Step 3: merge tiny chunks ─────────────────────────────────────────────
    chunks = merge_tiny_chunks(raw_chunks)
    print(f"[3] Chunks after merging tiny   : {len(chunks)}")
    print(f"    These {len(chunks)} chunks will go to LLM for metadata.\n")

    # ── Step 4: build output dicts ────────────────────────────────────────────
    output = []
    for idx, chunk in enumerate(chunks):
        meta = build_chunk_metadata(chunk, idx, meeting_id, project_id, company_id)
        output.append({
            "text":     chunk.text,
            "metadata": meta,
        })

    # ── Print detailed breakdown ──────────────────────────────────────────────
    print(f"{'─'*65}")
    print(f"  {'#':>2}  {'TIME':^13}  {'WDS':>4}  {'UTT':>3}  SPLIT REASON")
    print(f"{'─'*65}")
    for item in output:
        m = item["metadata"]
        print(f"  {m['chunk_index']+1:>2}  "
              f"{m['timestamp_start']}→{m['timestamp_end']:>5}  "
              f"{m['word_count']:>4}w  "
              f"{m['utterance_count']:>3}u  "
              f"{m['split_reason']}")
        # First speaker and first 70 chars of text
        first_line = item["text"].split('\n')[0][:72]
        print(f"      Speakers : {', '.join(m['speakers'])}")
        print(f"      Preview  : {first_line}")
        print()

    print(f"{'='*65}")
    print(f" TOTAL CHUNKS READY FOR LLM METADATA: {len(output)}")
    print(f"{'='*65}\n")

    # ── Full payload — exactly what goes to the LLM ───────────────────────────
    print(f"\n{'#'*65}")
    print(f"  FULL LLM PAYLOAD — {len(output)} chunks")
    print(f"{'#'*65}\n")
    for item in output:
        m = item["metadata"]
        print(f"┌─ CHUNK {m['chunk_index']+1} {'─'*55}")
        print(f"│  Time     : {m['timestamp_start']} → {m['timestamp_end']}  "
              f"({m['start_seconds']:.1f}s – {m['end_seconds']:.1f}s)")
        print(f"│  Speakers : {', '.join(m['speakers'])}  (count={m['speaker_count']})")
        print(f"│  Words    : {m['word_count']}   Utterances: {m['utterance_count']}")
        print(f"│  Split by : {m['split_reason']}")
        print(f"│  Signals  : "
              f"question={m['has_question']}  "
              f"agreement={m['has_agreement']}  "
              f"disagreement={m['has_disagreement']}")
        if m['has_question'] and m['question_speakers']:
            print(f"│  Q asked by: {', '.join(m['question_speakers'])}")
        print(f"│  Scope    : company={m['company_id']}  project={m['project_id']}  "
              f"meeting={m['meeting_id']}")
        print(f"│  LLM slots: topic=None  chunk_type=None  "
              f"hypothetical_q=None  decision_made=None")
        print(f"│")
        print(f"│  TEXT:")
        for line in item["text"].split("\n"):
            print(f"│    {line}")
        print(f"└{'─'*63}\n")

    return output


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":

    # ── Inline transcript (from the shared meeting) ───────────────────────────
    transcript = {
        "id":         "01KM2DD6MXGSZ4F1QW0BNJE16N",
        "title":      "Nolocode meeting with Ashpreet",
        "dateString": "2026-03-19T06:44:26.000Z",
        "sentences": [
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Would have been great to like also have gotten these questions before yesterday and had you guys already shared this document with, with what's the name Akash or.",
                    "start_time": 0.08,
                    "end_time": 12.4
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "No, we have to share any kind of document with Akash yet because they just informed us that we can discuss everything with you.",
                    "start_time": 14.96,
                    "end_time": 21.36
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "So that.",
                    "start_time": 21.36,
                    "end_time": 21.84
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Because that was the kind of loop that they are informing us then we still have the queries and we need to ask them again and they are asking you.",
                    "start_time": 21.84,
                    "end_time": 28.24
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "So that's why we have set up this meeting so that we can discuss everything with you directly",
                    "start_time": 28.62,
                    "end_time": 33.26
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "also ma'.",
                    "start_time": 35.34,
                    "end_time": 36.34
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Am.",
                    "start_time": 36.34,
                    "end_time": 36.54
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "But we have shared some of the questions with them.",
                    "start_time": 36.86,
                    "end_time": 39.82
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "We have not shared this sheet particularly but we have shared directly questions with",
                    "start_time": 40.22,
                    "end_time": 44.82
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "them they are aware about.",
                    "start_time": 44.82,
                    "end_time": 46.38
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Yeah, I think there was some confusion because I think we went back and forth but we didn't understand the actual questions.",
                    "start_time": 47.18,
                    "end_time": 52.42
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Now it seems a bit more clear.",
                    "start_time": 52.42,
                    "end_time": 53.82
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "So usually like ONCA and is really used in the balance sheet and the cash flow forecast.",
                    "start_time": 54.46,
                    "end_time": 59.58
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Right.",
                    "start_time": 59.58,
                    "end_time": 59.9
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "I'm trying to see like whether we did use it.",
                    "start_time": 62.38,
                    "end_time": 64.86
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah, no, so I'm looking at onca.",
                    "start_time": 66.46,
                    "end_time": 68.7
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "We haven't given long term investments, investment property goodwill.",
                    "start_time": 68.7,
                    "end_time": 74.22
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "We haven't given.",
                    "start_time": 74.22,
                    "end_time": 75.18
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah, I think we can, we haven't given a forecasted formula for it.",
                    "start_time": 80.87,
                    "end_time": 86.39
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "So when you can provide that to us because actually the thing is we are still stuck in these kind of things and we are unable to proceed it further.",
                    "start_time": 89.11,
                    "end_time": 96.87
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "So it would be good if you feel like that.",
                    "start_time": 97.35,
                    "end_time": 99.67
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Yes, some formulas are required from your end and then you can provide it at your earliest.",
                    "start_time": 99.67,
                    "end_time": 103.83
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay, let's go to the next question.",
                    "start_time": 109.52,
                    "end_time": 110.6
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "I can try to give you the formula on this call itself.",
                    "start_time": 110.6,
                    "end_time": 113.12
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "And other, my other question is for OCA we have four value in the document.",
                    "start_time": 114.64,
                    "end_time": 119.44
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Like one is prepaid open, new prepaid, prepaid amount and prepaid close.",
                    "start_time": 120.24,
                    "end_time": 127.52
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "So",
                    "start_time": 128.16,
                    "end_time": 128.56
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "OCA will be prepaid closed.",
                    "start_time": 130.56,
                    "end_time": 132.28
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right.",
                    "start_time": 132.28,
                    "end_time": 132.48
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "That is telling you the calculation of how to get there from open to close.",
                    "start_time": 132.48,
                    "end_time": 137.53
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So it's pretty paid.",
                    "start_time": 137.93,
                    "end_time": 139.21
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "So how we will calculate it like prepare close minus prepaid open for change in oca.",
                    "start_time": 139.37,
                    "end_time": 145.21
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Change in oca it will be what your prepaid close is from the previous month.",
                    "start_time": 149.13,
                    "end_time": 153.53
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So if you're looking at March 2026, you're comparing your March 2026 prepaid close number to February 2026 prepaid close and",
                    "start_time": 154.25,
                    "end_time": 164.21
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "for January we will take from the previous year.",
                    "start_time": 164.21,
                    "end_time": 168.05
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah.",
                    "start_time": 168.53,
                    "end_time": 168.93
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "December 2025.",
                    "start_time": 168.93,
                    "end_time": 170.21
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "So we will take that OC OCA value like in the code, like some of these three.",
                    "start_time": 171.89,
                    "end_time": 181.25
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah, so.",
                    "start_time": 181.33,
                    "end_time": 182.01
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So I think I've given that number as well.",
                    "start_time": 182.01,
                    "end_time": 184.17
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So if you go to inputs, the inputs tab here in this sheet.",
                    "start_time": 184.17,
                    "end_time": 190.43
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "No, no, no, no, no, no, no.",
                    "start_time": 191.63,
                    "end_time": 192.95
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Go back to the other sheet you're on or even.",
                    "start_time": 192.95,
                    "end_time": 195.67
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah.",
                    "start_time": 195.67,
                    "end_time": 196.07
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "If you go to inputs.",
                    "start_time": 196.07,
                    "end_time": 197.39
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "I think if you go down.",
                    "start_time": 198.11,
                    "end_time": 201.95
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "I think this is where he.",
                    "start_time": 201.95,
                    "end_time": 206.27
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Prepaid opening.",
                    "start_time": 212.84,
                    "end_time": 213.8
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah.",
                    "start_time": 214.36,
                    "end_time": 214.84
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So you have.",
                    "start_time": 214.84,
                    "end_time": 215.52
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right.",
                    "start_time": 215.52,
                    "end_time": 215.88
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "26 2.",
                    "start_time": 216.12,
                    "end_time": 217.32
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "You have the AR balance, inventory balance, AP balance.",
                    "start_time": 217.64,
                    "end_time": 220.92
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah, we've added all that in here.",
                    "start_time": 220.92,
                    "end_time": 222.6
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "I think we like we have to",
                    "start_time": 224.36,
                    "end_time": 226.08
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "only take this sub account value.",
                    "start_time": 226.08,
                    "end_time": 228.28
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yes, we gave the balance and then Akash had put in some, some comments right in there because I remember going through this with him in the call a couple of weeks ago.",
                    "start_time": 229.16,
                    "end_time": 238.83
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Just to clarify rhythm.",
                    "start_time": 242.19,
                    "end_time": 243.71
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Actually we need to take into.",
                    "start_time": 244.51,
                    "end_time": 246.07
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "For the oca, we need to take into account for the prepaid close.",
                    "start_time": 246.07,
                    "end_time": 251.07
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "And if you need to calculate for the December 2025, you will need to like take into account all the three other values and add and subtract according to the formula.",
                    "start_time": 251.39,
                    "end_time": 263.11
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Then you will get the value for the December part.",
                    "start_time": 263.11,
                    "end_time": 265.39
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "No, no, no, no, no, no.",
                    "start_time": 266.08,
                    "end_time": 267.4
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Repaid clothes you already have.",
                    "start_time": 267.4,
                    "end_time": 268.88
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right?",
                    "start_time": 268.88,
                    "end_time": 269.2
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "You already have the actual number from December 2025.",
                    "start_time": 269.28,
                    "end_time": 271.84
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "That's what I'm saying.",
                    "start_time": 271.84,
                    "end_time": 272.6
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "These are from there.",
                    "start_time": 272.6,
                    "end_time": 273.44
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Do you have it to them?",
                    "start_time": 273.44,
                    "end_time": 274.32
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Yep.",
                    "start_time": 274.88,
                    "end_time": 275.36
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "They are saying to take this value, this account prepaid expenses which come under code OCA for December 2025 and that value is 262141.",
                    "start_time": 275.36,
                    "end_time": 288.16
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay.",
                    "start_time": 288.88,
                    "end_time": 289.44
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Okay.",
                    "start_time": 289.92,
                    "end_time": 291.07
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "And for my next question is for earnings not in retained earning as I show you there cash flow, change in earnings not attribute to retained income.",
                    "start_time": 295.3,
                    "end_time": 309.86
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "So four changes for actual value.",
                    "start_time": 314.18,
                    "end_time": 319.18
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "We have this formula used in code by your team.",
                    "start_time": 319.26,
                    "end_time": 323.1
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Like change in retain learning and other equity equal to change in other equity plus change in current earning plus change in retained earnings minus these values.",
                    "start_time": 324.14,
                    "end_time": 333.9
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "But you only provide us this code.",
                    "start_time": 335.34,
                    "end_time": 338.06
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "We do not have any formula to how to calculate for forecasting.",
                    "start_time": 348.71,
                    "end_time": 353.43
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Can you show me where that is in the financial statements in the ua?",
                    "start_time": 357.27,
                    "end_time": 363.27
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah.",
                    "start_time": 363.59,
                    "end_time": 364.07
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Change in earnings.",
                    "start_time": 364.23,
                    "end_time": 365.35
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So this is in cash flow, right?",
                    "start_time": 367.51,
                    "end_time": 368.95
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Yep.",
                    "start_time": 370.11,
                    "end_time": 370.59
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "If we have to use the formula used by your team then we need these four values also like change in other equity, change in current earnings, dividends and adjustments like their forecasting values.",
                    "start_time": 382.35,
                    "end_time": 396.44
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So forecasting value for dividends you already have.",
                    "start_time": 397,
                    "end_time": 399.44
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right.",
                    "start_time": 399.44,
                    "end_time": 399.8
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Okay.",
                    "start_time": 400.2,
                    "end_time": 400.84
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "But we don't have change in other equity and change in current earnings.",
                    "start_time": 404.12,
                    "end_time": 409.88
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Can I see which the code that they're referring to if you go to the source documentation where there is.",
                    "start_time": 411.96,
                    "end_time": 419.48
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah.",
                    "start_time": 419.88,
                    "end_time": 420.36
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So change in other equity and change in current earnings.",
                    "start_time": 421.65,
                    "end_time": 424.29
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah.",
                    "start_time": 424.29,
                    "end_time": 424.85
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So the actual Excel with the financial data, which line items are you, are they referring to in the code?",
                    "start_time": 425.49,
                    "end_time": 432.29
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "In the code your team is using this formula.",
                    "start_time": 439.25,
                    "end_time": 442.93
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah.",
                    "start_time": 447.5,
                    "end_time": 447.78
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So which account Classifications are they taking.",
                    "start_time": 447.78,
                    "end_time": 450.22
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "They are taking break for a second.",
                    "start_time": 451.1,
                    "end_time": 454.06
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "They are taking oeq.",
                    "start_time": 460.46,
                    "end_time": 462.14
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay.",
                    "start_time": 464.46,
                    "end_time": 465.02
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Dividend div.",
                    "start_time": 465.5,
                    "end_time": 466.94
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Retained earning RA for adjustment.",
                    "start_time": 468.46,
                    "end_time": 471.9
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "They are taking adjustments.",
                    "start_time": 471.9,
                    "end_time": 473.59
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Can you just write these all down so it's clear to us as well?",
                    "start_time": 475.42,
                    "end_time": 479.42
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay.",
                    "start_time": 480.38,
                    "end_time": 481.02
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "In the document which you created and just write every code in front of the.",
                    "start_time": 481.58,
                    "end_time": 486.3
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah.",
                    "start_time": 487.74,
                    "end_time": 488.26
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So then it's.",
                    "start_time": 488.26,
                    "end_time": 489.02
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "It's clear",
                    "start_time": 489.02,
                    "end_time": 489.58
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "in the formula only.",
                    "start_time": 492.62,
                    "end_time": 493.62
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Can you.",
                    "start_time": 493.62,
                    "end_time": 494.1
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "In the formula, how we are calculating each value Just in the.",
                    "start_time": 494.1,
                    "end_time": 498.7
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "In the circular braces.",
                    "start_time": 498.7,
                    "end_time": 500.06
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Just write the.",
                    "start_time": 501.01,
                    "end_time": 501.73
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "You can write.",
                    "start_time": 504.93,
                    "end_time": 505.65
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "It.",
                    "start_time": 526.3,
                    "end_time": 526.54
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "So we need to calculate these forecasting values also to calculate this.",
                    "start_time": 554.87,
                    "end_time": 560.63
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Cediv.",
                    "start_time": 566.47,
                    "end_time": 567.59
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So div.",
                    "start_time": 567.749,
                    "end_time": 568.31
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "You have.",
                    "start_time": 568.55,
                    "end_time": 569.11
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Yeah.",
                    "start_time": 569.35,
                    "end_time": 569.91
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right.",
                    "start_time": 570.63,
                    "end_time": 571.03
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So can we just put a note that the values you already have.",
                    "start_time": 571.11,
                    "end_time": 573.99
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah, so this is already provided.",
                    "start_time": 574.47,
                    "end_time": 576.31
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Adj.",
                    "start_time": 578.24,
                    "end_time": 578.88
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "We said we're not doing.",
                    "start_time": 578.88,
                    "end_time": 580.04
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right.",
                    "start_time": 580.04,
                    "end_time": 580.4
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So we're not forecasting adjustments.",
                    "start_time": 580.72,
                    "end_time": 585
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right.",
                    "start_time": 585,
                    "end_time": 585.36
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "For forecasting.",
                    "start_time": 585.36,
                    "end_time": 586.48
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So that's not applicable.",
                    "start_time": 586.88,
                    "end_time": 588.08
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "We also have change in retained earnings.",
                    "start_time": 590,
                    "end_time": 592.32
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Then we need these two values.",
                    "start_time": 593.6,
                    "end_time": 595.2
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "And my last query is for fixed assets.",
                    "start_time": 601.52,
                    "end_time": 603.76
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah, Just one second.",
                    "start_time": 605.83,
                    "end_time": 607.11
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Is it ce?",
                    "start_time": 612.23,
                    "end_time": 613.03
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "I don't see CE as a classification anyway.",
                    "start_time": 613.11,
                    "end_time": 616.15
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "It is mentioned in the code there ce.",
                    "start_time": 617.19,
                    "end_time": 620.389
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So I don't.",
                    "start_time": 621.43,
                    "end_time": 622.11
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "If you look at the document.",
                    "start_time": 622.11,
                    "end_time": 623.39
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "I don't.",
                    "start_time": 623.39,
                    "end_time": 623.71
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Is it CE or re?",
                    "start_time": 623.71,
                    "end_time": 624.87
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Are you sure",
                    "start_time": 625.27,
                    "end_time": 625.91
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "this code in the",
                    "start_time": 629.19,
                    "end_time": 629.95
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "document,",
                    "start_time": 629.95,
                    "end_time": 630.47
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Are you able to define the code and find where it's been applied?",
                    "start_time": 640.6,
                    "end_time": 643.96
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Maybe it was renamed in the code.",
                    "start_time": 644.52,
                    "end_time": 646.519
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Obviously we are not aware.",
                    "start_time": 646.519,
                    "end_time": 647.72
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Like are you able to follow that and see how many times it's been used or in which calculation it was used in the code?",
                    "start_time": 647.88,
                    "end_time": 654.2
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "It is used for current earnings prior current running.",
                    "start_time": 656.74,
                    "end_time": 660.98
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "But why is it defined before this or used?",
                    "start_time": 665.94,
                    "end_time": 668.9
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "They are just using this classification code only and they will search it from DB then.",
                    "start_time": 671.3,
                    "end_time": 677.38
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So can you see where they're extracting the.",
                    "start_time": 678.74,
                    "end_time": 680.82
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So we have the db right.",
                    "start_time": 681.22,
                    "end_time": 682.66
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "And if we can we see what numbers they're extracting for some particular month so we can see where they're deriving the numbers from?",
                    "start_time": 683.34,
                    "end_time": 690.62
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "From the Excel db.",
                    "start_time": 690.86,
                    "end_time": 692.38
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Wait a second.",
                    "start_time": 693.58,
                    "end_time": 694.46
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "I will check.",
                    "start_time": 694.78,
                    "end_time": 695.46
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Prism.",
                    "start_time": 767.53,
                    "end_time": 767.85
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Can you run a query just to find all the data related to CE code only?",
                    "start_time": 767.85,
                    "end_time": 773.37
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Yes sir.",
                    "start_time": 773.69,
                    "end_time": 774.41
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "It.",
                    "start_time": 785.14,
                    "end_time": 785.38
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "No, we do not have any count related to that as we will uploading this Excel sheet.",
                    "start_time": 827.23,
                    "end_time": 835.39
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "But in this Excel sheet there is no such code.",
                    "start_time": 835.63,
                    "end_time": 839.54
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "So it is also not present in the db.",
                    "start_time": 840.02,
                    "end_time": 842.34
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So they're taking no.",
                    "start_time": 844.74,
                    "end_time": 845.86
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "No numbers.",
                    "start_time": 846.18,
                    "end_time": 847.14
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yep.",
                    "start_time": 847.54,
                    "end_time": 848.1
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So what's the only number taken then?",
                    "start_time": 848.98,
                    "end_time": 850.62
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "It's only taken from oeq.",
                    "start_time": 850.62,
                    "end_time": 853.7
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Is it?",
                    "start_time": 853.7,
                    "end_time": 854.18
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Yeah.",
                    "start_time": 855.14,
                    "end_time": 864.61
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Maybe your team is providing any other Excel sheet using any other Excel sheet.",
                    "start_time": 866.04,
                    "end_time": 873.72
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "No, it's the same one.",
                    "start_time": 874.28,
                    "end_time": 875.6
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "I'll check with Ashpreet.",
                    "start_time": 875.6,
                    "end_time": 877.16
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Yeah.",
                    "start_time": 877.72,
                    "end_time": 878.12
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Then There is no such code in Adobe.",
                    "start_time": 878.12,
                    "end_time": 881.72
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "We have this code, but no account related to that.",
                    "start_time": 881.88,
                    "end_time": 885.08
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay, so if I, if I take a particular month, what numbers are we using then?",
                    "start_time": 886.36,
                    "end_time": 890.56
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So let's take a number.",
                    "start_time": 890.56,
                    "end_time": 891.72
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Let's take a month like January 2024 for example.",
                    "start_time": 891.8,
                    "end_time": 894.81
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "What are the numbers that it's taking to do the calculation based on this code?",
                    "start_time": 895.05,
                    "end_time": 899.21
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Then we can see which numbers they're taking.",
                    "start_time": 899.69,
                    "end_time": 901.85
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Then they are just taking this code and use this in this function.",
                    "start_time": 920.42,
                    "end_time": 928.1
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "No, no.",
                    "start_time": 931.46,
                    "end_time": 932.02
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So can we take an example to see what numbers are taking and based on the code, let's see what numbers are extracting from the db.",
                    "start_time": 932.02,
                    "end_time": 941.38
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "But in a DB we do not have that account.",
                    "start_time": 942.82,
                    "end_time": 945.06
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Yeah, sorry, rhythm.",
                    "start_time": 948.84,
                    "end_time": 950.28
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "For the full formula they have, they have been taking the OEQ and the adj.",
                    "start_time": 950.84,
                    "end_time": 955.32
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "So can you calculate value for one month using the other other other data like change in retained earning another equity or there are other three things also?",
                    "start_time": 955.88,
                    "end_time": 968.08
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "No, can you let them, can you show the numbers for others?",
                    "start_time": 968.08,
                    "end_time": 972.68
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Have you understood algorithm what we are saying?",
                    "start_time": 977.68,
                    "end_time": 979.6
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "What was the tag again?",
                    "start_time": 1014.97,
                    "end_time": 1016.01
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Pe or ec?",
                    "start_time": 1016.65,
                    "end_time": 1018.01
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Ce.",
                    "start_time": 1019.45,
                    "end_time": 1019.85
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So I don't see ce, I see re.",
                    "start_time": 1020.09,
                    "end_time": 1022.25
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "What if maybe instead of EC they meant equity, they meant equity clause.",
                    "start_time": 1026.32,
                    "end_time": 1031.36
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Right?",
                    "start_time": 1032.8,
                    "end_time": 1033.2
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Because.",
                    "start_time": 1033.28,
                    "end_time": 1033.68
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "And then they're taking the equity open",
                    "start_time": 1033.68,
                    "end_time": 1036.24
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "plus the net profit and balance.",
                    "start_time": 1036.24,
                    "end_time": 1040.88
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "They should have been like ec but then they called it the.",
                    "start_time": 1041.92,
                    "end_time": 1045.44
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Because if you go back to the question they want to know like what value do they put in the cash flow statement and.",
                    "start_time": 1047.04,
                    "end_time": 1054.2
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Every month for.",
                    "start_time": 1060.12,
                    "end_time": 1061.16
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Okay, you guys are trying to calculate the total equity in the balance sheet or what was the question with regard to?",
                    "start_time": 1078.45,
                    "end_time": 1087.41
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "If you go back to the original, original question inside your document.",
                    "start_time": 1090.69,
                    "end_time": 1094.29
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So what's the calculation you after number three.",
                    "start_time": 1100.05,
                    "end_time": 1102.53
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "After number three for fixed assets.",
                    "start_time": 1104.46,
                    "end_time": 1107.26
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "No, no, no, no, no.",
                    "start_time": 1107.42,
                    "end_time": 1108.7
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Change in retaining earning another equity.",
                    "start_time": 1110.62,
                    "end_time": 1112.38
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "We are using change in other equity.",
                    "start_time": 1112.54,
                    "end_time": 1114.94
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "No, no, no.",
                    "start_time": 1115.58,
                    "end_time": 1116.18
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "What's, what's the calculation you're after?",
                    "start_time": 1116.18,
                    "end_time": 1118.14
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "This is a formula.",
                    "start_time": 1118.14,
                    "end_time": 1119.18
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "What is the actual calc.",
                    "start_time": 1119.18,
                    "end_time": 1120.26
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "What are you, what are we calculating?",
                    "start_time": 1120.26,
                    "end_time": 1121.66
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Earnings.",
                    "start_time": 1128.87,
                    "end_time": 1129.27
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Not in retained earnings.",
                    "start_time": 1129.27,
                    "end_time": 1131.07
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Wouldn't that be equity?",
                    "start_time": 1131.07,
                    "end_time": 1133.19
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Yeah, I will show you in ui.",
                    "start_time": 1134.23,
                    "end_time": 1136.63
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah, So it's under financing activities.",
                    "start_time": 1137.59,
                    "end_time": 1144.55
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay, just going to the Excel.",
                    "start_time": 1148.31,
                    "end_time": 1150.55
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "So shall we proceed with the next query?",
                    "start_time": 1174.72,
                    "end_time": 1176.56
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Just one second.",
                    "start_time": 1178.24,
                    "end_time": 1179.2
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay.",
                    "start_time": 1179.85,
                    "end_time": 1180.33
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay, let's go to the next query.",
                    "start_time": 1215.94,
                    "end_time": 1217.1
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "We'll come back to these two.",
                    "start_time": 1217.1,
                    "end_time": 1218.34
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Yeah, the next queries.",
                    "start_time": 1218.58,
                    "end_time": 1221.419
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "For fixed assets, as you mentioned in the sheet, for sub account we need to use PP closing and total depreciation from capex.",
                    "start_time": 1221.419,
                    "end_time": 1233.71
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "But for actual value for property and equipment or for accumulated depreciation, which code we will refer.",
                    "start_time": 1235.63,
                    "end_time": 1246.03
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Like under FA code we have four sub Accounts like land and building, plant and machinery, furniture, equipment, or computer equipments.",
                    "start_time": 1247.39,
                    "end_time": 1256.99
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "So all this will come under property and equipments.",
                    "start_time": 1259.21,
                    "end_time": 1262.65
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Correct.",
                    "start_time": 1263.21,
                    "end_time": 1263.77
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "And for accumulated depreciation, for actual, we have depth code which has amortization and depreciation.",
                    "start_time": 1264.49,
                    "end_time": 1274.97
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "So should we use depth code for that?",
                    "start_time": 1275.69,
                    "end_time": 1278.09
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Like I show you, in this financial sheet, we have code dep.",
                    "start_time": 1281.53,
                    "end_time": 1284.95
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "And DEP has six sub accounts.",
                    "start_time": 1286.55,
                    "end_time": 1288.79
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Go back to the ui because we shouldn't.",
                    "start_time": 1290.07,
                    "end_time": 1293.75
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yes.",
                    "start_time": 1294.23,
                    "end_time": 1294.63
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "If you go, where are we looking?",
                    "start_time": 1294.63,
                    "end_time": 1295.99
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "It's balance sheet, right?",
                    "start_time": 1296.23,
                    "end_time": 1297.59
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah.",
                    "start_time": 1303.67,
                    "end_time": 1304.11
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So we shouldn't have accumulated depreciation as a line item here to begin with.",
                    "start_time": 1304.11,
                    "end_time": 1309.35
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So this accumulated depreciation, this wasn't in Ashpreet's code, which is a question he was asking if you've merged the code.",
                    "start_time": 1313.13,
                    "end_time": 1319.81
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Because this accumulated depreciation row was never there and never calculated in the output he had produced.",
                    "start_time": 1319.81,
                    "end_time": 1330.73
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So we should.",
                    "start_time": 1334.33,
                    "end_time": 1335.13
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "We should not have accumulated appreciation.",
                    "start_time": 1335.41,
                    "end_time": 1337.41
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Your question on property and equipment is, basically, there's four accounts.",
                    "start_time": 1337.41,
                    "end_time": 1341.33
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah.",
                    "start_time": 1341.65,
                    "end_time": 1342.01
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "The answer to that, this accumulated depreciation should not be there.",
                    "start_time": 1342.01,
                    "end_time": 1345.65
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Okay.",
                    "start_time": 1346.37,
                    "end_time": 1346.89
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "So we shall remove it from the UI as well and we can just focus on the property and equipment for now.",
                    "start_time": 1346.89,
                    "end_time": 1352.77
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yes.",
                    "start_time": 1353.33,
                    "end_time": 1353.81
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Okay, got it.",
                    "start_time": 1354.05,
                    "end_time": 1355.65
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "And for fixed asset, the sum of this is fixed asset.",
                    "start_time": 1355.89,
                    "end_time": 1360.37
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Closing balance.",
                    "start_time": 1365.13,
                    "end_time": 1365.81
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "My nice.",
                    "start_time": 1365.81,
                    "end_time": 1366.69
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Accumulated depreciation equal to fixed assets.",
                    "start_time": 1366.69,
                    "end_time": 1369.69
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yes.",
                    "start_time": 1370.57,
                    "end_time": 1371.05
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah.",
                    "start_time": 1371.21,
                    "end_time": 1371.69
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "So we are not calculating this.",
                    "start_time": 1372.09,
                    "end_time": 1373.77
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "So this means fixed assets is equal to PP closing balance.",
                    "start_time": 1374.41,
                    "end_time": 1377.529
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Correct.",
                    "start_time": 1378.17,
                    "end_time": 1378.73
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay,",
                    "start_time": 1379.21,
                    "end_time": 1379.85
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "that's all from my side.",
                    "start_time": 1382.09,
                    "end_time": 1383.53
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay.",
                    "start_time": 1385.93,
                    "end_time": 1386.33
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So if you go to the top, don't stop sharing.",
                    "start_time": 1386.33,
                    "end_time": 1389.26
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So you had your question on onca, right?",
                    "start_time": 1389.66,
                    "end_time": 1392.3
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Yeah.",
                    "start_time": 1393.18,
                    "end_time": 1393.74
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So for.",
                    "start_time": 1395.74,
                    "end_time": 1396.26
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So for onca, what you can use is to keep it simple.",
                    "start_time": 1396.26,
                    "end_time": 1401.02
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "You can use the same numbers from the previous year.",
                    "start_time": 1401.02,
                    "end_time": 1403.34
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So ONCA has three items, right?",
                    "start_time": 1403.98,
                    "end_time": 1406.02
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "It has goodwill, investment property, long term investments.",
                    "start_time": 1406.02,
                    "end_time": 1409.18
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "You can use the Same numbers from 2025.",
                    "start_time": 1410.46,
                    "end_time": 1414.46
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Okay.",
                    "start_time": 1415.2,
                    "end_time": 1415.68
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah.",
                    "start_time": 1416.32,
                    "end_time": 1416.88
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "As your forecasted numbers for now.",
                    "start_time": 1417.12,
                    "end_time": 1418.96
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "So there's only one pending question, right?",
                    "start_time": 1435.2,
                    "end_time": 1437.04
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Okay,",
                    "start_time": 1438.48,
                    "end_time": 1439.04
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "yeah.",
                    "start_time": 1441.04,
                    "end_time": 1441.44
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Only one pending question, is it?",
                    "start_time": 1441.44,
                    "end_time": 1442.76
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "That's right.",
                    "start_time": 1442.76,
                    "end_time": 1443.24
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So if you go back to that one pending question.",
                    "start_time": 1443.24,
                    "end_time": 1445.52
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Just one.",
                    "start_time": 1445.76,
                    "end_time": 1446.47
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "One second.",
                    "start_time": 1446.54,
                    "end_time": 1446.94
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Can you share your screen?",
                    "start_time": 1447.26,
                    "end_time": 1448.18
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "One second, please.",
                    "start_time": 1448.18,
                    "end_time": 1448.94
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So what's the one pending question that we have?",
                    "start_time": 1456.06,
                    "end_time": 1458.46
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Not this one rhythm, the third one.",
                    "start_time": 1458.94,
                    "end_time": 1460.54
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah, yeah.",
                    "start_time": 1464.3,
                    "end_time": 1466.26
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So if you go to the Excel, because what you're doing is you're calculating your cash flow for your financing activities, go to the Excel and go to the cash flow tab here.",
                    "start_time": 1466.26,
                    "end_time": 1478.89
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So you can see in column J, you have your financing cash flow from financing activities.",
                    "start_time": 1482.01,
                    "end_time": 1488.41
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "You have the formula here.",
                    "start_time": 1488.41,
                    "end_time": 1489.85
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So if you go into it, You are getting all the numbers right that you have.",
                    "start_time": 1490.49,
                    "end_time": 1502.33
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Okay.",
                    "start_time": 1504.41,
                    "end_time": 1505.05
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So if you follow it to what it's calculating.",
                    "start_time": 1506.65,
                    "end_time": 1509.05
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "These are then your rows basically that you'll get that how you're getting your cash flow from financing activities.",
                    "start_time": 1509.13,
                    "end_time": 1515.69
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "That.",
                    "start_time": 1530.5,
                    "end_time": 1530.66
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Okay, can you repeat that question again?",
                    "start_time": 1530.66,
                    "end_time": 1534.18
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Go to the Excel, go to the sheet again and then click on the cell on.",
                    "start_time": 1536.26,
                    "end_time": 1540.82
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Click on the cell.",
                    "start_time": 1541.22,
                    "end_time": 1542.18
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Okay, now instead of.",
                    "start_time": 1542.18,
                    "end_time": 1543.34
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Yeah, just click once and then go to the, the top of the bar and then you click on CAPEX that you see F83 or any of the values, just click.",
                    "start_time": 1543.34,
                    "end_time": 1552.94
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Click on one of them.",
                    "start_time": 1553.01,
                    "end_time": 1553.81
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Yeah, they're up there.",
                    "start_time": 1554.45,
                    "end_time": 1555.33
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Up there where you are.",
                    "start_time": 1555.33,
                    "end_time": 1556.29
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "So he's saying you should basically, if you want to know the exact calculation and where the source data is coming from, when you click there, you should be able to highlight on this sheet where it's coming from and then use that as the same formula to understand the, the value, the output.",
                    "start_time": 1557.09,
                    "end_time": 1574.37
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Click on it once.",
                    "start_time": 1575.33,
                    "end_time": 1576.17
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Like click on an entire like CAPEX 32 83.",
                    "start_time": 1576.17,
                    "end_time": 1580.29
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Maybe pick one.",
                    "start_time": 1580.29,
                    "end_time": 1582.8
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Click on D83.",
                    "start_time": 1584.56,
                    "end_time": 1585.76
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "It's not there.",
                    "start_time": 1592.8,
                    "end_time": 1593.56
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "I think",
                    "start_time": 1593.56,
                    "end_time": 1594
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "it'll Highlight.",
                    "start_time": 1597.68,
                    "end_time": 1598.56
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "This is D83, 4.",
                    "start_time": 1601.2,
                    "end_time": 1602.88
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yes.",
                    "start_time": 1607.05,
                    "end_time": 1607.33
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "If you follow the formulas, it gives you all the numbers it's taking, right?",
                    "start_time": 1607.33,
                    "end_time": 1611.25
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "As a, as a calculation, there was C67, D67, C83.",
                    "start_time": 1611.25,
                    "end_time": 1617.05
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "If you go, you'll see there about four or five.",
                    "start_time": 1617.29,
                    "end_time": 1619.53
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right, so it's telling you which rows and what it's taking to derive the number.",
                    "start_time": 1620.89,
                    "end_time": 1626.41
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "So it.",
                    "start_time": 1628.17,
                    "end_time": 1628.73
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "We are calculating this, this earning like we have retained.",
                    "start_time": 1628.97,
                    "end_time": 1636.74
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "No, go to the ui.",
                    "start_time": 1637.38,
                    "end_time": 1638.74
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Yeah,",
                    "start_time": 1639.06,
                    "end_time": 1639.62
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "go to the cash flow.",
                    "start_time": 1642.34,
                    "end_time": 1643.62
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "You are calculating financing activities, right?",
                    "start_time": 1645.06,
                    "end_time": 1647.7
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Cash flow from financing activities.",
                    "start_time": 1647.779,
                    "end_time": 1649.62
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So you have got all the, the numbers there, right?",
                    "start_time": 1650.26,
                    "end_time": 1654.22
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "To do.",
                    "start_time": 1654.22,
                    "end_time": 1654.66
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "To, to get to your number,",
                    "start_time": 1654.66,
                    "end_time": 1655.86
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "All the sub items.",
                    "start_time": 1660.98,
                    "end_time": 1662.34
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "You're saying that we have this, this and this.",
                    "start_time": 1664.66,
                    "end_time": 1667.62
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "So we will minus.",
                    "start_time": 1668.58,
                    "end_time": 1670.02
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Then we will calculate financing financing activity.",
                    "start_time": 1670.42,
                    "end_time": 1674.02
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "We will minus this.",
                    "start_time": 1674.26,
                    "end_time": 1675.38
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Then we will get change in earning, not attribute to retaining income.",
                    "start_time": 1675.54,
                    "end_time": 1679.22
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "No, no, no, what I'm saying is from your.",
                    "start_time": 1680.58,
                    "end_time": 1682.58
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "You have sub line items that you can take your calculation from.",
                    "start_time": 1687.39,
                    "end_time": 1690.99
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "That's what I'm saying.",
                    "start_time": 1691.07,
                    "end_time": 1691.95
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "If you follow that formula, you have five, five numbers that it's relating to, right?",
                    "start_time": 1691.95,
                    "end_time": 1697.47
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So you have all the numbers, right?",
                    "start_time": 1697.79,
                    "end_time": 1700.27
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "And if you're summing them all up, you get your total, which is your financing activities.",
                    "start_time": 1700.27,
                    "end_time": 1704.59
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Okay, can you go to Rashid once again?",
                    "start_time": 1705.55,
                    "end_time": 1711.88
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Let me just see that formula.",
                    "start_time": 1712.12,
                    "end_time": 1713.64
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Financial cfa.",
                    "start_time": 1717,
                    "end_time": 1718.28
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Let's just write it down.",
                    "start_time": 1720.84,
                    "end_time": 1722
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right, so let's look at C67 and D67.",
                    "start_time": 1722,
                    "end_time": 1725.2
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Actually write down what?",
                    "start_time": 1725.2,
                    "end_time": 1726.36
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah, so what are C67 and D67?",
                    "start_time": 1727,
                    "end_time": 1729.48
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Why don't you actually write down.",
                    "start_time": 1729.48,
                    "end_time": 1730.84
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Great, yeah, write down the names, right, basically of what?",
                    "start_time": 1731.64,
                    "end_time": 1736.44
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "C67 83 +E83F83.",
                    "start_time": 1736.44,
                    "end_time": 1743
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "D67.",
                    "start_time": 1748.44,
                    "end_time": 1749.56
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "It's new loans here.",
                    "start_time": 1752.12,
                    "end_time": 1754.68
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "D67 is repayments.",
                    "start_time": 1755.72,
                    "end_time": 1758.44
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah.",
                    "start_time": 1758.84,
                    "end_time": 1759.2
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So it's short term debt.",
                    "start_time": 1759.2,
                    "end_time": 1760.76
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right.",
                    "start_time": 1761,
                    "end_time": 1761.4
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So you can see it says short term debt above.",
                    "start_time": 1761.4,
                    "end_time": 1763.88
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right.",
                    "start_time": 1763.88,
                    "end_time": 1764.2
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So short term debt repayments.",
                    "start_time": 1764.44,
                    "end_time": 1766.12
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Okay.",
                    "start_time": 1766.96,
                    "end_time": 1767.28
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "D83 owner funding, F83 dividends.",
                    "start_time": 1768.32,
                    "end_time": 1778.48
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah.",
                    "start_time": 1779.68,
                    "end_time": 1780.16
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So it's D and then ENF.",
                    "start_time": 1780.56,
                    "end_time": 1782.639
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right.",
                    "start_time": 1782.639,
                    "end_time": 1782.96
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So.",
                    "start_time": 1782.96,
                    "end_time": 1783.36
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "And one is external funding.",
                    "start_time": 1783.6,
                    "end_time": 1785.2
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "External funding and then dividends.",
                    "start_time": 1785.28,
                    "end_time": 1787.44
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So those are your.",
                    "start_time": 1791.44,
                    "end_time": 1792.4
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "That's your breakdown of how you get to your financing activities.",
                    "start_time": 1792.93,
                    "end_time": 1796.45
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "So what I would recommend if you",
                    "start_time": 1797.49,
                    "end_time": 1799.49
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "actually like.",
                    "start_time": 1801.57,
                    "end_time": 1802.69
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "We already calculated change in short term depth and change in long term depth.",
                    "start_time": 1802.69,
                    "end_time": 1806.93
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Like can you properly.",
                    "start_time": 1812.05,
                    "end_time": 1813.69
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Like we have we like in the.",
                    "start_time": 1813.69,
                    "end_time": 1816.57
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Before calculating the total financial activities.",
                    "start_time": 1816.57,
                    "end_time": 1818.93
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right.",
                    "start_time": 1819.52,
                    "end_time": 1819.76
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "So you are saying that this is the formula and this will be the total value.",
                    "start_time": 1819.76,
                    "end_time": 1822.96
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "But to calculate the only the change in earning note attribute retained income.",
                    "start_time": 1823.52,
                    "end_time": 1827.28
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "We don't know like which.",
                    "start_time": 1827.28,
                    "end_time": 1828.56
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Which column we should highlight from which column this or which code we need to take into account to calculate the.",
                    "start_time": 1828.56,
                    "end_time": 1834.48
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Just this part only.",
                    "start_time": 1834.48,
                    "end_time": 1835.44
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Like to calculate total financial activity.",
                    "start_time": 1838.48,
                    "end_time": 1840.44
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "You guys told that this is the formula and this is the columns you need to take into account.",
                    "start_time": 1840.44,
                    "end_time": 1844.08
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "But like in the change in earning.",
                    "start_time": 1844.64,
                    "end_time": 1847.41
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Not every tender.",
                    "start_time": 1847.41,
                    "end_time": 1848.53
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Like with what data?",
                    "start_time": 1848.61,
                    "end_time": 1850.89
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Like we need to calculate this from.",
                    "start_time": 1850.89,
                    "end_time": 1852.37
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "No, no.",
                    "start_time": 1852.77,
                    "end_time": 1853.29
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So what I'm saying is your financing activities make up of those five balances.",
                    "start_time": 1853.29,
                    "end_time": 1857.49
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So there's something.",
                    "start_time": 1857.97,
                    "end_time": 1859.01
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "There's something that's happened.",
                    "start_time": 1859.17,
                    "end_time": 1860.77
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Either you've merged the code because these items are not there in what Ashpreet had given.",
                    "start_time": 1860.77,
                    "end_time": 1865.41
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "This change in earnings not attributed to retained income was never there.",
                    "start_time": 1865.65,
                    "end_time": 1869.49
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Actually this is the mockup ui.",
                    "start_time": 1870.05,
                    "end_time": 1874.92
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "We.",
                    "start_time": 1874.92,
                    "end_time": 1875.24
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "We can't change to this part.",
                    "start_time": 1875.24,
                    "end_time": 1876.68
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "So it was there before.",
                    "start_time": 1877.16,
                    "end_time": 1879.4
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Only we haven't changed in the mocked ui.",
                    "start_time": 1879.4,
                    "end_time": 1881.16
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "It's provided from your side only.",
                    "start_time": 1881.16,
                    "end_time": 1882.68
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "It was there starting.",
                    "start_time": 1882.68,
                    "end_time": 1884.52
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Yeah.",
                    "start_time": 1884.52,
                    "end_time": 1884.92
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "No, no.",
                    "start_time": 1884.92,
                    "end_time": 1885.32
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So what I'm saying is current uses five items that we've just gone through.",
                    "start_time": 1885.32,
                    "end_time": 1890.279
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Follow the formulas.",
                    "start_time": 1890.279,
                    "end_time": 1891.32
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay.",
                    "start_time": 1891.56,
                    "end_time": 1892.12
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay.",
                    "start_time": 1892.12,
                    "end_time": 1892.44
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "So you want to that like in the financial activities.",
                    "start_time": 1892.44,
                    "end_time": 1895
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "We should mention those five points here.",
                    "start_time": 1895.4,
                    "end_time": 1897.56
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Not these ones.",
                    "start_time": 1897.56,
                    "end_time": 1898.6
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yes.",
                    "start_time": 1898.92,
                    "end_time": 1899.4
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay.",
                    "start_time": 1900.77,
                    "end_time": 1901.05
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Got it.",
                    "start_time": 1901.05,
                    "end_time": 1901.57
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Okay.",
                    "start_time": 1902.21,
                    "end_time": 1902.77
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So those five points are new loans, short term debt.",
                    "start_time": 1905.17,
                    "end_time": 1909.81
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "It's owner funding, external funding.",
                    "start_time": 1910.21,
                    "end_time": 1913.09
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "And then you have the last one which was.",
                    "start_time": 1913.49,
                    "end_time": 1917.01
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Repayments dividends.",
                    "start_time": 1921.97,
                    "end_time": 1924.21
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Not this one.",
                    "start_time": 1927.74,
                    "end_time": 1928.38
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "No, no.",
                    "start_time": 1929.02,
                    "end_time": 1929.74
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Okay, sir.",
                    "start_time": 1930.3,
                    "end_time": 1931.1
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Yeah, we go.",
                    "start_time": 1935.34,
                    "end_time": 1935.94
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "There we go.",
                    "start_time": 1935.94,
                    "end_time": 1936.54
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "We have.",
                    "start_time": 1936.86,
                    "end_time": 1937.5
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "We have to use these exact value.",
                    "start_time": 1938.06,
                    "end_time": 1939.98
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "We have to use like change in new loans or change in loan close or change in dividends.",
                    "start_time": 1939.98,
                    "end_time": 1945.94
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Like this.",
                    "start_time": 1945.94,
                    "end_time": 1946.54
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Let me answer.",
                    "start_time": 1948.78,
                    "end_time": 1949.74
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "You're calculating the cash flow.",
                    "start_time": 1949.9,
                    "end_time": 1951.5
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So you are asking you.",
                    "start_time": 1951.5,
                    "end_time": 1953.18
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "You are calculating the.",
                    "start_time": 1953.18,
                    "end_time": 1954.7
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Go back to the Excel.",
                    "start_time": 1955.55,
                    "end_time": 1956.91
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Note the movement for.",
                    "start_time": 1964.75,
                    "end_time": 1966.11
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "For that particular month.",
                    "start_time": 1966.11,
                    "end_time": 1967.31
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah, it's for the.",
                    "start_time": 1970.59,
                    "end_time": 1971.95
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "It's for those months.",
                    "start_time": 1971.95,
                    "end_time": 1972.91
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "What they're saying is you need to take the.",
                    "start_time": 1976.67,
                    "end_time": 1978.99
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Like.",
                    "start_time": 1979.15,
                    "end_time": 1979.55
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Suppose this is the.",
                    "start_time": 1979.55,
                    "end_time": 1980.83
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Like this is the value and these are drive from these five values.",
                    "start_time": 1980.99,
                    "end_time": 1983.75
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay.",
                    "start_time": 1983.75,
                    "end_time": 1984.11
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "And these are the actual values.",
                    "start_time": 1984.68,
                    "end_time": 1986.84
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "So you need to like you need to take into account these actual values.",
                    "start_time": 1987,
                    "end_time": 1990.68
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Get their change in values for every month and then we need to show it over there you have the.",
                    "start_time": 1990.84,
                    "end_time": 1996.04
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "No, no, these are the actual values.",
                    "start_time": 1996.84,
                    "end_time": 1998.4
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right.",
                    "start_time": 1998.4,
                    "end_time": 1998.6
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So your actual value.",
                    "start_time": 1998.6,
                    "end_time": 1999.56
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So for example.",
                    "start_time": 1999.56,
                    "end_time": 2000.519
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "No, this is forecasted values.",
                    "start_time": 2000.52,
                    "end_time": 2003.48
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah, yeah.",
                    "start_time": 2004.12,
                    "end_time": 2004.88
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So you're forecasted.",
                    "start_time": 2004.88,
                    "end_time": 2006.08
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So for your cash flow from financing activities, your forecasted value for Jan 2026 will be 20,000.",
                    "start_time": 2006.08,
                    "end_time": 2014.02
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Go back to the UI.",
                    "start_time": 2014.34,
                    "end_time": 2015.62
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah, so that will be minus 20,000.",
                    "start_time": 2017.14,
                    "end_time": 2019.22
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right.",
                    "start_time": 2019.22,
                    "end_time": 2019.5
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So here in financing activities in blue you will have minus 20,000 and then the breakdown you'll have is.",
                    "start_time": 2019.5,
                    "end_time": 2025.5
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "You'll have that breakdown of what those.",
                    "start_time": 2025.5,
                    "end_time": 2027.38
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "What those five items are.",
                    "start_time": 2028.26,
                    "end_time": 2029.74
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right.",
                    "start_time": 2029.74,
                    "end_time": 2030.02
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "How does minus 20,000 break down from.",
                    "start_time": 2030.1,
                    "end_time": 2032.58
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Okay, okay, I got it.",
                    "start_time": 2033.22,
                    "end_time": 2034.5
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Actually I was just trying to say that in here we are showing the change in values.",
                    "start_time": 2034.66,
                    "end_time": 2040.56
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "We are not showing the actual forecasted values.",
                    "start_time": 2040.56,
                    "end_time": 2043
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "So it will be not shown as here 20000 it will be subtract.",
                    "start_time": 2043.4,
                    "end_time": 2047.8
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Suppose we are showing the May value here.",
                    "start_time": 2047.8,
                    "end_time": 2050.12
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "It will be subtracted first and then that value will be shown here.",
                    "start_time": 2050.12,
                    "end_time": 2053.88
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Or do you want to show the actual just the forecasted value there only you don't want to show the change values here.",
                    "start_time": 2054.68,
                    "end_time": 2060.04
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Change in like as we are doing we are subtracting the of the previous month.",
                    "start_time": 2060.04,
                    "end_time": 2064.16
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Then we're showing here like we have",
                    "start_time": 2064.16,
                    "end_time": 2066.57
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "already done for change in short term depth or change in long term depth.",
                    "start_time": 2066.57,
                    "end_time": 2070.21
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "I mean I. I believe you should be showing the.",
                    "start_time": 2073.49,
                    "end_time": 2075.89
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "The forecasted values and then the variance is what shows the change.",
                    "start_time": 2076.13,
                    "end_time": 2079.81
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Correct?",
                    "start_time": 2081.49,
                    "end_time": 2082.13
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Right.",
                    "start_time": 2082.21,
                    "end_time": 2082.53
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "But yeah, so the variance column like at the last.",
                    "start_time": 2082.53,
                    "end_time": 2086.05
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "At the end, that's where usually changes.",
                    "start_time": 2086.21,
                    "end_time": 2088.53
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Yeah, we can do that also.",
                    "start_time": 2089.73,
                    "end_time": 2091.01
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Sure.",
                    "start_time": 2091.319,
                    "end_time": 2091.559
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Like for change in short term, long term depth we are using this formula like loan open from depth calculation for Jan 2026 minus December 2025.",
                    "start_time": 2092.679,
                    "end_time": 2105.159
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Can we do this on WhatsApp?",
                    "start_time": 2106.359,
                    "end_time": 2108.679
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Simran, are you looking at WhatsApp?",
                    "start_time": 2108.999,
                    "end_time": 2110.999
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Yes, yes.",
                    "start_time": 2112.039,
                    "end_time": 2112.839
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "So that's what we are proposing.",
                    "start_time": 2114.839,
                    "end_time": 2116.839
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Okay, you have shared an example.",
                    "start_time": 2118.27,
                    "end_time": 2120.03
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Yes.",
                    "start_time": 2120.99,
                    "end_time": 2121.47
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Okay, let me share that with my team so that they can have a look at it.",
                    "start_time": 2123.39,
                    "end_time": 2126.75
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Just a second.",
                    "start_time": 2130.19,
                    "end_time": 2130.91
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "I am doing it on a quality.",
                    "start_time": 2131.31,
                    "end_time": 2132.91
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "So I mean the example is Excel, right?",
                    "start_time": 2148.92,
                    "end_time": 2151.24
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "The current calculation shows it's 20,000 and that's how it ended up as 20,000 because of the addition or subtraction of Those items.",
                    "start_time": 2151.48,
                    "end_time": 2159.24
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Okay.",
                    "start_time": 2161.4,
                    "end_time": 2162.04
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "So instead of writing the line as change in,",
                    "start_time": 2164.04,
                    "end_time": 2166.44
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "we can show directly.",
                    "start_time": 2169,
                    "end_time": 2170.2
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "We can show directly the.",
                    "start_time": 2170.2,
                    "end_time": 2171.4
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah.",
                    "start_time": 2174.34,
                    "end_time": 2174.54
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "And then the variance column is your change.",
                    "start_time": 2174.54,
                    "end_time": 2176.18
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right.",
                    "start_time": 2176.18,
                    "end_time": 2176.54
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So you can see what that number was from this month versus last month.",
                    "start_time": 2176.54,
                    "end_time": 2179.9
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "And then that is your change in number.",
                    "start_time": 2179.9,
                    "end_time": 2181.94
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right?",
                    "start_time": 2181.94,
                    "end_time": 2182.26
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "You.",
                    "start_time": 2182.26,
                    "end_time": 2182.62
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "You subtracting the current.",
                    "start_time": 2182.62,
                    "end_time": 2183.86
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Current.",
                    "start_time": 2184.26,
                    "end_time": 2184.66
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Current month's number from the previous month's number.",
                    "start_time": 2184.9,
                    "end_time": 2187.54
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Yep, we have got it.",
                    "start_time": 2187.62,
                    "end_time": 2188.82
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "The screenshot, ma', am, I've shared.",
                    "start_time": 2189.54,
                    "end_time": 2191.86
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Yeah.",
                    "start_time": 2192.18,
                    "end_time": 2192.58
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Can you please check the group first?",
                    "start_time": 2192.58,
                    "end_time": 2194.1
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "No, no, local group.",
                    "start_time": 2195.22,
                    "end_time": 2196.42
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Yeah.",
                    "start_time": 2196.42,
                    "end_time": 2196.9
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay.",
                    "start_time": 2200.59,
                    "end_time": 2200.99
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "We don't want to show rhythm changes, actual forecasted values and the variance will show what are the changes values.",
                    "start_time": 2201.47,
                    "end_time": 2208.99
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Okay.",
                    "start_time": 2208.99,
                    "end_time": 2209.39
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "And like we have to do it",
                    "start_time": 2211.47,
                    "end_time": 2213.709
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "for all of this.",
                    "start_time": 2213.709,
                    "end_time": 2215.15
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Like",
                    "start_time": 2215.71,
                    "end_time": 2216.11
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "we are also showing change in other current liabilities, change in account payables, change in inventories.",
                    "start_time": 2218.51,
                    "end_time": 2223.31
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "So we have to show forecasted value or change in values.",
                    "start_time": 2224.29,
                    "end_time": 2228.85
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "For under cash flow.",
                    "start_time": 2230.21,
                    "end_time": 2232.17
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "It is like for operating activities, like change in account payables, change in other current liabilities, change in account receivables.",
                    "start_time": 2232.17,
                    "end_time": 2243.49
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "No, that, no, that is correct.",
                    "start_time": 2244.85,
                    "end_time": 2246.45
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "For operating activities that you have to show the change change.",
                    "start_time": 2246.45,
                    "end_time": 2249.41
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "That is correct.",
                    "start_time": 2249.41,
                    "end_time": 2250.17
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay.",
                    "start_time": 2250.25,
                    "end_time": 2250.69
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay.",
                    "start_time": 2250.69,
                    "end_time": 2251.13
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Like for fine activities, we have to show only forecasted values.",
                    "start_time": 2252.01,
                    "end_time": 2256.65
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah.",
                    "start_time": 2257.61,
                    "end_time": 2258.17
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay.",
                    "start_time": 2258.81,
                    "end_time": 2259.45
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Yes, sir.",
                    "start_time": 2270.41,
                    "end_time": 2271.05
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Thank you.",
                    "start_time": 2273.29,
                    "end_time": 2273.93
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Okay.",
                    "start_time": 2276.1,
                    "end_time": 2276.58
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "If you, if you look at that cash flow, indirect Excel, right.",
                    "start_time": 2277.62,
                    "end_time": 2280.82
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "It gives you the entire formulas of how to calculate your, your cash flow, right?",
                    "start_time": 2280.82,
                    "end_time": 2285.18
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "You just have to follow those formulas and what numbers it's linking to.",
                    "start_time": 2285.18,
                    "end_time": 2288.34
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right?",
                    "start_time": 2288.34,
                    "end_time": 2288.58
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "And you will get the numbers.",
                    "start_time": 2288.58,
                    "end_time": 2289.86
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "You will get what numbers you have to apply for a change versus what you just take as a forecast.",
                    "start_time": 2290.82,
                    "end_time": 2295.78
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Numbers.",
                    "start_time": 2295.78,
                    "end_time": 2296.22
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right, Just that Excel we've given.",
                    "start_time": 2296.22,
                    "end_time": 2297.74
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "You just need to follow it.",
                    "start_time": 2297.74,
                    "end_time": 2299.06
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah, right.",
                    "start_time": 2299.3,
                    "end_time": 2300.1
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "And it links through the different tabs of what numbers it's picking up and what accounts is picking up from.",
                    "start_time": 2300.33,
                    "end_time": 2305.45
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "You just have to follow that for one month.",
                    "start_time": 2305.45,
                    "end_time": 2308.17
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So you understand and then you can apply that for the month.",
                    "start_time": 2308.57,
                    "end_time": 2311.13
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Sure.",
                    "start_time": 2311.69,
                    "end_time": 2312.09
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah.",
                    "start_time": 2312.17,
                    "end_time": 2312.65
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Ma'.",
                    "start_time": 2319.45,
                    "end_time": 2319.73
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Am.",
                    "start_time": 2319.73,
                    "end_time": 2319.93
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So with us there was, with all.",
                    "start_time": 2320.65,
                    "end_time": 2322.89
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "That's the forecasting queries, right?",
                    "start_time": 2323.13,
                    "end_time": 2325.41
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Were there any.",
                    "start_time": 2325.41,
                    "end_time": 2326.01
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "These were all the forecasting queries.",
                    "start_time": 2326.33,
                    "end_time": 2328.25
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So now given these queries, what's the latest timeline?",
                    "start_time": 2329.32,
                    "end_time": 2333.4
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Simran for once you've built it and tested it internally with your QA before you hand over to us, what's your update timeline there?",
                    "start_time": 2333.4,
                    "end_time": 2342.36
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "See, I can provide the updated timelines in some time so that we can discuss and then we can plan accordingly.",
                    "start_time": 2342.36,
                    "end_time": 2350.36
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "That what.",
                    "start_time": 2350.36,
                    "end_time": 2350.92
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "How much time it will require.",
                    "start_time": 2350.92,
                    "end_time": 2352.52
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "And apart from this, we need to work upon the security points and the unit testing as well.",
                    "start_time": 2352.52,
                    "end_time": 2358.2
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "So I will accumulate the meeting with my internal team and then we can provide you with the timelines.",
                    "start_time": 2358.36,
                    "end_time": 2363.96
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay.",
                    "start_time": 2364.36,
                    "end_time": 2364.8
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So for module two it is just a forecasted financials page which is pending.",
                    "start_time": 2364.8,
                    "end_time": 2369.72
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "The other pages are done.",
                    "start_time": 2369.72,
                    "end_time": 2370.92
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Yeah.",
                    "start_time": 2371.32,
                    "end_time": 2371.76
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "You attached the other pages?",
                    "start_time": 2371.76,
                    "end_time": 2373.32
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Yeah, See we.",
                    "start_time": 2373.72,
                    "end_time": 2374.84
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "You can't check it out because the thing is that we have.",
                    "start_time": 2374.84,
                    "end_time": 2377.68
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "We are updating the pusher to socket IO regarding which I need to discuss related everything with Ashbit.",
                    "start_time": 2377.68,
                    "end_time": 2383.8
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "That's why I just want him to join the meeting because he just provided us with his feedback so we have some kind of queries on his feedback because these are some more of the enhancements instead of the changes because we have to put the extra efforts and that will even extend the deadline too.",
                    "start_time": 2383.8,
                    "end_time": 2402.2
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "So that was my only concern, that he should join the meeting so that we can have a discussion in the same call and then we can finalize everything.",
                    "start_time": 2402.6,
                    "end_time": 2410.12
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay, I'm just messaging him so he can join.",
                    "start_time": 2415.24,
                    "end_time": 2417.64
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Also I'm informing my two other team members who are working on a zero part and plus who are working on the socket IO so that they can discuss everything related to the feedback and whatever enhancements and architecture changes that Ashprit is asking for.",
                    "start_time": 2420.36,
                    "end_time": 2436.11
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "The document that Ashpreet sent with the fee.",
                    "start_time": 2437.31,
                    "end_time": 2440.27
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Okay.",
                    "start_time": 2450.19,
                    "end_time": 2450.749
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Any.",
                    "start_time": 2450.99,
                    "end_time": 2451.31
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Any concerns you had on that.",
                    "start_time": 2451.31,
                    "end_time": 2452.59
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "We have documented we have two documents, one with his feedback and other one with the R responses to that feedback.",
                    "start_time": 2454.19,
                    "end_time": 2463.09
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay, yeah, just bring it up.",
                    "start_time": 2463.33,
                    "end_time": 2468.89
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Let's see if there's anything Gomy or I can maybe answer while he joins.",
                    "start_time": 2468.89,
                    "end_time": 2473.33
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Yeah, sure.",
                    "start_time": 2473.65,
                    "end_time": 2475.73
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Yes, yes.",
                    "start_time": 2482.37,
                    "end_time": 2483.17
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "As rhythm is not working on these.",
                    "start_time": 2483.41,
                    "end_time": 2486.57
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "These kind of things.",
                    "start_time": 2486.57,
                    "end_time": 2487.57
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "So he can left the meeting for now because he's working more focused on the forecast module so he can continue his work.",
                    "start_time": 2487.57,
                    "end_time": 2493.61
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Right?",
                    "start_time": 2493.61,
                    "end_time": 2493.93
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Yeah, that's right.",
                    "start_time": 2496.97,
                    "end_time": 2497.65
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Thank you everyone.",
                    "start_time": 2497.65,
                    "end_time": 2498.25
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Yeah, thank you so much.",
                    "start_time": 2498.49,
                    "end_time": 2501.21
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Niha, please open the document they do with the ashpit feedback and plus that you have created the two of the documents.",
                    "start_time": 2518.74,
                    "end_time": 2527.06
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Okay.",
                    "start_time": 2527.54,
                    "end_time": 2528.18
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "And firstly share your screen with the one with the ashp feedback.",
                    "start_time": 2528.42,
                    "end_time": 2532.98
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "So Bhavnit Neha is a front end developer and Manish the back end developer.",
                    "start_time": 2536.02,
                    "end_time": 2540.1
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Hi bhavniti.",
                    "start_time": 2544.43,
                    "end_time": 2552.11
                },
                {
                    "speaker_name": "Neha",
                    "text": "Is my screen visible?",
                    "start_time": 2560.51,
                    "end_time": 2561.71
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Yes.",
                    "start_time": 2564.91,
                    "end_time": 2565.39
                },
                {
                    "speaker_name": "Neha",
                    "text": "So I have gone through this third document and.",
                    "start_time": 2582.2,
                    "end_time": 2585.72
                },
                {
                    "speaker_name": "Neha",
                    "text": "And we have implemented like a double Q system.",
                    "start_time": 2593.97,
                    "end_time": 2598.77
                },
                {
                    "speaker_name": "Neha",
                    "text": "Now dashboard is saying that we should go with the Redis pub sub which will be a better approach.",
                    "start_time": 2598.93,
                    "end_time": 2604.05
                },
                {
                    "speaker_name": "Neha",
                    "text": "And I have gone done some R D like Socket IO the W also a better approach.",
                    "start_time": 2605.57,
                    "end_time": 2613.33
                },
                {
                    "speaker_name": "Neha",
                    "text": "Just the redis is like messaging queue like when the consumer completes the task.",
                    "start_time": 2614.85,
                    "end_time": 2621.74
                },
                {
                    "speaker_name": "Neha",
                    "text": "Redis P also give the responses a little bit too fast as compared to the double Q.",
                    "start_time": 2622.46,
                    "end_time": 2628.86
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So",
                    "start_time": 2634.38,
                    "end_time": 2634.78
                },
                {
                    "speaker_name": "Neha",
                    "text": "WQ is also a better approach.",
                    "start_time": 2637.1,
                    "end_time": 2638.78
                },
                {
                    "speaker_name": "Neha",
                    "text": "We just share the timeline as well.",
                    "start_time": 2639.1,
                    "end_time": 2641.94
                },
                {
                    "speaker_name": "Neha",
                    "text": "That the recommendation which I provided by the split so will take our two working days off.",
                    "start_time": 2641.94,
                    "end_time": 2647.79
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay so I think Ashprit has just sent me a message.",
                    "start_time": 2650.51,
                    "end_time": 2653.19
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "He just stuck in a meeting.",
                    "start_time": 2653.19,
                    "end_time": 2654.27
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Can we do 2:30 India time and in the meantime these your responses to his feedback.",
                    "start_time": 2654.35,
                    "end_time": 2660.39
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "If you just share it on the WhatsApp group he can look at it in the meantime and then Simran if you can just put in a call at 2:30 Indian time which is 1 o' clock UA time.",
                    "start_time": 2660.39,
                    "end_time": 2672.55
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right.",
                    "start_time": 2673.19,
                    "end_time": 2673.55
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "And then can join and then the full and then you and Aspreet and the full team can go through that and and come to a decision.",
                    "start_time": 2673.55,
                    "end_time": 2679.91
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Yeah sure it works for us.",
                    "start_time": 2680.23,
                    "end_time": 2682.55
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "We can join it at 2:30.",
                    "start_time": 2682.71,
                    "end_time": 2684.47
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "All right then I'm sharing the new meeting invite for 2:30pm IST.",
                    "start_time": 2688.79,
                    "end_time": 2692.63
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah, yeah right.",
                    "start_time": 2693.35,
                    "end_time": 2695.03
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "And apart from this we will try to provide you with the time estimations for the forecast module.",
                    "start_time": 2695.35,
                    "end_time": 2700.96
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah and then the scenario modeling.",
                    "start_time": 2701.92,
                    "end_time": 2703.76
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Do you how is that coming along module 3?",
                    "start_time": 2703.76,
                    "end_time": 2706.32
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "See module 3 is totally focused and.",
                    "start_time": 2706.64,
                    "end_time": 2710.72
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Because a lot of, because a lot of the calculations you're using in module 3 are derived from module 2 right?",
                    "start_time": 2715.2,
                    "end_time": 2720.48
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Yes, yes these are all overlapped or interlinked.",
                    "start_time": 2720.72,
                    "end_time": 2723.52
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "So that's why if we have to work upon the few forecast financials in the forecast module and then we can only check with the scenario modeling and once it is done then only we can finalize both of the modules as these are interlinked.",
                    "start_time": 2723.52,
                    "end_time": 2738
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "So we will provide you with the time estimations of both the modules for now because scenario modeling is done but for now the socket IO regarding which we need to discuss discuss with Ashpreet and once it is finalized then we can provide you with that handover of scenario modeling.",
                    "start_time": 2744.72,
                    "end_time": 2760.33
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay.",
                    "start_time": 2761.69,
                    "end_time": 2762.25
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Yeah.",
                    "start_time": 2762.57,
                    "end_time": 2762.93
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Okay.",
                    "start_time": 2762.93,
                    "end_time": 2763.25
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "And was there anything on the AI plan that you wanted to discuss or that with Raheel and that's with Raheel",
                    "start_time": 2763.25,
                    "end_time": 2769.73
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "and Akash they were I believe they had discussion with Ashbay related to the second approach rack based approach for the AI module and we haven't get any feedback that with which approach we need to proceeded further.",
                    "start_time": 2769.73,
                    "end_time": 2781.06
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "So I believe they will provide us an insight on which approach we have to proceed it.",
                    "start_time": 2781.54,
                    "end_time": 2787.22
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "If you have an idea then you can let me know because we are stuck in the AM audience.",
                    "start_time": 2787.54,
                    "end_time": 2791.38
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "No, I think our approach is.",
                    "start_time": 2796.339,
                    "end_time": 2797.86
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah, go ahead.",
                    "start_time": 2797.86,
                    "end_time": 2798.58
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Well I mean I recommend that we we still need a little bit of a discussion on our side and then we'll get back to you asap.",
                    "start_time": 2800.42,
                    "end_time": 2806.22
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Okay.",
                    "start_time": 2807.25,
                    "end_time": 2807.73
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Okay, no problem.",
                    "start_time": 2807.89,
                    "end_time": 2808.93
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Then you can have your discussion and then you can let us know Still I want to highlight it here that when one you inform us that with each approach we will need to proceed it further.",
                    "start_time": 2808.93,
                    "end_time": 2820.13
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "According to that, I'll provide you with the timeline for the AI module.",
                    "start_time": 2820.37,
                    "end_time": 2823.73
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Right.",
                    "start_time": 2825.73,
                    "end_time": 2826.13
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "So it all if any kind of changes in the architecture or whenever we get the clarifications just now, we have get clarification the forecast module.",
                    "start_time": 2828.45,
                    "end_time": 2838.21
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "So we will work on the forecast financials.",
                    "start_time": 2838.21,
                    "end_time": 2841.05
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "So according to that the deadlines would be changed.",
                    "start_time": 2841.13,
                    "end_time": 2844.81
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "That's why I'm just informing you just an insight for you to that once we get an approval on the approach for the AI module, then only we will start working on it.",
                    "start_time": 2845.05,
                    "end_time": 2855.45
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Yes.",
                    "start_time": 2858.49,
                    "end_time": 2858.99
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay, that's noted.",
                    "start_time": 2859.22,
                    "end_time": 2860.3
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "That's fine.",
                    "start_time": 2860.3,
                    "end_time": 2860.82
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Okay.",
                    "start_time": 2860.82,
                    "end_time": 2861.3
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "All right.",
                    "start_time": 2861.3,
                    "end_time": 2861.86
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "So let's connect it to 30 then.",
                    "start_time": 2862.1,
                    "end_time": 2863.78
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "All right, thanks.",
                    "start_time": 2864.98,
                    "end_time": 2865.78
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Okay, thank you.",
                    "start_time": 2866.1,
                    "end_time": 2866.98
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Bye.",
                    "start_time": 2869.62,
                    "end_time": 2870.18
                }
        ],
        "summary": {
                "keywords": [
                    "forecasting",
                    "cash flow",
                    "ONCA",
                    "financing activities",
                    "database codes",
                    "Socket.IO"
                ],
                "action_items": "\n**Project Manager SFS**\nProvide updated delivery timelines for forecast module after internal QA, security, and unit testing (39:02)\nShare Ashpreet’s architectural feedback documents and coordinate team to address Socket.IO implementation and feedback (40:20)\nOrganize follow-up meeting at 14:30 IST to discuss architectural feedback and finalize decisions with Ashpreet and team (44:40)\nProvide timeline estimations for both forecast and scenario modeling modules once Socket.IO discussion is resolved (45:06)\n\n**Bhavneet Mhajan**\nProvide missing forecast formulas for ONCA items and clarify formulas during the call (01:29)\nDocument and clarify classification codes used in cash flow forecasting formulas to ensure alignment with database fields (07:55)\nConfirm exclusion of accumulated depreciation from UI and balance sheet output (21:04)\nExplain financing activities cash flow breakdown and formula components clearly to team (24:01)\nGuide team to use forecast actual values in UI and variance column to show monthly changes (33:54)\nConfirm that forecast numbers for ONCA items can use prior year’s data as base (23:15)\nHighlight to team to follow existing indirect cash flow Excel workbook formulas for correct cash flow forecast calculations (37:57)\n\n**Rhythm Jalhotra**\nValidate and provide actual sub-account values for prepaid expenses and link to OCA changes (01:54)\nProvide clarity on codes used for change in earnings not attributed to retained income and forecast components (04:48)\nConfirm removal or resolution of “CE” code ambiguity and database mappings (10:05)\nConfirm fixed assets formula use with property and equipment only and accumulated depreciation exclusion (20:18)\nShare screenshots and data to clarify forecast vs. changes for short and long-term debts and other financing activities components (30:02)\n\n**Ngũmi Gituro**\nRecommend showing forecasted values in cash flow with variance column for changes to aid clarity (34:33)\nSuggest tracing database extracts for example months to clarify source of forecast inputs (14:38)\n\n**Neha**\nPresent analysis of Redis pub/sub versus double queue system for messaging; estimate two days to implement recommended Redis approach (42:40)\n",
                "overview": "- **Forecasting Formulas Clarified:** Team aligned on key forecasting sources for cash flow and balance sheet to reduce confusion.\n\n- **Investment Data Usage Confirmed:** ONCA will use 2025 forecasted numbers as placeholders for goodwill and investment property, simplifying calculations.\n\n- **Module Development Progress:** Only the forecasted financials page remains incomplete; timelines will be reviewed post internal QA.\n\n- **AI Module on Hold:** Development awaits strategic decisions on approach and architecture, impacting resource allocation and timelines.\n\n- **Improved Communication Practices:** Direct discussions with stakeholders enhance decision-making speed and transparency, reducing previous delays.",
                "outline": "null"
        }
    }

    run_pipeline(transcript, "01KM2DD6MXGSZ4F1QW0BNJE16N")

    