# Changelog

All notable changes to this project will be documented in this file.

The format is inspired by Keep a Changelog and follows semantic versioning where practical.

## [Unreleased]

### Added

- Repository hardening files (`SECURITY.md`, `.env.example`, CI, Dependabot).
- Governance and contribution workflow files.
- Feedback-ready issue templates and PR template.
- Canonical report dataset preparation shared by normal and scheduled exports.
- Native Excel line charts with Date & Time X-axis and unit-labeled Y-axis.
- Excel chart downsampling that keeps large report workbooks responsive while preserving the complete report data.
- Plain-text report-email metadata that identifies the actual report window, selected parameters, valid reading count, and attached workbook.
- Reports-page delivery previews that show the effective scheduled window, Excel-only chart behavior, shared email/report scope, and no-data handling.
- Regression coverage for scheduled before/after snapshot selection, interval targets, and multi-meter Excel chart series with valid zero values.
- Reusable Phase 9 report QA runner for deterministic Excel and Word evidence generation.

### Fixed

- Removed timestamp-only rows from report output while preserving valid zero values.
- Restored plain-text attachment-only email formatting for report delivery.
- Improved Excel formula recalculation behavior for usage columns.
- Fixed on-demand Excel exports so native charts are included consistently.
- Added required Word table-grid XML for compatibility with standard DOCX readers.
- Added native Excel charts and Graph Data to scheduled daily-snapshot reports, matching other Excel report paths.
- Clarified scheduled snapshot tables by labeling the configured column as Target Time while charts retain actual reading timestamps.

## [0.1.0] - 2026-07-03

### Added

- Initial full-stack energy monitoring implementation.
- Backend collector, polling, database, API, and reporting flows.
- React frontend for dashboard, meters, alerts, and reports.
