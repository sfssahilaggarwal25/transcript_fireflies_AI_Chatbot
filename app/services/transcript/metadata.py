from datetime import datetime

def build_meeting_metadata(transcript):
    return {
        "meeting_id": transcript["meeting_id"],
        "title": transcript["title"],
        "date": transcript.get("date") or datetime.now().strftime("%Y-%m-%d"),
    }