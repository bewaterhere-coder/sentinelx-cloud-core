"""Provider-owned verification profile and immutable input contracts.

This module is intentionally pure with respect to execution.  It validates the
logical Node/npm verification profile, source-under-test snapshots, dependency
capsules and deterministic toolchain identity used by the scoped runtime.  It
does not grant filesystem/network authority or spawn a process.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


PROFILE_CONTRACT_REVISION = 1
SOURCE_SNAPSHOT_SCHEMA_VERSION = 1
DEPENDENCY_CAPSULE_SCHEMA_VERSION = 1
TOOLCHAIN_CONTRACT_REVISION = 1

_LOGICAL_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_GIT_SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")
_WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:")
_FILE_ATTRIBUTE_REPARSE_POINT = 0x400


@dataclass(frozen=True)
class VerificationResourceLimits:
    source_max_total_bytes: int = 536_870_912
    source_max_files: int = 50_000
    dependency_max_total_bytes: int = 1_073_741_824
    dependency_max_files: int = 50_000
    max_single_file_bytes: int = 268_435_456
    max_relative_path_chars: int = 512

    HARD_CEILINGS = {
        "source_max_total_bytes": 2_147_483_648,
        "source_max_files": 200_000,
        "dependency_max_total_bytes": 4_294_967_296,
        "dependency_max_files": 200_000,
        "max_single_file_bytes": 1_073_741_824,
        "max_relative_path_chars": 1024,
    }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any] | None) -> "VerificationResourceLimits":
        if value is None:
            return cls()
        if not isinstance(value, Mapping):
            raise ValueError("verification profile limits must be a mapping")
        unknown = set(value) - set(cls.HARD_CEILINGS)
        if unknown:
            raise ValueError(f"unknown verification limit fields: {sorted(unknown)!r}")

        values: dict[str, int] = {}
        defaults = cls()
        for name, ceiling in cls.HARD_CEILINGS.items():
            raw = value.get(name, getattr(defaults, name))
            try:
                parsed = int(raw)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"verification limit {name} must be an integer") from exc
            if parsed <= 0:
                raise ValueError(f"verification limit {name} must be positive")
            if parsed > ceiling:
                raise ValueError(f"verification limit {name} exceeds hard ceiling")
            values[name] = parsed
        return cls(**values)

    def canonical_payload(self) -> dict[str, int]:
        return {
            "source_max_total_bytes": self.source_max_total_bytes,
            "source_max_files": self.source_max_files,
            "dependency_max_total_bytes": self.dependency_max_total_bytes,
            "dependency_max_files": self.dependency_max_files,
            "max_single_file_bytes": self.max_single_file_bytes,
            "max_relative_path_chars": self.max_relative_path_chars,
        }

    @property
    def digest(self) -> str:
        return _sha256_bytes(_canonical_json(self.canonical_payload()))


def validate_profile_id(value: Any) -> str:
    text = str(value or "").strip()
    if not _LOGICAL_ID_RE.fullmatch(text):
        raise ValueError("verification profile id must be a bounded logical identifier")
    return text


def validate_logical_id(value: Any, field_name: str) -> str:
    text = str(value or "").strip()
    if not _LOGICAL_ID_RE.fullmatch(text):
        raise ValueError(f"{field_name} must be a bounded logical identifier")
    return text


def normalize_sha256(value: Any, field_name: str) -> str:
    text = str(value or "").strip().lower()
    if not _SHA256_RE.fullmatch(text):
        raise ValueError(f"{field_name} must be a lowercase 64-hex SHA-256")
    return text


def normalize_relative_path(
    value: Any,
    field_name: str = "path",
    *,
    max_chars: int = 1024,
) -> str:
    text = str(value or "").strip().replace("\\", "/")
    if not text or len(text) > max_chars or "\x00" in text:
        raise ValueError(f"{field_name} is empty or exceeds the path bound")
    if text.startswith("/") or _WINDOWS_DRIVE_RE.match(text):
        raise ValueError(f"{field_name} must be relative")
    parts = text.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError(f"{field_name} contains traversal or non-canonical segments")
    return "/".join(parts)


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _is_reparse_or_symlink(path: Path) -> bool:
    try:
        if path.is_symlink():
            return True
        attrs = int(getattr(path.lstat(), "st_file_attributes", 0))
        return bool(attrs & _FILE_ATTRIBUTE_REPARSE_POINT)
    except OSError as exc:
        raise ValueError("verification path cannot be inspected") from exc


def _resolve_within(root: Path, relative: str, field_name: str) -> Path:
    normalized = normalize_relative_path(relative, field_name)
    try:
        canonical_root = root.resolve(strict=False)
        candidate = (canonical_root / Path(*normalized.split("/"))).resolve(strict=False)
    except (OSError, RuntimeError) as exc:
        raise ValueError(f"{field_name} cannot be canonicalized") from exc
    if candidate == canonical_root or not candidate.is_relative_to(canonical_root):
        raise ValueError(f"{field_name} escapes its provider-owned root")
    return candidate


@dataclass(frozen=True)
class NodeNpmVerificationProfile:
    profile_id: str
    toolchain_root: Path
    source_snapshot_root: Path
    dependency_capsule_root: Path
    node_relative: str = "node.exe"
    npm_cli_relative: str = "node_modules/npm/bin/npm-cli.js"
    kind: str = "node_npm_v1"
    contract_revision: int = PROFILE_CONTRACT_REVISION
    capsule_manifest_revision: int = DEPENDENCY_CAPSULE_SCHEMA_VERSION
    limits: VerificationResourceLimits = VerificationResourceLimits()

    def __post_init__(self) -> None:
        object.__setattr__(self, "profile_id", validate_profile_id(self.profile_id))
        if self.kind != "node_npm_v1":
            raise ValueError("unsupported verification profile kind")
        if self.contract_revision != PROFILE_CONTRACT_REVISION:
            raise ValueError("unsupported verification profile contract revision")
        if self.capsule_manifest_revision != DEPENDENCY_CAPSULE_SCHEMA_VERSION:
            raise ValueError("unsupported dependency capsule manifest revision")
        object.__setattr__(
            self,
            "node_relative",
            normalize_relative_path(self.node_relative, "node_relative"),
        )
        object.__setattr__(
            self,
            "npm_cli_relative",
            normalize_relative_path(self.npm_cli_relative, "npm_cli_relative"),
        )

    def resolve_node(self, *, require_exists: bool = True) -> Path:
        return _resolve_toolchain_member(
            self.toolchain_root,
            self.node_relative,
            "node_relative",
            require_exists=require_exists,
        )

    def resolve_npm_cli(self, *, require_exists: bool = True) -> Path:
        return _resolve_toolchain_member(
            self.toolchain_root,
            self.npm_cli_relative,
            "npm_cli_relative",
            require_exists=require_exists,
        )

    def source_snapshot_path(self, source_id: str) -> Path:
        return _resolve_logical_child(self.source_snapshot_root, source_id, "source_id")

    def dependency_capsule_path(self, capsule_id: str) -> Path:
        return _resolve_logical_child(self.dependency_capsule_root, capsule_id, "capsule_id")


def _resolve_logical_child(root: Path, logical_id: str, field_name: str) -> Path:
    logical = validate_logical_id(logical_id, field_name)
    try:
        canonical_root = root.resolve(strict=False)
        candidate = (canonical_root / logical).resolve(strict=False)
    except (OSError, RuntimeError) as exc:
        raise ValueError(f"{field_name} cannot be resolved") from exc
    if candidate.parent != canonical_root:
        raise ValueError(f"{field_name} escapes provider-owned store")
    return candidate


def _resolve_toolchain_member(
    root: Path,
    relative: str,
    field_name: str,
    *,
    require_exists: bool,
) -> Path:
    candidate = _resolve_within(root, relative, field_name)
    if require_exists:
        try:
            canonical_root = root.resolve(strict=True)
            candidate = candidate.resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            raise ValueError(f"{field_name} is not physically available") from exc
        if not candidate.is_relative_to(canonical_root):
            raise ValueError(f"{field_name} final path escapes toolchain root")
        if _is_reparse_or_symlink(candidate) or not candidate.is_file():
            raise ValueError(f"{field_name} must resolve to a regular non-reparse file")
    return candidate


@dataclass(frozen=True)
class FileDigestEntry:
    path: str
    size: int
    sha256: str

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, Any],
        *,
        limits: VerificationResourceLimits,
        field_name: str,
    ) -> "FileDigestEntry":
        if not isinstance(value, Mapping):
            raise ValueError(f"{field_name} must be a mapping")
        unknown = set(value) - {"path", "size", "sha256"}
        if unknown:
            raise ValueError(f"{field_name} contains unknown fields")
        path = normalize_relative_path(
            value.get("path"),
            f"{field_name}.path",
            max_chars=limits.max_relative_path_chars,
        )
        try:
            size = int(value.get("size"))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{field_name}.size must be an integer") from exc
        if size < 0 or size > limits.max_single_file_bytes:
            raise ValueError(f"{field_name}.size exceeds the per-file bound")
        return cls(
            path=path,
            size=size,
            sha256=normalize_sha256(value.get("sha256"), f"{field_name}.sha256"),
        )

    def canonical_payload(self) -> dict[str, Any]:
        return {"path": self.path, "size": self.size, "sha256": self.sha256}


@dataclass(frozen=True)
class SourceRepositoryRef:
    vcs: str
    authority: str
    path: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "SourceRepositoryRef":
        if not isinstance(value, Mapping):
            raise ValueError("source repository must be a mapping")
        if set(value) - {"vcs", "authority", "path"}:
            raise ValueError("source repository contains unknown fields")
        # Verification source identity is integrity metadata, not a second
        # repository-authority model. Reuse the canonical mutation-placement
        # primitive so credentials, schemes, ports, .git suffixes and traversal
        # are normalized exactly the same way as the existing scoped runtime.
        from sentinelx_core.mutation_placement import RepositoryIdentity

        try:
            canonical = RepositoryIdentity(
                vcs=str(value.get("vcs") or ""),
                authority=str(value.get("authority") or ""),
                path=str(value.get("path") or ""),
            ).canonical
        except ValueError as exc:
            raise ValueError("source repository identity is invalid") from exc
        vcs, _, remainder = canonical.partition("://")
        authority, separator, path = remainder.partition("/")
        if not vcs or not separator or not authority or not path:
            raise ValueError("source repository identity is invalid")
        return cls(vcs=vcs, authority=authority, path=path)

    def canonical_payload(self) -> dict[str, str]:
        return {"vcs": self.vcs, "authority": self.authority, "path": self.path}

    @property
    def digest(self) -> str:
        return _sha256_bytes(_canonical_json(self.canonical_payload()))


@dataclass(frozen=True)
class SourceTransportRef:
    type: str
    revision: str
    pr_number: int | None = None

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "SourceTransportRef":
        if not isinstance(value, Mapping):
            raise ValueError("source transport must be a mapping")
        transport_type = str(value.get("type") or "").strip()
        if not transport_type:
            raise ValueError("source transport type is required")
        if transport_type == "github-pr":
            unknown = set(value) - {"type", "pr_number", "head_sha"}
            if unknown:
                raise ValueError("github-pr transport contains unknown fields")
            try:
                pr_number = int(value.get("pr_number"))
            except (TypeError, ValueError) as exc:
                raise ValueError("github-pr pr_number must be an integer") from exc
            revision = str(value.get("head_sha") or "").strip().lower()
            if pr_number <= 0 or not _GIT_SHA_RE.fullmatch(revision):
                raise ValueError("github-pr transport requires positive pr_number and 40-hex head_sha")
            return cls(type=transport_type, revision=revision, pr_number=pr_number)
        unknown = set(value) - {"type", "revision"}
        if unknown:
            raise ValueError("source transport contains unknown fields")
        revision = str(value.get("revision") or "").strip()
        if not revision:
            raise ValueError("source transport revision is required")
        return cls(type=transport_type, revision=revision)

    def canonical_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"type": self.type}
        if self.type == "github-pr":
            payload["pr_number"] = self.pr_number
            payload["head_sha"] = self.revision
        else:
            payload["revision"] = self.revision
        return payload


def _parse_entries(
    raw: Any,
    *,
    limits: VerificationResourceLimits,
    field_name: str,
    max_files: int,
    max_total_bytes: int,
) -> tuple[FileDigestEntry, ...]:
    if isinstance(raw, (str, bytes)) or not isinstance(raw, Sequence):
        raise ValueError(f"{field_name} must be a list")
    if len(raw) > max_files:
        raise ValueError(f"{field_name} exceeds the file-count bound")
    entries = [
        FileDigestEntry.from_mapping(
            item,
            limits=limits,
            field_name=f"{field_name}[{index}]",
        )
        for index, item in enumerate(raw)
    ]
    entries.sort(key=lambda item: item.path.casefold())
    keys = [entry.path.casefold() for entry in entries]
    if len(keys) != len(set(keys)):
        raise ValueError(f"{field_name} contains duplicate paths")
    if sum(entry.size for entry in entries) > max_total_bytes:
        raise ValueError(f"{field_name} exceeds the total-byte bound")
    return tuple(entries)


def _source_digest_payload(
    *,
    source_id: str,
    repository: SourceRepositoryRef,
    transport: SourceTransportRef,
    source_subpath: str,
    package_lock_sha256: str,
    files: Sequence[FileDigestEntry],
) -> dict[str, Any]:
    return {
        "schema_version": SOURCE_SNAPSHOT_SCHEMA_VERSION,
        "kind": "verification_source_snapshot",
        "source_id": source_id,
        "repository": repository.canonical_payload(),
        "transport": transport.canonical_payload(),
        "source_subpath": source_subpath,
        "package_lock_sha256": package_lock_sha256,
        "files": [entry.canonical_payload() for entry in files],
    }


@dataclass(frozen=True)
class SourceUnderTestSnapshot:
    source_id: str
    repository: SourceRepositoryRef
    transport: SourceTransportRef
    source_subpath: str
    source_manifest_digest: str
    package_lock_sha256: str
    files: tuple[FileDigestEntry, ...]

    @classmethod
    def from_manifest(
        cls,
        value: Mapping[str, Any],
        *,
        limits: VerificationResourceLimits,
    ) -> "SourceUnderTestSnapshot":
        if not isinstance(value, Mapping):
            raise ValueError("source snapshot manifest must be a mapping")
        allowed = {
            "schema_version",
            "kind",
            "source_id",
            "repository",
            "transport",
            "source_subpath",
            "source_manifest_digest",
            "package_lock_sha256",
            "files",
        }
        if set(value) - allowed:
            raise ValueError("source snapshot manifest contains unknown fields")
        if value.get("schema_version") != SOURCE_SNAPSHOT_SCHEMA_VERSION:
            raise ValueError("unsupported source snapshot schema version")
        if value.get("kind") != "verification_source_snapshot":
            raise ValueError("invalid source snapshot kind")
        source_id = validate_logical_id(value.get("source_id"), "source_id")
        repository = SourceRepositoryRef.from_mapping(value.get("repository"))
        transport = SourceTransportRef.from_mapping(value.get("transport"))
        source_subpath = normalize_relative_path(
            value.get("source_subpath"),
            "source_subpath",
            max_chars=limits.max_relative_path_chars,
        )
        package_lock = normalize_sha256(value.get("package_lock_sha256"), "package_lock_sha256")
        files = _parse_entries(
            value.get("files"),
            limits=limits,
            field_name="source files",
            max_files=limits.source_max_files,
            max_total_bytes=limits.source_max_total_bytes,
        )
        lock_entries = [entry for entry in files if entry.path == "package-lock.json"]
        if len(lock_entries) != 1 or lock_entries[0].sha256 != package_lock:
            raise ValueError("source snapshot package-lock entry does not match declared digest")
        payload = _source_digest_payload(
            source_id=source_id,
            repository=repository,
            transport=transport,
            source_subpath=source_subpath,
            package_lock_sha256=package_lock,
            files=files,
        )
        digest = _sha256_bytes(_canonical_json(payload))
        if normalize_sha256(value.get("source_manifest_digest"), "source_manifest_digest") != digest:
            raise ValueError("source snapshot manifest digest mismatch")
        return cls(
            source_id=source_id,
            repository=repository,
            transport=transport,
            source_subpath=source_subpath,
            source_manifest_digest=digest,
            package_lock_sha256=package_lock,
            files=files,
        )


def compute_source_manifest_digest(
    value: Mapping[str, Any],
    *,
    limits: VerificationResourceLimits | None = None,
) -> str:
    effective = limits or VerificationResourceLimits()
    source_id = validate_logical_id(value.get("source_id"), "source_id")
    repository = SourceRepositoryRef.from_mapping(value.get("repository"))
    transport = SourceTransportRef.from_mapping(value.get("transport"))
    source_subpath = normalize_relative_path(
        value.get("source_subpath"),
        "source_subpath",
        max_chars=effective.max_relative_path_chars,
    )
    package_lock = normalize_sha256(value.get("package_lock_sha256"), "package_lock_sha256")
    files = _parse_entries(
        value.get("files"),
        limits=effective,
        field_name="source files",
        max_files=effective.source_max_files,
        max_total_bytes=effective.source_max_total_bytes,
    )
    return _sha256_bytes(
        _canonical_json(
            _source_digest_payload(
                source_id=source_id,
                repository=repository,
                transport=transport,
                source_subpath=source_subpath,
                package_lock_sha256=package_lock,
                files=files,
            )
        )
    )


def _capsule_digest(files: Sequence[FileDigestEntry]) -> str:
    return _sha256_bytes(
        _canonical_json([entry.canonical_payload() for entry in files])
    )


@dataclass(frozen=True)
class DependencyCapsule:
    capsule_id: str
    package_lock_sha256: str
    payload_digest: str
    files: tuple[FileDigestEntry, ...]
    revision: int = DEPENDENCY_CAPSULE_SCHEMA_VERSION

    @classmethod
    def from_manifest(
        cls,
        value: Mapping[str, Any],
        *,
        limits: VerificationResourceLimits,
    ) -> "DependencyCapsule":
        if not isinstance(value, Mapping):
            raise ValueError("dependency capsule manifest must be a mapping")
        allowed = {
            "schema_version",
            "kind",
            "capsule_id",
            "package_lock_sha256",
            "payload_digest",
            "files",
        }
        if set(value) - allowed:
            raise ValueError("dependency capsule manifest contains unknown fields")
        if value.get("schema_version") != DEPENDENCY_CAPSULE_SCHEMA_VERSION:
            raise ValueError("unsupported dependency capsule schema version")
        if value.get("kind") != "node_npm_dependency_capsule":
            raise ValueError("invalid dependency capsule kind")
        capsule_id = validate_logical_id(value.get("capsule_id"), "capsule_id")
        package_lock = normalize_sha256(value.get("package_lock_sha256"), "package_lock_sha256")
        files = _parse_entries(
            value.get("files"),
            limits=limits,
            field_name="dependency files",
            max_files=limits.dependency_max_files,
            max_total_bytes=limits.dependency_max_total_bytes,
        )
        digest = _capsule_digest(files)
        if normalize_sha256(value.get("payload_digest"), "payload_digest") != digest:
            raise ValueError("dependency capsule payload digest mismatch")
        return cls(
            capsule_id=capsule_id,
            package_lock_sha256=package_lock,
            payload_digest=digest,
            files=files,
        )


def compute_dependency_payload_digest(
    files: Sequence[Mapping[str, Any]],
    *,
    limits: VerificationResourceLimits | None = None,
) -> str:
    effective = limits or VerificationResourceLimits()
    entries = _parse_entries(
        files,
        limits=effective,
        field_name="dependency files",
        max_files=effective.dependency_max_files,
        max_total_bytes=effective.dependency_max_total_bytes,
    )
    return _capsule_digest(entries)


def _iter_regular_files(root: Path) -> tuple[Path, ...]:
    if _is_reparse_or_symlink(root):
        raise ValueError("verification root must not be a reparse point")
    try:
        canonical_root = root.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValueError("verification root is unavailable") from exc
    if not canonical_root.is_dir():
        raise ValueError("verification root must be a directory")

    files: list[Path] = []
    for current, directories, names in os.walk(canonical_root, topdown=True, followlinks=False):
        current_path = Path(current)
        for name in list(directories):
            if _is_reparse_or_symlink(current_path / name):
                raise ValueError("verification tree contains a reparse directory")
        for name in names:
            item = current_path / name
            if _is_reparse_or_symlink(item) or not item.is_file():
                raise ValueError("verification tree contains a non-regular file")
            files.append(item)
    return tuple(sorted(files, key=lambda item: item.relative_to(canonical_root).as_posix().casefold()))


def _verify_files_on_disk(
    root: Path,
    entries: Sequence[FileDigestEntry],
    *,
    limits: VerificationResourceLimits,
    max_files: int,
    max_total_bytes: int,
    excluded_relative: set[str] | None = None,
) -> None:
    canonical_root = root.resolve(strict=True)
    excluded = {item.casefold() for item in (excluded_relative or set())}
    discovered: dict[str, Path] = {}
    for item in _iter_regular_files(canonical_root):
        relative = item.relative_to(canonical_root).as_posix()
        if relative.casefold() in excluded:
            continue
        normalized = normalize_relative_path(
            relative,
            "payload path",
            max_chars=limits.max_relative_path_chars,
        )
        discovered[normalized.casefold()] = item
    expected = {entry.path.casefold(): entry for entry in entries}
    if set(discovered) != set(expected):
        raise ValueError("verification payload contains missing or unexpected files")
    if len(discovered) > max_files:
        raise ValueError("verification payload exceeds the file-count bound")

    total = 0
    for key, item in discovered.items():
        entry = expected[key]
        size = item.stat().st_size
        total += size
        if size != entry.size or size > limits.max_single_file_bytes:
            raise ValueError("verification payload file size mismatch")
        if _sha256_file(item) != entry.sha256:
            raise ValueError("verification payload file digest mismatch")
    if total > max_total_bytes:
        raise ValueError("verification payload exceeds the total-byte bound")


def _load_json(path: Path, field_name: str) -> Mapping[str, Any]:
    if _is_reparse_or_symlink(path):
        raise ValueError(f"{field_name} must not be a reparse point")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{field_name} cannot be read as JSON") from exc
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must contain a JSON object")
    return value


def load_source_snapshot(
    root: Path,
    *,
    limits: VerificationResourceLimits,
    expected_manifest_sha256: str | None = None,
    expected_revision: str | None = None,
) -> SourceUnderTestSnapshot:
    snapshot = SourceUnderTestSnapshot.from_manifest(
        _load_json(root / "source-snapshot.json", "source snapshot manifest"),
        limits=limits,
    )
    if expected_manifest_sha256 is not None:
        expected = normalize_sha256(expected_manifest_sha256, "expected source manifest sha256")
        if snapshot.source_manifest_digest != expected:
            raise ValueError("source snapshot does not match expected manifest digest")
    if expected_revision is not None and snapshot.transport.revision != str(expected_revision).strip().lower():
        raise ValueError("source snapshot revision does not match expected revision")
    _verify_files_on_disk(
        root / "payload",
        snapshot.files,
        limits=limits,
        max_files=limits.source_max_files,
        max_total_bytes=limits.source_max_total_bytes,
    )
    return snapshot


def load_dependency_capsule(
    root: Path,
    *,
    limits: VerificationResourceLimits,
    expected_capsule_id: str | None = None,
) -> DependencyCapsule:
    capsule = DependencyCapsule.from_manifest(
        _load_json(root / "verification-capsule.json", "dependency capsule manifest"),
        limits=limits,
    )
    if expected_capsule_id is not None:
        if capsule.capsule_id != validate_logical_id(expected_capsule_id, "expected capsule id"):
            raise ValueError("dependency capsule id mismatch")
    _verify_files_on_disk(
        root,
        capsule.files,
        limits=limits,
        max_files=limits.dependency_max_files,
        max_total_bytes=limits.dependency_max_total_bytes,
        excluded_relative={"verification-capsule.json"},
    )
    return capsule


@dataclass(frozen=True)
class ToolchainManifest:
    kind: str
    node_relative: str
    npm_cli_relative: str
    files: tuple[FileDigestEntry, ...]
    toolchain_digest: str
    contract_revision: int = TOOLCHAIN_CONTRACT_REVISION


def build_toolchain_manifest(profile: NodeNpmVerificationProfile) -> ToolchainManifest:
    canonical_root = profile.toolchain_root.resolve(strict=True)
    profile.resolve_node(require_exists=True)
    profile.resolve_npm_cli(require_exists=True)
    entries: list[FileDigestEntry] = []
    for item in _iter_regular_files(canonical_root):
        relative = normalize_relative_path(
            item.relative_to(canonical_root).as_posix(),
            "toolchain path",
            max_chars=profile.limits.max_relative_path_chars,
        )
        size = item.stat().st_size
        if size > profile.limits.max_single_file_bytes:
            raise ValueError("toolchain member exceeds the per-file bound")
        entries.append(FileDigestEntry(relative, size, _sha256_file(item)))
    entries.sort(key=lambda entry: entry.path.casefold())
    payload = {
        "contract_revision": TOOLCHAIN_CONTRACT_REVISION,
        "kind": profile.kind,
        "node_relative": profile.node_relative,
        "npm_cli_relative": profile.npm_cli_relative,
        "files": [entry.canonical_payload() for entry in entries],
    }
    return ToolchainManifest(
        kind=profile.kind,
        node_relative=profile.node_relative,
        npm_cli_relative=profile.npm_cli_relative,
        files=tuple(entries),
        toolchain_digest=_sha256_bytes(_canonical_json(payload)),
    )


@dataclass(frozen=True)
class VerificationRequest:
    profile: str
    source_id: str
    source_manifest_sha256: str
    source_revision: str
    capsule_id: str
    package_lock_sha256: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "VerificationRequest":
        if not isinstance(value, Mapping):
            raise ValueError("verification request must be a mapping")
        allowed = {
            "profile",
            "source_id",
            "source_manifest_sha256",
            "source_revision",
            "capsule_id",
            "package_lock_sha256",
        }
        if set(value) != allowed:
            raise ValueError("verification request must contain only the bounded V1 fields")
        source_revision = str(value.get("source_revision") or "").strip().lower()
        if not source_revision:
            raise ValueError("source_revision is required")
        return cls(
            profile=validate_profile_id(value.get("profile")),
            source_id=validate_logical_id(value.get("source_id"), "source_id"),
            source_manifest_sha256=normalize_sha256(
                value.get("source_manifest_sha256"),
                "source_manifest_sha256",
            ),
            source_revision=source_revision,
            capsule_id=validate_logical_id(value.get("capsule_id"), "capsule_id"),
            package_lock_sha256=normalize_sha256(
                value.get("package_lock_sha256"),
                "package_lock_sha256",
            ),
        )


@dataclass(frozen=True)
class VerificationAdmission:
    profile_id: str
    profile_revision: int
    source: SourceUnderTestSnapshot
    capsule: DependencyCapsule
    toolchain: ToolchainManifest
    expected_package_lock_sha256: str
    resource_limits_digest: str
    network_mode: str = "none"


def build_verification_admission(
    *,
    profile: NodeNpmVerificationProfile,
    request: VerificationRequest,
    source: SourceUnderTestSnapshot,
    capsule: DependencyCapsule,
    toolchain: ToolchainManifest,
) -> VerificationAdmission:
    if request.profile != profile.profile_id:
        raise ValueError("verification request profile mismatch")
    if request.source_id != source.source_id:
        raise ValueError("verification request source id mismatch")
    if request.source_manifest_sha256 != source.source_manifest_digest:
        raise ValueError("verification request source manifest mismatch")
    if request.source_revision != source.transport.revision:
        raise ValueError("verification request source revision mismatch")
    if request.capsule_id != capsule.capsule_id:
        raise ValueError("verification request capsule id mismatch")
    if not (
        request.package_lock_sha256
        == source.package_lock_sha256
        == capsule.package_lock_sha256
    ):
        raise ValueError("verification package-lock digests do not match")
    if toolchain.kind != profile.kind:
        raise ValueError("verification toolchain kind mismatch")
    return VerificationAdmission(
        profile_id=profile.profile_id,
        profile_revision=profile.contract_revision,
        source=source,
        capsule=capsule,
        toolchain=toolchain,
        expected_package_lock_sha256=request.package_lock_sha256,
        resource_limits_digest=profile.limits.digest,
    )
