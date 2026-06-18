# service-ontology-lite · [![CI](https://github.com/verisworks-ai/service-ontology-lite-public/actions/workflows/ci.yml/badge.svg)](https://github.com/verisworks-ai/service-ontology-lite-public/actions/workflows/ci.yml) [![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org) [![MCP stdio](https://img.shields.io/badge/MCP-stdio-green.svg)](https://modelcontextprotocol.io) [![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)

English | [한국어](./README-ko_kr.md)

Map routes, auth boundaries, data entities, scheduled jobs, and external services before an AI agent edits a web app.

`service-ontology-lite` turns a small Next.js-style app into a machine-readable service map, then exposes that map through a CLI and MCP stdio server.

> Status: private staging repo. Public-safe core code lives here. Project-specific scoring, production schema, tokens, and incident runbooks stay outside this package.

## Why this exists

AI coding agents can change files quickly, but they often start without a service-level map.

This package gives the agent a compact answer before it edits:

```text
What routes exist?
Which routes are public, authenticated, admin, or cron?
Which data entities and external services are nearby?
If this file changes, what is the blast radius?
```

## What it returns

```text
Question                                      Output
Which routes exist?                           routes[] with path, handler, methods, auth
Which routes are public/auth/admin/cron?      auth boundary labels
Which data entities are touched?              entities[] and route-to-entity links
Which external services are in play?          external_services[] with env-name hints and used_by files
What is the blast radius of this edit?        LOW/MEDIUM/HIGH risk with impacted routes/services/jobs
```

## Install

Current private staging install:

```bash
python3 -m pip install "git+https://github.com/verisworks-ai/service-ontology-lite-public.git"
```

Local development install:

```bash
python3 -m pip install -e .
```

Planned public release install after hardening:

```bash
python3 -m pip install service-ontology-lite
```

The MVP has no runtime dependency.

## 30-second example

```bash
service-ontology validate ./your-nextjs-app
service-ontology audit ./your-nextjs-app --json
service-ontology risk ./your-nextjs-app --changed app/api/admin/route.ts --json
```

Use this before handing a task to an AI coding agent. The result tells the agent whether the change touches public routes, authenticated routes, admin routes, cron handlers, data entities, or external integrations.

## CLI

```bash
service-ontology --version   # or: service-ontology -V
service-ontology scan ./sample-app --json
service-ontology audit ./sample-app --json
service-ontology graph ./sample-app --json
service-ontology agent-os ./sample-app --json
service-ontology agent-os ./sample-app --project-context service-ontology-lite --json
service-ontology risk ./sample-app --changed app/api/admin/route.ts --json
service-ontology validate ./sample-app
```

Commands:

```text
scan       Generate routes, auth boundaries, entities, external services, and jobs
--version  Print installed package version
validate   Validate service-ontology.json/yaml metadata
risk       Classify changed files by service blast radius
audit      Flag missing auth/entity/job/service metadata
graph      Return the combined service graph
agent-os   Return Agent OS registry and project_context grouping
```

## MCP server

```bash
service-ontology-mcp ./sample-app
```

Supported MCP tools:

```text
get_service_graph
list_routes
list_external_dependencies
audit_change_risk
audit_service
validate_manifest
get_agent_os_graph
list_project_contexts
```

`agent-os` and `list_project_contexts` accept `project_context_id` filtering for a single project handoff context.

Hermes Agent MCP config example:

```yaml
mcp_servers:
  service_ontology:
    command: "service-ontology-mcp"
    args: ["/absolute/path/to/your-nextjs-app"]
    timeout: 60
    connect_timeout: 30
```

When registered, an AI agent can call `audit_change_risk` before editing a route and see whether the touched file crosses public, admin, cron, data, or external-service boundaries.

## Python API

```python
from service_ontology_lite import (
    audit_change_risk,
    filter_project_contexts,
    load_agent_os_registry,
    scan_project,
    validate_manifest,
)

registry = load_agent_os_registry("./sample-app")
project_context = filter_project_contexts(registry, "service-ontology-lite")
```

## Example dry-run result

Against the bundled sample app, the current release reports:

```text
scan route_count        5
external_services       Discord, Supabase
audit score             100
audit findings          0
risk admin route        HIGH
manifest_valid          true
MCP tools exposed       8
```

## Next.js route support

