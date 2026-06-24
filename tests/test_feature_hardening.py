from __future__ import annotations

import asyncio
import json
from pathlib import Path

from service_ontology_lite.cli import main as cli_main
from service_ontology_lite.mcp_server import create_app
from service_ontology_lite.scanner import scan_project
from service_ontology_lite.schema import validate_manifest

REVIEWED_MCP_TOOLS = {
    "get_service_graph",
    "list_routes",
    "list_external_dependencies",
    "audit_change_risk",
    "audit_service",
    "validate_manifest",
}


def test_nextjs_route_groups_dynamic_and_catch_all_segments(tmp_path: Path):
    app = tmp_path / "app"
    (app / "(marketing)" / "blog" / "[slug]").mkdir(parents=True)
    (app / "(marketing)" / "blog" / "[slug]" / "page.tsx").write_text(
        "export default function Page() {}",
        encoding="utf-8",
    )
    (app / "docs" / "[...parts]").mkdir(parents=True)
    (app / "docs" / "[...parts]" / "page.tsx").write_text("export default function Page() {}", encoding="utf-8")
    (app / "shop" / "[[...filters]]").mkdir(parents=True)
    (app / "shop" / "[[...filters]]" / "route.ts").write_text(
        "export async function GET() { return Response.json({}) }",
        encoding="utf-8",
    )

    graph = scan_project(tmp_path)
    paths = {route.path for route in graph.routes}

    assert "/blog/:slug" in paths
    assert "/docs/:parts*" in paths
    assert "/shop/:filters*" in paths


def test_validate_manifest_accepts_sample_manifest():
    manifest = json.loads(Path("sample-app/service-ontology.json").read_text(encoding="utf-8"))

    errors = validate_manifest(manifest)

    assert errors == []


def test_validate_manifest_reports_invalid_auth_and_missing_handler():
    manifest = {
        "routes": [
            {"path": "/admin", "auth": "superuser", "methods": ["GET"]},
            {"path": "dashboard", "auth": "required", "handler": "app/dashboard/page.tsx"},
        ],
        "jobs": [{"name": "nightly", "auth": "public"}],
    }

    errors = validate_manifest(manifest)

    assert "routes[0].auth must be one of" in "\n".join(errors)
    assert "routes[0].handler is required" in errors
    assert "routes[1].path must start with /" in errors
    assert "jobs[0].handler is required" in errors
    assert "jobs[0].auth must be cron/admin/required" in errors


def test_cli_validate_returns_non_zero_for_invalid_manifest(tmp_path: Path, capsys):
    (tmp_path / "service-ontology.json").write_text(
        json.dumps({"routes": [{"path": "bad", "auth": "nope"}]}),
        encoding="utf-8",
    )

    exit_code = cli_main(["validate", str(tmp_path)])
    out = capsys.readouterr().out

    assert exit_code == 1
    assert "manifest_valid: false" in out
    assert "routes[0].path must start with /" in out


def test_mcp_reviewed_tools_include_service_name_and_annotations():
    tools = asyncio.run(create_app().list_tools())
    reviewed = {tool.name: tool for tool in tools if tool.name in REVIEWED_MCP_TOOLS}

    assert set(reviewed) == REVIEWED_MCP_TOOLS
    for tool in reviewed.values():
        assert tool.description is not None
        assert "서비스 안전점검 온톨로지 엔진" in tool.description
        assert tool.annotations is not None
        assert tool.annotations.readOnlyHint is True
        assert tool.annotations.destructiveHint is False
        assert tool.annotations.idempotentHint is True
        assert tool.annotations.openWorldHint is False
