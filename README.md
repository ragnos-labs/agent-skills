# Agent Skills

Reusable agent skills for Claude Code and Codex.

## Skills

### [ship](skills/ship/SKILL.md)

A release workflow that takes a branch from "done coding" to "reviewed, committed, pushed, and PR-ready."

What it does:

1. Classifies changed files and builds PR context
2. Runs lint, tests, and security checks (blocking, non-optional)
3. Reviews the diff and applies accepted fixes
4. Commits an explicit file list (never the whole worktree)
5. Pushes the branch and opens or updates the PR
6. Reports the result: commit hash, PR URL, remaining warnings

Works with Claude Code (`/ship`) and Codex.

## Install

```bash
npx skills add ragnos-labs/agent-skills --skill ship
```

Pin to a release:

```bash
npx skills add ragnos-labs/agent-skills@v0.1.0 --skill ship
```

## Adapting to your repo

The skill defines a phase model and extension hooks. Map the hooks to your own commands. Replace any RAGnos-specific wrappers (`just codex-ship`, `just agent-commit`, etc.) with your own.

The rules that should survive any fork:

- no merge without explicit user instruction
- no skipping security checks
- no whole-worktree staging

See [CONTRIBUTING.md](CONTRIBUTING.md) for the forking checklist.

## Contributing

- Questions and discussion: [GitHub Discussions](../../discussions)
- Bugs: [open an issue](../../issues)
- Security: [SECURITY.md](SECURITY.md)
