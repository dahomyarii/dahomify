# Sharikly / ekra.app Commands

This runbook is the command companion for the `dahomify` CLI help text.
Use it when setting up local development, CI validation, staging checks, or production release flows for `ekra.app`.

Related docs:

- `docs/ci_plan.md` - policy, workflow, and CI/CD summary
- `docs/ekra_app_delivery_guide.md` - full end-to-end delivery and operating guide

## Core project entry points

Frontend and project help:

```bash
npm run help
```

Backend help:

```bash
python manage.py project_help
```

Full local stack:

```bash
docker compose up --build
```

## Recommended local workflow

### 1) Start dependencies

```bash
docker compose up --build
```

Expected services:

- frontend
- backend API
- PostgreSQL
- Redis
- worker / scheduler if used

### 2) Frontend checks

Use the project-provided commands first:

```bash
npm run help
```

Typical CI-safe commands:

```bash
npm run lint
npm run typecheck
npm run test -- --runInBand
npm run build
```

If Playwright is configured:

```bash
npx playwright test
```

### 3) Backend checks

Use the project-provided command index first:

```bash
python manage.py project_help
```

Typical CI-safe commands:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
python manage.py migrate
```

If the backend uses `pytest`:

```bash
pytest -q
```

## Dahomify commands

Use Dahomify as a standing quality gate, not just a reporting tool.

### Quick health pass

```bash
dahomify scan --path .
dahomify status
dahomify next --count 10
dahomify show security --status open
dahomify show smells --status open
```

### Agent-ready context

```bash
dahomify agent --scan --goal "stabilize ekra.app CI/CD, website, and API checks"
```

If an AI-assisted execution plan is wanted and `OPENAI_API_KEY` is available:

```bash
dahomify agent --scan --synthesize --goal "stabilize ekra.app CI/CD, website, and API checks"
```

### Subjective review pass

```bash
dahomify review --run-batches --runner codex --parallel --scan-after-import
```

## Suggested CI pipeline commands

Use these in the application repository workflows.

### Pull request CI

```bash
npm ci
python -m pip install -r requirements.txt
npm run lint
npm run typecheck
npm run test -- --runInBand
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
dahomify scan --path .
dahomify status
dahomify show security --status open
docker compose up -d --build
```

If API collections are present:

```bash
newman run postman/ekra.postman_collection.json
```

If browser smoke tests are present:

```bash
npx playwright test --project=chromium
```

## Suggested deployment gates

### Before staging deploy

```bash
dahomify status
python manage.py check
python manage.py makemigrations --check --dry-run
docker compose up -d --build
```

### Before production deploy

```bash
dahomify status
dahomify show security --status open
python manage.py check --deploy
python manage.py migrate --plan
```

Recommended manual confirmations:

- image digest already passed staging
- DB backup or snapshot completed
- smoke tests ready to run immediately after deploy
- rollback target identified

## Post-deploy smoke checklist

Run immediately after staging and production deploys:

```bash
curl -f https://ekra.app/
curl -f https://api.ekra.app/health
```

Then verify:

- homepage loads successfully
- login/auth flow works
- primary browse/search flow works
- at least one authenticated API write flow works
- worker/queue tasks are being consumed
- Sentry and metrics show no spike in errors

## Incident triage commands

Re-check health and debt posture:

```bash
dahomify status
dahomify next --count 20
dahomify show security --status open
```

Check application health:

```bash
curl -f https://ekra.app/
curl -f https://api.ekra.app/health
docker compose ps
docker compose logs
```

## Policy

- Treat high-severity open security findings as release blockers.
- Do not promote to production from untested artifacts.
- Keep CI, staging, and production as close as possible in runtime shape.
- Re-run Dahomify after meaningful backend, frontend, or workflow changes.

## Repo placement rule

For `ekra.app`, the real CI/CD should live in the application repo.

- keep actual workflows, tests, deploys, Docker files, and infra code with the app
- keep Dahomify policy, templates, and reusable standards in `dahomify`
