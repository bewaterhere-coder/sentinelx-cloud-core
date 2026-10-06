from __future__ import annotations

import asyncio
import hashlib
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

import sentinelx_core.handlers.basic as basic
import sentinelx_core.verification_readiness as readiness_module
from sentinelx_core.executor import HandlerError
from sentinelx_core.handlers.basic import make_capabilities_handler
from sentinelx_core.handlers.scoped_script import make_profiled_script_run_handler
from sentinelx_core.mutation_audit import MutationAuditJournal
from sentinelx_core.mutation_placement import RepositoryIdentity, SemanticIdentity
from sentinelx_core.mutation_readiness import MutationRuntimeReadiness
from sentinelx_core.mutation_scope import SCOPED_SCRIPT_OPERATION_CLASS, MutationScopeStore
from sentinelx_core.policy import MutationExecutionPolicy, Policy
from sentinelx_core.request_context import RequestContext
from sentinelx_core.verification_profile import (
    NodeNpmVerificationProfile,
    build_toolchain_manifest,
    compute_dependency_payload_digest,
    compute_source_manifest_digest,
)
from sentinelx_core.verification_readiness import (
    VerificationRuntimeReadiness,
    cached_node_npm_toolchain_digest,
    probe_node_npm_verification_runtime,
)

HEAD_SHA = "4" * 40  # Synthetic immutable source revision for the fixture.


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _base_ready() -> MutationRuntimeReadiness:
    return MutationRuntimeReadiness(True, "base ready", {"windows": True})


def _real_profile(tmp_path: Path) -> tuple[NodeNpmVerificationProfile, MutationExecutionPolicy]:
    node_executable = shutil.which("node")
    if node_executable is None:
        pytest.skip("Node is not installed on this Windows runner")
    source_node_root = Path(node_executable).resolve().parent
    npm_source = source_node_root / "node_modules" / "npm"
    if not (npm_source / "bin" / "npm-cli.js").is_file():
        pytest.skip("Node toolchain does not contain npm-cli.js")

    # Physical tests materialize a complete provider-owned toolchain copy
    # beneath the admitted D:\\coco workspace. This keeps Host proof inside the
    # operator boundary while preserving the real Node/npm loader tree.
    toolchain_root = tmp_path / "provider-node-toolchain"
    shutil.copytree(source_node_root, toolchain_root)
    sources = tmp_path / "provider-sources"
    capsules = tmp_path / "provider-capsules"
    workspace = tmp_path / "workspaces"
    protected = tmp_path / "protected"
    for root in (sources, capsules, workspace, protected):
        root.mkdir(parents=True)

    profile = NodeNpmVerificationProfile(
        profile_id="node_npm",
        toolchain_root=toolchain_root,
        source_snapshot_root=sources,
        dependency_capsule_root=capsules,
    )
    runtime_roots = {Path(sys.prefix).resolve(), Path(sys.base_prefix).resolve()}
    policy = MutationExecutionPolicy(
        configured=True,
        scoped_mutation_enabled=True,
        workspace_root=workspace,
        protected_roots=(protected,),
        runtime_read_roots=tuple(sorted(runtime_roots, key=lambda item: str(item).casefold())),
        scope_ttl_seconds=600,
        evidence_retention_days=7,
        verification_profiles=(profile,),
    )
    return profile, policy


