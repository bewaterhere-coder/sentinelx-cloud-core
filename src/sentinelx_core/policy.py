"""Policy: allowlist + service registry + paths, loaded from /etc/sentinelx/config.yaml.

This is the ONLY place that knows about per-host configuration. Handlers consult
the policy to decide whether a command/service is allowed; they do not hardcode
anything site-specific.
"""

from __future__ import annotations

import logging
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from sentinelx_core import platform_guidance as _pg

logger = logging.getLogger(__name__)

# Candidates for upload_base when the config does not name one, best first.
# /var/lib is where the service actually keeps its state on current installs;
# /home/sentinelx/uploads is kept for legacy hosts that still use it.
_UPLOAD_BASE_CANDIDATES = (
    Path("/var/lib/sentinelx/uploads"),
    Path("/home/sentinelx/uploads"),
)


def _is_usable_dir(path: Path) -> bool:
    """True if `path` is a writable directory, or can be created in one."""
    try:
        if path.is_dir():
            return os.access(path, os.W_OK)
        parent = path.parent
        return parent.is_dir() and os.access(parent, os.W_OK)
    except OSError:
        return False


def default_upload_base() -> Path:
    """First writable candidate, else a directory in the system temp space.

    Never raises and creates nothing: callers (see staging.py) create the
    directory when they need it, and fall back again at that point if the
    filesystem has changed underneath.
    """
    for candidate in _UPLOAD_BASE_CANDIDATES:
        if _is_usable_dir(candidate):
            return candidate
    return Path(tempfile.gettempdir()) / "sentinelx-uploads"



@dataclass(frozen=True)
class ServiceSpec:
    """Allowed actions for a systemd service."""
    unit: str
    actions: tuple[str, ...]
    requires_sudo: bool = True
    description: str = ""
    # macOS launchd domain for this service ("system" for a LaunchDaemon, or
    # "gui/<uid>" for a per-user LaunchAgent). Ignored on Linux (systemd).
    domain: str = "system"
    # Windows backend: "service" (default; SCM/WinSW via Get-Service / net) or
    # "task" (a per-user Scheduled Task via schtasks -- the no-admin user-mode
    # install). Ignored on Linux/macOS.
    backend: str = "service"


@dataclass(frozen=True)
class LocationSpec:
    """A known path on this host."""
    path: str
    description: str = ""


# Access levels for a file_ops path entry.
#
#   "r"  -> read-only primitives (read / list / search). This is the
#           legacy behaviour and the safe default: an entry whose access
#           level is missing or unrecognized is treated as "r".
#   "rw" -> everything "r" allows PLUS the mutating ops (edit, move,
#           copy, delete, chmod, chown). A path must be EXPLICITLY
#           declared "rw" for any mutation to be permitted there.
FILE_OPS_ACCESS_LEVELS = ("r", "rw")


@dataclass(frozen=True)
class FileOpsPath:
    """One entry in the unified file_ops path allowlist.

    `path` is the directory the operator chose to expose. `access` is
    "r" (read/list/search only) or "rw" (also edit + destructive ops).

    The security boundary is enforced by Policy.resolve_path(): a path
    is canonicalized (symlinks resolved) BEFORE the prefix check, so a
    symlink escaping to /etc cannot bypass an /home-only allowlist, and
    `../` traversal is defeated by the same resolve(). need_write=True
    additionally requires access == "rw".
    """
    path: str
    access: str = "r"

    def __post_init__(self) -> None:
        # Normalize unknown / missing access to the most restrictive
        # level. We never silently grant write: an operator typo like
        # `access: readwrite` degrades to "r", not "rw".
        if self.access not in FILE_OPS_ACCESS_LEVELS:
            object.__setattr__(self, "access", "r")


def _canonical_host_root(value: Any, field_name: str) -> Path:
    """Normalize one host-authoritative absolute root without creating it."""
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"mutation_execution.{field_name} must not be empty")
    root = Path(text).expanduser()
    if not root.is_absolute():
        raise ValueError(f"mutation_execution.{field_name} must be an absolute path")
    try:
        return root.resolve(strict=False)
    except (OSError, RuntimeError) as exc:
        raise ValueError(
            f"mutation_execution.{field_name} cannot be canonicalized: {exc}"
        ) from exc


