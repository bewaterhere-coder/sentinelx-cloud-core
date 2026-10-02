"""Authoritative operation/effect registration for provider-wide repository safety.

The mapping itself remains the dispatch source of truth.  Each registered handler
carries its repository-effect semantics in the same record, so capability/readiness
logic never depends on a second hand-maintained operation list.
"""
from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable, Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any

Handler = Callable[..., Awaitable[dict[str, Any]]]


class OperationExposure(str, Enum):
    MODEL_FACING = "model_facing"
    INTERNAL = "internal"


class RepositoryEffect(str, Enum):
    READ_ONLY = "read_only"
    NON_REPOSITORY_MUTATION = "non_repository_mutation"
    STRUCTURED_MUTATION = "structured_mutation"
    PROCESS_MUTATION = "process_mutation"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class FirewallCoverage(str, Enum):
    NOT_REQUIRED = "not_required"
    PROVEN = "proven"
    UNPROVEN = "unproven"


@dataclass(frozen=True)
class OperationEffectResolution:
    effect: RepositoryEffect
    coverage: FirewallCoverage = FirewallCoverage.NOT_REQUIRED
    selector: str | None = None
    reason: str | None = None


SuboperationClassifier = Callable[[dict[str, Any]], OperationEffectResolution]
EffectInventory = Callable[[], Iterable[OperationEffectResolution]]


@dataclass(frozen=True)
class OperationRegistration:
    handler: Handler
    exposure: OperationExposure
    repository_effect: RepositoryEffect
    firewall_coverage: FirewallCoverage
    classifier: SuboperationClassifier | None = None
    inventory: EffectInventory | None = None


@dataclass(frozen=True)
class OperationRegistryReadiness:
    ready: bool
    reasons: tuple[str, ...]


def _resolution_ready(resolution: OperationEffectResolution) -> bool:
    if resolution.effect in {RepositoryEffect.UNKNOWN, RepositoryEffect.MIXED}:
        return False
    if resolution.effect in {
        RepositoryEffect.STRUCTURED_MUTATION,
        RepositoryEffect.PROCESS_MUTATION,
    }:
        return resolution.coverage is FirewallCoverage.PROVEN
    return True


class OperationRegistry(dict[str, Handler]):
    """Dispatch mapping whose entries own their effect/coverage semantics."""

    def __init__(self) -> None:
        super().__init__()
        self._registrations: dict[str, OperationRegistration] = {}

    def register(
        self,
        name: str,
        handler: Handler,
        *,
        exposure: OperationExposure = OperationExposure.MODEL_FACING,
        repository_effect: RepositoryEffect = RepositoryEffect.UNKNOWN,
        firewall_coverage: FirewallCoverage = FirewallCoverage.UNPROVEN,
        classifier: SuboperationClassifier | None = None,
        inventory: EffectInventory | None = None,
    ) -> None:
        if repository_effect is RepositoryEffect.MIXED and classifier is None:
            raise ValueError(f"mixed operation {name!r} requires a classifier")
        dict.__setitem__(self, name, handler)
        self._registrations[name] = OperationRegistration(
            handler=handler,
            exposure=exposure,
            repository_effect=repository_effect,
            firewall_coverage=firewall_coverage,
            classifier=classifier,
            inventory=inventory,
        )

    def __setitem__(self, name: str, handler: Handler) -> None:
        # Future callers that bypass register() remain dispatchable but are
        # deliberately UNKNOWN for provider-wide readiness rather than silently
        # inheriting a safe effect.
        self.register(name, handler)

    def __delitem__(self, name: str) -> None:
        dict.__delitem__(self, name)
        self._registrations.pop(name, None)

    def registration(self, name: str) -> OperationRegistration | None:
        return self._registrations.get(name)

    def resolve_effect(
        self, name: str, payload: dict[str, Any] | None = None
    ) -> OperationEffectResolution:
        registration = self._registrations.get(name)
        if registration is None:
            return OperationEffectResolution(
                RepositoryEffect.UNKNOWN,
                FirewallCoverage.UNPROVEN,
                selector=name,
                reason="operation_not_registered",
            )
        if registration.repository_effect is not RepositoryEffect.MIXED:
            return OperationEffectResolution(
                registration.repository_effect,
                registration.firewall_coverage,
                selector=name,
            )
        assert registration.classifier is not None
        return registration.classifier(payload or {})

    @property
    def firewall_readiness(self) -> OperationRegistryReadiness:
        reasons: list[str] = []
        for name, registration in self._registrations.items():
            if registration.exposure is OperationExposure.INTERNAL:
                continue
            if registration.repository_effect is RepositoryEffect.MIXED:
                if registration.inventory is None:
                    reasons.append(f"{name}:mixed_effect_inventory_missing")
                    continue
                resolutions = tuple(registration.inventory())
                if not resolutions:
                    reasons.append(f"{name}:mixed_effect_inventory_empty")
                    continue
                for resolution in resolutions:
                    if not _resolution_ready(resolution):
                        suffix = resolution.selector or "unknown"
                        reasons.append(
                            f"{name}/{suffix}:{resolution.reason or resolution.effect.value}"
                        )
                continue
            resolution = OperationEffectResolution(
                registration.repository_effect,
                registration.firewall_coverage,
                selector=name,
            )
            if not _resolution_ready(resolution):
                reasons.append(
                    f"{name}:{resolution.reason or registration.repository_effect.value}"
                )
        return OperationRegistryReadiness(ready=not reasons, reasons=tuple(reasons))


