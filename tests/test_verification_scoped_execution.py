from __future__ import annotations

import asyncio
import hashlib
import json
import os
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

from sentinelx_core.executor import HandlerError
from sentinelx_core.handlers.scoped_script import make_profiled_script_run_handler
from sentinelx_core.mutation_audit import (
    EVENT_FINISHED,
    EVENT_SPAWNED,
    EVENT_STARTED,
    MutationAuditJournal,
)
from sentinelx_core.mutation_placement import RepositoryIdentity, SemanticIdentity
from sentinelx_core.mutation_scope import MutationScopeStore
from sentinelx_core.policy import MutationExecutionPolicy, Policy
from sentinelx_core.request_context import RequestContext
from sentinelx_core.verification_profile import (
    NodeNpmVerificationProfile,
    compute_dependency_payload_digest,
    compute_source_manifest_digest,
)

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows scoped verification only")

HEAD_SHA = "3" * 40


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _real_node_profile(tmp_path: Path) -> NodeNpmVerificationProfile:
    node_executable = shutil.which("node")
    if node_executable is None:
        pytest.skip("Node is not installed on this Windows runner")
    source_root = Path(node_executable).resolve().parent
    npm_source = source_root / "node_modules" / "npm"
    if not (npm_source / "bin" / "npm-cli.js").is_file():
        pytest.skip("Node toolchain does not contain provider-resolvable npm-cli.js")

    # The verification profile owns a bounded toolchain tree. Do not grant
    # AppContainer ACLs to GitHub Runner's shared C:\hostedtoolcache hierarchy.
    toolchain_root = tmp_path / "provider-node-toolchain"
    toolchain_root.mkdir(parents=True)
    shutil.copy2(Path(node_executable).resolve(), toolchain_root / "node.exe")
    shutil.copytree(npm_source, toolchain_root / "node_modules" / "npm")
    return NodeNpmVerificationProfile(
        profile_id="node_npm",
        toolchain_root=toolchain_root,
        source_snapshot_root=tmp_path / "provider-sources",
        dependency_capsule_root=tmp_path / "provider-capsules",
    )


