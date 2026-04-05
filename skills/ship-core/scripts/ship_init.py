#!/usr/bin/env python3
"""Generate a starter ship.yaml for the current repo."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ship_lib import DEFAULT_CONFIG, dump_yaml


PRESETS = {
    "javascript": {
        "commands": {
            "preflight": "npm test",
            "tests": "npm test",
            "gate": "npm run lint",
        },
        "review": {
            "critical_paths": ["src/auth/**", "src/security/**", ".github/workflows/**"],
            "mechanical_paths": ["docs/**", "tests/**", "**/*.md"],
        },
    },
    "python": {
        "commands": {
            "preflight": "python3 -m unittest discover -s tests -p 'test_*.py'",
            "tests": "python3 -m unittest discover -s tests -p 'test_*.py'",
            "gate": "python3 -m compileall .",
        },
        "review": {
            "critical_paths": ["app/auth/**", "app/security/**", ".github/workflows/**"],
            "mechanical_paths": ["docs/**", "tests/**", "**/*.md"],
        },
    },
    "polyglot-docs": {
        "commands": {
            "preflight": "npm test && python3 -m unittest discover -s tests -p 'test_*.py'",
            "docs_sync": "python3 -m unittest discover -s tests -p 'test_*.py'",
            "tests": "npm test && python3 -m unittest discover -s tests -p 'test_*.py'",
            "gate": "npm run lint",
        },
        "review": {
            "critical_paths": ["src/auth/**", "services/**/auth/**", ".github/workflows/**"],
            "mechanical_paths": ["docs/**", "tests/**", "**/*.md", "**/*.json"],
        },
        "docs": {"paths": ["docs/**", "**/*.md", "examples/**"]},
    },
}


def detect_preset(cwd: Path) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if (cwd / "package.json").exists():
        reasons.append("package.json found")
    if (cwd / "pyproject.toml").exists() or (cwd / "requirements.txt").exists():
        reasons.append("python project files found")
    if (cwd / "docs").exists():
        reasons.append("docs/ found")

    if "package.json found" in reasons and any("python" in item for item in reasons):
        return "polyglot-docs", reasons
    if "package.json found" in reasons:
        return "javascript", reasons
    if any("python" in item for item in reasons):
        return "python", reasons
    return "polyglot-docs", ["no strong preset signals found"]


def build_config(preset: str) -> dict:
    return {
        **DEFAULT_CONFIG,
        **PRESETS[preset],
        "commands": {**DEFAULT_CONFIG["commands"], **PRESETS[preset].get("commands", {})},
        "review": {**DEFAULT_CONFIG["review"], **PRESETS[preset].get("review", {})},
        "docs": {**DEFAULT_CONFIG["docs"], **PRESETS[preset].get("docs", {})},
        "policy": {**DEFAULT_CONFIG["policy"]},
        "scanners": {key: value.copy() for key, value in DEFAULT_CONFIG["scanners"].items()},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a starter ship.yaml")
    parser.add_argument("--preset", choices=sorted(PRESETS), default=None, help="Starter preset")
    parser.add_argument("--write", default="ship.yaml", help="Output path")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing config")
    args = parser.parse_args()

    cwd = Path.cwd()
    preset, reasons = detect_preset(cwd)
    selected = args.preset or preset
    output_path = Path(args.write)

    if output_path.exists() and not args.force:
        print(f"[ERROR] {output_path} already exists. Re-run with --force to overwrite.", file=sys.stderr)
        return 1

    config = build_config(selected)
    dump_yaml(output_path, config)
    print(f"Wrote {output_path} using preset '{selected}'.")
    print(f"Detection: {', '.join(reasons)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
