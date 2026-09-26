# Agent Skills

A growing catalog of open-source skills for Claude Code and Codex. Each skill encodes a real developer workflow so your agent can run it reliably — without you writing the logic from scratch every time.

## Skills

### [ship](skills/ship/SKILL.md)

Takes a branch from "done coding" to "reviewed, committed, pushed, and PR-ready."

What it does:

1. Classifies changed files and builds PR context
2. Runs lint, tests, and security checks (blocking, non-optional)
3. Reviews the diff and applies accepted fixes
4. Commits an explicit file list (never the whole worktree)
5. Pushes the branch and opens or updates the PR
6. Reports the result: commit hash, PR URL, remaining warnings

Works with Claude Code (`/ship`) and Codex.

### [exa-research](skills/exa-research/SKILL.md)

Provides a credential-safe, deterministic JSON search client built on Exa's
official Python SDK. The bundled installer uses an isolated, hash-locked
environment and never accepts the API key as a command argument. Installation
supports macOS and Linux with Python 3.11 or newer.

The `exa api` command exposes complete research request fields and responses:
search, contents, answer, similar pages, agents/research, batches, monitors, and
Websets. It uses a fixed HTTPS origin, rejects redirects, and accepts the key
only from `EXA_API_KEY`. Existing `exa search` behavior is unchanged.

```bash
exa api /search --data '{"query":"Blender interactive websites","startPublishedDate":"2026-09-01T00:00:00Z","includeDomains":["youtube.com"],"numResults":5,"contents":{"text":true}}'
exa api /contents --data '{"ids":["https://www.blender.org/"],"text":true}'
exa api /agent/runs --method GET --params '{"limit":1}'
exa api /answer --stream --data '{"query":"What is glTF?","stream":true}'
```

Use `--data @request.json` or `--data -` for a file or stdin. `--params` accepts
JSON query parameters. Methods: GET, POST (default), PATCH, PUT, DELETE.
`--timeout` is 1-3600 seconds (default 300). JSON output preserves provider fields;
`--stream` passes through server-sent events. Provider errors expose HTTP status,
never response bodies or credentials. Requests are not automatically retried,
so job creation cannot be duplicated by this client.

Use the [current API reference](https://exa.ai/docs/reference/search) for payloads
and account availability. Installing the interface does not authorize recurring
monitors, webhook delivery, destructive operations, or larger paid jobs. Team/key
administration is outside this research command's scope. Websets and other
features remain subject to the account's permissions and plan.

With an existing Infisical attended launcher, prefix commands with
`ragnos-infisical --`, for example `ragnos-infisical -- exa api /search --data
@request.json`. Do not put API keys in files or command arguments.

Firecrawl's official CLI already exposes search, scrape, map, crawl, agent,
interact, parse, developer/research indexes, and monitors. Reuse it through
`ragnos-infisical -- firecrawl <command>` and consult each command's `--help`.
No second Firecrawl client is needed. Live smoke checks should use credit-usage
and one bounded scrape; do not create recurring work just to test availability.

## Install

```bash
npx skills add ragnos-labs/agent-skills --skill ship
npx skills add ragnos-labs/agent-skills --skill exa-research
```

Pin to a release:

```bash
npx skills add ragnos-labs/agent-skills@v0.1.2 --skill ship
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

---

Built by [RAGnos Labs](https://ragnos.io) · [X](https://x.com/mrcommandline) · [Substack](https://substack.com/@mrcommandline)
