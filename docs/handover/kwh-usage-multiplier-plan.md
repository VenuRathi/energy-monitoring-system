# kWh usage multipliers: implementation and controlled deployment

Status: proposed plan only. Application code and plant configuration have not been changed.
Repository inspected: main at 47f6d6d. The running plant release has not been verified.

## 1. Requirement and acceptance boundary

For a valid usage value, corrected kWh usage = existing derived kWh usage × that meter's multiplier.

| Line | Physical meter | Multiplier |
| --- | --- | ---: |
| Stratapore | Stratapore Line Main Panel | 126 |
| Stratapore | TC Oven Machine Meter | 50 |
| OSP | Screen Printing Machine | 50 |
| Any other meter | Existing behavior | 1 |

Scope is the Excel kWh usage column, including interval and daily exports and attachments generated through those paths. Preserve cumulative kWh readings, acquisition scaling, database history, kVAh/kVARh usage, PF values, dashboards, and existing raw-reading graphs. Word currently renders raw parameter values; do not add or scale values there for this requirement.

Verify with plant maintenance that these numbers are the intended additional software multipliers for the specific readings being exported. Record a manual reference example for each physical meter to avoid applying a factor already included in those readings.

## 2. Actual code paths and the PF dependency

In app/api/service.py:

- `_daily_consumption_formula` generates interval subtraction formulas with blank, nonnumeric, and RESET/INVALID guards.
- The daily Excel writer instead writes already-derived daily consumption values and status text.
- `_pf_formula` divides the displayed kWh consumption cell by kVAh consumption. Scaling kWh without compensating here would change PF too.
- `_add_excel_graphs` uses source readings; retain that behavior.

Apply the factor only at report output, once. Do not alter the collector's `scale: 0.001`, energy parameter definitions, source rows, daily delta generation, or stored readings.

Preserve PF by calculating it from the original unscaled deltas. One compatible formula is `(corrected_kWh_usage / multiplier) / original_kVAh_usage`, retaining all current numeric and zero-denominator guards. Do not clamp PF to hide a calculation error. This preserves the existing PF behavior; this release does not redefine its physical interpretation.

## 3. Configuration design

Add a dedicated loader for `data/report_multipliers.json`. This is a proposed file and loader, not an existing feature. The data directory is already Git-ignored and protected by the deployment manifest. Ship a tracked example separately; never ship one plant's active mapping to another plant.

Use meter IDs, not names, COM ports, slave IDs alone, list positions, or fuzzy matching. IDs must be verified separately on every PC because IDs can repeat between installations. Include a revision, site label, meter display identity for operator review, factors, and an explicit historical application policy. Load and validate one configuration snapshot per export.

Implementation rules:

1. Missing configuration preserves legacy multiplier 1 for backward compatibility, but deployment cannot pass for these three meters until their mappings are present and verified.
2. An unlisted meter uses 1. A present but malformed file, duplicate meter ID, or invalid configured factor must fail the affected report visibly, not silently produce an uncorrected report. Polling must remain operational.
3. Accept finite positive numeric factors only; reject booleans, strings, zero, negatives, NaN, and infinity. Flag configured IDs absent from the active inventory in a deployment validation check.
4. Include a small report metadata sheet showing meter ID/name, factor, configuration revision, generation time, and historical policy. Embed the resolved numeric factor in formulas so the workbook is independent of the plant PC's configuration file.
5. Add a read-only validation command that prints the resolved meter-to-factor mapping and returns a nonzero exit code on validation failure. Use it before restarting and before production reports are released.

The checked-in config identifies MTR-001 as Screen Printing, location Old Spin On Line. This is only a candidate mapping; verify it against OSP's live inventory and physical meter. The two Stratapore IDs are not established by the checked-in config. Do not invent them.

## 4. Calculation and historical policy

For interval rows, multiply the successful numeric subtraction branch only:

```text
IF(missing or nonnumeric reading, blank,
   IF(current < previous, "RESET/INVALID",
      (current - previous) * meter_multiplier))
```

For daily rows, multiply only the existing valid numeric daily delta. Preserve zero as zero and keep all existing status strings and missing values unchanged. Do not derive daily usage again from the displayed readings: existing daily boundary logic must remain authoritative.

Suggested policy, subject to plant signoff: the factors correct an existing reporting omission, so newly generated reports for historical ranges also use the factors. Previously saved/sent workbooks remain unchanged. Do not rewrite database history or automatically resend past reports.

