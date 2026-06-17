from __future__ import annotations

import json
from pathlib import Path

from service_ontology_lite.audit import audit_change_risk
from service_ontology_lite.cli import main as cli_main
from service_ontology_lite.mcp_server import handle_request
from service_ontology_lite.scanner import scan_project
from service_ontology_lite.schema import validate_manifest


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


def test_scan_ignores_dependency_and_build_artifact_dirs(tmp_path: Path):
    (tmp_path / "node_modules" / "pkg" / "app" / "api" / "leak").mkdir(parents=True)
    (tmp_path / "node_modules" / "pkg" / "app" / "api" / "leak" / "route.ts").write_text(
        "export async function GET() { return Response.json({ DISCORD: true }) }",
        encoding="utf-8",
    )
    (tmp_path / ".vercel" / "output" / "functions" / "api" / "shadow.func").mkdir(parents=True)
    (tmp_path / ".vercel" / "output" / "functions" / "api" / "shadow.func" / "route.js").write_text(
        "export async function GET() { return Response.json({ VERCEL: true }) }",
        encoding="utf-8",
    )
    (tmp_path / "app" / "api" / "real").mkdir(parents=True)
    (tmp_path / "app" / "api" / "real" / "route.ts").write_text(
        "export async function GET() { return Response.json({ ok: true }) }",
        encoding="utf-8",
    )

    graph = scan_project(tmp_path)

    handlers = {route.handler for route in graph.routes}
    assert handlers == {"app/api/real/route.ts"}
    assert graph.external_services == []


def test_scan_detects_vercel_api_mjs_routes(tmp_path: Path):
    (tmp_path / "api" / "share").mkdir(parents=True)
    (tmp_path / "api" / "events.mjs").write_text(
        "export default function handler(req, res) { res.json({ ok: true }) }",
        encoding="utf-8",
    )
    (tmp_path / "api" / "share" / "[slug].mjs").write_text(
        "export default function handler(req, res) { res.json({ ok: true }) }",
        encoding="utf-8",
    )
    (tmp_path / "api" / "_lib").mkdir(parents=True)
    (tmp_path / "api" / "_lib" / "helper.mjs").write_text(
        "export function helper() { return 'not-a-route' }",
        encoding="utf-8",
    )

    graph = scan_project(tmp_path)
    routes = {route.path: route for route in graph.routes}

    assert routes["/api/events"].handler == "api/events.mjs"
    assert routes["/api/events"].methods == ["GET", "POST", "OPTIONS"]
    assert routes["/api/share/:slug"].handler == "api/share/[slug].mjs"
    assert "/api/_lib/helper" not in routes


def test_change_risk_service_role_external_dependency_is_high(tmp_path: Path):
    (tmp_path / "service-ontology.json").write_text(
        json.dumps(
            {
                "external_services": [
                    {
                        "name": "Supabase",
                        "type": "database",
                        "env": ["SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"],
                        "used_by": ["api/_lib/second-salary-api.mjs"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "api" / "_lib").mkdir(parents=True)
    (tmp_path / "api" / "_lib" / "second-salary-api.mjs").write_text(
        "const key = process.env.SUPABASE_SERVICE_ROLE_KEY;",
        encoding="utf-8",
    )

    graph = scan_project(tmp_path)
    risk = audit_change_risk(graph, ["api/_lib/second-salary-api.mjs"])

    assert risk["severity"] == "HIGH"
    assert "sensitive_external_dependency_touched" in risk["reasons"]


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


def test_mcp_unknown_tool_returns_jsonrpc_error(tmp_path: Path):
    response = handle_request(
        {"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": {"name": "missing_tool", "arguments": {}}},
        tmp_path,
    )

    assert response["id"] == 7
    assert response["error"]["code"] == -32602
    assert "Unknown tool" in response["error"]["message"]


def test_mcp_validate_manifest_tool_reports_valid_sample():
    response = handle_request(
        {
            "jsonrpc": "2.0",
            "id": 8,
            "method": "tools/call",
            "params": {"name": "validate_manifest", "arguments": {"root": "sample-app"}},
        },
        Path("."),
    )
    text = response["result"]["content"][0]["text"]
    payload = json.loads(text)

    assert payload == {"manifest_valid": True, "errors": []}
