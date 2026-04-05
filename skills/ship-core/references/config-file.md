# `ship.yaml`

Use `ship.yaml` when a repo wants one explicit file for `ship` commands and policy.

The file lives at repo root.

## Version 1 shape

```yaml
version: 1
base_branch: main
commands:
  preflight: npm test
  docs_sync: null
  tests: npm test
  gate: npm run lint
  publish_push: git push -u origin HEAD
  publish_pr: gh pr create --fill
  publish_release: null
review:
  critical_paths:
    - src/auth/**
    - .github/workflows/**
  mechanical_paths:
    - docs/**
    - tests/**
    - "**/*.md"
  always_review_paths: []
policy:
  require_pr: true
  allow_no_review: true
  use_cache: true
  block_on_warnings: false
docs:
  paths:
    - docs/**
    - "**/*.md"
scanners:
  gitleaks:
    enabled: false
    required: false
    command: null
  semgrep:
    enabled: false
    required: false
    command: null
  actionlint:
    enabled: false
    required: false
    command: null
```

## Rules

- `commands.publish_push` is required.
- `commands.publish_pr` is required when `policy.require_pr` is `true`.
- Missing optional scanner binaries should become `WARN`.
- Missing required scanner binaries should become `BLOCK`.
- `critical_paths` should be used for auth, security, deploy, secrets, and similar high-risk areas.
- `mechanical_paths` should be used for docs, fixtures, generated files, and low-risk config.

## Helper scripts

Use these optional helpers when they reduce ambiguity:

- `scripts/ship_init.py` writes a starter `ship.yaml`
- `scripts/ship_validate_config.py` validates the file
- `scripts/ship_prepare.py` profiles the branch and planned run
- `scripts/ship_gate.py` executes configured commands and normalizes `GO | WARN | BLOCK`
