import json
import os

_PROJECTS_FILE = os.path.join(os.path.dirname(__file__), "../../../projects.json")

_projects_cache = None


def _load():
    global _projects_cache
    if _projects_cache is None:
        with open(_PROJECTS_FILE, "r", encoding="utf-8") as f:
            _projects_cache = json.load(f)
    return _projects_cache


def get_project_for_meeting(meeting_id: str) -> dict | None:
    """Return project scope fields for a meeting_id, or None if not mapped."""
    projects = _load()
    for project_id, project in projects.items():
        if meeting_id in project.get("meeting_ids", []):
            return {
                "project_id":   project_id,
                "project_name": project["project_name"],
                "company_id":   project["company_id"],
                "company_name": project["company_name"],
            }
    return None


def get_speaker_role(meeting_id: str, speaker_name: str) -> str:
    """Return speaker role for a given meeting and speaker name.
    Falls back to 'unknown' if meeting or speaker is not in projects.json.
    """
    projects = _load()
    for project in projects.values():
        if meeting_id in project.get("meeting_ids", []):
            return project.get("speakers", {}).get(speaker_name, "unknown")
    return "unknown"
