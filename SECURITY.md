# Security Policy

## Supported Versions

The latest tagged release is the supported public baseline.

If you are reporting a security issue, include:

- the release tag or commit you tested,
- which skill is affected,
- the repo or environment assumptions required to reproduce the issue,
- clear reproduction steps,
- the impact if the issue is real.

## Reporting A Vulnerability

Please do not open a public issue for a suspected security vulnerability.

Use a private GitHub security advisory for this repository when possible. If a private advisory path is not available yet, contact the maintainers directly through the repo owner and request a private follow-up channel.

We will acknowledge legitimate reports, validate impact, and coordinate a fix and disclosure path.

## Security Scope

This repo ships instructions, adapters, and small helper assets. Many real risks come from:

- unsafe repo-specific hook commands,
- over-broad publish permissions,
- secrets embedded in release automation,
- shell commands copied into local workflows without review.

If you adapt `ship-core`, treat your local preflight, gate, and publish commands as part of your attack surface.
