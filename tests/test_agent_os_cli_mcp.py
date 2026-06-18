from __future__ import annotations

import json
from pathlib import Path

from service_ontology_lite.cli import main as cli_main
from service_ontology_lite.mcp_server import call_tool


def test_agent_os_cli_rejects_invalid_manifest(tmp_path: Path, capsys):
    (tmp_path / "service-ontology.json").write_text(
        json.dumps({"agent_os": {"tasks": [{"id": "task-1", "owner_agent": "codex-hermes"}]}}),
        encoding="utf-8",
    )

    exit_code = cli_main(["agent-os", str(tmp_path)])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "manifest_valid: false" in output
    assert "agent_os.tasks[0].project_context_id is required" in output


def test_mcp_agent_os_tools_reject_invalid_manifest(tmp_path: Path):
    (tmp_path / "service-ontology.json").write_text(
        json.dumps({"agent_os": {"artifacts": [{"id": "report-1"}]}}),
        encoding="utf-8",
    )

    payload = call_tool("get_agent_os_graph", {"root": str(tmp_path)}, tmp_path)

    assert payload == {
        "manifest_valid": False,
        "errors": ["agent_os.artifacts[0].project_context_id is required"],
    }


def test_mcp_list_project_contexts_returns_context_summary(tmp_path: Path):
    (tmp_path / "service-ontology.json").write_text(
        json.dumps(
            {
                "agent_os": {
                    "projects": [{"id": "service-ontology-lite"}],
                    "tasks": [
                        {
                            "id": "task-1",
                            "project_context_id": "service-ontology-lite",
                            "owner_agent": "codex-hermes",
                        }
                    ],
                }
            }
        ),
        encoding="utf-8",
    )

    payload = call_tool("list_project_contexts", {"root": str(tmp_path)}, tmp_path)

    assert payload["project_contexts"]["service-ontology-lite"]["counts"]["tasks"] == 1
    assert payload["project_contexts"]["service-ontology-lite"]["agents"] == ["codex-hermes"]
