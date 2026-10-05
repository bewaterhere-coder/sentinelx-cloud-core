"""Exact repository source acquisition and AppContainer materialization.

S02 deliberately keeps three authority domains separate:

* credential-bearing network Git runs only through ``run_user_scoped_git``;
* provider-owned source snapshots are immutable, path-free durable state;
* repository bytes enter the exact mutation workspace only from a fixed
  provider materializer running inside the existing AppContainer + Job.

No API in this module accepts a Host destination/source/cache path, Git argv,
credential control, sandbox identity, or operation class from the caller.
"""
from __future__ import annotations

import asyncio
import ctypes
import hashlib
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any, Protocol

from sentinelx_core.executor import HandlerError
from sentinelx_core.mutation_audit import (
    EVENT_FINISHED,
    FINISH_STATES,
    JOURNAL_VERSION,
    MutationAuditBinding,
    MutationAuditIdentityMismatch,
    MutationAuditJournal,
    MutationAuthorityEvidence,
    MutationFinishClosureEvidence,
    MutationProcessIntent,
)
from sentinelx_core.mutation_placement import RepositoryIdentity, SemanticIdentity
from sentinelx_core.mutation_sandbox import build_mutation_sandbox
from sentinelx_core.mutation_scope import MutationScopeRecord, MutationScopeStore
from sentinelx_core.policy import Policy
from sentinelx_core.repository_transaction import (
    RepositoryRefResolver,
    RepositoryTransactionError,
    RepositoryTransactionRecord,
    RepositoryTransactionStore,
    _exclusive_file_lock as _transaction_lock,
)
from sentinelx_core.request_context import MutationLineage, RequestContext
from sentinelx_core.user_git import UserScopedGitError, classify_result, redact_git_output, run_user_scoped_git
from sentinelx_core.windows_mutation_sandbox import (
    _current_process_sid,
    _dacl_entries,
    _remove_runtime_read,
    _run_icacls,
    _set_exact_acl,
    final_executable_path,
    requested_mutation_identity,
)

SNAPSHOT_VERSION = 1
CONTROL_NAMESPACE = ".sentinelx-control"
MAX_SOURCE_ENTRIES = 20_000
MAX_SOURCE_FILE_BYTES = 128 * 1024 * 1024
MAX_SOURCE_TOTAL_BYTES = 512 * 1024 * 1024
MAX_SOURCE_PATH_UTF8_BYTES = 1024
MATERIALIZE_TIMEOUT_SECONDS = 120

_RESERVED_WINDOWS_NAMES = frozenset(
    {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)), *(f"lpt{i}" for i in range(1, 10))}
)
_HOST_RE = re.compile(r"^[A-Za-z0-9.-]+$")


class RepositoryMaterializationError(RuntimeError):
    code = "RepositoryMaterializationError"


class RepositorySourceUnavailable(RepositoryMaterializationError):
    code = "RepositorySourceUnavailable"


class RepositorySourceUnsafe(RepositoryMaterializationError):
    code = "RepositorySourceUnsafe"


class RepositorySourceCorrupt(RepositoryMaterializationError):
    code = "RepositorySourceCorrupt"


class RepositoryMaterializationConflict(RepositoryMaterializationError):
    code = "RepositoryMaterializationConflict"


class RepositoryMaterializationFailed(RepositoryMaterializationError):
    code = "RepositoryMaterializationFailed"


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _iso(value: datetime | None = None) -> str:
    value = value or _utcnow()
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _json_digest(value: object) -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_source_path(value: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise RepositorySourceUnsafe("source path must be a non-empty UTF-8 string")
    try:
        encoded = value.encode("utf-8", "strict")
    except UnicodeError as exc:
        raise RepositorySourceUnsafe("source path is not valid UTF-8") from exc
    if len(encoded) > MAX_SOURCE_PATH_UTF8_BYTES:
        raise RepositorySourceUnsafe("source path exceeds V1 length ceiling")
    path = PurePosixPath(value)
    if path.is_absolute() or value.startswith(("/", "\\")):
        raise RepositorySourceUnsafe("absolute source paths are forbidden")
    parts = path.parts
    if not parts or any(part in ("", ".", "..") for part in parts):
        raise RepositorySourceUnsafe("source path contains traversal or empty components")
    if parts[0].casefold() == CONTROL_NAMESPACE.casefold():
        raise RepositorySourceUnsafe("repository collides with provider control namespace")
    for part in parts:
        if any(ord(ch) < 32 for ch in part) or ":" in part or "\\" in part:
            raise RepositorySourceUnsafe("source path contains Windows-unsafe syntax")
        if part.endswith((" ", ".")):
            raise RepositorySourceUnsafe("source path has a trailing dot/space component")
        base = part.split(".", 1)[0].casefold()
        if base in _RESERVED_WINDOWS_NAMES:
            raise RepositorySourceUnsafe("source path contains a reserved Windows device name")
    return path.as_posix()


def _safe_symlink_target(path: str, target: str) -> str:
    if not isinstance(target, str) or not target or "\x00" in target:
        raise RepositorySourceUnsafe("symlink target must be a non-empty UTF-8 string")
    if target.startswith(("/", "\\")) or ":" in target or "\\" in target:
        raise RepositorySourceUnsafe("absolute/drive/UNC symlink targets are forbidden")
    target_path = PurePosixPath(target)
    stack = list(PurePosixPath(path).parent.parts)
    for part in target_path.parts:
        if part in ("", "."):
            continue
        if part == "..":
            if not stack:
                raise RepositorySourceUnsafe("symlink target escapes repository root")
            stack.pop()
            continue
        if any(ord(ch) < 32 for ch in part):
            raise RepositorySourceUnsafe("symlink target contains unsafe syntax")
        stack.append(part)
    if not stack:
        raise RepositorySourceUnsafe("symlink target resolves outside/at empty repository root")
    return target


@dataclass(frozen=True)
class SourceEntry:
    path: str
    kind: str
    mode: str
    size: int
    sha256: str | None = None
    link_target: str | None = None

    def manifest_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "path": self.path,
            "kind": self.kind,
            "mode": self.mode,
            "size": self.size,
        }
        if self.sha256 is not None:
            result["sha256"] = self.sha256
        if self.link_target is not None:
            result["link_target"] = self.link_target
        return result


