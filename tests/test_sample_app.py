from __future__ import annotations

from service_ontology_lite.audit import audit_change_risk, audit_graph
from service_ontology_lite.scanner import scan_project


def test_scan_sample_app_counts():
    graph = scan_project("sample-app")
    assert graph.metadata["route_count"] >= 4
    paths = {route.path for route in graph.routes}
    assert "/dashboard" in paths
    assert "/api/admin" in paths
    assert any(service.name == "Discord" for service in graph.external_services)


def test_audit_sample_app_has_no_unknown_manifest_auth():
    graph = scan_project("sample-app")
    findings = audit_graph(graph)
    unknown = [finding for finding in findings if finding.type == "unknown_route_auth"]
    assert unknown == []


def test_change_risk_admin_route_is_high():
    graph = scan_project("sample-app")
    risk = audit_change_risk(graph, ["app/api/admin/route.ts"])
    assert risk["severity"] == "HIGH"
    assert "admin_or_cron_route_changed" in risk["reasons"]
