"""
Load agent registry and project plan for prompt-build orchestration.
See docs/PROMPT_BUILD_ORCHESTRATION.md.
Registry and plan are JSON (optional YAML if PyYAML present).
"""

import json
from pathlib import Path

from ..config import processing_path

PROMPT_BUILD_DIR = processing_path("prompt-build")
REGISTRY_FILE = PROMPT_BUILD_DIR / "agent_registry.json"
PROJECTS_DIR = PROMPT_BUILD_DIR / "projects"


def _load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def load_registry() -> dict:
    """Load agent_registry.json. Returns {generic: [...], project_specific: [...]}."""
    data = _load_json(REGISTRY_FILE)
    if not data:
        return {"generic": [], "project_specific": []}
    return {
        "generic": data.get("generic", []),
        "project_specific": data.get("project_specific", []),
    }


def load_project_plan(project_id: str) -> dict | None:
    """Load projects/<project_id>/plan.json. Returns plan dict or None."""
    path = PROJECTS_DIR / project_id / "plan.json"
    return _load_json(path)


def resolve_agents_for_project(project_id: str) -> list[dict]:
    """Return list of agent configs (from registry) for this project, in order: generic then project_agents."""
    registry = load_registry()
    plan = load_project_plan(project_id)
    if not plan:
        return []
    by_id = {}
    for a in registry.get("generic", []):
        by_id[a["id"]] = a
    for a in registry.get("project_specific", []):
        by_id[a["id"]] = a
    out = []
    for id in plan.get("generic_agents", []):
        if id in by_id:
            out.append(by_id[id])
    for id in plan.get("project_agents", []):
        if id in by_id:
            out.append(by_id[id])
    return out