@dataclass(frozen=True)
class RepositorySourceSnapshot:
    snapshot_id: str
    transaction_id: str
    source_sha: str
    tree_digest: str
    manifest_digest: str
    entry_count: int
    total_file_bytes: int
    created_at: str
    _root: Path

    @property
    def manifest_path(self) -> Path:
        return self._root / "manifest.json"

    @property
    def content_root(self) -> Path:
        return self._root / "content"

    def project(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "source_sha": self.source_sha,
            "tree_digest": self.tree_digest,
            "manifest_digest": self.manifest_digest,
            "entry_count": self.entry_count,
            "total_file_bytes": self.total_file_bytes,
            "created_at": self.created_at,
        }


class RepositorySourceSnapshotStore:
    """Provider-owned immutable source manifests/content keyed by transaction."""

    def __init__(self, state_root: Path) -> None:
        self.root = state_root.resolve(strict=False) / "repository-source-snapshots"
        self.root.mkdir(parents=True, exist_ok=True)

    def _snapshot_root(self, transaction_id: str) -> Path:
        if not re.fullmatch(r"rtx_[A-Za-z0-9_-]+", transaction_id):
            raise RepositorySourceUnsafe("invalid provider transaction identifier")
        return self.root / transaction_id

    @staticmethod
    def _manifest(entries: Iterable[SourceEntry], source_sha: str, transaction_id: str) -> dict[str, Any]:
        values = [entry.manifest_dict() for entry in entries]
        return {
            "version": SNAPSHOT_VERSION,
            "transaction_id": transaction_id,
            "source_sha": source_sha.lower(),
            "entries": values,
            "tree_digest": _json_digest(values),
        }

    def seal(
        self,
        *,
        transaction_id: str,
        source_sha: str,
        entries: list[tuple[str, str, str, bytes | str | None]],
    ) -> RepositorySourceSnapshot:
        """Seal validated Git tree material into broker-only regular files.

        ``entries`` items are ``(path, kind, mode, payload)``. File payloads are
        bytes; symlink payloads are their textual Git blob target; directories
        carry ``None``. No symlink/reparse point is created in the snapshot.
        """
        final_root = self._snapshot_root(transaction_id)
        if final_root.exists():
            return self.load_verified(transaction_id, expected_source_sha=source_sha)
        if len(entries) > MAX_SOURCE_ENTRIES:
            raise RepositorySourceUnsafe("source entry count exceeds V1 ceiling")

        normalized: list[SourceEntry] = []
        seen: set[str] = set()
        total = 0
        for raw_path, kind, mode, payload in entries:
            path = _safe_source_path(raw_path)
            folded = path.casefold()
            if folded in seen:
                raise RepositorySourceUnsafe("case-insensitive source path collision")
            seen.add(folded)
            if kind == "directory":
                if mode != "040000" or payload is not None:
                    raise RepositorySourceUnsafe("invalid Git directory entry")
                normalized.append(SourceEntry(path, kind, mode, 0))
                continue
            if kind == "symlink":
                if mode != "120000" or not isinstance(payload, str):
                    raise RepositorySourceUnsafe("invalid Git symlink entry")
                target = _safe_symlink_target(path, payload)
                raw = target.encode("utf-8", "strict")
                if len(raw) > MAX_SOURCE_FILE_BYTES:
                    raise RepositorySourceUnsafe("symlink target exceeds V1 ceiling")
                total += len(raw)
                normalized.append(
                    SourceEntry(path, kind, mode, len(raw), _sha256(raw), target)
                )
                continue
            if kind != "file" or mode not in {"100644", "100755"} or not isinstance(payload, bytes):
                raise RepositorySourceUnsafe("unsupported Git tree entry type/mode")
            if len(payload) > MAX_SOURCE_FILE_BYTES:
                raise RepositorySourceUnsafe("source file exceeds V1 per-file ceiling")
            total += len(payload)
            normalized.append(SourceEntry(path, kind, mode, len(payload), _sha256(payload)))
        if total > MAX_SOURCE_TOTAL_BYTES:
            raise RepositorySourceUnsafe("source bytes exceed V1 total ceiling")

        normalized.sort(key=lambda item: (item.path.count("/"), item.path.casefold(), item.kind))
        manifest = self._manifest(normalized, source_sha, transaction_id)
        manifest_bytes = (
            json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n"
        ).encode("utf-8")
        manifest_digest = _sha256(manifest_bytes)
        temp = self.root / f".{transaction_id}.{secrets.token_hex(8)}.tmp"
        content_root = temp / "content"
        try:
            temp.mkdir(parents=False, exist_ok=False)
            if sys.platform == "win32":
                _set_exact_acl(temp, _current_process_sid(), None)
            content_root.mkdir()
            payloads = {(_safe_source_path(p), k): value for p, k, _m, value in entries}
            for entry in normalized:
                target = content_root / Path(*PurePosixPath(entry.path).parts)
                if entry.kind == "directory":
                    target.mkdir(parents=True, exist_ok=True)
                elif entry.kind == "file":
                    target.parent.mkdir(parents=True, exist_ok=True)
                    raw = payloads[(entry.path, "file")]
                    assert isinstance(raw, bytes)
                    with target.open("xb") as handle:
                        handle.write(raw)
                        handle.flush()
                        os.fsync(handle.fileno())
                    try:
                        target.chmod(0o555 if entry.mode == "100755" else 0o444)
                    except OSError:
                        pass
                else:
                    # Git symlink bytes live only in the sealed manifest. This
                    # prevents the provider snapshot itself from becoming a
                    # reparse/traversal primitive.
                    target.parent.mkdir(parents=True, exist_ok=True)
            with (temp / "manifest.json").open("xb") as handle:
                handle.write(manifest_bytes)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp, final_root)
        except Exception:
            shutil.rmtree(temp, ignore_errors=True)
            raise
        return self.load_verified(transaction_id, expected_source_sha=source_sha)

    def load_verified(
        self,
        transaction_id: str,
        *,
        expected_source_sha: str | None = None,
    ) -> RepositorySourceSnapshot:
        root = self._snapshot_root(transaction_id)
        manifest_path = root / "manifest.json"
        try:
            raw = manifest_path.read_bytes()
            manifest = json.loads(raw.decode("utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise RepositorySourceCorrupt(f"cannot read sealed source manifest: {exc}") from exc
        if manifest.get("version") != SNAPSHOT_VERSION or manifest.get("transaction_id") != transaction_id:
            raise RepositorySourceCorrupt("sealed source manifest identity/version mismatch")
        source_sha = str(manifest.get("source_sha") or "").lower()
        if expected_source_sha is not None and source_sha != expected_source_sha.lower():
            raise RepositorySourceCorrupt("sealed source SHA differs from transaction authority")
        raw_entries = manifest.get("entries")
        if not isinstance(raw_entries, list) or len(raw_entries) > MAX_SOURCE_ENTRIES:
            raise RepositorySourceCorrupt("sealed source manifest entries are malformed")
        if manifest.get("tree_digest") != _json_digest(raw_entries):
            raise RepositorySourceCorrupt("sealed source tree digest mismatch")

        total = 0
        seen: set[str] = set()
        for raw_entry in raw_entries:
            if not isinstance(raw_entry, dict):
                raise RepositorySourceCorrupt("sealed source entry is malformed")
            path = _safe_source_path(str(raw_entry.get("path") or ""))
            if path.casefold() in seen:
                raise RepositorySourceCorrupt("sealed source case-fold collision")
            seen.add(path.casefold())
            kind = raw_entry.get("kind")
            if kind == "directory":
                continue
            size = raw_entry.get("size")
            if isinstance(size, bool) or not isinstance(size, int) or size < 0:
                raise RepositorySourceCorrupt("sealed source entry size is invalid")
            total += size
            if kind == "file":
                file_path = root / "content" / Path(*PurePosixPath(path).parts)
                try:
                    data = file_path.read_bytes()
                except OSError as exc:
                    raise RepositorySourceCorrupt(f"sealed source file is unavailable: {path}") from exc
                if len(data) != size or _sha256(data) != raw_entry.get("sha256"):
                    raise RepositorySourceCorrupt(f"sealed source file digest mismatch: {path}")
            elif kind == "symlink":
                target = _safe_symlink_target(path, str(raw_entry.get("link_target") or ""))
                data = target.encode("utf-8")
                if len(data) != size or _sha256(data) != raw_entry.get("sha256"):
                    raise RepositorySourceCorrupt(f"sealed symlink digest mismatch: {path}")
            else:
                raise RepositorySourceCorrupt("sealed source entry kind is unsupported")
        if total > MAX_SOURCE_TOTAL_BYTES:
            raise RepositorySourceCorrupt("sealed source exceeds total byte ceiling")
        return RepositorySourceSnapshot(
            snapshot_id=f"rss_{_sha256(raw)[:24]}",
            transaction_id=transaction_id,
            source_sha=source_sha,
            tree_digest=str(manifest["tree_digest"]),
            manifest_digest=_sha256(raw),
            entry_count=len(raw_entries),
            total_file_bytes=total,
            created_at=_iso(datetime.fromtimestamp(manifest_path.stat().st_mtime, tz=UTC)),
            _root=root,
        )


class SourceBroker(Protocol):
    async def acquire(
        self,
        repository: RepositoryIdentity,
        transaction: RepositoryTransactionRecord,
    ) -> RepositorySourceSnapshot: ...


def _repository_transport_url(repository: RepositoryIdentity) -> str:
    if repository.vcs.casefold() != "git":
        raise RepositorySourceUnavailable("repository source broker supports Git only in V1")
    authority = repository.authority.strip().lower()
    if not _HOST_RE.fullmatch(authority) or ".." in authority:
        raise RepositorySourceUnavailable("repository authority is not a bounded DNS host")
    path = repository.path.strip().strip("/")
    if not path or any(part in ("", ".", "..") for part in path.split("/")):
        raise RepositorySourceUnavailable("repository path is not transportable")
    suffix = "" if path.endswith(".git") else ".git"
    return f"https://{authority}/{path}{suffix}"


def _active_console_user_sid() -> str:
    if sys.platform != "win32":
        raise RepositorySourceUnavailable("user-scoped source acquisition requires Windows")
    from ctypes import wintypes

    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    wts = ctypes.WinDLL("wtsapi32", use_last_error=True)
    TOKEN_QUERY = 0x0008
    TOKEN_USER = 1
    INVALID_SESSION = 0xFFFFFFFF
    k32.WTSGetActiveConsoleSessionId.restype = wintypes.DWORD
    wts.WTSQueryUserToken.argtypes = [wintypes.ULONG, ctypes.POINTER(wintypes.HANDLE)]
    wts.WTSQueryUserToken.restype = wintypes.BOOL
    advapi.GetTokenInformation.argtypes = [
        wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)
    ]
    advapi.GetTokenInformation.restype = wintypes.BOOL
    advapi.ConvertSidToStringSidW.argtypes = [ctypes.c_void_p, ctypes.POINTER(wintypes.LPWSTR)]
    advapi.ConvertSidToStringSidW.restype = wintypes.BOOL
    session = k32.WTSGetActiveConsoleSessionId()
    if session == INVALID_SESSION:
        raise RepositorySourceUnavailable("no active interactive Windows session")
    token = wintypes.HANDLE()
    if not wts.WTSQueryUserToken(session, ctypes.byref(token)):
        raise RepositorySourceUnavailable("cannot acquire active user token for Git broker")
    try:
        required = wintypes.DWORD()
        advapi.GetTokenInformation(token, TOKEN_USER, None, 0, ctypes.byref(required))
        if not required.value:
            raise RepositorySourceUnavailable("cannot size active user SID")
        buffer = ctypes.create_string_buffer(required.value)
        if not advapi.GetTokenInformation(token, TOKEN_USER, buffer, required.value, ctypes.byref(required)):
            raise RepositorySourceUnavailable("cannot read active user SID")
        sid_ptr = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_void_p))[0]
        text = wintypes.LPWSTR()
        if not advapi.ConvertSidToStringSidW(sid_ptr, ctypes.byref(text)) or not text.value:
            raise RepositorySourceUnavailable("cannot stringify active user SID")
        try:
            return str(text.value)
        finally:
            k32.LocalFree(text)
    finally:
        k32.CloseHandle(token)


