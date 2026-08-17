from __future__ import annotations

import importlib.util
import json
import stat
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest


def _installer_module() -> ModuleType:
    path = (
        Path(__file__).parents[1] / "skills" / "exa-research" / "scripts" / "install.py"
    )
    spec = importlib.util.spec_from_file_location("exa_research_installer", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeEnvironmentBuilder:
    def create(self, environment_dir: Path) -> None:
        python = environment_dir / "bin" / "python"
        python.parent.mkdir(parents=True)
        python.write_text("synthetic python", encoding="utf-8")
        python.chmod(0o700)


def _prepare_fakes(
    module: ModuleType, monkeypatch: Any, *, returncode: int = 0
) -> None:
    monkeypatch.setattr(
        module.venv,
        "EnvBuilder",
        lambda **_kwargs: FakeEnvironmentBuilder(),
    )
    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=returncode),
    )


def _arguments(tmp_path: Path) -> tuple[list[str], Path, Path]:
    bin_dir = tmp_path / "bin"
    data_dir = tmp_path / "data"
    return ["--bin-dir", str(bin_dir), "--data-dir", str(data_dir)], bin_dir, data_dir


def _release_id(module: ModuleType) -> str:
    source_dir = Path(module.__file__).resolve().parent
    source_digest = module._sha256(source_dir / "exa_cli.py")
    bootstrap_digest = module._sha256(source_dir / "bootstrap.lock")
    lock_digest = module._sha256(source_dir / "requirements.lock")
    return (
        f"{module.CLIENT_VERSION}-{source_digest[:12]}-"
        f"{bootstrap_digest[:12]}-{lock_digest[:12]}"
    )


def test_installer_publishes_verified_release_before_launcher(
    tmp_path: Path, monkeypatch: Any, capsys: Any
) -> None:
    module = _installer_module()
    _prepare_fakes(module, monkeypatch)
    arguments, bin_dir, data_dir = _arguments(tmp_path)

    assert module.main(arguments) == 0

    printed = json.loads(capsys.readouterr().out)
    release_dir = data_dir / "releases" / printed["release_id"]
    stored = json.loads((release_dir / "release.json").read_text(encoding="utf-8"))
    assert stored["kind"] == "exa.release"
    assert stored["status"] == "ready"
    assert printed["kind"] == "exa.installation"
    assert printed["status"] == "installed"
    assert printed["command_path"] == str(bin_dir / "exa")
    assert stored["release_id"] == printed["release_id"]
    assert module._release_is_valid(
        release_dir,
        bootstrap_digest=printed["bootstrap_lock_sha256"],
        lock_digest=printed["lock_sha256"],
        release_id=printed["release_id"],
        source_digest=printed["source_sha256"],
    )
    assert (bin_dir / "exa").read_text(encoding="utf-8").startswith("#!/bin/sh\nexec ")
    assert stat.S_IMODE((bin_dir / "exa").stat().st_mode) == 0o700
    assert stat.S_IMODE((release_dir / "release.json").stat().st_mode) == 0o600
    assert not list((data_dir / "releases").glob(".*"))


def test_existing_command_stops_before_release_mutation(
    tmp_path: Path, monkeypatch: Any
) -> None:
    module = _installer_module()
    _prepare_fakes(module, monkeypatch)
    arguments, bin_dir, data_dir = _arguments(tmp_path)
    bin_dir.mkdir()
    command = bin_dir / "exa"
    command.write_text("existing", encoding="utf-8")

    with pytest.raises(SystemExit, match="already exists"):
        module.main(arguments)

    assert command.read_text(encoding="utf-8") == "existing"
    assert not data_dir.exists()


def test_failed_dependency_install_leaves_no_partial_release(
    tmp_path: Path, monkeypatch: Any
) -> None:
    module = _installer_module()
    _prepare_fakes(module, monkeypatch, returncode=1)
    arguments, _, data_dir = _arguments(tmp_path)

    with pytest.raises(SystemExit, match="hash-locked"):
        module.main(arguments)

    assert list((data_dir / "releases").iterdir()) == []


def test_incomplete_release_is_never_rewritten(
    tmp_path: Path, monkeypatch: Any
) -> None:
    module = _installer_module()
    _prepare_fakes(module, monkeypatch)
    arguments, _, data_dir = _arguments(tmp_path)
    release_id = _release_id(module)
    release_dir = data_dir / "releases" / release_id
    release_dir.mkdir(parents=True)
    sentinel = release_dir / "partial"
    sentinel.write_text("preserve", encoding="utf-8")

    with pytest.raises(SystemExit, match="incomplete or untrusted"):
        module.main(arguments)

    assert sentinel.read_text(encoding="utf-8") == "preserve"


def test_symlinked_path_and_atomic_destination_race_fail_closed(
    tmp_path: Path, monkeypatch: Any
) -> None:
    module = _installer_module()
    _prepare_fakes(module, monkeypatch)
    target = tmp_path / "target"
    target.mkdir()
    symlinked_data = tmp_path / "data-link"
    symlinked_data.symlink_to(target, target_is_directory=True)
    bin_dir = tmp_path / "bin"

    with pytest.raises(SystemExit, match="symlinked"):
        module.main(["--bin-dir", str(bin_dir), "--data-dir", str(symlinked_data)])

    destination = tmp_path / "destination"
    destination.write_text("existing", encoding="utf-8")
    with pytest.raises(SystemExit, match="appeared"):
        module._atomic_text(destination, "replacement", 0o600, replace=False)
    assert destination.read_text(encoding="utf-8") == "existing"


