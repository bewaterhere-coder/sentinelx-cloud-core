from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from sentinelx_core.handlers.script import prepare_scoped_script_evidence
from sentinelx_core.jobs import MutationJobIdentityError, build_completed_event_data
from sentinelx_core.mutation_audit import (
    EVENT_FINISHED,
    EVENT_SPAWNED,
    EVENT_STARTED,
    MutationAuditBinding,
    MutationAuditDurabilityError,
    MutationAuditJournal,
    MutationAuthorityEvidence,
    MutationContainmentEvidence,
    MutationFinishClosureEvidence,
    MutationOsIdentityEvidence,
    MutationProcessIntent,
    MutationSpawnEvidence,
    RequestedMutationIdentity,
)
from sentinelx_core.request_context import MutationLineage, RequestContext


def _context() -> RequestContext:
    return RequestContext(
        request_id="req-authoritative",
        op="script_run",
        opaque_ref="opaque-authoritative",
        received_at=datetime.now(UTC),
    )


def _lineage() -> MutationLineage:
    return MutationLineage.from_mapping(
        {
            "project_id": "sentinelx-cloud-core",
            "task_id": "SX-HMSA-001",
            "run_id": "run-3",
            "attempt_id": "attempt-1",
            "slice_id": "S03",
        }
    )


def _binding(*, job_id: str | None = None) -> MutationAuditBinding:
    return MutationAuditBinding.from_context(
        _context(),
        _lineage(),
        scope_id="scope-1",
        scope_generation=4,
        workspace_id="workspace-1",
        unique_lease_key="lease-1",
        job_id=job_id,
    )


def _authority() -> MutationAuthorityEvidence:
    return MutationAuthorityEvidence(
        scope_digest="scope-digest",
        exact_workspace_digest="workspace-digest",
        protected_inventory_digest="protected-digest",
        policy_digest="policy-digest",
        repository_identity_digest="repository-digest",
        semantic_identity_digest=_lineage().digest,
    )


def _intent() -> MutationProcessIntent:
    return MutationProcessIntent(
        interpreter="python3",
        argv=(r"C:\Python\python.exe", r"C:\scope\script.py"),
        executable_final_path=r"C:\Python\python.exe",
        cwd_final_path=r"C:\scope",
    )


def _requested() -> RequestedMutationIdentity:
    return RequestedMutationIdentity(
        host_platform="windows",
        host_user_sid="S-1-5-18",
        sandbox_kind="appcontainer",
        sandbox_profile="SentinelX.Mutation.fixture",
        sandbox_identity="S-1-15-2-123",
    )


def _spawn_evidence() -> MutationSpawnEvidence:
    return MutationSpawnEvidence(
        pid=4242,
        ppid=3131,
        executable_final_path=_intent().executable_final_path,
        cwd_final_path=_intent().cwd_final_path,
        os_identity=MutationOsIdentityEvidence(
            process_user_sid=_requested().host_user_sid,
            appcontainer_sid=_requested().sandbox_identity,
            is_appcontainer=True,
        ),
        containment=MutationContainmentEvidence(
            job_binding="job-object-1",
            contained=True,
            breakaway_allowed=False,
            active_process_count=1,
        ),
    )


def _closure() -> MutationFinishClosureEvidence:
    return MutationFinishClosureEvidence(
        scope_state="terminal",
        scope_digest=_authority().scope_digest,
        protected_inventory_digest=_authority().protected_inventory_digest,
        sandbox_identity=_requested().sandbox_identity,
        job_binding="job-object-1",
        root_pid=4242,
        job_handle_closed=True,
        job_active_process_count=0,
        active_job_ids=(),
        active_process_ids=(),
        sandbox_write_authority_present=False,
        process_tree_quiescent=True,
        terminalized_at="2026-09-30T00:00:00Z",
    )


def _start(journal: MutationAuditJournal, *, job_id: str | None = None):
    evidence = journal.evidence.retain(b"print('hello')\n")
    return journal.begin(
        _binding(job_id=job_id), evidence, authority=_authority(),
        process_intent=_intent(), requested_identity=_requested(),
    )


def test_request_transport_identity_is_separate_from_payload_lineage(tmp_path: Path):
    journal = MutationAuditJournal(tmp_path)
    payload = {
        "interpreter": "python3",
        "content": "print('ok')\n",
        "request_id": "spoofed-request",
        "opaque_ref": "spoofed-opaque",
        "job_id": "job-1",
    }

    prepared = prepare_scoped_script_evidence(
        context=_context(),
        payload=payload,
        lineage=_lineage(),
        audit=journal,
        scope_id="scope-1",
        scope_generation=4,
        workspace_id="workspace-1",
        unique_lease_key="lease-1",
        authority=_authority(),
        process_intent=_intent(),
        requested_identity=_requested(),
    )

    event = journal.read_events(prepared.audit_start.operation_id)[0]
    assert event["binding"]["request_id"] == "req-authoritative"
    assert event["binding"]["opaque_ref"] == "opaque-authoritative"
    assert event["binding"]["lineage"]["run_id"] == "run-3"
    assert event["binding"]["job_id"] == "job-1"
    assert event["authority"]["scope_digest"] == "scope-digest"
    assert event["authority"]["protected_inventory_digest"] == "protected-digest"
    assert event["process_intent"]["argv"] == list(_intent().argv)
    assert event["requested_identity"]["sandbox_identity"] == _requested().sandbox_identity


