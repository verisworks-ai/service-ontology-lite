from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import Entity, ExternalService, Job, Route, ServiceGraph
from .schema import validate_manifest

_ROUTE_FILE_NAMES = {"page.tsx", "page.ts", "page.jsx", "page.js", "route.ts", "route.js"}
_SECRET_HINTS = {
    "STRIPE": ("Stripe", "payments"),
    "SUPABASE": ("Supabase", "database"),
    "DATABASE_URL": ("Database", "database"),
    "OPENAI": ("OpenAI", "llm"),
    "ANTHROPIC": ("Anthropic", "llm"),
    "RESEND": ("Resend", "email"),
    "DISCORD": ("Discord", "notification"),
    "SLACK": ("Slack", "notification"),
    "VERCEL": ("Vercel", "hosting"),
    "GOOGLE": ("Google", "platform"),
    "NAVER": ("Naver", "platform"),
}


def scan_project(root: str | Path) -> ServiceGraph:
    project_root = Path(root).resolve()
    graph = ServiceGraph(root=str(project_root))
    manifest = _load_manifest(project_root)
    if manifest:
        _apply_manifest(graph, manifest)

    route_files = sorted(p for p in project_root.rglob("*") if p.is_file() and p.name in _ROUTE_FILE_NAMES)
    known_handlers = {r.handler for r in graph.routes if r.handler}
    for route_file in route_files:
        rel = route_file.relative_to(project_root).as_posix()
        if rel in known_handlers:
            continue
        content = _safe_read(route_file)
        graph.routes.append(_route_from_file(project_root, route_file, content))

    _infer_external_services(graph, project_root)
    _infer_entities(graph, project_root)
    _dedupe_graph(graph)
    graph.metadata.update({
        "route_count": len(graph.routes),
        "entity_count": len(graph.entities),
        "external_service_count": len(graph.external_services),
        "job_count": len(graph.jobs),
    })
    return graph


def _load_manifest(root: Path, *, validate: bool = True) -> dict[str, Any]:
    for name in ("service-ontology.json", "service-ontology.yaml", "service-ontology.yml"):
        path = root / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".json":
            manifest = json.loads(text)
        else:
            manifest = _parse_tiny_yaml(text)
        if validate:
            errors = validate_manifest(manifest)
            if errors:
                raise ValueError("Invalid service ontology manifest: " + "; ".join(errors))
        return manifest
    return {}


def _parse_tiny_yaml(text: str) -> dict[str, Any]:
    """Small YAML subset parser for this MVP: top-level lists of flat maps."""
    result: dict[str, Any] = {}
    current_key = ""
    current_item: dict[str, Any] | None = None
    for raw in text.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not raw.startswith(" ") and stripped.endswith(":"):
            current_key = stripped[:-1]
            result[current_key] = []
            current_item = None
            continue
        if stripped.startswith("- ") and current_key:
            current_item = {}
            result[current_key].append(current_item)
            remainder = stripped[2:]
            if ":" in remainder:
                key, value = remainder.split(":", 1)
                current_item[key.strip()] = _parse_scalar(value.strip())
            continue
        if current_item is not None and ":" in stripped:
            key, value = stripped.split(":", 1)
            current_item[key.strip()] = _parse_scalar(value.strip())
    return result


def _parse_scalar(value: str) -> Any:
    value = value.strip().strip('"').strip("'")
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [x.strip().strip('"').strip("'") for x in inner.split(",")]
    return value


def _apply_manifest(graph: ServiceGraph, manifest: dict[str, Any]) -> None:
    for item in manifest.get("routes", []):
        graph.routes.append(Route(
            path=str(item.get("path", "")),
            auth=_normalize_auth(item.get("auth", "unknown")),
            handler=str(item.get("handler", "")),
            methods=_list(item.get("methods", [])),
            entities=_list(item.get("entities", [])),
            external_services=_list(item.get("external_services", [])),
            source="manifest",
        ))
    for item in manifest.get("entities", []):
        graph.entities.append(Entity(
            name=str(item.get("name", "")),
            storage=str(item.get("storage", "unknown")),
            fields=_list(item.get("fields", [])),
            exposed_at=_list(item.get("exposed_at", [])),
        ))
    for item in manifest.get("external_services", []):
        graph.external_services.append(ExternalService(
            name=str(item.get("name", "")),
            type=str(item.get("type", "unknown")),
            env=_list(item.get("env", [])),
            used_by=_list(item.get("used_by", [])),
        ))
    for item in manifest.get("jobs", []):
        graph.jobs.append(Job(
            name=str(item.get("name", "")),
            schedule=str(item.get("schedule", "")),
            handler=str(item.get("handler", "")),
            auth=_normalize_auth(item.get("auth", "cron")),
        ))