def _local_git(root: Path, *args: str, timeout: float = 60) -> tuple[int, bytes, bytes]:
    git = shutil.which("git")
    if not git:
        raise RepositorySourceUnavailable("git.exe is unavailable to provider source broker")
    home = root / ".provider-home"
    home.mkdir(parents=True, exist_ok=True)
    empty_hooks = root / ".provider-hooks"
    empty_hooks.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env.update(
        {
            "HOME": str(home),
            "USERPROFILE": str(home),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_TERMINAL_PROMPT": "0",
            "GCM_INTERACTIVE": "Never",
            "GIT_ASKPASS": "",
        }
    )
    completed = subprocess.run(
        [git, "-c", f"core.hooksPath={empty_hooks}", "-C", str(root), *args],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
        shell=False,
        env=env,
        creationflags=0x08000000 if sys.platform == "win32" else 0,
    )
    return int(completed.returncode), bytes(completed.stdout), bytes(completed.stderr)


def _git_failure(returncode: int, stderr: bytes, *, phase: str) -> RepositorySourceUnavailable:
    text = redact_git_output(stderr.decode("utf-8", "replace")).strip()
    return RepositorySourceUnavailable(f"provider Git {phase} failed ({returncode}): {text[:800]}")


def _parse_ls_tree(raw: bytes) -> list[tuple[str, str, str, str]]:
    result: list[tuple[str, str, str, str]] = []
    for item in raw.split(b"\0"):
        if not item:
            continue
        header, sep, path_raw = item.partition(b"\t")
        if not sep:
            raise RepositorySourceCorrupt("git ls-tree emitted malformed record")
        try:
            path = path_raw.decode("utf-8", "strict")
            mode, kind, oid = header.decode("ascii", "strict").split(" ", 2)
        except (UnicodeError, ValueError) as exc:
            raise RepositorySourceUnsafe("git tree contains unsupported path/record encoding") from exc
        result.append((path, mode, kind, oid))
    return result


