# Ship Claude Runtime Notes

`ship-claude` stays intentionally thin.

The adapter exists to make three points explicit:

1. `ship-core` is the shared behavior contract.
2. Claude Code should use repo-local commands for validation and publish.
3. Parallel review and docs work are optional optimizations, not hidden requirements.

If you need heavier automation, build it as repo-local commands or scripts and keep this skill focused on when and how to use them.
