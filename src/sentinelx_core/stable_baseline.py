"""Pure Stable Baseline V1 evidence composition.

This module does not probe the Host, cache readiness, mutate policy, or grant
execution authority.  It classifies the existing sanitized capability
projections using the finite ``windows_dev_v1`` predicates.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal

BASELINE_ID = "windows_dev_v1"
FEATURE_ID = "host_runtime.stable_baseline_v1"

MUTATION = "host_mutation_sandbox_v1"
AUDIT = "pre_execution_audit_lineage_v1"
NODE_NPM = "host_runtime.scoped_verification_node_npm_v1"
FIREWALL = "canonical_repository_mutation_firewall_v1"
DIRECT_CODEX = "development_host.direct_codex_v1"
WINDOWS = "host_platform.windows_v1"

MANDATORY_CHECKS = (MUTATION, AUDIT, NODE_NPM, FIREWALL, DIRECT_CODEX, WINDOWS)

CheckStatus = Literal["verified", "unavailable", "unverified"]

_MUTATION_CHECKS = (
    "runtime_read_execute",
    "terminal_non_active",
    "residual_authority_absent",
)
_PENDING_DIRECT_REASONS = frozenset(
    {
        "direct_codex_containment_unproven",
        "direct_codex_real_sandbox_setup_unproven",
    }
)
_DIRECT_POLICY_FAILURES = frozenset(
    {
        "direct_codex_disabled",
        "direct_codex_not_configured",
        "direct_codex_workspace_root_missing",
        "direct_codex_unsupported_platform",
        "local_api_disabled",
    }
)


def _mapping(value: Any) -> Mapping[str, Any] | None:
    return value if isinstance(value, Mapping) else None


def _strings(value: Any) -> tuple[str, ...] | None:
    if not isinstance(value, (list, tuple)) or any(not isinstance(item, str) for item in value):
        return None
    return tuple(value)


def _physical_feature(
    feature: Any,
    *,
    required_scalars: Mapping[str, Any],
    required_checks: tuple[str, ...],
) -> tuple[CheckStatus, str]:
    item = _mapping(feature)
    if item is None:
        return "unverified", "mandatory_projection_absent_or_malformed"
    checks = _mapping(item.get("checks"))
    verified = bool(
        item.get("available") is True
        and item.get("verified") is True
        and all(item.get(key) == value for key, value in required_scalars.items())
        and checks is not None
        and all(checks.get(key) is True for key in required_checks)
    )
    if verified:
        return "verified", "verified"

    # Existing physical readiness features return the complete boolean check
    # inventory plus a reason on a concrete failed/disabled probe.  Missing or
    # malformed aggregate evidence remains unknown instead of manufacturing a
    # defect from an invalid document.
    concrete = bool(
        item.get("available") is False
        and item.get("verified") is False
        and isinstance(item.get("reason"), str)
        and item.get("reason")
        and checks is not None
        and checks
        and all(isinstance(value, bool) for value in checks.values())
        and all(isinstance(checks.get(key), bool) for key in required_checks)
    )
    return (
        ("unavailable", str(item["reason"]))
        if concrete
        else ("unverified", "mandatory_projection_absent_or_malformed")
    )


def _firewall(feature: Any, direct_status: CheckStatus) -> tuple[CheckStatus, str]:
    item = _mapping(feature)
    if item is None:
        return "unverified", "mandatory_projection_absent_or_malformed"
    reasons = _strings(item.get("uncovered_classes"))
    if (
        item.get("available") is True
        and item.get("verified") is True
        and item.get("inventory_ready") is True
        and item.get("effective_surface_ready") is True
        and item.get("platform_supported") is True
        and reasons == ()
    ):
        return "verified", "verified"
    if reasons is None:
        return "unverified", "mandatory_projection_absent_or_malformed"
    if reasons and set(reasons).issubset(_PENDING_DIRECT_REASONS) and direct_status == "unverified":
        return "unverified", "mandatory_direct_codex_proof_pending"
    if reasons and all(isinstance(item.get(key), bool) for key in (
        "available", "verified", "inventory_ready", "effective_surface_ready", "platform_supported"
    )):
        return "unavailable", reasons[0]
    return "unverified", "mandatory_projection_absent_or_malformed"


def _direct_codex(feature: Any) -> tuple[CheckStatus, str, dict[str, Any] | None]:
    item = _mapping(feature)
    if item is None:
        return "unverified", "mandatory_projection_absent_or_malformed", None
    proof = _mapping(item.get("proof"))
    transport = _mapping(item.get("transport_context"))
    sanitized_transport = None
    if transport is not None:
        sanitized_transport = {
            "kind": transport.get("kind"),
            "probe_attempted": transport.get("probe_attempted"),
            "verified": transport.get("verified"),
            "non_interactive": transport.get("non_interactive"),
            "credential_material_exposed": transport.get("credential_material_exposed"),
        }
    transport_verified = bool(
        transport is not None
        and transport.get("kind") == "user_scoped_git_v1"
        and transport.get("probe_attempted") is True
        and transport.get("verified") is True
        and transport.get("non_interactive") is True
        and transport.get("credential_material_exposed") is False
    )
    proof_verified = bool(
        proof is not None
        and proof.get("attempted") is True
        and proof.get("disposition") == "verified"
    )
    if item.get("available") is True and item.get("verified") is True and proof_verified and transport_verified:
        return "verified", "verified", sanitized_transport

    reasons = _strings(item.get("uncovered_classes"))
    reason_set = set(reasons or ())
    if reason_set & _DIRECT_POLICY_FAILURES:
        return "unavailable", min(reason_set & _DIRECT_POLICY_FAILURES), sanitized_transport
    if proof is not None and proof.get("attempted") is True and proof.get("disposition") == "failed":
        failure = proof.get("failure_class")
        return "unavailable", str(failure or "direct_codex_physical_proof_failed"), sanitized_transport
    if transport is not None and transport.get("probe_attempted") is True and transport.get("verified") is False:
        failure = transport.get("failure_class")
        return "unavailable", str(failure or "direct_codex_git_context_probe_failed"), sanitized_transport
    return "unverified", "direct_codex_physical_proof_pending", sanitized_transport


def _platform(platform_name: Any) -> tuple[CheckStatus, str]:
    if platform_name == "Windows":
        return "verified", "verified"
    if isinstance(platform_name, str) and platform_name:
        return "unavailable", "unsupported_platform"
    return "unverified", "platform_evidence_absent_or_malformed"


def compose_stable_baseline(
    execution_features: Mapping[str, Any],
    *,
    platform_name: str | None,
) -> dict[str, Any]:
    """Classify sanitized live evidence without performing I/O or mutation."""
    features = execution_features if isinstance(execution_features, Mapping) else {}
    direct_status, direct_reason, transport = _direct_codex(features.get(DIRECT_CODEX))
    resolved: dict[str, tuple[CheckStatus, str]] = {
        MUTATION: _physical_feature(
            features.get(MUTATION),
            required_scalars={"platform": "windows_appcontainer_v1", "self_check": "verified"},
            required_checks=_MUTATION_CHECKS,
        ),
        AUDIT: _physical_feature(
            features.get(AUDIT),
            required_scalars={
                "platform": "windows_appcontainer_v1",
                "self_check": "verified",
                "bound_to": MUTATION,
            },
            required_checks=_MUTATION_CHECKS,
        ),
        NODE_NPM: _physical_feature(
            features.get(NODE_NPM),
            required_scalars={
                "platform": "windows_appcontainer_v1",
                "self_check": "verified",
                "profile_id": "node_npm",
                "toolchain_kind": "node_npm_v1",
            },
            required_checks=("terminal_non_active", "transient_toolchain_authority_absent"),
        ),
        DIRECT_CODEX: (direct_status, direct_reason),
        WINDOWS: _platform(platform_name),
    }
    # A toolchain digest is a mandatory non-empty identity, not merely a key.
    node = _mapping(features.get(NODE_NPM))
    if resolved[NODE_NPM][0] == "verified" and not (
        node is not None and isinstance(node.get("toolchain_digest"), str) and node["toolchain_digest"]
    ):
        resolved[NODE_NPM] = ("unverified", "mandatory_projection_absent_or_malformed")
    resolved[FIREWALL] = _firewall(features.get(FIREWALL), direct_status)

    mandatory: dict[str, dict[str, Any]] = {}
    blockers: list[dict[str, str]] = []
    verification_required: list[dict[str, str]] = []
    for check_id in MANDATORY_CHECKS:
        status, reason = resolved[check_id]
        entry: dict[str, Any] = {"status": status}
        if reason != "verified":
            entry["reason"] = reason
        if check_id == DIRECT_CODEX and transport is not None:
            entry["transport_context"] = transport
        mandatory[check_id] = entry
        finding = {"check": check_id, "reason": reason}
        if status == "unavailable":
            blockers.append(finding)
        elif status == "unverified":
            verification_required.append(finding)

    status = "NotReady" if blockers else ("Unverified" if verification_required else "Ready")
    return {
        "available": True,
        "verified": status == "Ready",
        "status": status,
        "baseline_id": BASELINE_ID,
        "mandatory_checks": mandatory,
        "blockers": blockers,
        "verification_required": verification_required,
        "backlog_relevant": [],
    }