class GitRepositorySourceBroker:
    """Credential-bounded exact Git fetch -> immutable provider snapshot."""

    def __init__(
        self,
        *,
        policy: Policy,
        state_root: Path,
        snapshot_store: RepositorySourceSnapshotStore,
        ref_resolver: RepositoryRefResolver,
    ) -> None:
        self.policy = policy
        self.state_root = state_root.resolve(strict=False)
        self.snapshot_store = snapshot_store
        self.ref_resolver = ref_resolver
        self.staging_root = self.state_root / "repository-source-broker"
        self.staging_root.mkdir(parents=True, exist_ok=True)

    async def acquire(
        self,
        repository: RepositoryIdentity,
        transaction: RepositoryTransactionRecord,
    ) -> RepositorySourceSnapshot:
        try:
            existing = self.snapshot_store.load_verified(
                transaction.transaction_id,
                expected_source_sha=transaction.expected_source_sha,
            )
            return existing
        except RepositorySourceCorrupt:
            raise
        except Exception:
            pass

        resolved = (await self.ref_resolver(repository, transaction.source_ref)).lower()
        if resolved != transaction.expected_source_sha.lower():
            raise RepositoryMaterializationConflict(
                "source ref moved after admission; exact materialization authority is stale"
            )
        transport_url = _repository_transport_url(repository)
        staging = self.staging_root / f"src-{secrets.token_urlsafe(18)}"
        staging.mkdir(parents=False, exist_ok=False)
        broker_sid: str | None = None
        interactive_sid: str | None = None
        try:
            if sys.platform == "win32":
                broker_sid = _current_process_sid()
                interactive_sid = _active_console_user_sid()
                _set_exact_acl(
                    staging,
                    broker_sid,
                    None if interactive_sid == broker_sid else interactive_sid,
                )
            rc, _out, err = await asyncio.to_thread(_local_git, staging, "init", "--bare", ".")
            if rc:
                raise _git_failure(rc, err, phase="init")
            rc, _out, err = await asyncio.to_thread(
                _local_git, staging, "remote", "add", "origin", transport_url
            )
            if rc:
                raise _git_failure(rc, err, phase="remote-add")
            fetch_args = (
                "-c",
                f"core.hooksPath={staging / '.provider-hooks'}",
                "fetch",
                "--no-tags",
                "--depth=1",
                "origin",
                transaction.source_ref,
            )
            try:
                rc, _out, err = await run_user_scoped_git(
                    staging,
                    *fetch_args,
                    timeout=float(self.policy.authenticated_git_timeout_seconds),
                )
            except UserScopedGitError as exc:
                raise RepositorySourceUnavailable(
                    f"user-scoped Git source fetch failed: {exc.code}"
                ) from exc
            reason = classify_result(rc, err)
            if reason is not None:
                raise RepositorySourceUnavailable(f"user-scoped Git source fetch failed: {reason}")
            rc, out, err = await asyncio.to_thread(_local_git, staging, "rev-parse", "FETCH_HEAD")
            if rc:
                raise _git_failure(rc, err, phase="readback")
            fetched = out.decode("ascii", "strict").strip().lower()
            if fetched != transaction.expected_source_sha.lower():
                raise RepositoryMaterializationConflict(
                    "fetched source commit differs from sealed expected source SHA"
                )
            rc, tree_raw, err = await asyncio.to_thread(
                _local_git, staging, "ls-tree", "-rz", "-r", "-t", fetched
            )
            if rc:
                raise _git_failure(rc, err, phase="ls-tree")
            raw_entries = _parse_ls_tree(tree_raw)
            if len(raw_entries) > MAX_SOURCE_ENTRIES:
                raise RepositorySourceUnsafe("source entry count exceeds V1 ceiling")
            entries: list[tuple[str, str, str, bytes | str | None]] = []
            total = 0
            for path, mode, kind, oid in raw_entries:
                path = _safe_source_path(path)
                if mode == "040000" and kind == "tree":
                    entries.append((path, "directory", mode, None))
                    continue
                if mode == "160000" or kind == "commit":
                    raise RepositorySourceUnsafe("Gitlink/submodule entries are unsupported in V1")
                if kind != "blob" or mode not in {"100644", "100755", "120000"}:
                    raise RepositorySourceUnsafe("unsupported Git tree entry")
                rc, blob, err = await asyncio.to_thread(_local_git, staging, "cat-file", "blob", oid)
                if rc:
                    raise _git_failure(rc, err, phase="cat-file")
                if len(blob) > MAX_SOURCE_FILE_BYTES:
                    raise RepositorySourceUnsafe("source blob exceeds V1 per-file ceiling")
                total += len(blob)
                if total > MAX_SOURCE_TOTAL_BYTES:
                    raise RepositorySourceUnsafe("source bytes exceed V1 total ceiling")
                if mode == "120000":
                    try:
                        target = blob.decode("utf-8", "strict")
                    except UnicodeError as exc:
                        raise RepositorySourceUnsafe("Git symlink target is not UTF-8") from exc
                    _safe_symlink_target(path, target)
                    entries.append((path, "symlink", mode, target))
                else:
                    entries.append((path, "file", mode, blob))
            snapshot = self.snapshot_store.seal(
                transaction_id=transaction.transaction_id,
                source_sha=fetched,
                entries=entries,
            )
            return snapshot
        finally:
            if sys.platform == "win32" and broker_sid and staging.exists():
                try:
                    _set_exact_acl(staging, broker_sid, None)
                except Exception:
                    pass
            shutil.rmtree(staging, ignore_errors=True)


