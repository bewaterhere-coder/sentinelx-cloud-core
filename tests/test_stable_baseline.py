from __future__ import annotations

from copy import deepcopy

import pytest

from sentinelx_core.stable_baseline import (
    AUDIT,
    DIRECT_CODEX,
    FIREWALL,
    MUTATION,
    NODE_NPM,
    WINDOWS,
    compose_stable_baseline,
)


def _features() -> dict[str, object]:
    mutation = {
        "available": True,
        "verified": True,
        "platform": "windows_appcontainer_v1",
        "self_check": "verified",
        "reason": "physical probe passed",
        "checks": {
            "runtime_read_execute": True,
            "terminal_non_active": True,
            "residual_authority_absent": True,
        },
    }
    return {
        MUTATION: mutation,
        AUDIT: {**deepcopy(mutation), "bound_to": MUTATION},
        NODE_NPM: {
            "available": True,
            "verified": True,
            "platform": "windows_appcontainer_v1",
            "self_check": "verified",
            "profile_id": "node_npm",
            "toolchain_kind": "node_npm_v1",
            "toolchain_digest": "a" * 64,
            "checks": {
                "terminal_non_active": True,
                "transient_toolchain_authority_absent": True,
            },
        },
        FIREWALL: {
            "available": True,
            "verified": True,
            "inventory_ready": True,
            "effective_surface_ready": True,
            "platform_supported": True,
            "uncovered_classes": [],
        },
        DIRECT_CODEX: {
            "available": True,
            "verified": True,
            "reason": None,
            "uncovered_classes": [],
            "proof": {"attempted": True, "disposition": "verified"},
            "transport_context": {
                "kind": "user_scoped_git_v1",
                "probe_attempted": True,
                "verified": True,
                "non_interactive": True,
                "credential_material_exposed": False,
            },
        },
        # Explicitly non-mandatory for the direct/codex baseline.
        "host_runtime.git_execution_context_v1": {"available": False},
    }


def _compose(features: dict[str, object] | None = None) -> dict[str, object]:
    return compose_stable_baseline(features or _features(), platform_name="Windows")


def _status(result: dict[str, object], check: str) -> str:
    return result["mandatory_checks"][check]["status"]  # type: ignore[index]


def test_all_frozen_predicates_verified_is_ready() -> None:
    result = _compose()
    assert result["status"] == "Ready"
    assert result["verified"] is True
    assert result["blockers"] == []
    assert result["verification_required"] == []
    assert all(_status(result, check) == "verified" for check in (
        MUTATION, AUDIT, NODE_NPM, FIREWALL, DIRECT_CODEX, WINDOWS
    ))


@pytest.mark.parametrize("value", [None, "invalid", {"available": True}])
def test_absent_or_malformed_mandatory_projection_is_unverified(value: object) -> None:
    features = _features()
    if value is None:
        features.pop(MUTATION)
    else:
        features[MUTATION] = value
    result = _compose(features)
    assert result["status"] == "Unverified"
    assert _status(result, MUTATION) == "unverified"


def test_mutation_concrete_physical_failure_is_not_ready() -> None:
    features = _features()
    features[MUTATION] = {
        "available": False,
        "verified": False,
        "reason": "AppContainer physical probe failed",
        "checks": {
            "runtime_read_execute": False,
            "terminal_non_active": False,
            "residual_authority_absent": False,
        },
    }
    result = _compose(features)
    assert result["status"] == "NotReady"
    assert _status(result, MUTATION) == "unavailable"


def test_node_profile_explicitly_absent_is_not_ready_but_missing_aggregate_is_unknown() -> None:
    features = _features()
    features[NODE_NPM] = {
        "available": False,
        "verified": False,
        "reason": "node_npm profile is not configured",
        "checks": {
            "profile_configured": False,
            "terminal_non_active": False,
            "transient_toolchain_authority_absent": False,
        },
    }
    assert _status(_compose(features), NODE_NPM) == "unavailable"
    features.pop(NODE_NPM)
    assert _status(_compose(features), NODE_NPM) == "unverified"


