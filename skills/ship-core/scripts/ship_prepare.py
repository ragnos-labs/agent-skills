#!/usr/bin/env python3
"""Profile the current branch for ship."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ship_lib import (
    changed_files,
    docs_changed,
    ensure_cache_dir,
    file_bucket,
    git_shortstat,
    git_stdout,
    load_config,
)


def determine_scope(
    head_sha: str,
    changed: list[str],
    buckets: dict[str, int],
    commit_count: int,
    use_cache: bool,
    fresh: bool,
    cache_path: Path,
) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if fresh:
        return "full", ["--fresh requested"]
    if not changed:
        reasons.append("branch matches base")
        return "cached", reasons
    if buckets["critical"] > 0:
        reasons.append("critical-path files changed")
        return "full", reasons
    if len(changed) > 20 or commit_count > 10:
        reasons.append("branch is large")
        return "full", reasons
    if use_cache and cache_path.exists():
        try:
            previous = json.loads(cache_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            previous = {}
        if previous.get("head_sha") == head_sha:
            reasons.append("matching cache state found")
            return "cached", reasons
    reasons.append("default delta scope")
    return "delta", reasons


def main() -> int:
    parser = argparse.ArgumentParser(description="Profile the current branch for ship")
    parser.add_argument("--config", default="ship.yaml", help="Path to ship config")
    parser.add_argument("--base", default=None, help="Base branch override")
    parser.add_argument("--fresh", action="store_true", help="Force a full run")
    parser.add_argument("--json-output", default=None, help="Optional output path")
    args = parser.parse_args()

    cwd = Path.cwd()
    config = load_config(args.config)
    base_branch = args.base or config["base_branch"]
    changed = changed_files(cwd, base_branch)
    head_sha = git_stdout(cwd, "rev-parse", "HEAD")
    branch = git_stdout(cwd, "branch", "--show-current") or git_stdout(cwd, "rev-parse", "--short", "HEAD")
    commit_count = int(git_stdout(cwd, "rev-list", "--count", f"{base_branch}..HEAD") or "0")
    buckets = {"critical": 0, "code": 0, "mechanical": 0}
    bucketed_files: dict[str, list[str]] = {name: [] for name in buckets}
    for path in changed:
        bucket = file_bucket(path, config)
        buckets[bucket] += 1
        bucketed_files[bucket].append(path)
    stats = git_shortstat(cwd, f"{base_branch}...HEAD")
    cache_path = ensure_cache_dir(cwd) / "prepare.json"
    scope, reasons = determine_scope(
        head_sha=head_sha,
        changed=changed,
        buckets=buckets,
        commit_count=commit_count,
        use_cache=config["policy"]["use_cache"],
        fresh=args.fresh,
        cache_path=cache_path,
    )
    payload = {
        "ok": True,
        "branch": branch,
        "base_branch": base_branch,
        "head_sha": head_sha,
        "scope": scope,
        "scope_reasons": reasons,
        "changed_files": changed,
        "changed_count": len(changed),
        "commit_count": commit_count,
        "insertions": stats["insertions"],
        "deletions": stats["deletions"],
        "docs_changed": docs_changed(changed, config),
        "bucket_counts": buckets,
        "bucketed_files": bucketed_files,
        "planned_commands": {
            name: command
            for name, command in config["commands"].items()
            if command
        },
    }

    if config["policy"]["use_cache"]:
        cache_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if args.json_output:
        Path(args.json_output).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
