from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from sentinelx_core.policy import Policy
from sentinelx_core.verification_profile import (
    NodeNpmVerificationProfile,
    VerificationRequest,
    VerificationResourceLimits,
    build_toolchain_manifest,
    build_verification_admission,
    compute_dependency_payload_digest,
    compute_source_manifest_digest,
    load_dependency_capsule,
    load_source_snapshot,
)


HEAD_SHA = "1" * 40


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _profile_config(tmp_path: Path, **profile_overrides: object) -> dict[str, object]:
    profile: dict[str, object] = {
        "kind": "node_npm_v1",
        "toolchain_root": str(tmp_path / "toolchain"),
        "node_relative": "node.exe",
        "npm_cli_relative": "node_modules/npm/bin/npm-cli.js",
        "source_snapshot_root": str(tmp_path / "sources"),
        "dependency_capsule_root": str(tmp_path / "capsules"),
        "capsule_manifest_revision": 1,
    }
    profile.update(profile_overrides)
    return {
        "mutation_execution": {
            "workspace_root": str(tmp_path / "workspace"),
            "protected_roots": [str(tmp_path / "protected")],
            "verification_profiles": {"node_npm": profile},
        }
    }


def _direct_profile(tmp_path: Path) -> NodeNpmVerificationProfile:
    return NodeNpmVerificationProfile(
        profile_id="node_npm",
        toolchain_root=tmp_path / "toolchain",
        source_snapshot_root=tmp_path / "sources",
        dependency_capsule_root=tmp_path / "capsules",
    )


def _write_source_snapshot(root: Path) -> tuple[dict[str, object], str]:
    payload = root / "payload"
    payload.mkdir(parents=True)
    package_json = b'{"name":"fixture"}\n'
    package_lock = b'{"lockfileVersion":3}\n'
    (payload / "package.json").write_bytes(package_json)
    (payload / "package-lock.json").write_bytes(package_lock)
    lock_sha = _sha(package_lock)
    manifest: dict[str, object] = {
        "schema_version": 1,
        "kind": "verification_source_snapshot",
        "source_id": "pr015-mcp",
        "repository": {
            "vcs": "git",
            "authority": "github.com",
            "path": "bewaterhere-coder/ChatGPTControlShell",
        },
        "transport": {"type": "github-pr", "pr_number": 15, "head_sha": HEAD_SHA},
        "source_subpath": "mcp",
        "package_lock_sha256": lock_sha,
        "files": [
            {"path": "package.json", "size": len(package_json), "sha256": _sha(package_json)},
            {
                "path": "package-lock.json",
                "size": len(package_lock),
                "sha256": lock_sha,
            },
        ],
    }
    manifest["source_manifest_digest"] = compute_source_manifest_digest(manifest)
    (root / "source-snapshot.json").write_text(
        json.dumps(manifest, sort_keys=True), encoding="utf-8"
    )
    return manifest, lock_sha


def _write_capsule(root: Path, lock_sha: str) -> dict[str, object]:
    cache = root / "npm-cache"
    cache.mkdir(parents=True)
    package = b"offline-package-bytes"
    package_path = cache / "fixture.tgz"
    package_path.write_bytes(package)
    files = [
        {
            "path": "npm-cache/fixture.tgz",
            "size": len(package),
            "sha256": _sha(package),
        }
    ]
    manifest: dict[str, object] = {
        "schema_version": 1,
        "kind": "node_npm_dependency_capsule",
        "capsule_id": "capsule-a",
        "package_lock_sha256": lock_sha,
        "files": files,
        "payload_digest": compute_dependency_payload_digest(files),
    }
    (root / "verification-capsule.json").write_text(
        json.dumps(manifest, sort_keys=True), encoding="utf-8"
    )
    return manifest


def _write_toolchain(profile: NodeNpmVerificationProfile) -> None:
    profile.toolchain_root.mkdir(parents=True)
    profile.resolve_node(require_exists=False).write_bytes(b"node-binary")
    npm_cli = profile.resolve_npm_cli(require_exists=False)
    npm_cli.parent.mkdir(parents=True)
    npm_cli.write_bytes(b"npm-cli")
    (profile.toolchain_root / "runtime.dat").write_bytes(b"runtime")


def test_existing_host_without_verification_profiles_is_unchanged() -> None:
    policy = Policy.from_dict({"mutation_execution": {}})
    assert policy.mutation_execution.verification_profiles == ()
    assert policy.mutation_execution.verification_profile("node_npm") is None


