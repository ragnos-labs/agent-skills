---
name: ship
description: Release workflow that takes a branch from done coding to reviewed, committed, pushed, and PR-ready. Works with Claude Code and Codex.
---

# Ship

Takes a branch from "done coding" to "reviewed, committed, pushed, and PR-ready."

## Triggers

Use this skill when the user says:

- `/ship`
- "ship this branch"
- "ship this"
- "make this PR-ready"
- "review and open a PR"
- "prepare this for release"
- "publish the current work"

## Rules

These apply on every run:

- Run from the current branch unless the user asks to switch.
- Stage specific files only. Never the whole worktree.
- Fix security findings before publish.
- Do not silently defer review findings.
- Never merge without explicit user instruction.

## Flags

- `--no-review`: skip review, keep validation and publish
- `--review-only`: stop after review and reporting
- `--dry-run`: report what would be staged, validated, and published without doing it
- `--fresh`: ignore cached rerun state, do a full pass
- `--quick`: allow lighter non-security checks for small changes
- `--no-pr`: push the branch without opening a PR

## Phase Model

### Phase 0: Classify

- Inspect branch scope and changed files.
- Decide whether the run is full, delta-scoped, or cacheable.
- Outline likely PR and release material early.

### Phase 1: Preflight

Run the repo's baseline validation before review.

Extension hook: `preflight`

Typical checks: lint, unit tests, smoke tests, secret scanning, docs or schema validation.

### Phase 1.5: Docs Sync

If the change affects docs, examples, screenshots, or install instructions, update those before publish.

Extension hook: `docs_sync`

### Phase 2: Review

Review the actual delta, not the entire repo. Fan out by file category or risk area when useful.

Extension hook: `review`

Findings use three severities:

- `BLOCK`: fix before publish
- `WARN`: can publish, but report clearly
- `NOTE`: real improvement, not a blocker

Review for: correctness, process safety, security, release regression risk, missing tests or docs.

### Phase 3: Stage and Commit

After accepted fixes land:

- Stage intended files only.
- Write a clear commit message.
- Stop here if the user asked for `--review-only` or `--dry-run`.

### Phase 4: Quality Gate

Run the repo's post-commit gate.

Extension hook: `gate`

Gate result: `0` = GO, `1` = WARN, `2` = BLOCK.

Can combine: targeted regression tests, security checks, packaging checks, release artifact validation.

### Phase 5: Publish

Extension hook: `publish`

- Push the branch.
- Open or update a PR.
- Tag and release when the repo's release process calls for it.
- Include exact install examples in release notes if the repo distributes installable artifacts.

### Phase 6: Report

Return a short report:

- Rerun scope used
- Findings fixed
- Remaining warnings
- Validation commands run
- Publish result
- PR or release URL if created

## Extension Hooks

Map these to your repo's own commands. The skill does not assume any specific tooling.

| Hook | Purpose |
|---|---|
| `preflight` | Fast blocking validation before review |
| `docs_sync` | Update docs, examples, or screenshots affected by the change |
| `review` | Semantic review of the actual delta |
| `tests` | Targeted or full tests for confidence |
| `gate` | Post-commit go/warn/block check |
| `publish` | Push, PR creation, tag, and release handling |

## Rerun Model

Use prior ship state to save time, not to lower quality.

- `cached`: same HEAD, reuse prior non-security work if trustworthy
- `delta`: scope review and non-security checks to files changed since last ship
- `full`: no trustworthy prior state, or the change is large enough that full review is cheaper

Security validation is always treated as fresh.