def _script_run_profile(payload: dict[str, Any]) -> tuple[str | None, str | None]:
    """Resolve the bounded script_run profile without treating strings as proof."""
    mutation = payload.get("mutation")
    nested = mutation.get("execution_profile") if isinstance(mutation, dict) else None
    direct = payload.get("execution_profile")
    if nested is not None and direct is not None and nested != direct:
        return None, "conflicting_execution_profile"
    value = nested if nested is not None else direct
    if value is None:
        return None, None
    if not isinstance(value, str) or not value.strip():
        return None, "invalid_execution_profile"
    return value.strip(), None


def make_script_run_effect_classifier(policy: Any) -> SuboperationClassifier:
    """Classify only physical process dispositions already enforced by Core."""
    mutation_policy = policy.mutation_execution

    def classify(payload: dict[str, Any]) -> OperationEffectResolution:
        profile, error = _script_run_profile(payload)
        if error is not None:
            return OperationEffectResolution(
                RepositoryEffect.UNKNOWN,
                FirewallCoverage.UNPROVEN,
                selector="script_run/profile",
                reason=error,
            )
        if profile == "scoped_mutation":
            if mutation_policy.configured and mutation_policy.scoped_mutation_enabled:
                return OperationEffectResolution(
                    RepositoryEffect.PROCESS_MUTATION,
                    FirewallCoverage.PROVEN,
                    selector="scoped_mutation",
                )
            return OperationEffectResolution(
                RepositoryEffect.UNKNOWN,
                FirewallCoverage.UNPROVEN,
                selector="scoped_mutation",
                reason="scoped_mutation_profile_unavailable",
            )
        if profile == "operator_unrestricted":
            if mutation_policy.configured and mutation_policy.operator_unrestricted_enabled:
                return OperationEffectResolution(
                    RepositoryEffect.PROCESS_MUTATION,
                    FirewallCoverage.UNPROVEN,
                    selector="operator_unrestricted",
                    reason="operator_unrestricted_process_uncontained",
                )
            return OperationEffectResolution(
                RepositoryEffect.UNKNOWN,
                FirewallCoverage.UNPROVEN,
                selector="operator_unrestricted",
                reason="operator_unrestricted_disabled",
            )
        if profile is None:
            if mutation_policy.configured:
                return OperationEffectResolution(
                    RepositoryEffect.UNKNOWN,
                    FirewallCoverage.UNPROVEN,
                    selector="missing",
                    reason="execution_profile_required",
                )
            return OperationEffectResolution(
                RepositoryEffect.PROCESS_MUTATION,
                FirewallCoverage.UNPROVEN,
                selector="legacy_unprofiled",
                reason="legacy_unprofiled_process_uncontained",
            )
        return OperationEffectResolution(
            RepositoryEffect.UNKNOWN,
            FirewallCoverage.UNPROVEN,
            selector=profile,
            reason="unknown_script_run_execution_profile",
        )

    return classify


