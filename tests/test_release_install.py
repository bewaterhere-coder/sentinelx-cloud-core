from __future__ import annotations

import hashlib
import json
from pathlib import Path

from tests.test_release import release, release_repo


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def test_build_release_verifies_wheel_install_and_manifest(tmp_path: Path) -> None:
    repo = release_repo(tmp_path / "fixture")
    output = tmp_path / "release-output"

    manifest_path = release.build_release(repo, "9.8.7", output, "v9.8.7")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    wheel = output / manifest["artifact"]["filename"]

    assert manifest["schema"] == "sentinelx.release.v1"
    assert manifest["state"] == "built"
    assert manifest["version"] == "9.8.7"
    assert manifest["tag"] == "v9.8.7"
    assert manifest["source_commit"] == release._commit_for(repo, "v9.8.7")
    assert manifest["artifact"]["sha256"] == _sha256(wheel)
    assert manifest["artifact"]["size"] == wheel.stat().st_size
    assert manifest["verification"] == {
        "installed_agent_version": "9.8.7",
        "passed": True,
        "wheel_metadata_version": "9.8.7",
    }

    verification = release.verify_manifest(manifest_path, repo)
    assert verification["ok"] is True
    assert verification["version"] == "9.8.7"
    assert verification["wheel_metadata_version"] == "9.8.7"
    assert verification["installed_agent_version"] == "9.8.7"


def test_pyproject_has_no_static_release_version_authority() -> None:
    pyproject = (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(encoding="utf-8")
    assert 'dynamic = ["version"]' in pyproject
    assert '[tool.hatch.version]' in pyproject
    assert 'source = "vcs"' in pyproject
