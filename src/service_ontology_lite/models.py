from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal

AuthLevel = Literal["public", "required", "admin", "cron", "unknown"]
Severity = Literal["HIGH", "MEDIUM", "LOW", "INFO"]


@dataclass
class Route:
    path: str
    auth: AuthLevel = "unknown"
    handler: str = ""
    methods: list[str] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)
    external_services: list[str] = field(default_factory=list)
    source: str = "static"

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class Entity:
    name: str
    storage: str = "unknown"
    fields: list[str] = field(default_factory=list)
    exposed_at: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class ExternalService:
    name: str
    type: str = "unknown"
    env: list[str] = field(default_factory=list)
    used_by: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class Job:
    name: str
    schedule: str = ""
    handler: str = ""
    auth: AuthLevel = "cron"

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class Finding:
    module: str
    severity: Severity
    type: str
    title: str
    detail: str
    file: str = ""
    fix: str = ""
    blast_radius: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class ServiceGraph:
    root: str
    routes: list[Route] = field(default_factory=list)
    entities: list[Entity] = field(default_factory=list)
    external_services: list[ExternalService] = field(default_factory=list)
    jobs: list[Job] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "root": self.root,
            "routes": [r.as_dict() for r in self.routes],
            "entities": [e.as_dict() for e in self.entities],
            "external_services": [s.as_dict() for s in self.external_services],
            "jobs": [j.as_dict() for j in self.jobs],
            "metadata": self.metadata,
        }


def score_findings(findings: list[Finding]) -> int:
    high = sum(1 for f in findings if f.severity == "HIGH")
    medium = sum(1 for f in findings if f.severity == "MEDIUM")
    low = sum(1 for f in findings if f.severity == "LOW")
    deduction = min(high * 10, 50) + min(medium * 4, 30) + min(low * 1, 20)
    return max(0, 100 - deduction)