def make_script_run_effect_inventory(policy: Any) -> EffectInventory:
    """Enumerate effective script_run process paths from provider policy."""
    mutation_policy = policy.mutation_execution

    def inventory() -> tuple[OperationEffectResolution, ...]:
        if not mutation_policy.configured:
            return (
                OperationEffectResolution(
                    RepositoryEffect.PROCESS_MUTATION,
                    FirewallCoverage.UNPROVEN,
                    selector="legacy_unprofiled",
                    reason="legacy_unprofiled_process_uncontained",
                ),
            )
        effects: list[OperationEffectResolution] = []
        if mutation_policy.scoped_mutation_enabled:
            effects.append(
                OperationEffectResolution(
                    RepositoryEffect.PROCESS_MUTATION,
                    FirewallCoverage.PROVEN,
                    selector="scoped_mutation",
                )
            )
        if mutation_policy.operator_unrestricted_enabled:
            effects.append(
                OperationEffectResolution(
                    RepositoryEffect.PROCESS_MUTATION,
                    FirewallCoverage.UNPROVEN,
                    selector="operator_unrestricted",
                    reason="operator_unrestricted_process_uncontained",
                )
            )
        if not effects:
            effects.append(
                OperationEffectResolution(
                    RepositoryEffect.UNKNOWN,
                    FirewallCoverage.UNPROVEN,
                    selector="no_effective_profile",
                    reason="script_run_process_profile_unavailable",
                )
            )
        return tuple(effects)

    return inventory


_GIT_EFFECTS: dict[str, OperationEffectResolution] = {
    "diff": OperationEffectResolution(RepositoryEffect.READ_ONLY, selector="diff"),
    "ls_remote": OperationEffectResolution(RepositoryEffect.READ_ONLY, selector="ls_remote"),
    "apply_patch": OperationEffectResolution(
        RepositoryEffect.STRUCTURED_MUTATION,
        FirewallCoverage.PROVEN,
        selector="apply_patch",
    ),
    "fetch": OperationEffectResolution(
        RepositoryEffect.STRUCTURED_MUTATION,
        FirewallCoverage.PROVEN,
        selector="fetch",
    ),
    "clone": OperationEffectResolution(
        RepositoryEffect.STRUCTURED_MUTATION,
        FirewallCoverage.PROVEN,
        selector="clone",
    ),
    # push mutates a remote ref, not the local checkout. Remote publication
    # remains governed by its existing transport/CAS authority.
    "push": OperationEffectResolution(
        RepositoryEffect.NON_REPOSITORY_MUTATION,
        FirewallCoverage.NOT_REQUIRED,
        selector="push",
    ),
}


def classify_git_effect(payload: dict[str, Any]) -> OperationEffectResolution:
    operation = str(payload.get("operation") or "").strip()
    if operation == "apply_patch" and bool(payload.get("dry_run", False)):
        return OperationEffectResolution(RepositoryEffect.READ_ONLY, selector="apply_patch:dry_run")
    return _GIT_EFFECTS.get(
        operation,
        OperationEffectResolution(
            RepositoryEffect.UNKNOWN,
            FirewallCoverage.UNPROVEN,
            selector=operation or "missing",
            reason="unknown_git_selector",
        ),
    )


def git_effect_inventory() -> tuple[OperationEffectResolution, ...]:
    return tuple(_GIT_EFFECTS[name] for name in sorted(_GIT_EFFECTS))


def _configured_local_api_effect(
    endpoint: Any, action: Any, selector: str
) -> OperationEffectResolution:
    # run_as uses a helper process/relay. Operator effect metadata may not
    # downgrade that physical process-producing path to read-only.
    if getattr(endpoint, "run_as", None):
        return OperationEffectResolution(
            RepositoryEffect.PROCESS_MUTATION,
            FirewallCoverage.UNPROVEN,
            selector=selector,
            reason="external_local_api_run_as_unproven",
        )
    raw = getattr(action, "repository_effect", None)
    try:
        effect = RepositoryEffect(raw) if raw is not None else RepositoryEffect.UNKNOWN
    except ValueError:
        effect = RepositoryEffect.UNKNOWN
    if effect in {RepositoryEffect.READ_ONLY, RepositoryEffect.NON_REPOSITORY_MUTATION}:
        coverage = FirewallCoverage.NOT_REQUIRED
    elif effect in {RepositoryEffect.STRUCTURED_MUTATION, RepositoryEffect.PROCESS_MUTATION}:
        # Operator metadata may describe an effect but cannot self-assert that
        # SentinelX physically contains that mutation.
        coverage = FirewallCoverage.UNPROVEN
    else:
        coverage = FirewallCoverage.UNPROVEN
    return OperationEffectResolution(
        effect,
        coverage,
        selector=selector,
        reason="external_local_api_effect_unknown" if effect is RepositoryEffect.UNKNOWN else None,
    )


