from __future__ import annotations

import shutil
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import pytest

from sentinelx_core.mutation_audit import (
    MutationAuditBinding,
    MutationAuditJournal,
    MutationAuthorityEvidence,
    MutationProcessIntent,
)
from sentinelx_core.mutation_placement import (
    HostMutationScopeBindingMismatch,
    RepositoryIdentity,
    SemanticIdentity,
)
from sentinelx_core.mutation_sandbox import (
    HostMutationSandboxAclViolation,
    HostMutationSandboxPathViolation,
)
from sentinelx_core.mutation_scope import MutationScopeStore
from sentinelx_core.policy import MutationExecutionPolicy
from sentinelx_core.request_context import MutationLineage, RequestContext
from sentinelx_core.windows_mutation_sandbox import (
    WindowsMutationSandbox,
    _dacl_entries,
    _delete_appcontainer_profile,
    _ensure_appcontainer_profile,
    _profile_name,
    _set_exact_acl,
    final_executable_path,
    requested_mutation_identity,
    windows_sandbox_primitives_available,
)

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows AppContainer only")


class Fixture:
    def __init__(self, tmp_path: Path, *, attempt_id: str) -> None:
        self.root = tmp_path / "fixture"
        self.workspace_root = self.root / "workspaces"
        self.sibling = self.root / "sibling"
        self.protected = self.root / "protected"
        self.runtime = self.root / "runtime"
        for path in (self.workspace_root, self.sibling, self.protected, self.runtime):
            path.mkdir(parents=True, exist_ok=True)
        (self.sibling / "sentinel.txt").write_text("sibling-intact", encoding="utf-8")
        (self.protected / "sentinel.txt").write_text("protected-intact", encoding="utf-8")

        self.policy = MutationExecutionPolicy(
            configured=True,
            scoped_mutation_enabled=True,
            workspace_root=self.workspace_root,
            protected_roots=(self.protected,),
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
            task_id="SX-HMSA-001",
            run_id="s04-real-windows",
            attempt_id=attempt_id,
            slice_id="S04",
        )
        self.scope_store = MutationScopeStore(self.root / "state")
        self.record = self.scope_store.provision_scope(
            self.policy,
            self.repository,
            self.semantic,
            allowed_operation_classes=("workspace_materialize", "scoped_mutation"),
            provider_protected_roots=(self.protected,),
        )
        self.audit = MutationAuditJournal(self.root / "audit", evidence_retention_days=7)
        context = RequestContext(
            request_id=f"req-{attempt_id}",
            op="script_run",
            opaque_ref="s04-integration",
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
        evidence = self.audit.evidence.retain(b"S04 real Windows sandbox fixture\n")
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
        intent = MutationProcessIntent(
            interpreter="cmd.exe",
            argv=(str(cmd),),
            executable_final_path=final_executable_path(cmd),
            cwd_final_path=self.record.exact_workspace,
        )
        self.start = self.audit.begin(
            binding, evidence, authority=authority, process_intent=intent,
            requested_identity=requested_mutation_identity(self.record.unique_lease_key),
        )
        self.sandbox = WindowsMutationSandbox(
            policy=self.policy,
            scope_store=self.scope_store,
            repository=self.repository,
            semantic=self.semantic,
            provider_protected_roots=(self.protected,),
        )

    def activate(self):
        return self.sandbox.activate(self.record, self.start)


def _q(path: Path) -> str:
    return f'"{path}"'


def test_windows_primitives_are_really_available() -> None:
    available, detail = windows_sandbox_primitives_available()
    assert available, detail


def test_real_appcontainer_writes_only_exact_workspace(tmp_path: Path) -> None:
    fx = Fixture(tmp_path, attempt_id="exact-workspace")
    activation = fx.activate()
    retry_activation = fx.activate()
    assert retry_activation.sandbox_identity == activation.sandbox_identity
    app_sids = [
        sid
        for sid, _mask, _flags in _dacl_entries(activation.workspace)
        if sid.startswith("S-1-15-2-")
    ]
    assert app_sids == [activation.sandbox_identity]
    inside = activation.workspace / "inside.txt"
    parent_escape = fx.workspace_root / "parent-escape.txt"
    sibling_escape = fx.sibling / "sibling-escape.txt"
    protected_escape = fx.protected / "protected-escape.txt"

    # Keep cmd.exe syntax deliberately simple here. Shell/argv compatibility
    # belongs to S05; S04 is proving the OS write boundary from the exact cwd.
    command = (
        "echo inside>inside.txt & "
        "del /q ..\\..\\..\\sibling\\sentinel.txt & "
        "del /q ..\\..\\..\\protected\\sentinel.txt & "
        "echo parent>..\\..\\parent-escape.txt & "
        "echo sibling>..\\..\\..\\sibling\\sibling-escape.txt & "
        "echo protected>..\\..\\..\\protected\\protected-escape.txt"
    )
    process = fx.sandbox.spawn(
        activation,
        audit=fx.audit,
        audit_start=fx.start,
        argv=["cmd.exe", "/d", "/c", command],
    )
    assert process.contained is True
    assert process.breakaway_allowed is False
    assert process.wait(10), "AppContainer fixture did not exit"

    assert inside.exists()
    assert not parent_escape.exists()
    assert not sibling_escape.exists()
    assert not protected_escape.exists()
    assert (fx.sibling / "sentinel.txt").read_text(encoding="utf-8") == "sibling-intact"
    assert (fx.protected / "sentinel.txt").read_text(encoding="utf-8") == "protected-intact"

    active = fx.scope_store.read_scope(fx.record.scope_id)
    assert active.active_job_ids == ()
    assert active.active_process_ids == ()
    assert active.sandbox_write_authority_present is True
    assert active.sandbox_identity == activation.sandbox_identity

    terminal = fx.sandbox.terminalize(fx.record.scope_id, fx.record.generation)
    assert terminal.state == "terminal"
    assert terminal.active_job_ids == ()
    assert terminal.active_process_ids == ()
    assert terminal.sandbox_write_authority_present is False
    assert all(
        sid != activation.sandbox_identity
        for sid, _mask, _flags in _dacl_entries(activation.workspace)
    )


def test_spawn_audit_is_durable_before_first_instruction(tmp_path: Path, monkeypatch) -> None:
    fx = Fixture(tmp_path, attempt_id="spawn-order")
    activation = fx.activate()
    marker = activation.workspace / "first-instruction.txt"
    observed: list[str] = []
    original = fx.audit._durable_append

    def observe(event):
        if event.get("event") == "PROCESS_SPAWNED":
            assert not marker.exists(), "untrusted code ran before PROCESS_SPAWNED was durable"
            observed.append("spawn-durable")
        original(event)

    monkeypatch.setattr(fx.audit, "_durable_append", observe)
    process = fx.sandbox.spawn(
        activation,
        audit=fx.audit,
        audit_start=fx.start,
        argv=["cmd.exe", "/d", "/c", "echo executed>first-instruction.txt"],
    )
    assert observed == ["spawn-durable"]
    assert process.wait(10)
    assert marker.exists()
    fx.sandbox.terminalize(fx.record.scope_id, fx.record.generation)


def test_job_contains_child_and_termination_quiesces_tree(tmp_path: Path) -> None:
    fx = Fixture(tmp_path, attempt_id="job-tree")
    activation = fx.activate()
    batch = activation.workspace / "tree.cmd"
    batch.write_text(
        "@echo off\r\n"
        "start \"\" /b cmd.exe /d /c \"for /L %%i in (1,1,1000000000) do @rem\"\r\n"
        "for /L %%i in (1,1,1000000000) do @rem\r\n",
        encoding="utf-8",
    )
    process = fx.sandbox.spawn(
        activation,
        audit=fx.audit,
        audit_start=fx.start,
        argv=["cmd.exe", "/d", "/c", "tree.cmd"],
    )
    deadline = time.monotonic() + 3
    peak = process.active_process_count
    while time.monotonic() < deadline and peak < 2:
        time.sleep(0.05)
        peak = max(peak, process.active_process_count)
    assert peak >= 2, "fixture child never became visible in the Job"

    # Terminalization itself must revoke admission, terminate the whole Job,
    # remove the SID ACL, and only then publish terminal success.
    terminal = fx.sandbox.terminalize(fx.record.scope_id, fx.record.generation)
    assert terminal.state == "terminal"
    assert terminal.active_job_ids == ()
    assert terminal.active_process_ids == ()
    assert terminal.sandbox_write_authority_present is False
    assert process._released is True


def test_junction_at_exact_workspace_fails_closed(tmp_path: Path) -> None:
    fx = Fixture(tmp_path, attempt_id="junction")
    exact = Path(fx.record.exact_workspace)
    exact.parent.mkdir(parents=True, exist_ok=True)
    outside = fx.root / "junction-target"
    outside.mkdir()
    sentinel = outside / "sentinel.txt"
    sentinel.write_text("intact", encoding="utf-8")

    completed = subprocess.run(
        ["cmd.exe", "/d", "/c", "mklink", "/J", str(exact), str(outside)],
        capture_output=True,
        creationflags=0x08000000,
        timeout=10,
        check=False,
    )
    assert completed.returncode == 0, (completed.stdout, completed.stderr)
    try:
        with pytest.raises((HostMutationSandboxPathViolation, HostMutationScopeBindingMismatch)):
            fx.activate()
        assert sentinel.read_text(encoding="utf-8") == "intact"
        assert fx.scope_store.read_scope(fx.record.scope_id).active_process_ids == ()
    finally:
        if exact.exists():
            exact.rmdir()


def test_preexisting_foreign_appcontainer_acl_is_rejected(tmp_path: Path) -> None:
    fx = Fixture(tmp_path, attempt_id="foreign-sid")
    exact = Path(fx.record.exact_workspace)
    exact.mkdir(parents=True, exist_ok=True)
    foreign_name = _profile_name("foreign-lease-for-s04-regression")
    foreign_sid = _ensure_appcontainer_profile(foreign_name)
    try:
        _set_exact_acl(exact, fx.sandbox.broker_sid, foreign_sid)
        with pytest.raises(HostMutationSandboxAclViolation):
            fx.activate()
        entries = _dacl_entries(exact)
        assert any(sid == foreign_sid for sid, _mask, _flags in entries)
        assert fx.scope_store.read_scope(fx.record.scope_id).sandbox_identity is None
    finally:
        _set_exact_acl(exact, fx.sandbox.broker_sid, None)
        _delete_appcontainer_profile(foreign_name)


def test_terminal_cleanup_failure_stays_revoked_until_real_cleanup(tmp_path: Path) -> None:
    fx = Fixture(tmp_path, attempt_id="terminal-fail-closed")
    activation = fx.activate()

    def fail_cleanup(_record):
        raise RuntimeError("injected OS cleanup failure")

    with pytest.raises(RuntimeError, match="injected OS cleanup failure"):
        fx.scope_store.terminalize_scope(
            fx.record.scope_id,
            fx.record.generation,
            fx.policy,
            fx.repository,
            fx.semantic,
            provider_protected_roots=(fx.protected,),
            runtime_cleanup=fail_cleanup,
        )

    revoked = fx.scope_store.read_scope(fx.record.scope_id)
    assert revoked.state == "revoked"
    assert revoked.sandbox_identity == activation.sandbox_identity
    assert revoked.sandbox_write_authority_present is True

    terminal = fx.sandbox.terminalize(fx.record.scope_id, fx.record.generation)
    assert terminal.state == "terminal"
    assert terminal.active_job_ids == ()
    assert terminal.active_process_ids == ()
    assert terminal.sandbox_write_authority_present is False
