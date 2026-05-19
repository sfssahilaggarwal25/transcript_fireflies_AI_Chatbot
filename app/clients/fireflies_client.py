import requests
import logging
from typing import Dict, Any
from app.config import Config

logger = logging.getLogger(__name__)


class FirefliesAPIError(Exception):
    """Custom exception for Fireflies API errors"""



def fetch_transcript(transcript_id: str) -> Dict[str, Any]:
    """
    Fetch transcript from Fireflies API with proper error handling
    
    Args:
        transcript_id: The ID of the transcript to fetch
        
    Returns:
        Dict containing the transcript data
        
    Raises:
        FirefliesAPIError: If API request fails or returns invalid data
    """
    if not transcript_id:
        raise FirefliesAPIError("Transcript ID cannot be empty")
    
    if not Config.API_KEY:
        raise FirefliesAPIError("Fireflies API key not configured")
    
    query = """
    query Transcript($id: String!) {
      transcript(id: $id) {
        id
        title
        date
        sentences {
          text
          speaker_name
          rawStartTimeMs
          rawEndTimeMs
        }
        summary {
          overview
          action_items
        }
      }
    }
    """

    try:
        response = requests.post(
            Config.FIREFLIES_API_URL,
            headers={
                "Authorization": f"Bearer {Config.API_KEY}",
                "Content-Type": "application/json"
            },
            json={"query": query, "variables": {"id": transcript_id}},
            timeout=30  # Add timeout for production
        )
        
        response.raise_for_status()  # Raise exception for HTTP errors
        
        data = response.json()
        
        # Validate response structure
        if "errors" in data:
            error_msg = data["errors"][0].get("message", "Unknown API error")
            raise FirefliesAPIError(f"API Error: {error_msg}")
        
        if "data" not in data:
            raise FirefliesAPIError("Invalid API response: missing data field")
            
        logger.info(f"Successfully fetched transcript {transcript_id}")
        return data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching transcript {transcript_id}: {e}")
        raise FirefliesAPIError(f"Network error: {str(e)}")
    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching transcript {transcript_id}")
        raise FirefliesAPIError("Request timeout")
    except Exception as e:
        logger.error(f"Unexpected error fetching transcript {transcript_id}: {e}")
        raise FirefliesAPIError(f"Unexpected error: {str(e)}")


def validate_api_config() -> bool:
    """Validate that API configuration is properly set up"""
    return bool(Config.FIREFLIES_API_URL and Config.API_KEY)
