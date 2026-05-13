import logging 
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def answer_question(query: str, project_id: str):
    """
    Answer user question using RAG pipeline.
    """
    try:
        query = 'What was decided in the meeting?'
        project_id = 'test-project-id'
        print(f"Answering question: {query}")
        print(f"Project ID: {project_id}")

    except Exception as e:
        logger.error(f"Answer generation failed: {e}")
        raise