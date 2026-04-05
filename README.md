# RAGnos Labs Agent Skills

Installable skills for coding agents.

Current contents:

- `ship-core` defines the shared workflow contract.
- `ship-codex` adapts that contract for Codex.
- `ship-claude` adapts that contract for Claude Code.

If you want an agent to take a branch from "done coding" to "reviewed, validated, pushed, and PR-ready", start here.

## Install

Install from the repo:

```bash
npx skills add ragnos-labs/agent-skills --skill ship-core --skill ship-codex -a codex
npx skills add ragnos-labs/agent-skills --skill ship-core --skill ship-claude -a claude-code
```

Install from a direct skill path:

Codex:

```bash
npx skills add https://github.com/ragnos-labs/agent-skills/tree/main/skills/ship-core
npx skills add https://github.com/ragnos-labs/agent-skills/tree/main/skills/ship-codex
```

Claude Code:

```bash
npx skills add https://github.com/ragnos-labs/agent-skills/tree/main/skills/ship-core
npx skills add https://github.com/ragnos-labs/agent-skills/tree/main/skills/ship-claude
```

Use tags and releases for stable installs when possible:

Codex:

```bash
npx skills add https://github.com/ragnos-labs/agent-skills/tree/v0.0.1/skills/ship-core
npx skills add https://github.com/ragnos-labs/agent-skills/tree/v0.0.1/skills/ship-codex
```

Claude Code:

```bash
npx skills add https://github.com/ragnos-labs/agent-skills/tree/v0.0.1/skills/ship-core
npx skills add https://github.com/ragnos-labs/agent-skills/tree/v0.0.1/skills/ship-claude
```

## What `ship` Does

`ship` gives an agent a repeatable workflow for:

- inspecting the current branch,
- running preflight checks,
- reviewing the actual diff,
- fixing blockers before publish,
- staging only intended files,
- committing, pushing, and opening a PR when requested,
- reporting what ran and what is still risky.

The shared contract lives in `ship-core`. The agent-specific behavior lives in the Codex and Claude adapters.

The skill itself is still the markdown in each `SKILL.md`.

`ship-core/scripts/` contains optional helper resources that the skill can call when a repo wants a more deterministic config, prepare, gate, findings, commit, or publish step. They are support files for the skill, not a separate product.

## What You Need In Your Repo

`ship` is useful when the target repo already has:

- at least one working validation command,
- a clear publish path,
- git remote access already configured for the agent,
- repo-local docs or release rules that the agent can read.

It is not a replacement for your repo's own lint, test, release, or merge automation.

## Fast Start

### Codex

1. Install `ship-core` and `ship-codex`.
2. Open a repo that already has a working test or validation command.
3. Optionally generate a starter config with `python3 skills/ship-core/scripts/ship_init.py --write ship.yaml`.
4. Tell Codex to ship the current branch or prepare a PR.
5. Map the core extension hooks to your repo's actual lint, test, docs, and release commands.

### Claude Code

1. Install `ship-core` and `ship-claude`.
2. Open a repo with a defined validation and publishing path.
3. Optionally generate a starter config with `python3 skills/ship-core/scripts/ship_init.py --write ship.yaml`.
4. Ask Claude Code to ship the branch or prepare a reviewed PR.
5. Bind the adapter to your repo's own commands rather than copying ours.

## Hook Map

Before you rely on `ship`, make sure the agent can answer these hook questions for the target repo:

| Hook | Question |
|------|----------|
| `preflight` | What is the blocking validation baseline before review? |
| `docs_sync` | Which docs or examples need to stay in sync with the change? |
| `review` | What files or risk areas need semantic review? |
| `tests` | Which tests are required for confidence? |
| `gate` | What determines go, warn, or block after commit? |
| `publish` | How should the branch be pushed, proposed, tagged, or released? |

See [skills/ship-core/references/extension-hooks.md](skills/ship-core/references/extension-hooks.md) for the full mapping checklist.
See [skills/ship-core/references/config-file.md](skills/ship-core/references/config-file.md) for the public `ship.yaml` contract.

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
│   │   ├── scripts/
│   │   └── references/
│   ├── ship-codex/
│   │   ├── SKILL.md
│   │   └── agents/
│   └── ship-claude/
│       ├── SKILL.md
│       └── references/
└── .github/
```

## Current Limits

- Repo-specific automation is still your responsibility.
- No branch naming policy is enforced.
- No internal services are assumed.
- Quality depends on how clearly the target repo defines validation and publish commands.
- The adapters are intentionally thin. Most behavior lives in `ship-core`.
- The helper scripts are optional. The skill still works as a markdown workflow without them.

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

Use tagged installs instead of `main` when you want stable behavior.

The current baseline is `v0.0.1`. Keep treating it as an early contract while the workflow and docs are being tightened.