def _canonical_host_roots(value: Any, field_name: str) -> tuple[Path, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes)) or not isinstance(value, (list, tuple)):
        raise ValueError(f"mutation_execution.{field_name} must be a list of absolute paths")
    roots = {_canonical_host_root(item, field_name) for item in value}
    return tuple(sorted(roots, key=lambda item: str(item).casefold()))


def _paths_overlap(left: Path, right: Path) -> bool:
    return left == right or left.is_relative_to(right) or right.is_relative_to(left)


def _canonical_repository_identity(value: Any, field_name: str) -> str:
    """Normalize repository identity without retaining credentials."""
    if not isinstance(value, dict):
        raise ValueError(f"mutation_execution.{field_name}.repository must be a mapping")

    vcs = str(value.get("vcs") or "").strip().lower()
    authority = str(value.get("authority") or "").strip().lower().replace("\\", "/")
    path = str(value.get("path") or "").strip().replace("\\", "/").strip("/")

    if "://" in authority:
        authority = authority.split("://", 1)[1]
    authority = authority.rsplit("@", 1)[-1].split("/", 1)[0]
    if authority.startswith("["):
        # Preserve bracketed IPv6 authority without a port if one was provided.
        end = authority.find("]")
        authority = authority[: end + 1] if end >= 0 else authority
    elif ":" in authority:
        authority = authority.split(":", 1)[0]

    if path.lower().endswith(".git"):
        path = path[:-4]
    path_parts = tuple(part for part in path.split("/") if part)
    if any(part in {".", ".."} for part in path_parts):
        raise ValueError(
            f"mutation_execution.{field_name}.repository.path contains traversal segments"
        )
    path = "/".join(path_parts)

    if not vcs or not authority or not path:
        raise ValueError(
            f"mutation_execution.{field_name}.repository requires vcs, authority and path"
        )
    return f"{vcs}://{authority}/{path}"


@dataclass(frozen=True)
class CanonicalRepositorySpec:
    """One Host-authoritative canonical source checkout."""

    root: Path
    repository_identity: str
    canonical_branch: str | None = None
    provenance: str = "operator_config"


def _canonical_repository_inventory(
    value: Any,
    *,
    workspace_root: Path | None,
) -> tuple[tuple[CanonicalRepositorySpec, ...], bool, tuple[str, ...]]:
    """Parse canonical source roots while keeping diagnostics path-free."""
    if value is None:
        return (), True, ()
    if isinstance(value, (str, bytes)) or not isinstance(value, (list, tuple)):
        return (), False, ("canonical_repository_inventory_not_list",)

    specs: list[CanonicalRepositorySpec] = []
    diagnostics: list[str] = []
    seen_roots: set[str] = set()

    for index, entry in enumerate(value):
        field_name = f"canonical_repositories[{index}]"
        if not isinstance(entry, dict):
            diagnostics.append("canonical_repository_entry_not_mapping")
            continue
        try:
            root = _canonical_host_root(entry.get("root"), f"{field_name}.root")
            repository_identity = _canonical_repository_identity(
                entry.get("repository"), field_name
            )
        except ValueError:
            diagnostics.append("canonical_repository_entry_invalid")
            continue

        root_key = str(root).casefold()
        if root_key in seen_roots:
            diagnostics.append("canonical_repository_duplicate_root")
        seen_roots.add(root_key)

        branch_text = str(entry.get("canonical_branch") or "").strip()
        canonical_branch = branch_text or None
        if repository_identity.startswith("git://") and canonical_branch is None:
            diagnostics.append("canonical_repository_git_branch_missing")

        specs.append(
            CanonicalRepositorySpec(
                root=root,
                repository_identity=repository_identity,
                canonical_branch=canonical_branch,
            )
        )

    ordered = tuple(sorted(specs, key=lambda item: str(item.root).casefold()))
    for left_index, left in enumerate(ordered):
        if workspace_root is not None and _paths_overlap(left.root, workspace_root):
            diagnostics.append("canonical_repository_overlaps_workspace_root")
        for right in ordered[left_index + 1 :]:
            if _paths_overlap(left.root, right.root):
                diagnostics.append("canonical_repository_roots_overlap")

    unique_diagnostics = tuple(dict.fromkeys(diagnostics))
    return ordered, not unique_diagnostics, unique_diagnostics


