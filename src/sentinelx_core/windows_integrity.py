"""Provider-owned Windows mandatory-integrity-control sandbox (PR-015/S02).

The direct-Codex containment proof must be a *physical* negative proof: a child
process starts inside the legal execution workspace, really attempts a write
outside that workspace, and is refused by the operating system.

On Windows the refusal mechanism that is available to an unprivileged provider
process is Mandatory Integrity Control (MIC). A medium-integrity provider

1. takes ownership-level control of the provider-owned workspace directories it
   created (``WRITE_OWNER`` is required to relabel an object), and
2. stamps those directories with a **low** mandatory label
   (``NO_WRITE_UP``), then
3. starts every provider-owned child from a duplicated primary token whose
   ``TokenIntegrityLevel`` is **low**.

After that the kernel itself refuses every write that leaves the labeled
workspace: the child is a low-integrity subject and every other directory on
the host is a medium-integrity object, so ``NO_WRITE_UP`` denies the access
with ``EPERM``/``ERROR_ACCESS_DENIED``. The refusal is therefore produced by
the operating system, not by a Python-side cwd check.

Nothing here accepts caller data, widens any ACL on a foreign path, or grants
the sandbox authority over anything the provider did not create.
"""
from __future__ import annotations

import ctypes
import os
import sys
from contextlib import contextmanager
from ctypes import wintypes
from pathlib import Path
from typing import Iterator

FEATURE_NAME = "host_runtime.integrity_sandbox_v1"

SE_FILE_OBJECT = 1
LABEL_SECURITY_INFORMATION = 0x00000010
DACL_SECURITY_INFORMATION = 0x00000004
SYSTEM_MANDATORY_LABEL_NO_WRITE_UP = 0x00000001
ACL_REVISION = 2
GRANT_ACCESS = 1
SET_ACCESS = 2
FILE_ALL_ACCESS = 0x001F01FF

OBJECT_INHERIT_ACE = 0x00000001
CONTAINER_INHERIT_ACE = 0x00000002
# The label and the broker ACE must reach everything the execution checkout and
# the direct host create later, so both are stamped with inheritance.
SUBTREE_INHERIT_ACE = OBJECT_INHERIT_ACE | CONTAINER_INHERIT_ACE

TOKEN_QUERY = 0x0008
TOKEN_DUPLICATE = 0x0002
TOKEN_ADJUST_DEFAULT = 0x0080
TOKEN_ASSIGN_PRIMARY = 0x0001
TOKEN_INTEGRITY_LEVEL = 25
TOKEN_SESSION_ID = 12
SE_GROUP_INTEGRITY_ENABLED = 0x00000020
MAXIMUM_ALLOWED = 0x02000000
SECURITY_IMPERSONATION = 2
TOKEN_PRIMARY = 1

LOW_INTEGRITY_SID = "S-1-16-4096"
MEDIUM_INTEGRITY_SID = "S-1-16-8192"
HIGH_INTEGRITY_SID = "S-1-16-12288"
SYSTEM_INTEGRITY_SID = "S-1-16-16384"

INTEGRITY_NAMES = {
    LOW_INTEGRITY_SID: "low",
    MEDIUM_INTEGRITY_SID: "medium",
    HIGH_INTEGRITY_SID: "high",
    SYSTEM_INTEGRITY_SID: "system",
}
LOW_INTEGRITY = "low"


