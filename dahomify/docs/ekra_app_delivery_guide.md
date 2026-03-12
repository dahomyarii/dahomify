# ekra.app Delivery Guide

This is the complete implementation guide for shipping, testing, operating, and improving `ekra.app` with `dahomify`.

It answers three practical questions:

1. Where should the real CI/CD live?
2. What should be tested and when?
3. What documents, tools, and runbooks are required to operate the app professionally?

## Executive Decision

For `ekra.app`, the best setup is:

- keep the real application CI/CD, deployment workflows, tests, and infrastructure code in the `ekra.app` application repository
- keep reusable standards, quality policy, and reference documentation in `dahomify`

Do not keep the real production pipeline only inside `dahomify`, and do not put the live app pipeline in a separate orchestration-only repo unless there is a strong platform-engineering reason.

### Why this is the recommended structure

- pull request checks must run against the actual application code that changed
- website, API, migration, and worker checks need direct access to the real repo contents
- preview deployments work best when they are triggered by the same PR that changed the app
- keeping CI somewhere else creates drift between documentation and reality
- `dahomify` is best used as the shared quality engine and delivery standard

## Recommended Repo Strategy

### `dahomify` should contain

- CI/CD standards
- reusable workflow templates
- quality-gate policy
- command runbooks
- agent guidance
- documentation for how to adopt Dahomify in app repos

### `ekra.app` should contain

- `.github/workflows/*`
- Dockerfiles and `docker-compose.yml`
- frontend tests
- backend tests
- API contract tests
- Playwright browser tests
- deployment manifests or Terraform
- environment templates
- service-specific runbooks

### Optional separate infra repo

Use a separate infrastructure repo only if:

- the team manages many applications with shared platform modules
- Terraform ownership is already centralized
- application engineers and platform engineers intentionally work in separate delivery tracks

Even in that model, the app repo should still own:

- PR validation
- application build
- smoke tests
- quality gates
- release metadata

## Documentation Set

For a professional `ekra.app` setup, keep this documentation set complete:

- `docs/ci_plan.md`
- `docs/ekra_app_delivery_guide.md`
- `SHARIKLY_COMMANDS.md`
- application repo `README.md`
- deployment runbook
- rollback runbook
- incident response runbook
- environment matrix
- secrets and access policy
- testing strategy and ownership

## System Scope

The plan assumes `ekra.app` includes:

- a frontend website
- a backend API
- PostgreSQL
- Redis
- asynchronous jobs or workers
- object/file storage if uploads exist
- staging and production environments

If the stack differs, the same structure still applies; only the implementation details change.

## Environment Strategy

Use these environments:

- `local`
- `dev`
- `staging`
- `production`

### Local

Purpose:

- developer productivity
- feature validation
- fast smoke testing

Requirements:

- Docker Compose parity where possible
- local frontend and backend startup commands
- seeded or fixture data
- optional worker and scheduler startup

### Dev

Purpose:

- shared integration testing
- QA verification for incomplete work

Requirements:

- cheap to redeploy
- no production data
- stable URLs
- isolated secrets and services

### Staging

Purpose:

- production-like release candidate validation

Requirements:

- same runtime shape as production
- same deployment method as production
- same migration process as production
- realistic monitoring and alerting
- browser and API post-deploy smoke tests

### Production

Purpose:

- live traffic

Requirements:

- safe deploy strategy
- rollback path
- backup policy
- dashboards and alerts
- deployment approvals where needed

## Delivery Workflow

### Pull request workflow

Every pull request should trigger:

1. dependency installation and caching
2. frontend lint
3. frontend typecheck
4. backend lint
5. backend tests
6. frontend unit tests
7. API contract tests
8. Docker build verification
9. Dahomify scan and quality checks
10. Playwright smoke tests
11. artifact upload for logs, traces, reports, and screenshots

### Merge to main

On merge to `main`:

1. rerun required CI if needed
2. build immutable image tags
3. deploy to `staging`
4. run migrations
5. run post-deploy smoke tests
6. run synthetic checks
7. mark the release candidate for promotion

### Production promotion

Use manual approval or release-tag promotion:

1. promote the same tested image digest from staging
2. take a backup or snapshot before migration
3. deploy with blue/green or canary when possible
4. run production smoke tests immediately
5. monitor for regression signals
6. rollback automatically or manually on failure

## Full Testing Strategy

### Frontend test layers

- linting
- type checking
- unit tests
- component tests
- Playwright end-to-end tests
- Lighthouse performance budget checks on critical pages

Critical website flows:

- home page load
- authentication
- browse/search/listing discovery
- listing detail
- form submission or conversion path
- user dashboard or account path if present