class RepositoryTransactionProgress:
    """Durably update the mutable progress fields in the S01 transaction store."""

    def __init__(self, store: RepositoryTransactionStore) -> None:
        self.store = store

    def transition(
        self,
        transaction_id: str,
        *,
        expected: frozenset[str],
        target: str,
        evidence: dict[str, Any] | None = None,
    ) -> RepositoryTransactionRecord:
        with _transaction_lock(self.store._lock_path):
            state = self.store._load_state()
            current = self.store._record(state, transaction_id)
            if current.state == target:
                return current
            if current.state not in expected:
                raise RepositoryMaterializationConflict(
                    f"transaction {transaction_id} is {current.state}; expected {sorted(expected)}"
                )
            updated = replace(
                current,
                state=target,
                updated_at=_iso(),
                materialization_evidence=(
                    dict(evidence) if evidence is not None else current.materialization_evidence
                ),
            )
            state["transactions"][transaction_id] = updated.to_json()
            self.store._durable_write_state(state)
            return self.store._record(self.store._load_state(), transaction_id)


MATERIALIZER_SCRIPT = r'''from __future__ import annotations
import json, os, shutil, sys
from pathlib import Path, PurePosixPath

manifest_path=Path(sys.argv[1])
content_root=Path(sys.argv[2])
workspace=Path(sys.argv[3])
control_name=sys.argv[4]
manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
entries=manifest["entries"]

def target_for(value):
    p=PurePosixPath(value)
    if p.is_absolute() or not p.parts or any(x in ("", ".", "..") for x in p.parts):
        raise RuntimeError("unsafe materializer path")
    if p.parts[0].casefold()==control_name.casefold():
        raise RuntimeError("provider control namespace collision")
    target=workspace.joinpath(*p.parts)
    parent=target.parent
    cursor=workspace
    for part in p.parts[:-1]:
        cursor=cursor/part
        if cursor.exists() and (cursor.is_symlink() or os.path.islink(cursor)):
            raise RuntimeError("reparse/symlink traversal")
    return target

for e in entries:
    if e["kind"]=="directory":
        t=target_for(e["path"])
        t.mkdir(parents=True, exist_ok=True)
for e in entries:
    if e["kind"]!="file":
        continue
    t=target_for(e["path"])
    if t.exists() or t.is_symlink():
        raise RuntimeError("materializer target already exists")
    t.parent.mkdir(parents=True, exist_ok=True)
    s=content_root.joinpath(*PurePosixPath(e["path"]).parts)
    if s.is_symlink() or not s.is_file():
        raise RuntimeError("snapshot file is not a regular file")
    with s.open("rb") as src, t.open("xb") as dst:
        shutil.copyfileobj(src,dst,length=1024*1024)
    if e.get("mode")=="100755":
        try: os.chmod(t,0o755)
        except OSError: pass
for e in entries:
    if e["kind"]!="symlink":
        continue
    t=target_for(e["path"])
    if t.exists() or t.is_symlink():
        raise RuntimeError("materializer target already exists")
    t.parent.mkdir(parents=True, exist_ok=True)
    target=e["link_target"]
    if target.startswith(("/","\\")) or ":" in target or "\\" in target:
        raise RuntimeError("unsafe symlink target")
    stack=list(PurePosixPath(e["path"]).parent.parts)
    for part in PurePosixPath(target).parts:
        if part in ("", "."): continue
        if part=="..":
            if not stack: raise RuntimeError("symlink escapes source tree")
            stack.pop()
        else: stack.append(part)
    os.symlink(target,t)
result=workspace/control_name/"materialization-result.json"
result.write_text(json.dumps({"ok":True,"tree_digest":manifest["tree_digest"],"entries":len(entries)},sort_keys=True),encoding="utf-8")
'''


class RepositoryOperationAuditJournal(MutationAuditJournal):
    """Same append-only audit with an explicit nonterminal operation FINISH."""

    def finish_operation(
        self,
        start,
        *,
        status: str,
        closure: MutationFinishClosureEvidence,
    ) -> str:
        self._assert_start_identity(start)
        if status not in FINISH_STATES:
            raise ValueError(f"invalid mutation finish status: {status}")
        if (
            closure.scope_digest != start.authority.scope_digest
            or closure.protected_inventory_digest != start.authority.protected_inventory_digest
            or not closure.job_handle_closed
            or closure.job_active_process_count != 0
            or closure.active_job_ids
            or closure.active_process_ids
            or closure.sandbox_write_authority_present
            or not closure.process_tree_quiescent
        ):
            raise MutationAuditIdentityMismatch(
                "operation FINISH requires zero process/write authority read-back"
            )
        event_ref = f"mutation-audit:{start.operation_id}:finish:{secrets.token_hex(4)}"
        self._durable_append(
            {
                "version": JOURNAL_VERSION,
                "event": EVENT_FINISHED,
                "event_ref": event_ref,
                "operation_id": start.operation_id,
                "binding": start.binding.audit_dict(),
                "binding_digest": start.binding_digest,
                "status": status,
                "closure": closure.audit_dict(),
                "operation_scope_terminal": False,
                "recorded_at": _iso(),
            }
        )
        return event_ref


def _authority(record: MutationScopeRecord) -> MutationAuthorityEvidence:
    return MutationAuthorityEvidence(
        scope_digest=record.scope_digest,
        exact_workspace_digest=record.exact_workspace_digest,
        protected_inventory_digest=record.protected_inventory_digest,
        policy_digest=record.policy_digest,
        repository_identity_digest=record.repository_identity_digest,
        semantic_identity_digest=record.semantic_identity_digest,
    )