@dataclass(frozen=True)
class MutationExecutionPolicy:
    """Provider-owned mutation execution policy introduced by SX-HMSA-001/S01."""

    configured: bool = False
    scoped_mutation_enabled: bool = False
    workspace_root: Path | None = None
    protected_roots: tuple[Path, ...] = ()
    runtime_read_roots: tuple[Path, ...] = ()
    scope_ttl_seconds: int = 3600
    evidence_retention_days: int = 30
    operator_unrestricted_enabled: bool = False
    canonical_repository_firewall_enabled: bool = False
    canonical_repositories: tuple[CanonicalRepositorySpec, ...] = ()
    canonical_repository_inventory_valid: bool = True
    canonical_repository_inventory_diagnostics: tuple[str, ...] = ()

    @property
    def legacy_unrestricted_compat(self) -> bool:
        """Historical unprofiled script_run compatibility, never a new capability."""
        return not self.configured

    @property
    def scoped_runtime_ready(self) -> bool:
        """S01 readiness seam; mandatory later-slice prerequisites are absent."""
        return False

    @property
    def canonical_repository_inventory_ready(self) -> bool:
        """Inventory/classifier readiness only; not provider-wide capability readiness."""
        return (
            self.configured
            and self.canonical_repository_firewall_enabled
            and self.canonical_repository_inventory_valid
            and bool(self.canonical_repositories)
        )

    @property
    def canonical_repository_inventory_readiness_reasons(self) -> tuple[str, ...]:
        reasons = list(self.canonical_repository_inventory_diagnostics)
        if not self.configured:
            reasons.append("mutation_execution_not_configured")
        if not self.canonical_repository_firewall_enabled:
            reasons.append("canonical_repository_firewall_disabled")
        if not self.canonical_repositories:
            reasons.append("canonical_repository_inventory_empty")
        return tuple(dict.fromkeys(reasons))

    @classmethod
    def from_block(cls, block: dict[str, Any] | None, *, configured: bool) -> "MutationExecutionPolicy":
        if not configured:
            return cls(configured=False)
        if block is None:
            block = {}
        if not isinstance(block, dict):
            raise ValueError("mutation_execution must be a mapping")

        raw_workspace = block.get("workspace_root")
        workspace_root = (
            _canonical_host_root(raw_workspace, "workspace_root")
            if raw_workspace not in (None, "")
            else None
        )
        protected_roots = _canonical_host_roots(block.get("protected_roots"), "protected_roots")
        runtime_read_roots = _canonical_host_roots(
            block.get("runtime_read_roots"), "runtime_read_roots"
        )

        if workspace_root is not None:
            for protected in protected_roots:
                if _paths_overlap(workspace_root, protected):
                    raise ValueError(
                        "mutation_execution workspace_root overlaps protected_roots; "
                        "scoped mutation placement would be ambiguous"
                    )

        canonical_repositories, inventory_valid, inventory_diagnostics = (
            _canonical_repository_inventory(
                block.get("canonical_repositories"),
                workspace_root=workspace_root,
            )
        )

        try:
            scope_ttl_seconds = int(block.get("scope_ttl_seconds", 3600))
            evidence_retention_days = int(block.get("evidence_retention_days", 30))
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "mutation_execution scope_ttl_seconds/evidence_retention_days must be integers"
            ) from exc
        if scope_ttl_seconds <= 0:
            raise ValueError("mutation_execution.scope_ttl_seconds must be positive")
        if evidence_retention_days <= 0:
            raise ValueError("mutation_execution.evidence_retention_days must be positive")

        return cls(
            configured=True,
            scoped_mutation_enabled=bool(block.get("scoped_mutation_enabled", False)),
            workspace_root=workspace_root,
            protected_roots=protected_roots,
            runtime_read_roots=runtime_read_roots,
            scope_ttl_seconds=scope_ttl_seconds,
            evidence_retention_days=evidence_retention_days,
            operator_unrestricted_enabled=bool(block.get("operator_unrestricted_enabled", False)),
            canonical_repository_firewall_enabled=bool(
                block.get("canonical_repository_firewall_enabled", False)
            ),
            canonical_repositories=canonical_repositories,
            canonical_repository_inventory_valid=inventory_valid,
            canonical_repository_inventory_diagnostics=inventory_diagnostics,
        )


