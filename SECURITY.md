# Security Policy

## Supported Versions

This repository is actively maintained on the `main` branch.

## Reporting a Vulnerability

If you discover a security issue:

1. Do not open a public issue with exploit details.
2. Contact the maintainer directly and include:
   - affected component/file
   - reproduction steps
   - impact assessment
   - suggested fix (if available)
3. Allow reasonable time for triage and remediation before public disclosure.

## Security Baseline for Local/Production Usage

- Keep `.env` private and never commit real secrets.
- Rotate any credential that was ever exposed or suspected exposed.
- Restrict database/network access to trusted hosts only.
- Use strong, unique SMTP and database credentials.
- Run the API behind a trusted reverse proxy for internet-exposed deployments.
- Keep dependencies updated and monitor CI/security alerts.

## Secret Management Guidance

- Use `.env.example` as template only.
- Populate secrets from environment variables or secret managers.
- Avoid embedding credentials in source, scripts, or SQL files.