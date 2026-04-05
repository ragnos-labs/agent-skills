---
name: ship-core
description: Shared ship workflow contract for reviewing, validating, publishing, and releasing code changes across coding agents
metadata: {"ragnos":{"featured":true,"supportedAgents":["codex","claude-code"],"status":"active","summary":"Runtime-neutral ship workflow with explicit extension hooks."}}
---

# Ship Core

`ship-core` is the runtime-neutral skill for taking a branch from "done coding" to "reviewed, validated, pushed, and release-ready."

It is intentionally public-safe:

- no private RAGnos commands,
- no internal docs dependency,
- no ClickUp, GraphRAG, or private infra assumptions,
- no hidden merge policy.

Use this skill through an adapter such as `ship-codex` or `ship-claude`.

Optional helper resources live in `scripts/` and `references/`.

- `scripts/` are optional support files for repos that want deterministic setup or gating.
- `references/` hold the config contract, examples, findings format, and troubleshooting notes.
- If a repo does not use the helper scripts, the skill still works as a markdown workflow.

## When To Use

Use `ship-core` when the user wants to:

- ship the current branch,
- review and prepare a PR,
- run a reusable publish checklist,
- standardize how an agent decides whether work is ready to push.

## Non-Negotiable Rules

- Run from the current branch unless the user asks to switch.
- Stage specific files only.
- Security-sensitive findings are fixed before publish.
- Review findings are not silently deferred.
- Never merge without explicit user instruction.
- Release notes should point users to tags or releases, not to `main`.

## Recommended Startup

For a repo that does not already have a clear hook map:

1. Read `references/config-file.md`.
2. Generate a starter config with `python3 skills/ship-core/scripts/ship_init.py --write ship.yaml`.
3. Validate it with `python3 skills/ship-core/scripts/ship_validate_config.py --config ship.yaml`.
4. Use the generated file as the source of truth for commands and policy.

If the host repo already has a strong workflow contract, you can skip the helper scripts and map the hooks directly from repo docs.

## Public Flags

Adapters may expose additional flags, but the shared public meanings are:

- `--no-review`: skip the review phase, keep validation and publish
- `--review-only`: stop after review and reporting
- `--dry-run`: report what would be staged, validated, and published
- `--fresh`: ignore cached rerun state and perform a full pass
- `--review`: force a full review even when the rerun scope is narrow
- `--quick`: allow lighter non-security checks for small changes
- `--no-pr`: publish the branch without opening a PR

## Shared Phase Model

### Phase 0: Classify

- inspect branch scope,
- identify changed files,
- decide whether the run is full, delta-scoped, or cacheable,
- outline likely PR and release material early.

### Phase 1: Preflight

Run the repo's baseline validation hooks before semantic review.

Typical extension points:

- lint,
- unit tests,
- smoke tests,
- docs or schema validation,
- secret scanning.

### Phase 1.5: Docs Sync

If the change affects docs, examples, screenshots, or install instructions, update those before publish.

This phase may run in parallel with review once the docs impact is clear.

### Phase 2: Review

Review the actual delta, not the entire repository.

Minimum expectations:

- correctness,
- process safety,
- security,
- release regression risk,
- missing tests or docs.

Severity levels:

- `BLOCK`: must fix before publish
- `WARN`: can publish, but report clearly
- `NOTE`: real improvement, not a blocker

### Phase 3: Stage And Commit

After accepted fixes land:

- stage the intended files only,
- write a clear commit message,
- stop here if the user requested review-only or dry-run behavior.

### Phase 4: Quality Gate

Run the repo's post-commit gate.

This can combine:

- targeted regression tests,
- security checks,
- packaging checks,
- release artifact validation,
- repo-specific policy checks.

Gate semantics:

- `0` or equivalent: `GO`
- `1` or equivalent: `WARN`
- `2` or equivalent: `BLOCK`

### Phase 5: Publish

If the user wants a full ship:

- push the branch,
- open or update a PR,
- tag and release when the repo's release process calls for it,
- include exact install examples in release notes if the repo distributes installable artifacts.

### Phase 6: Report

Return a short ship report with:

- rerun scope used,
- findings fixed,
- remaining warnings,
- validation commands run,
- publish result,
- release or PR link if created.

## Extension Hooks

Public `ship-core` assumes you will map these hooks to your own repo:

| Hook | What it should do |
|------|-------------------|
| `preflight` | Fast blocking validation before review |
| `docs_sync` | Update docs, examples, or screenshots affected by the change |
| `review` | Semantic review of the actual delta |
| `tests` | Targeted or full tests needed for confidence |
| `gate` | Post-commit go/warn/block check |
| `publish` | Push, PR creation, tag, and release handling |

See `references/extension-hooks.md` for a portable mapping checklist.
See `references/config-file.md` for a concrete `ship.yaml` schema.
See `references/findings-format.md` for the public finding shape.

## Rerun Model

Use prior ship state only to save time, not to lower quality.

- `cached`: same HEAD, reuse prior non-security work if trustworthy
- `delta`: scope review and non-security checks to files changed since last ship
- `full`: no trustworthy prior state, or the change is large enough that full review is cheaper than guessing

Security-critical validation should be treated as fresh unless the host repo has a strong reason to trust caching.

## Gotchas

- Do not invent repo commands. Read them from `ship.yaml` or repo docs.
- Do not stage unrelated files just because a formatter touched them.
- Treat missing scanner binaries as `WARN` unless the config marks them required.
- Keep the final report short and structured; use `BLOCK`, `WARN`, and `NOTE` consistently.

## What Stays Private

The public contract does not assume:

- internal task trackers,
- internal knowledge systems,
- company-specific release gates,
- private evaluator services,
- proprietary security tooling.

If you have those internally, expose them through adapter hooks rather than presenting them as universal defaults.
