"""
core/project_engine.py — eLo AI project registry management.

Owns all project-related operations: loading the registry, resolving which
project an input belongs to, and querying project metadata.

The project namespace system ensures every interaction is tagged and memory
stays organised across eLo's active creative and technical projects.
"""

import json
import os

_DIR           = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_REGISTRY_PATH = os.path.join(_DIR, "memory", "project_registry.json")

_DEFAULT_REGISTRY = {
    "project_namespace": "elo_core",
    "active_projects": {},
}


def load_registry() -> dict:
    """Load the project registry from disk."""
    if os.path.exists(_REGISTRY_PATH):
        with open(_REGISTRY_PATH) as f:
            return json.load(f)
    return dict(_DEFAULT_REGISTRY)


def list_projects(registry: dict = None) -> dict:
    """Return the active_projects dict from the registry."""
    reg = registry or load_registry()
    return reg.get("active_projects", {})


def get_project(project_id: str, registry: dict = None) -> dict:
    """Return metadata for a specific project, or empty dict if not found."""
    return list_projects(registry).get(project_id, {})


def resolve_project(text: str, registry: dict = None) -> str:
    """
    Return the project namespace most relevant to the input text.

    Matches against:
        - project id
        - project id with spaces instead of underscores
        - linked system names from the project's metadata

    Falls back to the default project namespace.
    """
    reg        = registry or load_registry()
    text_lower = text.lower()

    for project_id, info in reg.get("active_projects", {}).items():
        candidates = [project_id, project_id.replace("_", " ")]
        candidates += info.get("linked_systems", [])
        if any(c.lower() in text_lower for c in candidates):
            return project_id

    return reg.get("project_namespace", "elo_core")


def default_namespace(registry: dict = None) -> str:
    """Return the fallback project namespace."""
    reg = registry or load_registry()
    return reg.get("project_namespace", "elo_core")
