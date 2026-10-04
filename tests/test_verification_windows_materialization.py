from __future__ import annotations

import hashlib
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

import sentinelx_core.windows_mutation_sandbox as windows_sandbox
from sentinelx_core.mutation_audit import (
    MutationAuditBinding,
    MutationAuditJournal,
    MutationAuthorityEvidence,
    MutationProcessIntent,
)
from sentinelx_core.mutation_placement import RepositoryIdentity, SemanticIdentity
from sentinelx_core.mutation_scope import MutationScopeStore
from sentinelx_core.policy import MutationExecutionPolicy
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
from sentinelx_core.verification_runtime import build_verification_runtime_plan
from sentinelx_core.windows_mutation_sandbox import (
    WindowsMutationSandbox,
    _dacl_entries,
    final_executable_path,
    requested_mutation_identity,
)

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows AppContainer only")
HEAD_SHA = "2" * 40


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class VerificationFixture:
    def __init__(self, tmp_path: Path, *, attempt_id: str) -> None:
        self.root = tmp_path / "fixture"
        self.workspace_root = self.root / "workspaces"
        self.protected = self.root / "protected"
        self.canonical = self.root / "canonical"
        for path in (self.workspace_root, self.protected, self.canonical):
            path.mkdir(parents=True, exist_ok=True)
        (self.protected / "sentinel.txt").write_text("protected", encoding="utf-8")
        (self.canonical / "sentinel.txt").write_text("canonical", encoding="utf-8")

        self.profile = NodeNpmVerificationProfile(
            profile_id="node_npm",
            toolchain_root=self.root / "toolchain",
            source_snapshot_root=self.root / "sources",
            dependency_capsule_root=self.root / "capsules",
        )
        self._write_toolchain()
        source, capsule, lock_sha = self._write_provider_inputs()
        toolchain = build_toolchain_manifest(self.profile)
        request = VerificationRequest.from_mapping(
            {
                "profile": "node_npm",
                "source_id": source.source_id,
                "source_manifest_sha256": source.source_manifest_digest,
                "source_revision": source.transport.revision,
                "capsule_id": capsule.capsule_id,
                "package_lock_sha256": lock_sha,
            }
        )
        admission = build_verification_admission(
            profile=self.profile,
            request=request,
            source=source,
            capsule=capsule,
            toolchain=toolchain,
        )
        self.plan = build_verification_runtime_plan(self.profile, admission)

        self.policy = MutationExecutionPolicy(
            configured=True,
            scoped_mutation_enabled=True,
            workspace_root=self.workspace_root,
            protected_roots=(self.protected, self.canonical),
            runtime_read_roots=(),
            scope_ttl_seconds=600,
            evidence_retention_days=7,
        )
        self.repository = RepositoryIdentity(
            vcs="git",
            authority="github.com",
            path="bewaterhere-coder/sentinelx-cloud-core",
        )
        self.semantic = SemanticIdentity(
            project_id="sentinelx-cloud-core",
            task_id="PR-011",
            run_id="s02-windows",
            attempt_id=attempt_id,
            slice_id="S02",
        )
        self.scope_store = MutationScopeStore(self.root / "state")
        self.record = self.scope_store.provision_scope(
            self.policy,
            self.repository,
            self.semantic,
            allowed_operation_classes=("workspace_materialize", "scoped_mutation"),
            provider_protected_roots=(self.protected, self.canonical),
        )
        self.audit = MutationAuditJournal(self.root / "audit", evidence_retention_days=7)
        context = RequestContext(
            request_id=f"req-{attempt_id}",
            op="script_run",
            opaque_ref="pr011-s02",
            received_at=datetime.now(UTC),
        )
        lineage = MutationLineage.from_mapping(
            {
                "project_id": self.semantic.project_id,
                "task_id": self.semantic.task_id,
                "run_id": self.semantic.run_id,
                "attempt_id": self.semantic.attempt_id,
                "slice_id": self.semantic.slice_id,
            }
        )
        evidence = self.audit.evidence.retain(b"PR-011 S02 verification fixture\n")
        binding = MutationAuditBinding.from_context(
            context,
            lineage,
            scope_id=self.record.scope_id,
            scope_generation=self.record.generation,
            workspace_id=self.record.workspace_id,
            unique_lease_key=self.record.unique_lease_key,
        )
        cmd = Path(shutil.which("cmd.exe") or r"C:\Windows\System32\cmd.exe")
        authority = MutationAuthorityEvidence(
            scope_digest=self.record.scope_digest,
            exact_workspace_digest=self.record.exact_workspace_digest,
            protected_inventory_digest=self.record.protected_inventory_digest,
            policy_digest=self.record.policy_digest,
            repository_identity_digest=self.record.repository_identity_digest,
            semantic_identity_digest=self.record.semantic_identity_digest,
        )
        process_intent = MutationProcessIntent(
            interpreter="cmd.exe",
            argv=(str(cmd),),
            executable_final_path=final_executable_path(cmd),
            cwd_final_path=str(Path(self.record.exact_workspace) / "source"),
        )
        self.start = self.audit.begin(
            binding,
            evidence,
            authority=authority,
            process_intent=process_intent,
            requested_identity=requested_mutation_identity(self.record.unique_lease_key),
            verification_intent=self.plan.audit_intent,
        )
        self.sandbox = WindowsMutationSandbox(
            policy=self.policy,
            scope_store=self.scope_store,
            repository=self.repository,
            semantic=self.semantic,
            provider_protected_roots=(self.protected, self.canonical),
        )
        self.activation = self.sandbox.activate(self.record, self.start)
        self.materialized = self.sandbox.materialize_verification(
            self.activation,
            self.start,
            self.plan,
        )

    def _write_toolchain(self) -> None:
        self.profile.toolchain_root.mkdir(parents=True)
        self.profile.resolve_node(require_exists=False).write_bytes(b"node-placeholder")
        npm_cli = self.profile.resolve_npm_cli(require_exists=False)
        npm_cli.parent.mkdir(parents=True)
        npm_cli.write_bytes(b"npm-cli-placeholder")
        (self.profile.toolchain_root / "runtime.dat").write_bytes(b"runtime")

    def _write_provider_inputs(self):
        source_store = self.profile.source_snapshot_path("source-a")
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
            "transport": {"type": "github-pr", "pr_number": 11, "head_sha": HEAD_SHA},
            "source_subpath": "fixture",
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

        capsule_store = self.profile.dependency_capsule_path("capsule-a")
        cache = capsule_store / "npm-cache"
        cache.mkdir(parents=True)
        package = b"offline-package"
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
        return (
            load_source_snapshot(source_store, limits=self.profile.limits),
            load_dependency_capsule(capsule_store, limits=self.profile.limits),
            lock_sha,
        )


