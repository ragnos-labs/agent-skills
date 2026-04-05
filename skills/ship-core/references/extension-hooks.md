# Ship Core Extension Hooks

Map `ship-core` onto a real repo by naming the commands and decisions that your agent should use.

## Minimum Hook Map

| Hook | Questions to answer |
|------|---------------------|
| `preflight` | What is the blocking validation baseline before review? |
| `docs_sync` | Which docs or examples must stay in sync with code changes? |
| `review` | What files or risk areas need semantic review? |
| `tests` | Which tests are required for confidence on this repo? |
| `gate` | What determines go, warn, or block after commit? |
| `publish` | How should the branch be pushed, proposed, tagged, and released? |

## Portable Default

If a repo has no custom policy yet, a practical baseline is:

1. `preflight`
   - format or lint if defined
   - run unit tests or the smallest stable test target
   - validate docs or examples if changed
2. `review`
   - review the diff for bugs, regressions, and unsafe shell or file operations
3. `tests`
   - re-run only what is needed to prove the fix
4. `gate`
   - confirm validation passed and no blocker findings remain
5. `publish`
   - push the branch
   - open a PR
   - create a tag or release only if the repo uses releases as a user-facing distribution surface

## Generic Example Commands

These are examples, not defaults:

```bash
# preflight
npm test
pytest -q
make lint

# docs sync
npm run docs:check

# publish
git push -u origin HEAD
gh pr create --fill
gh release create v0.0.1 --notes-file release-notes/v0.0.1.md
```

## What Not To Bake In

Avoid hard-coding:

- company-internal CLIs,
- internal ticket IDs,
- non-public dashboards,
- repo-specific branch naming rules that do not generalize,
- private release or approval systems.

Public skills stay useful by describing the contract and leaving the implementation hooks replaceable.
