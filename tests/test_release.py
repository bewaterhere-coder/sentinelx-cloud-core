from __future__ import annotations

import importlib.util
from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("sentinelx_release", ROOT / "tools" / "release.py")
assert SPEC is not None and SPEC.loader is not None
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return proc.stdout.strip()


def release_repo(tmp_path: Path, version: str = "9.8.7") -> Path:
    repo = tmp_path / "repo"
    shutil.copytree(
        ROOT,
        repo,
        ignore=shutil.ignore_patterns(".git", ".pytest_cache", "__pycache__", "*.bak.*"),
    )
    _git(repo, "init")
    _git(repo, "config", "user.name", "release-test")
    _git(repo, "config", "user.email", "release-test@example.invalid")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "fixture")
    _git(repo, "tag", f"v{version}")
    return repo


def test_release_identity_binds_exact_tag_and_ref(tmp_path: Path) -> None:
    repo = release_repo(tmp_path)
    identity = release.resolve_release_identity(repo, "9.8.7", "HEAD")
    assert identity["tag"] == "v9.8.7"
    assert identity["source_commit"] == _git(repo, "rev-parse", "HEAD")


def test_release_identity_rejects_ref_after_tag(tmp_path: Path) -> None:
    repo = release_repo(tmp_path)
    (repo / "post-tag.txt").write_text("drift\n", encoding="utf-8")
    _git(repo, "add", "post-tag.txt")
    _git(repo, "commit", "-m", "post tag drift")
    with pytest.raises(release.ReleaseError, match="release ref/tag mismatch"):
        release.resolve_release_identity(repo, "9.8.7", "HEAD")


def test_release_identity_rejects_missing_requested_version_tag(tmp_path: Path) -> None:
    repo = release_repo(tmp_path)
    with pytest.raises(release.ReleaseError, match="release ref does not resolve"):
        release.resolve_release_identity(repo, "9.8.8", "HEAD")


def test_verify_rejects_tampered_artifact_before_install(tmp_path: Path, monkeypatch) -> None:
    wheel = tmp_path / "sentinelx_cloud_core-1.2.3-py3-none-any.whl"
    wheel.write_bytes(b"not-a-wheel")
    manifest = tmp_path / "release-manifest.json"
    manifest.write_text(
        '{"schema":"sentinelx.release.v1","version":"1.2.3","tag":"v1.2.3",'
        '"artifact":{"filename":"sentinelx_cloud_core-1.2.3-py3-none-any.whl",'
        '"size":11,"sha256":"wrong"}}',
        encoding="utf-8",
    )
    called = False

    def should_not_run(*_args, **_kwargs):
        nonlocal called
        called = True
        raise AssertionError("install verification must not run before digest check")

    monkeypatch.setattr(release, "_verify_wheel", should_not_run)
    with pytest.raises(release.ReleaseError, match="SHA-256 mismatch"):
        release.verify_manifest(manifest)
    assert called is False
