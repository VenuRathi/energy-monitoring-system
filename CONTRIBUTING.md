# Contributing Guide

Thank you for your interest in improving this project.

## Before You Start

- Read [README.md](README.md) and [SECURITY.md](SECURITY.md).
- Check existing issues before opening a new one.
- Keep changes focused and easy to review.

## Development Setup

1. Fork and clone the repository.
2. Create a Python virtual environment and install dependencies.
3. Set up local `.env` from `.env.example`.
4. Install frontend dependencies in `frontend/`.

## Branching and Commits

- Create a feature branch from `main`.
- Use clear commit messages.
- Keep each commit logically scoped.

Examples:

- `feat(api): add meter batch sync endpoint`
- `fix(frontend): correct trend chart tooltip values`
- `docs: improve setup and security notes`

## Pull Request Checklist

- Include a short summary and motivation.
- Link related issues.
- Add or update tests where applicable.
- Ensure backend tests pass.
- Ensure frontend build passes.
- Add screenshots for UI changes.

## Code Quality Expectations

- Avoid hardcoded secrets, credentials, or private endpoints.
- Keep architecture boundaries clear (collectors, services, database, API, UI).
- Prefer small, reviewable changes over broad rewrites.

## Security Notes

- Never commit `.env`.
- Never include real DB or SMTP passwords in issues/PRs.
- Use placeholders in examples.