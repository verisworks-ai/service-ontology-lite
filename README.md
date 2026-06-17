# service-ontology-lite

A lightweight service ontology and audit MCP for vibe-coded web apps.

`service-ontology-lite` turns a small web app into a machine-readable service map before an AI agent edits it.
It records routes, auth boundaries, data entities, external dependencies, cron jobs, and risk findings.

## Positioning

```text
OpenCrab
→ document/domain knowledge ontology pack + Graph RAG + MCP platform

service-ontology-lite
→ developer-facing service structure audit + MCP guardrail for AI-coded web apps
```

## Install locally

```bash
python3 -m pip install -e .
```

No runtime dependency is required for the MVP.

## Release gate

Before publishing or pushing a release branch, run:

```bash
python3 -m compileall -q src tests
python3 -m pytest -q
python3 -m ruff check .
python3 -m build --sdist --wheel
```

The GitHub Actions workflow in `.github/workflows/ci.yml` runs the same gate on Python 3.11.

## CLI

```bash
service-ontology scan ./sample-app --json
service-ontology audit ./sample-app --json
service-ontology graph ./sample-app --json
service-ontology risk ./sample-app --changed app/api/admin/route.ts --json
service-ontology validate ./sample-app
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
```

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

## Next.js route support

The scanner understands common App Router path conventions:

```text
app/(marketing)/blog/[slug]/page.tsx       → /blog/:slug
app/docs/[...parts]/page.tsx               → /docs/:parts*
app/shop/[[...filters]]/route.ts           → /shop/:filters*
app/api/admin/route.ts                     → /api/admin
```

## Explicit manifest

Static scanning works without config. Add `service-ontology.yaml` for durable project knowledge:

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
```

Validate a manifest before sharing it with agents:

```bash
service-ontology validate ./sample-app
```

The JSON Schema reference is in `docs/service-ontology.schema.json`.
The same schema file is also included in the wheel as package data at
`service_ontology_lite/service-ontology.schema.json` so installed tools can reference the released schema without cloning the repository.

## Security model

`service-ontology-lite` is a static inspection and guardrail tool. It does not execute application code, open network connections, read `.env` files, or collect secret values. The scanner reads project files from the target directory and emits structural metadata: routes, declared auth boundaries, entities, external service names, cron handlers, and generic risk findings.

The tool is designed to flag risky edit boundaries before an AI coding agent changes a project. It is not a replacement for authentication tests, dependency scanning, SAST/DAST, or a production penetration test.

## Limitations

- Static route detection currently targets common Next.js App Router conventions.
- Manifest validation is intentionally lightweight and does not enforce every JSON Schema keyword at runtime.
- Risk scoring is generic; project-specific compliance, billing, affiliate, or incident rules should live in private plugins outside this package.
- The bundled sample app is a fixture for scanner and MCP verification, not a deployable production template.

## Public/private boundary

Public core:

```text
- schema
- CLI
- MCP stdio server
- generic scanner
- generic audit rules
- sample Next.js/Vercel app
- report format
```

Private project plugins stay outside the package:

```text
- domain-specific scoring
- live production database structure
- affiliate/commercial logic
- real cron tokens
- incident runbooks
- SEO/GEO monetization formulas
```
