#!/usr/bin/env python3
"""Validate catalog.json against the published skills directories."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "catalog.json"
SKILLS_DIR = ROOT / "skills"

REQUIRED_FIELDS = {
    "name",
    "path",
    "summary",
    "supported_agents",
    "status",
    "featured",
}


def fail(message: str) -> int:
    print(f"[FAIL] {message}")
    return 1


def main() -> int:
    if not CATALOG.exists():
        return fail("catalog.json is missing")

    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    skills = data.get("skills")
    if not isinstance(skills, list) or not skills:
        return fail("catalog.json must contain a non-empty 'skills' list")

    seen_names: set[str] = set()
    seen_paths: set[str] = set()
    catalog_paths: set[str] = set()

    for entry in skills:
        if not isinstance(entry, dict):
            return fail("every catalog entry must be an object")

        missing = REQUIRED_FIELDS - set(entry)
        if missing:
            return fail(f"catalog entry is missing required fields: {sorted(missing)}")

        name = entry["name"]
        path = entry["path"]
        if name in seen_names:
            return fail(f"duplicate skill name: {name}")
        if path in seen_paths:
            return fail(f"duplicate skill path: {path}")
        if not isinstance(entry["supported_agents"], list) or not entry["supported_agents"]:
            return fail(f"{name} must declare at least one supported agent")

        skill_dir = ROOT / path
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            return fail(f"{name} points to missing SKILL.md at {path}/SKILL.md")

        seen_names.add(name)
        seen_paths.add(path)
        catalog_paths.add(skill_dir.resolve().as_posix())

    disk_paths = {
        path.resolve().as_posix()
        for path in SKILLS_DIR.iterdir()
        if path.is_dir() and (path / "SKILL.md").exists()
    }

    missing_from_catalog = sorted(disk_paths - catalog_paths)
    missing_on_disk = sorted(catalog_paths - disk_paths)
    if missing_from_catalog:
        return fail(f"skills missing from catalog.json: {missing_from_catalog}")
    if missing_on_disk:
        return fail(f"catalog.json references missing skill dirs: {missing_on_disk}")

    print("[PASS] catalog.json matches the published skill folders")
    return 0


if __name__ == "__main__":
    sys.exit(main())
