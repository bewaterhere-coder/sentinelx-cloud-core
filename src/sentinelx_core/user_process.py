"""Internal provider-owned Windows active-user process runner (PR-015/S02).

This module exists because PR-015/D4 forbids using ``sentinel_exec``, generic
``script_run``, ``cmd /c``, PowerShell or a caller-selected executable as the
direct-Codex execution boundary. It is the single place where a provider-built
executable + argv list is turned into a contained child process.

Boundary rules enforced here:

- the executable and argv are entirely provider-owned; nothing in this module
  accepts caller text, prompts, shell strings or environment overrides;
- the child is always placed in a Job object with ``KILL_ON_JOB_CLOSE`` and no
  breakaway, so the whole process tree dies with the root process;
- stdout/stderr are captured through inheritable temp-file handles and are
  bounded by ``max_output_bytes``;
- the active-user environment block is created but never returned, logged or
  persisted, so no credential value can leak through a result;
- this module is intentionally NOT registered as an operation or a local-api
  action. It is reachable only from provider code such as
  ``handlers/direct_codex.py``.
"""
from __future__ import annotations

import asyncio
import os
import subprocess
import sys
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

FEATURE_NAME = "host_runtime.user_process_v1"

_CREATE_NO_WINDOW = 0x08000000
_CREATE_UNICODE_ENVIRONMENT = 0x00000400
_STARTF_USESTDHANDLES = 0x00000100
_WAIT_OBJECT_0 = 0x00000000
_WAIT_TIMEOUT = 0x00000102
_INFINITE = 0xFFFFFFFF
_JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9
_JOB_OBJECT_BASIC_ACCOUNTING_INFORMATION = 1
_JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000


