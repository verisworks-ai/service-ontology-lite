from __future__ import annotations

import json
from pathlib import Path

from service_ontology_lite.agent_os import load_agent_os_registry, summarize_project_contexts
from service_ontology_lite.scanner import scan_project
from service_ontology_lite.schema import validate_manifest


def test_validate_manifest_accepts_agent_os_registry_sections():
    manifest = {
        "agent_os": {
            "agents": [{"id": "implementation-agent", "role": "implementation"}],
            "surfaces": [
                {
                    "id": "collaboration-thread-1",
                    "type": "discord_thread",
                    "project_context_id": "service-ontology-lite",
                }
            ],
            "skills": [{"id": "ontology-risk-map"}],
            "hooks": [{"id": "on_task_complete", "event": "task.complete"}],
            "loops": [{"id": "evidence_capture_loop"}],
            "plugins": [{"id": "service-ontology-lite"}],
            "memories": [{"id": "sample/service-ontology-lite", "namespace": "project"}],
            "projects": [{"id": "service-ontology-lite", "name": "service-ontology-lite"}],
            "artifacts": [
                {
                    "id": "agent-os-registry-test",
                    "type": "pytest",
                    "project_context_id": "service-ontology-lite",
                }
            ],
            "tasks": [
                {
                    "id": "agent-os-poc",
                    "project_context_id": "service-ontology-lite",
                    "owner_agent": "implementation-agent",
                    "surface_id": "collaboration-thread-1",
                    "skills": ["ontology-risk-map"],
                }
            ],
            "relations": [
                {"source": "implementation-agent", "relation": "uses", "target": "ontology-risk-map"},
                {
                    "source": "collaboration-thread-1",
                    "relation": "binds_to",
                    "target": "service-ontology-lite",
                },
            ],
        }
    }

    assert validate_manifest(manifest) == []


def test_load_agent_os_registry_normalizes_counts_and_relationships(tmp_path: Path):
    (tmp_path / "service-ontology.json").write_text(
        json.dumps(
            {
                "agent_os": {
                    "agents": [{"id": "implementation-agent", "role": "implementation"}],
                    "surfaces": [
                        {"id": "thread-1", "type": "discord_thread", "project_context_id": "service-ontology-lite"}
                    ],
                    "tasks": [
                        {
                            "id": "task-1",
                            "project_context_id": "service-ontology-lite",
                            "owner_agent": "implementation-agent",
                            "surface_id": "thread-1",
                            "skills": ["ontology-risk-map"],
                        }
                    ],
                    "relations": [{"source": "implementation-agent", "relation": "owns", "target": "task-1"}],
                }
            }
        ),
        encoding="utf-8",
    )

    registry = load_agent_os_registry(tmp_path)
    graph = scan_project(tmp_path)

    assert registry["counts"] == {
        "projects": 0,
        "agents": 1,
        "surfaces": 1,
        "tasks": 1,
        "skills": 0,
        "hooks": 0,
        "loops": 0,
        "plugins": 0,
        "artifacts": 0,
        "memories": 0,
        "relations": 1,
    }
    assert registry["tasks"][0]["owner_agent"] == "implementation-agent"
    assert graph.metadata["agent_os"]["counts"]["tasks"] == 1
    assert graph.metadata["agent_os"]["relations"][0] == {
        "source": "implementation-agent",
        "relation": "owns",
        "target": "task-1",
    }


def test_summarize_project_contexts_groups_surfaces_tasks_and_artifacts():
    registry = {
        "projects": [{"id": "service-ontology-lite", "name": "service-ontology-lite"}],
        "agents": [{"id": "implementation-agent", "role": "implementation"}],
        "surfaces": [
            {"id": "collaboration-thread-1", "type": "discord_thread", "project_context_id": "service-ontology-lite"},
            {"id": "local-repo", "type": "local_repo", "project_context_id": "service-ontology-lite"},
        ],
        "tasks": [
            {"id": "task-1", "project_context_id": "service-ontology-lite", "owner_agent": "implementation-agent"},
            {"id": "task-2", "project_context_id": "missing-project", "owner_agent": "research-agent"},
        ],
        "artifacts": [
            {"id": "pytest-output", "type": "test", "project_context_id": "service-ontology-lite"}
        ],
        "memories": [
            {
                "id": "sample/service-ontology-lite",
                "namespace": "project",
                "project_context_id": "service-ontology-lite",
            }
        ],
        "relations": [{"source": "task-1", "relation": "produces", "target": "pytest-output"}],
    }

    summary = summarize_project_contexts(registry)

    assert summary["service-ontology-lite"]["declared"] is True
    assert summary["service-ontology-lite"]["counts"] == {
        "surfaces": 2,
        "tasks": 1,
        "artifacts": 1,
        "memories": 1,
        "relations": 1,
    }
    assert summary["service-ontology-lite"]["agents"] == ["implementation-agent"]
    assert summary["missing-project"]["declared"] is False
    assert summary["missing-project"]["warnings"] == [
        "project_context_id is referenced but not declared in agent_os.projects"
    ]


def test_validate_manifest_reports_agent_os_missing_required_ids():
    errors = validate_manifest(
        {
            "agent_os": {
                "agents": [{"role": "implementation"}],
                "surfaces": [{"id": "thread-1", "project_context_id": "service-ontology-lite"}],
                "projects": [{"name": "service-ontology-lite"}],
                "artifacts": [{"type": "report", "project_context_id": "service-ontology-lite"}],
                "tasks": [{"id": "task-1", "owner_agent": "implementation-agent"}],
                "relations": [{"source": "implementation-agent", "target": "task-1"}],
            }
        }
    )

    assert "agent_os.agents[0].id is required" in errors
    assert "agent_os.surfaces[0].type is required" in errors
    assert "agent_os.projects[0].id is required" in errors
    assert "agent_os.artifacts[0].id is required" in errors
    assert "agent_os.tasks[0].project_context_id is required" in errors
    assert "agent_os.relations[0].relation is required" in errors