def test_nested_releases_and_exact_release_symlinks_fail_closed(
    tmp_path: Path, monkeypatch: Any
) -> None:
    module = _installer_module()
    _prepare_fakes(module, monkeypatch)
    arguments, _, data_dir = _arguments(tmp_path)
    data_dir.mkdir()
    target = tmp_path / "releases-target"
    target.mkdir()
    (data_dir / "releases").symlink_to(target, target_is_directory=True)

    with pytest.raises(SystemExit, match="symlinked"):
        module.main(arguments)

    (data_dir / "releases").unlink()
    releases_dir = data_dir / "releases"
    releases_dir.mkdir()
    release_target = tmp_path / "release-target"
    release_target.mkdir()
    (releases_dir / _release_id(module)).symlink_to(
        release_target, target_is_directory=True
    )

    with pytest.raises(SystemExit, match="symlinked"):
        module.main(arguments)


def test_concurrent_release_winner_is_never_overwritten(tmp_path: Path) -> None:
    module = _installer_module()
    release_dir = tmp_path / "release"
    release_dir.mkdir()
    winner = release_dir / "winner"
    winner.write_text("preserve", encoding="utf-8")
    losing_staging = tmp_path / "staging"
    losing_staging.mkdir()
    (losing_staging / "loser").write_text("discard", encoding="utf-8")

    assert module._publish_release(losing_staging, release_dir) is False

    assert winner.read_text(encoding="utf-8") == "preserve"
    assert (losing_staging / "loser").read_text(encoding="utf-8") == "discard"


def test_nested_release_symlink_is_rejected(tmp_path: Path) -> None:
    module = _installer_module()
    release_dir = tmp_path / "release"
    release_dir.mkdir()
    client = release_dir / "exa_cli.py"
    bootstrap = release_dir / "bootstrap.lock"
    lock = release_dir / "requirements.lock"
    for path, content in (
        (client, "client"),
        (bootstrap, "bootstrap"),
        (lock, "lock"),
    ):
        path.write_text(content, encoding="utf-8")
    attacker_venv = tmp_path / "attacker-venv"
    python = attacker_venv / "bin" / "python"
    python.parent.mkdir(parents=True)
    python.write_text("attacker python", encoding="utf-8")
    (release_dir / "venv").symlink_to(attacker_venv, target_is_directory=True)
    source_digest = module._sha256(client)
    bootstrap_digest = module._sha256(bootstrap)
    lock_digest = module._sha256(lock)
    release_id = "synthetic-release"
    receipt = module._release_receipt(
        bootstrap_digest=bootstrap_digest,
        lock_digest=lock_digest,
        release_id=release_id,
        source_digest=source_digest,
    )
    (release_dir / "release.json").write_text(json.dumps(receipt), encoding="utf-8")

    assert not module._release_is_valid(
        release_dir,
        bootstrap_digest=bootstrap_digest,
        lock_digest=lock_digest,
        release_id=release_id,
        source_digest=source_digest,
    )

    (release_dir / "venv").unlink()
    (release_dir / "venv").mkdir()
    (release_dir / "venv" / "bin").symlink_to(
        attacker_venv / "bin", target_is_directory=True
    )
    assert not module._release_is_valid(
        release_dir,
        bootstrap_digest=bootstrap_digest,
        lock_digest=lock_digest,
        release_id=release_id,
        source_digest=source_digest,
    )


def test_linux_venv_lib64_alias_is_the_only_allowed_release_symlink(
    tmp_path: Path,
) -> None:
    module = _installer_module()
    release_dir = tmp_path / "release"
    library_dir = release_dir / "venv" / "lib"
    library_dir.mkdir(parents=True)
    alias = release_dir / "venv" / "lib64"
    alias.symlink_to("lib", target_is_directory=True)

    assert module._release_tree_is_safe(release_dir)

    alias.unlink()
    attacker_dir = tmp_path / "attacker"
    attacker_dir.mkdir()
    alias.symlink_to(attacker_dir, target_is_directory=True)

    assert not module._release_tree_is_safe(release_dir)


def test_post_publication_verification_failure_rolls_back_owned_release(
    tmp_path: Path, monkeypatch: Any
) -> None:
    module = _installer_module()
    _prepare_fakes(module, monkeypatch)
    arguments, _, data_dir = _arguments(tmp_path)
    monkeypatch.setattr(module, "_release_is_valid", lambda *_args, **_kwargs: False)

    with pytest.raises(SystemExit, match="published release failed"):
        module.main(arguments)

    assert list((data_dir / "releases").iterdir()) == []


def test_replace_failure_preserves_existing_command(
    tmp_path: Path, monkeypatch: Any
) -> None:
    module = _installer_module()
    destination = tmp_path / "exa"
    destination.write_text("existing command", encoding="utf-8")

    def fail_replace(_source: Path, _destination: Path) -> None:
        raise OSError("private local path")

    monkeypatch.setattr(module.os, "replace", fail_replace)
    with pytest.raises(SystemExit, match="atomic destination update failed"):
        module._atomic_text(destination, "replacement", 0o700, replace=True)

    assert destination.read_text(encoding="utf-8") == "existing command"
