"""Windows user-scoped Git process execution.

This module is intentionally Git-specific.  It is NOT a general run-as-user
primitive.  A LocalSystem SentinelX service may use the active interactive
Windows user's already-loaded credential context (GCM/SSH agent environment)
without ever reading, copying, returning, or persisting the credential itself.

The caller supplies a fixed Git argv.  No shell is involved.
"""
from __future__ import annotations

import asyncio
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

FEATURE_NAME = "host_runtime.git_execution_context_v1"
LEGACY_FEATURE_NAME = "host_runtime.git_authenticated_v1"

_SECRET_URL_RE = re.compile(r"(https?://)([^/@:\s]+):([^/@\s]+)@", re.IGNORECASE)


class UserScopedGitError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def redact_git_output(text: str) -> str:
    """Best-effort redaction for credentials embedded in HTTP(S) URLs."""
    return _SECRET_URL_RE.sub(r"\1***:***@", text)


def user_scoped_git_supported() -> bool:
    return sys.platform == "win32"


def _classify_git_failure(stderr: str) -> str:
    low = stderr.lower()
    if "authentication failed" in low or "permission denied (publickey)" in low:
        return "GitCredentialRejected"
    if (
        "could not read username" in low
        or "terminal prompts disabled" in low
        or "cannot prompt" in low
    ):
        return "GitCredentialInteractiveRequired"
    if "connection was reset" in low or "recv failure" in low:
        return "GitTransportReset"
    if (
        "failed to connect" in low
        or "connection timed out" in low
        or "operation timed out" in low
    ):
        return "GitTransportTimeout"
    if "could not resolve host" in low or "name or service not known" in low:
        return "GitRemoteTemporarilyUnavailable"
    return "GitRemoteFailed"


def _parse_environment_block(ptr: int) -> dict[str, str]:
    """Decode CreateEnvironmentBlock's double-NUL-terminated UTF-16 block."""
    import ctypes

    env: dict[str, str] = {}
    offset = 0
    wchar = ctypes.sizeof(ctypes.c_wchar)
    while True:
        value = ctypes.wstring_at(ptr + offset)
        if not value:
            break
        offset += (len(value) + 1) * wchar
        # Windows environment blocks contain pseudo entries such as =C:=...
        # Preserve them: CreateProcess accepts them and cmd/git may depend on
        # drive-current-directory state.
        if value.startswith("="):
            idx = value.find("=", 1)
        else:
            idx = value.find("=")
        if idx > 0:
            env[value[:idx]] = value[idx + 1 :]
    return env


def _build_environment_buffer(base: dict[str, str]) -> Any:
    """Return a mutable UTF-16 environment block with noninteractive Git guards."""
    import ctypes

    env = dict(base)
    env.update(
        {
            "GIT_TERMINAL_PROMPT": "0",
            "GCM_INTERACTIVE": "Never",
            "GIT_ASKPASS": "",
            "GIT_PAGER": "cat",
            "GIT_OPTIONAL_LOCKS": "0",
        }
    )
    # Environment blocks are conventionally case-insensitive sorted.
    items = [f"{k}={v}" for k, v in sorted(env.items(), key=lambda kv: kv[0].upper())]
    return ctypes.create_unicode_buffer("\0".join(items) + "\0\0")


