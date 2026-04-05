# Public Skill Release Checklist

Use this checklist when publishing or updating a skill in this repo.

## Repo Surface

1. Confirm the README explains what the skill does in practical terms.
2. Confirm the README lists prerequisites and current limits.
3. Remove internal-only commands, links, and assumptions from any touched docs.
4. Keep install paths, release tags, and repo links current.

## Skill Packaging

1. Keep each public skill under `skills/<skill-name>/`.
2. Include only the files needed to install and use the skill.
3. Update `catalog.json` if a published skill is added, renamed, or removed.
4. Keep shared behavior in common skill layers such as `ship-core` and keep runtime-specific behavior in adapters.

## Community Surface

1. Ensure Issues and Discussions are enabled if they are part of the support path.
2. Keep issue templates aligned with the current public scope.
3. Point adopters to Discussions for workflow questions and improvement ideas.

## Release Notes

1. Publish exact install examples for each supported agent.
2. Note any contract changes that affect extension-hook mapping.
3. Call out backward-incompatible changes clearly.

## Validation

1. Run `python3 scripts/validate_catalog.py`.
2. Validate any changed workflow or JSON files.
3. Check rendered markdown for stale internal references before tagging a release.