class IntegritySandboxError(RuntimeError):
    """Fail-closed error for the provider-owned integrity sandbox."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class _SID_AND_ATTRIBUTES(ctypes.Structure):
    _fields_ = [("Sid", ctypes.c_void_p), ("Attributes", wintypes.DWORD)]


class _TOKEN_MANDATORY_LABEL(ctypes.Structure):
    _fields_ = [("Label", _SID_AND_ATTRIBUTES)]


class _TRUSTEE_W(ctypes.Structure):
    _fields_ = [  # noqa: RUF012
        ("pMultipleTrustee", ctypes.c_void_p),
        ("MultipleTrusteeOperation", ctypes.c_int),
        ("TrusteeForm", ctypes.c_int),
        ("TrusteeType", ctypes.c_int),
        ("ptstrName", ctypes.c_void_p),
    ]


class _EXPLICIT_ACCESS_W(ctypes.Structure):
    _fields_ = [  # noqa: RUF012
        ("grfAccessPermissions", wintypes.DWORD),
        ("grfAccessMode", ctypes.c_int),
        ("grfInheritance", wintypes.DWORD),
        ("Trustee", _TRUSTEE_W),
    ]


def supported() -> bool:
    return sys.platform == "win32"


def _require_windows() -> None:
    if not supported():
        raise IntegritySandboxError(
            "integrity_sandbox_platform_unsupported",
            "the provider-owned integrity sandbox requires Windows",
        )


def _apis() -> tuple[Any, Any]:
    _require_windows()
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    k32.GetCurrentProcess.restype = wintypes.HANDLE
    k32.CloseHandle.argtypes = [wintypes.HANDLE]
    k32.CloseHandle.restype = wintypes.BOOL
    k32.LocalFree.argtypes = [ctypes.c_void_p]
    k32.LocalFree.restype = ctypes.c_void_p
    k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    k32.OpenProcess.restype = wintypes.HANDLE
    advapi.ConvertStringSidToSidW.argtypes = [
        wintypes.LPCWSTR,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    advapi.ConvertStringSidToSidW.restype = wintypes.BOOL
    advapi.ConvertSidToStringSidW.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(wintypes.LPWSTR),
    ]
    advapi.ConvertSidToStringSidW.restype = wintypes.BOOL
    advapi.GetLengthSid.argtypes = [ctypes.c_void_p]
    advapi.GetLengthSid.restype = wintypes.DWORD
    advapi.InitializeAcl.argtypes = [ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD]
    advapi.InitializeAcl.restype = wintypes.BOOL
    advapi.AddMandatoryAce.argtypes = [
        ctypes.c_void_p,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.c_void_p,
    ]
    advapi.AddMandatoryAce.restype = wintypes.BOOL
    advapi.SetNamedSecurityInfoW.argtypes = [
        wintypes.LPWSTR,
        ctypes.c_int,
        wintypes.DWORD,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
    ]
    advapi.SetNamedSecurityInfoW.restype = wintypes.DWORD
    advapi.GetNamedSecurityInfoW.argtypes = [
        wintypes.LPWSTR,
        ctypes.c_int,
        wintypes.DWORD,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    advapi.GetNamedSecurityInfoW.restype = wintypes.DWORD
    advapi.OpenProcessToken.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.HANDLE),
    ]
    advapi.OpenProcessToken.restype = wintypes.BOOL
    advapi.GetTokenInformation.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
    ]
    advapi.GetTokenInformation.restype = wintypes.BOOL
    advapi.DuplicateTokenEx.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.POINTER(wintypes.HANDLE),
    ]
    advapi.DuplicateTokenEx.restype = wintypes.BOOL
    advapi.SetTokenInformation.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
    ]
    advapi.SetTokenInformation.restype = wintypes.BOOL
    return k32, advapi


def _win_error(prefix: str) -> IntegritySandboxError:
    code = ctypes.get_last_error()
    return IntegritySandboxError(
        "integrity_sandbox_unavailable",
        f"{prefix}: WinError {code}: {ctypes.FormatError(code)}",
    )


def _sid_string(sid: int | ctypes.c_void_p) -> str:
    k32, advapi = _apis()
    text = wintypes.LPWSTR()
    pointer = sid if isinstance(sid, ctypes.c_void_p) else ctypes.c_void_p(sid)
    if not advapi.ConvertSidToStringSidW(pointer, ctypes.byref(text)):
        raise _win_error("ConvertSidToStringSidW failed")
    try:
        if not text.value:
            raise IntegritySandboxError(
                "integrity_sandbox_unavailable", "Windows returned an empty SID string"
            )
        return text.value
    finally:
        if text:
            k32.LocalFree(text)


class _SidHandle:
    """Owned SID pointer converted from its string form."""

    def __init__(self, value: str) -> None:
        _require_windows()
        self._k32, advapi = _apis()
        self._sid = ctypes.c_void_p()
        if not advapi.ConvertStringSidToSidW(value, ctypes.byref(self._sid)):
            raise _win_error(f"ConvertStringSidToSidW failed for {value}")
        self.value = int(self._sid.value) if self._sid.value else 0

    def pointer(self) -> ctypes.c_void_p:
        return self._sid

    def close(self) -> None:
        if self._sid:
            self._k32.LocalFree(self._sid)
            self._sid = ctypes.c_void_p()

    def __enter__(self) -> "_SidHandle":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()


def current_process_sid() -> str:
    """Return the broker/active-user SID owning the current process token."""
    k32, advapi = _apis()

    class _TOKEN_USER(ctypes.Structure):
        _fields_ = [("User", _SID_AND_ATTRIBUTES)]

    token = wintypes.HANDLE()
    if not advapi.OpenProcessToken(k32.GetCurrentProcess(), TOKEN_QUERY, ctypes.byref(token)):
        raise _win_error("OpenProcessToken failed")
    try:
        size = wintypes.DWORD()
        if not advapi.GetTokenInformation(token, 1, None, 0, ctypes.byref(size)):
            code = ctypes.get_last_error()
            if code != 122:  # ERROR_INSUFFICIENT_BUFFER
                raise _win_error("GetTokenInformation(TokenUser) sizing failed")
        buffer = ctypes.create_string_buffer(max(int(size.value), ctypes.sizeof(_TOKEN_USER)))
        if not advapi.GetTokenInformation(
            token, 1, buffer, ctypes.sizeof(buffer), ctypes.byref(size)
        ):
            raise _win_error("GetTokenInformation(TokenUser) failed")
        info = ctypes.cast(buffer, ctypes.POINTER(_TOKEN_USER)).contents
        return _sid_string(info.User.Sid)
    finally:
        k32.CloseHandle(token)


def grant_owner_full_control(path: Path) -> str:
    """Grant the broker SID full control so the object can be relabeled.

    ``WRITE_OWNER`` is required to set a mandatory label and is not an implicit
    owner right, so the provider first grants itself full control on the
    directories it created. No foreign object is touched.
    """
    k32, advapi = _apis()
    sid = current_process_sid()
    acl = ctypes.c_void_p()
    with _SidHandle(sid) as handle:
        entries = (_EXPLICIT_ACCESS_W * 1)()
        entries[0].grfAccessPermissions = FILE_ALL_ACCESS
        entries[0].grfAccessMode = GRANT_ACCESS
        entries[0].grfInheritance = SUBTREE_INHERIT_ACE
        advapi.BuildTrusteeWithSidW.argtypes = [
            ctypes.POINTER(_TRUSTEE_W),
            ctypes.c_void_p,
        ]
        advapi.BuildTrusteeWithSidW(ctypes.byref(entries[0].Trustee), handle.pointer())
        advapi.SetEntriesInAclW.argtypes = [
            wintypes.ULONG,
            ctypes.POINTER(_EXPLICIT_ACCESS_W),
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_void_p),
        ]
        advapi.SetEntriesInAclW.restype = wintypes.DWORD
        result = advapi.SetEntriesInAclW(1, entries, None, ctypes.byref(acl))
        if result != 0:
            raise IntegritySandboxError(
                "integrity_sandbox_unavailable",
                f"SetEntriesInAclW failed for {path}: WinError {result}",
            )
        try:
            result = advapi.SetNamedSecurityInfoW(
                str(path),
                SE_FILE_OBJECT,
                DACL_SECURITY_INFORMATION,
                None,
                None,
                acl,
                None,
            )
        finally:
            if acl:
                k32.LocalFree(acl)
        if result != 0:
            raise IntegritySandboxError(
                "integrity_sandbox_unavailable",
                f"SetNamedSecurityInfoW(DACL) failed for {path}: WinError {result}",
            )
    return sid


def set_low_mandatory_label(path: Path, *, inherit: bool = True, verify: bool = True) -> None:
    """Stamp ``path`` with the low mandatory label (``NO_WRITE_UP``).

    A low-integrity child can still write here; every medium-integrity path on
    the host becomes unwritable for it. ``inherit`` makes the label reach
    objects created later inside a directory.
    """
    k32, advapi = _apis()
    with _SidHandle(LOW_INTEGRITY_SID) as sid:
        size = 8 + 4 + 4 + 4 + advapi.GetLengthSid(sid.pointer())
        buffer = ctypes.create_string_buffer(size)
        if not advapi.InitializeAcl(buffer, size, ACL_REVISION):
            raise _win_error(f"InitializeAcl failed for {path}")
        if not advapi.AddMandatoryAce(
            buffer,
            ACL_REVISION,
            SUBTREE_INHERIT_ACE if inherit else 0,
            SYSTEM_MANDATORY_LABEL_NO_WRITE_UP,
            sid.pointer(),
        ):
            raise _win_error(f"AddMandatoryAce failed for {path}")
        result = advapi.SetNamedSecurityInfoW(
            str(path),
            SE_FILE_OBJECT,
            LABEL_SECURITY_INFORMATION,
            None,
            None,
            None,
            buffer,
        )
    if result != 0:
        raise IntegritySandboxError(
            "integrity_sandbox_unavailable",
            f"SetNamedSecurityInfoW(label) failed for {path}: WinError {result}",
        )
    if verify:
        applied = mandatory_label(path)
        if applied != LOW_INTEGRITY:
            raise IntegritySandboxError(
                "integrity_sandbox_label_not_verified",
                f"mandatory label read-back for {path} is {applied!r}, not low",
            )


def set_low_mandatory_label_tree(path: Path) -> int:
    """Stamp an existing provider-owned tree low.

    Inheritance only reaches objects created *after* activation, so a checkout
    that already holds content has to be relabeled explicitly. Returns the
    number of stamped objects.
    """
    root = Path(os.path.abspath(str(path)))
    stamped = 0
    for current in (root,):
        grant_owner_full_control(current)
        set_low_mandatory_label(current)
        stamped += 1
    for directory, subdirectories, files in os.walk(str(root)):
        for name in (*subdirectories, *files):
            child = Path(directory) / name
            grant_owner_full_control(child)
            set_low_mandatory_label(child, inherit=True, verify=False)
            stamped += 1
    return stamped


def mandatory_label(path: Path) -> str | None:
    """Read back the mandatory integrity label of ``path``."""
    k32, advapi = _apis()
    sacl = ctypes.c_void_p()
    descriptor = ctypes.c_void_p()
    result = advapi.GetNamedSecurityInfoW(
        str(path),
        SE_FILE_OBJECT,
        LABEL_SECURITY_INFORMATION,
        None,
        None,
        None,
        ctypes.byref(sacl),
        ctypes.byref(descriptor),
    )
    if result != 0 or not sacl:
        return None
    try:
        class _ACL_SIZE_INFORMATION(ctypes.Structure):
            _fields_ = [  # noqa: RUF012
                ("AceCount", wintypes.DWORD),
                ("AclBytesInUse", wintypes.DWORD),
                ("AclBytesFree", wintypes.DWORD),
            ]

        info = _ACL_SIZE_INFORMATION()
        advapi.GetAclInformation.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            wintypes.DWORD,
            ctypes.c_int,
        ]
        advapi.GetAclInformation.restype = wintypes.BOOL
        if not advapi.GetAclInformation(
            sacl, ctypes.byref(info), ctypes.sizeof(info), 2
        ):
            return None
        if info.AceCount == 0:
            return "medium"
        for index in range(int(info.AceCount)):
            ace_pointer = ctypes.c_void_p()
            advapi.GetAce.argtypes = [
                ctypes.c_void_p,
                wintypes.DWORD,
                ctypes.POINTER(ctypes.c_void_p),
            ]
            advapi.GetAce.restype = wintypes.BOOL
            if not advapi.GetAce(sacl, index, ctypes.byref(ace_pointer)):
                return None

            class _ACE_HEADER(ctypes.Structure):
                _fields_ = [  # noqa: RUF012
                    ("AceType", ctypes.c_ubyte),
                    ("AceFlags", ctypes.c_ubyte),
                    ("AceSize", wintypes.WORD),
                ]

            class _SYSTEM_MANDATORY_LABEL_ACE(ctypes.Structure):
                _fields_ = [  # noqa: RUF012
                    ("Header", _ACE_HEADER),
                    ("Mask", wintypes.DWORD),
                    ("SidStart", wintypes.DWORD),
                ]

            ace = ctypes.cast(ace_pointer, ctypes.POINTER(_SYSTEM_MANDATORY_LABEL_ACE)).contents
            if ace.Header.AceType != 0x11:  # SYSTEM_MANDATORY_LABEL_ACE_TYPE
                continue
            sid_pointer = int(ace_pointer.value) + _SYSTEM_MANDATORY_LABEL_ACE.SidStart.offset
            return INTEGRITY_NAMES.get(_sid_string(sid_pointer))
        return "medium"
    finally:
        if descriptor:
            k32.LocalFree(descriptor)


def low_integrity_token(source: int | None = None) -> int:
    """Return a primary token handle for the active user at low integrity.

    ``source`` is an already-resolved active-user token handle; when it is
    ``None`` the current process token is duplicated. The returned handle is
    owned by the caller.
    """
    k32, advapi = _apis()
    token = wintypes.HANDLE()
    if source:
        token = wintypes.HANDLE(source)
        owned_source = False
    else:
        owned_source = True
        if not advapi.OpenProcessToken(
            k32.GetCurrentProcess(),
            TOKEN_DUPLICATE | TOKEN_QUERY | TOKEN_ADJUST_DEFAULT | TOKEN_ASSIGN_PRIMARY,
            ctypes.byref(token),
        ):
            raise _win_error("OpenProcessToken failed")
    duplicate = wintypes.HANDLE()
    try:
        if not advapi.DuplicateTokenEx(
            token,
            MAXIMUM_ALLOWED,
            None,
            SECURITY_IMPERSONATION,
            TOKEN_PRIMARY,
            ctypes.byref(duplicate),
        ):
            raise _win_error("DuplicateTokenEx failed")
    finally:
        if owned_source:
            k32.CloseHandle(token)
    try:
        with _SidHandle(LOW_INTEGRITY_SID) as sid:
            label = _TOKEN_MANDATORY_LABEL()
            label.Label.Sid = sid.pointer()
            label.Label.Attributes = SE_GROUP_INTEGRITY_ENABLED
            if not advapi.SetTokenInformation(
                duplicate,
                TOKEN_INTEGRITY_LEVEL,
                ctypes.byref(label),
                ctypes.sizeof(label),
            ):
                raise _win_error("SetTokenInformation(TokenIntegrityLevel) failed")
    except Exception:
        k32.CloseHandle(duplicate)
        raise
    return int(duplicate.value)


def close_handle(handle: int) -> None:
    if not handle:
        return
    k32, _ = _apis()
    k32.CloseHandle(wintypes.HANDLE(handle))


@contextmanager
def _open_process_token(process_handle: int) -> Iterator[int]:
    k32, advapi = _apis()
    token = wintypes.HANDLE()
    if not advapi.OpenProcessToken(
        wintypes.HANDLE(process_handle), TOKEN_QUERY, ctypes.byref(token)
    ):
        raise _win_error("OpenProcessToken(child) failed")
    try:
        yield int(token.value)
    finally:
        k32.CloseHandle(token)


def token_integrity_level(token: int) -> str | None:
    """Return ``low``/``medium``/... for a token handle."""
    _k32, advapi = _apis()
    size = wintypes.DWORD()
    if not advapi.GetTokenInformation(
        wintypes.HANDLE(token), TOKEN_INTEGRITY_LEVEL, None, 0, ctypes.byref(size)
    ):
        code = ctypes.get_last_error()
        if code != 122:  # ERROR_INSUFFICIENT_BUFFER
            raise _win_error("GetTokenInformation(TokenIntegrityLevel) sizing failed")
    buffer = ctypes.create_string_buffer(max(int(size.value), ctypes.sizeof(_TOKEN_MANDATORY_LABEL)))
    if not advapi.GetTokenInformation(
        wintypes.HANDLE(token),
        TOKEN_INTEGRITY_LEVEL,
        buffer,
        ctypes.sizeof(buffer),
        ctypes.byref(size),
    ):
        raise _win_error("GetTokenInformation(TokenIntegrityLevel) failed")
    info = ctypes.cast(buffer, ctypes.POINTER(_TOKEN_MANDATORY_LABEL)).contents
    if not info.Label.Sid:
        return None
    return INTEGRITY_NAMES.get(_sid_string(info.Label.Sid))


def token_session_id(token: int) -> int | None:
    """Return the Windows session id a token belongs to."""
    _k32, advapi = _apis()
    session = wintypes.DWORD()
    size = wintypes.DWORD()
    if not advapi.GetTokenInformation(
        wintypes.HANDLE(token),
        TOKEN_SESSION_ID,
        ctypes.byref(session),
        ctypes.sizeof(session),
        ctypes.byref(size),
    ):
        return None
    return int(session.value)


def process_integrity_level(process_handle: int) -> str | None:
    """Read back the integrity level of a running child process."""
    with _open_process_token(process_handle) as token:
        return token_integrity_level(token)


def process_session_id(process_handle: int) -> int | None:
    """Read back the Windows session id of a running child process."""
    with _open_process_token(process_handle) as token:
        return token_session_id(token)


def absolute(path: Path) -> Path:
    return Path(os.path.abspath(str(path)))
