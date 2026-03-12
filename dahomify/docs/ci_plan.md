# CI/CD Plan

This document has two jobs:

1. Define the repository CI/CD contract for `dahomify` itself.
2. Provide a production-ready DevOps blueprint for shipping and validating the `ekra.app` website and APIs with Dahomify as a quality gate.

## Part 1: Repository CI/CD Contract

### Goals

1. Block merges unless quality gates pass.
2. Decouple package publishing from ordinary pushes.
3. Keep expensive integration checks visible and reproducible.
4. Preserve local-to-CI parity through `Makefile` targets.

### Workflows

#### 1) CI (`.github/workflows/ci.yml`)

Triggers:
- `pull_request`
- `push` to `main`

Required jobs:
- `lint`:
  - `make lint`
- `typecheck`:
  - `make typecheck`
- `arch-contracts`:
  - `make arch`
- `ci-contracts`:
  - `make ci-contracts` (workflow/docs/policy contract tests)
- `tests-core`:
  - `make tests PYTEST_XML=pytest-core.xml`
- `tests-full`:
  - `make tests-full PYTEST_XML=pytest-full.xml`
- `package-smoke`:
  - `make package-smoke`

Artifacts uploaded:
- `pytest-core-report`
- `pytest-full-report`
- `dist-packages`

#### 2) Integration (`.github/workflows/integration.yml`)

Triggers:
- Nightly schedule (`17 04:00 UTC`)
- Manual (`workflow_dispatch`)

Job:
- `roslyn-integration`
  - Runs `make integration-roslyn`
  - Uses `.github/scripts/roslyn_stub.py` for deterministic CI payloads.

Notes:
- Integration workflow is intentionally separate from required PR checks.
- Failures should be triaged, but do not block normal merges by policy.

#### 3) Publish (`.github/workflows/python-publish.yml`)

Triggers:
- `release.published`
- `push` tag `v*`
- `workflow_dispatch`

Safety gates before publish:
- Validate tag version matches `pyproject.toml` version (for tag pushes)
- Skip publish if version already exists on PyPI
- Run `make package-smoke`

### Branch Protection Policy (`main`)

Required status checks:
- `CI / lint`
- `CI / typecheck`
- `CI / arch-contracts`
- `CI / ci-contracts`
- `CI / tests-core`
- `CI / tests-full`
- `CI / package-smoke`

Pull request policy:
- Require PRs before merging
- Require at least 1 approving review
- Dismiss stale approvals on new commits
- Require conversation resolution

Enforcement notes:
- Admin enforcement can be enabled later after workflow stability is proven.

### Local Parity Commands

Use the `Makefile` targets:

- `make ci-fast`: lint + typecheck + import contracts + tests
- `make ci`: `ci-fast` + full tests + package smoke
- `make ci-contracts`: verify CI/workflow/docs contracts
- `make integration-roslyn`: run Roslyn-path integration parity tests

## Part 2: `ekra.app` Delivery Blueprint

### Documentation Map

Use these documents together:

- `docs/ci_plan.md` for the policy and workflow summary
- `docs/ekra_app_delivery_guide.md` for the full implementation guide
- `SHARIKLY_COMMANDS.md` for practical commands and operational checks

### Repo Placement Recommendation

For `ekra.app`, the actual CI/CD should live in the `ekra.app` application repository, not only in `dahomify` and not in a separate orchestration-only repo by default.

Use this split:

- keep the real workflows, tests, deploy scripts, Docker assets, and infrastructure code with the application repo
- keep the standards, policy, templates, and quality-gate guidance in `dahomify`

Only split infrastructure into a separate repo if a platform-team model already exists and the separation is intentional.

### Mission

Ship `ekra.app` safely with a repeatable pipeline that validates:

- website rendering and UX
- API correctness and contract stability
- database migrations
- background jobs and queues
- infrastructure health
- production observability
- rollback readiness

### Recommended Tooling Stack

Use this baseline unless the application already standardizes on an equivalent managed service:

- Source control and CI: GitHub + GitHub Actions
- Quality gate: `dahomify`
- Web UI tests: Playwright
- API tests: `pytest` + `pytest-django` or framework-native backend tests, plus Newman for collection-based smoke tests
- Load tests: `k6`
- Containerization: Docker + Docker Compose for local parity
- Registry: GitHub Container Registry or Amazon ECR
- IaC: Terraform
- Runtime: AWS ECS Fargate or Kubernetes
- Edge and DNS: Cloudflare
- Database: PostgreSQL
- Cache and queues: Redis
- Async workers: Celery or the stack-native worker runtime
- Monitoring: Prometheus + Grafana or Grafana Cloud
- Error tracking: Sentry
- Logs: Better Stack, Grafana Loki, or ELK
- Synthetic checks: Checkly, Uptime Kuma, or Better Stack checks
- Security scanning: Trivy, `pip-audit`, `npm audit`, CodeQL, Dependabot
- Secrets: GitHub Actions secrets plus cloud secret manager or 1Password/Vault

### Environment Model

Use four environments with clear promotion rules:

- `local`: Docker Compose for frontend, API, database, Redis, and worker parity
- `dev`: shared developer environment, low-cost, fast iteration
- `staging`: production-like, same deployment shape as prod, safe test data only
- `production`: live traffic, guarded deploys, rollback ready

Minimum environment requirements:

- Isolated database per environment
- Separate Redis/cache namespace per environment
- Separate object storage bucket/prefix per environment
- Separate secrets scopes per environment
- Separate Sentry environment tags
- Health endpoints for web, API, and worker

### Branching and Release Model

- Feature branches open PRs into `main`
- Every PR deploys a preview environment when feasible
- Merge to `main` deploys automatically to `staging`
- Production deploys require manual approval or release tags
- Hotfix branches can deploy directly to `production` with mandatory smoke tests

