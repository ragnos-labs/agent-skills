---
name: ship-codex
description: Codex adapter for ship-core with guidance for tool usage, validation flow, and publish behavior
metadata: {"ragnos":{"featured":true,"supportedAgents":["codex"],"status":"active","summary":"Codex wrapper for ship-core."}}
---

# Ship Codex

`ship-codex` is the Codex runtime adapter for `ship-core`.

Read `../ship-core/SKILL.md` first for the shared workflow contract. This adapter only adds Codex-specific execution guidance.

## When To Use

Use this skill when a Codex user wants to:

- ship the current branch,
- prepare a reviewed PR,
- run the repo's validation and publish path with an explicit agent workflow.

## Codex Runtime Guidance

- Inspect the repo before acting. Start with branch state, changed files, and any repo-local contribution or release docs.
- Use parallel reads when the retrieval steps are independent.
- Keep edits precise. Change the smallest set of files that closes the real findings.
- Before publishing, verify the exact files being staged and the commands actually run.
- Keep the final ship report short and operational.

## Codex-Specific Flow

### 1. Build Context

- read git status,
- read the diff,
- find the repo's validation and publish commands,
- identify whether docs or examples changed.

### 2. Apply `ship-core`

Run the shared phase model from `ship-core` using the repo's own hooks.

### 3. Publish Carefully

When the user asked for a full ship:

- push only after blockers are fixed,
- open or update the PR,
- if the repo distributes installable artifacts, include exact install commands in the release notes.

### 4. Report

Codex should report:

- what changed,
- what was validated,
- which warnings remain,
- where the PR or release lives.

## Good Trigger Phrases

Common requests that should activate this adapter:

- "ship this branch"
- "review and open a PR"
- "prepare this for release"
- "publish the current work"

## Practical Defaults

If the repo does not define its own publish path yet, a safe Codex fallback is:

1. run the smallest stable validation baseline,
2. review the diff,
3. fix blockers,
4. stage specific files,
5. commit with a clear message,
6. push,
7. open a PR,
8. stop before merge unless the user explicitly asks to merge.
