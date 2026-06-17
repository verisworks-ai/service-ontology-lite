from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from .audit import audit_change_risk, audit_graph
from .models import score_findings
from .scanner import _load_manifest, scan_project
from .schema import validate_manifest

SERVER_INFO = {"name": "service-ontology-lite", "version": "0.1.0"}


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    root = Path(argv[0] if argv else ".").resolve()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            response = handle_request(request, root)
        except Exception as exc:
            response = {"jsonrpc": "2.0", "id": None, "error": {"code": -32000, "message": str(exc)}}
        sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
        sys.stdout.flush()
    return 0


def handle_request(request: dict[str, Any], root: Path) -> dict[str, Any]:
    method = request.get("method")
    request_id = request.get("id")
    params = request.get("params") or {}

    if method == "initialize":
        return _result(request_id, {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": SERVER_INFO,
        })
    if method == "tools/list":
        return _result(request_id, {"tools": _tools()})
    if method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments") or {}
        try:
            payload = call_tool(tool_name, arguments, root)
        except ValueError as exc:
            return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32602, "message": str(exc)}}
        return _result(request_id, {"content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False, indent=2)}]})
    if method == "notifications/initialized":
        return _result(request_id, {})
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": f"Unknown method: {method}"}}


def call_tool(name: str, arguments: dict[str, Any], root: Path) -> dict[str, Any]:
    if name == "validate_manifest":
        target = Path(arguments.get("root") or root)
        manifest = _load_manifest(target, validate=False)
        errors = validate_manifest(manifest) if manifest else ["service-ontology manifest not found"]
        return {"manifest_valid": not errors, "errors": errors}
    graph = scan_project(arguments.get("root") or root)
    if name == "get_service_graph":
        return graph.as_dict()
    if name == "list_routes":
        return {"routes": [route.as_dict() for route in graph.routes]}
    if name == "list_external_dependencies":
        return {"external_services": [service.as_dict() for service in graph.external_services]}
    if name == "audit_change_risk":
        return audit_change_risk(graph, arguments.get("changed_files", []))
    if name == "audit_service":
        findings = audit_graph(graph)
        return {"score": score_findings(findings), "findings": [f.as_dict() for f in findings]}
    raise ValueError(f"Unknown tool: {name}")


def _tools() -> list[dict[str, Any]]:
    return [
        {"name": "get_service_graph", "description": "Return routes, entities, external services, jobs, and metadata.", "inputSchema": {"type": "object", "properties": {"root": {"type": "string"}}}},
        {"name": "list_routes", "description": "List service routes with auth boundaries and handlers.", "inputSchema": {"type": "object", "properties": {"root": {"type": "string"}}}},
        {"name": "list_external_dependencies", "description": "List detected external dependencies and env hints.", "inputSchema": {"type": "object", "properties": {"root": {"type": "string"}}}},
        {"name": "audit_change_risk", "description": "Estimate blast radius for changed files.", "inputSchema": {"type": "object", "properties": {"root": {"type": "string"}, "changed_files": {"type": "array", "items": {"type": "string"}}}}},
        {"name": "audit_service", "description": "Run generic service ontology audit rules.", "inputSchema": {"type": "object", "properties": {"root": {"type": "string"}}}},
        {"name": "validate_manifest", "description": "Validate service-ontology.json/yaml manifest structure before scan.", "inputSchema": {"type": "object", "properties": {"root": {"type": "string"}}}},
    ]


def _result(request_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


if __name__ == "__main__":
    raise SystemExit(main())
