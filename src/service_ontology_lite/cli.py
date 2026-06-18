from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import __version__
from .agent_os import filter_project_contexts, load_agent_os_registry
from .audit import audit_change_risk, audit_graph
from .models import score_findings
from .scanner import _load_manifest, scan_project
from .schema import validate_manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="service-ontology")
    parser.add_argument("-V", "--version", action="version", version=f"service-ontology {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    for name in ("scan", "graph", "audit"):
        p = sub.add_parser(name)
        p.add_argument("root", nargs="?", default=".")
        p.add_argument("--json", action="store_true")

    agent_os = sub.add_parser("agent-os")
    agent_os.add_argument("root", nargs="?", default=".")
    agent_os.add_argument("--json", action="store_true")
    agent_os.add_argument("--project-context", dest="project_context_id")

    risk = sub.add_parser("risk")
    risk.add_argument("root", nargs="?", default=".")
    risk.add_argument("--changed", action="append", default=[])
    risk.add_argument("--json", action="store_true")

    validate = sub.add_parser("validate")
    validate.add_argument("root", nargs="?", default=".")
    validate.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)

    if args.command == "validate":
        manifest = _load_manifest(Path(args.root).resolve(), validate=False)
        errors = validate_manifest(manifest) if manifest else ["service-ontology manifest not found"]
        payload = {"manifest_valid": not errors, "errors": errors}
        if getattr(args, "json", False):
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(_format_text(args.command, payload))
        return 0 if not errors else 1

    if args.command == "agent-os":
        root = Path(args.root).resolve()
        manifest = _load_manifest(root, validate=False)
        errors = validate_manifest(manifest) if manifest else ["service-ontology manifest not found"]
        if errors:
            payload = {"manifest_valid": False, "errors": errors}
            if getattr(args, "json", False):
                print(json.dumps(payload, ensure_ascii=False, indent=2))
            else:
                print(_format_text("validate", payload))
            return 1
        payload = load_agent_os_registry(root)
        if args.project_context_id:
            payload = filter_project_contexts(payload, args.project_context_id)
        if getattr(args, "json", False):
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(_format_text(args.command, payload))
        return 0

    graph = scan_project(Path(args.root))

    if args.command in {"scan", "graph"}:
        payload = graph.as_dict()
    elif args.command == "audit":
        findings = audit_graph(graph)
        payload = {
            "score": score_findings(findings),
            "finding_count": len(findings),
            "findings": [f.as_dict() for f in findings],
            "metrics": graph.metadata,
        }
    elif args.command == "risk":
        payload = audit_change_risk(graph, args.changed)
    else:
        raise AssertionError(args.command)

    if getattr(args, "json", False):
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(_format_text(args.command, payload))
    return 0


def _format_text(command: str, payload: dict) -> str:
    if command in {"scan", "graph"}:
        return "\n".join([
            "service-ontology-lite graph",
            f"routes: {len(payload.get('routes', []))}",
            f"entities: {len(payload.get('entities', []))}",
            f"external_services: {len(payload.get('external_services', []))}",
            f"jobs: {len(payload.get('jobs', []))}",
        ])
    if command == "audit":
        lines = [f"score: {payload['score']}", f"findings: {payload['finding_count']}"]
        for item in payload["findings"]:
            lines.append(f"[{item['severity']}] {item['title']}")
        return "\n".join(lines)
    if command == "validate":
        lines = [f"manifest_valid: {str(payload['manifest_valid']).lower()}"]
        lines.extend(payload.get("errors", []))
        return "\n".join(lines)
    if command == "agent-os":
        counts = payload.get("counts", {})
        lines = [
            "service-ontology-lite agent-os",
            f"projects: {counts.get('projects', 0)}",
            f"agents: {counts.get('agents', 0)}",
            f"surfaces: {counts.get('surfaces', 0)}",
            f"tasks: {counts.get('tasks', 0)}",
            f"artifacts: {counts.get('artifacts', 0)}",
            f"project_contexts: {len(payload.get('project_contexts', {}))}",
        ]
        for project_context_id, context in payload.get("project_contexts", {}).items():
            context_counts = context.get("counts", {})
            status = "declared" if context.get("declared") else "undeclared"
            lines.append(
                f"- {project_context_id} ({status}): "
                f"surfaces={context_counts.get('surfaces', 0)}, "
                f"tasks={context_counts.get('tasks', 0)}, "
                f"artifacts={context_counts.get('artifacts', 0)}, "
                f"memories={context_counts.get('memories', 0)}"
            )
        return "\n".join(lines)
    return json.dumps(payload, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    raise SystemExit(main())
