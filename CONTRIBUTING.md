# Contributing

Thanks for contributing.

## Contribution Priorities

We are most likely to accept:

- fixes that make `ship` clearer or more portable,
- install and onboarding fixes,
- examples that make the skill easier to adopt,
- docs that remove private RAGnos assumptions.

We are less likely to accept:

- new skill families unrelated to `ship`,
- private stack assumptions presented as defaults,
- per-skill `README.md` or `CHANGELOG.md` files,
- features that only make sense inside RAGnos infrastructure.

## Repo Contract

Each public skill lives in `skills/<skill-name>/`.

Allowed contents:

- `SKILL.md`
- `scripts/`
- `references/`
- `assets/`

Do not add per-skill `README.md` or `CHANGELOG.md` files.

If you add or rename a published skill, update `catalog.json` in the same change.

## How To Propose Changes

1. Open an issue or Discussion first for larger changes.
2. Keep the change scoped to one skill or one repo-level concern.
3. Include install or usage examples when docs change.
4. Run the local checks before opening a PR.

## Local Checks

```bash
python3 scripts/validate_catalog.py
```

If you change JSON or workflow files, validate those as well before you open a PR.

## Style

- Use ASCII only.
- Keep skill docs concise and operational.
- Prefer extension hooks over repo-specific assumptions.
- Keep the public baseline useful without private services.

## Pull Requests

PRs should include:

- what changed,
- why it belongs here,
- whether it changes install or release behavior,
- any follow-up work that should become an issue instead of expanding the PR.

Use the PR template and link the issue or Discussion when applicable.