def _quoted(path: Path) -> str:
    return f'"{path}"'


def test_verification_toolchain_is_read_execute_only_and_revoked_at_terminal(tmp_path: Path) -> None:
    fx = VerificationFixture(tmp_path, attempt_id="rx-only")
    workspace_write_marker = fx.materialized.source_root / "workspace-write.txt"
    read_marker = fx.materialized.source_root / "toolchain-read.txt"
    read_error = fx.materialized.source_root / "toolchain-read-error.txt"
    read_status = fx.materialized.source_root / "toolchain-read-status.txt"
    toolchain_write = fx.profile.toolchain_root / "tamper.txt"
    source_store_write = fx.profile.source_snapshot_root / "tamper.txt"
    capsule_store_write = fx.profile.dependency_capsule_root / "tamper.txt"
    protected_write = fx.protected / "tamper.txt"
    canonical_write = fx.canonical / "tamper.txt"
    runtime_file = fx.profile.toolchain_root / "runtime.dat"
    app_sid = fx.activation.sandbox_identity
    for materialized_root in (
        fx.materialized.source_root,
        fx.materialized.npm_cache_root,
        fx.materialized.shim_root,
    ):
        assert any(
            sid == app_sid for sid, _mask, _flags in _dacl_entries(materialized_root)
        ), f"materialized verification root lost AppContainer authority: {materialized_root}"

    command = (
        "echo workspace-ok>workspace-write.txt & "
        f"type {_quoted(runtime_file)} >toolchain-read.txt 2>toolchain-read-error.txt "
        "&& echo 0>toolchain-read-status.txt || echo 1>toolchain-read-status.txt & "
        f"echo tamper>{_quoted(toolchain_write)} & "
        f"echo tamper>{_quoted(source_store_write)} & "
        f"echo tamper>{_quoted(capsule_store_write)} & "
        f"echo tamper>{_quoted(protected_write)} & "
        f"echo tamper>{_quoted(canonical_write)} & exit /b 0"
    )
    process = fx.sandbox.spawn(
        fx.activation,
        audit=fx.audit,
        audit_start=fx.start,
        argv=["cmd.exe", "/d", "/c", command],
        cwd=fx.materialized.source_root,
        verification=fx.materialized,
    )
    assert process.wait(15), "verification ACL probe did not exit"
    assert workspace_write_marker.read_text(encoding="utf-8").strip() == "workspace-ok"
    status = read_status.read_text(encoding="utf-8").strip() if read_status.exists() else "<missing>"
    error = read_error.read_text(encoding="utf-8", errors="replace").strip() if read_error.exists() else "<missing>"
    assert read_marker.exists(), f"toolchain direct read failed; status={status!r}; stderr={error!r}"
    assert read_marker.read_bytes() == b"runtime"
    assert not toolchain_write.exists()
    assert not source_store_write.exists()
    assert not capsule_store_write.exists()
    assert not protected_write.exists()
    assert not canonical_write.exists()

    assert any(sid == app_sid for sid, _mask, _flags in _dacl_entries(fx.profile.toolchain_root))
    terminal = fx.sandbox.terminalize(fx.record.scope_id, fx.record.generation)
    assert terminal.state == "terminal"
    assert all(sid != app_sid for sid, _mask, _flags in _dacl_entries(fx.profile.toolchain_root))


