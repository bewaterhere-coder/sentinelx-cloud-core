from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

import sentinelx_core.verification_runtime as runtime
from sentinelx_core.mutation_audit import (
    MutationAuditBinding,
    MutationAuditJournal,
    MutationAuthorityEvidence,
    MutationProcessIntent,
    RequestedMutationIdentity,
)
from sentinelx_core.request_context import MutationLineage, RequestContext
from sentinelx_core.verification_profile import (
    NodeNpmVerificationProfile,
    VerificationRequest,
    build_toolchain_manifest,
    build_verification_admission,
    compute_dependency_payload_digest,
    compute_source_manifest_digest,
    load_dependency_capsule,
    load_source_snapshot,
)
from sentinelx_core.verification_runtime import (
    build_verification_runtime_plan,
    materialize_verification_runtime,
    revalidate_verification_before_spawn,
)

HEAD_SHA = "1" * 40


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _fixture(tmp_path: Path):
    profile = NodeNpmVerificationProfile(
        profile_id="node_npm",
        toolchain_root=tmp_path / "toolchain",
        source_snapshot_root=tmp_path / "sources",
        dependency_capsule_root=tmp_path / "capsules",
    )
    profile.toolchain_root.mkdir(parents=True)
    profile.resolve_node(require_exists=False).write_bytes(b"node-binary")
    npm_cli = profile.resolve_npm_cli(require_exists=False)
    npm_cli.parent.mkdir(parents=True)
    npm_cli.write_bytes(b"npm-cli")
    (profile.toolchain_root / "runtime.dat").write_bytes(b"runtime")

    source_store = profile.source_snapshot_path("source-a")
    payload = source_store / "payload"
    payload.mkdir(parents=True)
    package_json = b'{"name":"fixture"}\n'
    package_lock = b'{"lockfileVersion":3}\n'
    (payload / "package.json").write_bytes(package_json)
    (payload / "package-lock.json").write_bytes(package_lock)
    lock_sha = _sha(package_lock)
    source_manifest: dict[str, object] = {
        "schema_version": 1,
        "kind": "verification_source_snapshot",
        "source_id": "source-a",
        "repository": {
            "vcs": "git",
            "authority": "github.com",
            "path": "bewaterhere-coder/fixture",
        },
        "transport": {"type": "github-pr", "pr_number": 15, "head_sha": HEAD_SHA},
        "source_subpath": "mcp",
        "package_lock_sha256": lock_sha,
        "files": [
            {"path": "package.json", "size": len(package_json), "sha256": _sha(package_json)},
            {"path": "package-lock.json", "size": len(package_lock), "sha256": lock_sha},
        ],
    }
    source_manifest["source_manifest_digest"] = compute_source_manifest_digest(source_manifest)
    (source_store / "source-snapshot.json").write_text(
        json.dumps(source_manifest, sort_keys=True), encoding="utf-8"
    )

    capsule_store = profile.dependency_capsule_path("capsule-a")
    cache = capsule_store / "npm-cache"
    cache.mkdir(parents=True)
    package = b"offline-package-bytes"
    (cache / "fixture.tgz").write_bytes(package)
    capsule_files = [
        {
            "path": "npm-cache/fixture.tgz",
            "size": len(package),
            "sha256": _sha(package),
        }
    ]
    capsule_manifest = {
        "schema_version": 1,
        "kind": "node_npm_dependency_capsule",
        "capsule_id": "capsule-a",
        "package_lock_sha256": lock_sha,
        "files": capsule_files,
        "payload_digest": compute_dependency_payload_digest(capsule_files),
    }
    (capsule_store / "verification-capsule.json").write_text(
        json.dumps(capsule_manifest, sort_keys=True), encoding="utf-8"
    )

    source = load_source_snapshot(source_store, limits=profile.limits)
    capsule = load_dependency_capsule(capsule_store, limits=profile.limits)
    toolchain = build_toolchain_manifest(profile)
    request = VerificationRequest.from_mapping(
        {
            "profile": "node_npm",
            "source_id": "source-a",
            "source_manifest_sha256": source.source_manifest_digest,
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
    plan = build_verification_runtime_plan(profile, admission)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    return profile, admission, plan, workspace


def test_runtime_plan_seals_bounded_audit_intent_without_raw_paths(tmp_path: Path) -> None:
    profile, admission, plan, _workspace = _fixture(tmp_path)
    payload = plan.audit_intent.audit_dict()
    assert set(payload) == {
        "profile_id",
        "profile_revision",
        "source_repository_digest",
        "source_revision",
        "source_manifest_digest",
        "toolchain_kind",
        "toolchain_digest",
        "launcher_digest",
        "capsule_id",
        "capsule_revision",
        "capsule_payload_digest",
        "expected_package_lock_sha256",
        "network_mode",
        "resource_limits_digest",
    }
    assert payload["network_mode"] == "none"
    assert payload["toolchain_digest"] == admission.toolchain.toolchain_digest
    serialized = json.dumps(payload, sort_keys=True)
    assert str(profile.toolchain_root) not in serialized
    assert str(profile.source_snapshot_root) not in serialized
    assert str(profile.dependency_capsule_root) not in serialized


def test_materialization_copies_only_sealed_inputs_and_revalidates(tmp_path: Path) -> None:
    _profile, admission, plan, workspace = _fixture(tmp_path)
    materialized = materialize_verification_runtime(plan, workspace)
    assert (materialized.source_root / "package.json").read_bytes() == b'{"name":"fixture"}\n'
    assert (materialized.npm_cache_root / "fixture.tgz").read_bytes() == b"offline-package-bytes"
    assert {path.name for path in materialized.shim_root.iterdir()} == {"node.cmd", "npm.cmd"}
    revalidate_verification_before_spawn(materialized)
    assert _sha((materialized.source_root / "package-lock.json").read_bytes()) == admission.expected_package_lock_sha256


def test_toolchain_tamper_is_rejected_by_second_pre_spawn_check(tmp_path: Path) -> None:
    profile, _admission, plan, workspace = _fixture(tmp_path)
    materialized = materialize_verification_runtime(plan, workspace)
    (profile.toolchain_root / "runtime.dat").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="toolchain changed"):
        revalidate_verification_before_spawn(materialized)


def test_source_lock_tamper_is_rejected_before_spawn(tmp_path: Path) -> None:
    _profile, _admission, plan, workspace = _fixture(tmp_path)
    materialized = materialize_verification_runtime(plan, workspace)
    (materialized.source_root / "package-lock.json").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="payload digest mismatch|package-lock"):
        revalidate_verification_before_spawn(materialized)


