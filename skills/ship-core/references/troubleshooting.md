# Troubleshooting

## `ship.yaml` is missing

- Create one with `python3 skills/ship-core/scripts/ship_init.py --write ship.yaml`
- Or skip the helper scripts and map hooks directly from repo docs

## Command binary not found

- Check the first token in the configured command
- Install the missing tool or change the command
- Optional scanners should warn; required scanners should block

## The skill keeps reviewing too much

- Mark docs and low-risk paths in `review.mechanical_paths`
- Mark auth, deploy, and security-sensitive paths in `review.critical_paths`
- Use `--review-only` or `--no-review` only when the host repo policy allows it

## Too many false positives

- Normalize findings with `scripts/ship_findings.py`
- Add repo-local suppression rules in `.ship/fp-suppressions.yaml`
- Use expiry dates on suppressions whenever possible
