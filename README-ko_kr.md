# service-ontology-lite · [![CI](https://github.com/verisworks-ai/service-ontology-lite-public/actions/workflows/ci.yml/badge.svg)](https://github.com/verisworks-ai/service-ontology-lite-public/actions/workflows/ci.yml) [![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org) [![MCP stdio](https://img.shields.io/badge/MCP-stdio-green.svg)](https://modelcontextprotocol.io) [![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)

[English](./README.md) | 한국어

AI 에이전트가 웹앱을 수정하기 전에 라우트, 인증 경계, 데이터 엔티티, 예약 작업, 외부 서비스를 구조화한다.

`service-ontology-lite`는 작은 Next.js 스타일 앱을 기계가 읽을 수 있는 서비스 맵으로 변환하고, 그 맵을 CLI와 MCP stdio 서버로 제공한다.

> 상태: private staging repo. 공개 가능한 핵심 코드만 이 저장소에 둔다. 프로젝트별 점수 규칙, 운영 스키마, 토큰, 장애 대응 문서는 패키지 밖에 둔다.

## 존재 이유

AI 코딩 에이전트는 파일을 빠르게 수정하지만, 수정 전에 서비스 구조를 모르는 상태에서 시작하는 경우가 많다.

이 패키지는 수정 전에 에이전트에게 짧은 구조 답변을 제공한다.

```text
어떤 라우트가 있는가?
어떤 라우트가 public, authenticated, admin, cron인가?
근처 데이터 엔티티와 외부 서비스는 무엇인가?
이 파일을 바꾸면 영향 범위는 어디까지인가?
```

## 반환 정보

```text
질문                                         출력
어떤 라우트가 있는가?                         path, handler, methods, auth가 포함된 routes[]
public/auth/admin/cron 경계는 무엇인가?       인증 경계 라벨
어떤 데이터 엔티티를 건드리는가?               entities[] 및 route-to-entity 링크
어떤 외부 서비스를 쓰는가?                    external_services[] 및 env-name 힌트, used_by 파일
수정 영향 범위는 어느 정도인가?                영향 라우트/서비스/작업이 포함된 LOW/MEDIUM/HIGH risk
```

## 설치

현재 private staging 설치:

```bash
python3 -m pip install "git+https://github.com/verisworks-ai/service-ontology-lite-public.git"
```

로컬 개발 설치:

```bash
python3 -m pip install -e .
```

공개 릴리스 후 예정 설치:

```bash
python3 -m pip install service-ontology-lite
```

MVP 런타임 의존성은 없다.

## 30초 예제

```bash
service-ontology validate ./your-nextjs-app
service-ontology audit ./your-nextjs-app --json
service-ontology risk ./your-nextjs-app --changed app/api/admin/route.ts --json
```

AI 코딩 에이전트에게 작업을 넘기기 전에 실행한다. 결과는 수정 대상이 public route, authenticated route, admin route, cron handler, data entity, external integration 중 어디를 건드리는지 알려준다.

## CLI

```bash
service-ontology --version   # 또는: service-ontology -V
service-ontology scan ./sample-app --json
service-ontology audit ./sample-app --json
service-ontology graph ./sample-app --json
service-ontology agent-os ./sample-app --json
service-ontology agent-os ./sample-app --project-context service-ontology-lite --json
service-ontology risk ./sample-app --changed app/api/admin/route.ts --json
service-ontology validate ./sample-app
```

명령:

```text
scan       라우트, 인증 경계, 엔티티, 외부 서비스, 작업 생성
--version  설치된 패키지 버전 출력
validate   service-ontology.json/yaml 메타데이터 검증
risk       변경 파일의 서비스 영향 범위 분류
audit      누락된 auth/entity/job/service 메타데이터 점검
graph      통합 서비스 그래프 반환
agent-os   Agent OS registry와 project_context 그룹 반환
```

## MCP 서버

```bash
service-ontology-mcp ./sample-app
```

지원 MCP 도구:

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

`agent-os`와 `list_project_contexts`는 단일 프로젝트 인계 컨텍스트만 반환하도록 `project_context_id` 필터를 받는다.

Hermes Agent MCP 설정 예시:

```yaml
mcp_servers:
  service_ontology:
    command: "service-ontology-mcp"
    args: ["/absolute/path/to/your-nextjs-app"]
    timeout: 60
    connect_timeout: 30
```

등록 후 AI 에이전트는 라우트를 수정하기 전에 `audit_change_risk`를 호출해 해당 파일이 public, admin, cron, data, external-service 경계를 넘는지 확인한다.

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