def _lineage(semantic: SemanticIdentity) -> MutationLineage:
    return MutationLineage.from_mapping(
        {
            "project_id": semantic.project_id,
            "task_id": semantic.task_id,
            "run_id": semantic.run_id,
            "attempt_id": semantic.attempt_id,
            **({"slice_id": semantic.slice_id} if semantic.slice_id else {}),
        }
    )


def _grant_snapshot_read(snapshot_root: Path, broker_sid: str, app_sid: str) -> None:
    _set_exact_acl(snapshot_root, broker_sid, None)
    _run_icacls([str(snapshot_root), "/grant:r", f"*{app_sid}:(OI)(CI)(R)", "/T", "/C"])
    observed = {sid: mask for sid, mask, _flags in _dacl_entries(snapshot_root)}
    if app_sid not in observed:
        raise RepositoryMaterializationFailed("snapshot AppContainer read grant was not installed")
    # FILE_GENERIC_WRITE / FILE_WRITE_DATA / DELETE-like broad write bits.
    if observed[app_sid] & 0x00120116:
        raise RepositoryMaterializationFailed("snapshot grant contains write authority")


def _remove_snapshot_read(snapshot_root: Path, app_sid: str) -> None:
    if snapshot_root.exists():
        _run_icacls([str(snapshot_root), "/remove:g", f"*{app_sid}", "/T", "/C"])
        if any(sid == app_sid for sid, _mask, _flags in _dacl_entries(snapshot_root)):
            raise RepositoryMaterializationFailed("snapshot AppContainer read grant survived cleanup")


def _materializer_environment(workspace: Path) -> dict[str, str]:
    control = workspace / CONTROL_NAMESPACE
    profile = control / "profile"
    temp = control / "tmp"
    profile.mkdir(parents=True, exist_ok=True)
    temp.mkdir(parents=True, exist_ok=True)
    result = {
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "HOME": str(profile),
        "USERPROFILE": str(profile),
        "TEMP": str(temp),
        "TMP": str(temp),
    }
    for name in ("SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT"):
        value = os.environ.get(name)
        if value:
            result[name] = value
    return result


def _workspace_tree_digest(workspace: Path, snapshot: RepositorySourceSnapshot) -> str:
    manifest = json.loads(snapshot.manifest_path.read_text(encoding="utf-8"))
    entries = manifest["entries"]
    expected_paths = {str(e["path"]).casefold() for e in entries}
    observed_paths: set[str] = set()
    for path in workspace.rglob("*"):
        rel = path.relative_to(workspace).as_posix()
        if rel.split("/", 1)[0].casefold() == CONTROL_NAMESPACE.casefold():
            continue
        observed_paths.add(rel.casefold())
    if observed_paths != expected_paths:
        raise RepositoryMaterializationFailed("materialized source tree contains missing/extra paths")
    for entry in entries:
        rel = _safe_source_path(str(entry["path"]))
        path = workspace / Path(*PurePosixPath(rel).parts)
        kind = entry["kind"]
        if kind == "directory":
            if not path.is_dir() or path.is_symlink():
                raise RepositoryMaterializationFailed(f"materialized directory mismatch: {rel}")
        elif kind == "file":
            if not path.is_file() or path.is_symlink():
                raise RepositoryMaterializationFailed(f"materialized file type mismatch: {rel}")
            data = path.read_bytes()
            if len(data) != entry["size"] or _sha256(data) != entry["sha256"]:
                raise RepositoryMaterializationFailed(f"materialized file digest mismatch: {rel}")
        elif kind == "symlink":
            if not path.is_symlink() or os.readlink(path) != entry["link_target"]:
                raise RepositoryMaterializationFailed(f"materialized symlink mismatch: {rel}")
        else:
            raise RepositoryMaterializationFailed("unexpected materialized source entry kind")
    digest = _json_digest(entries)
    if digest != snapshot.tree_digest:
        raise RepositoryMaterializationFailed("materialized source digest differs from sealed snapshot")
    return digest