def test_policy_parses_provider_owned_node_npm_profile(tmp_path: Path) -> None:
    policy = Policy.from_dict(_profile_config(tmp_path))
    profile = policy.mutation_execution.verification_profile("node_npm")
    assert profile is not None
    assert profile.kind == "node_npm_v1"
    assert profile.toolchain_root == (tmp_path / "toolchain").resolve(strict=False)
    assert profile.limits == VerificationResourceLimits()


def test_policy_rejects_profile_root_overlap_with_protected_authority(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="root overlaps"):
        Policy.from_dict(
            _profile_config(tmp_path, toolchain_root=str(tmp_path / "protected" / "node"))
        )


def test_policy_rejects_relative_member_traversal(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="traversal"):
        Policy.from_dict(_profile_config(tmp_path, node_relative="../node.exe"))


def test_policy_rejects_resource_limit_above_hard_ceiling(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="hard ceiling"):
        Policy.from_dict(
            _profile_config(
                tmp_path,
                limits={"source_max_total_bytes": 2_147_483_649},
            )
        )


def test_source_snapshot_is_bound_to_exact_revision_and_payload(tmp_path: Path) -> None:
    root = tmp_path / "source"
    manifest, _ = _write_source_snapshot(root)
    snapshot = load_source_snapshot(
        root,
        limits=VerificationResourceLimits(),
        expected_manifest_sha256=str(manifest["source_manifest_digest"]),
        expected_revision=HEAD_SHA,
    )
    assert snapshot.source_id == "pr015-mcp"
    assert snapshot.transport.revision == HEAD_SHA
    assert snapshot.repository.path == "bewaterhere-coder/ChatGPTControlShell"

    with pytest.raises(ValueError, match="revision"):
        load_source_snapshot(
            root,
            limits=VerificationResourceLimits(),
            expected_revision="2" * 40,
        )


def test_source_snapshot_tamper_and_unexpected_file_fail_closed(tmp_path: Path) -> None:
    root = tmp_path / "source"
    _write_source_snapshot(root)
    (root / "payload" / "package.json").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="digest mismatch|size mismatch"):
        load_source_snapshot(root, limits=VerificationResourceLimits())

    root = tmp_path / "source2"
    _write_source_snapshot(root)
    (root / "payload" / "extra.txt").write_text("unexpected", encoding="utf-8")
    with pytest.raises(ValueError, match="unexpected"):
        load_source_snapshot(root, limits=VerificationResourceLimits())


def test_dependency_capsule_is_lock_bound_and_tamper_evident(tmp_path: Path) -> None:
    root = tmp_path / "capsule"
    lock_sha = _sha(b"lock")
    manifest = _write_capsule(root, lock_sha)
    capsule = load_dependency_capsule(
        root,
        limits=VerificationResourceLimits(),
        expected_capsule_id="capsule-a",
    )
    assert capsule.package_lock_sha256 == lock_sha
    assert capsule.payload_digest == manifest["payload_digest"]

    (root / "npm-cache" / "fixture.tgz").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="digest mismatch|size mismatch"):
        load_dependency_capsule(root, limits=VerificationResourceLimits())


def test_dependency_capsule_rejects_unsupported_revision(tmp_path: Path) -> None:
    root = tmp_path / "capsule"
    manifest = _write_capsule(root, _sha(b"lock"))
    manifest["schema_version"] = 2
    (root / "verification-capsule.json").write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported"):
        load_dependency_capsule(root, limits=VerificationResourceLimits())


def test_toolchain_manifest_is_deterministic_and_complete(tmp_path: Path) -> None:
    profile = _direct_profile(tmp_path)
    _write_toolchain(profile)
    first = build_toolchain_manifest(profile)
    second = build_toolchain_manifest(profile)
    assert first.toolchain_digest == second.toolchain_digest
    assert {entry.path for entry in first.files} == {
        "node.exe",
        "node_modules/npm/bin/npm-cli.js",
        "runtime.dat",
    }

    (profile.toolchain_root / "runtime.dat").write_bytes(b"changed")
    assert build_toolchain_manifest(profile).toolchain_digest != first.toolchain_digest


def test_verification_request_rejects_authority_smuggling_fields() -> None:
    request = {
        "profile": "node_npm",
        "source_id": "source-a",
        "source_manifest_sha256": "a" * 64,
        "source_revision": HEAD_SHA,
        "capsule_id": "capsule-a",
        "package_lock_sha256": "b" * 64,
        "toolchain_root": "C:/caller-selected",
    }
    with pytest.raises(ValueError, match="bounded V1 fields"):
        VerificationRequest.from_mapping(request)


