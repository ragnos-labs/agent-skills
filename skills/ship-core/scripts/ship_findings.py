#!/usr/bin/env python3
"""Aggregate and filter findings for public ship."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from fnmatch import fnmatch
from pathlib import Path

import yaml

from ship_lib import normalize_finding, sort_findings


def load_findings(path: Path) -> list[dict]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        if isinstance(raw.get("findings"), list):
            return [normalize_finding(item, source=path.stem) for item in raw["findings"]]
        if all(key in raw for key in ("file", "severity", "issue")):
            return [normalize_finding(raw, source=path.stem)]
        return []
    if isinstance(raw, list):
        return [normalize_finding(item, source=path.stem) for item in raw if isinstance(item, dict)]
    return []


def load_rules(path: Path | None) -> list[dict]:
    if not path or not path.exists():
        return []
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        return []
    rules = raw.get("rules", [])
    return rules if isinstance(rules, list) else []


def is_suppressed(finding: dict, rules: list[dict]) -> tuple[bool, str | None]:
    for rule in rules:
        expires_at = rule.get("expires_at")
        if expires_at and date.fromisoformat(str(expires_at)) < date.today():
            continue
        if finding["severity"] not in rule.get("severity_filter", []):
            continue
        if not fnmatch(finding["file"], rule.get("scope", "*")):
            continue
        pattern = rule.get("pattern", "")
        haystack = " ".join((finding["issue"], finding["code"]))
        if pattern and re.search(pattern, haystack, re.IGNORECASE):
            return True, rule.get("rule_id")
    return False, None


def main() -> int:
    parser = argparse.ArgumentParser(description="Aggregate and filter ship findings")
    parser.add_argument("--input", action="append", required=True, help="JSON file with findings")
    parser.add_argument("--suppressions", default=None, help="Optional YAML suppression registry")
    parser.add_argument("--format", choices=("json", "markdown"), default="json", help="Output format")
    parser.add_argument("--json-output", default=None, help="Optional output path")
    args = parser.parse_args()

    findings: list[dict] = []
    for raw_path in args.input:
        findings.extend(load_findings(Path(raw_path)))

    rules = load_rules(Path(args.suppressions).resolve() if args.suppressions else None)
    kept: list[dict] = []
    suppressed: list[dict] = []
    for finding in findings:
        matched, rule_id = is_suppressed(finding, rules)
        if matched:
            suppressed.append({**finding, "suppressed_by": rule_id})
        else:
            kept.append(finding)

    kept = sort_findings(kept)
    payload = {"ok": True, "findings": kept, "suppressed": suppressed}
    if args.json_output:
        Path(args.json_output).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    if args.format == "markdown":
        if not kept:
            print("No findings.")
            return 0
        for item in kept:
            print(f"- `{item['severity']}` {item['file']}:{item.get('line') or '?'} - {item['issue']}")
    else:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
