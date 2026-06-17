# service-ontology-lite

**AI agents should not edit a web app before they know its routes, auth boundaries, data entities, external services, cron jobs, and blast radius.**

`service-ontology-lite` turns a small Next.js-style web app into a machine-readable service map, then exposes that map through a CLI and MCP server.

[![CI](https://github.com/verisworks-ai/service-ontology-lite/actions/workflows/ci.yml/badge.svg)](https://github.com/verisworks-ai/service-ontology-lite/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org)
[![MCP stdio](https://img.shields.io/badge/MCP-stdio-green.svg)](https://modelcontextprotocol.io)

> Current status: private staging repo. The package is being hardened for a later public release. Public-safe core code lives here; project-specific scoring, production schema, tokens, and incident runbooks stay outside the package.

---

## One-line result

```text
service-ontology-lite = service map + release audit + edit-risk guardrail for AI-coded web apps
```

## Why this exists

AI coding agents can change files quickly, but they often start without a service-level map.

This repo gives the agent a small, structured answer before it edits:

```text
What routes exist?
Which ones are public, authenticated, admin, or cron?
Which data entities and external services are nearby?
If this file changes, what is the blast radius?
```

## Positioning

```text
OpenCrab
→ document/domain knowledge ontology pack + Graph RAG + MCP platform

service-ontology-lite
→ developer-facing service structure audit + MCP guardrail for AI-coded web apps
```

## What you get

`service-ontology-lite` gives an AI coding agent a compact map of a web app before it edits code.

It answers five practical questions:

```text
Question                                      Output
Which routes exist?                           routes[] with path, handler, methods, auth
Which routes are public/auth/admin/cron?      auth boundary labels
Which data entities are touched?              entities[] and route-to-entity links
Which external services are in play?          external_services[] with env-name hints and used_by files
What is the blast radius of this edit?        LOW/MEDIUM/HIGH risk with impacted routes/services/jobs
```

This is useful when a project was built quickly, has scattered Next.js routes, and needs a machine-readable service map before another AI agent changes auth, API, cron, database, or integration code.

## What you can do with it

### 0. Run the agent preflight

```bash
service-ontology validate ./your-nextjs-app
service-ontology audit ./your-nextjs-app --json
service-ontology risk ./your-nextjs-app --changed app/api/admin/route.ts --json
```

Use this before handing a task to an AI coding agent. The result tells the agent whether the change is touching public routes, authenticated routes, admin routes, cron handlers, data entities, or external integrations.

### 1. Generate a service graph

```bash
service-ontology scan ./your-nextjs-app --json
```

Produces JSON for:

```text
- routes
- auth boundaries
- data entities
- external services
- scheduled jobs
- project metadata counts
```

### 2. Audit service structure before release

```bash
service-ontology audit ./your-nextjs-app --json
```

Flags generic issues such as:

```text
- route auth not declared
- sensitive-looking public route
- route references an undeclared entity
- external service env documentation with no usage
- scheduled job missing schedule metadata
```

### 3. Check edit risk before changing files

```bash
service-ontology risk ./your-nextjs-app --changed app/api/admin/route.ts --json
```

Example result class:

```text
severity: HIGH
reasons:
- admin_or_cron_route_changed
- external_dependency_touched
```

Use this as a pre-edit guardrail: if the touched file crosses admin, cron, auth, data, or external-service boundaries, require stricter review/test steps.

### 4. Add explicit project knowledge

Create `service-ontology.json`, `service-ontology.yaml`, or `service-ontology.yml` in the target app.

```json
{
  "routes": [
    {
      "path": "/dashboard",
      "auth": "required",
      "handler": "app/dashboard/page.tsx",
      "entities": ["User"],
      "external_services": []
    }
  ],
  "entities": [
    {
      "name": "User",
      "storage": "database:users",
      "fields": ["id", "email"],
      "exposed_at": ["/dashboard"]
    }
  ],
  "external_services": [],
  "jobs": []
}
```

Then validate it:

```bash
service-ontology validate ./your-nextjs-app
```

### 5. Expose the graph to AI agents through MCP

```bash
service-ontology-mcp ./your-nextjs-app
```

Agents can call MCP tools to inspect the app instead of guessing from filenames.

## Example dry-run result

Against the bundled sample app, the current release reports:

```text
scan route_count        5
external_services       Discord, Supabase
audit score             100
audit findings          0
risk admin route        HIGH
manifest_valid          true
MCP tools exposed       6
```

## Practical scenarios

### Scenario 1 — before an AI agent edits an admin route

```bash
service-ontology risk . --changed app/api/admin/route.ts --json
```

Expected signal:

```text
severity: HIGH
reason: admin_or_cron_route_changed
next step: require route-level tests and human review before merge
```

### Scenario 2 — before changing an integration file

```bash
service-ontology risk . --changed app/lib/supabase.ts --json
```

Expected signal:

```text
severity: HIGH when the file is linked to an external dependency
next step: check env names, failure mode, retry behavior, and release rollback path
```

### Scenario 3 — before public release

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
- authentication tests
- dependency vulnerability scanning
- SAST/DAST
- production penetration tests
- framework-specific type checking
- real database schema introspection
- runtime traffic analysis
```

The package is a static inspection layer. It does not execute the target app, open network connections, read `.env` values, or verify production authorization behavior.

## Install

Current private staging install:

```bash
python3 -m pip install "git+https://github.com/verisworks-ai/service-ontology-lite.git"
```

Local development install:

```bash
python3 -m pip install -e .
```

Planned public release install after hardening:

```bash
python3 -m pip install service-ontology-lite
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

## Public release checklist

This repo is private while the package is being prepared for public use.

Before switching visibility to public:

```text
1. Keep project-specific rules outside this package
2. Keep sample app synthetic, not copied from production
3. Verify wheel/sdist contain schema and no local state
4. Re-run compileall, pytest, ruff, build, and secret scan
5. Decide package registry path: PyPI or GitHub-only release
6. Normalize public-facing commit author if needed
7. Add public examples that do not expose production routes or runbooks
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