def _builtin_effect(provider: Any, action: str, selector: str) -> OperationEffectResolution:
    resolver = getattr(provider, "repository_effect", None)
    if not callable(resolver):
        return OperationEffectResolution(
            RepositoryEffect.UNKNOWN,
            FirewallCoverage.UNPROVEN,
            selector=selector,
            reason="builtin_effect_metadata_unavailable",
        )
    try:
        raw = resolver(action)
    except Exception:  # provider-owned metadata must fail closed
        return OperationEffectResolution(
            RepositoryEffect.UNKNOWN,
            FirewallCoverage.UNPROVEN,
            selector=selector,
            reason="builtin_effect_metadata_invalid",
        )
    if isinstance(raw, OperationEffectResolution):
        return OperationEffectResolution(
            raw.effect,
            raw.coverage,
            selector=selector,
            reason=raw.reason,
        )
    return OperationEffectResolution(
        RepositoryEffect.UNKNOWN,
        FirewallCoverage.UNPROVEN,
        selector=selector,
        reason="builtin_effect_metadata_invalid",
    )


def make_local_api_effect_classifier(
    policy: Any,
    *,
    builtin_providers: Mapping[str, Any] | None = None,
) -> SuboperationClassifier:
    builtins = dict(builtin_providers or {})

    def classify(payload: dict[str, Any]) -> OperationEffectResolution:
        operation = str(payload.get("operation") or "").strip()
        if operation in {"list", "describe"}:
            return OperationEffectResolution(RepositoryEffect.READ_ONLY, selector=operation)
        if operation != "call":
            return OperationEffectResolution(
                RepositoryEffect.UNKNOWN,
                FirewallCoverage.UNPROVEN,
                selector=operation or "missing",
                reason="unknown_local_api_operation",
            )
        endpoint_name = str(payload.get("endpoint") or "").strip()
        action_name = str(payload.get("action") or "").strip()
        selector = f"{endpoint_name or 'missing'}/{action_name or 'missing'}"
        endpoint = policy.local_apis.get(endpoint_name)
        if endpoint is not None:
            action = endpoint.actions.get(action_name)
            if action is None:
                return OperationEffectResolution(
                    RepositoryEffect.UNKNOWN,
                    FirewallCoverage.UNPROVEN,
                    selector=selector,
                    reason="configured_local_api_action_unknown",
                )
            return _configured_local_api_effect(endpoint, action, selector)
        provider = builtins.get(endpoint_name)
        if provider is not None and endpoint_name not in policy.local_apis:
            return _builtin_effect(provider, action_name, selector)
        return OperationEffectResolution(
            RepositoryEffect.UNKNOWN,
            FirewallCoverage.UNPROVEN,
            selector=selector,
            reason="local_api_endpoint_unknown",
        )

    return classify


def make_local_api_effect_inventory(
    policy: Any,
    *,
    builtin_providers: Mapping[str, Any] | None = None,
) -> EffectInventory:
    builtins = dict(builtin_providers or {})

    def inventory() -> tuple[OperationEffectResolution, ...]:
        effects: list[OperationEffectResolution] = [
            OperationEffectResolution(RepositoryEffect.READ_ONLY, selector="list"),
            OperationEffectResolution(RepositoryEffect.READ_ONLY, selector="describe"),
        ]
        for endpoint_name, endpoint in sorted(policy.local_apis.items()):
            for action_name, action in sorted(endpoint.actions.items()):
                effects.append(
                    _configured_local_api_effect(
                        endpoint, action, f"{endpoint_name}/{action_name}"
                    )
                )
        for endpoint_name, provider in sorted(builtins.items()):
            if endpoint_name in policy.local_apis:
                continue
            actions = getattr(provider, "available_actions", None)
            if not callable(actions):
                effects.append(
                    OperationEffectResolution(
                        RepositoryEffect.UNKNOWN,
                        FirewallCoverage.UNPROVEN,
                        selector=f"{endpoint_name}/unknown",
                        reason="builtin_action_inventory_unavailable",
                    )
                )
                continue
            for action_name in actions():
                effects.append(
                    _builtin_effect(
                        provider, str(action_name), f"{endpoint_name}/{action_name}"
                    )
                )
        return tuple(effects)

    return inventory