def _provider_inputs(profile: NodeNpmVerificationProfile) -> dict[str, str]:
    source_store = profile.source_snapshot_path("readiness-tamper-source")
    payload = source_store / "payload"
    payload.mkdir(parents=True)
    package = {"name": "sentinelx-readiness-tamper", "version": "1.0.0", "private": True}
    lock = {
        "name": package["name"],
        "version": package["version"],
        "lockfileVersion": 3,
        "requires": True,
        "packages": {"": {"name": package["name"], "version": package["version"]}},
    }
    package_bytes = (json.dumps(package, sort_keys=True) + "\n").encode()
    lock_bytes = (json.dumps(lock, sort_keys=True) + "\n").encode()
    (payload / "package.json").write_bytes(package_bytes)
    (payload / "package-lock.json").write_bytes(lock_bytes)
    lock_sha = _sha(lock_bytes)
    source_manifest: dict[str, object] = {
        "schema_version": 1,
        "kind": "verification_source_snapshot",
        "source_id": "readiness-tamper-source",
        "repository": {
            "vcs": "git",
            "authority": "github.com",
            "path": "bewaterhere-coder/sentinelx-cloud-core",
        },
        "transport": {"type": "github-pr", "pr_number": 11, "head_sha": HEAD_SHA},
        "source_subpath": "tests/readiness",
        "package_lock_sha256": lock_sha,
        "files": [
            {"path": "package.json", "size": len(package_bytes), "sha256": _sha(package_bytes)},
            {"path": "package-lock.json", "size": len(lock_bytes), "sha256": lock_sha},
        ],
    }
    source_manifest["source_manifest_digest"] = compute_source_manifest_digest(source_manifest)
    (source_store / "source-snapshot.json").write_text(
        json.dumps(source_manifest, sort_keys=True), encoding="utf-8"
    )
    capsule_store = profile.dependency_capsule_path("readiness-tamper-capsule")
    (capsule_store / "npm-cache").mkdir(parents=True)
    capsule_files: list[dict[str, object]] = []
    (capsule_store / "verification-capsule.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "kind": "node_npm_dependency_capsule",
                "capsule_id": "readiness-tamper-capsule",
                "package_lock_sha256": lock_sha,
                "files": capsule_files,
                "payload_digest": compute_dependency_payload_digest(capsule_files),
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return {
        "profile": "node_npm",
        "source_id": "readiness-tamper-source",
        "source_manifest_sha256": str(source_manifest["source_manifest_digest"]),
        "source_revision": HEAD_SHA,
        "capsule_id": "readiness-tamper-capsule",
        "package_lock_sha256": lock_sha,
    }


def test_verification_readiness_fails_closed_off_windows(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(readiness_module.sys, "platform", "linux")
    result = probe_node_npm_verification_runtime(
        MutationExecutionPolicy(), tmp_path / "state", base_readiness=_base_ready(), force=True
    )
    assert result.available is False
    assert result.checks["windows"] is False
    assert "Windows AppContainer" in result.reason


def test_missing_profile_is_independent_from_base_readiness(tmp_path: Path, monkeypatch) -> None:
    base = _base_ready()
    verification = VerificationRuntimeReadiness(
        False, "Node/npm verification profile is not configured", {"profile_configured": False}
    )
    monkeypatch.setattr(basic, "probe_mutation_runtime", lambda *_a, **_k: base)
    monkeypatch.setattr(
        basic, "probe_node_npm_verification_runtime", lambda *_a, **_k: verification
    )
    policy = Policy(
        mutation_execution=MutationExecutionPolicy(
            configured=True,
            scoped_mutation_enabled=True,
            workspace_root=tmp_path / "workspace",
        ),
        upload_base=tmp_path / "uploads",
    )
    handler = make_capabilities_handler(
        policy,
        config_path=tmp_path / "config.yaml",
        upload_base=tmp_path / "uploads",
        ops_supported=lambda: ("capabilities", "script_run"),
    )
    features = asyncio.run(handler({"detail": "full"}))["execution_features"]
    assert features["host_mutation_sandbox_v1"]["available"] is True
    assert features["host_runtime.scoped_verification_node_npm_v1"]["available"] is False


def test_verification_feature_never_projects_provider_paths(tmp_path: Path, monkeypatch) -> None:
    base = _base_ready()
    verification = VerificationRuntimeReadiness(
        True,
        "physical self-check passed",
        {"appcontainer_node": True, "appcontainer_npm": True},
        profile_id="node_npm",
        toolchain_kind="node_npm_v1",
        toolchain_digest="a" * 64,
    )
    monkeypatch.setattr(basic, "probe_mutation_runtime", lambda *_a, **_k: base)
    monkeypatch.setattr(
        basic, "probe_node_npm_verification_runtime", lambda *_a, **_k: verification
    )
    secret_root = tmp_path / "private-toolchain"
    policy = Policy(
        mutation_execution=MutationExecutionPolicy(
            configured=True,
            scoped_mutation_enabled=True,
            workspace_root=tmp_path / "workspace",
        ),
        upload_base=tmp_path / "uploads",
    )
    handler = make_capabilities_handler(
        policy,
        config_path=tmp_path / "config.yaml",
        upload_base=tmp_path / "uploads",
        ops_supported=lambda: ("capabilities",),
    )
    feature = asyncio.run(handler({"detail": "full"}))["execution_features"][
        "host_runtime.scoped_verification_node_npm_v1"
    ]
    serialized = json.dumps(feature, sort_keys=True)
    assert str(secret_root) not in serialized
    assert feature["profile_id"] == "node_npm"
    assert feature["toolchain_digest"] == "a" * 64


@pytest.mark.skipif(sys.platform != "win32", reason="Windows AppContainer readiness only")
def test_real_windows_node_npm_readiness_is_physical_and_revokes_toolchain_acl(tmp_path: Path) -> None:
    from sentinelx_core.windows_mutation_sandbox import _dacl_entries

    profile, policy = _real_profile(tmp_path)
    before = tuple(_dacl_entries(profile.toolchain_root))
    result = probe_node_npm_verification_runtime(
        policy, tmp_path / "state", base_readiness=_base_ready(), force=True
    )
    after = tuple(_dacl_entries(profile.toolchain_root))
    assert result.available is True, result
    assert all(result.checks.values()), result.checks
    assert result.profile_id == "node_npm"
    assert result.toolchain_kind == "node_npm_v1"
    assert before == after


@pytest.mark.skipif(sys.platform != "win32", reason="Windows AppContainer readiness only")
def test_post_readiness_toolchain_tamper_fails_before_start(tmp_path: Path) -> None:
    profile, mutation_policy = _real_profile(tmp_path)
    verification = _provider_inputs(profile)
    state_root = tmp_path / "state"
    ready = probe_node_npm_verification_runtime(
        mutation_policy, state_root, base_readiness=_base_ready(), force=True
    )
    assert ready.available is True, ready
    cached_digest = cached_node_npm_toolchain_digest(
        mutation_policy, state_root, profile.profile_id
    )
    assert cached_digest == ready.toolchain_digest
    assert build_toolchain_manifest(profile).toolchain_digest == cached_digest

    audit = MutationAuditJournal(state_root, evidence_retention_days=7)
    readiness_events = audit.read_events()

    tamper_target = profile.resolve_npm_cli(require_exists=True)
    original_toolchain_bytes = tamper_target.read_bytes()
    tamper_target.write_bytes(original_toolchain_bytes + b"\n// sentinelx-readiness-tamper\n")
    tampered_digest = build_toolchain_manifest(profile).toolchain_digest
    assert tampered_digest != cached_digest
    policy = Policy(mutation_execution=mutation_policy, upload_base=tmp_path / "uploads")
    repository = RepositoryIdentity(
        vcs="git", authority="github.com", path="bewaterhere-coder/sentinelx-cloud-core"
    )
    semantic = SemanticIdentity(
        project_id="sentinelx-cloud-core",
        task_id="PR-011-scoped-verification-toolchain-dependency-capsule-v1",
        run_id="s04-tamper",
        attempt_id="1",
        slice_id="S04",
    )
    store = MutationScopeStore(state_root)
    record = store.provision_scope(
        mutation_policy,
        repository,
        semantic,
        allowed_operation_classes=(SCOPED_SCRIPT_OPERATION_CLASS,),
        provider_protected_roots=(state_root.resolve(),),
    )
    handler = make_profiled_script_run_handler(
        policy, tmp_path / "uploads", mutation_state_root=state_root
    )
    context = RequestContext(
        request_id="req-s04-tamper",
        op="script_run",
        opaque_ref="pr011-s04",
        received_at=datetime.now(UTC),
    )
    try:
        with pytest.raises(HandlerError) as exc_info:
            asyncio.run(
                handler(
                    context,
                    {
                        "execution_profile": "scoped_mutation",
                        "interpreter": "python3",
                        "content": "print('must-not-run')",
                        "cleanup": True,
                        "verification": verification,
                        "mutation": {
                            "scope_ref": {
                                "scope_id": record.scope_id,
                                "generation": record.generation,
                            }
                        },
                        "lineage": {
                            "project_id": semantic.project_id,
                            "task_id": semantic.task_id,
                            "run_id": semantic.run_id,
                            "attempt_id": semantic.attempt_id,
                            "slice_id": semantic.slice_id,
                        },
                        "repository": {
                            "vcs": repository.vcs,
                            "authority": repository.authority,
                            "path": repository.path,
                        },
                    },
                )
            )
        assert exc_info.value.code == "HostMutationVerificationAdmissionFailed"
        assert "changed since the verified readiness" in str(exc_info.value)
        assert audit.read_events() == readiness_events
    finally:
        tamper_target.write_bytes(original_toolchain_bytes)
        current = store.read_scope(record.scope_id)
        if current.state != "terminal":
            store.terminalize_scope(
                record.scope_id,
                record.generation,
                mutation_policy,
                repository,
                semantic,
                provider_protected_roots=(state_root.resolve(),),
            )
