# Contributing

Thanks for contributing.

This repo currently focuses on the `ship` family.

Contributions should make the skill easier to use in real repos, not broaden it with extra positioning or repo-specific assumptions.

## Contribution Priorities

We are most likely to accept:

- fixes that make `ship-core` clearer or more portable,
- Codex and Claude adapter improvements,
- install and onboarding fixes,
- examples that make the public contract easier to adopt,
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
- `agents/openai.yaml`
- `scripts/`
- `references/`
- `assets/`

Do not add per-skill `README.md` or `CHANGELOG.md` files.

If you add or rename a published skill, update `catalog.json` in the same change.

## How To Propose Changes

1. Open an issue or Discussion first for larger changes.
2. Keep the change scoped to one skill family or one repo-level concern.
3. If behavior changes, explain whether the change belongs in `ship-core` or an adapter.
4. Include install or usage examples when docs change.
5. Run the local checks before opening a PR.

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
- Write for developers who may fork the skill and wire it into a different stack.
- Avoid marketing language. Prefer concrete instructions, prerequisites, and examples.

## Pull Requests

PRs should include:

- what changed,
- why it belongs here,
- whether it changes install or release behavior,
- any follow-up work that should become an issue instead of expanding the PR.

Use the PR template and link the issue or Discussion when applicable.
