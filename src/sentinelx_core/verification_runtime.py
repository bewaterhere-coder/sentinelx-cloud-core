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
            f'@echo off\r\n"{node}" "{npm_cli}" %*\r\n'.encode("utf-8"),
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
    if candidate == canonical_root or not candidate.is_relative_to(canonical_root):
        raise ValueError("verification payload member escaped provider root")
    if not candidate.is_file():
        raise ValueError("verification payload member is not a regular file")
    return candidate


def _copy_entries(
    source_root: Path,
    destination_root: Path,
    entries: tuple[FileDigestEntry, ...],
) -> None:
    destination_root.mkdir(parents=True, exist_ok=False)
    for entry in entries:
        source = _safe_member(source_root, entry.path)
        destination = destination_root / Path(*entry.path.split("/"))
        destination.parent.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256()
        size = 0
        with source.open("rb") as reader, destination.open("xb") as writer:
            while True:
                block = reader.read(_COPY_CHUNK_BYTES)
                if not block:
                    break
                size += len(block)
                if size > entry.size:
                    raise ValueError("verification payload exceeded sealed file size during copy")
                digest.update(block)
                writer.write(block)
            writer.flush()
            os.fsync(writer.fileno())
        if size != entry.size or digest.hexdigest() != entry.sha256:
            raise ValueError("verification payload changed during broker copy")


def _npm_cache_entries(entries: tuple[FileDigestEntry, ...]) -> tuple[FileDigestEntry, ...]:
    prefix = "npm-cache/"
    projected: list[FileDigestEntry] = []
    for entry in entries:
        if not entry.path.casefold().startswith(prefix):
            raise ValueError("dependency capsule V1 members must be rooted under npm-cache/")
        relative = entry.path[len(prefix) :]
        if not relative:
            raise ValueError("dependency capsule V1 member path is empty after npm-cache/")
        projected.append(FileDigestEntry(relative, entry.size, entry.sha256))
    return tuple(projected)


def _verify_entries(root: Path, entries: tuple[FileDigestEntry, ...]) -> None:
    canonical_root = root.resolve(strict=True)
    if _is_reparse_or_symlink(canonical_root):
        raise ValueError("materialized verification root must not be a reparse point")
    expected = {entry.path.casefold(): entry for entry in entries}
    observed: dict[str, Path] = {}
    for current, directories, names in os.walk(canonical_root, topdown=True, followlinks=False):
        current_path = Path(current)
        for name in directories:
            item = current_path / name
            if _is_reparse_or_symlink(item):
                raise ValueError("materialized verification tree contains a reparse directory")
        for name in names:
            item = current_path / name
            if _is_reparse_or_symlink(item) or not item.is_file():
                raise ValueError("materialized verification tree contains a non-regular file")
            relative = item.relative_to(canonical_root).as_posix()
            observed[relative.casefold()] = item
    if set(observed) != set(expected):
        raise ValueError("materialized verification tree differs from sealed manifest")
    for key, item in observed.items():
        entry = expected[key]
        if item.stat().st_size != entry.size or _sha256_file(item) != entry.sha256:
            raise ValueError("materialized verification payload digest mismatch")


def _write_launchers(root: Path, launchers: tuple[tuple[str, bytes], ...]) -> None:
    root.mkdir(parents=True, exist_ok=False)
    for name, content in launchers:
        path = root / name
        with path.open("xb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if path.read_bytes() != content:
            raise ValueError("verification launcher read-back mismatch")


def _assert_lock(path: Path, expected: str) -> None:
    if not path.is_file() or _sha256_file(path) != expected:
        raise ValueError("materialized package-lock digest mismatch")


def materialize_verification_runtime(
    plan: VerificationRuntimePlan,
    workspace: Path,
) -> VerificationMaterialization:
    workspace = workspace.resolve(strict=True)
    source_target = workspace / _SOURCE_DIR
    verification_root = workspace / _VERIFICATION_DIR
    cache_target = verification_root / _CACHE_DIR
    shim_target = verification_root / _SHIM_DIR
    if source_target.exists() or verification_root.exists():
        raise ValueError("verification materialization target already exists")

    source_store = plan.profile.source_snapshot_path(plan.admission.source.source_id)
    capsule_store = plan.profile.dependency_capsule_path(plan.admission.capsule.capsule_id)
    source = load_source_snapshot(
        source_store,
        limits=plan.profile.limits,
        expected_manifest_sha256=plan.admission.source.source_manifest_digest,
        expected_revision=plan.admission.source.transport.revision,
    )
    capsule = load_dependency_capsule(
        capsule_store,
        limits=plan.profile.limits,
        expected_capsule_id=plan.admission.capsule.capsule_id,
    )
    if source != plan.admission.source or capsule != plan.admission.capsule:
        raise ValueError("verification provider stores changed after admission")
    if source.package_lock_sha256 != capsule.package_lock_sha256:
        raise ValueError("verification source/capsule lock binding changed")

    cache_entries = _npm_cache_entries(capsule.files)
    try:
        _copy_entries(source_store / "payload", source_target, source.files)
        verification_root.mkdir(parents=True, exist_ok=False)
        _copy_entries(capsule_store / "npm-cache", cache_target, cache_entries)
        _write_launchers(shim_target, plan.launchers)
        materialized = VerificationMaterialization(
            plan=plan,
            workspace=workspace,
            source_root=source_target,
            npm_cache_root=cache_target,
            shim_root=shim_target,
        )
        revalidate_verification_before_spawn(materialized)
        return materialized
    except Exception:
        shutil.rmtree(source_target, ignore_errors=True)
        shutil.rmtree(verification_root, ignore_errors=True)
        raise


def revalidate_verification_before_spawn(materialized: VerificationMaterialization) -> None:
    plan = materialized.plan
    current_toolchain = build_toolchain_manifest(plan.profile)
    if not _same_toolchain(current_toolchain, plan.toolchain):
        raise ValueError("verification toolchain changed before SPAWN")
    _verify_entries(materialized.source_root, plan.admission.source.files)
    _verify_entries(
        materialized.npm_cache_root,
        _npm_cache_entries(plan.admission.capsule.files),
    )
    _assert_lock(
        materialized.source_root / "package-lock.json",
        plan.admission.expected_package_lock_sha256,
    )
    if launcher_digest(
        (name, (materialized.shim_root / name).read_bytes())
        for name, _content in plan.launchers
    ) != plan.audit_intent.launcher_digest:
        raise ValueError("verification launcher identity changed before SPAWN")


def cleanup_verification_materialization(materialized: VerificationMaterialization) -> None:
    shutil.rmtree(materialized.source_root, ignore_errors=True)
    shutil.rmtree(materialized.workspace / _VERIFICATION_DIR, ignore_errors=True)