### Backend and API test layers

- framework health checks
- unit tests
- integration tests with PostgreSQL and Redis
- authentication and authorization tests
- serializer/schema validation
- API contract tests
- idempotency tests for unsafe writes
- migration safety tests
- management command smoke tests if used

Critical API flows:

- auth login and token/session lifecycle
- listing read endpoints
- listing create/update/delete endpoints if applicable
- file upload endpoints if applicable
- payment or order endpoints if applicable
- health endpoints

### Runtime and platform tests

- Docker Compose smoke startup
- worker task execution
- scheduled job execution
- cache connectivity
- object storage smoke tests
- external dependency connectivity checks

### Post-deploy smoke tests

After staging and production deployments, validate:

- frontend URL returns success
- API health endpoint returns success
- one authenticated request path works
- database-backed read works
- queue-backed async flow works if applicable
- no immediate error spike in Sentry or logs

## Dahomify Operating Model

Use `dahomify` as a permanent quality gate.

### Required recurring commands

```bash
dahomify scan --path .
dahomify status
dahomify next --count 10
dahomify show security --status open
dahomify show smells --status open
```

### Review cadence

Run subjective review on a regular schedule or before major release hardening:

```bash
dahomify review --run-batches --runner codex --parallel --scan-after-import
```

### Suggested policy

- block on high-severity security findings
- block on newly introduced T1 and T2 findings
- allow known T3 and T4 debt temporarily during adoption
- ratchet the strict score upward over time

## GitHub Actions Layout for `ekra.app`

Recommended workflows in the application repo:

- `.github/workflows/pr-ci.yml`
- `.github/workflows/staging-deploy.yml`
- `.github/workflows/prod-deploy.yml`
- `.github/workflows/synthetics.yml`
- `.github/workflows/security.yml`

Recommended job families:

- `frontend-lint`
- `frontend-typecheck`
- `frontend-test`
- `frontend-build`
- `backend-lint`
- `backend-test`
- `api-contracts`
- `docker-build`
- `docker-smoke`
- `playwright-smoke`
- `newman-smoke`
- `dahomify-gate`
- `deploy-staging`
- `deploy-production`
- `post-deploy-smoke`

## Security and Access Model

### Minimum requirements

- no secrets committed to git
- GitHub Actions secrets or OIDC-based cloud auth
- separate secret scopes by environment
- protected branches
- required reviews for workflow and infra changes
- dependency scanning enabled
- image scanning enabled
- audit trail for production deploys

### Recommended security tooling

- Dependabot
- CodeQL
- Trivy
- `pip-audit`
- `npm audit`
- cloud secret manager

## Observability and Incident Readiness

### Metrics

Track at minimum:

- request volume
- latency
- error rate
- CPU and memory
- DB health
- Redis health
- queue depth
- worker lag

### Logs

Logs should support:

- request tracing
- deployment correlation
- error diagnosis
- search by environment, service, and release

### Alerts

Alert on:

- site down
- API health failure
- sustained 5xx spike
- queue backlog
- migration failure
- certificate expiry
- backup failure

### Incident runbooks

Keep written runbooks for:

- frontend outage
- API outage
- failed deploy
- failed migration
- queue backlog
- provider outage
- rollback execution

## Backup, Recovery, and Rollback

### Database

- scheduled backups
- retention policy
- restore test rehearsals
- pre-release snapshot before risky migrations

### Application rollback

- immutable image tags
- previous known-good image digest
- rollback command or workflow documented
- feature flags for risky changes

## Ownership Model

Assign clear owners for:

- frontend quality gates
- backend quality gates
- CI workflow health
- staging environment
- production deploy approval
- monitoring and alerts
- security findings
- Dahomify baseline management

## Implementation Checklist

### Foundation

- add application-repo GitHub Actions workflows
- add Docker Compose parity stack
- add test report artifacts
- add secrets and environment strategy

### Quality gates

- add frontend lint and typecheck
- add backend tests
- add Playwright smoke coverage
- add API contract tests
- add Dahomify gate

### Deployment

- add staging deploy workflow
- add production promotion workflow
- add backup-before-migrate guard
- add post-deploy smoke checks

### Operations

- add Sentry
- add dashboards
- add alerts
- add rollback documentation
- add incident runbooks

## Success Criteria

The `ekra.app` delivery setup is complete when:

- the real CI/CD lives in the app repo
- `dahomify` provides shared standards and quality policy
- PRs are blocked on required quality gates
- staging receives tested builds automatically
- production promotions reuse tested artifacts
- smoke tests run after every deploy
- rollback is documented and fast
- alerts catch user-visible issues quickly
