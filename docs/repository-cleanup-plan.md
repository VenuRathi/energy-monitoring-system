# Repository Cleanup Plan

This repository should stay focused on source code, configuration templates, setup scripts, tests, and durable handover documentation.

Generated runtime output, local machine state, release artifacts, and one-off evidence bundles should stay out of git.

## Keep In Git

- application source: `main.py`, `app/`, `utils/`
- frontend source and lockfile: `frontend/src/`, `frontend/package.json`, `frontend/package-lock.json`
- configuration templates and loaders: `.env.example`, `config/`
- deployment and operations scripts: `scripts/`, `deployment/`
- database scripts: `sql/`
- tests and CI: `tests/`, `.github/`
- durable docs: architecture, deployment, operations, backup, incident response, developer guides, API contract

## Keep Local And Ignored

These are expected to exist during development or plant-PC operation, but should not be committed:

- secrets and machine config: `.env`
- Python environments: `.venv/`, `.venv_old_*/`
- Python caches: `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`
- frontend dependencies and builds: `frontend/node_modules/`, `frontend/dist/`, `frontend/.vite/`
- runtime logs and Excel-era log exports: `logs/*.log`, `logs/*.xlsx`
- runtime data and locks: `data/`
- local PostgreSQL backups: `backups/`
- generated releases and installers: `release/`, `installer/output/`
- pilot and deployment evidence: `pilot-evidence/`, `deployment-reports/`, `deployment/reports/`
- installer smoke-test copies: `.installer_smoke/`

## Archived On 2026-08-06

The cleanup pass moved generated or stale files to:

```text
F:\energy-monitoring-system-cleanup-archive_2026-08-06
```

Archived project artifacts included:

- old installer smoke-test folders
- old Python virtual environment backup
- generated release bundles
- generated installer output
- local database backups
- pilot evidence folders
- deployment report folders
- old Excel log files and old stdout/stderr logs
- stale planning docs that were not referenced by README or handover navigation

## Cleanup Rules

1. Do not delete plant/runtime evidence unless it has been archived or the owner confirms it is no longer needed.
2. Do not commit timestamped health-check, pilot-evidence, release, backup, log, or installer-output folders.
3. Keep only one current public deployment toolkit document unless a second document is intentionally linked from README or the handover index.
4. Before removing a doc, search for references in `README.md`, `docs/`, `scripts/`, and `deployment/`.
5. After cleanup, run `git status --short` and verify that only intentional source/doc changes remain.

## Phase 2 outcome

- Duplicate deployment, operations, maintenance, pilot-checklist, demo, and
  transitional documents were removed from the active repository in Phase 2.
- `pilot-validation-runbook.md` and `pilot-evidence-log.md` remain active under
  `docs/handover/` because they support real field validation and release handoff.
- `pilot-validation-results.md` and `engineering-gap-review.md` remain under
  `docs/archive/` as historical records.
- Release-bundle and installer references were updated to the organized paths.
- Removed files remain recoverable through Git history; they were not deleted from
  repository history.
