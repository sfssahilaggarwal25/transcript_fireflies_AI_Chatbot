from app.core.storage.db import get_raw_collection

col = get_raw_collection()
results = col.get(include=["metadatas"])
metas = results["metadatas"]

non_sum = [m for m in metas if not m.get("is_meeting_summary")]

meetings = {}
for m in non_sum:
    mid = m.get("meeting_id")
    if mid not in meetings:
        meetings[mid] = {
            "title": m.get("meeting_title"),
            "date": m.get("meeting_date"),
            "chunks": 0,
            "speakers": set(),
            "decisions": 0,
            "commitments": 0,
            "questions": 0,
        }
    meetings[mid]["chunks"] += 1
    meetings[mid]["speakers"].add(m.get("speaker_name", ""))
    if m.get("contains_decision"):   meetings[mid]["decisions"] += 1
    if m.get("contains_commitment"): meetings[mid]["commitments"] += 1
    if m.get("contains_question"):   meetings[mid]["questions"] += 1

for mid, info in sorted(meetings.items(), key=lambda x: x[1]["date"]):
    print("=" * 55)
    print("Meeting :", info["title"])
    print("Date    :", info["date"])
    print("ID      :", mid)
    print("Chunks  :", info["chunks"])
    print("Speakers:", sorted(info["speakers"]))
    print("Signals : decisions=%d  commitments=%d  questions=%d" % (
        info["decisions"], info["commitments"], info["questions"]))

print()

# Check overlapping topics between meetings — look for shared keywords
print("=" * 55)
print("SHARED TOPICS CHECK")
print("=" * 55)

shared_keywords = [
    "AI module", "forecast", "scenario modeling", "socket", "timeline",
    "module", "approach", "stress test", "agent", "architecture",
]

from app.core.retrieval.retriever import retrieve_documents

for keyword in shared_keywords:
    docs = retrieve_documents(keyword, "proj_nolocode_001", k=6)
    hit_meetings = set(d.metadata.get("meeting_title", "") for d in docs)
    if len(hit_meetings) > 1:
        print("SPANS BOTH  :", keyword, "->", sorted(hit_meetings))
    else:
        title = list(hit_meetings)[0] if hit_meetings else "none"
        short = title.split()[0] if title != "none" else "none"
        print("Single only :", keyword, "->", short + "...")