def test_forensic_script_is_retained_before_start_and_survives_cleanup(tmp_path: Path):
    journal = MutationAuditJournal(tmp_path, evidence_retention_days=30)
    prepared = prepare_scoped_script_evidence(
        context=_context(),
        payload={"interpreter": "python3", "content": "print('durable')\n"},
        lineage=_lineage(),
        audit=journal,
        scope_id="scope-1",
        scope_generation=4,
        workspace_id="workspace-1",
        unique_lease_key="lease-1",
        authority=_authority(),
        process_intent=_intent(),
        requested_identity=_requested(),
    )

    staging = tmp_path / "temporary-execution-staging"
    staging.mkdir()
    (staging / "script.py").write_text("temporary", encoding="utf-8")
    for child in staging.iterdir():
        child.unlink()
    staging.rmdir()

    assert journal.evidence.read_verified(prepared.evidence) == prepared.exact_bytes
    start_event = journal.read_events(prepared.audit_start.operation_id)[0]
    assert start_event["event"] == EVENT_STARTED
    assert start_event["script_evidence"]["sha256"] == prepared.evidence.sha256
    assert "_artifact_path" not in start_event["script_evidence"]
    assert str(tmp_path) not in start_event["script_evidence"]["artifact_ref"]


def test_start_durability_failure_precedes_workspace_materialization_and_spawn(
    tmp_path: Path, monkeypatch
):
    journal = MutationAuditJournal(tmp_path)
    workspace = tmp_path / "workspace-root" / "admitted-workspace"
    spawned: list[int] = []

    def fail_start(event):
        assert event["event"] == EVENT_STARTED
        raise MutationAuditDurabilityError("injected fsync failure")

    monkeypatch.setattr(journal, "_durable_append", fail_start)

    with pytest.raises(MutationAuditDurabilityError):
        prepare_scoped_script_evidence(
            context=_context(),
            payload={"interpreter": "python3", "content": "print('never runs')\n"},
            lineage=_lineage(),
            audit=journal,
            scope_id="scope-1",
            scope_generation=4,
            workspace_id="workspace-1",
            unique_lease_key="lease-1",
            authority=_authority(),
            process_intent=_intent(),
            requested_identity=_requested(),
        )

    assert not workspace.exists()
    assert spawned == []
    # Evidence is intentionally retained even when START itself fails; losing it
    # would make the attempted mutation less forensically observable.
    assert list(journal.evidence.root.glob("*.script"))


def test_spawn_audit_failure_kills_suspended_child_and_never_resumes(
    tmp_path: Path, monkeypatch
):
    journal = MutationAuditJournal(tmp_path)
    start = _start(journal)
    original = journal._durable_append
    calls = {"terminated": 0, "resumed": 0}

    def fail_spawn(event):
        if event["event"] == EVENT_SPAWNED:
            raise MutationAuditDurabilityError("injected spawn fsync failure")
        return original(event)

    monkeypatch.setattr(journal, "_durable_append", fail_spawn)

    with pytest.raises(MutationAuditDurabilityError):
        journal.commit_spawn_before_resume(
            start,
            _spawn_evidence(),
            terminate_suspended=lambda: calls.__setitem__("terminated", calls["terminated"] + 1),
            resume_suspended=lambda: calls.__setitem__("resumed", calls["resumed"] + 1),
        )

    assert calls == {"terminated": 1, "resumed": 0}
    assert [event["event"] for event in journal.read_events(start.operation_id)] == [
        EVENT_STARTED
    ]


def test_successful_spawn_is_recorded_before_resume(tmp_path: Path):
    journal = MutationAuditJournal(tmp_path)
    start = _start(journal)
    order: list[str] = []
    original = journal._durable_append

    def observe(event):
        original(event)
        order.append(event["event"])

    journal._durable_append = observe  # type: ignore[method-assign]
    journal.commit_spawn_before_resume(
        start,
        _spawn_evidence(),
        terminate_suspended=lambda: order.append("TERMINATED"),
        resume_suspended=lambda: order.append("RESUMED"),
    )

    assert order == [EVENT_SPAWNED, "RESUMED"]
    spawned = journal.read_events(start.operation_id)[1]
    assert spawned["ppid"] == 3131
    assert spawned["executable_final_path"] == _intent().executable_final_path
    assert spawned["cwd_final_path"] == _intent().cwd_final_path
    assert spawned["os_identity"]["is_appcontainer"] is True
    assert spawned["containment"]["contained"] is True


