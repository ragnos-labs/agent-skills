# Agent Skills

Reusable agent skills for Claude Code and Codex.

## Skills

### ship

A release workflow that takes a branch from "done coding" to "reviewed, committed, pushed, and PR-ready."

**What it does:**

1. Classifies changed files and builds PR context
2. Runs lint, tests, and security checks (blocking, non-optional)
3. Reviews the diff and applies accepted fixes
4. Commits an explicit file list (never the whole worktree)
5. Pushes the branch and opens or updates the PR
6. Reports the result: commit hash, PR URL, remaining warnings

**Three files make up the skill:**

| Skill | What it is |
|---|---|
| [`skills/ship-core`](skills/ship-core/SKILL.md) | The shared contract: phase order, flags, safety rules |
| [`skills/ship-codex`](skills/ship-codex/SKILL.md) | Runtime adapter for Codex |
| [`skills/ship-claude`](skills/ship-claude/SKILL.md) | Runtime adapter for Claude Code |

## Install

```bash
# Codex
npx skills add ragnos-labs/agent-skills --skill ship-core --skill ship-codex

# Claude Code
npx skills add ragnos-labs/agent-skills --skill ship-core --skill ship-claude
```

Pin to a release for stable installs:

```bash
npx skills add ragnos-labs/agent-skills@v0.1.0 --skill ship-core --skill ship-codex
npx skills add ragnos-labs/agent-skills@v0.1.0 --skill ship-core --skill ship-claude
```

## Adapting to your repo

`ship-core` defines the contract. The adapters are thin on top of it.

When you fork:

- replace `just codex-ship`, `just agent-commit`, and other RAGnos-specific commands with your own wrappers
- keep the phase order
- keep the safety rules: no merge without user instruction, no skipping security checks, no whole-worktree staging

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full checklist.

## Contributing

- Questions and discussion: [GitHub Discussions](../../discussions)
- Bugs: [open an issue](../../issues)
- Security: [SECURITY.md](SECURITY.md)