@dataclass(frozen=True)
class LocalApiAction:
    """One permitted action on a local endpoint.

    `request` is for protocol=http ("GET /v1.44/containers/json"); `method` is
    for protocol=jsonrpc ("agent.list"). Exactly one applies.

    `select` is NOT cosmetic. Measured against nine real containers on jupiter:
    `docker ps` text is 712 bytes, the raw socket JSON for the same question is
    20,336, and a curated projection is 1,457. A passthrough would be 28x worse
    than the text it replaces, so an action declares what to keep.
    """

    request: str | None = None
    method: str | None = None
    select: tuple[str, ...] = ()
    description: str | None = None
    params_schema: dict[str, Any] | None = None


@dataclass(frozen=True)
class LocalApiEndpoint:
    """A host-local endpoint the agent may talk to."""

    name: str
    transport: str
    path: str
    protocol: str
    actions: dict[str, LocalApiAction]
    timeout_s: float = 30.0
    run_as: str | None = None
    compatibility: dict[str, Any] = field(default_factory=dict)


@dataclass
class Policy:
    """Loaded policy. Immutable after construction."""

    exec_strict: bool = False
    disabled_ops: frozenset[str] = field(default_factory=frozenset)
    allowed_commands: tuple[str, ...] = field(default_factory=tuple)
    authenticated_git_enabled: bool = False
    authenticated_git_allow_push: bool = False
    authenticated_git_timeout_seconds: int = 20
    mutation_execution: MutationExecutionPolicy = field(default_factory=MutationExecutionPolicy)
    services: dict[str, ServiceSpec] = field(default_factory=dict)
    local_apis: dict[str, LocalApiEndpoint] = field(default_factory=dict)
    locations: dict[str, LocationSpec] = field(default_factory=dict)
    playbooks: dict[str, dict[str, Any]] = field(default_factory=dict)
    hostname_label: str | None = None
    preferred_profile: str | None = None
    exec_timeout_default: int = 60
    exec_timeout_max: int = 600
    upload_base: Path = field(default_factory=lambda: default_upload_base())
    trusted_fetch_hosts: tuple[str, ...] = ()
    file_url_timeout_seconds: int = 15
    file_ops_paths: tuple[FileOpsPath, ...] = ()
    file_ops_max_read_bytes: int = 65536
    file_ops_max_list_entries: int = 1000
    file_ops_max_search_results: int = 200

    @classmethod
    def empty(cls) -> "Policy":
        return cls()

    @classmethod
    def from_file(cls, path: Path) -> "Policy":
        if not path.exists():
            logger.warning("policy_config_missing", extra={"path": str(path)})
            return cls.empty()
        try:
            data = yaml.safe_load(path.read_text()) or {}
        except (yaml.YAMLError, OSError) as exc:
            logger.error("policy_config_invalid", extra={"path": str(path), "error": str(exc)})
            return cls.empty()
        try:
            return cls.from_dict(data)
        except ValueError as exc:
            logger.error("policy_config_schema_error", extra={"path": str(path), "error": str(exc)})
            raise

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Policy":
        TYPO_HINTS = {
            "allow": "allowed_commands",
            "allowedCommands": "allowed_commands",
            "commands": "allowed_commands",
            "service": "services",
            "location": "locations",
            "playbook": "playbooks",
            "hub": "hub_url",
        }
        typos_found = [k for k in data.keys() if k in TYPO_HINTS]
        if typos_found:
            hints = [
                f"  '{k}' is not recognized — did you mean '{TYPO_HINTS[k]}'?"
                for k in sorted(typos_found)
            ]
            raise ValueError(
                "config.yaml contains keys that look like common typos:\n"
                + "\n".join(hints)
                + "\nFix the key name(s) and restart the agent."
            )

        KNOWN_KEYS = {
            "agent", "exec", "allowed_commands", "services", "locations",
            "playbooks", "hub_url", "upload_base", "log", "security",
            "file_ops", "local_apis", "disabled_ops", "exec_strict",
            "authenticated_git", "mutation_execution",
        }
        unknown = set(data.keys()) - KNOWN_KEYS - set(TYPO_HINTS.keys())
        if unknown:
            logger.warning(
                "policy_unknown_keys",
                extra={"unknown_keys": sorted(unknown), "known_keys": sorted(KNOWN_KEYS)},
            )

        agent_block = data.get("agent", {}) or {}
        exec_block = data.get("exec", {}) or {}
        security_block = data.get("security", {}) or {}
        file_ops_block = data.get("file_ops", {}) or {}
        authenticated_git_block = data.get("authenticated_git", {}) or {}
        if not isinstance(authenticated_git_block, dict):
            raise ValueError("authenticated_git must be a mapping")

        mutation_execution_present = "mutation_execution" in data
        mutation_execution = MutationExecutionPolicy.from_block(
            data.get("mutation_execution"), configured=mutation_execution_present
        )
        if not mutation_execution_present:
            logger.warning(
                "mutation_execution_legacy_unrestricted_compat",
                extra={"detail": (
                    "mutation_execution is absent; preserving historical unprofiled "
                    "script_run behavior as legacy compatibility only. This does not "
                    "satisfy scoped mutation or pre-execution audit capabilities."
                )},
            )

        services: dict[str, ServiceSpec] = {}
        for name, meta in (data.get("services") or {}).items():
            actions = tuple(meta.get("actions") or [])
            services[name] = ServiceSpec(
                unit=meta.get("unit", name), actions=actions,
                requires_sudo=bool(meta.get("requires_sudo", True)),
                description=meta.get("description", ""),
                domain=meta.get("domain", "system"), backend=meta.get("backend", "service"),
            )

        local_apis: dict[str, LocalApiEndpoint] = {}
        for name, meta in (data.get("local_apis") or {}).items():
            if not isinstance(meta, dict):
                logger.warning("local_apis: %s is not a mapping; skipped", name)
                continue
            transport = str(meta.get("transport") or "").strip()
            protocol = str(meta.get("protocol") or "").strip()
            path_value = str(meta.get("path") or "").strip()
            raw_actions = meta.get("actions")
            if transport not in ("unix", "stdio") or protocol not in ("http", "jsonrpc"):
                logger.warning("local_apis: %s has invalid transport/protocol; skipped", name)
                continue
            if not path_value or not isinstance(raw_actions, dict) or not raw_actions:
                logger.warning("local_apis: %s is incomplete; skipped", name)
                continue
            actions: dict[str, LocalApiAction] = {}
            for act_name, act in raw_actions.items():
                act = act or {}
                if not isinstance(act, dict):
                    continue
                request = act.get("request")
                method = act.get("method")
                if protocol == "http" and not request:
                    continue
                if protocol == "jsonrpc" and not method:
                    continue
                pschema = act.get("params")
                if pschema is not None and not isinstance(pschema, dict):
                    pschema = None
                actions[str(act_name)] = LocalApiAction(
                    request=str(request) if request else None,
                    method=str(method) if method else None,
                    select=tuple(str(x) for x in (act.get("select") or ())),
                    description=str(act["description"]) if act.get("description") else None,
                    params_schema=pschema,
                )
            if not actions:
                continue
            compat = meta.get("compatibility") or {}
            if compat and not isinstance(compat, dict):
                compat = {}
            local_apis[str(name)] = LocalApiEndpoint(
                name=str(name), transport=transport, path=path_value, protocol=protocol,
                actions=actions, timeout_s=float(meta.get("timeout_s") or 30),
                run_as=str(meta["run_as"]) if meta.get("run_as") else None,
                compatibility=compat if isinstance(compat, dict) else {},
            )

        locations: dict[str, LocationSpec] = {}
        for label, meta in (data.get("locations") or {}).items():
            if isinstance(meta, str):
                locations[label] = LocationSpec(path=meta)
            else:
                locations[label] = LocationSpec(
                    path=meta["path"], description=meta.get("description", "")
                )

        raw_paths = file_ops_block.get("paths")
        legacy_read_paths = file_ops_block.get("allowed_read_paths")
        file_ops_paths_list: list[FileOpsPath] = []
        if raw_paths:
            if legacy_read_paths:
                logger.warning("file_ops_both_keys_present")
            for entry in raw_paths:
                if isinstance(entry, str):
                    file_ops_paths_list.append(FileOpsPath(path=entry))
                elif isinstance(entry, dict) and entry.get("path"):
                    file_ops_paths_list.append(
                        FileOpsPath(path=str(entry["path"]), access=str(entry.get("access", "r")))
                    )
                else:
                    logger.warning("file_ops_path_entry_invalid", extra={"entry": repr(entry)})
        elif legacy_read_paths:
            logger.warning("file_ops_allowed_read_paths_deprecated")
            for entry in legacy_read_paths:
                file_ops_paths_list.append(FileOpsPath(path=str(entry), access="r"))

        _raw_profile = agent_block.get("preferred_profile")
        if _raw_profile in (None, "compact", "full"):
            _preferred_profile = _raw_profile
        else:
            logger.warning("policy_preferred_profile_invalid", extra={"value": repr(_raw_profile)})
            _preferred_profile = None

        policy = cls(
            allowed_commands=tuple(data.get("allowed_commands") or []),
            exec_strict=bool(data.get("exec_strict", False)),
            disabled_ops=frozenset(
                str(o).strip() for o in (data.get("disabled_ops") or []) if str(o).strip()
            ),
            authenticated_git_enabled=bool(authenticated_git_block.get("enabled", False)),
            authenticated_git_allow_push=bool(authenticated_git_block.get("allow_push", False)),
            authenticated_git_timeout_seconds=max(
                5, min(int(authenticated_git_block.get("timeout_seconds", 20)), 50)
            ),
            mutation_execution=mutation_execution,
            services=services,
            local_apis=local_apis,
            locations=locations,
            playbooks=dict(data.get("playbooks") or {}),
            hostname_label=agent_block.get("hostname_label"),
            preferred_profile=_preferred_profile,
            exec_timeout_default=int(exec_block.get("timeout_default", 60)),
            exec_timeout_max=int(exec_block.get("timeout_max", 600)),
            upload_base=Path(data.get("upload_base") or default_upload_base()).resolve(),
            trusted_fetch_hosts=tuple(security_block.get("trusted_fetch_hosts") or ()),
            file_url_timeout_seconds=int(security_block.get("file_url_timeout_seconds", 15)),
            file_ops_paths=tuple(file_ops_paths_list),
            file_ops_max_read_bytes=int(file_ops_block.get("max_read_bytes", 65536)),
            file_ops_max_list_entries=int(file_ops_block.get("max_list_entries", 1000)),
            file_ops_max_search_results=int(file_ops_block.get("max_search_results", 200)),
        )
        if not policy.allowed_commands:
            logger.warning(
                "Policy loaded with NO allowed_commands. All `exec` calls will be rejected."
            )
        else:
            logger.info(
                "policy_loaded",
                extra={
                    "allowed_commands_count": len(policy.allowed_commands),
                    "services_count": len(policy.services),
                    "playbooks_count": len(policy.playbooks),
                },
            )
        return policy

    def is_command_allowed(self, cmd: str) -> bool:
        cmd = (cmd or "").strip()
        if not cmd:
            return False
        return any(cmd.startswith(allowed) for allowed in self.allowed_commands)

    def get_service(self, name: str) -> ServiceSpec | None:
        return self.services.get(name)

    def is_service_action_allowed(self, name: str, action: str) -> bool:
        spec = self.services.get(name)
        return spec is not None and action in spec.actions

    def resolve_path(self, path: str, *, need_write: bool = False) -> Path | None:
        if not self.file_ops_paths or not path:
            return None
        try:
            candidate = Path(path).resolve(strict=False)
        except (OSError, RuntimeError, ValueError):
            return None
        for entry in self.file_ops_paths:
            if need_write and entry.access != "rw":
                continue
            try:
                allowed = Path(entry.path).resolve(strict=False)
            except (OSError, RuntimeError, ValueError):
                continue
            if candidate == allowed or candidate.is_relative_to(allowed):
                return candidate
        return None

    def resolve_read_path(self, path: str) -> Path | None:
        return self.resolve_path(path, need_write=False)
