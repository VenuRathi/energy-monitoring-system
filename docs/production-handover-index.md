# Production Handover Index

This is the plant deployment and operations handover package for the Energy Monitoring System.

Use this index first, then open the document for the task you are doing.

## Deployment

- [Production deployment checklist](production-deployment-checklist.md)

Use this before installing or moving the system to a plant PC/server. It covers Windows setup, PostgreSQL, Python, frontend build, `.env`, API key mode, SMTP, COM ports, firewall, and scheduled startup.

## Daily Operation

- [24/7 operations SOP](operations-sop-24x7.md)

Use this for daily, weekly, and monthly checks. It explains what healthy looks like and what to review in logs, database size, time sync, meter communication, and reports.

## Backup And Restore

- [Backup and restore SOP](backup-restore-sop.md)

Use this to create backups, schedule backups, verify backups, restore PostgreSQL, and recover after plant PC/server replacement.

## Incidents

- [Incident response guide](incident-response-guide.md)

Use this when meters stop updating, reports fail, the database fails, the frontend cannot connect, API key errors appear, SMTP fails, the PC restarts, or the clock is wrong.

## Readiness Signoff

- [Production readiness and signoff checklist](production-readiness-signoff.md)

Use this before calling the system production-ready. It lists completed hardening and the remaining production conditions: soak test evidence, backup/restore proof, time-sync discipline, duplicate-history cleanup, future DB unique index migration, and optional archive-before-delete.

## Supporting References

- [Environment variables](environment-variables.md)
- [Task Scheduler setup](task-scheduler-setup.md)
- [Plant PC deployment guide](plant-pc-deployment.md)
- [Backup and maintenance](backup-and-maintenance.md)
- [Pilot validation runbook](pilot-validation-runbook.md)
- [Data model](data-model.md)
- [Troubleshooting](troubleshooting.md)
