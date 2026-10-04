"""Provider-owned canonical repository inventory admission.

S01 deliberately stops at classification. Handler integration, process fail-closed
semantics and capability advertisement belong to later PR-010 slices.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from sentinelx_core.executor import HandlerError
from sentinelx_core.policy import MutationExecutionPolicy


class CanonicalRepositoryFirewallDisposition(str, Enum):
    """Stable provider-level classification outcomes."""

    ALLOWED_NON_CANONICAL_TARGET = "AllowedNonCanonicalTarget"
    CANONICAL_REPOSITORY_MUTATION_BLOCKED = "CanonicalRepositoryMutationBlocked"
    HOST_CANONICAL_MUTATION_FIREWALL_INDETERMINATE = (
        "HostCanonicalMutationFirewallIndeterminate"
    )


@dataclass(frozen=True)
class CanonicalRepositoryFirewallDecision:
    disposition: CanonicalRepositoryFirewallDisposition
    repository_identity: str | None = None
    reason: str | None = None

    @property
    def allowed(self) -> bool:
        return self.disposition is CanonicalRepositoryFirewallDisposition.ALLOWED_NON_CANONICAL_TARGET


@dataclass(frozen=True)
class CanonicalRepositoryFirewallReadiness:
    """Inventory/classifier readiness, not provider-wide capability readiness."""

    ready: bool
    enabled: bool
    inventory_valid: bool
    inventory_count: int
    reasons: tuple[str, ...]


class CanonicalRepositoryFirewall:
    """Classify concrete Host mutation targets against Host-owned source roots."""

    def __init__(self, policy: MutationExecutionPolicy) -> None:
        self._policy = policy

    @property
    def readiness(self) -> CanonicalRepositoryFirewallReadiness:
        return CanonicalRepositoryFirewallReadiness(
            ready=self._policy.canonical_repository_inventory_ready,
            enabled=self._policy.canonical_repository_firewall_enabled,
            inventory_valid=self._policy.canonical_repository_inventory_valid,
            inventory_count=len(self._policy.canonical_repositories),
            reasons=self._policy.canonical_repository_inventory_readiness_reasons,
        )

    def classify_write_target(self, target: str | Path) -> CanonicalRepositoryFirewallDecision:
        """Classify one concrete material mutation target before side effects.

        Caller-supplied repository identity, branch names, cwd or file_ops access
        never participate. Only the Host-owned inventory loaded into the policy
        can establish canonical protection.
        """
        readiness = self.readiness
        if not readiness.ready:
            reason = readiness.reasons[0] if readiness.reasons else "inventory_not_ready"
            return CanonicalRepositoryFirewallDecision(
                CanonicalRepositoryFirewallDisposition.HOST_CANONICAL_MUTATION_FIREWALL_INDETERMINATE,
                reason=reason,
            )

        try:
            candidate = Path(target).expanduser()
        except (TypeError, ValueError):
            return self._indeterminate("target_invalid")
        if not candidate.is_absolute():
            return self._indeterminate("target_not_absolute")

        try:
            candidate = candidate.resolve(strict=False)
        except (OSError, RuntimeError, ValueError):
            return self._indeterminate("target_canonicalization_failed")

        for repository in self._policy.canonical_repositories:
            root = repository.root
            # An operation targeting the checkout, one of its descendants, or
            # an ancestor whose mutation can remove/rename the checkout intersects
            # the protected source role. Structured handlers may later pass the
            # exact endpoint they mutate; this central seam stays conservative.
            if (
                candidate == root
                or candidate.is_relative_to(root)
                or root.is_relative_to(candidate)
            ):
                return CanonicalRepositoryFirewallDecision(
                    CanonicalRepositoryFirewallDisposition.CANONICAL_REPOSITORY_MUTATION_BLOCKED,
                    repository_identity=repository.repository_identity,
                    reason="target_intersects_canonical_repository",
                )

        return CanonicalRepositoryFirewallDecision(
            CanonicalRepositoryFirewallDisposition.ALLOWED_NON_CANONICAL_TARGET,
            reason="target_outside_canonical_inventory",
        )

    @staticmethod
    def _indeterminate(reason: str) -> CanonicalRepositoryFirewallDecision:
        return CanonicalRepositoryFirewallDecision(
            CanonicalRepositoryFirewallDisposition.HOST_CANONICAL_MUTATION_FIREWALL_INDETERMINATE,
            reason=reason,
        )


def enforce_material_write_target(
    policy: MutationExecutionPolicy,
    target: str | Path,
    *,
    operation: str,
    label: str = "path",
) -> Path:
    """Apply the canonical-repository firewall before a material write.

    A disabled firewall preserves legacy behavior. Once explicitly enabled,
    invalid inventory/indeterminate classification fails closed just like a
    positive canonical-root match. Callers must invoke this before backups,
    overwrite/delete, metadata changes, patch application, or finalization.
    """
    candidate = Path(target).expanduser().resolve(strict=False)
    if not policy.canonical_repository_firewall_enabled:
        return candidate

    decision = CanonicalRepositoryFirewall(policy).classify_write_target(candidate)
    if decision.allowed:
        return candidate

    details = {
        "operation": operation,
        "target_label": label,
        "disposition": decision.disposition.value,
        "reason": decision.reason,
    }
    if decision.repository_identity:
        details["repository_identity"] = decision.repository_identity

    if (
        decision.disposition
        is CanonicalRepositoryFirewallDisposition.CANONICAL_REPOSITORY_MUTATION_BLOCKED
    ):
        raise HandlerError(
            CanonicalRepositoryFirewallDisposition.CANONICAL_REPOSITORY_MUTATION_BLOCKED.value,
            f"{operation} is blocked because {label} intersects a canonical repository",
            details=details,
        )
    raise HandlerError(
        CanonicalRepositoryFirewallDisposition.HOST_CANONICAL_MUTATION_FIREWALL_INDETERMINATE.value,
        f"{operation} cannot prove that {label} is outside the canonical repository inventory",
        details=details,
    )
