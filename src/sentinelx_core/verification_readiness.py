"""Physical readiness for provider-owned Node/npm scoped verification.

The base scoped-mutation readiness remains independent.  This module adds a
second fail-closed capability probe that reuses the canonical profiled
``script_run`` executor and a disposable provider-owned source/capsule fixture.
It never turns cached readiness into request-time execution authority: every
real verification request still rebuilds and validates its source, capsule and
toolchain admission before START/SPAWN.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import secrets
import shutil
import sys
import threading
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sentinelx_core.mutation_placement import RepositoryIdentity, SemanticIdentity
from sentinelx_core.mutation_readiness import MutationRuntimeReadiness, probe_mutation_runtime
from sentinelx_core.mutation_scope import SCOPED_SCRIPT_OPERATION_CLASS, MutationScopeStore
from sentinelx_core.policy import MutationExecutionPolicy, Policy
from sentinelx_core.request_context import RequestContext
from sentinelx_core.verification_profile import (
    NodeNpmVerificationProfile,
    build_toolchain_manifest,
    compute_dependency_payload_digest,
    compute_source_manifest_digest,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class VerificationRuntimeReadiness:
    available: bool
    reason: str
    checks: dict[str, bool]
    profile_id: str | None = None
    toolchain_kind: str | None = None
    toolchain_digest: str | None = None

    def feature(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "available": self.available,
            "verified": self.available,
            "platform": "windows_appcontainer_v1",
            "self_check": "verified" if self.available else "unavailable",
            "reason": self.reason,
            "checks": dict(self.checks),
        }
        if self.profile_id is not None:
            result["profile_id"] = self.profile_id
        if self.toolchain_kind is not None:
            result["toolchain_kind"] = self.toolchain_kind
        if self.toolchain_digest is not None:
            result["toolchain_digest"] = self.toolchain_digest
        return result


_CACHE_LOCK = threading.Lock()
_CACHE: dict[tuple[object, ...], VerificationRuntimeReadiness] = {}


def _checks() -> dict[str, bool]:
    return {
        "windows": False,
        "base_scoped_mutation": False,
        "profile_configured": False,
        "profile_stores": False,
        "toolchain_integrity": False,
        "appcontainer_node": False,
        "appcontainer_npm": False,
        "dns_denied": False,
        "http_denied": False,
        "protected_root_denied": False,
        "terminal_non_active": False,
        "transient_toolchain_authority_absent": False,
    }


def _unavailable(
    reason: str,
    checks: dict[str, bool],
    profile: NodeNpmVerificationProfile | None = None,
) -> VerificationRuntimeReadiness:
    return VerificationRuntimeReadiness(
        False,
        reason,
        checks,
        profile_id=profile.profile_id if profile is not None else None,
        toolchain_kind=profile.kind if profile is not None else None,
    )


def _cache_key(policy: MutationExecutionPolicy, state_root: Path) -> tuple[object, ...]:
    profiles = tuple(
        (
            profile.profile_id,
            profile.kind,
            str(profile.toolchain_root).casefold(),
            str(profile.source_snapshot_root).casefold(),
            str(profile.dependency_capsule_root).casefold(),
            profile.node_relative.casefold(),
            profile.npm_cli_relative.casefold(),
            profile.contract_revision,
            profile.capsule_manifest_revision,
            tuple(sorted(profile.limits.canonical_payload().items())),
        )
        for profile in policy.verification_profiles
    )
    return (
        str(state_root.resolve(strict=False)).casefold(),
        policy.configured,
        policy.scoped_mutation_enabled,
        str(policy.workspace_root).casefold() if policy.workspace_root else None,
        tuple(str(path).casefold() for path in policy.protected_roots),
        tuple(str(path).casefold() for path in policy.runtime_read_roots),
        policy.scope_ttl_seconds,
        policy.evidence_retention_days,
        profiles,
    )


def _write_probe_inputs(
    profile: NodeNpmVerificationProfile,
    fixture_root: Path,
    token: str,
) -> tuple[NodeNpmVerificationProfile, dict[str, str]]:
    """Build disposable source/capsule inputs without mutating configured stores."""
    probe_profile = replace(
        profile,
        source_snapshot_root=fixture_root / "sources",
        dependency_capsule_root=fixture_root / "capsules",
    )
    source_id = "readiness-source"
    capsule_id = "readiness-capsule"
    payload = probe_profile.source_snapshot_path(source_id) / "payload"
    payload.mkdir(parents=True, exist_ok=True)

    package = {
        "name": "sentinelx-verification-readiness",
        "version": "1.0.0",
        "private": True,
    }
    lock = {
        "name": package["name"],
        "version": package["version"],
        "lockfileVersion": 3,
        "requires": True,
        "packages": {"": {"name": package["name"], "version": package["version"]}},
    }
    package_bytes = (json.dumps(package, sort_keys=True) + "\n").encode("utf-8")
    lock_bytes = (json.dumps(lock, sort_keys=True) + "\n").encode("utf-8")
    (payload / "package.json").write_bytes(package_bytes)
    (payload / "package-lock.json").write_bytes(lock_bytes)
    lock_sha = hashlib.sha256(lock_bytes).hexdigest()
    head_sha = hashlib.sha256(token.encode("ascii")).hexdigest()[:40]

    source_manifest: dict[str, object] = {
        "schema_version": 1,
        "kind": "verification_source_snapshot",
        "source_id": source_id,
        "repository": {
            "vcs": "git",
            "authority": "sentinelx.local",
            "path": "runtime/verification-readiness",
        },
        "transport": {"type": "github-pr", "pr_number": 1, "head_sha": head_sha},
        "source_subpath": "readiness",
        "package_lock_sha256": lock_sha,
        "files": [
            {
                "path": "package.json",
                "size": len(package_bytes),
                "sha256": hashlib.sha256(package_bytes).hexdigest(),
            },
            {
                "path": "package-lock.json",
                "size": len(lock_bytes),
                "sha256": lock_sha,
            },
        ],
    }
    source_manifest["source_manifest_digest"] = compute_source_manifest_digest(source_manifest)
    source_store = probe_profile.source_snapshot_path(source_id)
    (source_store / "source-snapshot.json").write_text(
        json.dumps(source_manifest, sort_keys=True), encoding="utf-8"
    )

    capsule_store = probe_profile.dependency_capsule_path(capsule_id)
    (capsule_store / "npm-cache").mkdir(parents=True, exist_ok=True)
    capsule_files: list[dict[str, object]] = []
    capsule = {
        "schema_version": 1,
        "kind": "node_npm_dependency_capsule",
        "capsule_id": capsule_id,
        "package_lock_sha256": lock_sha,
        "files": capsule_files,
        "payload_digest": compute_dependency_payload_digest(capsule_files),
    }
    (capsule_store / "verification-capsule.json").write_text(
        json.dumps(capsule, sort_keys=True), encoding="utf-8"
    )
    return probe_profile, {
        "profile": probe_profile.profile_id,
        "source_id": source_id,
        "source_manifest_sha256": str(source_manifest["source_manifest_digest"]),
        "source_revision": head_sha,
        "capsule_id": capsule_id,
        "package_lock_sha256": lock_sha,
    }


def _probe_once(
    policy: MutationExecutionPolicy,
    state_root: Path,
    base_readiness: MutationRuntimeReadiness,
) -> VerificationRuntimeReadiness:
    checks = _checks()
    if sys.platform != "win32":
        return _unavailable("Windows AppContainer enforcement is required", checks)
    checks["windows"] = True
    if not base_readiness.available:
        return _unavailable("base scoped mutation runtime is unavailable", checks)
    checks["base_scoped_mutation"] = True

    profile = next(
        (candidate for candidate in policy.verification_profiles if candidate.kind == "node_npm_v1"),
        None,
    )
    if profile is None:
        return _unavailable("Node/npm verification profile is not configured", checks)
    checks["profile_configured"] = True

    try:
        source_store = profile.source_snapshot_root.resolve(strict=True)
        capsule_store = profile.dependency_capsule_root.resolve(strict=True)
        if not source_store.is_dir() or not capsule_store.is_dir():
            raise OSError("verification store is not a directory")
    except (OSError, RuntimeError):
        return _unavailable("provider verification stores are unavailable", checks, profile)
    checks["profile_stores"] = True

    try:
        toolchain = build_toolchain_manifest(profile)
    except (OSError, RuntimeError, ValueError):
        return _unavailable(
            "configured Node/npm toolchain failed integrity validation", checks, profile
        )
    checks["toolchain_integrity"] = True

    token = secrets.token_hex(10)
    state_root = state_root.resolve(strict=False)
    fixture_root = state_root / "verification-readiness" / token
    protected_marker = fixture_root / "provider-protected.marker"
    try:
        fixture_root.mkdir(parents=True, exist_ok=False)
        protected_marker.write_text("provider-only", encoding="utf-8")
        probe_profile, verification = _write_probe_inputs(profile, fixture_root, token)
        probe_policy = replace(policy, verification_profiles=(probe_profile,))
        runtime_policy = Policy(
            mutation_execution=probe_policy,
            upload_base=fixture_root / "uploads",
        )
        repository = RepositoryIdentity(
            vcs="git",
            authority="sentinelx.local",
            path="runtime/verification-readiness",
        )
        semantic = SemanticIdentity(
            project_id="sentinelx-runtime",
            task_id="scoped-verification-readiness",
            run_id=f"probe-{token}",
            attempt_id=f"attempt-{token}",
            slice_id="readiness",
        )
        store = MutationScopeStore(state_root)
        record = store.provision_scope(
            probe_policy,
            repository,
            semantic,
            allowed_operation_classes=(SCOPED_SCRIPT_OPERATION_CLASS,),
            provider_protected_roots=(state_root,),
        )

        from sentinelx_core.handlers.scoped_script import make_profiled_script_run_handler

        handler = make_profiled_script_run_handler(
            runtime_policy,
            fixture_root / "uploads",
            mutation_state_root=state_root,
        )
        context = RequestContext(
            request_id=f"verification-readiness-{token}",
            op="script_run",
            opaque_ref="scoped-verification-readiness",
            received_at=datetime.now(UTC),
        )
        marker_literal = repr(str(protected_marker))
        node_literal = repr(str(profile.resolve_node(require_exists=True)))
        npm_cli_literal = repr(str(profile.resolve_npm_cli(require_exists=True)))
        content = f'''\
import subprocess
import sys

node_executable = {node_literal}
npm_cli = {npm_cli_literal}

def stage(name):
    print("SENTINELX_STAGE_" + name, flush=True)

def run(command):
    try:
        completed = subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return False
    return completed.returncode == 0

def run_network_probe(source, timeout):
    try:
        completed = subprocess.run(
            [sys.executable, "-c", source],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return "denied"
    output = (completed.stdout + "\\n" + completed.stderr).strip()
    if "SENTINELX_PROBE_AVAILABLE" in output:
        return "available"
    if "SENTINELX_PROBE_DENIED" in output:
        return "denied"
    return "inconclusive"

stage("PYTHON_CHILD_START")
if not run([sys.executable, "-c", "raise SystemExit(0)"]):
    raise SystemExit("python child readiness execution failed")
print("SENTINELX_PYTHON_CHILD_READY")
stage("PYTHON_CHILD_DONE")

stage("NODE_START")
if not run([node_executable, "--version"]):
    raise SystemExit("node readiness execution failed")
print("SENTINELX_NODE_READY")
stage("NODE_DONE")
stage("NPM_START")
if not run([
    node_executable,
    "--preserve-symlinks",
    "--preserve-symlinks-main",
    npm_cli,
    "--version",
]):
    raise SystemExit("npm readiness execution failed")
print("SENTINELX_NPM_READY")
stage("NPM_DONE")

stage("DNS_START")
dns_probe = run_network_probe(
    """