If the factors instead became valid on a particular date, stop this simple rollout and implement effective-dated configuration first, including splitting intervals that cross a factor change. A report generation date is not a substitute for the measurement's effective date.

## 5. Test and release gate

Extend tests/test_reports_hardening.py and add focused loader tests. Required cases:

| Case | Expected result |
| --- | --- |
| Main Panel, raw usage 10 | kWh usage 1260 |
| TC Oven, raw usage 10 | kWh usage 500 |
| Screen Printing, raw usage 10 | kWh usage 500 |
| Unconfigured meter, raw usage 10 | kWh usage 10 |
| Raw kWh delta 10, kVAh delta 12.5, factor 126 | kWh 1260; kVAh 12.5; PF stays 0.8 |
| Zero, first interval row, missing data, reset | Existing zero/blank/status behavior preserved |
| Daily numeric values and daily status strings | Only valid numeric kWh usage multiplied |
| Multiple meters, reordered/selected parameters | Each factor stays attached to the correct meter and kWh column |
| Renamed meter with same ID | Same factor applies |
| Invalid config and duplicate/unknown IDs | Clear validation failure; acquisition unaffected |
| Repeated exports of same source rows | Same result; no in-place mutation or double multiplication |
| Manual and scheduled attachment generation | Same factors and PF behavior, without sending email during tests |

Assert raw kWh, kVAh, kVARh, PF, graph source values, and source rows match the baseline. Check both Excel writer paths. Open a generated workbook in Excel and recalculate: openpyxl does not evaluate Excel formulas, so formula-string assertions alone do not establish the displayed result.

Run from the development checkout after implementation:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

No frontend rebuild or dependency installation should be required if this release remains strictly backend/config/tests/docs with no dependency changes. If the plant is behind and receives other commits, review the entire intervening diff and include their migrations, builds, and dependencies in a separately validated upgrade.

## 6. Development Git push procedure

These are future operator steps. Do not deploy the documentation-only commit as the feature.

1. Confirm a clean development worktree, fetch origin, and review upstream changes before updating main. Stop on divergence.
2. Create `codex/kwh-usage-multipliers`, implement the change, run the tests, and inspect representative workbooks.
3. Stage only the intended code, tests, example configuration, and documentation. Never stage .env, active plant configuration, backups, or generated reports.
4. Review `git diff --cached`, commit, and push the branch.
5. Merge through the normal review/CI process. Record the exact reviewed main commit as the approved release SHA. Optionally create an immutable release tag at that SHA. Do not deploy the pre-merge branch SHA if the merge changes it.

```powershell
git status --short
git fetch origin
git switch main
git pull --ff-only origin main
git switch -c codex/kwh-usage-multipliers
# Implement, test, stage explicit paths, and inspect the staged diff here.
git commit -m "fix: apply per-meter multipliers to report kWh usage"
git push -u origin codex/kwh-usage-multipliers
```

Check every native command's exit code before continuing; PowerShell does not automatically stop on every failed native executable.

## 7. Current deployment model and plant preflight

The repository documents Windows + local PostgreSQL + a Task Scheduler backend/watchdog named EnergyMonitoringBackend, with built frontend/dist served on port 5000. Common roots are C:\EnergyMonitoring\energy-monitoring-system and C:\ProgramData\Plant Energy Monitor; the actual root, task name, port, and release must be inspected on each PC.

For EACH installation record: root, deployment type (Git/bundle/installer), current SHA/version, task action path, enabled meter count, three applicable physical-meter identities and IDs, factor mapping, approved target SHA, operator, and maintenance window. Export one baseline report with a fixed historical range and retain it for comparison.

Use scripts/collect_pc_inventory.ps1 and the live meter inventory. Record baseline /api/status and polling health. Resolve pre-existing failures before attributing them to this change.

Back up PostgreSQL with scripts/backup_postgres.ps1 to a new dedicated backup directory; verify success and inspect the dump with pg_restore --list. Keep a previously tested restore procedure. Preserve .env, config/meter_config.json, data, frontend/dist, and the old application release in an access-controlled backup outside the active checkout. Copy SQLite spool files only after the backend stops, including any journal/WAL companion files.

Keep local secrets/configuration on the plant PC. A git pull does not update database meter records and must never substitute development meter configuration for live configuration.

## 8. Git-based plant cutover

