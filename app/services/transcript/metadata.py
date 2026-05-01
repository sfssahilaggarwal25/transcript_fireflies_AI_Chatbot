from datetime import datetime

def build_meeting_metadata(transcript):
    return {
        "meeting_id": transcript["meeting_id"],
        "title": transcript["title"],
        "date": datetime.now().strftime("%Y-%m-%d")  # or real meeting date
    }