The scanner understands common App Router path conventions:

```text
app/(marketing)/blog/[slug]/page.tsx       → /blog/:slug
app/docs/[...parts]/page.tsx               → /docs/:parts*
app/shop/[[...filters]]/route.ts           → /shop/:filters*
app/api/admin/route.ts                     → /api/admin
```

## Explicit manifest

Static scanning works without config. Add `service-ontology.json`, `service-ontology.yaml`, or `service-ontology.yml` for durable project knowledge:

```yaml
routes:
  - path: /dashboard
    auth: required
    handler: app/dashboard/page.tsx
    entities: [User]
    external_services: []
entities:
  - name: User
    storage: database:users
    fields: [id, email]
external_services:
  - name: Stripe
    type: payments
    env: [STRIPE_SECRET_KEY]
jobs:
  - name: daily-sync
    schedule: "0 0 * * *"
    handler: app/api/cron/route.ts
agent_os:
  projects:
    - id: service-ontology-lite
      name: service-ontology-lite sample
  agents:
    - id: implementation-agent
      role: implementation
  surfaces:
    - id: local-sample-app
      type: local_repo
      project_context_id: service-ontology-lite
  tasks:
    - id: agent-os-registry-poc
      project_context_id: service-ontology-lite
      owner_agent: implementation-agent
  artifacts:
    - id: pytest-agent-os-registry
      type: test_output
      project_context_id: service-ontology-lite
```

Validate a manifest before sharing it with agents:

```bash
service-ontology validate ./sample-app
```

The JSON Schema reference is in `docs/service-ontology.schema.json`. The same schema file is included in the wheel as package data at `service_ontology_lite/service-ontology.schema.json`.

## Practical scenarios

### Before an AI agent edits an admin route

```bash
service-ontology risk . --changed app/api/admin/route.ts --json
```

Expected signal:

```text
severity: HIGH
reason: admin_or_cron_route_changed
next step: require route-level tests and human review before merge
```

### Before changing an integration file

```bash
service-ontology risk . --changed app/lib/supabase.ts --json
```

Expected signal:

```text
severity: HIGH when the file is linked to an external dependency
next step: check env names, failure mode, retry behavior, and release rollback path
```

### Before public release

```bash
service-ontology validate .
service-ontology audit . --json
```

Expected signal:

```text
manifest_valid: true
finding_count: 0 or reviewed findings with explicit fixes
```

## Good use cases

```text
Use case                                      How this repo helps
Pre-release check for a small Next.js app      Run validate + audit + risk before deploy
AI coding guardrail                            Give agents a route/auth/service map first
Private app documentation                      Keep service-ontology.json beside source
Refactor planning                              See which routes/entities/services are touched
Cron/API safety review                         Flag admin/cron/external-service edits as high risk
MCP experiment                                 Serve service graph over stdio without app runtime dependencies
```

## Not a replacement for

```text
authentication tests
dependency vulnerability scanning
SAST/DAST
production penetration tests
framework-specific type checking
real database schema introspection
runtime traffic analysis
```

The package is a static inspection layer. It does not execute the target app, open network connections, read `.env` values, or verify production authorization behavior.

## Release gate

Before publishing or pushing a release branch, run:

```bash
python3 -m compileall -q src tests
python3 -m pytest -q
python3 -m ruff check .
python3 -m build --sdist --wheel
```

The GitHub Actions workflow in `.github/workflows/ci.yml` runs the same gate on Python 3.11.

## Security model

`service-ontology-lite` is a static inspection and guardrail tool. It reads project files from the target directory and emits structural metadata: routes, declared auth boundaries, entities, external service names, cron handlers, and generic risk findings.

It does not execute application code, open network connections, read `.env` files, or collect secret values.

## Public/private boundary

Public core:

```text
schema
CLI
MCP stdio server
generic scanner
generic audit rules
sample Next.js/Vercel app
report format
```

Private project plugins stay outside the package:

```text
domain-specific scoring
live production database structure
affiliate/commercial logic
real cron tokens
incident runbooks
SEO/GEO monetization formulas
```

## Contributing

See [CONTRIBUTING](./.github/CONTRIBUTING.md). Korean guide: [CONTRIBUTING-ko_kr](./.github/CONTRIBUTING-ko_kr.md).

## License

MIT. See [LICENSE](./LICENSE).