class UserProcessError(RuntimeError):
    """Fail-closed error for the internal active-user process runner."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class UserProcessRequest:
    """Provider-built execution request. Caller data can never reach here."""

    executable: str
    argv: Sequence[str]
    cwd: Path
    timeout_seconds: float
    max_output_bytes: int = 65536
    allowed_root: Path | None = None
    environment: Mapping[str, str] | None = None


@dataclass(frozen=True)
class UserProcessResult:
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool
    process_tree_closed: bool
    job_contained: bool
    pid: int
    execution_context: str


def supported() -> bool:
    return sys.platform == "win32"


def _require_windows() -> None:
    if not supported():
        raise UserProcessError(
            "user_process_platform_unsupported",
            "the internal active-user process runner requires Windows",
        )


def _require_containment(cwd: Path, allowed_root: Path | None) -> Path:
    resolved = Path(os.path.abspath(str(cwd)))
    if not resolved.is_dir():
        raise UserProcessError("user_process_workspace_missing", f"cwd is not a directory: {cwd}")
    if allowed_root is None:
        return resolved
    root = Path(os.path.abspath(str(allowed_root)))
    if resolved == root or not _is_relative_to(resolved, root):
        raise UserProcessError(
            "user_process_workspace_escape",
            "process cwd escaped the provider-owned direct-codex workspace root",
        )
    return resolved


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        common = os.path.commonpath([str(path).casefold(), str(root).casefold()])
    except ValueError:
        return False
    return common == str(root).casefold()


def _bound(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...[truncated]"


def _read_capture(handle: Any, limit: int) -> str:
    handle.seek(0)
    raw = handle.read(limit + 1)
    handle.close()
    text = raw.decode("utf-8", errors="replace")
    return _bound(text, limit)


def _windows_api() -> Any:
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    return ctypes, wintypes, kernel32


def active_console_session() -> int | None:
    """Return the active Windows console session id, or ``None`` when absent."""
    if not supported():
        return None
    ctypes_mod, _wintypes_mod, kernel32 = _windows_api()
    kernel32.WTSGetActiveConsoleSessionId.restype = ctypes_mod.c_ulong
    session = int(kernel32.WTSGetActiveConsoleSessionId())
    if session == 0xFFFFFFFF:
        return None
    return session


def _current_session_id(kernel32: Any, ctypes_mod: Any) -> int:
    session = ctypes_mod.c_ulong()
    if not kernel32.ProcessIdToSessionId(os.getpid(), ctypes_mod.byref(session)):
        raise UserProcessError(
            "user_process_context_unavailable", "cannot resolve the current Windows session id"
        )
    return int(session.value)


def _user_token(kernel32: Any, ctypes_mod: Any, wintypes_mod: Any) -> int:
    wtsapi32 = ctypes_mod.WinDLL("wtsapi32", use_last_error=True)
    wtsapi32.WTSQueryUserToken.argtypes = [wintypes_mod.ULONG, ctypes_mod.POINTER(wintypes_mod.HANDLE)]
    wtsapi32.WTSQueryUserToken.restype = wintypes_mod.BOOL
    token = wintypes_mod.HANDLE()
    session = active_console_session()
    if session is None:
        raise UserProcessError(
            "user_process_context_unavailable", "no active interactive Windows console session"
        )
    if not wtsapi32.WTSQueryUserToken(session, ctypes_mod.byref(token)):
        raise UserProcessError(
            "user_process_context_unavailable",
            "WTSQueryUserToken is unavailable for the active console session",
        )
    return int(token.value)


def _job_object(kernel32: Any, ctypes_mod: Any, wintypes_mod: Any) -> int:
    kernel32.CreateJobObjectW.argtypes = [ctypes_mod.c_void_p, wintypes_mod.LPCWSTR]
    kernel32.CreateJobObjectW.restype = wintypes_mod.HANDLE
    handle = kernel32.CreateJobObjectW(None, None)
    if not handle:
        raise UserProcessError("user_process_containment_unavailable", "CreateJobObjectW failed")

    class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes_mod.Structure):
        _fields_ = [  # noqa: RUF012
            ("PerProcessUserTimeLimit", ctypes_mod.c_longlong),
            ("PerJobUserTimeLimit", ctypes_mod.c_longlong),
            ("LimitFlags", wintypes_mod.DWORD),
            ("MinimumWorkingSetSize", ctypes_mod.c_size_t),
            ("MaximumWorkingSetSize", ctypes_mod.c_size_t),
            ("ActiveProcessLimit", wintypes_mod.DWORD),
            ("Affinity", ctypes_mod.c_size_t),
            ("PriorityClass", wintypes_mod.DWORD),
            ("SchedulingClass", wintypes_mod.DWORD),
        ]

    class IO_COUNTERS(ctypes_mod.Structure):
        _fields_ = [  # noqa: RUF012
            ("ReadOperationCount", ctypes_mod.c_ulonglong),
            ("WriteOperationCount", ctypes_mod.c_ulonglong),
            ("OtherOperationCount", ctypes_mod.c_ulonglong),
            ("ReadTransferCount", ctypes_mod.c_ulonglong),
            ("WriteTransferCount", ctypes_mod.c_ulonglong),
            ("OtherTransferCount", ctypes_mod.c_ulonglong),
        ]

    class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes_mod.Structure):
        _fields_ = [  # noqa: RUF012
            ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
            ("IoInfo", IO_COUNTERS),
            ("ProcessMemoryLimit", ctypes_mod.c_size_t),
            ("JobMemoryLimit", ctypes_mod.c_size_t),
            ("PeakProcessMemoryUsed", ctypes_mod.c_size_t),
            ("PeakJobMemoryUsed", ctypes_mod.c_size_t),
        ]

    info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
    info.BasicLimitInformation.LimitFlags = _JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    ok = kernel32.SetInformationJobObject(
        handle,
        _JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
        ctypes_mod.byref(info),
        ctypes_mod.sizeof(info),
    )
    if not ok:
        kernel32.CloseHandle(handle)
        raise UserProcessError(
            "user_process_containment_unavailable", "cannot seal the child job object"
        )
    return int(handle)


def _job_active_processes(kernel32: Any, ctypes_mod: Any, job: int) -> int:
    class JOBOBJECT_BASIC_ACCOUNTING_INFORMATION(ctypes_mod.Structure):
        _fields_ = [  # noqa: RUF012
            ("TotalUserTime", ctypes_mod.c_longlong),
            ("TotalKernelTime", ctypes_mod.c_longlong),
            ("ThisPeriodTotalUserTime", ctypes_mod.c_longlong),
            ("ThisPeriodTotalKernelTime", ctypes_mod.c_longlong),
            ("TotalPageFaultCount", ctypes_mod.c_ulong),
            ("TotalProcesses", ctypes_mod.c_ulong),
            ("ActiveProcesses", ctypes_mod.c_ulong),
            ("TotalTerminatedProcesses", ctypes_mod.c_ulong),
        ]

    info = JOBOBJECT_BASIC_ACCOUNTING_INFORMATION()
    ok = kernel32.QueryInformationJobObject(
        job,
        _JOB_OBJECT_BASIC_ACCOUNTING_INFORMATION,
        ctypes_mod.byref(info),
        ctypes_mod.sizeof(info),
        None,
    )
    if not ok:
        return -1
    return int(info.ActiveProcesses)


def _run_windows(request: UserProcessRequest) -> UserProcessResult:
    import ctypes
    import msvcrt
    from ctypes import wintypes

    ctypes_mod: Any = ctypes
    wintypes_mod: Any = wintypes
    kernel32 = ctypes_mod.WinDLL("kernel32", use_last_error=True)

    cwd = _require_containment(request.cwd, request.allowed_root)
    if not request.argv:
        raise UserProcessError("user_process_invalid_argv", "argv must not be empty")
    argv = [str(item) for item in request.argv]
    if not all(argv):
        raise UserProcessError("user_process_invalid_argv", "argv entries must be non-empty")
    executable = str(request.executable)
    if not os.path.isfile(executable):
        raise UserProcessError("user_process_executable_missing", f"missing executable: {executable}")

    command_line = subprocess.list2cmdline(argv)
    # The capture files stay open until after the child exits because the child
    # inherits their handles: a with-block would close them too early.
    stdout_file = tempfile.TemporaryFile("w+b")  # noqa: SIM115
    stderr_file = tempfile.TemporaryFile("w+b")  # noqa: SIM115
    handles: list[Any] = [stdout_file, stderr_file]

    class STARTUPINFOW(ctypes_mod.Structure):
        _fields_ = [  # noqa: RUF012
            ("cb", wintypes_mod.DWORD),
            ("lpReserved", wintypes_mod.LPWSTR),
            ("lpDesktop", wintypes_mod.LPWSTR),
            ("lpTitle", wintypes_mod.LPWSTR),
            ("dwX", wintypes_mod.DWORD),
            ("dwY", wintypes_mod.DWORD),
            ("dwXSize", wintypes_mod.DWORD),
            ("dwYSize", wintypes_mod.DWORD),
            ("dwXCountChars", wintypes_mod.DWORD),
            ("dwYCountChars", wintypes_mod.DWORD),
            ("dwFillAttribute", wintypes_mod.DWORD),
            ("dwFlags", wintypes_mod.DWORD),
            ("wShowWindow", wintypes_mod.WORD),
            ("cbReserved2", wintypes_mod.WORD),
            ("lpReserved2", ctypes_mod.c_char_p),
            ("hStdInput", wintypes_mod.HANDLE),
            ("hStdOutput", wintypes_mod.HANDLE),
            ("hStdError", wintypes_mod.HANDLE),
        ]

    class PROCESS_INFORMATION(ctypes_mod.Structure):
        _fields_ = [  # noqa: RUF012
            ("hProcess", wintypes_mod.HANDLE),
            ("hThread", wintypes_mod.HANDLE),
            ("dwProcessId", wintypes_mod.DWORD),
            ("dwThreadId", wintypes_mod.DWORD),
        ]

    token = 0
    context = "active_console_session_direct"
    if _current_session_id(kernel32, ctypes_mod) != active_console_session():
        token = _user_token(kernel32, ctypes_mod, wintypes_mod)
        context = "wts_user_token"

    job = _job_object(kernel32, ctypes_mod, wintypes_mod)
    process_info = PROCESS_INFORMATION()
    startup = STARTUPINFOW()
    startup.cb = ctypes_mod.sizeof(startup)
    startup.dwFlags = _STARTF_USESTDHANDLES
    startup.hStdInput = wintypes_mod.HANDLE(0)
    stdout_handle = msvcrt.get_osfhandle(stdout_file.fileno())
    stderr_handle = msvcrt.get_osfhandle(stderr_file.fileno())
    startup.hStdOutput = wintypes_mod.HANDLE(stdout_handle)
    startup.hStdError = wintypes_mod.HANDLE(stderr_handle)
    os.set_handle_inheritable(stdout_handle, True)
    os.set_handle_inheritable(stderr_handle, True)

    env_buffer = None
    creation_flags = _CREATE_NO_WINDOW
    if request.environment is not None:
        env_buffer = _environment_buffer(request.environment, ctypes_mod)
        creation_flags |= _CREATE_UNICODE_ENVIRONMENT

    try:
        if token:
            advapi32 = ctypes_mod.WinDLL("advapi32", use_last_error=True)
            advapi32.CreateProcessAsUserW.argtypes = [
                wintypes_mod.HANDLE,
                wintypes_mod.LPCWSTR,
                wintypes_mod.LPWSTR,
                ctypes_mod.c_void_p,
                ctypes_mod.c_void_p,
                wintypes_mod.BOOL,
                wintypes_mod.DWORD,
                ctypes_mod.c_void_p,
                wintypes_mod.LPCWSTR,
                ctypes_mod.POINTER(STARTUPINFOW),
                ctypes_mod.POINTER(PROCESS_INFORMATION),
            ]
            advapi32.CreateProcessAsUserW.restype = wintypes_mod.BOOL
            created = advapi32.CreateProcessAsUserW(
                wintypes_mod.HANDLE(token),
                executable,
                command_line,
                None,
                None,
                True,
                creation_flags,
                env_buffer,
                str(cwd),
                ctypes_mod.byref(startup),
                ctypes_mod.byref(process_info),
            )
        else:
            kernel32.CreateProcessW.argtypes = [
                wintypes_mod.LPCWSTR,
                wintypes_mod.LPWSTR,
                ctypes_mod.c_void_p,
                ctypes_mod.c_void_p,
                wintypes_mod.BOOL,
                wintypes_mod.DWORD,
                ctypes_mod.c_void_p,
                wintypes_mod.LPCWSTR,
                ctypes_mod.POINTER(STARTUPINFOW),
                ctypes_mod.POINTER(PROCESS_INFORMATION),
            ]
            kernel32.CreateProcessW.restype = wintypes_mod.BOOL
            created = kernel32.CreateProcessW(
                executable,
                command_line,
                None,
                None,
                True,
                creation_flags,
                env_buffer,
                str(cwd),
                ctypes_mod.byref(startup),
                ctypes_mod.byref(process_info),
            )
        if not created:
            raise UserProcessError(
                "user_process_spawn_failed",
                f"cannot start the provider-owned child process: {ctypes_mod.get_last_error()}",
            )

        assigned = kernel32.AssignProcessToJobObject(
            wintypes_mod.HANDLE(job), process_info.hProcess
        )
        contained = False
        if assigned:
            in_job = wintypes_mod.BOOL()
            kernel32.IsProcessInJob.argtypes = [
                wintypes_mod.HANDLE,
                wintypes_mod.HANDLE,
                ctypes_mod.POINTER(wintypes_mod.BOOL),
            ]
            kernel32.IsProcessInJob.restype = wintypes_mod.BOOL
            if kernel32.IsProcessInJob(
                process_info.hProcess, wintypes_mod.HANDLE(job), ctypes_mod.byref(in_job)
            ):
                contained = bool(in_job.value)
        if not contained:
            kernel32.TerminateProcess(process_info.hProcess, 1)
            raise UserProcessError(
                "user_process_containment_unavailable",
                "the provider-owned child process is not contained in its job object",
            )

        timeout_ms = max(1, int(request.timeout_seconds * 1000))
        wait_result = int(
            kernel32.WaitForSingleObject(process_info.hProcess, wintypes_mod.DWORD(timeout_ms))
        )
        timed_out = wait_result == _WAIT_TIMEOUT
        if timed_out:
            kernel32.TerminateJobObject(wintypes_mod.HANDLE(job), 1)

        exit_code = wintypes_mod.DWORD()
        kernel32.GetExitCodeProcess.argtypes = [
            wintypes_mod.HANDLE,
            ctypes_mod.POINTER(wintypes_mod.DWORD),
        ]
        kernel32.GetExitCodeProcess.restype = wintypes_mod.BOOL
        kernel32.GetExitCodeProcess(process_info.hProcess, ctypes_mod.byref(exit_code))

        active = _job_active_processes(kernel32, ctypes_mod, job)
        if active > 0:
            kernel32.TerminateJobObject(wintypes_mod.HANDLE(job), 1)
            active = _job_active_processes(kernel32, ctypes_mod, job)
        tree_closed = active == 0

        pid = int(process_info.dwProcessId)
        kernel32.CloseHandle(process_info.hThread)
        kernel32.CloseHandle(process_info.hProcess)
        kernel32.CloseHandle(wintypes_mod.HANDLE(job))
        if token:
            kernel32.CloseHandle(wintypes_mod.HANDLE(token))

        return UserProcessResult(
            returncode=int(exit_code.value) if not timed_out else 124,
            stdout=_read_capture(stdout_file, request.max_output_bytes),
            stderr=_read_capture(stderr_file, request.max_output_bytes),
            timed_out=timed_out,
            process_tree_closed=tree_closed,
            job_contained=contained,
            pid=pid,
            execution_context=context,
        )
    except UserProcessError:
        for handle in handles:
            try:
                handle.close()
            except OSError:
                pass
        kernel32.CloseHandle(wintypes_mod.HANDLE(job))
        if token:
            kernel32.CloseHandle(wintypes_mod.HANDLE(token))
        raise


def _environment_buffer(environment: Mapping[str, str], ctypes_mod: Any) -> Any:
    """Build a provider-owned unicode environment block (never returned)."""
    body = "".join(f"{key}={value}\0" for key, value in sorted(environment.items()))
    encoded = (body + "\0").encode("utf-16-le")
    buffer = ctypes_mod.create_string_buffer(encoded, len(encoded))
    return ctypes_mod.cast(buffer, ctypes_mod.c_void_p)


async def run_user_scoped_process(request: UserProcessRequest) -> UserProcessResult:
    """Run a provider-built executable as the active user inside a job object."""
    _require_windows()
    return await asyncio.to_thread(_run_windows, request)
