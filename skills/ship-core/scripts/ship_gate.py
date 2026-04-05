#!/usr/bin/env python3
"""Run public ship command phases and normalize results."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ship_lib import command_available, load_config, run_shell


PHASE_STEPS = {
    "preflight": ("preflight",),
    "tests": ("tests",),
    "gate": ("gate",),
    "all": ("preflight", "tests", "gate"),
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run ship gate commands")
    parser.add_argument("--config", default="ship.yaml", help="Path to ship config")
    parser.add_argument(
        "--phase",
        choices=sorted(PHASE_STEPS),
        default="all",
        help="Command phase to run",
    )
    parser.add_argument("--dry-run", action="store_true", help="Do not execute commands")
    parser.add_argument("--json-output", default=None, help="Optional output path")
    args = parser.parse_args()

    cwd = Path.cwd()
    config = load_config(args.config)
    steps: list[dict] = []
    decision = "GO"

    def mark_decision(required: bool) -> None:
        nonlocal decision
        if required:
            decision = "BLOCK"
        elif decision == "GO":
            decision = "WARN"

    for name in PHASE_STEPS[args.phase]:
        command = config["commands"].get(name)
        if not command:
            steps.append({"name": name, "status": "skipped", "reason": "no command configured"})
            continue
        if not command_available(command):
            status = "block" if name in {"preflight", "gate"} else "warn"
            steps.append(
                {
                    "name": name,
                    "command": command,
                    "status": status,
                    "reason": "command binary not found",
                }
            )
            mark_decision(status == "block")
            continue
        if args.dry_run:
            steps.append({"name": name, "command": command, "status": "planned"})
            continue
        result = run_shell(command, cwd)
        status = "pass" if result.returncode == 0 else ("block" if name in {"preflight", "gate"} else "warn")
        steps.append(
            {
                "name": name,
                "command": command,
                "status": status,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        )
        if status != "pass":
            mark_decision(status == "block")

    for name, scanner in config["scanners"].items():
        if not scanner.get("enabled"):
            continue
        command = scanner.get("command")
        required = bool(scanner.get("required"))
        if not command:
            steps.append({"name": name, "status": "skipped", "reason": "scanner missing command"})
            continue
        if not command_available(command):
            status = "block" if required else "warn"
            steps.append(
                {
                    "name": name,
                    "command": command,
                    "status": status,
                    "reason": "scanner binary not found",
                }
            )
            mark_decision(required)
            continue
        if args.dry_run:
            steps.append({"name": name, "command": command, "status": "planned"})
            continue
        result = run_shell(command, cwd)
        status = "pass" if result.returncode == 0 else ("block" if required else "warn")
        steps.append(
            {
                "name": name,
                "command": command,
                "status": status,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        )
        if status != "pass":
            mark_decision(required)

    if config["policy"]["block_on_warnings"] and decision == "WARN":
        decision = "BLOCK"

    payload = {
        "ok": decision != "BLOCK",
        "decision": decision,
        "phase": args.phase,
        "steps": steps,
    }
    if args.json_output:
        Path(args.json_output).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
