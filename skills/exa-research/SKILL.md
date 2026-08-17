---
name: exa-research
description: Search the web with Exa through a credential-safe, deterministic JSON CLI built on Exa's official Python SDK. Use when an agent needs Exa web research, source discovery, domain-filtered searches, or a local Exa CLI that receives EXA_API_KEY from a broker or environment without placing the key on the command line.
---

# Exa Research

Use the bundled `exa` client for bounded source discovery. It fixes the API
origin, emits JSON only, and never accepts a credential as a command argument.

## Install

Run the installer from this skill directory:

```text
python3 scripts/install.py --bin-dir <user-bin-directory>
```

The installer creates an isolated virtual environment, installs the exact
hash-locked official `exa-py` dependency set, copies the client into an
immutable release directory, and writes an `exa` launcher. It supports macOS
and Linux with Python 3.11 or newer. Windows is not currently supported because
the launcher and installation lock use POSIX primitives. Release construction
is serialized and staged privately before one atomic publication step. Use
`--replace` only after identifying the existing command that will be replaced.

## Check readiness

Run `exa doctor`. Treat `credential: available` as presence evidence only.
Doctor does not call Exa and never prints the value. Provide `EXA_API_KEY`
through the approved secret broker or process environment; never put it in
shell history, Git, prompts, logs, or command arguments.

## Search

Run a bounded search:

```text
exa search "query" --num-results 5
```

Optional controls include `--type`, repeated `--include-domain`, repeated
`--exclude-domain`, and `--max-highlight-characters`. Prefer the default
highlight-only contents over full page text. Increase result or highlight
limits only when the task requires it because provider cost and output size
grow with them.

Read the JSON result, use the returned URLs as citations, and distinguish the
provider's current response from your own inference. A successful process is
not proof that every returned source is accurate or authoritative.

## Failure rules

- Stop on `credential_unavailable`; do not ask to print or inspect the key.
- Stop on `provider_unavailable` or `provider_contract_invalid`; preserve the
  error code without relaying raw provider bodies that may contain private
  data.
- Do not add a plain-text or raw-response mode. Extend the normalized JSON
  contract deliberately if another field is required.
- Keep the API origin fixed at `https://api.exa.ai` so a credential cannot be
  redirected to an arbitrary host.

The client implementation is `scripts/exa_cli.py`. `scripts/bootstrap.lock`
upgrades the isolated installer before `scripts/requirements.lock` installs
the official SDK closure. Both are generated with hashes from their adjacent
input files.