def _run_windows_user_git(root: Path, args: tuple[str, ...], timeout: float) -> tuple[int, bytes, bytes]:
    """Run fixed Git argv as the active interactive Windows user."""
    if sys.platform != "win32":
        raise UserScopedGitError(
            "GitExecutionContextUnavailable",
            "user-scoped Git execution is available only on Windows in V1",
        )

    import ctypes
    import msvcrt
    from ctypes import wintypes

    git_exe = shutil.which("git")
    if not git_exe:
        raise UserScopedGitError("GitExecutionContextUnavailable", "git.exe is not on PATH")

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    wtsapi32 = ctypes.WinDLL("wtsapi32", use_last_error=True)
    userenv = ctypes.WinDLL("userenv", use_last_error=True)

    INVALID_SESSION = 0xFFFFFFFF
    CREATE_NO_WINDOW = 0x08000000
    CREATE_UNICODE_ENVIRONMENT = 0x00000400
    STARTF_USESTDHANDLES = 0x00000100
    WAIT_TIMEOUT = 0x00000102
    INFINITE = 0xFFFFFFFF

    class STARTUPINFOW(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("lpReserved", wintypes.LPWSTR),
            ("lpDesktop", wintypes.LPWSTR),
            ("lpTitle", wintypes.LPWSTR),
            ("dwX", wintypes.DWORD),
            ("dwY", wintypes.DWORD),
            ("dwXSize", wintypes.DWORD),
            ("dwYSize", wintypes.DWORD),
            ("dwXCountChars", wintypes.DWORD),
            ("dwYCountChars", wintypes.DWORD),
            ("dwFillAttribute", wintypes.DWORD),
            ("dwFlags", wintypes.DWORD),
            ("wShowWindow", wintypes.WORD),
            ("cbReserved2", wintypes.WORD),
            ("lpReserved2", ctypes.POINTER(ctypes.c_byte)),
            ("hStdInput", wintypes.HANDLE),
            ("hStdOutput", wintypes.HANDLE),
            ("hStdError", wintypes.HANDLE),
        ]

    class PROCESS_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("hProcess", wintypes.HANDLE),
            ("hThread", wintypes.HANDLE),
            ("dwProcessId", wintypes.DWORD),
            ("dwThreadId", wintypes.DWORD),
        ]

    kernel32.WTSGetActiveConsoleSessionId.restype = wintypes.DWORD
    wtsapi32.WTSQueryUserToken.argtypes = [wintypes.ULONG, ctypes.POINTER(wintypes.HANDLE)]
    wtsapi32.WTSQueryUserToken.restype = wintypes.BOOL
    userenv.CreateEnvironmentBlock.argtypes = [
        ctypes.POINTER(ctypes.c_void_p),
        wintypes.HANDLE,
        wintypes.BOOL,
    ]
    userenv.CreateEnvironmentBlock.restype = wintypes.BOOL
    userenv.DestroyEnvironmentBlock.argtypes = [ctypes.c_void_p]
    userenv.DestroyEnvironmentBlock.restype = wintypes.BOOL
    advapi32.CreateProcessAsUserW.argtypes = [
        wintypes.HANDLE,
        wintypes.LPCWSTR,
        wintypes.LPWSTR,
        ctypes.c_void_p,
        ctypes.c_void_p,
        wintypes.BOOL,
        wintypes.DWORD,
        ctypes.c_void_p,
        wintypes.LPCWSTR,
        ctypes.POINTER(STARTUPINFOW),
        ctypes.POINTER(PROCESS_INFORMATION),
    ]
    advapi32.CreateProcessAsUserW.restype = wintypes.BOOL

    session_id = kernel32.WTSGetActiveConsoleSessionId()
    if session_id == INVALID_SESSION:
        raise UserScopedGitError(
            "GitExecutionContextUnavailable",
            "no active interactive Windows console session",
        )

    token = wintypes.HANDLE()
    if not wtsapi32.WTSQueryUserToken(session_id, ctypes.byref(token)):
        err = ctypes.get_last_error()
        raise UserScopedGitError(
            "GitExecutionContextUnavailable",
            f"WTSQueryUserToken failed with Windows error {err}",
        )

    env_ptr = ctypes.c_void_p()
    pi = PROCESS_INFORMATION()
    try:
        if not userenv.CreateEnvironmentBlock(ctypes.byref(env_ptr), token, False):
            err = ctypes.get_last_error()
            raise UserScopedGitError(
                "GitExecutionContextUnavailable",
                f"CreateEnvironmentBlock failed with Windows error {err}",
            )

        base_env = _parse_environment_block(env_ptr.value)
        env_buffer = _build_environment_buffer(base_env)

        argv = [
            git_exe,
            "-c",
            "credential.interactive=never",
            "-C",
            str(root),
            "-c",
            "core.fsmonitor=false",
            *args,
        ]
        cmdline = ctypes.create_unicode_buffer(subprocess.list2cmdline(argv))

        with tempfile.TemporaryFile("w+b") as out_file, tempfile.TemporaryFile("w+b") as err_file:
            out_handle = msvcrt.get_osfhandle(out_file.fileno())
            err_handle = msvcrt.get_osfhandle(err_file.fileno())
            os.set_handle_inheritable(out_handle, True)
            os.set_handle_inheritable(err_handle, True)

            si = STARTUPINFOW()
            si.cb = ctypes.sizeof(si)
            si.dwFlags = STARTF_USESTDHANDLES
            si.hStdInput = wintypes.HANDLE(0)
            si.hStdOutput = wintypes.HANDLE(out_handle)
            si.hStdError = wintypes.HANDLE(err_handle)

            ok = advapi32.CreateProcessAsUserW(
                token,
                git_exe,
                cmdline,
                None,
                None,
                True,
                CREATE_NO_WINDOW | CREATE_UNICODE_ENVIRONMENT,
                ctypes.cast(env_buffer, ctypes.c_void_p),
                str(root),
                ctypes.byref(si),
                ctypes.byref(pi),
            )
            if not ok:
                err = ctypes.get_last_error()
                raise UserScopedGitError(
                    "GitExecutionContextUnavailable",
                    f"CreateProcessAsUserW failed with Windows error {err}",
                )

            wait_ms = max(1, int(timeout * 1000))
            result = kernel32.WaitForSingleObject(pi.hProcess, wait_ms)
            if result == WAIT_TIMEOUT:
                kernel32.TerminateProcess(pi.hProcess, 1)
                kernel32.WaitForSingleObject(pi.hProcess, INFINITE)
                raise UserScopedGitError(
                    "GitTransportTimeout",
                    f"user-scoped git exceeded bounded timeout of {timeout:.0f}s",
                )

            exit_code = wintypes.DWORD()
            kernel32.GetExitCodeProcess(pi.hProcess, ctypes.byref(exit_code))
            out_file.seek(0)
            err_file.seek(0)
            return int(exit_code.value), out_file.read(), err_file.read()
    finally:
        if pi.hThread:
            kernel32.CloseHandle(pi.hThread)
        if pi.hProcess:
            kernel32.CloseHandle(pi.hProcess)
        if env_ptr.value:
            userenv.DestroyEnvironmentBlock(env_ptr)
        if token:
            kernel32.CloseHandle(token)


async def run_user_scoped_git(
    root: Path,
    *args: str,
    timeout: float,
) -> tuple[int, bytes, bytes]:
    """Async wrapper around the Windows token-bound Git runner."""
    try:
        return await asyncio.to_thread(_run_windows_user_git, root, tuple(args), timeout)
    except UserScopedGitError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise UserScopedGitError(
            "GitExecutionContextUnavailable",
            f"user-scoped git execution failed: {exc}",
        ) from exc


def classify_result(returncode: int, stderr: bytes) -> str | None:
    """Return a DevForge-compatible reason code for a failed remote Git call."""
    if returncode == 0:
        return None
    text = redact_git_output(stderr.decode("utf-8", "replace"))
    return _classify_git_failure(text)