def test_toolchain_tamper_fails_before_first_process_creation(tmp_path: Path, monkeypatch) -> None:
    fx = VerificationFixture(tmp_path, attempt_id="pre-spawn-toolchain-tamper")
    (fx.profile.toolchain_root / "runtime.dat").write_bytes(b"tampered")
    created = False

    def forbidden_spawn(**kwargs):
        nonlocal created
        created = True
        raise AssertionError("root process creation must not be reached")

    monkeypatch.setattr(windows_sandbox, "create_suspended_appcontainer_job_process", forbidden_spawn)
    with pytest.raises(ValueError, match="toolchain changed before SPAWN"):
        fx.sandbox.spawn(
            fx.activation,
            audit=fx.audit,
            audit_start=fx.start,
            argv=["cmd.exe", "/d", "/c", "echo must-not-run"],
            cwd=fx.materialized.source_root,
            verification=fx.materialized,
        )
    assert created is False
    terminal = fx.sandbox.terminalize(fx.record.scope_id, fx.record.generation)
    assert terminal.state == "terminal"


def test_source_lock_tamper_fails_before_first_process_creation(tmp_path: Path, monkeypatch) -> None:
    fx = VerificationFixture(tmp_path, attempt_id="pre-spawn-source-tamper")
    (fx.materialized.source_root / "package-lock.json").write_bytes(b"tampered")
    created = False

    def forbidden_spawn(**kwargs):
        nonlocal created
        created = True
        raise AssertionError("root process creation must not be reached")

    monkeypatch.setattr(windows_sandbox, "create_suspended_appcontainer_job_process", forbidden_spawn)
    with pytest.raises(ValueError, match="payload digest mismatch|package-lock"):
        fx.sandbox.spawn(
            fx.activation,
            audit=fx.audit,
            audit_start=fx.start,
            argv=["cmd.exe", "/d", "/c", "echo must-not-run"],
            cwd=fx.materialized.source_root,
            verification=fx.materialized,
        )
    assert created is False
    terminal = fx.sandbox.terminalize(fx.record.scope_id, fx.record.generation)
    assert terminal.state == "terminal"
