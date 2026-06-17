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

## CLI

```bash
service-ontology scan ./sample-app --json
service-ontology audit ./sample-app --json
service-ontology graph ./sample-app --json
service-ontology risk ./sample-app --changed app/api/admin/route.ts --json
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
