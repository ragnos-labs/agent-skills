#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ship_commit.sh --message "scope: summary" [--dry-run] [--allow-dirty] <file1> [file2...]

Stages the listed files only, blocks if unrelated unstaged changes exist unless
--allow-dirty is set, and creates a git commit.
EOF
}

MESSAGE=""
DRY_RUN=0
ALLOW_DIRTY=0
FILES=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --message|-m)
      MESSAGE="${2:-}"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --allow-dirty)
      ALLOW_DIRTY=1
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
      FILES+=("$1")
      shift
      ;;
  esac
done

if [[ -z "$MESSAGE" ]]; then
  echo "--message is required" >&2
  exit 2
fi

if [[ ${#FILES[@]} -eq 0 ]]; then
  echo "At least one file is required" >&2
  exit 2
fi

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || {
  echo "Not inside a git repo" >&2
  exit 1
}

mapfile -t UNSTAGED < <(git diff --name-only)
if [[ $ALLOW_DIRTY -eq 0 ]]; then
  for path in "${UNSTAGED[@]}"; do
    skip=0
    for target in "${FILES[@]}"; do
      if [[ "$path" == "$target" ]]; then
        skip=1
        break
      fi
    done
    if [[ $skip -eq 0 ]]; then
      echo "Refusing to commit with unrelated unstaged changes: $path" >&2
      echo "Re-run with --allow-dirty if that is intentional." >&2
      exit 1
    fi
  done
fi

git add -- "${FILES[@]}"

if [[ $DRY_RUN -eq 1 ]]; then
  echo "Planned commit message: $MESSAGE"
  git diff --cached --name-only
  exit 0
fi

git commit -m "$MESSAGE"
