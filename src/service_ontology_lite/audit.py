from __future__ import annotations

from pathlib import Path

from .models import Finding, ServiceGraph


SENSITIVE_NAME_PARTS = ("secret", "token", "key", "password", "credential")


def audit_graph(graph: ServiceGraph) -> list[Finding]:
    findings: list[Finding] = []
    findings.extend(_audit_auth_boundaries(graph))
    findings.extend(_audit_entities(graph))
    findings.extend(_audit_external_services(graph))
    findings.extend(_audit_jobs(graph))
    return findings


def audit_change_risk(graph: ServiceGraph, changed_files: list[str]) -> dict:
    impacted_routes = []
    impacted_services = []
    impacted_jobs = []
    normalized = [f.replace("\\", "/") for f in changed_files]
    for route in graph.routes:
        if any(_matches_file(route.handler, changed) for changed in normalized):
            impacted_routes.append(route.as_dict())
    for service in graph.external_services:
        if any(_matches_file(used, changed) for used in service.used_by for changed in normalized):
            impacted_services.append(service.as_dict())
    for job in graph.jobs:
        if any(_matches_file(job.handler, changed) for changed in normalized):
            impacted_jobs.append(job.as_dict())

    severity = "LOW"
    reasons = []
    if any(r.get("auth") in {"admin", "cron"} for r in impacted_routes):
        severity = "HIGH"
        reasons.append("admin_or_cron_route_changed")
    elif any(r.get("auth") in {"required", "unknown"} for r in impacted_routes):
        severity = "MEDIUM"
        reasons.append("authenticated_or_unknown_route_changed")
    if impacted_services:
        severity = "HIGH" if severity == "MEDIUM" else severity
        reasons.append("external_dependency_touched")
    if impacted_jobs:
        severity = "HIGH"
        reasons.append("scheduled_job_touched")
    if not reasons:
        reasons.append("no_declared_blast_radius")

    return {
        "severity": severity,
        "reasons": reasons,
        "changed_files": changed_files,
        "impacted_routes": impacted_routes,
        "impacted_external_services": impacted_services,
        "impacted_jobs": impacted_jobs,
    }


def _audit_auth_boundaries(graph: ServiceGraph) -> list[Finding]:
    findings: list[Finding] = []
    for route in graph.routes:
        if route.auth == "unknown":
            findings.append(Finding(
                module="auth_boundary",
                severity="MEDIUM",
                type="unknown_route_auth",
                title=f"Auth boundary not declared: {route.path}",
                detail=f"Handler {route.handler} has no explicit auth classification.",
                file=route.handler,
                fix="Add service-ontology manifest auth: public|required|admin|cron.",
                blast_radius=[route.path],
            ))
        if route.auth == "public" and any(part in route.path.lower() for part in ("admin", "private", "internal")):
            findings.append(Finding(
                module="auth_boundary",
                severity="HIGH",
                type="public_sensitive_route",
                title=f"Sensitive-looking route is public: {route.path}",
                detail="Route path contains admin/private/internal but auth is public.",
                file=route.handler,
                fix="Change auth to admin/required or rename the route if it is intentionally public.",
                blast_radius=[route.path],
            ))
    return findings


def _audit_entities(graph: ServiceGraph) -> list[Finding]:
    findings: list[Finding] = []
    declared = {entity.name for entity in graph.entities}
    for route in graph.routes:
        for entity in route.entities:
            if entity not in declared:
                findings.append(Finding(
                    module="ontology_integrity",
                    severity="LOW",
                    type="undeclared_entity",
                    title=f"Route references undeclared entity: {entity}",
                    detail=f"{route.path} references {entity}, but entities[] has no matching declaration.",
                    file=route.handler,
                    fix="Add the entity to service-ontology manifest with storage and fields.",
                    blast_radius=[route.path],
                ))
    return findings


def _audit_external_services(graph: ServiceGraph) -> list[Finding]:
    findings: list[Finding] = []
    for service in graph.external_services:
        sensitive_env = [env for env in service.env if any(part.upper() in env.upper() for part in SENSITIVE_NAME_PARTS)]
        if sensitive_env and not service.used_by:
            findings.append(Finding(
                module="external_dependency",
                severity="LOW",
                type="unused_external_service",
                title=f"External service has env keys but no usage: {service.name}",
                detail=", ".join(sensitive_env),
                fix="Connect used_by handlers or remove stale env documentation.",
            ))
    return findings


def _audit_jobs(graph: ServiceGraph) -> list[Finding]:
    findings: list[Finding] = []
    for job in graph.jobs:
        if not job.schedule:
            findings.append(Finding(
                module="job_boundary",
                severity="MEDIUM",
                type="missing_job_schedule",
                title=f"Job schedule not declared: {job.name}",
                detail=f"Handler {job.handler} is declared as a job but has no schedule.",
                file=job.handler,
                fix="Add cron schedule metadata.",
                blast_radius=[job.name],
            ))
    return findings


def _matches_file(handler: str, changed: str) -> bool:
    if not handler:
        return False
    h = handler.replace("\\", "/").strip("/")
    c = str(Path(changed)).replace("\\", "/").strip("/")
    return h == c or h.endswith(c) or c.endswith(h)
