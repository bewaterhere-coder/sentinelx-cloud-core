"""Windows V1 scoped mutation boundary: AppContainer + exact ACL + Job.

Nothing in this module falls back to LocalSystem, an ordinary user token,
CreateRestrictedToken, unrestricted subprocess execution, command filtering or
path-only enforcement. If any Windows primitive/read-back is unavailable the
operation fails closed.
"""
from __future__ import annotations

import ctypes
import hashlib
import os
import subprocess
import sys
import time
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from ctypes import wintypes
from pathlib import Path

from sentinelx_core.mutation_audit import (
    MutationAuditJournal,
    MutationAuditStart,
    MutationContainmentEvidence,
    MutationOsIdentityEvidence,
    MutationSpawnEvidence,
    RequestedMutationIdentity,
)
from sentinelx_core.mutation_placement import RepositoryIdentity, SemanticIdentity
from sentinelx_core.mutation_sandbox import (
    ActivatedMutationSandbox,
    HostMutationSandboxAclViolation,
    HostMutationSandboxBindingMismatch,
    HostMutationSandboxContainmentFailed,
    HostMutationSandboxPathViolation,
    HostMutationSandboxResidualAuthority,
    HostMutationSandboxUnavailable,
    assert_audit_scope_binding,
)
from sentinelx_core.mutation_scope import (
    MutationRuntimeClosure,
    MutationScopeRecord,
    MutationScopeStore,
)
from sentinelx_core.policy import MutationExecutionPolicy
from sentinelx_core.verification_runtime import (
    VerificationMaterialization,
    VerificationRuntimePlan,
    cleanup_verification_materialization,
    materialize_verification_runtime,
    revalidate_verification_before_spawn,
)
from sentinelx_core.winspawn import (
    SuspendedJobProcess,
    create_suspended_appcontainer_job_process,
)

ERROR_SUCCESS = 0
ERROR_ALREADY_EXISTS_HRESULT = 0x800700B7
ERROR_FILE_NOT_FOUND_HRESULT = 0x80070002
TOKEN_QUERY = 0x0008
TOKEN_USER = 1
TOKEN_IS_APPCONTAINER = 29
TOKEN_APPCONTAINER_SID = 31
TH32CS_SNAPPROCESS = 0x00000002
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
FILE_ALL_ACCESS = 0x001F01FF
FILE_TRAVERSE = 0x0020
OBJECT_INHERIT_ACE = 0x1
CONTAINER_INHERIT_ACE = 0x2
INHERITED_ACE = 0x10
GRANT_ACCESS = 1
SET_ACCESS = 2
REVOKE_ACCESS = 4
SE_FILE_OBJECT = 1
SE_WINDOW_OBJECT = 7
DACL_SECURITY_INFORMATION = 0x00000004
PROTECTED_DACL_SECURITY_INFORMATION = 0x80000000
READ_CONTROL = 0x00020000
WINSTA_ENUMDESKTOPS = 0x0001
WINSTA_READATTRIBUTES = 0x0002
WINSTA_ENUMERATE = 0x0100
DESKTOP_READOBJECTS = 0x0001
DESKTOP_ENUMERATE = 0x0040
WINDOW_STATION_VERIFICATION_READ = (
    READ_CONTROL | WINSTA_ENUMDESKTOPS | WINSTA_READATTRIBUTES | WINSTA_ENUMERATE
)
DESKTOP_VERIFICATION_READ = READ_CONTROL | DESKTOP_READOBJECTS | DESKTOP_ENUMERATE
ACL_SIZE_INFORMATION_CLASS = 2
ACCESS_ALLOWED_ACE_TYPE = 0
FILE_ATTRIBUTE_REPARSE_POINT = 0x00000400
INVALID_FILE_ATTRIBUTES = 0xFFFFFFFF
FILE_READ_ATTRIBUTES = 0x0080
FILE_SHARE_ALL = 0x00000007
OPEN_EXISTING = 3
FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
SYNCHRONIZE = 0x00100000
STILL_ACTIVE = 259


class _SID_AND_ATTRIBUTES(ctypes.Structure):
    _fields_ = [("Sid", ctypes.c_void_p), ("Attributes", wintypes.DWORD)]


class _TOKEN_USER(ctypes.Structure):
    _fields_ = [("User", _SID_AND_ATTRIBUTES)]


class _TOKEN_APPCONTAINER_INFORMATION(ctypes.Structure):
    _fields_ = [("TokenAppContainer", ctypes.c_void_p)]


class _PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.c_size_t),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", ctypes.c_long),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", wintypes.WCHAR * 260),
    ]


class _TRUSTEE_W(ctypes.Structure):
    _fields_ = [
        ("pMultipleTrustee", ctypes.c_void_p),
        ("MultipleTrusteeOperation", ctypes.c_int),
        ("TrusteeForm", ctypes.c_int),
        ("TrusteeType", ctypes.c_int),
        ("ptstrName", wintypes.LPWSTR),
    ]


class _EXPLICIT_ACCESS_W(ctypes.Structure):
    _fields_ = [
        ("grfAccessPermissions", wintypes.DWORD),
        ("grfAccessMode", ctypes.c_int),
        ("grfInheritance", wintypes.DWORD),
        ("Trustee", _TRUSTEE_W),
    ]


class _ACL_SIZE_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("AceCount", wintypes.DWORD),
        ("AclBytesInUse", wintypes.DWORD),
        ("AclBytesFree", wintypes.DWORD),
    ]


class _ACE_HEADER(ctypes.Structure):
    _fields_ = [
        ("AceType", ctypes.c_ubyte),
        ("AceFlags", ctypes.c_ubyte),
        ("AceSize", wintypes.WORD),
    ]


class _ACCESS_ALLOWED_ACE(ctypes.Structure):
    _fields_ = [
        ("Header", _ACE_HEADER),
        ("Mask", wintypes.DWORD),
        ("SidStart", wintypes.DWORD),
    ]


