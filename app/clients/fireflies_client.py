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
          start_time
          end_time
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
            timeout=30
        )

        # Read the body BEFORE raise_for_status so the actual Fireflies error
        # message is included — raise_for_status() discards the response body.
        if not response.ok:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text[:500]
            logger.error(
                "Fireflies API HTTP %d for transcript %s: %s",
                response.status_code, transcript_id, error_body,
            )
            raise FirefliesAPIError(
                f"Fireflies API returned HTTP {response.status_code} for transcript '{transcript_id}'. "
                f"Details: {error_body}"
            )

        data = response.json()

        if "errors" in data:
            error_msg = data["errors"][0].get("message", "Unknown API error")
            logger.error("Fireflies GraphQL error for %s: %s", transcript_id, error_msg)
            raise FirefliesAPIError(f"Fireflies API error: {error_msg}")

        if "data" not in data:
            raise FirefliesAPIError("Invalid API response: missing data field")

        logger.info("Successfully fetched transcript %s", transcript_id)
        return data

    except FirefliesAPIError:
        raise
    except requests.exceptions.Timeout:
        logger.error("Timeout fetching transcript %s", transcript_id)
        raise FirefliesAPIError(f"Request timed out fetching transcript '{transcript_id}'")
    except requests.exceptions.RequestException as e:
        logger.error("Network error fetching transcript %s: %s", transcript_id, e)
        raise FirefliesAPIError(f"Network error: {str(e)}")
    except Exception as e:
        logger.error("Unexpected error fetching transcript %s: %s", transcript_id, e)
        raise FirefliesAPIError(f"Unexpected error: {str(e)}")


def validate_api_config() -> bool:
    """Validate that API configuration is properly set up"""
    return bool(Config.FIREFLIES_API_URL and Config.API_KEY)