def test_crash_after_start_does_not_invent_false_finish(tmp_path: Path):
    journal = MutationAuditJournal(tmp_path)
    start = _start(journal)

    # Simulate process loss by simply abandoning the operation after START.
    reopened = MutationAuditJournal(tmp_path)
    events = reopened.read_events(start.operation_id)

    assert [event["event"] for event in events] == [EVENT_STARTED]
    assert all(event["event"] != EVENT_FINISHED for event in events)


def test_full_lifecycle_preserves_one_binding_digest(tmp_path: Path):
    journal = MutationAuditJournal(tmp_path)
    start = _start(journal)
    spawn = journal.record_spawn(start, _spawn_evidence())
    finish_ref = journal.finish(
        start, status="succeeded", closure=_closure(), returncode=0
    )

    events = journal.read_events(start.operation_id)
    assert [event["event"] for event in events] == [
        EVENT_STARTED,
        EVENT_SPAWNED,
        EVENT_FINISHED,
    ]
    assert events[0]["binding_digest"] == start.binding_digest
    assert events[1]["binding_digest"] == start.binding_digest
    assert events[2]["binding_digest"] == start.binding_digest
    assert spawn.operation_id == start.operation_id
    assert finish_ref.startswith(f"mutation-audit:{start.operation_id}:finish:")
    assert events[2]["closure"]["scope_state"] == "terminal"
    assert events[2]["closure"]["process_tree_quiescent"] is True


def test_finish_rejects_unclosed_scope_without_fabricating_finish(tmp_path: Path):
    journal = MutationAuditJournal(tmp_path)
    start = _start(journal)
    unclosed = MutationFinishClosureEvidence(
        scope_state="revoked",
        scope_digest=_authority().scope_digest,
        protected_inventory_digest=_authority().protected_inventory_digest,
        sandbox_identity=_requested().sandbox_identity,
        job_binding="job-object-1",
        root_pid=4242,
        job_handle_closed=False,
        job_active_process_count=1,
        active_job_ids=("job-object-1",),
        active_process_ids=("4242",),
        sandbox_write_authority_present=True,
        process_tree_quiescent=False,
        terminalized_at="",
    )
    with pytest.raises(Exception, match="terminal scope"):
        journal.finish(start, status="succeeded", closure=unclosed, returncode=0)
    assert [event["event"] for event in journal.read_events(start.operation_id)] == [EVENT_STARTED]


def test_materialization_uses_exact_retained_bytes(tmp_path: Path):
    journal = MutationAuditJournal(tmp_path)
    prepared = prepare_scoped_script_evidence(
        context=_context(),
        payload={"interpreter": "python3", "content": "print('exact')\n"},
        lineage=_lineage(),
        audit=journal,
        scope_id="scope-1",
        scope_generation=4,
        workspace_id="workspace-1",
        unique_lease_key="lease-1",
        authority=_authority(),
        process_intent=_intent(),
        requested_identity=_requested(),
    )
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    destination = workspace / "script.py"

    digest = journal.evidence.materialize_verified(prepared.evidence, destination)

    assert destination.read_bytes() == prepared.exact_bytes
    assert digest == prepared.evidence.sha256


def test_background_completion_carries_same_mutation_identity(tmp_path: Path):
    journal = MutationAuditJournal(tmp_path)
    start = _start(journal, job_id="job-1")
    identity = start.background_identity()
    started = datetime.now(UTC)

    event = build_completed_event_data(
        job_id="job-1",
        op="script_run",
        host="host-1",
        dispatch_response={
            "ok": True,
            "result": {
                "ok": True,
                "returncode": 0,
                "output": "done",
                "mutation_identity": identity,
            },
        },
        started_at=started,
        finished_at=started + timedelta(seconds=2),
    )

    assert event["mutation_identity"] == identity
    assert event["mutation_identity"]["request_id"] == "req-authoritative"
    assert event["mutation_identity"]["semantic_digest"] == _lineage().digest


def test_background_completion_rejects_job_identity_drift(tmp_path: Path):
    journal = MutationAuditJournal(tmp_path)
    start = _start(journal, job_id="job-original")
    started = datetime.now(UTC)

    with pytest.raises(MutationJobIdentityError):
        build_completed_event_data(
            job_id="job-other",
            op="script_run",
            host="host-1",
            dispatch_response={
                "ok": True,
                "result": {
                    "ok": True,
                    "returncode": 0,
                    "output": "done",
                    "mutation_identity": start.background_identity(),
                },
            },
            started_at=started,
            finished_at=started + timedelta(seconds=1),
        )


def test_retention_prunes_only_expired_artifacts(tmp_path: Path):
    journal = MutationAuditJournal(tmp_path, evidence_retention_days=2)
    old = journal.evidence.retain(b"old")
    fresh = journal.evidence.retain(b"fresh")
    old_time = datetime.now(UTC) - timedelta(days=4)
    os.utime(old._artifact_path, (old_time.timestamp(), old_time.timestamp()))

    removed = journal.evidence.prune_expired(now=datetime.now(UTC))

    assert removed == 1
    assert not old._artifact_path.exists()
    assert journal.evidence.read_verified(fresh) == b"fresh"
