---
name: ship-claude
description: Claude Code adapter for ship-core with guidance for parallel review, doc sync, and PR preparation
metadata: {"ragnos":{"featured":true,"supportedAgents":["claude-code"],"status":"active","summary":"Claude Code wrapper for ship-core."}}
---

# Ship Claude

`ship-claude` is the Claude Code runtime adapter for `ship-core`.

Read `../ship-core/SKILL.md` first for the shared workflow. This adapter adds Claude Code-specific execution notes and keeps the repo-specific commands replaceable.

## When To Use

Use this skill when a Claude Code user wants to:

- ship a branch,
- review and prep a PR,
- reuse the same ship contract across repos without private RAGnos dependencies.

## Claude Code Runtime Guidance

- Start with repo discovery, not assumptions.
- Parallelize independent reads, checks, and doc updates when the repo and tooling support it.
- Keep review findings concrete and severity-based.
- Treat the repo's own validation and publish commands as the source of truth, not the adapter text.

## Claude-Specific Flow

### 1. Discover

- inspect the branch,
- identify changed files,
- locate repo contribution, release, or validation docs,
- map the `ship-core` hooks to local commands.

### 2. Run Parallel Tracks When Safe

Once the docs impact and validation baseline are known:

- docs sync can run independently of semantic review,
- review can fan out by file category or risk area,
- publish waits until blockers are resolved.

### 3. Publish

If the user asked for a full ship:

- push the branch,
- open or update a PR,
- create a release only if the repo actually uses tags and releases as a public distribution surface.

### 4. Report

Keep the report short:

- findings fixed,
- commands run,
- warnings left,
- PR or release URL.

## Good Trigger Phrases

Common requests that should activate this adapter:

- "/ship"
- "ship this"
- "make this PR-ready"
- "review and publish this branch"

## Portable Fallback

If a repo has no explicit ship automation, Claude Code can still apply the public contract:

1. run the baseline validation command,
2. review the delta,
3. fix blockers,
4. stage intended files only,
5. commit,
6. push,
7. open a PR,
8. stop before merge unless the user explicitly asks for merge handling.
