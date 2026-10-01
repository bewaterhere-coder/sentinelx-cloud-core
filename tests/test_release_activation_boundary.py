from __future__ import annotations

import asyncio
from pathlib import Path

import sentinelx_core.handlers.basic as basic
import sentinelx_core.mutation_readiness as readiness_module
import sentinelx_core.windows_mutation_sandbox as windows_sandbox
from sentinelx_core.handlers.basic import make_capabilities_handler
from sentinelx_core.mutation_readiness import MutationRuntimeReadiness, probe_mutation_runtime
from sentinelx_core.policy import MutationExecutionPolicy, Policy


ROOT = Path(__file__).resolve().parents[1]


def _features(policy: Policy, tmp_path: Path) -> dict[str, object]:
    handler = make_capabilities_handler(
        policy,
        ops_supported=lambda: ("script_run", "capabilities"),
        upload_base=tmp_path / "uploads",
        config_path=tmp_path / "config.yaml",
    )
    result = asyncio.run(handler({"detail": "full"}))
    return result["execution_features"]


def test_disabled_policy_keeps_both_mutation_features_unavailable(tmp_path: Path) -> None:
    policy = Policy(
        mutation_execution=MutationExecutionPolicy(
            configured=True,
            scoped_mutation_enabled=False,
        ),
        upload_base=tmp_path / "uploads",
    )
    features = _features(policy, tmp_path)
    sandbox = features["host_mutation_sandbox_v1"]
    audit = features["pre_execution_audit_lineage_v1"]
    assert sandbox["available"] is False
    assert sandbox["verified"] is False
    assert "not enabled" in sandbox["reason"]
    assert audit["available"] is False
    assert audit["reason"] == sandbox["reason"]
    assert audit["bound_to"] == "host_mutation_sandbox_v1"


def test_non_windows_platform_remains_fail_closed(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    policy = MutationExecutionPolicy(
        configured=True,
        scoped_mutation_enabled=True,
        workspace_root=workspace,
    )
    monkeypatch.setattr(readiness_module.sys, "platform", "linux")
    result = probe_mutation_runtime(policy, tmp_path / "state", force=True)
    assert result.available is False
    assert result.checks["windows"] is False
    assert "Windows AppContainer" in result.reason


def test_missing_workspace_fails_closed_with_diagnostic_checks(tmp_path: Path, monkeypatch) -> None:
    policy = MutationExecutionPolicy(
        configured=True,
        scoped_mutation_enabled=True,
        workspace_root=tmp_path / "missing-workspace",
    )
    monkeypatch.setattr(readiness_module.sys, "platform", "win32")
    monkeypatch.setattr(
        windows_sandbox,
        "windows_sandbox_primitives_available",
        lambda: (True, "available for test"),
    )
    result = probe_mutation_runtime(policy, tmp_path / "state", force=True)
    assert result.available is False
    assert result.reason == "provider workspace_root is unavailable"
    assert result.checks["windows"] is True
    assert result.checks["policy_enabled"] is True
    assert result.checks["scope_store"] is False


def test_package_version_alone_never_enables_mutation_capabilities(tmp_path: Path, monkeypatch) -> None:
    policy = Policy(
        mutation_execution=MutationExecutionPolicy(
            configured=True,
            scoped_mutation_enabled=True,
            workspace_root=tmp_path / "workspace",
        ),
        upload_base=tmp_path / "uploads",
    )
    forced = MutationRuntimeReadiness(
        False,
        "forced readiness failure",
        {"windows": True, "policy_enabled": True},
    )
    monkeypatch.setattr(basic, "AGENT_VERSION", "99.99.99")
    monkeypatch.setattr(basic, "probe_mutation_runtime", lambda *_args, **_kwargs: forced)
    handler = make_capabilities_handler(
        policy,
        ops_supported=lambda: ("script_run", "capabilities"),
        upload_base=tmp_path / "uploads",
        config_path=tmp_path / "config.yaml",
    )
    result = asyncio.run(handler({"detail": "full"}))
    assert result["version"] == "99.99.99"
    assert result["execution_features"]["host_mutation_sandbox_v1"]["available"] is False
    assert result["execution_features"]["pre_execution_audit_lineage_v1"]["available"] is False
    assert result["execution_features"]["host_mutation_sandbox_v1"]["reason"] == "forced readiness failure"


def test_operator_docs_keep_release_lifecycle_states_distinct() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for state in (
        "source_implemented",
        "release_artifact_built",
        "release_published",
        "release_installed_on_host",
        "runtime_capability_ready",
    ):
        assert state in readme
