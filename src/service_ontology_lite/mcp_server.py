from __future__ import annotations

from pathlib import Path
from typing import Any

import fastmcp

from .audit import audit_change_risk as compute_change_risk
from .audit import audit_graph
from .models import score_findings
from .scanner import _load_manifest, scan_project
from .schema import validate_manifest as _validate_schema

# Default root for scanning
DEFAULT_ROOT = Path.cwd()


def _read_only_annotations(title: str) -> dict[str, Any]:
    return {
        "title": title,
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }


def create_app() -> fastmcp.FastMCP:
    """Create FastMCP app with tool handlers."""
    app = fastmcp.FastMCP("service-ontology-lite", version="0.1.0")

    @app.tool(
        description="서비스 안전점검 온톨로지 엔진: 서비스의 경로, 엔티티, 외부 의존성을 조회합니다.",
        annotations=_read_only_annotations("서비스 그래프 조회"),
    )
    def get_service_graph(root: str = ".") -> dict[str, Any]:
        """Return routes, entities, external services, jobs, and metadata."""
        target = Path(root).resolve()
        graph = scan_project(target)
        return graph.as_dict()

    @app.tool(
        description="서비스 안전점검 온톨로지 엔진: 모든 서비스 경로를 인증 경계와 핸들러 정보와 함께 조회합니다.",
        annotations=_read_only_annotations("서비스 경로 목록"),
    )
    def list_routes(root: str = ".") -> dict[str, Any]:
        """List service routes with auth boundaries and handlers."""
        target = Path(root).resolve()
        graph = scan_project(target)
        return {"routes": [route.as_dict() for route in graph.routes]}

    @app.tool(
        description="서비스 안전점검 온톨로지 엔진: 감지된 외부 의존성과 환경 변수 힌트를 조회합니다.",
        annotations=_read_only_annotations("외부 의존성 목록"),
    )
    def list_external_dependencies(root: str = ".") -> dict[str, Any]:
        """List detected external dependencies and env hints."""
        target = Path(root).resolve()
        graph = scan_project(target)
        return {"external_services": [service.as_dict() for service in graph.external_services]}

    @app.tool(
        description="서비스 안전점검 온톨로지 엔진: 변경된 파일의 영향 범위(blast radius)를 추정합니다.",
        annotations=_read_only_annotations("변경 위험도 감사"),
    )
    def audit_change_risk(root: str = ".", changed_files: list[str] | None = None) -> dict[str, Any]:
        """Estimate blast radius for changed files."""
        target = Path(root).resolve()
        graph = scan_project(target)
        return compute_change_risk(graph, changed_files or [])

    @app.tool(
        description="서비스 안전점검 온톨로지 엔진: 일반적인 서비스 온톨로지 감사 규칙을 실행합니다.",
        annotations=_read_only_annotations("서비스 감사"),
    )
    def audit_service(root: str = ".") -> dict[str, Any]:
        """Run generic service ontology audit rules."""
        target = Path(root).resolve()
        graph = scan_project(target)
        findings = audit_graph(graph)
        return {"score": score_findings(findings), "findings": [f.as_dict() for f in findings]}

    @app.tool(
        description="서비스 안전점검 온톨로지 엔진: 스캔 전 service-ontology.json/yaml 매니페스트 구조를 검증합니다.",
        annotations=_read_only_annotations("매니페스트 검증"),
    )
    def validate_manifest(root: str = ".") -> dict[str, Any]:
        """Validate service-ontology.json/yaml manifest structure before scan."""
        target = Path(root).resolve()
        manifest = _load_manifest(target, validate=False)
        errors = _validate_schema(manifest) if manifest else ["service-ontology manifest not found"]
        return {"manifest_valid": not errors, "errors": errors}

    return app


def main() -> None:
    """Run FastMCP server."""
    app = create_app()
    app.run()


if __name__ == "__main__":
    main()
