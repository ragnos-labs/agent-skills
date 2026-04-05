# Findings Format

Use this shape when a helper script, scanner adapter, or agent emits `ship` findings.

```json
{
  "file": "src/auth/session.ts",
  "line": 42,
  "severity": "BLOCK",
  "issue": "Session token is logged",
  "fix": "Remove the log or redact the token",
  "source": "review",
  "code": "console.log(sessionToken)"
}
```

## Severity meanings

- `BLOCK`: must fix before publish
- `WARN`: real issue, but publish can proceed if explicitly reported
- `NOTE`: improvement or low-risk issue

## Rules

- `file`, `severity`, and `issue` are required.
- Use `source` to distinguish `review`, `semgrep`, `gitleaks`, `actionlint`, or other scanners.
- Keep `issue` short and factual.
- Keep `fix` actionable.
- `code` should be a real snippet when available.
