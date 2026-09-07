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

### Fixed

- Removed timestamp-only rows from report output while preserving valid zero values.
- Restored plain-text attachment-only email formatting for report delivery.
- Improved Excel formula recalculation behavior for usage columns.
- Fixed on-demand Excel exports so native charts are included consistently.
- Added required Word table-grid XML for compatibility with standard DOCX readers.

## [0.1.0] - 2026-07-03

### Added

- Initial full-stack energy monitoring implementation.
- Backend collector, polling, database, API, and reporting flows.
- React frontend for dashboard, meters, alerts, and reports.
