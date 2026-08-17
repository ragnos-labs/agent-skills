#!/usr/bin/env python3
"""Install the exa-research client into an isolated user-scoped release."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import venv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import fcntl
except ImportError:  # pragma: no cover - the installer rejects non-POSIX systems
    fcntl = None  # type: ignore[assignment]

CLIENT_VERSION = "0.1.0"
SDK_VERSION = "2.18.1"
MINIMUM_PYTHON = (3, 11)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _absolute(value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise argparse.ArgumentTypeError("path must be absolute")
    return path


def _parser() -> argparse.ArgumentParser:
    data_home = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    parser = argparse.ArgumentParser(prog="install-exa-research")
    parser.add_argument(
        "--bin-dir", type=_absolute, default=Path.home() / ".local" / "bin"
    )
    parser.add_argument(
        "--data-dir",
        type=_absolute,
        default=data_home / "ragnos-agent-skills" / "exa-research",
    )
    parser.add_argument("--replace", action="store_true")
    return parser


def _atomic_text(path: Path, content: str, mode: int, *, replace: bool) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.chmod(mode)
        if replace:
            try:
                os.replace(temporary, path)
            except OSError as exc:
                raise SystemExit("atomic destination update failed") from exc
        else:
            try:
                os.link(temporary, path, follow_symlinks=False)
            except FileExistsError as exc:
                raise SystemExit("destination appeared during installation") from exc
            except OSError as exc:
                raise SystemExit("atomic destination update failed") from exc
    finally:
        temporary.unlink(missing_ok=True)


def _reject_symlink_components(path: Path) -> None:
    for component in (path, *path.parents):
        if component.is_symlink():
            raise SystemExit("symlinked install paths are rejected")


def _check_platform() -> None:
    if os.name != "posix" or fcntl is None:
        raise SystemExit("installer requires a POSIX system")
    if sys.version_info < MINIMUM_PYTHON:
        raise SystemExit("installer requires Python 3.11 or newer")


def _release_tree_is_safe(release_dir: Path) -> bool:
    """Reject symlinks except Python's Linux venv ``lib64 -> lib`` alias."""
    allowed_link = release_dir / "venv" / "lib64"
    allowed_target = release_dir / "venv" / "lib"
    try:
        for path in release_dir.rglob("*"):
            if not path.is_symlink():
                continue
            if path != allowed_link or os.readlink(path) != "lib":
                return False
            if path.resolve(strict=True) != allowed_target.resolve(strict=True):
                return False
    except OSError:
        return False
    return True


def _release_receipt(
    *,
    bootstrap_digest: str,
    lock_digest: str,
    release_id: str,
    source_digest: str,
) -> dict[str, Any]:
    return {
        "client": "exa-research",
        "client_version": CLIENT_VERSION,
        "bootstrap_lock_sha256": bootstrap_digest,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "kind": "exa.release",
        "lock_sha256": lock_digest,
        "release_id": release_id,
        "schema_version": "1.0",
        "sdk": "exa-py",
        "sdk_version": SDK_VERSION,
        "source_sha256": source_digest,
        "status": "ready",
    }


def _installation_receipt(
    release_receipt: dict[str, Any], *, command: Path
) -> dict[str, Any]:
    return {
        **release_receipt,
        "command_path": str(command),
        "installed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "kind": "exa.installation",
        "status": "installed",
    }


def _release_is_valid(
    release_dir: Path,
    *,
    bootstrap_digest: str,
    lock_digest: str,
    release_id: str,
    source_digest: str,
) -> bool:
    if release_dir.is_symlink() or not release_dir.is_dir():
        return False
    if not _release_tree_is_safe(release_dir):
        return False
    client = release_dir / "exa_cli.py"
    bootstrap = release_dir / "bootstrap.lock"
    lock = release_dir / "requirements.lock"
    python = release_dir / "venv" / "bin" / "python"
    receipt_path = release_dir / "release.json"
    required = (client, bootstrap, lock, python, receipt_path)
    if any(path.is_symlink() or not path.is_file() for path in required):
        return False
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return False
    return (
        _sha256(client) == source_digest
        and _sha256(bootstrap) == bootstrap_digest
        and _sha256(lock) == lock_digest
        and receipt.get("bootstrap_lock_sha256") == bootstrap_digest
        and receipt.get("lock_sha256") == lock_digest
        and receipt.get("release_id") == release_id
        and receipt.get("source_sha256") == source_digest
        and receipt.get("kind") == "exa.release"
        and receipt.get("status") == "ready"
    )