def build_effect_registry(
    dispatch: Mapping[str, Handler],
    policy: Any,
    *,
    builtin_local_api_providers: Mapping[str, Any] | None = None,
) -> OperationRegistry:
    """Bind fail-closed effect metadata to the *effective* dispatch surface.

    The dispatch mapping remains authoritative: disabled operations are already
    absent, internal entries are identified here, and any present-but-unknown
    future operation is registered as UNKNOWN rather than being omitted.  This
    is an effect projection over actual registry keys, not a second dispatch or
    exposure list.
    """
    registry = OperationRegistry()
    for name, handler in dispatch.items():
        if name in {"file_export_init", "file_export_chunk", "file_export_complete"}:
            registry.register(
                name,
                handler,
                exposure=OperationExposure.INTERNAL,
                repository_effect=RepositoryEffect.READ_ONLY,
                firewall_coverage=FirewallCoverage.NOT_REQUIRED,
            )
        elif name in {
            "ping",
            "capabilities",
            "help",
            "state",
            "read",
            "list",
            "search",
            "project_snapshot",
            "read_audit",
        }:
            registry.register(
                name,
                handler,
                repository_effect=RepositoryEffect.READ_ONLY,
                firewall_coverage=FirewallCoverage.NOT_REQUIRED,
            )
        elif name in {"service", "restart"}:
            registry.register(
                name,
                handler,
                repository_effect=RepositoryEffect.NON_REPOSITORY_MUTATION,
                firewall_coverage=FirewallCoverage.NOT_REQUIRED,
            )
        elif name in {
            "edit",
            "edit_upload_init",
            "edit_upload_file",
            "edit_upload_complete",
            "move",
            "copy",
            "delete",
            "chmod",
            "chown",
            "upload_file",
            "upload_init",
            "upload_chunk",
            "upload_complete",
        }:
            registry.register(
                name,
                handler,
                repository_effect=RepositoryEffect.STRUCTURED_MUTATION,
                firewall_coverage=FirewallCoverage.PROVEN,
            )
        elif name == "exec":
            # Generic exec has no physical repository exclusion boundary. It
            # remains available for compatibility, but its presence prevents
            # provider-wide firewall readiness from becoming true.
            registry.register(
                name,
                handler,
                repository_effect=RepositoryEffect.PROCESS_MUTATION,
                firewall_coverage=FirewallCoverage.UNPROVEN,
            )
        elif name == "script_run":
            # script_run is mixed by execution profile. Only the existing
            # scoped_mutation path has physical sandbox/audit containment;
            # legacy and operator-unrestricted paths remain fail-closed for
            # provider-wide readiness.
            registry.register(
                name,
                handler,
                repository_effect=RepositoryEffect.MIXED,
                firewall_coverage=FirewallCoverage.UNPROVEN,
                classifier=make_script_run_effect_classifier(policy),
                inventory=make_script_run_effect_inventory(policy),
            )
        elif name == "git":
            registry.register(
                name,
                handler,
                repository_effect=RepositoryEffect.MIXED,
                firewall_coverage=FirewallCoverage.UNPROVEN,
                classifier=classify_git_effect,
                inventory=git_effect_inventory,
            )
        elif name == "local_api":
            registry.register(
                name,
                handler,
                repository_effect=RepositoryEffect.MIXED,
                firewall_coverage=FirewallCoverage.UNPROVEN,
                classifier=make_local_api_effect_classifier(
                    policy, builtin_providers=builtin_local_api_providers
                ),
                inventory=make_local_api_effect_inventory(
                    policy, builtin_providers=builtin_local_api_providers
                ),
            )
        else:
            # Includes future model-facing operations and PR-007-only surfaces
            # until their owning provider supplies an explicit composition.
            registry.register(name, handler)
    return registry
