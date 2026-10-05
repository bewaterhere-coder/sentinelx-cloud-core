"""Pre-SPAWN materialization for provider-owned scoped verification.

The broker copies already-admitted immutable source/capsule inputs into the
exact mutation workspace and seals deterministic launcher identity before any
untrusted process exists.  This module grants no OS authority by itself; the
Windows sandbox owns AppContainer ACLs and process creation.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from sentinelx_core.mutation_audit import MutationVerificationIntent
from sentinelx_core.verification_profile import (
    FileDigestEntry,
    NodeNpmVerificationProfile,
    ToolchainManifest,
    VerificationAdmission,
    build_toolchain_manifest,
    load_dependency_capsule,
    load_source_snapshot,
)

_COPY_CHUNK_BYTES = 1024 * 1024
_FILE_ATTRIBUTE_REPARSE_POINT = 0x400
_VERIFICATION_DIR = ".sentinelx-verification"
_SOURCE_DIR = "source"
_CACHE_DIR = "npm-cache"
_SHIM_DIR = "bin"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(_COPY_CHUNK_BYTES), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_digest(value: object) -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _same_toolchain(left: ToolchainManifest, right: ToolchainManifest) -> bool:
    return (
        left.kind == right.kind
        and left.node_relative == right.node_relative
        and left.npm_cli_relative == right.npm_cli_relative
        and left.files == right.files
        and left.toolchain_digest == right.toolchain_digest
        and left.contract_revision == right.contract_revision
    )


def _cmd_path(path: Path) -> str:
    text = str(path.resolve(strict=True))
    if '"' in text or "\r" in text or "\n" in text:
        raise ValueError("verification launcher path contains unsupported characters")
    return text.replace("%", "%%")


def launcher_files(profile: NodeNpmVerificationProfile) -> tuple[tuple[str, bytes], ...]:
    node = _cmd_path(profile.resolve_node(require_exists=True))
    npm_cli = _cmd_path(profile.resolve_npm_cli(require_exists=True))
    return (
        ("node.cmd", f'@echo off\r\n"{node}" %*\r\n'.encode("utf-8")),
        (
            "npm.cmd",
            (
                '@echo off\r\n'
                f'"{node}" --preserve-symlinks --preserve-symlinks-main "{npm_cli}" %*\r\n'
            ).encode("utf-8"),
        ),
    )


def launcher_digest(files: Iterable[tuple[str, bytes]]) -> str:
    payload = [
        {
            "name": name,
            "size": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
        }
        for name, content in files
    ]
    return _canonical_digest(payload)


@dataclass(frozen=True)
class VerificationRuntimePlan:
    profile: NodeNpmVerificationProfile
    admission: VerificationAdmission
    toolchain: ToolchainManifest
    launchers: tuple[tuple[str, bytes], ...]
    audit_intent: MutationVerificationIntent


@dataclass(frozen=True)
class VerificationMaterialization:
    plan: VerificationRuntimePlan
    workspace: Path
    source_root: Path
    npm_cache_root: Path
    shim_root: Path

    @property
    def toolchain_root(self) -> Path:
        return self.plan.profile.toolchain_root.resolve(strict=True)


def build_verification_runtime_plan(
    profile: NodeNpmVerificationProfile,
    admission: VerificationAdmission,
) -> VerificationRuntimePlan:
    if admission.profile_id != profile.profile_id:
        raise ValueError("verification admission/profile mismatch")
    if admission.network_mode != "none":
        raise ValueError("verification runtime requires network_mode=none")
    current_toolchain = build_toolchain_manifest(profile)
    if not _same_toolchain(current_toolchain, admission.toolchain):
        raise ValueError("verification toolchain changed after admission")
    launchers = launcher_files(profile)
    intent = MutationVerificationIntent(
        profile_id=admission.profile_id,
        profile_revision=admission.profile_revision,
        source_repository_digest=admission.source.repository.digest,
        source_revision=admission.source.transport.revision,
        source_manifest_digest=admission.source.source_manifest_digest,
        toolchain_kind=admission.toolchain.kind,
        toolchain_digest=admission.toolchain.toolchain_digest,
        launcher_digest=launcher_digest(launchers),
        capsule_id=admission.capsule.capsule_id,
        capsule_revision=admission.capsule.revision,
        capsule_payload_digest=admission.capsule.payload_digest,
        expected_package_lock_sha256=admission.expected_package_lock_sha256,
        network_mode=admission.network_mode,
        resource_limits_digest=admission.resource_limits_digest,
    )
    return VerificationRuntimePlan(
        profile=profile,
        admission=admission,
        toolchain=current_toolchain,
        launchers=launchers,
        audit_intent=intent,
    )


def _is_reparse_or_symlink(path: Path) -> bool:
    try:
        if path.is_symlink():
            return True
        attrs = int(getattr(path.lstat(), "st_file_attributes", 0))
        return bool(attrs & _FILE_ATTRIBUTE_REPARSE_POINT)
    except OSError as exc:
        raise ValueError("verification payload path cannot be inspected") from exc


def _safe_member(root: Path, relative: str) -> Path:
    canonical_root = root.resolve(strict=True)
    if _is_reparse_or_symlink(canonical_root):
        raise ValueError("verification payload root must not be a reparse point")
    cursor = canonical_root
    for part in relative.split("/"):
        cursor = cursor / part
        if _is_reparse_or_symlink(cursor):
            raise ValueError("verification payload member traverses a reparse point")
    candidate = cursor.resolve(strict=True)
    if not candidate.is_relative_to(canonical_root):
        raise ValueError("verification payload member escaped its root")
    return candidate


def _copy_and_verify_payload(
    *,
    source_root: Path,
    destination_root: Path,
    files: tuple[FileDigestEntry, ...],
    max_total_bytes: int,
    max_files: int,
    max_single_file_bytes: int,
    label: str,
) -> None:
    if destination_root.exists():
        raise ValueError(f"{label} destination is already reserved")
    destination_root.mkdir(parents=True, exist_ok=False)
    copied_bytes = 0
    copied_files = 0
    try:
        for entry in files:
            if entry.size > max_single_file_bytes:
                raise ValueError(f"{label} file exceeds configured maximum")
            copied_bytes += entry.size
            copied_files += 1
            if copied_bytes > max_total_bytes or copied_files > max_files:
                raise ValueError(f"{label} exceeds configured resource limits")
            source = _safe_member(source_root, entry.path)
            if not source.is_file():
                raise ValueError(f"{label} payload member is not a regular file")
            if source.stat().st_size != entry.size or _sha256_file(source) != entry.sha256:
                raise ValueError(f"{label} payload changed after admission")
            destination = destination_root / Path(entry.path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with source.open("rb") as source_handle, destination.open("xb") as destination_handle:
                while block := source_handle.read(_COPY_CHUNK_BYTES):
                    destination_handle.write(block)
            if destination.stat().st_size != entry.size or _sha256_file(destination) != entry.sha256:
                raise ValueError(f"{label} materialized payload digest mismatch")
    except Exception:
        shutil.rmtree(destination_root, ignore_errors=True)
        raise


def _write_launchers(
    *,
    shim_root: Path,
    launchers: tuple[tuple[str, bytes], ...],
    expected_digest: str,
) -> None:
    if shim_root.exists():
        raise ValueError("verification launcher destination is already reserved")
    shim_root.mkdir(parents=True, exist_ok=False)
    try:
        for name, content in launchers:
            if Path(name).name != name or name in {".", ".."}:
                raise ValueError("verification launcher name is invalid")
            (shim_root / name).write_bytes(content)
        observed = launcher_digest(
            (name, (shim_root / name).read_bytes()) for name, _content in launchers
        )
        if observed != expected_digest:
            raise ValueError("verification launcher materialization digest mismatch")
    except Exception:
        shutil.rmtree(shim_root, ignore_errors=True)
        raise


def materialize_verification_runtime(
    plan: VerificationRuntimePlan,
    workspace: Path,
) -> VerificationMaterialization:
    exact_workspace = workspace.resolve(strict=True)
    source_root = exact_workspace / _SOURCE_DIR
    verification_root = exact_workspace / _VERIFICATION_DIR
    cache_root = verification_root / _CACHE_DIR
    shim_root = verification_root / _SHIM_DIR
    verification_root.mkdir(parents=True, exist_ok=True)
    limits = plan.profile.limits

    _copy_and_verify_payload(
        source_root=plan.admission.source.payload_root,
        destination_root=source_root,
        files=plan.admission.source.files,
        max_total_bytes=limits.source_max_total_bytes,
        max_files=limits.source_max_files,
        max_single_file_bytes=limits.max_single_file_bytes,
        label="source snapshot",
    )
    try:
        _copy_and_verify_payload(
            source_root=plan.admission.capsule.cache_root,
            destination_root=cache_root,
            files=plan.admission.capsule.files,
            max_total_bytes=limits.dependency_max_total_bytes,
            max_files=limits.dependency_max_files,
            max_single_file_bytes=limits.max_single_file_bytes,
            label="dependency capsule",
        )
        _write_launchers(
            shim_root=shim_root,
            launchers=plan.launchers,
            expected_digest=plan.audit_intent.launcher_digest,
        )
    except Exception:
        shutil.rmtree(source_root, ignore_errors=True)
        shutil.rmtree(verification_root, ignore_errors=True)
        raise

    return VerificationMaterialization(
        plan=plan,
        workspace=exact_workspace,
        source_root=source_root,
        npm_cache_root=cache_root,
        shim_root=shim_root,
    )


def cleanup_verification_materialization(materialized: VerificationMaterialization) -> None:
    shutil.rmtree(materialized.source_root, ignore_errors=True)
    shutil.rmtree(materialized.workspace / _VERIFICATION_DIR, ignore_errors=True)


def revalidate_verification_before_spawn(materialized: VerificationMaterialization) -> None:
    plan = materialized.plan
    current_toolchain = build_toolchain_manifest(plan.profile)
    if not _same_toolchain(current_toolchain, plan.toolchain):
        raise ValueError("verification toolchain changed before SPAWN")
    source = load_source_snapshot(
        plan.profile.source_snapshot_path(plan.admission.source.source_id),
        limits=plan.profile.limits,
        expected_manifest_sha256=plan.admission.source.source_manifest_digest,
        expected_revision=plan.admission.source.transport.revision,
    )
    if source != plan.admission.source:
        raise ValueError("verification source snapshot changed before SPAWN")
    capsule = load_dependency_capsule(
        plan.profile.dependency_capsule_path(plan.admission.capsule.capsule_id),
        limits=plan.profile.limits,
        expected_capsule_id=plan.admission.capsule.capsule_id,
    )
    if capsule != plan.admission.capsule:
        raise ValueError("verification dependency capsule changed before SPAWN")
    lock_path = _safe_member(materialized.source_root, "package-lock.json")
    if _sha256_file(lock_path) != plan.admission.expected_package_lock_sha256:
        raise ValueError("materialized package-lock digest changed before SPAWN")
    observed_launcher_digest = launcher_digest(
        (name, (materialized.shim_root / name).read_bytes())
        for name, _content in plan.launchers
    )
    if observed_launcher_digest != plan.audit_intent.launcher_digest:
        raise ValueError("verification launcher changed before SPAWN")