## 샘플 앱 dry-run 결과

번들된 sample app 기준 현재 릴리스 결과:

```text
scan route_count        5
external_services       Discord, Supabase
audit score             100
audit findings          0
risk admin route        HIGH
manifest_valid          true
MCP tools exposed       8
```

## Next.js 라우트 지원

스캐너는 흔한 App Router 경로 규칙을 이해한다.

```text
app/(marketing)/blog/[slug]/page.tsx       → /blog/:slug
app/docs/[...parts]/page.tsx               → /docs/:parts*
app/shop/[[...filters]]/route.ts           → /shop/:filters*
app/api/admin/route.ts                     → /api/admin
```

## 명시적 manifest

정적 스캔은 설정 없이 작동한다. 프로젝트 지식을 명시하려면 `service-ontology.json`, `service-ontology.yaml`, `service-ontology.yml`을 추가한다.

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

에이전트에게 공유하기 전에 manifest를 검증한다.

```bash
service-ontology validate ./sample-app
```

JSON Schema 참조는 `docs/service-ontology.schema.json`에 있다. 같은 스키마 파일은 wheel 안에도 `service_ontology_lite/service-ontology.schema.json` 경로로 포함된다.

## 사용 시나리오

### AI 에이전트가 admin route를 수정하기 전

```bash
service-ontology risk . --changed app/api/admin/route.ts --json
```

예상 신호:

```text
severity: HIGH
reason: admin_or_cron_route_changed
next step: merge 전 route-level test와 human review 필요
```

### integration 파일을 바꾸기 전

```bash
service-ontology risk . --changed app/lib/supabase.ts --json
```

예상 신호:

```text
severity: 파일이 외부 의존성과 연결되어 있으면 HIGH
next step: env 이름, 실패 모드, retry 동작, rollback 경로 확인
```

### 공개 릴리스 전

```bash
service-ontology validate .
service-ontology audit . --json
```

예상 신호:

```text
manifest_valid: true
finding_count: 0 또는 명시적으로 검토된 finding
```

## 적합한 사용처

```text
사용처                                       효과
작은 Next.js 앱 배포 전 점검                  validate + audit + risk 실행
AI 코딩 guardrail                            에이전트에게 route/auth/service map 선제 제공
비공개 앱 문서화                              service-ontology.json을 소스 옆에 유지
리팩터링 계획                                 어떤 route/entity/service가 영향받는지 확인
Cron/API 안전성 리뷰                          admin/cron/external-service 수정 HIGH 분류
MCP 실험                                      앱 런타임 의존성 없이 stdio로 service graph 제공
```

## 대체하지 않는 것

```text
authentication test
dependency vulnerability scanning
SAST/DAST
production penetration test
framework-specific type checking
real database schema introspection
runtime traffic analysis
```

이 패키지는 정적 검사 계층이다. 대상 앱을 실행하지 않고, 네트워크 연결을 열지 않고, `.env` 값을 읽지 않고, 운영 권한 동작을 검증하지 않는다.

## 릴리스 게이트

publish 또는 release branch push 전 실행:

```bash
python3 -m compileall -q src tests
python3 -m pytest -q
python3 -m ruff check .
python3 -m build --sdist --wheel
```

`.github/workflows/ci.yml`의 GitHub Actions workflow가 Python 3.11에서 같은 게이트를 실행한다.

## 보안 모델

`service-ontology-lite`는 정적 검사 및 guardrail 도구다. 대상 디렉터리의 프로젝트 파일을 읽고 라우트, 선언된 인증 경계, 엔티티, 외부 서비스 이름, cron handler, 일반 risk finding 같은 구조 메타데이터를 출력한다.

애플리케이션 코드를 실행하지 않고, 네트워크 연결을 열지 않고, `.env` 파일을 읽지 않고, secret 값을 수집하지 않는다.

## 공개/비공개 경계

공개 core:

```text
schema
CLI
MCP stdio server
generic scanner
generic audit rules
sample Next.js/Vercel app
report format
```

비공개 프로젝트 plugin은 패키지 밖에 둔다.

```text
domain-specific scoring
live production database structure
affiliate/commercial logic
real cron tokens
incident runbooks
SEO/GEO monetization formulas
```

## 기여

영문 가이드: [CONTRIBUTING](./.github/CONTRIBUTING.md). 한국어 가이드: [CONTRIBUTING-ko_kr](./.github/CONTRIBUTING-ko_kr.md).

## 라이선스

MIT. [LICENSE](./LICENSE)를 확인한다.