def _provider_inputs(profile: NodeNpmVerificationProfile) -> dict[str, str]:
    source_store = profile.source_snapshot_path("s03-source")
    payload = source_store / "payload"
    payload.mkdir(parents=True)

    package = {
        "name": "sentinelx-s03-offline-fixture",
        "version": "1.0.0",
        "private": True,
        "scripts": {
            "check": "node -e \"console.log('offline-check-ok')\"",
        },
    }
    lock = {
        "name": package["name"],
        "version": package["version"],
        "lockfileVersion": 3,
        "requires": True,
        "packages": {
            "": {
                "name": package["name"],
                "version": package["version"],
            }
        },
    }
    package_bytes = (json.dumps(package, sort_keys=True) + "\n").encode("utf-8")
    lock_bytes = (json.dumps(lock, sort_keys=True) + "\n").encode("utf-8")
    (payload / "package.json").write_bytes(package_bytes)
    (payload / "package-lock.json").write_bytes(lock_bytes)
    lock_sha = _sha(lock_bytes)

    source_manifest: dict[str, object] = {
        "schema_version": 1,
        "kind": "verification_source_snapshot",
        "source_id": "s03-source",
        "repository": {
            "vcs": "git",
            "authority": "github.com",
            "path": "bewaterhere-coder/sentinelx-cloud-core",
        },
        "transport": {"type": "github-pr", "pr_number": 11, "head_sha": HEAD_SHA},
        "source_subpath": "tests/s03-fixture",
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

    capsule_store = profile.dependency_capsule_path("s03-empty-cache")
    (capsule_store / "npm-cache").mkdir(parents=True)
    capsule_files: list[dict[str, object]] = []
    capsule = {
        "schema_version": 1,
        "kind": "node_npm_dependency_capsule",
        "capsule_id": "s03-empty-cache",
        "package_lock_sha256": lock_sha,
        "files": capsule_files,
        "payload_digest": compute_dependency_payload_digest(capsule_files),
    }
    (capsule_store / "verification-capsule.json").write_text(
        json.dumps(capsule, sort_keys=True), encoding="utf-8"
    )
    return {
        "profile": profile.profile_id,
        "source_id": "s03-source",
        "source_manifest_sha256": str(source_manifest["source_manifest_digest"]),
        "source_revision": HEAD_SHA,
        "capsule_id": "s03-empty-cache",
        "package_lock_sha256": lock_sha,
    }


def _fixture(tmp_path: Path):
    profile = _real_node_profile(tmp_path)
    verification = _provider_inputs(profile)
    workspace_root = tmp_path / "workspaces"
    state_root = tmp_path / "provider-state"
    upload_base = tmp_path / "uploads"
    protected = tmp_path / "protected"
    for root in (workspace_root, state_root, upload_base, protected):
        root.mkdir(parents=True, exist_ok=True)

    runtime_roots = {Path(sys.prefix).resolve(), Path(sys.base_prefix).resolve()}
    pwsh = shutil.which("pwsh")
    if pwsh is None:
        pytest.skip("pwsh is required for the S03 physical verification fixture")
    runtime_roots.add(Path(pwsh).resolve().parent)

    mutation_policy = MutationExecutionPolicy(
        configured=True,
        scoped_mutation_enabled=True,
        workspace_root=workspace_root,
        protected_roots=(protected,),
        runtime_read_roots=tuple(sorted(runtime_roots, key=lambda item: str(item).casefold())),
        scope_ttl_seconds=600,
        evidence_retention_days=7,
        operator_unrestricted_enabled=False,
        verification_profiles=(profile,),
    )
    policy = Policy(mutation_execution=mutation_policy, upload_base=upload_base)
    repository = RepositoryIdentity(
        vcs="git",
        authority="github.com",
        path="bewaterhere-coder/sentinelx-cloud-core",
    )
    semantic = SemanticIdentity(
        project_id="sentinelx-cloud-core",
        task_id="PR-011-scoped-verification-toolchain-dependency-capsule-v1",
        run_id="s03-offline-node-npm",
        attempt_id="1",
        slice_id="S03",
    )
    store = MutationScopeStore(state_root)
    record = store.provision_scope(
        mutation_policy,
        repository,
        semantic,
        allowed_operation_classes=("scoped_script",),
        provider_protected_roots=(state_root.resolve(),),
    )
    handler = make_profiled_script_run_handler(
        policy,
        upload_base,
        mutation_state_root=state_root,
    )
    context = RequestContext(
        request_id="req-s03",
        op="script_run",
        opaque_ref="pr011-s03",
        received_at=datetime.now(UTC),
    )
    lineage = {
        "project_id": semantic.project_id,
        "task_id": semantic.task_id,
        "run_id": semantic.run_id,
        "attempt_id": semantic.attempt_id,
        "slice_id": semantic.slice_id,
    }
    repository_payload = {
        "vcs": repository.vcs,
        "authority": repository.authority,
        "path": repository.path,
    }
    mutation = {
        "execution_profile": "scoped_mutation",
        "scope_ref": {"scope_id": record.scope_id, "generation": record.generation},
    }
    return profile, verification, handler, context, store, record, mutation, lineage, repository_payload


def _run(handler, context, payload):
    return asyncio.run(handler(context, payload))


def test_profiled_scoped_execution_runs_real_node_npm_offline_and_bounds_evidence(
    tmp_path: Path, monkeypatch
) -> None:
    profile, verification, handler, context, store, record, mutation, lineage, repo = _fixture(tmp_path)
    shadow = tmp_path / "host-shadow"
    shadow.mkdir()
    marker = tmp_path / "host-shadow-ran.txt"
    (shadow / "npm.cmd").write_text(
        f"@echo shadow>{marker}\r\nexit /b 0\r\n", encoding="utf-8"
    )
    monkeypatch.setenv("PATH", str(shadow) + os.pathsep + os.environ.get("PATH", ""))
    monkeypatch.setenv("GITHUB_TOKEN", "must-not-inherit")
    monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:9")

    content = r"""
$ErrorActionPreference='Stop'
if ($env:GITHUB_TOKEN) { throw 'credential leaked' }
if ($env:HTTPS_PROXY) { throw 'proxy leaked' }
if ($env:NPM_CONFIG_OFFLINE -ne 'true') { throw 'npm offline mode missing' }
node --version
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
npm --version
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
npm ci --offline
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
npm run check
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
npm view sentinelx-pr011-s03-package-that-does-not-exist-6f43b9 version --offline *> $null
if ($LASTEXITCODE -eq 0) { throw 'offline cache miss unexpectedly succeeded' }
Write-Output 'cache-miss-offline-ok'
exit 0
"""
    result = _run(
        handler,
        context,
        {
            "interpreter": "pwsh",
            "content": content,
            "timeout": 120,
            "cleanup": True,
            "verification": verification,
            "mutation": mutation,
            "lineage": lineage,
            "repository": repo,
        },
    )
    if result["ok"] is not True:
        print("S03_RESULT=" + json.dumps(result, sort_keys=True, default=str))
    assert result["ok"] is True, result
    assert result["cwd"] == "source"
    assert "offline-check-ok" in result["output"]
    assert "cache-miss-offline-ok" in result["output"]
    assert "command" not in result
    assert not marker.exists()
    evidence = result["verification"]
    assert evidence["profile_id"] == "node_npm"
    assert evidence["source_revision"] == HEAD_SHA
    assert evidence["network_mode"] == "none"
    assert evidence["offline"] is True
    assert evidence["verified_package_lock_sha256"] == verification["package_lock_sha256"]
    serialized = json.dumps(evidence, sort_keys=True)
    assert str(profile.toolchain_root) not in serialized
    assert str(profile.source_snapshot_root) not in serialized
    assert result["terminal_state"] == "terminal"
    assert store.read_scope(record.scope_id).state == "terminal"

    events = MutationAuditJournal(store.root.parent, evidence_retention_days=7).read_events(
        result["audit_operation_id"]
    )
    assert [item["event"] for item in events] == [EVENT_STARTED, EVENT_SPAWNED, EVENT_FINISHED]
    assert events[0]["verification_intent"]["network_mode"] == "none"
    assert events[1]["containment"]["breakaway_allowed"] is False
    assert events[2]["closure"]["process_tree_quiescent"] is True


def test_profiled_scoped_execution_rejects_caller_path_and_proxy_authority_before_start(
    tmp_path: Path,
) -> None:
    _profile, verification, handler, context, store, record, mutation, lineage, repo = _fixture(tmp_path)
    with pytest.raises(HandlerError) as exc_info:
        _run(
            handler,
            context,
            {
                "interpreter": "pwsh",
                "content": "Write-Output 'must-not-run'",
                "timeout": 30,
                "env": {"PATH": str(tmp_path), "HTTPS_PROXY": "http://127.0.0.1:1"},
                "verification": verification,
                "mutation": mutation,
                "lineage": lineage,
                "repository": repo,
            },
        )
    assert exc_info.value.code == "HostMutationVerificationAdmissionFailed"
    assert store.read_scope(record.scope_id).state == "provisioned"
    assert MutationAuditJournal(store.root.parent, evidence_retention_days=7).read_events() == []
