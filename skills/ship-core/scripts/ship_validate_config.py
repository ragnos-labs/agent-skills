#!/usr/bin/env python3
"""Validate ship.yaml."""

from __future__ import annotations

import argparse
import json

from ship_lib import command_available, validate_config_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate ship.yaml")
    parser.add_argument("--config", default="ship.yaml", help="Path to ship config")
    parser.add_argument("--check-commands", action="store_true", help="Check binaries for configured commands")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()

    result = validate_config_file(args.config)
    warnings = list(result.warnings)
    errors = list(result.errors)

    if args.check_commands and result.ok:
        commands = result.config["commands"]
        for key, command in commands.items():
            if command and not command_available(command):
                level = "error" if key in {"publish_push", "publish_pr"} else "warning"
                message = f"commands.{key} binary is not available for '{command}'"
                if level == "error":
                    errors.append(message)
                else:
                    warnings.append(message)
        for name, scanner in result.config["scanners"].items():
            command = scanner.get("command")
            if scanner.get("enabled") and command and not command_available(command):
                message = f"scanners.{name} binary is not available for '{command}'"
                if scanner.get("required"):
                    errors.append(message)
                else:
                    warnings.append(message)

    payload = {
        "ok": not errors,
        "config_path": args.config,
        "errors": errors,
        "warnings": warnings,
    }

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        if payload["ok"]:
            print(f"[PASS] {args.config} is valid")
        for warning in warnings:
            print(f"[WARN] {warning}")
        for error in errors:
            print(f"[ERROR] {error}")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