def test_verification_admission_binds_source_capsule_toolchain_and_lock(tmp_path: Path) -> None:
    profile = _direct_profile(tmp_path)
    _write_toolchain(profile)
    source_root = tmp_path / "source"
    source_manifest, lock_sha = _write_source_snapshot(source_root)
    capsule_root = tmp_path / "capsule"
    _write_capsule(capsule_root, lock_sha)

    source = load_source_snapshot(source_root, limits=profile.limits)
    capsule = load_dependency_capsule(capsule_root, limits=profile.limits)
    toolchain = build_toolchain_manifest(profile)
    request = VerificationRequest.from_mapping(
        {
            "profile": "node_npm",
            "source_id": "pr015-mcp",
            "source_manifest_sha256": source_manifest["source_manifest_digest"],
            "source_revision": HEAD_SHA,
            "capsule_id": "capsule-a",
            "package_lock_sha256": lock_sha,
        }
    )
    admission = build_verification_admission(
        profile=profile,
        request=request,
        source=source,
        capsule=capsule,
        toolchain=toolchain,
    )
    assert admission.network_mode == "none"
    assert admission.expected_package_lock_sha256 == lock_sha
    assert admission.toolchain.toolchain_digest == toolchain.toolchain_digest

    bad_request = VerificationRequest.from_mapping(
        {
            "profile": "node_npm",
            "source_id": "pr015-mcp",
            "source_manifest_sha256": source_manifest["source_manifest_digest"],
            "source_revision": HEAD_SHA,
            "capsule_id": "capsule-a",
            "package_lock_sha256": "f" * 64,
        }
    )
    with pytest.raises(ValueError, match="package-lock"):
        build_verification_admission(
            profile=profile,
            request=bad_request,
            source=source,
            capsule=capsule,
            toolchain=toolchain,
        )


def test_policy_rejects_unknown_profile_field(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unknown fields"):
        Policy.from_dict(_profile_config(tmp_path, executable_path="C:/caller/node.exe"))


def test_policy_rejects_profile_root_overlap_with_canonical_repository(tmp_path: Path) -> None:
    config = _profile_config(tmp_path, toolchain_root=str(tmp_path / "canonical" / "node"))
    mutation = config["mutation_execution"]
    assert isinstance(mutation, dict)
    mutation["canonical_repository_firewall_enabled"] = True
    mutation["canonical_repositories"] = [
        {
            "root": str(tmp_path / "canonical"),
            "repository": {
                "vcs": "git",
                "authority": "github.com",
                "path": "bewaterhere-coder/sentinelx-cloud-core",
            },
            "canonical_branch": "main",
        }
    ]
    with pytest.raises(ValueError, match="canonical authority"):
        Policy.from_dict(config)


def test_source_repository_identity_reuses_existing_canonical_semantics(tmp_path: Path) -> None:
    root = tmp_path / "source"
    manifest, _ = _write_source_snapshot(root)
    repository = manifest["repository"]
    assert isinstance(repository, dict)
    repository["authority"] = "https://token@GitHub.com:443"
    repository["path"] = "bewaterhere-coder/ChatGPTControlShell.git"
    manifest["source_manifest_digest"] = compute_source_manifest_digest(manifest)
    (root / "source-snapshot.json").write_text(json.dumps(manifest), encoding="utf-8")
    snapshot = load_source_snapshot(root, limits=VerificationResourceLimits())
    assert snapshot.repository.authority == "github.com:443"
    assert snapshot.repository.path == "bewaterhere-coder/ChatGPTControlShell"
    assert "token" not in snapshot.repository.canonical_payload()["authority"]


def test_source_manifest_rejects_traversal_file_path(tmp_path: Path) -> None:
    root = tmp_path / "source"
    manifest, _ = _write_source_snapshot(root)
    files = manifest["files"]
    assert isinstance(files, list)
    first = files[0]
    assert isinstance(first, dict)
    first["path"] = "../package.json"
    with pytest.raises(ValueError, match="traversal"):
        compute_source_manifest_digest(manifest)


def test_source_manifest_enforces_configured_file_count_and_byte_bounds(tmp_path: Path) -> None:
    root = tmp_path / "source"
    manifest, _ = _write_source_snapshot(root)
    with pytest.raises(ValueError, match="file-count"):
        compute_source_manifest_digest(
            manifest,
            limits=VerificationResourceLimits(source_max_files=1),
        )
    with pytest.raises(ValueError, match="total-byte"):
        compute_source_manifest_digest(
            manifest,
            limits=VerificationResourceLimits(source_max_total_bytes=1),
        )
