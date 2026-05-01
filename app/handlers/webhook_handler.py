import time
from app.config import Config, CONSTANT_TRANSCRIPT


from app.services.transcript.metadata import build_meeting_metadata
from app.services.transcript.chunking import create_chunks
from app.services.transcript.normalize import normalize_transcript
from app.clients.fireflies_client import fetch_transcript


def wait_for_summary(transcript_id):
    """Wait for transcript summary to be available"""
    for _ in range(6):
        data = fetch_transcript(transcript_id)
        
        if not data or "data" not in data:
            print("Failed to fetch transcript data")
            time.sleep(5)
            continue

        transcript = data.get("data", {}).get("transcript")

        if not transcript:
            print("No transcript data found")
            time.sleep(5)
            continue

        summary = transcript.get("summary")

        if summary and summary.get("overview"):
            return summary

        time.sleep(5)

    return None


async def handle_fireflies_webhook(payload):
    """Handle incoming Fireflies webhook with full processing pipeline"""
    print("Webhook received") 
    
    # Development mode: Use constant transcript for fast testing
    if Config.DEVELOPMENT_MODE:
        print("DEVELOPMENT MODE: Using constant transcript")
        transcript_data = CONSTANT_TRANSCRIPT
        
        # Normalize the transcript data
        normalized_data = normalize_transcript(transcript_data)
        print(f"Normalized transcript (dev mode): meeting_id={normalized_data['meeting_id']}, sentences={len(normalized_data['sentences'])}")
        
        # Build meeting metadata
        meeting_metadata = build_meeting_metadata(normalized_data)
        print(f"Meeting metadata (dev mode): meeting_id={meeting_metadata['meeting_id']}")
        
        # Create chunks
        chunks = create_chunks(normalized_data["sentences"], meeting_metadata)
        print(f"Chunks (dev mode): Created {len(chunks)} chunks")
        return
    
    # Production mode: Normal webhook processing
    # Step 0: Wait for transcript ID to be available
    transcript_id = None
    for attempt in range(3):
        transcript_id = (
            payload.get("transcript_id")
            or payload.get("meetingId")
            or payload.get("meeting_id")   
            or payload.get("data", {}).get("transcript_id")
        )
        
        if transcript_id:
            print("Transcript ID found:", transcript_id)
            break
        else:
            print(f"Transcript ID not available yet (attempt {attempt + 1}/3), waiting 10 seconds...")
            time.sleep(10)
    
    if not transcript_id:
        print("No transcript ID found after retries")
        return

    print("Processing transcript:", transcript_id)

    # Step 1: Fetch transcript with retry for early webhooks
    transcript_data = None
    for attempt in range(3):
        transcript_data = fetch_transcript(transcript_id)
        
        if transcript_data and "data" in transcript_data and transcript_data["data"].get("transcript"):
            print("Transcript fetched successfully")
            break
        else:
            print(f"Transcript not ready yet (attempt {attempt + 1}/3), waiting 10 seconds...")
            time.sleep(10)
    
    if not transcript_data or "data" not in transcript_data or not transcript_data["data"].get("transcript"):
        print("Failed to fetch transcript after retries")
        return

    # Step 2: Wait for summary
    print("Waiting for summary...")
    summary = wait_for_summary(transcript_id)
    
    if summary:
        print("Summary retrieved successfully")

        if "data" in transcript_data and "transcript" in transcript_data["data"]:
            transcript_data["data"]["transcript"]["summary"] = summary
        else:
            print("Warning: Could not update summary in transcript data structure")
    else:
        print("Summary not available after retries")

    # Step 3: Normalize and process
    normalized_data = normalize_transcript(transcript_data)
    print(f"Normalized transcript: meeting_id={normalized_data['meeting_id']}, sentences={len(normalized_data['sentences'])}")

    # Build meeting metadata
    meeting_metadata = build_meeting_metadata(normalized_data)
    print(f"Meeting metadata: meeting_id={meeting_metadata['meeting_id']}")

    # Create chunks
    chunks = create_chunks(normalized_data["sentences"], meeting_metadata)
    print(f"Chunks: Created {len(chunks)} chunks")
    
    # TODO: Store chunks to database
    return chunks