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