### CI Pipeline Design

#### PR validation pipeline

Run on every pull request:

1. Checkout and dependency restore
2. Frontend lint and typecheck
3. Backend lint and typecheck
4. Unit tests for frontend and backend
5. API contract validation against OpenAPI schema
6. Build Docker images for frontend and API
7. Run `docker compose` integration smoke tests
8. Run Playwright smoke tests against preview or compose environment
9. Run Newman API smoke suite
10. Run Dahomify scan and gate on quality/security thresholds
11. Upload test reports, coverage, screenshots, and traces

#### Staging deployment pipeline

Run on merge to `main` after CI passes:

1. Build and tag immutable images
2. Apply Terraform plan or GitOps sync
3. Run database migration dry run
4. Deploy web, API, and worker to `staging`
5. Run post-deploy smoke checks
6. Run short `k6` load smoke
7. Run synthetic browser and API checks
8. Mark release candidate as ready for production

#### Production deployment pipeline

Run on release tag or manual promotion:

1. Reuse already-tested image digest from staging
2. Require approval from engineering owner
3. Take database backup or snapshot before migration
4. Run migration with timeout and rollback guard
5. Use blue/green or canary deployment
6. Run production smoke tests
7. Watch error rate, latency, and saturation for 10-30 minutes
8. Auto-rollback on failed smoke tests or alert thresholds

### Testing Matrix

#### Frontend

- ESLint
- TypeScript typecheck
- Unit/component tests
- Playwright E2E journeys:
  - landing page loads
  - login/register flows
  - key browsing/search path
  - checkout/contact/conversion path if applicable
- Lighthouse performance budget on key pages

#### Backend / APIs

- Lint and formatting checks
- Type checks where available
- Unit tests for business logic
- Integration tests with PostgreSQL and Redis
- Contract tests against OpenAPI or schema snapshots
- Authentication and authorization tests
- Idempotency tests for write endpoints
- Migration tests on production-like schema data

#### Cross-service and runtime

- Docker Compose smoke environment
- Queue/worker execution tests
- Object storage upload/download smoke tests
- Cron or scheduled job validation
- Disaster-recovery restore rehearsal on schedule

### Dahomify Quality Gates

Use Dahomify in both CI and release governance.

Required commands:

```bash
dahomify scan --path .
dahomify status
dahomify next --count 10
dahomify show security --status open
dahomify show smells --status open
```

Recommended subjective review cadence:

```bash
dahomify review --run-batches --runner codex --parallel --scan-after-import
```

Suggested deployment policy for `ekra.app`:

- Fail PR CI if any high-severity security finding is open
- Fail PR CI if new T1 or T2 Dahomify findings are introduced
- Warn, but do not block, on existing accepted T3/T4 debt during early rollout
- Block production if strict score drops below agreed threshold
- Start with `strict >= 70`, then raise to `80`, `90`, and eventually `95`

### Observability and Operations

Every production deployment should emit:

- request rate
- p95 and p99 latency
- error rate
- container CPU and memory
- DB CPU, connections, locks, and slow queries
- Redis memory and eviction signals
- queue depth and worker lag
- external dependency failures

Alerting must cover:

- website unavailable
- API health endpoint failure
- spike in 5xx responses
- auth failures spike
- background job backlog
- migration failure
- certificate expiry
- backup failure

### Secrets, Security, and Compliance

- Store no secrets in repo
- Use OIDC or short-lived cloud credentials in CI where possible
- Rotate secrets regularly
- Enable branch protection and CODEOWNERS for infra and workflow files
- Run Trivy against built images
- Run `pip-audit` and `npm audit` with agreed severity thresholds
- Enable Dependabot for Python, npm, and GitHub Actions
- Enable CodeQL for Python and JavaScript/TypeScript if applicable

### Backup and Rollback

- Nightly automated PostgreSQL backups with retention policy
- Pre-release snapshot before production migration
- Tested restore procedure documented and rehearsed
- Immutable image rollback by prior digest
- Feature flags for risky frontend and backend releases
- Rollback command path documented in runbooks

### Minimum GitHub Actions Layout for `ekra.app`

Use this structure in the app repository:

- `.github/workflows/pr-ci.yml`
- `.github/workflows/staging-deploy.yml`
- `.github/workflows/prod-deploy.yml`
- `.github/workflows/synthetics.yml`
- `.github/workflows/security.yml`

Suggested job groups:

- `frontend-lint`
- `frontend-test`
- `frontend-build`
- `backend-lint`
- `backend-test`
- `api-contracts`
- `docker-smoke`
- `playwright-smoke`
- `newman-smoke`
- `dahomify-gate`
- `deploy-staging`
- `deploy-production`
- `post-deploy-smoke`

### Rollout Plan

Phase 1:
- Add workflows and branch protection
- Add Docker Compose parity stack
- Add Playwright and API smoke suites
- Add Dahomify CI gates in advisory mode

Phase 2:
- Add staging auto-deploy
- Add Sentry, metrics, dashboards, and synthetic checks
- Add backup verification and migration rehearsal
- Raise Dahomify from advisory to blocking for security and new debt

Phase 3:
- Add production canary or blue/green deployment
- Add load smoke tests and rollback automation
- Raise strict-score threshold
- Formalize incident runbooks and on-call ownership

## Success Criteria

The plan is considered complete when:

- PRs cannot merge without green quality gates
- `main` reliably promotes to staging
- production deploys reuse tested artifacts
- website and API smoke tests run after deploy
- observability can detect user-visible failures quickly
- rollback is fast and documented
- Dahomify is part of the regular release gate, not a one-off report
