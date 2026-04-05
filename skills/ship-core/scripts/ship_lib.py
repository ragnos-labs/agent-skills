#!/usr/bin/env python3
"""Shared helpers for the public ship runtime."""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG_PATH = "ship.yaml"
DEFAULT_CACHE_DIR = ".ship-cache"
SUPPORTED_SCANNERS = ("gitleaks", "semgrep", "actionlint")
SEVERITY_ORDER = {"BLOCK": 0, "WARN": 1, "NOTE": 2}

DEFAULT_CONFIG: dict[str, Any] = {
    "version": 1,
    "base_branch": "main",
    "commands": {
        "preflight": None,
        "docs_sync": None,
        "tests": None,
        "gate": None,
        "publish_push": "git push -u origin HEAD",
        "publish_pr": "gh pr create --fill",
        "publish_release": None,
    },
    "review": {
        "critical_paths": [],
        "mechanical_paths": [],
        "always_review_paths": [],
    },
    "policy": {
        "require_pr": True,
        "allow_no_review": True,
        "use_cache": True,
        "block_on_warnings": False,
    },
    "docs": {
        "paths": ["docs/**", "**/*.md"],
    },
    "scanners": {
        name: {"enabled": False, "required": False, "command": None}
        for name in SUPPORTED_SCANNERS
    },
}


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str]
    warnings: list[str]
    config: dict[str, Any]


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = json.loads(json.dumps(base))
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def dump_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )


def resolve_config_path(path: str | None) -> Path:
    return Path(path or DEFAULT_CONFIG_PATH).resolve()


def load_config(path: str | None = None) -> dict[str, Any]:
    config_path = resolve_config_path(path)
    raw = load_yaml(config_path) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"{config_path} must contain a YAML mapping")
    return deep_merge(DEFAULT_CONFIG, raw)


def validate_config_data(config: dict[str, Any]) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(config.get("version"), int):
        errors.append("version must be an integer")

    if not isinstance(config.get("base_branch"), str) or not config["base_branch"].strip():
        errors.append("base_branch must be a non-empty string")

    for section in ("commands", "review", "policy", "docs", "scanners"):
        if not isinstance(config.get(section), dict):
            errors.append(f"{section} must be a mapping")

    commands = config.get("commands", {})
    for key in (
        "preflight",
        "docs_sync",
        "tests",
        "gate",
        "publish_push",
        "publish_pr",
        "publish_release",
    ):
        value = commands.get(key)
        if value is not None and not isinstance(value, str):
            errors.append(f"commands.{key} must be a string or null")

    review = config.get("review", {})
    for key in ("critical_paths", "mechanical_paths", "always_review_paths"):
        value = review.get(key, [])
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            errors.append(f"review.{key} must be a list of strings")

    policy = config.get("policy", {})
    for key in ("require_pr", "allow_no_review", "use_cache", "block_on_warnings"):
        value = policy.get(key)
        if not isinstance(value, bool):
            errors.append(f"policy.{key} must be true or false")

    docs = config.get("docs", {})
    doc_paths = docs.get("paths", [])
    if not isinstance(doc_paths, list) or any(not isinstance(item, str) for item in doc_paths):
        errors.append("docs.paths must be a list of strings")

    scanners = config.get("scanners", {})
    for name, scanner in scanners.items():
        if not isinstance(scanner, dict):
            errors.append(f"scanners.{name} must be a mapping")
            continue
        if not isinstance(scanner.get("enabled"), bool):
            errors.append(f"scanners.{name}.enabled must be true or false")
        if not isinstance(scanner.get("required"), bool):
            errors.append(f"scanners.{name}.required must be true or false")
        command = scanner.get("command")
        if command is not None and not isinstance(command, str):
            errors.append(f"scanners.{name}.command must be a string or null")
        if scanner.get("enabled") and not command:
            errors.append(f"scanners.{name}.command is required when enabled is true")
        if name not in SUPPORTED_SCANNERS:
            warnings.append(f"scanners.{name} is not a built-in scanner name, but it will still run")

    if not commands.get("publish_push"):
        errors.append("commands.publish_push is required")

    if policy.get("require_pr") and not commands.get("publish_pr"):
        errors.append("commands.publish_pr is required when policy.require_pr is true")

    return ValidationResult(ok=not errors, errors=errors, warnings=warnings, config=config)


