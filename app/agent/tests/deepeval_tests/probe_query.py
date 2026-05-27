"""
probe_query.py — Run ONE query against the production agent and print everything
you need to write an accurate expected_output for a DeepEval Golden.

HOW TO USE
----------
# Run a single query (prints answer + sources + tool calls + derivation hints):
python -m app.agent.tests.deepeval_tests.probe_query "Were any commitments made in the previous meeting?"

# Run with explicit project ID:
python -m app.agent.tests.deepeval_tests.probe_query "How many meetings?" --project-id proj_nolocode_001

OUTPUT FORMAT
-------------
The script prints four sections:

  [ANSWER]          ← the exact text the agent returned
  [TOOL CALLS]      ← which tools the agent called and with what args
  [SOURCES]         ← speaker name + meeting title + date + timestamp for every chunk cited
  [DERIVATION HINTS]← extracted facts you can directly copy into expected_output sentences

This output gives you everything you need to:
  1. Verify the answer is factually correct
  2. Identify the concrete checkable facts
  3. Write the expected_output sentences
"""

import argparse
import re
import sys
from pathlib import Path

# Project root on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

from app.agent.service import answer_query


# ── Hint extractor ────────────────────────────────────────────────────────────

def _extract_hints(answer: str, sources: list[dict], tool_calls: list[dict]) -> list[str]:
    """
    Pull concrete facts out of the answer and sources.
    Each hint is a candidate sentence for expected_output.
    """
    hints = []

    # ── Dates found in answer ─────────────────────────────────────────────────
    dates = sorted(set(re.findall(r"\b\d{4}-\d{2}-\d{2}\b", answer)))
    if dates:
        hints.append(f"DATES IN ANSWER: {', '.join(dates)}")
        hints.append(f"  → expected_output sentence: \"The date {dates[0]} appears in the answer.\"")
        if len(dates) > 1:
            hints.append(f"  → or: \"The dates {dates[0]} and {dates[-1]} are both mentioned.\"")

    # ── Timestamps found in answer (MM:SS) ────────────────────────────────────
    timestamps = re.findall(r"\b\d{1,2}:\d{2}\b", answer)
    if timestamps:
        hints.append(f"\nTIMESTAMPS IN ANSWER: {', '.join(timestamps[:5])}")
        hints.append(f"  → expected_output sentence: \"At least one timestamp in MM:SS format is present.\"")
    else:
        hints.append(f"\nNO TIMESTAMPS FOUND — expected_output sentence: \"At least one timestamp in MM:SS format appears in the answer.\" will FAIL → fix the agent first")

    # ── Speaker names found in sources ───────────────────────────────────────
    speaker_names = sorted(set(
        s["speaker_name"] for s in sources
        if s["speaker_name"] not in ("Meeting Summary", "Unknown")
    ))
    if speaker_names:
        hints.append(f"\nSPEAKER NAMES IN SOURCES: {', '.join(speaker_names)}")
        for name in speaker_names[:3]:
            in_answer = name.lower() in answer.lower() or name.split()[0].lower() in answer.lower()
            status = "✓ appears in answer" if in_answer else "✗ NOT in answer — check attribution"
            hints.append(f"  → {name}: {status}")
        hints.append(f"  → expected_output sentence: \"The name {speaker_names[0]} appears in the answer.\"")

    # ── Meetings referenced in sources ────────────────────────────────────────
    meeting_dates = sorted(set(s["meeting_date"] for s in sources if s["meeting_date"]))
    if meeting_dates:
        hints.append(f"\nMEETING DATES IN SOURCES: {', '.join(meeting_dates)}")
        if len(meeting_dates) == 1:
            hints.append(f"  → Scoped to ONE meeting: {meeting_dates[0]}")
            hints.append(f"  → expected_output sentence: \"The answer is scoped to the meeting on {meeting_dates[0]}.\"")
        else:
            hints.append(f"  → Spans {len(meeting_dates)} meetings: {meeting_dates[0]} to {meeting_dates[-1]}")
            hints.append(f"  → expected_output sentence: \"Content from {len(meeting_dates)} meetings appears in the answer.\"")

    # ── Tools called ──────────────────────────────────────────────────────────
    tool_names = [tc["tool"] for tc in tool_calls]
    if tool_names:
        hints.append(f"\nTOOLS CALLED: {' → '.join(tool_names)}")

    # ── Yes/No detection ──────────────────────────────────────────────────────
    first_word = answer.strip().split()[0].lower().rstrip(".,;:") if answer.strip() else ""
    if first_word in ("yes", "no"):
        hints.append(f"\nANSWER STARTS WITH: '{first_word.upper()}'")
        hints.append(f"  → expected_output sentence: \"The answer begins with {first_word.capitalize()}.\"")

    # ── Numbers found in answer ───────────────────────────────────────────────
    counts = re.findall(r"\b(?:about |at least |approximately )?(\d+)\b", answer)
    if counts:
        hints.append(f"\nNUMBERS IN ANSWER: {', '.join(counts[:8])}")

    return hints


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Probe a single query and print derivation hints for expected_output"
    )
    parser.add_argument("query", help="The PM question to run")
    parser.add_argument(
        "--project-id", default="proj_nolocode_001",
        help="Project ID (default: proj_nolocode_001)"
    )
    args = parser.parse_args()

    print(f"\n{'═'*65}")
    print(f"  QUERY: {args.query}")
    print(f"  PROJECT: {args.project_id}")
    print(f"{'═'*65}\n")

    result = answer_query(args.query, args.project_id)

    # ── SECTION 1: Answer ─────────────────────────────────────────────────────
    print("━"*65)
    print("  [ANSWER]")
    print("━"*65)
    print(result["answer"])

    # ── SECTION 2: Tool calls ─────────────────────────────────────────────────
    print("\n" + "━"*65)
    print("  [TOOL CALLS]")
    print("━"*65)
    if result["tool_calls"]:
        for i, tc in enumerate(result["tool_calls"], 1):
            print(f"  {i}. {tc['tool']}")
            for k, v in tc["args"].items():
                print(f"       {k}: {v!r}")
    else:
        print("  (no tool calls recorded)")

    # ── SECTION 3: Sources ────────────────────────────────────────────────────
    print("\n" + "━"*65)
    print(f"  [SOURCES]  ({len(result['sources'])} chunks retrieved)")
    print("━"*65)
    if result["sources"]:
        for s in result["sources"]:
            ts = f" ({s['timestamp']})" if s["timestamp"] else ""
            print(f"  [{s['chunk_num']}] {s['speaker_name']}{ts}")
            print(f"       {s['meeting_title']} — {s['meeting_date']}")
            if s["content_preview"]:
                preview = s["content_preview"][:120].replace("\n", " ")
                print(f"       \"{preview}…\"")
    else:
        print("  (no sources — metadata-only answer)")

    # ── SECTION 4: Derivation hints ───────────────────────────────────────────
    print("\n" + "━"*65)
    print("  [DERIVATION HINTS — copy these into expected_output]")
    print("━"*65)
    hints = _extract_hints(result["answer"], result["sources"], result["tool_calls"])
    for h in hints:
        print(f"  {h}")

    print(f"\n{'═'*65}\n")


if __name__ == "__main__":
    main()