def test_direct_codex_not_attempted_is_unverified_and_failed_attempt_is_not_ready() -> None:
    features = _features()
    direct = features[DIRECT_CODEX]
    assert isinstance(direct, dict)
    direct.update(
        available=False,
        verified=False,
        reason="direct_codex_containment_unproven",
        uncovered_classes=["direct_codex_containment_unproven"],
        proof={"attempted": False, "disposition": "not_attempted"},
    )
    assert _status(_compose(features), DIRECT_CODEX) == "unverified"
    direct["proof"] = {
        "attempted": True,
        "disposition": "failed",
        "failure_class": "direct_codex_real_sandbox_setup_unproven",
    }
    assert _status(_compose(features), DIRECT_CODEX) == "unavailable"


def test_explicitly_disabled_direct_codex_is_not_ready() -> None:
    features = _features()
    features[DIRECT_CODEX] = {
        "available": False,
        "verified": False,
        "uncovered_classes": ["direct_codex_disabled"],
        "proof": {"attempted": False, "disposition": "not_attempted"},
        "transport_context": {
            "kind": "user_scoped_git_v1",
            "probe_attempted": False,
            "verified": False,
            "non_interactive": True,
            "credential_material_exposed": False,
        },
    }
    assert _status(_compose(features), DIRECT_CODEX) == "unavailable"


def test_git_context_pending_is_unverified_and_attempted_failure_is_not_ready() -> None:
    features = _features()
    direct = features[DIRECT_CODEX]
    assert isinstance(direct, dict)
    direct["available"] = False
    direct["verified"] = False
    direct["transport_context"] = {
        "kind": "user_scoped_git_v1",
        "probe_attempted": False,
        "verified": False,
        "non_interactive": True,
        "credential_material_exposed": False,
    }
    assert _status(_compose(features), DIRECT_CODEX) == "unverified"
    direct["transport_context"] = {
        "kind": "user_scoped_git_v1",
        "probe_attempted": True,
        "verified": False,
        "non_interactive": True,
        "credential_material_exposed": False,
        "failure_class": "direct_codex_git_context_unavailable",
    }
    assert _status(_compose(features), DIRECT_CODEX) == "unavailable"


def test_generic_git_and_optional_features_do_not_change_ready() -> None:
    features = _features()
    features["host_runtime.git_execution_context_v1"] = {"available": False}
    features["optional.provider"] = {"available": False, "reason": "broken"}
    assert _compose(features)["status"] == "Ready"


def test_firewall_pending_on_direct_is_unverified_but_uncovered_surface_blocks() -> None:
    features = _features()
    direct = features[DIRECT_CODEX]
    assert isinstance(direct, dict)
    direct.update(
        available=False,
        verified=False,
        proof={"attempted": False, "disposition": "not_attempted"},
    )
    features[FIREWALL] = {
        "available": False,
        "verified": False,
        "inventory_ready": True,
        "effective_surface_ready": False,
        "platform_supported": True,
        "uncovered_classes": ["direct_codex_containment_unproven"],
    }
    assert _status(_compose(features), FIREWALL) == "unverified"
    features[FIREWALL]["uncovered_classes"] = ["future_repository_tool:unknown"]  # type: ignore[index]
    assert _status(_compose(features), FIREWALL) == "unavailable"


def test_composer_is_pure_and_projects_no_provider_private_material() -> None:
    features = _features()
    direct = features[DIRECT_CODEX]
    assert isinstance(direct, dict)
    direct["transport_context"]["raw_path"] = r"C:\\Users\\secret"  # type: ignore[index]
    direct["transport_context"]["credential"] = "token"  # type: ignore[index]
    before = deepcopy(features)
    result = _compose(features)
    assert features == before
    rendered = repr(result)
    assert "raw_path" not in rendered
    assert "C:\\Users\\secret" not in rendered
    assert "credential'" not in rendered
    assert "token" not in rendered


def test_non_windows_is_a_concrete_baseline_blocker() -> None:
    result = compose_stable_baseline(_features(), platform_name="Linux")
    assert result["status"] == "NotReady"
    assert _status(result, WINDOWS) == "unavailable"
