import logging
from typing import Optional

from langchain_core.documents import Document

from app.services.storage.db import get_vectorstore

logger = logging.getLogger(__name__)

DEFAULT_TOP_K = 8
MAX_TOP_K = 25


def _validate_query(query: str) -> str:
    """
    Validate and normalize user query.
    """

    if not query:
        raise ValueError("Query cannot be empty.")

    cleaned = query.strip()

    if not cleaned:
        raise ValueError("Query cannot be blank.")

    return cleaned


def _validate_project_id(project_id: str) -> str:
    """
    Validate project scoping.
    """

    if not project_id:
        raise ValueError("project_id is required.")

    cleaned = project_id.strip()

    if not cleaned:
        raise ValueError("project_id cannot be blank.")

    return cleaned


def _validate_top_k(k: int) -> int:
    """
    Validate retrieval depth.
    """

    if k <= 0:
        return DEFAULT_TOP_K

    if k > MAX_TOP_K:
        logger.warning(
            "Requested top_k=%s exceeds max. Capping to %s.",
            k,
            MAX_TOP_K,
        )
        return MAX_TOP_K

    return k


def _build_filter(
    project_id: str,
    filters: Optional[dict] = None,
) -> dict:
    """
    Build safe Chroma metadata filter.
    Always scopes retrieval to a single project.
    """

    metadata_filter = {
        "project_id": project_id,
    }

    if filters:
        metadata_filter.update(filters)

    return metadata_filter


def retrieve_documents(
    query: str,
    project_id: str,
    filters: Optional[dict] = None,
    k: int = DEFAULT_TOP_K,
) -> list[Document]:
    """
    Retrieve semantically relevant transcript documents.

    Args:
        query:
            User semantic search query.

        project_id:
            Required project isolation boundary.

        filters:
            Optional metadata filters.
            Example:
                {
                    "speaker_role": "client",
                    "contains_commitment": True
                }

        k:
            Number of documents to retrieve.

    Returns:
        List[Document]
    """

    try:
        query = _validate_query(query)
        project_id = _validate_project_id(project_id)
        k = _validate_top_k(k)

        metadata_filter = _build_filter(
            project_id=project_id,
            filters=filters,
        )

        vectorstore = get_vectorstore()

        logger.info(
            "Retrieving documents | query='%s' | project_id=%s | k=%s | filters=%s",
            query,
            project_id,
            k,
            metadata_filter,
        )

        documents = vectorstore.similarity_search(
            query=query,
            k=k,
            filter=metadata_filter,
        )

        logger.info(
            "Retrieved %s documents.",
            len(documents),
        )

        return documents

    except Exception as e:
        logger.exception(
            "Document retrieval failed | query='%s' | project_id=%s",
            query,
            project_id,
        )
        raise RuntimeError(
            f"Document retrieval failed: {str(e)}"
        ) from e


def retrieve_commitment_documents(
    query: str,
    project_id: str,
    k: int = DEFAULT_TOP_K,
) -> list[Document]:
    """
    Retrieve commitment-related candidate chunks.
    Metadata hint only — not authoritative truth.
    """

    return retrieve_documents(
        query=query,
        project_id=project_id,
        filters={
            "contains_commitment": True,
        },
        k=k,
    )


def retrieve_question_documents(
    query: str,
    project_id: str,
    k: int = DEFAULT_TOP_K,
) -> list[Document]:
    """
    Retrieve question-related transcript chunks.
    """

    return retrieve_documents(
        query=query,
        project_id=project_id,
        filters={
            "contains_question": True,
        },
        k=k,
    )


def retrieve_decision_candidates(
    query: str,
    project_id: str,
    k: int = DEFAULT_TOP_K,
) -> list[Document]:
    """
    Retrieve decision candidates.

    IMPORTANT:
    Do NOT hard filter only decision metadata.
    Decision hints are weak signals.
    Use broad semantic retrieval instead.
    Semantic validation happens later.
    """

    return retrieve_documents(
        query=query,
        project_id=project_id,
        filters=None,
        k=k,
    )