def _route_from_file(root: Path, file: Path, content: str) -> Route:
    rel = file.relative_to(root).as_posix()
    path = _path_from_app_file(rel)
    auth = _auth_from_content(path, content)
    methods = [
        m
        for m in ["GET", "POST", "PUT", "PATCH", "DELETE"]
        if f"export async function {m}" in content or f"export function {m}" in content
    ]
    if file.name.startswith("page") and not methods:
        methods = ["GET"]
    route = Route(path=path, auth=auth, handler=rel, methods=methods, source="static")
    lower = content.lower()
    for entity_hint in ["user", "profile", "session", "order", "post", "notice", "payment"]:
        if entity_hint in lower:
            route.entities.append(entity_hint.title())
    return route


def _path_from_app_file(rel: str) -> str:
    parts = rel.split("/")
    if "app" in parts:
        parts = parts[parts.index("app") + 1:]
    if parts and parts[-1] in _ROUTE_FILE_NAMES:
        parts = parts[:-1]
    segments = []
    for part in parts:
        if part.startswith("(") and part.endswith(")"):
            continue
        if part.startswith("[[...") and part.endswith("]]"):
            segments.append(":" + part[5:-2] + "*")
        elif part.startswith("[...") and part.endswith("]"):
            segments.append(":" + part[4:-1] + "*")
        elif part.startswith("[") and part.endswith("]"):
            segments.append(":" + part[1:-1])
        else:
            segments.append(part)
    return "/" + "/".join(segments) if segments else "/"


def _auth_from_content(path: str, content: str):
    lower = content.lower()
    if "admin" in path or "admin" in lower:
        return "admin"
    if "cron" in path or "cron" in lower or "authorization" in lower:
        return "cron"
    if "getserversession" in lower or "requireauth" in lower or "session" in lower or "auth" in lower:
        return "required"
    if path.startswith("/api/"):
        return "unknown"
    return "public"


def _infer_external_services(graph: ServiceGraph, root: Path) -> None:
    services: dict[str, ExternalService] = {s.name: s for s in graph.external_services if s.name}
    for file in root.rglob("*"):
        if not file.is_file() or file.suffix.lower() not in {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".json"}:
            continue
        content = _safe_read(file)
        rel = file.relative_to(root).as_posix()
        for hint, (name, kind) in _SECRET_HINTS.items():
            if hint in content:
                service = services.setdefault(name, ExternalService(name=name, type=kind))
                if hint not in service.env and hint.isupper():
                    service.env.append(hint)
                if rel not in service.used_by:
                    service.used_by.append(rel)
    graph.external_services = sorted(services.values(), key=lambda s: s.name)


def _infer_entities(graph: ServiceGraph, root: Path) -> None:
    names = {e.name for e in graph.entities}
    for route in graph.routes:
        for name in route.entities:
            if name and name not in names:
                graph.entities.append(Entity(name=name, storage="inferred", exposed_at=[route.path]))
                names.add(name)


def _dedupe_graph(graph: ServiceGraph) -> None:
    route_map: dict[str, Route] = {}
    for route in graph.routes:
        if not route.path:
            continue
        if route.path in route_map and route_map[route.path].source == "manifest":
            continue
        route_map[route.path] = route
    graph.routes = sorted(route_map.values(), key=lambda r: r.path)

    entity_map = {e.name: e for e in graph.entities if e.name}
    graph.entities = sorted(entity_map.values(), key=lambda e: e.name)


def _safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def _normalize_auth(value: Any):
    auth = str(value).lower()
    if auth in {"public", "required", "admin", "cron", "unknown"}:
        return auth
    if auth in {"private", "authenticated", "auth"}:
        return "required"
    return "unknown"


def _list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]