class RepositoryMaterializationService:
    def __init__(
        self,
        *,
        policy: Policy,
        transaction_store: RepositoryTransactionStore,
        ref_resolver: RepositoryRefResolver,
        state_root: Path | None = None,
        source_broker: SourceBroker | None = None,
    ) -> None:
        self.policy = policy
        self.state_root = (state_root or (policy.upload_base.parent / "state")).resolve(strict=False)
        self.transaction_store = transaction_store
        self.progress = RepositoryTransactionProgress(transaction_store)
        self.scope_store = MutationScopeStore(self.state_root)
        self.snapshot_store = RepositorySourceSnapshotStore(self.state_root)
        self.source_broker = source_broker or GitRepositorySourceBroker(
            policy=policy,
            state_root=self.state_root,
            snapshot_store=self.snapshot_store,
            ref_resolver=ref_resolver,
        )

    async def materialize(
        self,
        context: RequestContext,
        repository: RepositoryIdentity,
        semantic: SemanticIdentity,
        *,
        scope_id: str,
        generation: int,
    ) -> dict[str, Any]:
        mutation = self.policy.mutation_execution
        if not mutation.configured or not mutation.scoped_mutation_enabled:
            raise RepositoryMaterializationFailed("scoped mutation is not enabled")
        if sys.platform != "win32":
            raise RepositoryMaterializationFailed("repository materialization V1 requires Windows AppContainer")
        transaction = self.transaction_store.inspect(
            repository, semantic, scope_id=scope_id, generation=generation
        )
        if transaction.state == "materialized":
            snapshot = self.snapshot_store.load_verified(
                transaction.transaction_id, expected_source_sha=transaction.expected_source_sha
            )
            _workspace_tree_digest(Path(self.scope_store.read_scope(scope_id).exact_workspace), snapshot)
            return {
                "repository_transaction": transaction.project(),
                "materialization": dict(transaction.materialization_evidence or {}),
                "idempotent": True,
            }
        if transaction.state != "provisioned":
            raise RepositoryMaterializationConflict(
                f"transaction is {transaction.state}; materialization requires provisioned"
            )
        protected = (self.state_root,)
        scope = self.scope_store.revalidate_scope_for_operation(
            scope_id,
            generation,
            mutation,
            repository,
            semantic,
            required_operation_class="repository_materialize",
            provider_protected_roots=protected,
        )
        transaction = self.progress.transition(
            transaction.transaction_id,
            expected=frozenset({"provisioned"}),
            target="materializing",
        )
        snapshot: RepositorySourceSnapshot | None = None
        sandbox = None
        activation = None
        process = None
        audit: RepositoryOperationAuditJournal | None = None
        start = None
        snapshot_granted = False
        try:
            snapshot = await self.source_broker.acquire(repository, transaction)
            if snapshot.source_sha.lower() != transaction.expected_source_sha.lower():
                raise RepositoryMaterializationConflict("source snapshot SHA differs from transaction")

            audit = RepositoryOperationAuditJournal(
                self.state_root,
                evidence_retention_days=mutation.evidence_retention_days,
            )
            script_evidence = audit.evidence.retain(MATERIALIZER_SCRIPT.encode("utf-8"))
            planned_workspace = Path(scope.exact_workspace)
            script_path = planned_workspace / CONTROL_NAMESPACE / "materializer.py"
            argv = [
                str(Path(sys.executable)),
                str(script_path),
                str(snapshot.manifest_path),
                str(snapshot.content_root),
                str(planned_workspace),
                CONTROL_NAMESPACE,
            ]
            binding = MutationAuditBinding.from_context(
                context,
                _lineage(semantic),
                scope_id=scope.scope_id,
                scope_generation=scope.generation,
                workspace_id=scope.workspace_id,
                unique_lease_key=scope.unique_lease_key,
            )
            intent = MutationProcessIntent(
                interpreter="python3",
                argv=tuple(argv),
                executable_final_path=final_executable_path(Path(sys.executable)),
                cwd_final_path=str(planned_workspace),
            )
            start = audit.begin(
                binding,
                script_evidence,
                authority=_authority(scope),
                process_intent=intent,
                requested_identity=requested_mutation_identity(scope.unique_lease_key),
            )
            # Only after durable START may any exact-workspace bytes/ACLs be created.
            sandbox = build_mutation_sandbox(
                policy=mutation,
                scope_store=self.scope_store,
                repository=repository,
                semantic=semantic,
                provider_protected_roots=protected,
            )
            activation = sandbox.activate(scope, start)
            control = activation.workspace / CONTROL_NAMESPACE
            control.mkdir(parents=True, exist_ok=False)
            audit.evidence.materialize_verified(script_evidence, script_path)
            _grant_snapshot_read(snapshot._root, activation.broker_identity, activation.sandbox_identity)
            snapshot_granted = True
            process = sandbox.spawn(
                activation,
                audit=audit,
                audit_start=start,
                argv=argv,
                cwd=activation.workspace,
                env=_materializer_environment(activation.workspace),
            )
            if not process.wait(MATERIALIZE_TIMEOUT_SECONDS):
                process.terminate()
                raise RepositoryMaterializationFailed("repository materializer timed out")
            if process.exit_code not in (0, None):
                raise RepositoryMaterializationFailed(
                    f"repository materializer exited with code {process.exit_code}"
                )
            result_path = control / "materialization-result.json"
            try:
                result = json.loads(result_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                raise RepositoryMaterializationFailed("materializer did not persist valid result") from exc
            if result.get("ok") is not True or result.get("tree_digest") != snapshot.tree_digest:
                raise RepositoryMaterializationFailed("materializer result does not match sealed snapshot")

            _remove_snapshot_read(snapshot._root, activation.sandbox_identity)
            snapshot_granted = False
            current = self.scope_store.read_scope(scope_id)
            closure = sandbox._cleanup_runtime(current)
            current = self.scope_store.read_scope(scope_id)
            if (
                closure.active_job_ids
                or closure.active_process_ids
                or closure.sandbox_write_authority_present
                or current.active_job_ids
                or current.active_process_ids
                or current.sandbox_write_authority_present
            ):
                raise RepositoryMaterializationFailed("materialization operation left residual authority")
            tree_digest = _workspace_tree_digest(activation.workspace, snapshot)
            finish_closure = MutationFinishClosureEvidence(
                scope_state=current.state,
                scope_digest=current.scope_digest,
                protected_inventory_digest=current.protected_inventory_digest,
                sandbox_identity=current.sandbox_identity,
                job_binding=process.job_ref if process is not None else None,
                root_pid=process.pid if process is not None else None,
                job_handle_closed=True,
                job_active_process_count=0,
                active_job_ids=current.active_job_ids,
                active_process_ids=current.active_process_ids,
                sandbox_write_authority_present=current.sandbox_write_authority_present,
                process_tree_quiescent=True,
                terminalized_at="",
            )
            finish_ref = audit.finish_operation(start, status="succeeded", closure=finish_closure)
            evidence = {
                **snapshot.project(),
                "source_tree_digest": tree_digest,
                "audit_operation_id": start.operation_id,
                "audit_start_ref": start.event_ref,
                "audit_finish_ref": finish_ref,
                "sandbox_identity_digest": _sha256(activation.sandbox_identity.encode("utf-8")),
                "job_contained": True,
                "process_tree_quiescent": True,
                "snapshot_read_authority_removed": True,
                "workspace_write_authority_removed": True,
                "canonical_checkout_mutated": False,
                "completed_at": _iso(),
            }
            completed = self.progress.transition(
                transaction.transaction_id,
                expected=frozenset({"materializing"}),
                target="materialized",
                evidence=evidence,
            )
            return {
                "repository_transaction": completed.project(),
                "materialization": evidence,
                "idempotent": False,
            }
        except Exception as exc:
            if snapshot_granted and snapshot is not None and activation is not None:
                try:
                    _remove_snapshot_read(snapshot._root, activation.sandbox_identity)
                except Exception:
                    pass
            if process is not None:
                try:
                    process.terminate()
                except Exception:
                    pass
            try:
                if sandbox is not None:
                    sandbox.terminalize(scope_id, generation)
                else:
                    self.scope_store.revoke_scope(scope_id, generation)
            except Exception:
                pass
            failure = {
                "status": "failed",
                "reason_code": getattr(exc, "code", type(exc).__name__),
                "canonical_checkout_mutated": False,
                "published": False,
                "failed_at": _iso(),
            }
            try:
                self.progress.transition(
                    transaction.transaction_id,
                    expected=frozenset({"materializing", "provisioned"}),
                    target="terminal",
                    evidence=failure,
                )
            except Exception:
                pass
            if isinstance(exc, RepositoryMaterializationError):
                raise
            if isinstance(exc, RepositoryTransactionError):
                raise RepositoryMaterializationConflict(str(exc)) from exc
            raise RepositoryMaterializationFailed(str(exc)) from exc


_REPOSITORY_SCHEMA = {
    "type": "object",
    "required": ["vcs", "authority", "path"],
    "additionalProperties": False,
    "properties": {
        "vcs": {"type": "string"},
        "authority": {"type": "string"},
        "path": {"type": "string"},
    },
}
_LINEAGE_SCHEMA = {
    "type": "object",
    "required": ["project_id", "task_id", "run_id", "attempt_id"],
    "additionalProperties": False,
    "properties": {
        "project_id": {"type": "string"},
        "task_id": {"type": "string"},
        "run_id": {"type": "string"},
        "attempt_id": {"type": "string"},
        "slice_id": {"type": "string"},
    },
}
_SCOPE_REF_SCHEMA = {
    "type": "object",
    "required": ["scope_id", "generation"],
    "additionalProperties": False,
    "properties": {
        "scope_id": {"type": "string"},
        "generation": {"type": "integer", "minimum": 1},
    },
}
_MATERIALIZE_SCHEMA = {
    "type": "object",
    "required": ["scope_ref", "repository", "lineage"],
    "additionalProperties": False,
    "properties": {
        "scope_ref": _SCOPE_REF_SCHEMA,
        "repository": _REPOSITORY_SCHEMA,
        "lineage": _LINEAGE_SCHEMA,
    },
}


def _identities(params: dict[str, Any]) -> tuple[RepositoryIdentity, SemanticIdentity, str, int]:
    if set(params) != {"scope_ref", "repository", "lineage"}:
        raise HandlerError("invalid_payload", "materialize_repository accepts only scope_ref/repository/lineage")
    scope = params.get("scope_ref")
    repo = params.get("repository")
    lineage = params.get("lineage")
    if not isinstance(scope, dict) or set(scope) != {"scope_id", "generation"}:
        raise HandlerError("invalid_payload", "scope_ref must contain only scope_id/generation")
    if not isinstance(repo, dict) or set(repo) != {"vcs", "authority", "path"}:
        raise HandlerError("invalid_payload", "repository identity is malformed")
    if not isinstance(lineage, dict) or not {"project_id", "task_id", "run_id", "attempt_id"}.issubset(lineage):
        raise HandlerError("invalid_payload", "lineage identity is malformed")
    if set(lineage) - {"project_id", "task_id", "run_id", "attempt_id", "slice_id"}:
        raise HandlerError("invalid_payload", "lineage contains unsupported fields")
    scope_id = scope.get("scope_id")
    generation = scope.get("generation")
    if not isinstance(scope_id, str) or not scope_id.strip():
        raise HandlerError("invalid_payload", "scope_ref.scope_id must be non-empty")
    if isinstance(generation, bool) or not isinstance(generation, int) or generation <= 0:
        raise HandlerError("invalid_payload", "scope_ref.generation must be positive")
    try:
        repository = RepositoryIdentity(
            vcs=str(repo.get("vcs") or ""),
            authority=str(repo.get("authority") or ""),
            path=str(repo.get("path") or ""),
        )
        _ = repository.canonical
        semantic = SemanticIdentity(
            project_id=str(lineage.get("project_id") or ""),
            task_id=str(lineage.get("task_id") or ""),
            run_id=str(lineage.get("run_id") or ""),
            attempt_id=str(lineage.get("attempt_id") or ""),
            slice_id=str(lineage["slice_id"]) if lineage.get("slice_id") is not None else None,
        )
        _ = semantic.canonical
    except ValueError as exc:
        raise HandlerError("invalid_payload", str(exc)) from exc
    return repository, semantic, scope_id.strip(), generation


class RepositoryMaterializationProvider:
    """Decorator adding S02 action without replacing S01/PR-012 provider semantics."""

    def __init__(self, base: Any, service: RepositoryMaterializationService) -> None:
        self.base = base
        self.service = service
        self.name = base.name

    def available_actions(self) -> tuple[str, ...]:
        actions = list(self.base.available_actions())
        if self.base.repository_transactions_ready and "materialize_repository" not in actions:
            actions.append("materialize_repository")
        return tuple(actions)

    def list_entry(self) -> dict[str, Any]:
        result = dict(self.base.list_entry())
        result["action_count"] = len(self.available_actions())
        return result

    def describe(self) -> dict[str, Any]:
        result = dict(self.base.describe())
        actions = dict(result["actions"])
        if "materialize_repository" in self.available_actions():
            actions["materialize_repository"] = {
                "description": "Bounded exact repository source materialization",
                "params": ["scope_ref", "repository", "lineage"],
                "params_schema": _MATERIALIZE_SCHEMA,
            }
        result["actions"] = actions
        return result

    async def call(
        self,
        context: RequestContext,
        action: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        if action != "materialize_repository":
            result = await self.base.call(context, action, params)
            if action == "inspect_repository_transaction" and isinstance(result, dict):
                try:
                    repository, semantic, scope_id, generation = _identities(params)
                    record = self.base._repository_transactions.inspect(
                        repository, semantic, scope_id=scope_id, generation=generation
                    )
                    if record.materialization_evidence:
                        projected = dict(result.get("repository_transaction") or {})
                        projected["materialization"] = dict(record.materialization_evidence)
                        result = dict(result)
                        result["repository_transaction"] = projected
                except Exception:
                    pass
            return result
        if "materialize_repository" not in self.available_actions():
            raise HandlerError(
                "RepositoryMaterializationUnavailable",
                "repository materialization is not admitted by Host policy",
            )
        repository, semantic, scope_id, generation = _identities(params)
        try:
            return await self.service.materialize(
                context,
                repository,
                semantic,
                scope_id=scope_id,
                generation=generation,
            )
        except RepositoryMaterializationError as exc:
            raise HandlerError(exc.code, str(exc)) from exc
        except RepositoryTransactionError as exc:
            raise HandlerError(str(getattr(exc, "code", type(exc).__name__)), str(exc)) from exc


def make_repository_materialization_provider(base: Any, policy: Policy) -> RepositoryMaterializationProvider:
    state_root = (policy.upload_base.parent / "state").resolve(strict=False)
    service = RepositoryMaterializationService(
        policy=policy,
        transaction_store=base._repository_transactions,
        ref_resolver=base._repository_ref_resolver,
        state_root=state_root,
    )
    return RepositoryMaterializationProvider(base, service)