def test_partial_copy_failure_cleans_reserved_workspace_material(tmp_path: Path, monkeypatch) -> None:
    _profile, _admission, plan, workspace = _fixture(tmp_path)
    original = runtime._copy_entries
    calls = 0

    def fail_second_copy(source_root, destination_root, entries):
        nonlocal calls
        calls += 1
        if calls == 2:
            destination_root.mkdir(parents=True, exist_ok=False)
            (destination_root / "partial.bin").write_bytes(b"partial")
            raise OSError("synthetic partial copy failure")
        return original(source_root, destination_root, entries)

    monkeypatch.setattr(runtime, "_copy_entries", fail_second_copy)
    with pytest.raises(OSError, match="partial copy"):
        materialize_verification_runtime(plan, workspace)
    assert not (workspace / "source").exists()
    assert not (workspace / ".sentinelx-verification").exists()


def test_mutation_audit_start_seals_verification_intent(tmp_path: Path) -> None:
    _profile, _admission, plan, _workspace = _fixture(tmp_path)
    audit = MutationAuditJournal(tmp_path / "audit")
    evidence = audit.evidence.retain(b"verification-script")
    context = RequestContext(
        request_id="req-verification",
        op="script_run",
        opaque_ref="verification",
        received_at=datetime.now(UTC),
    )
    lineage = MutationLineage.from_mapping(
        {
            "project_id": "sentinelx-cloud-core",
            "task_id": "PR-011",
            "run_id": "s02",
            "attempt_id": "1",
            "slice_id": "S02",
        }
    )
    binding = MutationAuditBinding.from_context(
        context,
        lineage,
        scope_id="scope-a",
        scope_generation=1,
        workspace_id="workspace-a",
        unique_lease_key="lease-a",
    )
    authority = MutationAuthorityEvidence(
        scope_digest="a" * 64,
        exact_workspace_digest="b" * 64,
        protected_inventory_digest="c" * 64,
        policy_digest="d" * 64,
        repository_identity_digest="e" * 64,
        semantic_identity_digest="f" * 64,
    )
    process_intent = MutationProcessIntent(
        interpreter="python3",
        argv=("python3", "script.py"),
        executable_final_path="C:/Python/python.exe",
        cwd_final_path="C:/workspace",
    )
    requested = RequestedMutationIdentity(
        host_platform="windows",
        host_user_sid="S-1-5-18",
        sandbox_kind="appcontainer",
        sandbox_profile="profile-a",
        sandbox_identity="S-1-15-2-1",
    )
    start = audit.begin(
        binding,
        evidence,
        authority=authority,
        process_intent=process_intent,
        requested_identity=requested,
        verification_intent=plan.audit_intent,
    )
    assert start.verification_intent == plan.audit_intent
    events = audit.read_events(start.operation_id)
    assert events[0]["verification_intent"] == plan.audit_intent.audit_dict()


def test_legacy_mutation_audit_start_shape_remains_unchanged(tmp_path: Path) -> None:
    audit = MutationAuditJournal(tmp_path / "audit")
    evidence = audit.evidence.retain(b"legacy-script")
    context = RequestContext(
        request_id="req-legacy",
        op="script_run",
        opaque_ref="legacy",
        received_at=datetime.now(UTC),
    )
    lineage = MutationLineage.from_mapping(
        {
            "project_id": "sentinelx-cloud-core",
            "task_id": "legacy",
            "run_id": "run",
            "attempt_id": "1",
            "slice_id": "S00",
        }
    )
    binding = MutationAuditBinding.from_context(
        context,
        lineage,
        scope_id="scope-legacy",
        scope_generation=1,
        workspace_id="workspace-legacy",
        unique_lease_key="lease-legacy",
    )
    authority = MutationAuthorityEvidence(
        scope_digest="a" * 64,
        exact_workspace_digest="b" * 64,
        protected_inventory_digest="c" * 64,
        policy_digest="d" * 64,
        repository_identity_digest="e" * 64,
        semantic_identity_digest="f" * 64,
    )
    process_intent = MutationProcessIntent(
        interpreter="python3",
        argv=("python3", "script.py"),
        executable_final_path="C:/Python/python.exe",
        cwd_final_path="C:/workspace",
    )
    requested = RequestedMutationIdentity(
        host_platform="windows",
        host_user_sid="S-1-5-18",
        sandbox_kind="appcontainer",
        sandbox_profile="profile-legacy",
        sandbox_identity="S-1-15-2-2",
    )
    start = audit.begin(
        binding,
        evidence,
        authority=authority,
        process_intent=process_intent,
        requested_identity=requested,
    )
    event = audit.read_events(start.operation_id)[0]
    assert "verification_intent" not in event
