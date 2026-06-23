from __future__ import annotations

from pathlib import Path
from typing import Any

import fastmcp

from .audit import audit_change_risk as compute_change_risk
from .audit import audit_graph
from .models import score_findings
from .scanner import _load_manifest, scan_project
from .schema import validate_manifest

# Default root for scanning
DEFAULT_ROOT = Path.cwd()


def create_app() -> fastmcp.FastMCP:
    """Create FastMCP app with tool handlers."""
    app = fastmcp.FastMCP("service-ontology-lite", version="0.1.0")

    @app.tool()
    def get_service_graph(root: str = ".") -> dict[str, Any]:
        """Return routes, entities, external services, jobs, and metadata."""
        target = Path(root).resolve()
        graph = scan_project(target)
        return graph.as_dict()

    @app.tool()
    def list_routes(root: str = ".") -> dict[str, Any]:
        """List service routes with auth boundaries and handlers."""
        target = Path(root).resolve()
        graph = scan_project(target)
        return {"routes": [route.as_dict() for route in graph.routes]}

    @app.tool()
    def list_external_dependencies(root: str = ".") -> dict[str, Any]:
        """List detected external dependencies and env hints."""
        target = Path(root).resolve()
        graph = scan_project(target)
        return {"external_services": [service.as_dict() for service in graph.external_services]}

    @app.tool()
    def audit_change_risk(root: str = ".", changed_files: list[str] | None = None) -> dict[str, Any]:
        """Estimate blast radius for changed files."""
        target = Path(root).resolve()
        graph = scan_project(target)
        return compute_change_risk(graph, changed_files or [])

    @app.tool()
    def audit_service(root: str = ".") -> dict[str, Any]:
        """Run generic service ontology audit rules."""
        target = Path(root).resolve()
        graph = scan_project(target)
        findings = audit_graph(graph)
        return {"score": score_findings(findings), "findings": [f.as_dict() for f in findings]}

    @app.tool()
    def validate_manifest(root: str = ".") -> dict[str, Any]:
        """Validate service-ontology.json/yaml manifest structure before scan."""
        target = Path(root).resolve()
        manifest = _load_manifest(target, validate=False)
        errors = validate_manifest(manifest) if manifest else ["service-ontology manifest not found"]
        return {"manifest_valid": not errors, "errors": errors}

    return app


def main() -> None:
    """Run FastMCP server."""
    app = create_app()
    app.run()


if __name__ == "__main__":
    main()
