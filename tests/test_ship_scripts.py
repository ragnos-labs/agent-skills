#!/usr/bin/env python3
"""Tests for the public ship runtime."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "skills" / "ship-core" / "scripts"


def run_script(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


class ShipRuntimeTests(unittest.TestCase):
    def test_ship_init_generates_python_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            (cwd / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
            result = run_script(str(SCRIPT_DIR / "ship_init.py"), "--write", "ship.yaml", cwd=cwd)
            self.assertEqual(result.returncode, 0, result.stderr)
            config = yaml.safe_load((cwd / "ship.yaml").read_text(encoding="utf-8"))
            self.assertEqual(config["base_branch"], "main")
            self.assertIn("python3 -m unittest", config["commands"]["preflight"])

    def test_ship_validate_config_passes_for_valid_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            config = {
                "version": 1,
                "base_branch": "main",
                "commands": {
                    "preflight": "python3 -m unittest",
                    "docs_sync": None,
                    "tests": "python3 -m unittest",
                    "gate": "python3 -m compileall .",
                    "publish_push": "git push -u origin HEAD",
                    "publish_pr": "gh pr create --fill",
                    "publish_release": None,
                },
                "review": {
                    "critical_paths": ["src/auth/**"],
                    "mechanical_paths": ["docs/**"],
                    "always_review_paths": [],
                },
                "policy": {
                    "require_pr": True,
                    "allow_no_review": True,
                    "use_cache": True,
                    "block_on_warnings": False,
                },
                "docs": {"paths": ["docs/**", "**/*.md"]},
                "scanners": {
                    "gitleaks": {"enabled": False, "required": False, "command": None},
                    "semgrep": {"enabled": False, "required": False, "command": None},
                    "actionlint": {"enabled": False, "required": False, "command": None},
                },
            }
            (cwd / "ship.yaml").write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
            result = run_script(
                str(SCRIPT_DIR / "ship_validate_config.py"),
                "--config",
                "ship.yaml",
                "--json",
                cwd=cwd,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["ok"])

    def test_ship_prepare_profiles_docs_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            subprocess.run(["git", "init", "-b", "main"], cwd=cwd, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=cwd, check=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=cwd, check=True)
            (cwd / "README.md").write_text("hello\n", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=cwd, check=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=cwd, check=True)
            (cwd / "docs").mkdir()
            (cwd / "docs" / "guide.md").write_text("changed\n", encoding="utf-8")
            config = {
                "version": 1,
                "base_branch": "main",
                "commands": {
                    "preflight": "echo preflight",
                    "docs_sync": None,
                    "tests": "echo tests",
                    "gate": "echo gate",
                    "publish_push": "git push -u origin HEAD",
                    "publish_pr": "gh pr create --fill",
                    "publish_release": None,
                },
                "review": {"critical_paths": [], "mechanical_paths": ["docs/**"], "always_review_paths": []},
                "policy": {"require_pr": True, "allow_no_review": True, "use_cache": True, "block_on_warnings": False},
                "docs": {"paths": ["docs/**", "**/*.md"]},
                "scanners": {"gitleaks": {"enabled": False, "required": False, "command": None}},
            }
            (cwd / "ship.yaml").write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
            result = run_script(str(SCRIPT_DIR / "ship_prepare.py"), "--config", "ship.yaml", cwd=cwd)
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["docs_changed"])
            self.assertIn("docs/guide.md", payload["bucketed_files"]["mechanical"])

    def test_ship_gate_warns_for_optional_missing_scanner(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            (cwd / "ship.yaml").write_text(
                yaml.safe_dump(
                    {
                        "version": 1,
                        "base_branch": "main",
                        "commands": {
                            "preflight": "python3 -c \"print('ok')\"",
                            "docs_sync": None,
                            "tests": None,
                            "gate": None,
                            "publish_push": "git push -u origin HEAD",
                            "publish_pr": "gh pr create --fill",
                            "publish_release": None,
                        },
                        "review": {"critical_paths": [], "mechanical_paths": [], "always_review_paths": []},
                        "policy": {"require_pr": True, "allow_no_review": True, "use_cache": True, "block_on_warnings": False},
                        "docs": {"paths": ["docs/**"]},
                        "scanners": {
                            "semgrep": {"enabled": True, "required": False, "command": "missing-semgrep --config auto ."}
                        },
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            result = run_script(
                str(SCRIPT_DIR / "ship_gate.py"),
                "--config",
                "ship.yaml",
                "--phase",
                "preflight",
                cwd=cwd,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["decision"], "WARN")

    def test_ship_findings_applies_suppressions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            findings_path = cwd / "findings.json"
            suppressions_path = cwd / "suppressions.yaml"
            findings_path.write_text(
                json.dumps(
                    [
                        {
                            "file": "scripts/build.sh",
                            "line": 12,
                            "severity": "WARN",
                            "issue": "shell injection warning",
                            "fix": "quote args",
                            "code": "bash -lc \"$USER_INPUT\"",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            suppressions_path.write_text(
                yaml.safe_dump(
                    {
                        "rules": [
                            {
                                "rule_id": "shell-example",
                                "pattern": "shell injection",
                                "scope": "scripts/**",
                                "severity_filter": ["WARN"],
                                "reason": "example false positive",
                                "expires_at": "2099-01-01",
                            }
                        ]
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            result = run_script(
                str(SCRIPT_DIR / "ship_findings.py"),
                "--input",
                str(findings_path),
                "--suppressions",
                str(suppressions_path),
                cwd=cwd,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["findings"], [])
            self.assertEqual(len(payload["suppressed"]), 1)


if __name__ == "__main__":
    unittest.main()