1. In the verified application root, inspect `git status --short`, branch, remote, and HEAD. Save the old SHA outside the checkout. If there are local modifications, stop and reconcile them deliberately. Do not force reset, clean, or automatically stash machine-specific files.
2. Fetch while the old backend is running. Confirm the approved SHA exists and is a descendant of the plant HEAD. Review the full old-to-target diff. If origin/main has advanced beyond the approved SHA, do not blindly pull main.
3. Prepare and validate the plant-specific multiplier file against live inventory. Preserve any prior file. Agree on historical policy before activation.
4. Use a maintenance window away from scheduled report delivery. Record pending/due report schedules. Temporarily pause their delivery through supported controls, or temporarily set REPORT_WORKER_ENABLED=false in the plant .env for the first validation restart; preserve its original setting.
5. Disable the verified backend scheduled task temporarily to prevent a reboot/logon trigger during cutover. Run the project's stop_backend_task.ps1, passing the actual root/task name if nondefault. Confirm watchdog and child backend are stopped and the API listener is gone. Do not stop unrelated Python processes.
6. Complete the stopped-state runtime backup and database backup verification. Record the collection gap start. Collection is paused during this window; the spool cannot collect while the process is stopped.
7. Fast-forward to precisely the approved SHA using `git merge --ff-only <APPROVED_SHA>` after fetch. This is the pinned equivalent of the fetch/merge that git pull performs. Confirm HEAD equals that SHA. If using literal `git pull --ff-only origin main`, first prove origin/main equals the approved SHA and verify HEAD afterward before starting the backend; a moving branch introduces a race, so the pinned merge is preferred.
8. Place the validated plant-local multiplier file in data/report_multipliers.json. Run the new configuration validation command using the plant .venv interpreter. Require the printed IDs/factors to match the signed mapping.
9. Enable the task and start it with Start-ScheduledTask. Never also launch main.py manually. Confirm only one backend owns the COM ports.
10. Run scripts/check_runtime_health.ps1 with -MinimumExpectedEnabledMeters set to THIS PC's expected count and -FailOnDegraded. Wait at least two configured polling cycles; verify new timestamps, database/schema health, meter communication, and spool recovery.
11. Export the same historical range as baseline. Verify all three applicable factors, unchanged other meters/columns, unchanged PF, raw readings, and Excel recalculation. Validate daily and interval reports. Keep evidence with the deployment record.
12. Restore the original report-worker/schedule settings and restart through the project stop/start sequence if needed. Check due jobs before allowing catch-up delivery to avoid unintended duplicate historical reports. Observe the next normal scheduled report through the operator's existing workflow.

Stop on any failed step. Do not continue to a restart after a failed update/configuration validation. Pilot one PC first, then repeat on the remaining installations after its acceptance checks pass.

## 9. Bundle or installer deployment

An installer/bundle installation may not contain .git. Do not run git pull there. Build and validate the release from the same approved SHA with the repository release-bundle/installer workflow, then use its documented upgrade process. Confirm its protection of .env, config/meter_config.json, and runtime directories. Preserve the previous release and frontend build. Apply the same stop, backup, site mapping, validation, restart, and acceptance gates above.

## 10. Rollback and completion

Trigger rollback for incorrect factors, changed PF/other columns, report failures, or new startup/polling failures.

1. Pause report delivery, disable automatic backend startup, and stop via the project stop script.
2. Preserve failed-release logs and report evidence. Restore the previous multiplier file or move the newly introduced file into the rollback evidence directory.
3. For a clean Git checkout, `git switch --detach <OLD_SHA>` restores the recorded prior code without deleting history. Stop if Git reports local changes. For bundles/installers, restore the previous approved application release while preserving current runtime data and plant configuration. Restore frontend/dist only if the upgrade changed it.
4. Restore original worker settings, re-enable/start the task, and repeat health/report checks. Record the old SHA and the fact that multiplier support is temporarily withdrawn.
5. Do not restore an old database dump for this report-only rollback: no schema/data migration is planned, and restoring it would discard newer readings. Keep the dump for disaster recovery.
6. After a Git rollback, document detached HEAD and deliberately reattach to the approved deployment branch during the next reviewed upgrade. Do not blindly pull from detached HEAD.

Completion evidence: deployed SHA, configuration revision, verified meter mapping, historical policy, backup location, before/after workbooks, PF comparison, health results, polling-gap timestamps, and operator acceptance. No production deployment is complete solely because git pull succeeded.
