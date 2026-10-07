"""Provider-owned DevForge execution-workspace source role and capsule (PR-014 S02).

D1-D4 of Plan R5:

- D1: the canonical source checkout role is derived from the current Host
  DevForge workspace binding; a caller never supplies a source path.
- D2: materialization input is bounded to an exact ``refs/heads/<logical>``
  ref and an immutable full commit sha, both independently verified against
  the remote and the verified local object store.
- D3: user-scoped Git is reused only as the provider transport.  The caller
  cannot supply Git argv or remote URLs; credentials never leave the active
  user Git context and prompts stay disabled.
- D4: the provider-private immutable source capsule is a deterministic,
  digest-sealed, durable input for the contained materializer.  It contains
  no credential material and no caller-controlled absolute paths.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import zlib
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any, Iterator, Sequence
from urllib.parse import urlsplit

from sentinelx_core.devforge_workspace_placement import _repository_segments
from sentinelx_core.mutation_placement import RepositoryIdentity
from sentinelx_core.policy import Policy
SOURCE_ROLE_POLICY = "devforge-execution-workspace-source-v1"
CAPSULE_MANIFEST_VERSION = 1
SUPPORTED_OBJECT_FORMATS = ("sha1",)
ALLOWED_TREE_MODES = frozenset({"100644", "100755"})
ALLOWED_TREE_TYPES = frozenset({"blob"})
MAX_CAPSULE_FILES = 20000
MAX_CAPSULE_TOTAL_BYTES = 512 * 1024 * 1024
MAX_CAPSULE_FILE_BYTES = 32 * 1024 * 1024
GIT_TIMEOUT_SECONDS = 120.0

_REF_PREFIX = "refs/heads/"
_SAFE_LOGICAL_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")
_COMMIT_SHA = re.compile(r"^[0-9a-f]{40}$")


class DevforgeSourceError(RuntimeError):
    code = "WorkspaceSourceBlocked"


class SourceRoleUnavailable(DevforgeSourceError):
    code = "SourceRoleUnavailable"


class SourceIdentityMismatch(DevforgeSourceError):
    code = "SourceIdentityMismatch"


class SourceAcquisitionBlocked(DevforgeSourceError):
    code = "SourceAcquisitionBlocked"


class SourceCapsuleError(DevforgeSourceError):
    code = "SourceCapsuleError"


def _digest(value: object) -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _iso_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def validate_source_binding(expected_ref: str, expected_commit: str) -> tuple[str, str]:
    """Fail closed unless the binding is an exact logical branch + full sha."""
    ref = str(expected_ref or "").strip()
    commit = str(expected_commit or "").strip()
    if not ref.startswith(_REF_PREFIX):
        raise SourceIdentityMismatch("expected_ref must be refs/heads/<logical branch>")
    logical = ref[len(_REF_PREFIX):]
    if not logical or not _SAFE_LOGICAL_REF.match(logical) or ".." in logical or logical.endswith("/"):
        raise SourceIdentityMismatch("expected_ref logical branch is not a safe V1 branch name")
    if not _COMMIT_SHA.match(commit):
        raise SourceIdentityMismatch("expected_commit must be a full lowercase hex sha1")
    return ref, logical


def normalize_origin_identity(url: str) -> tuple[str, str]:
    """Normalize a Git remote URL to (host, owner/repo) identity tokens."""
    text = str(url or "").strip()
    if text.startswith("git@"):
        text = "ssh://" + text.replace(":", "/", 1)
    parsed = urlsplit(text)
    host = (parsed.hostname or "").lower()
    parts = tuple(part for part in parsed.path.split("/") if part)
    if len(parts) < 2:
        raise SourceIdentityMismatch("origin URL does not resolve to owner/repository")
    owner, name = parts[-2], parts[-1]
    if name.endswith(".git"):
        name = name[: -len(".git")]
    return host, f"{owner}/{name}"


def repository_identity_tokens(repository: RepositoryIdentity) -> tuple[str, str]:
    parsed = urlsplit(repository.canonical)
    host = (parsed.hostname or "").lower()
    parts = tuple(part for part in parsed.path.split("/") if part)
    if len(parts) != 2:
        raise SourceIdentityMismatch(
            "DevForge V1 repository identity must resolve to exactly owner/repository"
        )
    return host, f"{parts[0]}/{parts[1]}"


def _host_devforge_roots(policy: Policy) -> tuple[Path, Path]:
    """D1 derivation: workspace_root and the repository checkout root."""
    location = policy.locations.get("devforge_workspace_root")
    if location is None:
        raise SourceRoleUnavailable("locations.devforge_workspace_root is not configured")
    text = str(location.path or "").strip()
    if not text:
        raise SourceRoleUnavailable("locations.devforge_workspace_root is empty")
    root = Path(text).expanduser()
    if not root.is_absolute():
        raise SourceRoleUnavailable("locations.devforge_workspace_root must be absolute")
    workspace_root = root.resolve(strict=False)
    repository_root = (workspace_root / "repos").resolve(strict=False)
    return workspace_root, repository_root


@dataclass(frozen=True)
class SourceRoleBinding:
    """Verified canonical source checkout role (D1).  Host evidence only."""

    repository: str
    checkout_root: str
    origin_url: str
    branch: str
    head_commit: str
    clean: bool
    verified_at: str


@dataclass(frozen=True)
class SourceCapsule:
    """Provider-private immutable materialization input (D4)."""

    capsule_id: str
    repository: str
    expected_ref: str
    logical_branch: str
    expected_commit: str
    object_format: str
    manifest_digest: str
    file_count: int
    total_bytes: int
    created_at: str
    _root: Path

    @property
    def root(self) -> Path:
        return self._root

    def to_json(self) -> dict[str, Any]:
        body = asdict(self)
        body["_root"] = str(self._root)
        return body


async def _user_git(root: Path, *args: str) -> str:
    from sentinelx_core import user_git

    try:
        returncode, out, err = await user_git.run_user_scoped_git(
            root, *args, timeout=GIT_TIMEOUT_SECONDS
        )
    except user_git.UserScopedGitError as exc:
        raise SourceAcquisitionBlocked(f"{exc.code}: {exc}") from exc
    if returncode != 0:
        reason = user_git.classify_result(returncode, err)
        raise SourceAcquisitionBlocked(
            f"git {' '.join(args[:2])} failed: {reason or f'exit {returncode}'}"
        )
    return out.decode("utf-8", "replace")


async def resolve_canonical_source_role(
    policy: Policy,
    repository: RepositoryIdentity,
) -> SourceRoleBinding:
    """Verify the Host-derived canonical source checkout (D1/D3 read-only)."""
    host, repo_path = repository_identity_tokens(repository)
    _, repository_root = _host_devforge_roots(policy)
    owner, name = _repository_segments(repository)
    checkout = (repository_root / owner / name).resolve(strict=False)
    if checkout == repository_root or not checkout.is_relative_to(repository_root):
        raise SourceRoleUnavailable("derived source checkout escaped the repository root")
    if not checkout.is_dir():
        raise SourceRoleUnavailable("canonical source checkout does not exist")

    toplevel = (await _user_git(checkout, "rev-parse", "--show-toplevel")).strip()
    if os.path.normcase(Path(toplevel).resolve(strict=False)) != os.path.normcase(checkout):
        raise SourceRoleUnavailable("source checkout is not a repository toplevel")
    branch = (await _user_git(checkout, "rev-parse", "--abbrev-ref", "HEAD")).strip()
    if branch != "main":
        raise SourceRoleUnavailable("source checkout is not on canonical main")
    status = (await _user_git(checkout, "status", "--porcelain")).strip()
    if status:
        raise SourceRoleUnavailable("source checkout working tree is not clean")
    origin = (await _user_git(checkout, "remote", "get-url", "origin")).strip()
    origin_host, origin_path = normalize_origin_identity(origin)
    if (origin_host, origin_path) != (host, repo_path):
        raise SourceRoleUnavailable("source checkout origin does not normalize to the admitted repository")
    head = (await _user_git(checkout, "rev-parse", "HEAD")).strip().lower()
    if not _COMMIT_SHA.match(head):
        raise SourceIdentityMismatch("source HEAD is not a full commit sha")

    return SourceRoleBinding(
        repository=repository.canonical,
        checkout_root=str(checkout),
        origin_url=origin,
        branch=branch,
        head_commit=head,
        clean=True,
        verified_at=_iso_now(),
    )


async def verify_source_identity(
    role: SourceRoleBinding,
    expected_ref: str,
    expected_commit: str,
) -> tuple[str, str]:
    """Independently verify remote ref -> commit and local object identity (D2)."""
    ref, logical = validate_source_binding(expected_ref, expected_commit)
    checkout = Path(role.checkout_root)

    remote_lines = (await _user_git(checkout, "ls-remote", "origin", ref)).splitlines()
    remote_shas = {
        line.split(maxsplit=1)[0].strip().lower()
        for line in remote_lines
        if line.strip()
    }
    if expected_commit not in remote_shas:
        raise SourceIdentityMismatch("remote expected_ref does not resolve to expected_commit")

    object_format = (await _user_git(checkout, "rev-parse", "--show-object-format")).strip()
    if object_format not in SUPPORTED_OBJECT_FORMATS:
        raise SourceIdentityMismatch(f"unsupported repository object format: {object_format}")

    resolved = (await _user_git(checkout, "rev-parse", f"{expected_commit}^{{commit}}")).strip().lower()
    if resolved != expected_commit:
        raise SourceIdentityMismatch("local object store does not contain expected_commit")
    object_type = (await _user_git(checkout, "cat-file", "-t", expected_commit)).strip()
    if object_type != "commit":
        raise SourceIdentityMismatch("expected_commit object is not a commit")
    return logical, object_format


def _write_durable_bytes(path: Path, payload: bytes) -> None:
    temp = path.parent / f".{path.name}.{secrets.token_hex(6)}.tmp"
    try:
        with temp.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        try:
            temp.unlink(missing_ok=True)
        except OSError:
            pass


def _iter_ls_tree(raw: bytes) -> Iterator[tuple[str, str, str, str]]:
    for record in raw.split(b"\x00"):
        if not record:
            continue
        meta, _, path_bytes = record.partition(b"\t")
        meta_text = meta.decode("ascii")
        mode, obj_type, sha = meta_text.split(maxsplit=2)
        path = path_bytes.decode("utf-8")
        yield mode, obj_type, sha, path


def _safe_worktree_path(raw: str) -> PurePosixPath:
    pure = PurePosixPath(raw)
    if pure.is_absolute() or raw.startswith("/") or ":" in raw:
        raise SourceCapsuleError("capsule entry path is absolute")
    if str(pure) != raw:
        raise SourceCapsuleError("capsule entry path is not in canonical relative form")
    if any(part in ("", ".", "..") for part in pure.parts):
        raise SourceCapsuleError("capsule entry path is not a safe relative path")
    return pure


def _load_loose_object(source: Path, sha: str) -> tuple[str, bytes]:
    object_path = source / ".git" / "objects" / sha[:2] / sha[2:]
    try:
        raw = object_path.read_bytes()
    except OSError as exc:
        raise SourceAcquisitionBlocked(f"cannot read source object {sha}: {exc}") from exc
    inflated = zlib.decompress(raw)
    header, _, payload = inflated.partition(b"\x00")
    obj_type, _, size_text = header.decode("ascii").partition(" ")
    if int(size_text) != len(payload):
        raise SourceAcquisitionBlocked(f"source object {sha} has an invalid size header")
    return obj_type, payload


def _write_loose_object(objects_dir: Path, obj_type: str, payload: bytes) -> str:
    header = f"{obj_type} {len(payload)}\0".encode("ascii")
    sha = hashlib.sha1(header + payload).hexdigest()
    directory = objects_dir / sha[:2]
    directory.mkdir(parents=True, exist_ok=True)
    _write_durable_bytes(directory / sha[2:], zlib.compress(header + payload))
    return sha


async def build_source_capsule(
    state_root: Path,
    role: SourceRoleBinding,
    expected_ref: str,
    expected_commit: str,
) -> SourceCapsule:
    """Build (or reuse) the provider-private immutable source capsule (D4)."""
    logical, object_format = await verify_source_identity(role, expected_ref, expected_commit)
    checkout = Path(role.checkout_root)

    capsule_id = "dsc_" + _digest(
        {
            "policy": SOURCE_ROLE_POLICY,
            "repository": role.repository,
            "expected_ref": expected_ref,
            "expected_commit": expected_commit,
        }
    )[:32]
    capsule_root = state_root.resolve(strict=False) / "devforge-source-capsules" / capsule_id
    manifest_path = capsule_root / "manifest.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise SourceCapsuleError(f"existing capsule manifest is unreadable: {exc}") from exc
        stored_body = {key: value for key, value in manifest.items() if key != "manifest_digest"}
        if manifest.get("manifest_digest") != _digest(stored_body):
            raise SourceCapsuleError("existing capsule manifest digest changed")
        existing = SourceCapsule(
            capsule_id=manifest["capsule_id"],
            repository=manifest["repository"],
            expected_ref=manifest["expected_ref"],
            logical_branch=manifest["logical_branch"],
            expected_commit=manifest["expected_commit"],
            object_format=manifest["object_format"],
            manifest_digest=manifest["manifest_digest"],
            file_count=int(manifest["file_count"]),
            total_bytes=int(manifest["total_bytes"]),
            created_at=manifest["created_at"],
            _root=capsule_root,
        )
        return existing

    entries: list[dict[str, Any]] = []
    object_shas: list[str] = []
    total_bytes = 0
    capsule_root.mkdir(parents=True, exist_ok=True)
    try:
        listing = (
            await _user_git(checkout, "ls-tree", "-r", "-t", "-z", expected_commit)
        ).encode("utf-8")
        seen_trees: set[str] = set()
        for mode, obj_type, sha, path in _iter_ls_tree(listing):
            if obj_type == "tree":
                seen_trees.add(sha)
                continue
            if obj_type not in ALLOWED_TREE_TYPES or mode not in ALLOWED_TREE_MODES:
                raise SourceCapsuleError(
                    f"unsupported tree entry {mode}/{obj_type} at {path!r}; V1 fails closed"
                )
            _safe_worktree_path(path)
            obj_type_payload, payload = _load_loose_object(checkout, sha)
            if obj_type_payload != "blob":
                raise SourceCapsuleError(f"source object {sha} is not a blob")
            if len(payload) > MAX_CAPSULE_FILE_BYTES:
                raise SourceCapsuleError("capsule file exceeds the per-file ceiling")
            total_bytes += len(payload)
            if total_bytes > MAX_CAPSULE_TOTAL_BYTES:
                raise SourceCapsuleError("capsule exceeds the total-size ceiling")
            entries.append(
                {
                    "path": path,
                    "mode": mode,
                    "sha": sha,
                    "size": len(payload),
                }
            )
            object_shas.append(sha)
        if len(entries) > MAX_CAPSULE_FILES:
            raise SourceCapsuleError("capsule exceeds the file-count ceiling")
        if not entries:
            raise SourceCapsuleError("source commit has no worktree files")

        commit_type, commit_payload = _load_loose_object(checkout, expected_commit)
        if commit_type != "commit":
            raise SourceCapsuleError("source commit object is not a commit")
        object_shas.append(expected_commit)
        for tree_sha in sorted(seen_trees):
            tree_type, tree_payload = _load_loose_object(checkout, tree_sha)
            if tree_type != "tree":
                raise SourceCapsuleError(f"source object {tree_sha} is not a tree")
            object_shas.append(tree_sha)

        objects_dir = capsule_root / "objects"
        written: dict[str, str] = {}
        for sha in sorted(set(object_shas)):
            obj_type, payload = (
                (commit_type, commit_payload)
                if sha == expected_commit
                else _lookup_object(entries, checkout, sha)
            )
            written[sha] = _write_loose_object(objects_dir, obj_type, payload)
            if written[sha] != sha:
                raise SourceCapsuleError(f"object {sha} content digest mismatch after export")

        entries.sort(key=lambda entry: entry["path"])
        manifest: dict[str, Any] = {
            "manifest_version": CAPSULE_MANIFEST_VERSION,
            "policy": SOURCE_ROLE_POLICY,
            "capsule_id": capsule_id,
            "repository": role.repository,
            "origin_url": role.repository,
            "expected_ref": expected_ref,
            "logical_branch": logical,
            "expected_commit": expected_commit,
            "object_format": object_format,
            "entries": entries,
            "objects": sorted(set(object_shas)),
            "file_count": len(entries),
            "total_bytes": total_bytes,
            "created_at": _iso_now(),
        }
        manifest_digest = _digest(manifest)
        manifest["manifest_digest"] = manifest_digest
        _write_durable_bytes(
            manifest_path,
            (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8"),
        )
        persisted = json.loads(manifest_path.read_text(encoding="utf-8"))
        if persisted != manifest:
            raise SourceCapsuleError("capsule manifest read-back changed")
    except Exception:
        for leftover in sorted(capsule_root.rglob("*"), reverse=True):
            try:
                if leftover.is_file():
                    leftover.unlink()
            except OSError:
                pass
        raise

    return SourceCapsule(
        capsule_id=capsule_id,
        repository=role.repository,
        expected_ref=expected_ref,
        logical_branch=logical,
        expected_commit=expected_commit,
        object_format=object_format,
        manifest_digest=manifest_digest,
        file_count=len(entries),
        total_bytes=total_bytes,
        created_at=manifest["created_at"],
        _root=capsule_root,
    )


def _lookup_object(
    entries: Sequence[dict[str, Any]], checkout: Path, sha: str
) -> tuple[str, bytes]:
    """Read one object payload from the verified source object store."""
    return _load_loose_object(checkout, sha)