def validate_config_file(path: str | None = None) -> ValidationResult:
    return validate_config_data(load_config(path))


def command_binary(command: str | None) -> str | None:
    if not command:
        return None
    try:
        parts = shlex.split(command)
    except ValueError:
        return None
    if not parts:
        return None
    return parts[0]


def command_available(command: str | None) -> bool:
    binary = command_binary(command)
    if not binary:
        return False
    if os.path.sep in binary:
        return Path(binary).exists()
    return shutil.which(binary) is not None


def run_shell(command: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "-lc", command],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def git_stdout(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def git_shortstat(cwd: Path, diff_spec: str) -> dict[str, int]:
    out = git_stdout(cwd, "diff", diff_spec, "--shortstat")
    values = {"insertions": 0, "deletions": 0}
    for key in values:
        marker = "insertion" if key == "insertions" else "deletion"
        for token in out.split(","):
            token = token.strip()
            if marker in token:
                values[key] = int(token.split()[0])
    return values


def branch_diff_spec(cwd: Path, base_branch: str) -> str:
    preferred = f"{base_branch}...HEAD"
    result = subprocess.run(
        ["git", "diff", preferred, "--name-only"],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    return preferred if result.returncode == 0 else f"{base_branch}..HEAD"


def changed_files(cwd: Path, base_branch: str) -> list[str]:
    diff_spec = branch_diff_spec(cwd, base_branch)
    branch_out = git_stdout(cwd, "diff", diff_spec, "--name-only")
    worktree_out = git_stdout(cwd, "diff", "HEAD", "--name-only")
    untracked_out = git_stdout(cwd, "ls-files", "--others", "--exclude-standard")
    combined = [
        *[line for line in branch_out.splitlines() if line.strip()],
        *[line for line in worktree_out.splitlines() if line.strip()],
        *[line for line in untracked_out.splitlines() if line.strip()],
    ]
    deduped: list[str] = []
    seen: set[str] = set()
    for path in combined:
        if path not in seen:
            seen.add(path)
            deduped.append(path)
    return deduped


def file_bucket(path: str, config: dict[str, Any]) -> str:
    review = config["review"]
    docs = config["docs"]["paths"]

    if any(fnmatch(path, pattern) for pattern in review["critical_paths"]):
        return "critical"
    if any(fnmatch(path, pattern) for pattern in review["mechanical_paths"]):
        return "mechanical"
    if path.endswith((".md", ".json", ".yaml", ".yml")):
        return "mechanical"
    if any(fnmatch(path, pattern) for pattern in docs):
        return "mechanical"
    return "code"


def docs_changed(files: list[str], config: dict[str, Any]) -> bool:
    patterns = config["docs"]["paths"]
    return any(any(fnmatch(path, pattern) for pattern in patterns) for path in files)


def ensure_cache_dir(cwd: Path) -> Path:
    path = cwd / DEFAULT_CACHE_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def normalize_finding(raw: dict[str, Any], source: str | None = None) -> dict[str, Any]:
    severity = str(raw.get("severity") or "NOTE").upper()
    if severity not in SEVERITY_ORDER:
        severity = "NOTE"
    return {
        "file": str(raw.get("file") or ""),
        "line": raw.get("line"),
        "severity": severity,
        "issue": str(raw.get("issue") or ""),
        "fix": str(raw.get("fix") or ""),
        "source": str(raw.get("source") or source or "unknown"),
        "code": str(raw.get("code") or ""),
    }


def sort_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        findings,
        key=lambda item: (
            SEVERITY_ORDER.get(item.get("severity", "NOTE"), 99),
            item.get("file", ""),
            int(item.get("line") or 0),
        ),
    )
