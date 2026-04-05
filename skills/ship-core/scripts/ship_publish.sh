#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ship_publish.sh [--config ship.yaml] [--dry-run] [--no-pr] [--release]

Reads publish commands from ship.yaml and runs push, PR, and optional release
commands for the current branch.
EOF
}

CONFIG="ship.yaml"
DRY_RUN=0
NO_PR=0
DO_RELEASE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --config)
      CONFIG="${2:-}"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --no-pr)
      NO_PR=1
      shift
      ;;
    --release)
      DO_RELEASE=1
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    --*)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
    *)
      echo "Unexpected argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

readarray -t COMMANDS < <(python3 - "$CONFIG" <<'PY'
import sys
from pathlib import Path
import yaml

config_path = Path(sys.argv[1])
config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
commands = config.get("commands", {})
policy = config.get("policy", {})

print(commands.get("publish_push") or "")
print(commands.get("publish_pr") or "")
print(commands.get("publish_release") or "")
print("true" if policy.get("require_pr", True) else "false")
PY
)

PUSH_COMMAND="${COMMANDS[0]:-}"
PR_COMMAND="${COMMANDS[1]:-}"
RELEASE_COMMAND="${COMMANDS[2]:-}"
REQUIRE_PR="${COMMANDS[3]:-true}"

if [[ -z "$PUSH_COMMAND" ]]; then
  echo "commands.publish_push is required" >&2
  exit 1
fi

if [[ $DRY_RUN -eq 1 ]]; then
  echo "push: $PUSH_COMMAND"
  if [[ $NO_PR -eq 0 && "$REQUIRE_PR" == "true" && -n "$PR_COMMAND" ]]; then
    echo "pr: $PR_COMMAND"
  fi
  if [[ $DO_RELEASE -eq 1 && -n "$RELEASE_COMMAND" ]]; then
    echo "release: $RELEASE_COMMAND"
  fi
  exit 0
fi

bash -lc "$PUSH_COMMAND"
if [[ $NO_PR -eq 0 && "$REQUIRE_PR" == "true" && -n "$PR_COMMAND" ]]; then
  bash -lc "$PR_COMMAND"
fi
if [[ $DO_RELEASE -eq 1 && -n "$RELEASE_COMMAND" ]]; then
  bash -lc "$RELEASE_COMMAND"
fi