def _prepare_release(
    staging_dir: Path,
    *,
    bootstrap_source: Path,
    client_source: Path,
    lock_source: Path,
    receipt: dict[str, Any],
) -> None:
    installed_client = staging_dir / "exa_cli.py"
    installed_bootstrap = staging_dir / "bootstrap.lock"
    installed_lock = staging_dir / "requirements.lock"
    shutil.copyfile(client_source, installed_client, follow_symlinks=False)
    shutil.copyfile(bootstrap_source, installed_bootstrap, follow_symlinks=False)
    shutil.copyfile(lock_source, installed_lock, follow_symlinks=False)
    installed_client.chmod(0o700)
    installed_bootstrap.chmod(0o600)
    installed_lock.chmod(0o600)

    environment_dir = staging_dir / "venv"
    venv.EnvBuilder(with_pip=True, clear=False, symlinks=False).create(environment_dir)
    python = environment_dir / "bin" / "python"
    if python.is_symlink() or not python.is_file():
        raise SystemExit("isolated Python environment was not created safely")
    for requirement in (installed_bootstrap, installed_lock):
        completed = subprocess.run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--no-input",
                "--only-binary=:all:",
                "--require-hashes",
                "-r",
                str(requirement),
            ],
            check=False,
            text=True,
            capture_output=True,
        )
        if completed.returncode != 0:
            raise SystemExit("hash-locked dependency installation failed")
    _atomic_text(
        staging_dir / "release.json",
        json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n",
        0o600,
        replace=False,
    )


def _publish_release(staging_dir: Path, release_dir: Path) -> bool:
    try:
        staging_dir.rename(release_dir)
        return True
    except OSError as exc:
        if not release_dir.exists():
            raise SystemExit("atomic release publication failed") from exc
        return False


def main(argv: list[str] | None = None) -> int:
    _check_platform()
    args = _parser().parse_args(argv)
    source_dir = Path(__file__).resolve().parent
    client_source = source_dir / "exa_cli.py"
    bootstrap_source = source_dir / "bootstrap.lock"
    lock_source = source_dir / "requirements.lock"
    if (
        not client_source.is_file()
        or not bootstrap_source.is_file()
        or not lock_source.is_file()
    ):
        raise SystemExit("skill resources are incomplete")
    if any(
        path.is_symlink() for path in (client_source, bootstrap_source, lock_source)
    ):
        raise SystemExit("symlinked skill resources are rejected")
    source_digest = _sha256(client_source)
    bootstrap_digest = _sha256(bootstrap_source)
    lock_digest = _sha256(lock_source)
    release_id = f"{CLIENT_VERSION}-{source_digest[:12]}-{bootstrap_digest[:12]}-{lock_digest[:12]}"
    command = args.bin_dir / "exa"
    _reject_symlink_components(args.bin_dir)
    _reject_symlink_components(args.data_dir)
    if (command.exists() or command.is_symlink()) and not args.replace:
        raise SystemExit(
            "exa command already exists; inspect it and rerun with --replace"
        )

    args.data_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    args.data_dir.chmod(0o700)
    releases_dir = args.data_dir / "releases"
    releases_dir.mkdir(mode=0o700, exist_ok=True)
    _reject_symlink_components(releases_dir)
    releases_dir.chmod(0o700)
    release_dir = args.data_dir / "releases" / release_id
    _reject_symlink_components(release_dir)
    release_receipt = _release_receipt(
        bootstrap_digest=bootstrap_digest,
        lock_digest=lock_digest,
        release_id=release_id,
        source_digest=source_digest,
    )
    lock_flags = os.O_CREAT | os.O_RDWR
    if hasattr(os, "O_NOFOLLOW"):
        lock_flags |= os.O_NOFOLLOW
    lock_descriptor = os.open(args.data_dir / ".install.lock", lock_flags, 0o600)
    with os.fdopen(lock_descriptor, "w", encoding="utf-8") as install_lock:
        fcntl.flock(install_lock.fileno(), fcntl.LOCK_EX)
        if not _release_is_valid(
            release_dir,
            bootstrap_digest=bootstrap_digest,
            lock_digest=lock_digest,
            release_id=release_id,
            source_digest=source_digest,
        ):
            if release_dir.exists() or release_dir.is_symlink():
                raise SystemExit("existing release is incomplete or untrusted")
            staging_dir = Path(
                tempfile.mkdtemp(prefix=f".{release_id}.", dir=releases_dir)
            )
            staging_dir.chmod(0o700)
            try:
                _prepare_release(
                    staging_dir,
                    bootstrap_source=bootstrap_source,
                    client_source=client_source,
                    lock_source=lock_source,
                    receipt=release_receipt,
                )
                if not _release_tree_is_safe(staging_dir):
                    raise SystemExit("staged release contains symlinks")
                published_release = _publish_release(staging_dir, release_dir)
                if not _release_is_valid(
                    release_dir,
                    bootstrap_digest=bootstrap_digest,
                    lock_digest=lock_digest,
                    release_id=release_id,
                    source_digest=source_digest,
                ):
                    if (
                        published_release
                        and release_dir.is_dir()
                        and not release_dir.is_symlink()
                    ):
                        shutil.rmtree(release_dir)
                    raise SystemExit("published release failed verification")
            finally:
                if staging_dir.exists():
                    shutil.rmtree(staging_dir)

        args.bin_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        _reject_symlink_components(args.bin_dir)
        python = release_dir / "venv" / "bin" / "python"
        installed_client = release_dir / "exa_cli.py"
        launcher = (
            "#!/bin/sh\n"
            f'exec {shlex.quote(str(python))} {shlex.quote(str(installed_client))} "$@"\n'
        )
        _atomic_text(command, launcher, 0o700, replace=args.replace)

    installation_receipt = _installation_receipt(release_receipt, command=command)
    print(json.dumps(installation_receipt, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
