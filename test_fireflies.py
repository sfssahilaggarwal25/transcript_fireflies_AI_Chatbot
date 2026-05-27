#!/usr/bin/env python3
"""
Test script to verify all fireflies functions work correctly
"""

import os
import sys
import asyncio
import json
from app.core.transcript.normalize import normalize_transcript, group_by_speaker
from app.core.transcript.metadata import build_meeting_metadata
from app.handlers.webhook_handler import handle_fireflies_webhook
from app.config import CONSTANT_TRANSCRIPT

def test_normalize_transcript():
    """Test normalize_transcript function"""
    # print("=== Testing normalize_transcript ===")
    
    # Test with constant transcript
    result = normalize_transcript(CONSTANT_TRANSCRIPT)
    
    # Verify structure
    assert "meeting_id" in result
    assert "title" in result
    assert "sentences" in result
    assert "summary" in result
    assert result["meeting_id"] is not None
    assert result["title"] is not None
    assert len(result["sentences"]) > 0
    
    # print(f"✅ Meeting ID: {result['meeting_id']}")
    # print(f"✅ Title: {result['title']}")
    # print(f"✅ Sentences: {len(result['sentences'])}")
    # print("✅ normalize_transcript working correctly\n")

def test_build_meeting_metadata():
    """Test build_meeting_metadata function"""
    print("=== Testing build_meeting_metadata ===")
    
    # Use normalized data from constant transcript
    normalized_data = normalize_transcript(CONSTANT_TRANSCRIPT)
    result = build_meeting_metadata(normalized_data)
    # print(f"✅ build_meeting_metadata result: {result}")
    
    # Verify structure
    assert "meeting_id" in result
    assert "title" in result
    assert "date" in result
    assert result["meeting_id"] == normalized_data["meeting_id"]
    assert result["title"] == normalized_data["title"]
    assert result["date"] is not None
    
    # print("✅ build_meeting_metadata working correctly\n")

def test_create_chunks():
    """Test create_chunks function"""
    print("=== Testing create_chunks ===")
    
    # Use dynamic data from constant transcript
    normalized_data = normalize_transcript(CONSTANT_TRANSCRIPT)
    metadata = build_meeting_metadata(normalized_data)
    sentences = normalized_data["sentences"]

    grouped_sentences = group_by_speaker(sentences)
    
    result = create_chunks(sentences, metadata)
    print(f"✅ create_chunks created {len(result)} chunks")
    if result:
        print(f"✅ First chunk speaker: {result[0]['speaker_name']}")
        print(f"✅ First chunk length: {result[0]['text_length']} chars")
        
    #     # Save chunks to JSON file
    #     output_file = "chunks_output.json"
    #     with open(output_file, 'w', encoding='utf-8') as f:
    #         json.dump(result, f, indent=2, ensure_ascii=False)
    #     print(f"✅ Chunks saved to {output_file}")
    
    # Verify structure
    assert isinstance(result, list)
    assert len(result) > 0
    if result:
        assert "text" in result[0]
        assert "speaker_name" in result[0]
        assert "speaker_id" in result[0]
        assert "speaker_role" in result[0]
        assert "meeting_id" in result[0]
        assert "meeting_title" in result[0]
        assert "meeting_date" in result[0]
        assert "chunk_index" in result[0]
        assert "chunk_type" in result[0]
        assert "is_meeting_summary" in result[0]
        assert "contains_decision" in result[0]
        assert "contains_commitment" in result[0]
        assert "contains_question" in result[0]
        assert "sentiment" in result[0]
        assert "chunk_id" in result[0]
        assert "text_length" in result[0]
        assert result[0]["meeting_id"] == metadata["meeting_id"]
        assert result[0]["meeting_title"] == metadata["title"]
    
    # print("✅ create_chunks working correctly\n")

async def test_webhook_development_mode():
    """Test webhook handler in development mode"""
    print("=== Testing webhook (development mode) ===")
    
    # Set development mode
    os.environ["DEVELOPMENT_MODE"] = "true"
    
    # Create test payload
    test_payload = {"transcript_id": "test-123"}
    
    try:
        await handle_fireflies_webhook(test_payload)
        print("✅ Webhook development mode working correctly\n")
    except Exception as e:
        print(f"❌ Webhook test failed: {e}\n")

async def test_webhook_production_mode():
    """Test webhook handler in production mode (without API calls)"""
    # print("=== Testing webhook (production mode structure) ===")
    
    # Set production mode
    os.environ["DEVELOPMENT_MODE"] = "false"
    
    # Create test payload with transcript_id
    test_payload = {"transcript_id": "non-existent-id"}
    
    try:
        await handle_fireflies_webhook(test_payload)
        # print("✅ Webhook production mode structure working correctly\n")
    except Exception as e:
        print(f"ℹ️ Expected failure (no API): {e}\n")

async def main():
    """Run all tests"""
    # print("🧪 Testing Fireflies Integration...\n")
    
    # Test individual functions
    test_normalize_transcript()
    test_build_meeting_metadata()
    # test_group_by_speaker()
    test_create_chunks()
    
    # Test webhook modes
    # await test_webhook_development_mode()
    # await test_webhook_production_mode()
    
    # print("🎉 All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())