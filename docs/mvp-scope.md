# MVP scope

`service-ontology-lite` starts as a generic, public-safe extraction from the 내집각 service ontology/audit workflow.

## Included

- Static route scanner for Next.js App Router conventions.
- Optional `service-ontology.json` manifest.
- Generic auth boundary audit rules.
- Generic entity/external dependency/job metadata.
- JSON CLI output.
- Minimal JSON-RPC stdio MCP server.

## Excluded

- Live production database introspection.
- Supabase schema details from 내집각.
- 청약 eligibility or switching calculations.
- Affiliate/commercial conversion scoring.
- Real cron token names and incident runbooks.
- SEO/GEO strategy rules.

## First useful agent flow

```text
1. Agent calls get_service_graph before editing.
2. Agent sees route auth/data/external dependency map.
3. Agent calls audit_change_risk with candidate changed files.
4. Agent avoids high-blast-radius edits without user review.
```
