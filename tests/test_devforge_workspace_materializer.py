"""PR-014 S02 — trusted contained checkout materializer (D5)."""
from __future__ import annotations

import json
import zlib
from pathlib import Path

import pytest

from sentinelx_core import devforge_workspace_materializer as materializer


def _manifest(entries: list[dict], objects: list[str], **overrides) -> dict:
    manifest: dict = {
        "manifest_version": 1,
        "policy": "devforge-execution-workspace-source-v1",
        "capsule_id": "dsc_test",
        "repository": "https://github.com/bewaterhere-coder/sentinelx-cloud-core",
        "origin_url": "https://github.com/bewaterhere-coder/sentinelx-cloud-core",
        "expected_ref": "refs/heads/main",
        "logical_branch": "main",
        "expected_commit": "a" * 40,
        "object_format": "sha1",
        "entries": entries,
        "objects": objects,
        "file_count": len(entries),
        "total_bytes": sum(entry["size"] for entry in entries),
        "created_at": "2026-10-08T00:00:00Z",
    }
    manifest.update(overrides)
    body = {key: value for key, value in manifest.items() if key != "manifest_digest"}
    import hashlib

    manifest["manifest_digest"] = hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return manifest


def _capsule(tmp_path: Path, manifest: dict, blobs: dict[str, bytes]) -> Path:
    capsule = tmp_path / "capsule"
    capsule.mkdir(parents=True)
    (capsule / "manifest.json").write_text(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    for sha, payload in blobs.items():
        blob_dir = capsule / "objects" / sha[:2]
        blob_dir.mkdir(parents=True, exist_ok=True)
        header = f"blob {len(payload)}\0".encode("ascii")
        (blob_dir / sha[2:]).write_bytes(zlib.compress(header + payload))
    return capsule


def _blob_sha(payload: bytes) -> str:
    import hashlib

    header = f"blob {len(payload)}\0".encode("ascii")
    return hashlib.sha1(header + payload).hexdigest()


def test_materializer_writes_normal_git_metadata(tmp_path: Path) -> None:
    payload = b"hello workspace\n"
    sha = _blob_sha(payload)
    manifest = _manifest(
        [{"path": "docs/readme.md", "mode": "100644", "sha": sha, "size": len(payload)}],
        [sha],
    )
    capsule = _capsule(tmp_path, manifest, {sha: payload})
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    result = materializer.materialize_from_capsule(capsule, workspace)
    assert result["ok"] is True
    assert result["file_count"] == 1
    assert result["manifest_digest"] == manifest["manifest_digest"]

    assert (workspace / "docs" / "readme.md").read_bytes() == payload
    git_dir = workspace / ".git"
    assert (git_dir / "HEAD").read_text(encoding="ascii") == "ref: refs/heads/main\n"
    assert (git_dir / "refs" / "heads" / "main").read_text(encoding="ascii") == "a" * 40 + "\n"
    config = (git_dir / "config").read_text(encoding="utf-8")
    assert '[remote "origin"]' in config
    assert "https://github.com/bewaterhere-coder/sentinelx-cloud-core" in config
    loose = git_dir / "objects" / sha[:2] / sha[2:]
    header, _, content = zlib.decompress(loose.read_bytes()).partition(b"\x00")
    assert content == payload


def test_materializer_refuses_non_empty_workspace(tmp_path: Path) -> None:
    payload = b"x\n"
    sha = _blob_sha(payload)
    manifest = _manifest(
        [{"path": "f.txt", "mode": "100644", "sha": sha, "size": len(payload)}],
        [sha],
    )
    capsule = _capsule(tmp_path, manifest, {sha: payload})
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "pre-existing.txt").write_bytes(b"residue\n")

    with pytest.raises(materializer.MaterializerError):
        materializer.materialize_from_capsule(capsule, workspace)


def test_materializer_refuses_tampered_manifest(tmp_path: Path) -> None:
    payload = b"x\n"
    sha = _blob_sha(payload)
    manifest = _manifest(
        [{"path": "f.txt", "mode": "100644", "sha": sha, "size": len(payload)}],
        [sha],
    )
    capsule = _capsule(tmp_path, manifest, {sha: payload})
    body = json.loads((capsule / "manifest.json").read_text(encoding="utf-8"))
    body["total_bytes"] = 999
    (capsule / "manifest.json").write_text(
        json.dumps(body, sort_keys=True, separators=(",", ":")), encoding="utf-8"
    )

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    with pytest.raises(materializer.MaterializerError):
        materializer.materialize_from_capsule(capsule, workspace)


def test_materializer_refuses_unsafe_entry_paths(tmp_path: Path) -> None:
    payload = b"x\n"
    sha = _blob_sha(payload)
    for bad_path in ("../escape.txt", "/abs.txt", "C:/x.txt", "a/../../b.txt"):
        manifest = _manifest(
            [{"path": bad_path, "mode": "100644", "sha": sha, "size": len(payload)}],
            [sha],
        )
        capsule = _capsule(tmp_path / bad_path.replace("/", "_").replace(":", "_"), manifest, {sha: payload})
        workspace = tmp_path / "workspace"
        workspace.mkdir(exist_ok=True)
        with pytest.raises(materializer.MaterializerError):
            materializer.materialize_from_capsule(capsule, workspace)


def test_materializer_refuses_object_hash_mismatch(tmp_path: Path) -> None:
    payload = b"x\n"
    sha = _blob_sha(payload)
    manifest = _manifest(
        [{"path": "f.txt", "mode": "100644", "sha": sha, "size": len(payload)}],
        [sha],
    )
    capsule = _capsule(tmp_path, manifest, {sha: payload})
    (capsule / "objects" / sha[:2] / sha[2:]).write_bytes(
        zlib.compress(f"blob 3\0".encode("ascii") + b"y\n\n")
    )

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    with pytest.raises(materializer.MaterializerError):
        materializer.materialize_from_capsule(capsule, workspace)


def test_worker_source_is_self_contained_and_deterministic() -> None:
    first = materializer.build_materializer_worker()
    second = materializer.build_materializer_worker()
    assert first == second
    text = first.decode("utf-8")
    assert "import sentinelx_core" not in text
    assert "subprocess" not in text
    assert "socket" not in text
    compile(first, "worker.py", "exec")


def test_worker_result_parsing_is_fail_closed() -> None:
    assert materializer.parse_worker_result(b'{"ok": true, "file_count": 1}')["file_count"] == 1
    with pytest.raises(materializer.MaterializerError):
        materializer.parse_worker_result(b'{"ok": false, "error": "boom"}')
    with pytest.raises(materializer.MaterializerError):
        materializer.parse_worker_result(b"not json")
