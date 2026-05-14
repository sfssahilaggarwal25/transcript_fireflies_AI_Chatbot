import logging
from typing import Optional

from langchain_core.documents import Document

from app.services.storage.db import get_vectorstore
from app.services.storage.project_store import get_meeting_ids_for_project

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
    Build ChromaDB metadata filter.
    Always excludes is_meeting_summary chunks — those are fetched separately
    via _retrieve_summary_chunks() using the raw collection, not vector search.
    Multiple conditions use $and — ChromaDB 1.5+ rejects flat multi-key dicts.
    """
    base = {"project_id": {"$eq": project_id}}

    if not filters:
        return base

    conditions = [base]
    for key, value in filters.items():
        conditions.append({key: {"$eq": value}})
    return {"$and": conditions}


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
        logger.debug("  filter     : %s", metadata_filter)

        documents = vectorstore.similarity_search(
            query=query,
            k=k,
            filter=metadata_filter,
        )

        logger.info("  retrieved  : %d documents", len(documents))
        for i, doc in enumerate(documents, 1):
            m = doc.metadata
            preview = doc.page_content[:90].replace("\n", " ")
            logger.info(
                "  doc[%d/%d]  : %s (%s) | %s | \"%s...\"",
                i,
                len(documents),
                m.get("meeting_title", "?")[:35],
                m.get("meeting_date", "?"),
                m.get("speaker_name", "?"),
                preview,
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


def retrieve_timeline_documents(
    query: str,
    project_id: str,
    k_per_meeting: int = 6,
) -> list[Document]:
    """
    Retrieve documents for timeline/historical queries.

    Runs one semantic search per meeting in the project, then merges results
    sorted chronologically by meeting_date. This ensures every meeting
    contributes equally — plain similarity_search would skew toward whichever
    meeting is semantically closer to the query.
    """
    meeting_ids = get_meeting_ids_for_project(project_id)
    if not meeting_ids:
        logger.warning("No meeting IDs found for project_id=%s", project_id)
        return retrieve_documents(query, project_id, k=k_per_meeting * 2)

    all_docs: list[Document] = []
    for meeting_id in meeting_ids:
        try:
            docs = retrieve_documents(
                query=query,
                project_id=project_id,
                filters={"meeting_id": meeting_id},
                k=k_per_meeting,
            )
            all_docs.extend(docs)
            logger.debug("  timeline   : %d docs from meeting_id=%s", len(docs), meeting_id)
        except Exception as e:
            logger.warning("Timeline retrieval skipped for meeting_id=%s: %s", meeting_id, e)

    all_docs.sort(key=lambda d: d.metadata.get("meeting_date", ""))
    return all_docs