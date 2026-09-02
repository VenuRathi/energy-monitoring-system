"""Validate repository hygiene and the deployment contract without external dependencies."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
FORBIDDEN_TRACKED_PARTS = {
    ".env",
    ".idea",
    ".pytest_cache",
    ".venv",
    ".vscode",
    "__pycache__",
    "backups",
    "data",
    "deployment-reports",
    "frontend/.vite",
    "frontend/node_modules",
    "frontend/dist",
    "installer/output",
    "logs",
    "pilot-evidence",
    "release",
}
REQUIRED_TRACKED_FILES = {
    ".env.example",
    ".gitignore",
    "README.md",
    "config/deployment-manifest.json",
    "frontend/package-lock.json",
    "pyproject.toml",
    "requirements.txt",
}
REMOVED_DOC_REFERENCES = {
    "docs/plant-pc-deployment.md",
    "docs/release-bundle.md",
    "docs/pilot-evidence-log.md",
    "docs/pilot-validation-runbook.md",
    "docs/backup-and-maintenance.md",
    "docs/deployment-checklist.md",
    "docs/operations-runbook.md",
    "docs/maintenance-playbook.md",
    "docs/pilot-checklist.md",
    "docs/known-limitations.md",
    "docs/boss-demo-script.md",
    "docs/temporary-control-utility.md",
}


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line.replace("\\", "/") for line in result.stdout.splitlines() if line]


def check_tracked_paths(files: list[str]) -> list[str]:
    errors: list[str] = []
    tracked = set(files)
    for required in sorted(REQUIRED_TRACKED_FILES - tracked):
        errors.append(f"required tracked file is missing: {required}")

    for relative in files:
        parts = set(relative.split("/"))
        normalized = relative.lower()
        forbidden = sorted(
            candidate
            for candidate in FORBIDDEN_TRACKED_PARTS
            if candidate.lower() in parts or normalized == candidate.lower() or normalized.startswith(candidate.lower() + "/")
        )
        if forbidden:
            errors.append(f"generated/local path is tracked: {relative}")
    return errors


def check_markdown_links(files: list[str]) -> list[str]:
    errors: list[str] = []
    for relative in files:
        if not relative.lower().endswith(".md"):
            continue
        source = ROOT / relative
        if not source.exists():
            errors.append(f"tracked Markdown file is missing: {relative}")
            continue
        text = source.read_text(encoding="utf-8")
        for match in MARKDOWN_LINK_RE.finditer(text):
            target = match.group(1).strip()
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = target.split("#", 1)[0].split("?", 1)[0]
            if not target:
                continue
            resolved = (source.parent / target).resolve()
            if not resolved.exists():
                errors.append(f"broken Markdown link in {relative}: {match.group(1)}")
    return errors


def check_deployment_manifest() -> list[str]:
    errors: list[str] = []
    path = ROOT / "config" / "deployment-manifest.json"
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"deployment manifest cannot be read: {exc}"]

    for key in ("manifestVersion", "productName", "applicationRootModes", "protectedDuringUpgrade"):
        if key not in manifest:
            errors.append(f"deployment manifest missing key: {key}")

    protected = set(manifest.get("protectedDuringUpgrade", []))
    for required in (".env", "config\\meter_config.json", "data", "logs", "backups"):
        if required not in protected:
            errors.append(f"deployment manifest does not protect during upgrade: {required}")

    excluded = set(manifest.get("releaseContentsExclude", []))
    for required in (".git", ".venv", "node_modules", "docs\\archive"):
        if required not in excluded:
            errors.append(f"deployment manifest does not exclude from releases: {required}")
    if "frontend\\dist" in excluded:
        errors.append("deployment manifest incorrectly excludes shipped frontend\\dist")
    return errors


def check_removed_references(files: list[str]) -> list[str]:
    errors: list[str] = []
    for relative in files:
        path = ROOT / relative
        if path.suffix.lower() not in {".md", ".ps1", ".py", ".iss", ".bat", ".vbs", ".yml", ".yaml"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace").replace("\\", "/")
        for removed in sorted(REMOVED_DOC_REFERENCES):
            if removed in text and relative != "scripts/validate_repository.py":
                errors.append(f"stale removed-doc reference in {relative}: {removed}")
    return errors


def main() -> int:
    try:
        files = tracked_files()
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"Repository hygiene check could not inspect Git: {exc}", file=sys.stderr)
        return 2

    errors = []
    errors.extend(check_tracked_paths(files))
    errors.extend(check_markdown_links(files))
    errors.extend(check_deployment_manifest())
    errors.extend(check_removed_references(files))

    if errors:
        print("Repository hygiene check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Repository hygiene check passed for {len(files)} tracked files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
