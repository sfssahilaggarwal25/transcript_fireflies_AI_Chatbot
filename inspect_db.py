"""
Inspect what is stored in ChromaDB.

Usage:
    python inspect_db.py
"""

import sys
import logging

sys.stdout.reconfigure(encoding="utf-8")

from app.services.storage.db import get_raw_collection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    try:
        collection = get_raw_collection()
        
        print(f'\n\n collection: {collection} \n\n')
        print("Fetching chunks with contains_commitment = True...")
        results = collection.get(
            where={"contains_commitment": True},
            include=["metadatas", "documents"],
        )

        for i in range(min(10, len(results["ids"]))):
            print("\n---")
            print(results["documents"][i])
        

        total = collection.count()

        print(f"\n{'=' * 55}")
        print("  ChromaDB — meeting_chunks collection")
        print(f"{'=' * 55}")
        print(f"  Total chunks stored : {total}")

        if total == 0:
            print("  Collection is empty.")
            print(f"\n{'=' * 55}\n")
            return

        # ---------------------------------------------------
        # All projects + meetings
        # ---------------------------------------------------
        all_results = collection.get(include=["metadatas"])

        projects = {}

        for metadata in all_results.get("metadatas", []):
            if not metadata:
                continue

            project_id = metadata.get("project_id", "unknown")
            meeting_id = metadata.get("meeting_id", "unknown")

            if project_id not in projects:
                projects[project_id] = {}

            projects[project_id][meeting_id] = (
                projects[project_id].get(meeting_id, 0) + 1
            )

        print("\n  Projects & meetings:")

        for project_id, meetings in projects.items():
            print(f"\n    project_id : {project_id}")

            for meeting_id, count in meetings.items():
                print(f"      meeting_id : {meeting_id}  ->  {count} chunks")

        # ---------------------------------------------------
        # Summary chunks
        # ---------------------------------------------------
        summary_results = collection.get(
            where={"is_meeting_summary": True},
            include=["metadatas", "documents"],
        )

        summary_ids = summary_results.get("ids", [])
        summary_metadatas = summary_results.get("metadatas", [])
        summary_docs = summary_results.get("documents", [])

        print(f"\n  Summary chunks : {len(summary_ids)}")

        for i, doc_id in enumerate(summary_ids):
            metadata = summary_metadatas[i]
            text = summary_docs[i]

            print(f"\n    [{doc_id}]")
            print(
                f"    meeting : {metadata.get('meeting_title')} "
                f"({metadata.get('meeting_date')})"
            )
            print(
                f"    text    : "
                f"{text[:200]}{'...' if len(text) > 200 else ''}"
            )

        # ---------------------------------------------------
        # Signal counts
        # ---------------------------------------------------
        decision_results = collection.get(where={"contains_decision": True})
        commitment_results = collection.get(where={"contains_commitment": True})
        question_results = collection.get(where={"contains_question": True})

        print(f"\n  Signal counts:")
        print(f"    contains_decision   : {len(decision_results.get('ids', []))}")
        print(f"    contains_commitment : {len(commitment_results.get('ids', []))}")
        print(f"    contains_question   : {len(question_results.get('ids', []))}")

        # ---------------------------------------------------
        # Sample chunks
        # ---------------------------------------------------
        sample = collection.get(
            limit=3,
            include=["metadatas", "documents"],
        )

        sample_ids = sample.get("ids", [])
        sample_metadatas = sample.get("metadatas", [])
        sample_docs = sample.get("documents", [])

        print(f"\n  Sample (first 3 chunks):")

        for i, doc_id in enumerate(sample_ids):
            metadata = sample_metadatas[i]
            text = sample_docs[i]

            print(f"\n    chunk_id   : {doc_id}")
            print(
                f"    speaker    : "
                f"{metadata.get('speaker_name')} "
                f"[{metadata.get('speaker_role')}]"
            )
            print(
                f"    meeting    : "
                f"{metadata.get('meeting_title')} "
                f"#{metadata.get('meeting_number')}"
            )
            print(
                f"    signals    : "
                f"decision={metadata.get('contains_decision')}  "
                f"commitment={metadata.get('contains_commitment')}  "
                f"question={metadata.get('contains_question')}"
            )
            print(
                f"    text       : "
                f"{text[:150]}{'...' if len(text) > 150 else ''}"
            )

        print(f"\n{'=' * 55}\n")

    except Exception as e:
        logger.exception("Failed to inspect ChromaDB: %s", e)
        raise


if __name__ == "__main__":
    main()