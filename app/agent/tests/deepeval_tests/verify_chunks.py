"""
verify_chunks.py — Independent ChromaDB inspector for ground-truth verification.

PURPOSE
-------
When you write expected_output for a Golden, you must verify TWO things
that probe_query.py CANNOT tell you (because it goes through the agent):

  1. RECALL  — Does ChromaDB have MORE relevant chunks than the agent retrieved?
               Agent missed chunks → expected_output encodes an incomplete answer.

  2. PRECISION — Are the retrieved chunks actually about the topic you asked?
               Agent retrieved wrong chunks → expected_output encodes hallucination.

This script bypasses the agent entirely. It queries ChromaDB directly — the
same data store the agent reads from — and shows you what ACTUALLY EXISTS for
a given meeting, speaker, signal, or topic.

COMMANDS
--------

# What chunks exist for a signal in a specific meeting?
# → Use this to check RECALL: did the agent get ALL of them?
python -m app.agent.tests.deepeval_tests.verify_chunks signal \
    --signal commitment \
    --meeting-date 2026-05-07

# What does a specific speaker say in a meeting?
# → Use this before writing expected_output for speaker-attribution queries.
python -m app.agent.tests.deepeval_tests.verify_chunks speaker \
    --name "Rhythm jalhotra" \
    --meeting-date 2026-05-07

# Search raw ChromaDB by keyword (no semantic ranking — pure text match).
# → Use this to find ground-truth chunks for a topic without agent bias.
python -m app.agent.tests.deepeval_tests.verify_chunks keyword \
    --keyword "OCA" \
    --keyword "cash flow"

# Compare: what the agent retrieved vs what ChromaDB has.
# → The most useful command — shows recall % directly.
python -m app.agent.tests.deepeval_tests.verify_chunks compare \
    --signal commitment \
    --meeting-date 2026-05-07 \
    --agent-count 44

# List all meetings with their chunk counts and signal counts.
# → Use this to verify facts before writing project-level Goldens.
python -m app.agent.tests.deepeval_tests.verify_chunks meetings

# List all speakers with their chunk counts, optionally scoped to one meeting.
python -m app.agent.tests.deepeval_tests.verify_chunks speakers \
    --meeting-date 2026-05-07
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

from app.core.storage.db import get_raw_collection

_PROJECT_ID = "proj_nolocode_001"

_SIGNAL_MAP = {
    "decision":       "contains_decision",
    "commitment":     "contains_commitment",
    "question":       "contains_question",
    "open_issue":     "contains_open_issue",
    "document_share": "contains_document_share",
}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _fmt_ts(sec) -> str:
    if sec is None:
        return "?:??"
    total = int(sec)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def _get_all_meta(project_id: str) -> list[dict]:
    col = get_raw_collection()
    results = col.get(
        where={"project_id": {"$eq": project_id}},
        include=["metadatas", "documents"],
    )
    return list(zip(
        results.get("metadatas", []),
        results.get("documents", []),
    ))


def _get_all_meta_only(project_id: str) -> list[dict]:
    col = get_raw_collection()
    results = col.get(
        where={"project_id": {"$eq": project_id}},
        include=["metadatas"],
    )
    return results.get("metadatas", [])


# ── Command: signal ────────────────────────────────────────────────────────────

def cmd_signal(args):
    """
    Show every chunk that has a given signal flag, optionally scoped to one meeting.

    This is your GROUND TRUTH for recall verification.
    Compare the total shown here with how many chunks your agent retrieved.
    """
    signal = args.signal
    if signal not in _SIGNAL_MAP:
        print(f"[ERROR] Unknown signal '{signal}'. Choose from: {list(_SIGNAL_MAP.keys())}")
        sys.exit(1)

    db_field = _SIGNAL_MAP[signal]
    col = get_raw_collection()

    where_clauses = [
        {"project_id":    {"$eq": args.project_id}},
        {db_field:        {"$eq": True}},
        {"is_meeting_summary": {"$ne": True}},
    ]
    if args.meeting_date:
        where_clauses.append({"meeting_date": {"$eq": args.meeting_date}})

    results = col.get(
        where={"$and": where_clauses},
        include=["metadatas", "documents"],
    )

    metas = results.get("metadatas", [])
    docs  = results.get("documents", [])

    scope_label = f" in meeting {args.meeting_date}" if args.meeting_date else " across ALL meetings"

    print(f"\n{'═'*65}")
    print(f"  GROUND TRUTH — '{signal}' chunks{scope_label}")
    print(f"  Total found in ChromaDB: {len(metas)}")
    print(f"{'═'*65}")
    print()
    print("  ┌─ This is what ACTUALLY EXISTS in your database.")
    print("  │  Compare this count to what your agent retrieved.")
    print("  │  If agent count < ChromaDB count → agent has a RECALL GAP.")
    print()

    # Sort chronologically
    pairs = sorted(zip(metas, docs), key=lambda p: p[0].get("start_time", 0))

    for i, (meta, doc) in enumerate(pairs, 1):
        ts      = _fmt_ts(meta.get("start_time"))
        speaker = meta.get("speaker_name", "Unknown")
        meeting = meta.get("meeting_title", "Unknown")
        date    = meta.get("meeting_date", "")
        text    = doc.strip()

        # Flag likely false positives — short or vague chunks
        flag = ""
        word_count = len(text.split())
        if word_count < 8:
            flag = "  ⚠️  SHORT CHUNK — may be a false positive"
        elif not any(kw in text.lower() for kw in _get_signal_keywords(signal)):
            flag = "  ⚠️  NO SIGNAL KEYWORD — possible false positive"

        print(f"  [{i:03d}] {speaker} ({ts})  —  {meeting} ({date}){flag}")
        print(f"         \"{text}{'…' if len(doc.strip()) > 200 else ''}\"")
        print()

    print(f"{'─'*65}")
    print(f"  TOTAL: {len(metas)} chunks with signal='{signal}'{scope_label}")
    print()

    # Precision hint: flag potential false positives
    fp_count = sum(
        1 for meta, doc in pairs
        if len(doc.split()) < 8 or not any(
            kw in doc.lower() for kw in _get_signal_keywords(signal)
        )
    )
    if fp_count > 0:
        print(f"  ⚠️  {fp_count} chunk(s) flagged as potential false positives")
        print(f"     (short text or no signal keyword found)")
        print(f"     → These inflated the count. Read them above (⚠️ markers).")

    print()
    print("  HOW TO USE THIS FOR expected_output:")
    print(f"  If agent retrieved N chunks, ChromaDB has {len(metas)} total.")
    if args.agent_count:
        agent_n = int(args.agent_count)
        true_n  = len(metas)
        if agent_n < true_n:
            gap = true_n - agent_n
            recall_pct = round(100 * agent_n / true_n) if true_n else 0
            print(f"  RECALL GAP: agent got {agent_n}, DB has {true_n} → missed ~{gap} chunks ({recall_pct}% recall)")
            print(f"  → Do NOT write expected_output saying 'all X commitments listed'")
            print(f"  → Write: 'At least N specific {signal}s are listed' (conservative)")
        elif agent_n == true_n:
            print(f"  ✓ PERFECT RECALL: agent retrieved all {true_n} chunks")
            print(f"  → Safe to write: 'All {true_n} {signal}s from this meeting are listed'")
        else:
            print(f"  ⚠️  Agent count ({agent_n}) > DB count ({true_n}) — check for duplicate chunks")
    else:
        print(f"  → Pass --agent-count N to see the recall gap calculation")

    print(f"{'═'*65}\n")


def _get_signal_keywords(signal: str) -> list[str]:
    """Return keywords that should appear in a genuine signal chunk."""
    return {
        "commitment":     ["will", "i'll", "going to", "commit", "responsible", "take", "action", "follow"],
        "decision":       ["decided", "decision", "agreed", "confirmed", "approved", "finalized",
                           "going with", "stick with", "let's go with", "move forward with",
                           "chosen", "selected"],
        "question":       ["?", "how", "why", "what", "when", "where", "could you", "can you"],
        "open_issue":     ["issue", "problem", "error", "bug", "not working", "concern", "blocker", "risk"],
        "document_share": ["http", "www", "link", "doc", "sheet", "file", "folder", "drive", "share"],
    }.get(signal, [])


# ── Command: speaker ───────────────────────────────────────────────────────────

def cmd_speaker(args):
    """
    Show every chunk from a specific speaker, optionally scoped to one meeting.

    Use this BEFORE writing expected_output for speaker-attribution Goldens.
    Tells you:
    - The exact stored speaker name (for your expected_output sentence)
    - What they actually said (ground truth for content checks)
    - Whether they spoke in the meeting you're testing
    """
    if not args.name:
        print("[ERROR] --name is required for 'speaker' command")
        sys.exit(1)

    col = get_raw_collection()

    # First: find the exact stored name using partial match
    all_metas = _get_all_meta_only(args.project_id)
    all_names = set(
        m.get("speaker_name") for m in all_metas
        if m.get("speaker_name") and not m.get("is_meeting_summary")
    )

    partial_lower = args.name.lower()
    matches = [n for n in all_names if partial_lower in n.lower()]

    if not matches:
        print(f"\n[ERROR] No speaker matching '{args.name}' found in project.")
        print(f"  Known speakers: {sorted(all_names)}")
        sys.exit(1)

    if len(matches) > 1:
        print(f"\n[WARN] Multiple speakers match '{args.name}':")
        for m in matches:
            print(f"  - '{m}'")
        print(f"  Using '{matches[0]}'. Pass a more specific name if wrong.")

    exact_name = matches[0]

    where_clauses = [
        {"project_id":    {"$eq": args.project_id}},
        {"speaker_name":  {"$eq": exact_name}},
        {"is_meeting_summary": {"$ne": True}},
    ]
    if args.meeting_date:
        where_clauses.append({"meeting_date": {"$eq": args.meeting_date}})

    results = col.get(
        where={"$and": where_clauses},
        include=["metadatas", "documents"],
    )

    metas = results.get("metadatas", [])
    docs  = results.get("documents", [])
    pairs = sorted(zip(metas, docs), key=lambda p: p[0].get("start_time", 0))

    scope_label = f" in {args.meeting_date}" if args.meeting_date else " across ALL meetings"

    print(f"\n{'═'*65}")
    print(f"  GROUND TRUTH — Speaker: '{exact_name}'{scope_label}")
    print(f"  Stored name (exact): '{exact_name}'  ← use this in expected_output")
    print(f"  Total chunks: {len(metas)}")
    print(f"{'═'*65}\n")

    for i, (meta, doc) in enumerate(pairs, 1):
        ts      = _fmt_ts(meta.get("start_time"))
        meeting = meta.get("meeting_title", "Unknown")
        date    = meta.get("meeting_date", "")
        signals = [s for s, f in _SIGNAL_MAP.items() if meta.get(f)]
        sig_str = f"  [{', '.join(signals)}]" if signals else ""
        print(f"  [{i:03d}] ({ts})  —  {meeting} ({date}){sig_str}")
        print(f"         \"{doc.strip()[:200]}{'…' if len(doc.strip()) > 200 else ''}\"")
        print()

    print(f"{'─'*65}")
    print(f"  TOTAL: {len(metas)} chunks by '{exact_name}'{scope_label}")
    print()
    print(f"  HOW TO USE FOR expected_output:")
    print(f"  Use the EXACT stored name: \"{exact_name}\"")
    print(f"  → Sentence: \"The name {exact_name} appears in the answer.\"")
    if metas:
        dates_seen = sorted(set(m.get("meeting_date","") for m in metas))
        print(f"  → Meetings where they appear: {dates_seen}")
    print(f"{'═'*65}\n")


# ── Command: keyword ───────────────────────────────────────────────────────────

def cmd_keyword(args):
    """
    Find all chunks containing specific keywords — raw text scan, no agent involved.

    Use this for topics where you don't know the signal flag.
    The results show you WHAT EXISTS in ChromaDB for a topic before writing expected_output.
    """
    if not args.keyword:
        print("[ERROR] At least one --keyword is required")
        sys.exit(1)

    col = get_raw_collection()
    results = col.get(
        where={"project_id": {"$eq": args.project_id}},
        include=["metadatas", "documents"],
    )

    metas = results.get("metadatas", [])
    docs  = results.get("documents", [])

    # Filter: all keywords must appear in chunk text (case-insensitive)
    keywords_lower = [kw.lower() for kw in args.keyword]
    matched = [
        (m, d) for m, d in zip(metas, docs)
        if not m.get("is_meeting_summary")
        and all(kw in d.lower() for kw in keywords_lower)
    ]
    matched.sort(key=lambda p: (p[0].get("meeting_date",""), p[0].get("start_time", 0)))

    kw_label = " AND ".join(f'"{kw}"' for kw in args.keyword)
    print(f"\n{'═'*65}")
    print(f"  GROUND TRUTH — Keyword search: {kw_label}")
    print(f"  Chunks found in ChromaDB: {len(matched)}")
    print(f"{'═'*65}\n")

    if not matched:
        print("  ✗ ZERO chunks contain these keywords.")
        print("  → This explains why the agent returns 0 results for this topic.")
        print("  → The topic may use different terminology in the transcripts.")
        print()
        # Show adjacent terms — chunks that contain at least one keyword
        partial = [
            (m, d) for m, d in zip(metas, docs)
            if not m.get("is_meeting_summary")
            and any(kw in d.lower() for kw in keywords_lower)
        ]
        if partial:
            print(f"  PARTIAL MATCHES (chunks with at least one keyword):")
            for m, d in partial[:5]:
                ts  = _fmt_ts(m.get("start_time"))
                spk = m.get("speaker_name","?")
                dt  = m.get("meeting_date","")
                print(f"    ({ts}) {spk} — {dt}")
                print(f"    \"{d.strip()[:150]}…\"")
                print()
    else:
        for i, (meta, doc) in enumerate(matched, 1):
            ts      = _fmt_ts(meta.get("start_time"))
            speaker = meta.get("speaker_name","Unknown")
            meeting = meta.get("meeting_title","Unknown")
            date    = meta.get("meeting_date","")
            signals = [s for s, f in _SIGNAL_MAP.items() if meta.get(f)]
            sig_str = f"  [{', '.join(signals)}]" if signals else ""
            print(f"  [{i:03d}] {speaker} ({ts})  —  {meeting} ({date}){sig_str}")
            print(f"         \"{doc.strip()[:200]}{'…' if len(doc.strip()) > 200 else ''}\"")
            print()

    print(f"{'─'*65}")
    print(f"  TOTAL: {len(matched)} chunks contain {kw_label}")
    print(f"{'═'*65}\n")


# ── Command: compare ───────────────────────────────────────────────────────────

def cmd_compare(args):
    """
    Compare what ChromaDB has vs what the agent retrieved.
    Shows recall % directly.
    """
    print()
    args.agent_count = args.agent_count  # already set
    cmd_signal(args)


# ── Command: meetings ──────────────────────────────────────────────────────────

def cmd_meetings(args):
    """
    List every meeting with total chunk count and per-signal counts.
    Use this to verify facts for project-level Goldens.
    """
    col = get_raw_collection()
    results = col.get(
        where={"project_id": {"$eq": args.project_id}},
        include=["metadatas"],
    )
    metas = results.get("metadatas", [])

    meetings: dict[str, dict] = {}
    for m in metas:
        mid = m.get("meeting_id")
        if not mid or m.get("is_meeting_summary"):
            continue
        if mid not in meetings:
            meetings[mid] = {
                "title":   m.get("meeting_title", "?"),
                "date":    m.get("meeting_date", "?"),
                "number":  m.get("meeting_number", "?"),
                "total":   0,
                **{s: 0 for s in _SIGNAL_MAP},
            }
        meetings[mid]["total"] += 1
        for sig, field in _SIGNAL_MAP.items():
            if m.get(field):
                meetings[mid][sig] += 1

    ordered = sorted(meetings.values(), key=lambda x: x["date"])

    print(f"\n{'═'*75}")
    print(f"  GROUND TRUTH — All Meetings in project '{args.project_id}'")
    print(f"  Total meetings: {len(ordered)}")
    print(f"{'═'*75}")
    print(f"  {'#':<4} {'Date':<12} {'Title':<30} {'Chunks':>6}  commit  dec  quest  issue  doc")
    print(f"  {'─'*4} {'─'*12} {'─'*30} {'─'*6}  {'─'*6}  {'─'*3}  {'─'*5}  {'─'*5}  {'─'*3}")
    for m in ordered:
        print(
            f"  {str(m['number']):<4} {m['date']:<12} {m['title'][:30]:<30} "
            f"{m['total']:>6}  "
            f"{m['commitment']:>6}  {m['decision']:>3}  "
            f"{m['question']:>5}  {m['open_issue']:>5}  {m['document_share']:>3}"
        )
    print()
    print(f"  HOW TO USE FOR expected_output:")
    print(f"  Copy the exact date, chunk count, and signal counts into your")
    print(f"  expected_output sentences so they encode REAL facts from the DB.")
    print(f"{'═'*75}\n")


# ── Command: speakers ──────────────────────────────────────────────────────────

def cmd_speakers(args):
    """
    List all speakers with exact stored names and chunk counts.
    Use this to verify speaker names BEFORE writing expected_output.
    """
    col = get_raw_collection()

    where_clauses: list[dict] = [
        {"project_id": {"$eq": args.project_id}},
        {"is_meeting_summary": {"$ne": True}},
    ]
    if args.meeting_date:
        where_clauses.append({"meeting_date": {"$eq": args.meeting_date}})

    results = col.get(
        where={"$and": where_clauses},
        include=["metadatas"],
    )
    metas = results.get("metadatas", [])

    speakers: dict[str, dict] = {}
    for m in metas:
        name = m.get("speaker_name")
        if not name:
            continue
        if name not in speakers:
            speakers[name] = {"role": m.get("speaker_role","?"), "count": 0, "meetings": set()}
        speakers[name]["count"] += 1
        speakers[name]["meetings"].add(m.get("meeting_date","?"))

    scope_label = f" in meeting {args.meeting_date}" if args.meeting_date else " across all meetings"

    print(f"\n{'═'*65}")
    print(f"  GROUND TRUTH — Speakers{scope_label}")
    print(f"  (These are the EXACT stored names — use verbatim in expected_output)")
    print(f"{'═'*65}\n")

    for name, info in sorted(speakers.items(), key=lambda x: x[1]["count"], reverse=True):
        mtg_list = sorted(info["meetings"])
        print(f"  \"{name}\"  [{info['role']}]  —  {info['count']} chunks  |  meetings: {mtg_list}")

    print(f"\n  Total speakers: {len(speakers)}")
    print()
    print(f"  HOW TO USE FOR expected_output:")
    print(f"  Use the EXACT name string above (with quotes shown) in sentences like:")
    for name in list(speakers.keys())[:2]:
        print(f"  → \"The name {name} appears in the answer.\"")
    print(f"{'═'*65}\n")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Verify ChromaDB ground truth for expected_output derivation"
    )
    parser.add_argument("--project-id", default=_PROJECT_ID)
    sub = parser.add_subparsers(dest="command", required=True)

    # signal
    p_signal = sub.add_parser("signal", help="Show all chunks with a given signal flag")
    p_signal.add_argument("--signal", required=True, choices=list(_SIGNAL_MAP.keys()))
    p_signal.add_argument("--meeting-date", help="e.g. 2026-05-07")
    p_signal.add_argument("--agent-count", type=int, help="How many chunks your agent retrieved")

    # speaker
    p_speaker = sub.add_parser("speaker", help="Show all chunks from a speaker")
    p_speaker.add_argument("--name", required=True, help="Partial or full speaker name")
    p_speaker.add_argument("--meeting-date")

    # keyword
    p_kw = sub.add_parser("keyword", help="Find chunks containing keywords (raw text scan)")
    p_kw.add_argument("--keyword", action="append", required=True,
                      help="Keyword to search for (repeat for multiple, all must match)")

    # compare
    p_cmp = sub.add_parser("compare", help="Compare agent retrieval vs ChromaDB ground truth")
    p_cmp.add_argument("--signal", required=True, choices=list(_SIGNAL_MAP.keys()))
    p_cmp.add_argument("--meeting-date")
    p_cmp.add_argument("--agent-count", type=int, required=True,
                       help="How many chunks the agent retrieved for this query")

    # meetings
    sub.add_parser("meetings", help="List all meetings with chunk and signal counts")

    # speakers
    p_spk = sub.add_parser("speakers", help="List all speakers with exact stored names")
    p_spk.add_argument("--meeting-date")

    args = parser.parse_args()

    dispatch = {
        "signal":   cmd_signal,
        "speaker":  cmd_speaker,
        "keyword":  cmd_keyword,
        "compare":  cmd_compare,
        "meetings": cmd_meetings,
        "speakers": cmd_speakers,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()