import socket
try:
    socket.getaddrinfo("example.com", 80)
except OSError:
    print("SENTINELX_PROBE_DENIED")
else:
    print("SENTINELX_PROBE_AVAILABLE")
""",
    4,
)
if dns_probe == "denied":
    print("SENTINELX_DNS_DENIED")
elif dns_probe == "available":
    raise SystemExit("verification DNS unexpectedly available")
else:
    raise SystemExit("verification DNS probe inconclusive")
stage("DNS_DONE")

stage("HTTP_START")
http_probe = run_network_probe(
    """
import urllib.request
try:
    urllib.request.urlopen("http://example.com", timeout=2).close()
except Exception:
    print("SENTINELX_PROBE_DENIED")
else:
    print("SENTINELX_PROBE_AVAILABLE")
""",
    5,
)
if http_probe == "denied":
    print("SENTINELX_HTTP_DENIED")
elif http_probe == "available":
    raise SystemExit("verification HTTP unexpectedly available")
else:
    raise SystemExit("verification HTTP probe inconclusive")
stage("HTTP_DONE")

stage("PROTECTED_START")
try:
    with open({marker_literal}, "rb") as handle:
        handle.read(1)
except OSError:
    print("SENTINELX_PROTECTED_DENIED")
else:
    raise SystemExit("provider protected state unexpectedly readable")
stage("PROTECTED_DONE")
'''
        result = asyncio.run(
            handler(
                context,
                {
                    "interpreter": "python3",
                    "content": content,
                    "timeout": 120,
                    "cleanup": True,
                    "verification": verification,
                    "mutation": {
                        "execution_profile": "scoped_mutation",
                        "scope_ref": {
                            "scope_id": record.scope_id,
                            "generation": record.generation,
                        },
                    },
                    "lineage": {
                        "project_id": semantic.project_id,
                        "task_id": semantic.task_id,
                        "run_id": semantic.run_id,
                        "attempt_id": semantic.attempt_id,
                        "slice_id": semantic.slice_id,
                    },
                    "repository": {
                        "vcs": repository.vcs,
                        "authority": repository.authority,
                        "path": repository.path,
                    },
                },
            )
        )
        output = str(result.get("output") or "")
        checks["appcontainer_node"] = "SENTINELX_NODE_READY" in output
        checks["appcontainer_npm"] = "SENTINELX_NPM_READY" in output
        checks["dns_denied"] = "SENTINELX_DNS_DENIED" in output
        checks["http_denied"] = "SENTINELX_HTTP_DENIED" in output
        checks["protected_root_denied"] = "SENTINELX_PROTECTED_DENIED" in output
        checks["terminal_non_active"] = result.get("terminal_state") == "terminal"
        # The canonical terminalizer revokes the tracked toolchain ACL before
        # projecting a terminal result.  The Windows physical test additionally
        # reads back the DACL after terminalization.
        checks["transient_toolchain_authority_absent"] = checks["terminal_non_active"]
        if not all(checks.values()):
            stages = (
                "PROTECTED_DONE", "PROTECTED_START",
                "HTTP_DONE", "HTTP_START",
                "DNS_DONE", "DNS_START",
                "NPM_DONE", "NPM_START",
                "NODE_DONE", "NODE_START",
                "PYTHON_CHILD_DONE", "PYTHON_CHILD_START",
            )
            last_stage = next(
                (stage_name for stage_name in stages if f"SENTINELX_STAGE_{stage_name}" in output),
                "BEFORE_SCRIPT_STAGE",
            )
            if result.get("timed_out") is True:
                return _unavailable(
                    f"Node/npm verification self-check timed out at {last_stage}",
                    checks,
                    profile,
                )
            return _unavailable(
                "one or more Node/npm verification self-checks failed", checks, profile
            )
        return VerificationRuntimeReadiness(
            True,
            "real Windows AppContainer Node/npm verification self-check passed",
            checks,
            profile_id=profile.profile_id,
            toolchain_kind=toolchain.kind,
            toolchain_digest=toolchain.toolchain_digest,
        )
    except Exception as exc:  # noqa: BLE001 - readiness must fail closed on every defect.
        logger.warning("Node/npm verification readiness probe failed: %s", exc)
        return _unavailable(
            f"Node/npm verification self-check failed ({type(exc).__name__})", checks, profile
        )
    finally:
        shutil.rmtree(fixture_root, ignore_errors=True)


def probe_node_npm_verification_runtime(
    policy: MutationExecutionPolicy,
    state_root: Path,
    *,
    base_readiness: MutationRuntimeReadiness | None = None,
    force: bool = False,
) -> VerificationRuntimeReadiness:
    """Return cached physical Node/npm readiness independently from base readiness."""
    key = _cache_key(policy, state_root)
    with _CACHE_LOCK:
        if not force and key in _CACHE:
            return _CACHE[key]

    base = base_readiness
    if base is None:
        base = probe_mutation_runtime(policy, state_root, force=force)
    result = _probe_once(policy, state_root, base)
    with _CACHE_LOCK:
        _CACHE[key] = result
    return result


def cached_node_npm_toolchain_digest(
    policy: MutationExecutionPolicy,
    state_root: Path,
    profile_id: str,
) -> str | None:
    """Return only a previously *verified* digest as a negative drift guard.

    Absence never authorizes or blocks execution by itself.  When present, the
    request path still recomputes the full manifest and may only reject a drift;
    it never substitutes this cached value for request-time validation.
    """
    key = _cache_key(policy, state_root)
    with _CACHE_LOCK:
        result = _CACHE.get(key)
    if (
        result is None
        or not result.available
        or result.profile_id != profile_id
        or result.toolchain_digest is None
    ):
        return None
    return result.toolchain_digest
