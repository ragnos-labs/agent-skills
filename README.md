# RAGnos Labs Agent Skills

Public, GitHub-first agent skills from RAGnos Labs.

This repo launches the public `ship` family first:

- `ship-core` defines the shared workflow contract.
- `ship-codex` adapts that contract for Codex.
- `ship-claude` adapts that contract for Claude Code.

If you want a reusable "review, commit, push, release" workflow for coding agents without inheriting our private stack, start here.

## Install

Install from the repo:

```bash
npx skills add ragnos-labs/agent-skills --skill ship-core --skill ship-codex -a codex
npx skills add ragnos-labs/agent-skills --skill ship-core --skill ship-claude -a claude-code
```

Install from a direct skill path:

```bash
npx skills add https://github.com/ragnos-labs/agent-skills/tree/main/skills/ship-core
npx skills add https://github.com/ragnos-labs/agent-skills/tree/main/skills/ship-codex
npx skills add https://github.com/ragnos-labs/agent-skills/tree/main/skills/ship-core
npx skills add https://github.com/ragnos-labs/agent-skills/tree/main/skills/ship-claude
```

Use tags and releases for stable installs when possible:

```bash
npx skills add https://github.com/ragnos-labs/agent-skills/tree/v0.1.0/skills/ship-core
npx skills add https://github.com/ragnos-labs/agent-skills/tree/v0.1.0/skills/ship-codex
npx skills add https://github.com/ragnos-labs/agent-skills/tree/v0.1.0/skills/ship-core
npx skills add https://github.com/ragnos-labs/agent-skills/tree/v0.1.0/skills/ship-claude
```

## What This Repo Is For

The public goal is not "every skill we use internally."

The goal is a small, credible catalog of agent skills that:

- solve a real developer workflow problem,
- work across multiple agents,
- stay useful without RAGnos-private infrastructure,
- ship like open source software instead of like an internal memo.

For the first release, that means one flagship workflow only: `ship`.

## Fast Start

### Codex

1. Install `ship-core` and `ship-codex`.
2. Open a repo that already has a working test or validation command.
3. Tell Codex to ship the current branch or prepare a PR.
4. Map the core extension hooks to your repo's actual lint, test, docs, and release commands.

### Claude Code

1. Install `ship-core` and `ship-claude`.
2. Open a repo with a defined validation and publishing path.
3. Ask Claude Code to ship the branch or prepare a reviewed PR.
4. Bind the adapter to your repo's own commands rather than copying ours.

## Architecture

`ship-core` is the canonical workflow contract. It describes:

- phase order,
- flag semantics,
- rerun behavior,
- review and gate expectations,
- adapter hook points.

`ship-codex` and `ship-claude` are thin runtime adapters. They inherit the shared behavior from `ship-core`, then add agent-specific guidance for tool usage, review flow, and publish mechanics.

## Repo Layout

```text
.
├── catalog.json
├── skills/
│   ├── ship-core/
│   │   ├── SKILL.md
│   │   └── references/
│   ├── ship-codex/
│   │   ├── SKILL.md
│   │   └── agents/
│   └── ship-claude/
│       ├── SKILL.md
│       └── references/
└── .github/
```

## Maintainers

- Hunter Canning, creator and public distribution lead under the Mr. CLI voice
- RAGnos Labs, repo owner and release maintainer

## Contributing

Start with [CONTRIBUTING.md](CONTRIBUTING.md).

The short version:

- improve an existing skill first,
- keep cross-agent behavior in `ship-core`,
- keep runtime-specific behavior in the adapter skill,
- do not add per-skill `README.md` or `CHANGELOG.md` files,
- update `catalog.json` whenever you add or rename a published skill.

## Community

- Questions: use GitHub Discussions
- Bugs: open an issue
- Security issues: follow [SECURITY.md](SECURITY.md)
- Help or onboarding: see [SUPPORT.md](SUPPORT.md)

## Releases

Releases are the stable versioning surface for this repo.

Each release notes file includes:

- the exact install commands for Codex and Claude Code,
- the skills included in the release,
- any adapter contract changes that may require user action.

## Why GitHub First

For the first 90 days, this project is optimizing for:

- stars,
- watches,
- follows,
- installs,
- Discussions,
- outside issues and pull requests.

The canonical home is this GitHub repo. Any website or social page should point back here rather than competing with it.
