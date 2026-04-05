# Contributing

Thanks for contributing.

## Adding a New Skill

Each skill lives in `skills/<skill-name>/SKILL.md`.

Minimum required structure:

```
skills/
  your-skill/
    SKILL.md
```

Required `SKILL.md` frontmatter:

```yaml
---
name: your-skill
description: One sentence describing when to use this skill.
---
```

Once the skill is in place, add an entry to `catalog.json`:

```json
{
  "name": "your-skill",
  "path": "skills/your-skill",
  "summary": "Short description.",
  "supported_agents": ["claude-code", "codex"],
  "status": "active",
  "featured": false
}
```

Optional directories inside a skill folder:

- `references/` — supporting docs, config examples, hook templates
- `scripts/` — helper scripts the skill may reference
- `assets/` — images or other static files

Do not add per-skill `README.md` or `CHANGELOG.md` files.

## Contribution Priorities

We are most likely to accept:

- new skills that solve a real developer workflow problem
- fixes that make an existing skill clearer or more portable
- install and onboarding improvements
- examples that make skills easier to adopt

We are less likely to accept:

- private stack assumptions presented as defaults
- per-skill `README.md` or `CHANGELOG.md` files
- features that only make sense inside RAGnos infrastructure

## How To Propose Changes

1. Open an issue or Discussion first for new skills or larger changes.
2. Keep the change scoped to one skill or one repo-level concern.
3. Include install or usage examples when public behavior changes.
4. Run local checks before opening a PR.

## Local Checks

```bash
python3 scripts/validate_catalog.py
```

## Style

- ASCII only.
- Keep skill docs concise and operational.
- Prefer extension hooks over repo-specific assumptions.
- Keep skills useful without private services.

## Pull Requests

PRs should include:

- what changed,
- why it belongs here,
- whether it changes install or release behavior,
- any follow-up work that should become a separate issue.

Use the PR template and link the issue or Discussion when applicable.
