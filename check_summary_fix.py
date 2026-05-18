from app.services.answer_service import answer_question

cases = [
    ("what was discussed on 9th of May. Summarize it.", "approx date match"),
    ("Summarize the meeting on June 3rd.", "no match at all"),
    ("Give me a summary of the project.", "no date — return all"),
]

for q, label in cases:
    try:
        r = answer_question(q, "proj_nolocode_001")
        print(f"[{label}]")
        print("  notice :", r.get("notice"))
        src = [(s["speaker_name"], s["meeting_date"], s.get("is_summary")) for s in r["sources"]]
        print("  sources:", src)
        print("  answer :", r["answer"][:90].replace("\n", " "))
        print()
    except Exception as e:
        print(f"[{label}] ERROR:", e)
