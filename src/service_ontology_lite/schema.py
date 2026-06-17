from __future__ import annotations

from typing import Any

AUTH_VALUES = {"public", "required", "admin", "cron", "unknown"}
JOB_AUTH_VALUES = {"cron", "admin", "required"}
HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}

MANIFEST_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://veris.kr/schemas/service-ontology-lite.manifest.json",
    "title": "service-ontology-lite manifest",
    "type": "object",
    "additionalProperties": True,
    "properties": {
        "routes": {"type": "array"},
        "entities": {"type": "array"},
        "external_services": {"type": "array"},
        "jobs": {"type": "array"},
    },
}


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(manifest, dict):
        return ["manifest must be an object"]

    for index, item in enumerate(_items(manifest, "routes", errors)):
        prefix = f"routes[{index}]"
        _require_string(item, "path", prefix, errors)
        _require_string(item, "handler", prefix, errors)
        auth = item.get("auth", "unknown")
        if str(auth).lower() not in AUTH_VALUES:
            errors.append(f"{prefix}.auth must be one of {', '.join(sorted(AUTH_VALUES))}")
        path = item.get("path")
        if isinstance(path, str) and not path.startswith("/"):
            errors.append(f"{prefix}.path must start with /")
        methods = item.get("methods", [])
        if methods is not None:
            _validate_string_list(methods, f"{prefix}.methods", errors, allowed=HTTP_METHODS)
        _validate_string_list(item.get("entities", []), f"{prefix}.entities", errors)
        _validate_string_list(item.get("external_services", []), f"{prefix}.external_services", errors)

    for index, item in enumerate(_items(manifest, "entities", errors)):
        prefix = f"entities[{index}]"
        _require_string(item, "name", prefix, errors)
        _validate_string_list(item.get("fields", []), f"{prefix}.fields", errors)
        _validate_string_list(item.get("exposed_at", []), f"{prefix}.exposed_at", errors)

    for index, item in enumerate(_items(manifest, "external_services", errors)):
        prefix = f"external_services[{index}]"
        _require_string(item, "name", prefix, errors)
        _validate_string_list(item.get("env", []), f"{prefix}.env", errors)
        _validate_string_list(item.get("used_by", []), f"{prefix}.used_by", errors)

    for index, item in enumerate(_items(manifest, "jobs", errors)):
        prefix = f"jobs[{index}]"
        _require_string(item, "name", prefix, errors)
        _require_string(item, "handler", prefix, errors)
        auth = item.get("auth", "cron")
        if str(auth).lower() not in JOB_AUTH_VALUES:
            errors.append(f"{prefix}.auth must be cron/admin/required")

    return errors


def _items(manifest: dict[str, Any], key: str, errors: list[str]) -> list[dict[str, Any]]:
    value = manifest.get(key, [])
    if value is None:
        return []
    if not isinstance(value, list):
        errors.append(f"{key} must be an array")
        return []
    valid: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if isinstance(item, dict):
            valid.append(item)
        else:
            errors.append(f"{key}[{index}] must be an object")
    return valid


def _require_string(item: dict[str, Any], key: str, prefix: str, errors: list[str]) -> None:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{prefix}.{key} is required")


def _validate_string_list(value: Any, path: str, errors: list[str], allowed: set[str] | None = None) -> None:
    if value is None:
        return
    if not isinstance(value, list):
        errors.append(f"{path} must be an array")
        return
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item:
            errors.append(f"{path}[{index}] must be a non-empty string")
            continue
        if allowed is not None and item.upper() not in allowed:
            errors.append(f"{path}[{index}] must be one of {', '.join(sorted(allowed))}")