def _windows_only() -> tuple[ctypes.WinDLL, ctypes.WinDLL, ctypes.WinDLL]:
    if sys.platform != "win32":
        raise HostMutationSandboxUnavailable("Windows AppContainer APIs are unavailable")
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    userenv = ctypes.WinDLL("userenv", use_last_error=True)

    k32.GetCurrentProcess.restype = wintypes.HANDLE
    k32.GetCurrentThreadId.argtypes = []
    k32.GetCurrentThreadId.restype = wintypes.DWORD
    k32.LocalFree.argtypes = [ctypes.c_void_p]
    k32.LocalFree.restype = ctypes.c_void_p
    k32.CloseHandle.argtypes = [wintypes.HANDLE]
    k32.CloseHandle.restype = wintypes.BOOL
    k32.CreateFileW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.c_void_p,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    k32.CreateFileW.restype = wintypes.HANDLE
    k32.GetFinalPathNameByHandleW.argtypes = [
        wintypes.HANDLE,
        wintypes.LPWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
    ]
    k32.GetFinalPathNameByHandleW.restype = wintypes.DWORD
    k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    k32.OpenProcess.restype = wintypes.HANDLE
    k32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    k32.GetExitCodeProcess.restype = wintypes.BOOL
    k32.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)
    ]
    k32.QueryFullProcessImageNameW.restype = wintypes.BOOL
    k32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    k32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    k32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(_PROCESSENTRY32W)]
    k32.Process32FirstW.restype = wintypes.BOOL
    k32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(_PROCESSENTRY32W)]
    k32.Process32NextW.restype = wintypes.BOOL

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
    advapi.ConvertSidToStringSidW.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(wintypes.LPWSTR),
    ]
    advapi.ConvertSidToStringSidW.restype = wintypes.BOOL
    advapi.ConvertStringSidToSidW.argtypes = [
        wintypes.LPCWSTR,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    advapi.ConvertStringSidToSidW.restype = wintypes.BOOL
    advapi.BuildTrusteeWithSidW.argtypes = [ctypes.POINTER(_TRUSTEE_W), ctypes.c_void_p]
    advapi.SetEntriesInAclW.argtypes = [
        wintypes.ULONG,
        ctypes.POINTER(_EXPLICIT_ACCESS_W),
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    advapi.SetEntriesInAclW.restype = wintypes.DWORD
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
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    advapi.GetNamedSecurityInfoW.restype = wintypes.DWORD
    advapi.GetSecurityInfo.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.DWORD,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    advapi.GetSecurityInfo.restype = wintypes.DWORD
    advapi.SetSecurityInfo.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.DWORD,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
    ]
    advapi.SetSecurityInfo.restype = wintypes.DWORD
    advapi.GetAclInformation.argtypes = [
        ctypes.c_void_p,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.c_int,
    ]
    advapi.GetAclInformation.restype = wintypes.BOOL
    advapi.GetAce.argtypes = [
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    advapi.GetAce.restype = wintypes.BOOL
    advapi.FreeSid.argtypes = [ctypes.c_void_p]
    advapi.FreeSid.restype = ctypes.c_void_p

    userenv.CreateAppContainerProfile.argtypes = [
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    userenv.CreateAppContainerProfile.restype = ctypes.c_long
    userenv.DeriveAppContainerSidFromAppContainerName.argtypes = [
        wintypes.LPCWSTR,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    userenv.DeriveAppContainerSidFromAppContainerName.restype = ctypes.c_long
    userenv.DeleteAppContainerProfile.argtypes = [wintypes.LPCWSTR]
    userenv.DeleteAppContainerProfile.restype = ctypes.c_long
    return k32, advapi, userenv


def _win32_error(prefix: str) -> HostMutationSandboxUnavailable:
    code = ctypes.get_last_error()
    return HostMutationSandboxUnavailable(
        f"{prefix}: WinError {code}: {ctypes.FormatError(code)}"
    )


def _hresult(value: int) -> int:
    return int(ctypes.c_ulong(value).value)


def _sid_to_string(sid: int | ctypes.c_void_p) -> str:
    k32, advapi, _ = _windows_only()
    text = wintypes.LPWSTR()
    pointer = sid if isinstance(sid, ctypes.c_void_p) else ctypes.c_void_p(sid)
    if not advapi.ConvertSidToStringSidW(pointer, ctypes.byref(text)):
        raise _win32_error("ConvertSidToStringSidW failed")
    try:
        if not text.value:
            raise HostMutationSandboxUnavailable("Windows returned an empty SID string")
        return text.value
    finally:
        if text:
            k32.LocalFree(text)


@contextmanager
def _string_sid(value: str) -> Iterator[int]:
    k32, advapi, _ = _windows_only()
    sid = ctypes.c_void_p()
    if not advapi.ConvertStringSidToSidW(str(value), ctypes.byref(sid)):
        raise _win32_error(f"ConvertStringSidToSidW failed for {value}")
    try:
        yield int(sid.value)
    finally:
        if sid:
            k32.LocalFree(sid)


def _current_process_sid() -> str:
    k32, advapi, _ = _windows_only()
    token = wintypes.HANDLE()
    if not advapi.OpenProcessToken(k32.GetCurrentProcess(), TOKEN_QUERY, ctypes.byref(token)):
        raise _win32_error("OpenProcessToken failed")
    try:
        required = wintypes.DWORD()
        advapi.GetTokenInformation(token, TOKEN_USER, None, 0, ctypes.byref(required))
        if not required.value:
            raise _win32_error("GetTokenInformation(TokenUser) sizing failed")
        buffer = ctypes.create_string_buffer(required.value)
        if not advapi.GetTokenInformation(
            token, TOKEN_USER, buffer, required.value, ctypes.byref(required)
        ):
            raise _win32_error("GetTokenInformation(TokenUser) failed")
        token_user = ctypes.cast(buffer, ctypes.POINTER(_TOKEN_USER)).contents
        return _sid_to_string(int(token_user.User.Sid))
    finally:
        k32.CloseHandle(token)


def final_executable_path(path: Path) -> str:
    """Resolve an existing executable through the same Win32 final-path primitive used at SPAWN."""
    return str(_final_path(path))


def requested_mutation_identity(unique_lease_key: str) -> RequestedMutationIdentity:
    """Provider-derived Host/AppContainer identity sealed before materialization."""
    profile = _profile_name(unique_lease_key)
    return RequestedMutationIdentity(
        host_platform="windows",
        host_user_sid=_current_process_sid(),
        sandbox_kind="appcontainer",
        sandbox_profile=profile,
        sandbox_identity=_derive_appcontainer_sid(profile),
    )


def _process_parent_pid(pid: int) -> int:
    k32, _, _ = _windows_only()
    snapshot = k32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if not snapshot or int(snapshot) == INVALID_HANDLE_VALUE:
        raise _win32_error("CreateToolhelp32Snapshot failed")
    try:
        entry = _PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(entry)
        if not k32.Process32FirstW(snapshot, ctypes.byref(entry)):
            raise _win32_error("Process32FirstW failed")
        while True:
            if int(entry.th32ProcessID) == pid:
                parent = int(entry.th32ParentProcessID)
                if parent <= 0:
                    raise HostMutationSandboxContainmentFailed(
                        "suspended process PPID read-back was empty"
                    )
                return parent
            if not k32.Process32NextW(snapshot, ctypes.byref(entry)):
                break
        raise HostMutationSandboxContainmentFailed("suspended process absent from process snapshot")
    finally:
        k32.CloseHandle(snapshot)


def _process_image_path(process_handle: int) -> str:
    k32, _, _ = _windows_only()
    size = wintypes.DWORD(32768)
    buffer = ctypes.create_unicode_buffer(size.value)
    if not k32.QueryFullProcessImageNameW(process_handle, 0, buffer, ctypes.byref(size)):
        raise _win32_error("QueryFullProcessImageNameW failed")
    return str(_final_path(Path(buffer.value)))


def _process_os_identity(process_handle: int) -> MutationOsIdentityEvidence:
    k32, advapi, _ = _windows_only()
    token = wintypes.HANDLE()
    if not advapi.OpenProcessToken(process_handle, TOKEN_QUERY, ctypes.byref(token)):
        raise _win32_error("OpenProcessToken(suspended process) failed")
    try:
        def token_buffer(info_class: int):
            required = wintypes.DWORD()
            advapi.GetTokenInformation(token, info_class, None, 0, ctypes.byref(required))
            if not required.value:
                raise _win32_error(f"GetTokenInformation({info_class}) sizing failed")
            buffer = ctypes.create_string_buffer(required.value)
            if not advapi.GetTokenInformation(
                token, info_class, buffer, required.value, ctypes.byref(required)
            ):
                raise _win32_error(f"GetTokenInformation({info_class}) failed")
            return buffer

        user_buffer = token_buffer(TOKEN_USER)
        user = ctypes.cast(user_buffer, ctypes.POINTER(_TOKEN_USER)).contents
        app_flag = wintypes.DWORD()
        returned = wintypes.DWORD()
        if not advapi.GetTokenInformation(
            token,
            TOKEN_IS_APPCONTAINER,
            ctypes.byref(app_flag),
            ctypes.sizeof(app_flag),
            ctypes.byref(returned),
        ):
            raise _win32_error("GetTokenInformation(TokenIsAppContainer) failed")
        app_buffer = token_buffer(TOKEN_APPCONTAINER_SID)
        app = ctypes.cast(
            app_buffer, ctypes.POINTER(_TOKEN_APPCONTAINER_INFORMATION)
        ).contents.TokenAppContainer
        if not app:
            raise HostMutationSandboxContainmentFailed("suspended process has no AppContainer SID")
        return MutationOsIdentityEvidence(
            process_user_sid=_sid_to_string(int(user.User.Sid)),
            appcontainer_sid=_sid_to_string(int(app)),
            is_appcontainer=bool(app_flag.value),
        )
    finally:
        k32.CloseHandle(token)


def _profile_name(unique_lease_key: str) -> str:
    digest = hashlib.sha256(unique_lease_key.encode("utf-8")).hexdigest()[:32]
    return f"SentinelX.Mutation.{digest}"


def _ensure_appcontainer_profile(name: str) -> str:
    _, advapi, userenv = _windows_only()
    sid = ctypes.c_void_p()
    hr = userenv.CreateAppContainerProfile(
        name, name, "SentinelX scoped mutation", None, 0, ctypes.byref(sid)
    )
    status = _hresult(hr)
    if status == ERROR_SUCCESS:
        try:
            return _sid_to_string(int(sid.value))
        finally:
            advapi.FreeSid(sid)
    if status != ERROR_ALREADY_EXISTS_HRESULT:
        raise HostMutationSandboxUnavailable(
            f"CreateAppContainerProfile failed for {name}: HRESULT 0x{status:08x}"
        )
    return _derive_appcontainer_sid(name)


def _derive_appcontainer_sid(name: str) -> str:
    _, advapi, userenv = _windows_only()
    sid = ctypes.c_void_p()
    hr = userenv.DeriveAppContainerSidFromAppContainerName(name, ctypes.byref(sid))
    status = _hresult(hr)
    if status != ERROR_SUCCESS:
        raise HostMutationSandboxUnavailable(
            f"DeriveAppContainerSidFromAppContainerName failed: HRESULT 0x{status:08x}"
        )
    try:
        return _sid_to_string(int(sid.value))
    finally:
        advapi.FreeSid(sid)


@contextmanager
def _appcontainer_sid_pointer(name: str) -> Iterator[int]:
    _, advapi, userenv = _windows_only()
    sid = ctypes.c_void_p()
    hr = userenv.DeriveAppContainerSidFromAppContainerName(name, ctypes.byref(sid))
    status = _hresult(hr)
    if status != ERROR_SUCCESS:
        raise HostMutationSandboxUnavailable(
            f"cannot derive AppContainer SID for spawn: HRESULT 0x{status:08x}"
        )
    try:
        yield int(sid.value)
    finally:
        advapi.FreeSid(sid)


def _delete_appcontainer_profile(name: str) -> None:
    _, _, userenv = _windows_only()
    status = _hresult(userenv.DeleteAppContainerProfile(name))
    if status not in (ERROR_SUCCESS, ERROR_FILE_NOT_FOUND_HRESULT):
        raise HostMutationSandboxResidualAuthority(
            f"DeleteAppContainerProfile failed for {name}: HRESULT 0x{status:08x}"
        )


def _normal_path(path: Path) -> Path:
    return Path(os.path.abspath(str(path)))


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        return os.path.commonpath([str(_normal_path(path)), str(_normal_path(root))]).casefold() == str(
            _normal_path(root)
        ).casefold()
    except ValueError:
        return False


def _existing_chain(root: Path, target: Path) -> list[Path]:
    root = _normal_path(root)
    target = _normal_path(target)
    if not _is_relative_to(target, root):
        raise HostMutationSandboxPathViolation(
            f"sandbox path escaped provider workspace root: {target}"
        )
    relative = target.relative_to(root)
    paths = [root]
    current = root
    for part in relative.parts:
        current = current / part
        paths.append(current)
    return paths


def _assert_no_reparse(root: Path, target: Path) -> None:
    for path in _existing_chain(root, target):
        if not path.exists():
            continue
        try:
            attrs = os.lstat(path).st_file_attributes
        except AttributeError:
            _, _, _ = _windows_only()
            attrs = 0
        if attrs & FILE_ATTRIBUTE_REPARSE_POINT:
            raise HostMutationSandboxPathViolation(
                f"reparse/junction component is forbidden in mutation workspace: {path}"
            )


def _strip_final_path_prefix(value: str) -> str:
    if value.startswith("\\\\?\\UNC\\"):
        return "\\\\" + value[8:]
    if value.startswith("\\\\?\\"):
        return value[4:]
    return value


def _final_path(path: Path) -> Path:
    k32, _, _ = _windows_only()
    handle = k32.CreateFileW(
        str(path),
        FILE_READ_ATTRIBUTES,
        FILE_SHARE_ALL,
        None,
        OPEN_EXISTING,
        FILE_FLAG_BACKUP_SEMANTICS,
        None,
    )
    invalid = ctypes.c_void_p(-1).value
    if not handle or int(handle) == invalid:
        raise _win32_error(f"CreateFileW(final-path) failed for {path}")
    try:
        needed = k32.GetFinalPathNameByHandleW(handle, None, 0, 0)
        if not needed:
            raise _win32_error(f"GetFinalPathNameByHandleW sizing failed for {path}")
        buffer = ctypes.create_unicode_buffer(needed + 1)
        written = k32.GetFinalPathNameByHandleW(handle, buffer, len(buffer), 0)
        if not written:
            raise _win32_error(f"GetFinalPathNameByHandleW failed for {path}")
        return Path(_strip_final_path_prefix(buffer.value))
    finally:
        k32.CloseHandle(handle)


def _assert_final_path(path: Path) -> None:
    expected = os.path.normcase(os.path.abspath(str(path)))
    observed = os.path.normcase(os.path.abspath(str(_final_path(path))))
    if observed != expected:
        raise HostMutationSandboxPathViolation(
            f"Windows final path changed mutation binding: expected {expected!r}, observed {observed!r}"
        )


def _set_exact_acl(path: Path, broker_sid: str, app_sid: str | None) -> None:
    k32, advapi, _ = _windows_only()
    identities = [broker_sid] + ([app_sid] if app_sid else [])
    sid_handles: list[ctypes.c_void_p] = []
    new_acl = ctypes.c_void_p()
    try:
        entries = (_EXPLICIT_ACCESS_W * len(identities))()
        for index, identity in enumerate(identities):
            sid = ctypes.c_void_p()
            if not advapi.ConvertStringSidToSidW(identity, ctypes.byref(sid)):
                raise _win32_error(f"ConvertStringSidToSidW ACL failed for {identity}")
            sid_handles.append(sid)
            entries[index].grfAccessPermissions = FILE_ALL_ACCESS
            entries[index].grfAccessMode = SET_ACCESS
            entries[index].grfInheritance = OBJECT_INHERIT_ACE | CONTAINER_INHERIT_ACE
            advapi.BuildTrusteeWithSidW(ctypes.byref(entries[index].Trustee), sid)
        result = advapi.SetEntriesInAclW(
            len(identities), entries, None, ctypes.byref(new_acl)
        )
        if result != ERROR_SUCCESS:
            raise HostMutationSandboxAclViolation(
                f"SetEntriesInAclW failed for {path}: WinError {result}"
            )
        result = advapi.SetNamedSecurityInfoW(
            str(path),
            SE_FILE_OBJECT,
            DACL_SECURITY_INFORMATION | PROTECTED_DACL_SECURITY_INFORMATION,
            None,
            None,
            new_acl,
            None,
        )
        if result != ERROR_SUCCESS:
            raise HostMutationSandboxAclViolation(
                f"SetNamedSecurityInfoW failed for {path}: WinError {result}"
            )
    finally:
        if new_acl:
            k32.LocalFree(new_acl)
        for sid in sid_handles:
            if sid:
                k32.LocalFree(sid)


def _dacl_entries(path: Path) -> list[tuple[str, int, int]]:
    k32, advapi, _ = _windows_only()
    dacl = ctypes.c_void_p()
    descriptor = ctypes.c_void_p()
    result = advapi.GetNamedSecurityInfoW(
        str(path),
        SE_FILE_OBJECT,
        DACL_SECURITY_INFORMATION,
        None,
        None,
        ctypes.byref(dacl),
        None,
        ctypes.byref(descriptor),
    )
    if result != ERROR_SUCCESS:
        raise HostMutationSandboxAclViolation(
            f"GetNamedSecurityInfoW failed for {path}: WinError {result}"
        )
    try:
        info = _ACL_SIZE_INFORMATION()
        if not advapi.GetAclInformation(
            dacl, ctypes.byref(info), ctypes.sizeof(info), ACL_SIZE_INFORMATION_CLASS
        ):
            raise _win32_error(f"GetAclInformation failed for {path}")
        entries: list[tuple[str, int, int]] = []
        for index in range(info.AceCount):
            ace_pointer = ctypes.c_void_p()
            if not advapi.GetAce(dacl, index, ctypes.byref(ace_pointer)):
                raise _win32_error(f"GetAce({index}) failed for {path}")
            ace = ctypes.cast(ace_pointer, ctypes.POINTER(_ACCESS_ALLOWED_ACE)).contents
            if ace.Header.AceType != ACCESS_ALLOWED_ACE_TYPE:
                raise HostMutationSandboxAclViolation(
                    f"unexpected non-allow ACE type {ace.Header.AceType} on exact workspace"
                )
            sid_pointer = int(ace_pointer.value) + _ACCESS_ALLOWED_ACE.SidStart.offset
            entries.append(
                (_sid_to_string(sid_pointer), int(ace.Mask), int(ace.Header.AceFlags))
            )
        return entries
    finally:
        if descriptor:
            k32.LocalFree(descriptor)


def _assert_exact_workspace_acl(path: Path, broker_sid: str, app_sid: str) -> None:
    entries = _dacl_entries(path)
    observed = {sid: (mask, flags) for sid, mask, flags in entries}
    if set(observed) != {broker_sid, app_sid}:
        raise HostMutationSandboxAclViolation(
            f"workspace DACL is not exact broker+scope authority: {sorted(observed)}"
        )
    for sid, (mask, flags) in observed.items():
        if mask != FILE_ALL_ACCESS:
            raise HostMutationSandboxAclViolation(
                f"workspace ACE for {sid} is not exact full subtree authority"
            )
        if flags & INHERITED_ACE:
            raise HostMutationSandboxAclViolation(
                f"workspace ACE for {sid} is inherited; exact DACL protection failed"
            )
        if (flags & (OBJECT_INHERIT_ACE | CONTAINER_INHERIT_ACE)) != (
            OBJECT_INHERIT_ACE | CONTAINER_INHERIT_ACE
        ):
            raise HostMutationSandboxAclViolation(
                f"workspace ACE for {sid} does not inherit to contained objects"
            )


def _assert_no_foreign_appcontainer_sid(path: Path, expected_sid: str | None = None) -> None:
    if not path.exists():
        return
    for sid, _mask, _flags in _dacl_entries(path):
        if sid.startswith("S-1-15-2-") and sid != expected_sid:
            raise HostMutationSandboxAclViolation(
                f"workspace contains stale/foreign AppContainer authority {sid}"
            )


def _run_icacls(
    args: list[str],
    *,
    timeout_seconds: int = 20,
    operation: str = "ACL update",
) -> None:
    try:
        completed = subprocess.run(
            ["icacls", *args],
            capture_output=True,
            creationflags=0x08000000,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise HostMutationSandboxAclViolation(
            f"{operation} timed out after {timeout_seconds}s"
        ) from exc
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).decode(errors="replace").strip()
        raise HostMutationSandboxAclViolation(f"{operation} failed: {detail}")


def _grant_runtime_read(
    root: Path,
    app_sid: str,
    *,
    timeout_seconds: int,
) -> None:
    _assert_no_reparse(root, root)
    _assert_final_path(root)
    try:
        _run_icacls(
            [str(root), "/grant:r", f"*{app_sid}:(OI)(CI)(RX)"],
            timeout_seconds=timeout_seconds,
            operation=f"runtime ACL grant for {root}",
        )
    except HostMutationSandboxAclViolation as grant_error:
        # icacls may time out or fail after Windows has already applied some
        # inherited ACEs. The currently-attempted root is not yet present in
        # the activation rollback list, so compensate here and require exact
        # SID-absence readback before surfacing the original grant failure.
        try:
            _remove_runtime_read(
                root,
                app_sid,
                timeout_seconds=timeout_seconds,
            )
        except HostMutationSandboxResidualAuthority as cleanup_error:
            raise HostMutationSandboxResidualAuthority(
                f"runtime ACL grant for {root} failed and compensating cleanup "
                f"could not prove AppContainer SID removal: {cleanup_error}"
            ) from grant_error
        raise


def _remove_runtime_read(
    root: Path,
    app_sid: str,
    *,
    timeout_seconds: int,
) -> None:
    if not root.exists():
        return
    try:
        entries = _dacl_entries(root)
    except (RuntimeError, OSError, ValueError) as exc:
        raise HostMutationSandboxResidualAuthority(
            f"runtime ACL cleanup could not read back AppContainer SID state on {root}: {exc}"
        ) from exc

    if not any(sid == app_sid for sid, _mask, _flags in entries):
        # Closure is already proven. Avoid a needless ACL mutation on protected
        # runtime roots where the original grant may have failed before the SID
        # was ever installed.
        return

    try:
        _run_icacls(
            [str(root), "/remove:g", f"*{app_sid}"],
            timeout_seconds=timeout_seconds,
            operation=f"runtime ACL cleanup for {root}",
        )
        entries = _dacl_entries(root)
    except (RuntimeError, OSError, ValueError) as exc:
        raise HostMutationSandboxResidualAuthority(
            f"runtime ACL cleanup could not prove AppContainer SID removal on {root}: {exc}"
        ) from exc
    if any(sid == app_sid for sid, _mask, _flags in entries):
        raise HostMutationSandboxResidualAuthority(
            f"runtime ACL cleanup read-back still contains AppContainer SID on {root}"
        )


def _verification_toolchain_traverse_ancestors(root: Path) -> tuple[Path, ...]:
    """Return existing parents that need only FILE_TRAVERSE for AppContainer reachability."""
    canonical = root.resolve(strict=True)
    anchor = Path(canonical.anchor)
    ancestors: list[Path] = []
    current = canonical.parent
    while current != anchor and current != current.parent:
        ancestors.append(current)
        current = current.parent
    return tuple(reversed(ancestors))


def _user32_window_objects() -> tuple[int, int]:
    """Return the broker process window station and current thread desktop."""
    k32, _, _ = _windows_only()
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.GetProcessWindowStation.argtypes = []
    user32.GetProcessWindowStation.restype = wintypes.HANDLE
    user32.GetThreadDesktop.argtypes = [wintypes.DWORD]
    user32.GetThreadDesktop.restype = wintypes.HANDLE

    window_station = user32.GetProcessWindowStation()
    if not window_station:
        raise _win32_error("GetProcessWindowStation failed")
    desktop = user32.GetThreadDesktop(k32.GetCurrentThreadId())
    if not desktop:
        raise _win32_error("GetThreadDesktop failed")
    return int(window_station), int(desktop)


def _window_object_dacl_entries(handle: int, label: str) -> list[tuple[str, int, int]]:
    """Read allow ACEs from a window-station/desktop DACL for bounded proof."""
    k32, advapi, _ = _windows_only()
    dacl = ctypes.c_void_p()
    descriptor = ctypes.c_void_p()
    result = advapi.GetSecurityInfo(
        wintypes.HANDLE(handle),
        SE_WINDOW_OBJECT,
        DACL_SECURITY_INFORMATION,
        None,
        None,
        ctypes.byref(dacl),
        None,
        ctypes.byref(descriptor),
    )
    if result != ERROR_SUCCESS:
        raise HostMutationSandboxAclViolation(
            f"GetSecurityInfo failed for {label}: WinError {result}"
        )
    try:
        info = _ACL_SIZE_INFORMATION()
        if not advapi.GetAclInformation(
            dacl, ctypes.byref(info), ctypes.sizeof(info), ACL_SIZE_INFORMATION_CLASS
        ):
            raise _win32_error(f"GetAclInformation failed for {label}")
        entries: list[tuple[str, int, int]] = []
        for index in range(info.AceCount):
            ace_pointer = ctypes.c_void_p()
            if not advapi.GetAce(dacl, index, ctypes.byref(ace_pointer)):
                raise _win32_error(f"GetAce({index}) failed for {label}")
            header = ctypes.cast(ace_pointer, ctypes.POINTER(_ACE_HEADER)).contents
            if header.AceType != ACCESS_ALLOWED_ACE_TYPE:
                continue
            ace = ctypes.cast(ace_pointer, ctypes.POINTER(_ACCESS_ALLOWED_ACE)).contents
            sid_pointer = int(ace_pointer.value) + _ACCESS_ALLOWED_ACE.SidStart.offset
            entries.append(
                (_sid_to_string(sid_pointer), int(ace.Mask), int(ace.Header.AceFlags))
            )
        return entries
    finally:
        if descriptor:
            k32.LocalFree(descriptor)


def _merge_window_object_access(
    handle: int,
    label: str,
    app_sid: str,
    *,
    mode: int,
    mask: int,
) -> None:
    """Merge/revoke one unique AppContainer ACE while preserving the shared DACL."""
    k32, advapi, _ = _windows_only()
    dacl = ctypes.c_void_p()
    descriptor = ctypes.c_void_p()
    new_acl = ctypes.c_void_p()
    result = advapi.GetSecurityInfo(
        wintypes.HANDLE(handle),
        SE_WINDOW_OBJECT,
        DACL_SECURITY_INFORMATION,
        None,
        None,
        ctypes.byref(dacl),
        None,
        ctypes.byref(descriptor),
    )
    if result != ERROR_SUCCESS:
        raise HostMutationSandboxAclViolation(
            f"GetSecurityInfo failed for {label}: WinError {result}"
        )
    try:
        entries = (_EXPLICIT_ACCESS_W * 1)()
        with _string_sid(app_sid) as sid:
            entries[0].grfAccessPermissions = int(mask)
            entries[0].grfAccessMode = int(mode)
            entries[0].grfInheritance = 0
            advapi.BuildTrusteeWithSidW(ctypes.byref(entries[0].Trustee), ctypes.c_void_p(sid))
            result = advapi.SetEntriesInAclW(1, entries, dacl, ctypes.byref(new_acl))
            if result != ERROR_SUCCESS:
                raise HostMutationSandboxAclViolation(
                    f"SetEntriesInAclW failed for {label}: WinError {result}"
                )
            result = advapi.SetSecurityInfo(
                wintypes.HANDLE(handle),
                SE_WINDOW_OBJECT,
                DACL_SECURITY_INFORMATION,
                None,
                None,
                new_acl,
                None,
            )
            if result != ERROR_SUCCESS:
                raise HostMutationSandboxAclViolation(
                    f"SetSecurityInfo failed for {label}: WinError {result}"
                )
    finally:
        if new_acl:
            k32.LocalFree(new_acl)
        if descriptor:
            k32.LocalFree(descriptor)


def _grant_verification_session_read(app_sid: str) -> tuple[int, int]:
    """Grant read-only access to the service session's window objects.

    USER32-linked descendants created by a LocalSystem service AppContainer
    need read access to the non-interactive session window station/desktop.
    This grant is verification-only, SID-scoped, non-inheriting, and revoked
    during terminalization.
    """
    window_station, desktop = _user32_window_objects()
    objects = (
        (window_station, "window station", WINDOW_STATION_VERIFICATION_READ),
        (desktop, "desktop", DESKTOP_VERIFICATION_READ),
    )
    granted: list[tuple[int, str]] = []
    try:
        for handle, label, mask in objects:
            if any(
                sid == app_sid
                for sid, _ace_mask, _flags in _window_object_dacl_entries(handle, label)
            ):
                raise HostMutationSandboxAclViolation(
                    f"{label} already contains the scope AppContainer SID"
                )
            _merge_window_object_access(
                handle, label, app_sid, mode=GRANT_ACCESS, mask=mask
            )
            granted.append((handle, label))
            observed = {
                sid: ace_mask
                for sid, ace_mask, _flags in _window_object_dacl_entries(handle, label)
            }
            if observed.get(app_sid, 0) & mask != mask:
                raise HostMutationSandboxAclViolation(
                    f"{label} did not retain the required verification read ACE"
                )
        return window_station, desktop
    except Exception:
        for handle, label in reversed(granted):
            try:
                _merge_window_object_access(
                    handle, label, app_sid, mode=REVOKE_ACCESS, mask=0
                )
            except Exception:
                pass
        raise


def _remove_verification_session_read(
    handles: tuple[int, int], app_sid: str
) -> None:
    window_station, desktop = handles
    for handle, label in (
        (desktop, "desktop"),
        (window_station, "window station"),
    ):
        _merge_window_object_access(
            handle, label, app_sid, mode=REVOKE_ACCESS, mask=0
        )
        if any(
            sid == app_sid
            for sid, _ace_mask, _flags in _window_object_dacl_entries(handle, label)
        ):
            raise HostMutationSandboxResidualAuthority(
                f"{label} DACL still contains the mutation AppContainer SID"
            )


def _grant_verification_toolchain_read(root: Path, app_sid: str) -> None:
    """Grant RX only on the sealed provider-owned toolchain tree.

    Provider toolchains may live beneath protected system parents such as
    C:\\Program Files. Verification must never widen authority by rewriting
    ACLs on those ancestors. Existing Host traversal policy is a prerequisite;
    if it is insufficient, readiness fails closed instead of mutating a
    broader parent directory.
    """
    _assert_no_reparse(root, root)
    _assert_final_path(root)
    try:
        _run_icacls([str(root), "/grant:r", f"*{app_sid}:(RX)", "/T", "/C"])
    except Exception:
        if root.exists():
            try:
                _run_icacls([str(root), "/remove:g", f"*{app_sid}", "/T", "/C"])
            except Exception:
                pass
        raise


def _remove_verification_toolchain_read(root: Path, app_sid: str) -> None:
    """Revoke transient RX from the provider-owned toolchain tree."""
    if root.exists():
        _run_icacls([str(root), "/remove:g", f"*{app_sid}", "/T", "/C"])


def _merge_file_access(path: Path, app_sid: str, *, mode: int, mask: int) -> None:
    """Merge/revoke one non-inheriting file ACE without spawning icacls."""
    k32, advapi, _ = _windows_only()
    dacl = ctypes.c_void_p()
    descriptor = ctypes.c_void_p()
    new_acl = ctypes.c_void_p()
    result = advapi.GetNamedSecurityInfoW(
        str(path),
        SE_FILE_OBJECT,
        DACL_SECURITY_INFORMATION,
        None,
        None,
        ctypes.byref(dacl),
        None,
        ctypes.byref(descriptor),
    )
    if result != ERROR_SUCCESS:
        raise HostMutationSandboxAclViolation(
            f"GetNamedSecurityInfoW failed for {path}: WinError {result}"
        )
    try:
        entries = (_EXPLICIT_ACCESS_W * 1)()
        with _string_sid(app_sid) as sid:
            entries[0].grfAccessPermissions = int(mask)
            entries[0].grfAccessMode = int(mode)
            entries[0].grfInheritance = 0
            advapi.BuildTrusteeWithSidW(
                ctypes.byref(entries[0].Trustee), ctypes.c_void_p(sid)
            )
            result = advapi.SetEntriesInAclW(1, entries, dacl, ctypes.byref(new_acl))
            if result != ERROR_SUCCESS:
                raise HostMutationSandboxAclViolation(
                    f"SetEntriesInAclW failed for {path}: WinError {result}"
                )
            result = advapi.SetNamedSecurityInfoW(
                str(path),
                SE_FILE_OBJECT,
                DACL_SECURITY_INFORMATION,
                None,
                None,
                new_acl,
                None,
            )
            if result != ERROR_SUCCESS:
                raise HostMutationSandboxAclViolation(
                    f"SetNamedSecurityInfoW failed for {path}: WinError {result}"
                )
    finally:
        if new_acl:
            k32.LocalFree(new_acl)
        if descriptor:
            k32.LocalFree(descriptor)


def _grant_workspace_traverse(workspace: Path, app_sid: str) -> tuple[Path, ...]:
    """Grant only FILE_TRAVERSE on parents needed to reach an exact workspace."""
    granted: list[Path] = []
    try:
        for ancestor in _verification_toolchain_traverse_ancestors(workspace):
            _assert_final_path(ancestor)
            _merge_file_access(
                ancestor, app_sid, mode=GRANT_ACCESS, mask=FILE_TRAVERSE
            )
            granted.append(ancestor)
        return tuple(granted)
    except Exception:
        for ancestor in reversed(granted):
            try:
                _merge_file_access(
                    ancestor, app_sid, mode=REVOKE_ACCESS, mask=0
                )
            except Exception:
                pass
        raise


def _remove_workspace_traverse(ancestors: Sequence[Path], app_sid: str) -> None:
    for ancestor in reversed(tuple(ancestors)):
        _merge_file_access(ancestor, app_sid, mode=REVOKE_ACCESS, mask=0)


def _pid_alive(pid: int) -> bool:
    k32, _, _ = _windows_only()
    handle = k32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION | SYNCHRONIZE, False, int(pid))
    if not handle:
        error = ctypes.get_last_error()
        if error == 87:  # ERROR_INVALID_PARAMETER: PID no longer exists.
            return False
        raise HostMutationSandboxResidualAuthority(
            f"cannot prove whether process {pid} is gone: WinError {error}: {ctypes.FormatError(error)}"
        )
    try:
        code = wintypes.DWORD()
        if not k32.GetExitCodeProcess(handle, ctypes.byref(code)):
            raise HostMutationSandboxResidualAuthority(
                f"GetExitCodeProcess failed while proving process {pid} quiescent"
            )
        return int(code.value) == STILL_ACTIVE
    finally:
        k32.CloseHandle(handle)


class ManagedMutationProcess:
    def __init__(
        self,
        owner: WindowsMutationSandbox,
        activation: ActivatedMutationSandbox,
        process: SuspendedJobProcess,
    ) -> None:
        self._owner = owner
        self.activation = activation
        self._process = process
        self._released = False

    @property
    def pid(self) -> int:
        return self._process.pid

    @property
    def job_ref(self) -> str:
        return self._process.job_ref

    @property
    def contained(self) -> bool:
        return self._process.contained

    @property
    def breakaway_allowed(self) -> bool:
        return self._process.breakaway_allowed

    @property
    def active_process_count(self) -> int:
        return self._process.active_process_count

    @property
    def exit_code(self) -> int | None:
        return self._process.exit_code

    @property
    def job_handle_closed(self) -> bool:
        return self._process._closed

    def _release(self) -> None:
        if self._released:
            return
        self._process.close()
        self._owner.scope_store.release_runtime_process(
            self.activation.scope_id,
            self.activation.generation,
            job_id=self.job_ref,
            process_id=self.pid,
        )
        self._owner._processes.pop(self.job_ref, None)
        self._released = True

    def wait(self, timeout_seconds: float | None = None) -> bool:
        timeout_ms = None if timeout_seconds is None else int(max(0, timeout_seconds) * 1000)
        done = self._process.wait(timeout_ms)
        if done:
            self._release()
        return done

    def terminate(self) -> None:
        if self._released:
            return
        self._process.terminate()
        self._release()


class WindowsMutationSandbox:
    def __init__(
        self,
        *,
        policy: MutationExecutionPolicy,
        scope_store: MutationScopeStore,
        repository: RepositoryIdentity,
        semantic: SemanticIdentity,
        provider_protected_roots: Sequence[Path] = (),
    ) -> None:
        if sys.platform != "win32":
            raise HostMutationSandboxUnavailable("Windows AppContainer enforcement is required")
        if not policy.configured or not policy.scoped_mutation_enabled or policy.workspace_root is None:
            raise HostMutationSandboxUnavailable("scoped mutation policy/workspace_root is not enabled")
        self.policy = policy
        self.scope_store = scope_store
        self.repository = repository
        self.semantic = semantic
        self.provider_protected_roots = tuple(provider_protected_roots)
        self._processes: dict[str, ManagedMutationProcess] = {}
        self._verification_toolchain_reads: dict[tuple[str, int], Path] = {}
        self._verification_session_reads: dict[tuple[str, int], tuple[int, int]] = {}
        self._workspace_traverse_reads: dict[tuple[str, int], tuple[Path, ...]] = {}
        # Fail early if the required APIs are absent.
        _windows_only()
        self.broker_sid = _current_process_sid()

    def _revalidate(self, scope_id: str, generation: int) -> MutationScopeRecord:
        return self.scope_store.revalidate_scope(
            scope_id,
            generation,
            self.policy,
            self.repository,
            self.semantic,
            provider_protected_roots=self.provider_protected_roots,
        )

    def _materialize_workspace(self, record: MutationScopeRecord) -> tuple[Path, bool]:
        root = _normal_path(self.policy.workspace_root)
        workspace = _normal_path(Path(record.exact_workspace))
        if not root.exists() or not root.is_dir():
            raise HostMutationSandboxPathViolation(
                f"provider mutation workspace_root does not exist: {root}"
            )
        if not _is_relative_to(workspace, root) or workspace == root:
            raise HostMutationSandboxPathViolation("exact workspace escaped provider root")
        _assert_no_reparse(root, workspace)
        _assert_final_path(root)
        existed = workspace.exists()
        if existed and not workspace.is_dir():
            raise HostMutationSandboxPathViolation("exact workspace exists but is not a directory")
        if not existed:
            workspace.mkdir(parents=True, exist_ok=False)
        _assert_no_reparse(root, workspace)
        _assert_final_path(workspace)
        return workspace, existed

    def activate(
        self,
        record: MutationScopeRecord,
        audit_start: MutationAuditStart,
    ) -> ActivatedMutationSandbox:
        """Create/verify exact workspace authority only after durable START."""
        current = self._revalidate(record.scope_id, record.generation)
        assert_audit_scope_binding(audit_start, current)
        if current.active_job_ids or current.active_process_ids:
            raise HostMutationSandboxContainmentFailed(
                "scope already has an active runtime process; duplicate activation is forbidden"
            )
        if current.sandbox_identity is not None and not current.sandbox_write_authority_present:
            raise HostMutationSandboxBindingMismatch(
                "previous sandbox authority was cleared; the same Attempt cannot reactivate it"
            )

        workspace, existed = self._materialize_workspace(current)
        profile_name = _profile_name(current.unique_lease_key)
        app_sid = _ensure_appcontainer_profile(profile_name)
        if current.sandbox_identity not in (None, app_sid):
            raise HostMutationSandboxBindingMismatch(
                "deterministic AppContainer SID does not match durable lease reservation"
            )
        if current.sandbox_identity is None:
            if existed:
                try:
                    if any(workspace.iterdir()):
                        raise HostMutationSandboxPathViolation(
                            "unbound exact workspace existed with material content before activation"
                        )
                    _assert_no_foreign_appcontainer_sid(workspace)
                except Exception:
                    # The deterministic profile was created above but no scope
                    # reservation/ACL authority exists yet. Do not leak it when
                    # a pre-existing workspace fails admission.
                    _delete_appcontainer_profile(profile_name)
                    raise
            current = self.scope_store.reserve_sandbox_identity(
                current.scope_id, current.generation, app_sid
            )
        else:
            _assert_no_foreign_appcontainer_sid(workspace, expected_sid=app_sid)

        activation = ActivatedMutationSandbox(
            scope_id=current.scope_id,
            generation=current.generation,
            workspace_id=current.workspace_id,
            unique_lease_key=current.unique_lease_key,
            workspace=workspace,
            sandbox_identity=app_sid,
            appcontainer_name=profile_name,
            broker_identity=self.broker_sid,
        )
        scope_key = (current.scope_id, current.generation)
        granted_runtime: list[Path] = []
        workspace_traverse: tuple[Path, ...] = ()
        try:
            _set_exact_acl(workspace, self.broker_sid, app_sid)
            _assert_exact_workspace_acl(workspace, self.broker_sid, app_sid)
            workspace_traverse = _grant_workspace_traverse(workspace, app_sid)
            self._workspace_traverse_reads[scope_key] = workspace_traverse
            for root in self.policy.runtime_read_roots:
                runtime_root = _normal_path(root)
                if not runtime_root.exists() or not runtime_root.is_dir():
                    raise HostMutationSandboxPathViolation(
                        f"runtime_read_root is unavailable: {runtime_root}"
                    )
                self.scope_store.reserve_runtime_read_authority(
                    current.scope_id,
                    current.generation,
                    app_sid,
                    str(runtime_root),
                )
                try:
                    _grant_runtime_read(
                        runtime_root,
                        app_sid,
                        timeout_seconds=self.policy.runtime_acl_timeout_seconds,
                    )
                except HostMutationSandboxResidualAuthority:
                    # The exact root marker must remain durable: compensation
                    # could not prove closure.
                    raise
                except (RuntimeError, OSError, ValueError):
                    # _grant_runtime_read only re-raises its original grant
                    # failure after compensating removal has proved SID absence.
                    self.scope_store.clear_runtime_read_authority(
                        current.scope_id,
                        current.generation,
                        app_sid,
                        str(runtime_root),
                    )
                    raise
                granted_runtime.append(runtime_root)
            _assert_no_reparse(_normal_path(self.policy.workspace_root), workspace)
            _assert_final_path(workspace)
            return activation
        except (RuntimeError, OSError, ValueError) as activation_error:
            cleanup_errors: list[str] = []
            traverse = self._workspace_traverse_reads.pop(scope_key, workspace_traverse)
            try:
                _remove_workspace_traverse(traverse, app_sid)
            except (RuntimeError, OSError, ValueError) as cleanup_error:
                cleanup_errors.append(f"workspace traverse grant: {cleanup_error}")
            for runtime_root in reversed(granted_runtime):
                try:
                    _remove_runtime_read(
                        runtime_root,
                        app_sid,
                        timeout_seconds=self.policy.runtime_acl_timeout_seconds,
                    )
                    self.scope_store.clear_runtime_read_authority(
                        current.scope_id,
                        current.generation,
                        app_sid,
                        str(runtime_root),
                    )
                except (RuntimeError, OSError, ValueError) as cleanup_error:
                    cleanup_errors.append(f"runtime read grant: {cleanup_error}")
            try:
                if workspace.exists():
                    _set_exact_acl(workspace, self.broker_sid, None)
            except (RuntimeError, OSError, ValueError) as cleanup_error:
                cleanup_errors.append(f"workspace ACL: {cleanup_error}")
            try:
                _delete_appcontainer_profile(profile_name)
            except (RuntimeError, OSError, ValueError) as cleanup_error:
                cleanup_errors.append(f"AppContainer profile: {cleanup_error}")
            try:
                self.scope_store.clear_sandbox_write_authority(
                    current.scope_id, current.generation, app_sid
                )
            except (RuntimeError, OSError, ValueError) as cleanup_error:
                cleanup_errors.append(f"scope authority marker: {cleanup_error}")
            try:
                self.scope_store.revoke_scope(current.scope_id, current.generation)
            except (RuntimeError, OSError, ValueError) as cleanup_error:
                cleanup_errors.append(f"scope revocation: {cleanup_error}")
            if cleanup_errors:
                raise HostMutationSandboxResidualAuthority(
                    "sandbox activation failed and cleanup could not prove closure: "
                    + "; ".join(cleanup_errors)
                ) from activation_error
            raise

    def _assert_activation_current(
        self, activation: ActivatedMutationSandbox, audit_start: MutationAuditStart
    ) -> MutationScopeRecord:
        record = self._revalidate(activation.scope_id, activation.generation)
        assert_audit_scope_binding(audit_start, record)
        if (
            record.sandbox_identity != activation.sandbox_identity
            or not record.sandbox_write_authority_present
            or _normal_path(Path(record.exact_workspace)) != _normal_path(activation.workspace)
        ):
            raise HostMutationSandboxBindingMismatch("active OS sandbox no longer matches scope")
        _assert_no_reparse(_normal_path(self.policy.workspace_root), activation.workspace)
        _assert_final_path(activation.workspace)
        _assert_exact_workspace_acl(
            activation.workspace, activation.broker_identity, activation.sandbox_identity
        )
        return record

    def materialize_verification(
        self,
        activation: ActivatedMutationSandbox,
        audit_start: MutationAuditStart,
        plan: VerificationRuntimePlan,
    ) -> VerificationMaterialization:
        """Broker-materialize sealed verification inputs after START, before SPAWN."""
        self._assert_activation_current(activation, audit_start)
        if audit_start.verification_intent is None:
            raise HostMutationSandboxBindingMismatch(
                "verification materialization requires a sealed START verification intent"
            )
        if audit_start.verification_intent != plan.audit_intent:
            raise HostMutationSandboxBindingMismatch(
                "verification runtime plan differs from sealed START intent"
            )
        key = (activation.scope_id, activation.generation)
        if key in self._verification_toolchain_reads or key in self._verification_session_reads:
            raise HostMutationSandboxBindingMismatch(
                "verification runtime authority already exists for this scope generation"
            )

        materialized: VerificationMaterialization | None = None
        toolchain_root = _normal_path(plan.profile.toolchain_root)
        try:
            materialized = materialize_verification_runtime(plan, activation.workspace)
            _grant_verification_toolchain_read(toolchain_root, activation.sandbox_identity)
            self._verification_toolchain_reads[key] = toolchain_root
            revalidate_verification_before_spawn(materialized)
            return materialized
        except Exception:
            cleanup_errors: list[str] = []
            try:
                _remove_verification_toolchain_read(toolchain_root, activation.sandbox_identity)
            except (RuntimeError, OSError, ValueError) as cleanup_error:
                cleanup_errors.append(f"verification toolchain read: {cleanup_error}")
                # Keep the tracked root so terminalize() can retry revocation and
                # fail closed if residual read/execute authority cannot be removed.
                if key not in self._verification_toolchain_reads:
                    self._verification_toolchain_reads[key] = toolchain_root
            else:
                self._verification_toolchain_reads.pop(key, None)
            if materialized is not None:
                cleanup_verification_materialization(materialized)
            if cleanup_errors:
                raise HostMutationSandboxResidualAuthority(
                    "; ".join(cleanup_errors)
                )
            raise

    def spawn(
        self,
        activation: ActivatedMutationSandbox,
        *,
        audit: MutationAuditJournal,
        audit_start: MutationAuditStart,
        argv: list[str],
        cwd: Path | None = None,
        env: dict[str, str] | None = None,
        verification: VerificationMaterialization | None = None,
    ) -> ManagedMutationProcess:
        """Create suspended -> bind Job -> durable SPAWN -> only then resume."""
        self._assert_activation_current(activation, audit_start)
        spawn_cwd = _normal_path(cwd or activation.workspace)
        if not _is_relative_to(spawn_cwd, activation.workspace):
            raise HostMutationSandboxPathViolation("sandbox cwd escaped exact workspace")
        if not spawn_cwd.exists() or not spawn_cwd.is_dir():
            raise HostMutationSandboxPathViolation("sandbox cwd is not an existing directory")
        _assert_no_reparse(activation.workspace, spawn_cwd)
        _assert_final_path(spawn_cwd)

        if verification is not None:
            key = (activation.scope_id, activation.generation)
            if audit_start.verification_intent != verification.plan.audit_intent:
                raise HostMutationSandboxBindingMismatch(
                    "verification materialization differs from sealed START intent"
                )
            if verification.workspace.resolve(strict=True) != activation.workspace.resolve(strict=True):
                raise HostMutationSandboxBindingMismatch(
                    "verification materialization belongs to a different exact workspace"
                )
            granted_root = self._verification_toolchain_reads.get(key)
            if granted_root is None or granted_root != _normal_path(verification.toolchain_root):
                raise HostMutationSandboxBindingMismatch(
                    "verification toolchain read authority is absent or mismatched"
                )
            handshake_root = (
                verification.workspace
                / ".sentinelx-verification"
                / "runtime"
                / "descendant-session"
            )
            handshake_root.mkdir(parents=True, exist_ok=True)
            for marker_name in ("root-ready", "authority-ready"):
                marker = handshake_root / marker_name
                if marker.exists():
                    marker.unlink()
            (handshake_root / "request").write_text("required", encoding="ascii")
            revalidate_verification_before_spawn(verification)
        elif audit_start.verification_intent is not None:
            raise HostMutationSandboxBindingMismatch(
                "sealed START verification intent requires pre-SPAWN materialization"
            )

        with _appcontainer_sid_pointer(activation.appcontainer_name) as sid_pointer:
            raw = create_suspended_appcontainer_job_process(
                appcontainer_sid=sid_pointer,
                argv=argv,
                cwd=str(spawn_cwd),
                env=env,
            )
        if not raw.contained or raw.breakaway_allowed:
            raw.close()
            raise HostMutationSandboxContainmentFailed(
                "suspended root did not read back as no-breakaway Job-contained"
            )


        try:
            self.scope_store.bind_runtime_process(
                activation.scope_id,
                activation.generation,
                activation.sandbox_identity,
                job_id=raw.job_ref,
                process_id=raw.pid,
            )
        except (RuntimeError, OSError, ValueError):
            raw.close()
            raise

        managed = ManagedMutationProcess(self, activation, raw)
        self._processes[raw.job_ref] = managed

        def terminate_suspended() -> None:
            raw.terminate()
            managed._release()

        try:
            executable_final_path = _process_image_path(raw._process)
            cwd_final_path = str(_final_path(spawn_cwd))
            spawn_evidence = MutationSpawnEvidence(
                pid=raw.pid,
                ppid=_process_parent_pid(raw.pid),
                executable_final_path=executable_final_path,
                cwd_final_path=cwd_final_path,
                os_identity=_process_os_identity(raw._process),
                containment=MutationContainmentEvidence(
                    job_binding=raw.job_ref,
                    contained=raw.contained,
                    breakaway_allowed=raw.breakaway_allowed,
                    active_process_count=raw.active_process_count,
                ),
            )
            if (
                executable_final_path.casefold()
                != audit_start.process_intent.executable_final_path.casefold()
                or cwd_final_path.casefold() != audit_start.process_intent.cwd_final_path.casefold()
            ):
                raise HostMutationSandboxBindingMismatch(
                    "suspended process final executable/cwd differs from sealed START intent"
                )
            audit.commit_spawn_before_resume(
                audit_start,
                spawn_evidence,
                terminate_suspended=terminate_suspended,
                resume_suspended=raw.resume,
            )
        except (RuntimeError, OSError, ValueError):
            if not managed._released:
                terminate_suspended()
            raise
        return managed

    def enable_pr018_paired_session_read(
        self,
        activation: ActivatedMutationSandbox,
        process: ManagedMutationProcess,
        marker_root: Path,
        *,
        timeout_seconds: float = 30.0,
    ) -> dict[str, object]:
        """Grant exact PR-011 masks only after paired Variant A completed."""
        if (
            self.semantic.project_id != "sentinelx-cloud-core"
            or self.semantic.task_id != "PR-018-unity-6-6-appcontainer-dll-initialization-compatibility-v1"
            or self.semantic.slice_id != "S01"
            or self.repository.path != "bewaterhere-coder/sentinelx-cloud-core"
        ):
            raise HostMutationSandboxBindingMismatch("PR-018 paired diagnostic lineage mismatch")
        if process._owner is not self or process.activation != activation:
            raise HostMutationSandboxBindingMismatch("PR-018 paired process/activation mismatch")
        key = (activation.scope_id, activation.generation)
        if key in self._verification_session_reads:
            raise HostMutationSandboxBindingMismatch("Session-0 authority already exists")
        variant_a_done = marker_root / "variant-a-done"
        variant_b_ready = marker_root / "variant-b-ready"
        deadline = time.monotonic() + max(0.1, float(timeout_seconds))
        while not variant_a_done.exists():
            if process.wait(0):
                raise HostMutationSandboxUnavailable(
                    "paired diagnostic root exited before Variant A completion"
                )
            if time.monotonic() >= deadline:
                raise HostMutationSandboxUnavailable(
                    "paired diagnostic Variant A completion marker timed out"
                )
            time.sleep(0.05)

        window_station, desktop = _user32_window_objects()
        before_window = {
            sid: mask for sid, mask, _flags in _window_object_dacl_entries(
                window_station, "window station"
            )
        }
        before_desktop = {
            sid: mask for sid, mask, _flags in _window_object_dacl_entries(
                desktop, "desktop"
            )
        }
        app_sid = activation.sandbox_identity
        if app_sid in before_window or app_sid in before_desktop:
            raise HostMutationSandboxAclViolation(
                "paired diagnostic SID existed before Variant B grant"
            )
        handles = _grant_verification_session_read(app_sid)
        self._verification_session_reads[key] = handles
        after_window = {
            sid: mask for sid, mask, _flags in _window_object_dacl_entries(
                window_station, "window station"
            )
        }
        after_desktop = {
            sid: mask for sid, mask, _flags in _window_object_dacl_entries(
                desktop, "desktop"
            )
        }
        if (
            after_window.get(app_sid) != WINDOW_STATION_VERIFICATION_READ
            or after_desktop.get(app_sid) != DESKTOP_VERIFICATION_READ
        ):
            raise HostMutationSandboxAclViolation(
                "paired diagnostic did not observe exact PR-011 masks"
            )
        variant_b_ready.write_text("ready", encoding="ascii")
        return {
            "sandbox_identity": app_sid,
            "window_station_mask": WINDOW_STATION_VERIFICATION_READ,
            "desktop_mask": DESKTOP_VERIFICATION_READ,
            "window_station_sid_present_before_b": False,
            "desktop_sid_present_before_b": False,
            "window_station_sid_present_during_b": True,
            "desktop_sid_present_during_b": True,
        }

    def pr018_paired_session_absence(self, app_sid: str) -> dict[str, object]:
        window_station, desktop = _user32_window_objects()
        window_present = any(
            sid == app_sid
            for sid, _mask, _flags in _window_object_dacl_entries(
                window_station, "window station"
            )
        )
        desktop_present = any(
            sid == app_sid
            for sid, _mask, _flags in _window_object_dacl_entries(desktop, "desktop")
        )
        if window_present or desktop_present:
            raise HostMutationSandboxResidualAuthority(
                "paired diagnostic SID remains on Session-0 objects"
            )
        return {
            "sandbox_identity": app_sid,
            "window_station_sid_absent": True,
            "desktop_sid_absent": True,
        }

    def enable_verification_descendants(
        self,
        activation: ActivatedMutationSandbox,
        process: ManagedMutationProcess,
        verification: VerificationMaterialization,
        *,
        timeout_seconds: float = 10.0,
    ) -> None:
        """Enable minimum Session-0 read authority after trusted root startup.

        The verification root first initializes without the extra
        window-station/desktop ACE and enters the provider-owned runner. The
        runner writes root-ready and blocks. Only then does the broker grant
        the unique AppContainer SID read-only Session-0 authority and release
        the runner to create descendants.
        """
        if process._owner is not self or process.activation != activation:
            raise HostMutationSandboxBindingMismatch(
                "verification descendant handshake process/activation mismatch"
            )
        key = (activation.scope_id, activation.generation)
        if key in self._verification_session_reads:
            raise HostMutationSandboxBindingMismatch(
                "verification descendant session authority already exists"
            )
        granted_root = self._verification_toolchain_reads.get(key)
        if granted_root is None or granted_root != _normal_path(verification.toolchain_root):
            raise HostMutationSandboxBindingMismatch(
                "verification toolchain read authority is absent or mismatched"
            )
        handshake_root = (
            verification.workspace
            / ".sentinelx-verification"
            / "runtime"
            / "descendant-session"
        )
        request = handshake_root / "request"
        root_ready = handshake_root / "root-ready"
        authority_ready = handshake_root / "authority-ready"
        if not request.exists():
            raise HostMutationSandboxBindingMismatch(
                "verification descendant handshake request is absent"
            )

        deadline = time.monotonic() + max(0.1, float(timeout_seconds))
        while not root_ready.exists():
            if process.wait(0):
                raise HostMutationSandboxUnavailable(
                    "verification root exited before descendant authority handshake"
                )
            if time.monotonic() >= deadline:
                raise HostMutationSandboxUnavailable(
                    "verification root did not reach trusted descendant handshake"
                )
            time.sleep(0.05)

        session_handles = _grant_verification_session_read(activation.sandbox_identity)
        self._verification_session_reads[key] = session_handles
        try:
            authority_ready.write_text("ready", encoding="ascii")
        except Exception:
            try:
                _remove_verification_session_read(
                    session_handles, activation.sandbox_identity
                )
            finally:
                self._verification_session_reads.pop(key, None)
            raise

    def _cleanup_runtime(self, record: MutationScopeRecord) -> MutationRuntimeClosure:
        for job_id in record.active_job_ids:
            managed = self._processes.pop(job_id, None)
            if managed is not None:
                try:
                    managed._process.terminate()
                finally:
                    managed._process.close()
                    managed._released = True
        represented = {
            str(managed.pid)
            for managed in self._processes.values()
            if managed.job_ref in record.active_job_ids
        }
        for process_id in record.active_process_ids:
            if process_id in represented:
                continue
            try:
                pid = int(process_id)
            except ValueError as exc:
                raise HostMutationSandboxResidualAuthority(
                    f"invalid durable process id {process_id!r}"
                ) from exc
            if _pid_alive(pid):
                # No Job handle means we cannot prove this is still our process;
                # killing by PID risks PID-reuse damage. Fail closed instead.
                raise HostMutationSandboxResidualAuthority(
                    f"process {pid} is still alive but its authoritative Job handle is unavailable"
                )

        app_sid = record.sandbox_identity
        if app_sid:
            workspace = _normal_path(Path(record.exact_workspace))
            if workspace.exists():
                _assert_no_reparse(_normal_path(self.policy.workspace_root), workspace)
                _assert_final_path(workspace)
                _set_exact_acl(workspace, self.broker_sid, None)
                if any(sid == app_sid for sid, _mask, _flags in _dacl_entries(workspace)):
                    raise HostMutationSandboxResidualAuthority(
                        "workspace DACL still contains the mutation AppContainer SID"
                    )
            key = (record.scope_id, record.generation)
            session_handles = self._verification_session_reads.pop(key, None)
            if session_handles is not None:
                _remove_verification_session_read(session_handles, app_sid)
            verification_root = self._verification_toolchain_reads.pop(key, None)
            if verification_root is not None:
                _remove_verification_toolchain_read(verification_root, app_sid)
            durable_runtime_roots = tuple(record.runtime_read_authority_roots)
            runtime_roots = (
                tuple(Path(value) for value in durable_runtime_roots)
                if durable_runtime_roots
                else tuple(self.policy.runtime_read_roots)
            )
            for root in runtime_roots:
                runtime_root = _normal_path(root)
                _remove_runtime_read(
                    runtime_root,
                    app_sid,
                    timeout_seconds=self.policy.runtime_acl_timeout_seconds,
                )
                if durable_runtime_roots:
                    self.scope_store.clear_runtime_read_authority(
                        record.scope_id,
                        record.generation,
                        app_sid,
                        str(runtime_root),
                    )
            workspace_traverse = self._workspace_traverse_reads.pop(
                (record.scope_id, record.generation), ()
            )
            _remove_workspace_traverse(workspace_traverse, app_sid)
            _delete_appcontainer_profile(_profile_name(record.unique_lease_key))

        current = self.scope_store.read_scope(record.scope_id)
        return MutationRuntimeClosure(
            sandbox_identity=app_sid,
            active_job_ids=(),
            active_process_ids=(),
            sandbox_write_authority_present=False,
            runtime_read_authority_roots=current.runtime_read_authority_roots,
        )

    def terminalize(self, scope_id: str, generation: int) -> MutationScopeRecord:
        return self.scope_store.terminalize_scope(
            scope_id,
            generation,
            self.policy,
            self.repository,
            self.semantic,
            provider_protected_roots=self.provider_protected_roots,
            runtime_cleanup=self._cleanup_runtime,
        )


def windows_sandbox_primitives_available() -> tuple[bool, str]:
    """Cheap capability prerequisite check; no profile or filesystem mutation."""
    if sys.platform != "win32":
        return False, "platform is not Windows"
    try:
        k32, advapi, userenv = _windows_only()
        for library, name in (
            (userenv, "CreateAppContainerProfile"),
            (userenv, "DeriveAppContainerSidFromAppContainerName"),
            (k32, "InitializeProcThreadAttributeList"),
            (k32, "UpdateProcThreadAttribute"),
            (k32, "CreateJobObjectW"),
            (k32, "AssignProcessToJobObject"),
            (advapi, "SetNamedSecurityInfoW"),
        ):
            getattr(library, name)
        _current_process_sid()
        return True, "Windows AppContainer/ACL/Job primitives are present"
    except (AttributeError, OSError, RuntimeError, ValueError) as exc:
        return False, str(exc)
