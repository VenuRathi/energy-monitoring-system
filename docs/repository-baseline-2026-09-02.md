# Repository Baseline — 2026-09-02

This document records the Phase 0 baseline before repository and plant-PC cleanup.
It is an audit record, not a cleanup instruction. No runtime data, secrets, backups,
or user changes were removed or moved as part of this baseline.

## 1. Repository freeze

- Repository: `energy-monitoring-system`
- Branch: `main`
- HEAD at baseline: `83a1cd2186785e195e119a8679ead53a8723152f`
- Remote: `origin` configured to the project GitHub repository
- Tracked file count: 177
- Working tree was already modified before Phase 0:
  - `app/api/service.py` — modified, 18 changed lines
  - `tests/test_reports_hardening.py` — modified, 87 added lines
- These two files are explicitly protected from cleanup operations.
- No commit, reset, checkout, rebase, or destructive filesystem operation was performed.

### Protected working-copy fingerprints

These hashes identify the current local versions and can be rechecked before later
phases:

| File | SHA-256 |
|---|---|
| `app/api/service.py` | `7F5899A083903F20844C9D33AAB095722E9593BA4D95A24ECBEB40ABF83B70B3` |
| `tests/test_reports_hardening.py` | `FA8991EC17894D74EA7237A2D1AB257D20D2424D2FD1DB14C9115056408BD95C` |

## 2. Current workspace inventory

The following items exist on the inspected development/operations PC. Their
presence does not mean they belong in Git or in a production release bundle.

| Path | State | Phase 0 decision |
|---|---|---|
| `.env` | Present | Keep local; never commit or copy into a release bundle |
| `.venv` | Present | Local development artifact; recreate per machine |
| `.pytest_cache` | Present | Generated cache; disposable after verification |
| `__pycache__` | Present | Generated cache; disposable after verification |
| `.idea` | Present | IDE-local state; not part of deployment |
| `.vscode` | Present | Editor-local state; not part of deployment |
| `frontend/node_modules` | Present | Dependency install; recreate from lockfile |
| `frontend/dist` | Present | Generated frontend build; release-only artifact |
| `frontend/.vite` | Present | Generated bundler cache; disposable |
| `logs` | Present | Runtime evidence; retain according to operations policy, never Git |
| `data` | Present | Runtime state/database spool; protect during cleanup |
| `backups` | Absent | Must be provisioned outside the source checkout for production |
| `release` | Absent | Release output is not currently present in this checkout |
| `deployment-reports` | Absent | No local deployment-report bundle present |
| `pilot-evidence` | Absent | No local pilot-evidence bundle present |
| `installer/output` | Absent | No local installer output present |

Measured local artifact sizes at baseline:

- `.venv`: approximately 120.6 MB
- `frontend/node_modules`: approximately 123.5 MB
- `frontend/.vite`: approximately 12.7 MB
- `frontend/dist`: approximately 0.8 MB
- `logs`: approximately 6.5 MB
- `data`: approximately 32 KB

## 3. Runtime and machine observations

- PostgreSQL service `postgresql-x64-18` was observed as `Running` with automatic
  startup.
- Python and Node-related processes were present during inspection.
- No matching Energy Monitoring, backend, watchdog, or backup scheduled task was
  returned by the local scheduled-task query.
- Hardware/OS CIM details could not be read in the restricted inspection context;
  no hardware or operating-system claim is made here.
- This report covers the current accessible workspace only. Other plant PCs need
  the same inventory captured locally before rollout.

## 4. Phase 0 decisions

1. Do not clean the current checkout until the two protected modified files are
   committed or explicitly handed off by the owner.
2. Do not delete or move `.env`, `data`, `logs`, or any future `backups` and
   evidence folders without an owner-approved retention decision.
3. Treat the Git repository as source and durable documentation only.
4. Treat virtual environments, dependency folders, build output, caches, logs,
   runtime state, backups, and evidence as machine/release data.
5. Before rollout to other PCs, record each PC's install path, service/task names,
   database endpoint, backup destination, and installed release version.

## 5. Exit criteria for Phase 0

- [x] Repository branch, HEAD, tracked-file count, and working-tree changes recorded.
- [x] Existing modified files fingerprinted and protected.
- [x] Local generated/runtime directories inventoried without deleting them.
- [x] PostgreSQL service and scheduled-task state checked.
- [x] No secrets or runtime database contents copied into this report.
- [ ] Inventory captured for every additional plant PC.
- [ ] Owner confirms disposition of the two existing working-tree modifications.

The remaining two unchecked items are rollout prerequisites and require access to
the other PCs and an owner decision; they are intentionally not guessed here.
