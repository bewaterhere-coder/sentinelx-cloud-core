"""Shared Windows process creation helpers.

The ordinary :func:`spawn_kwargs` path keeps historical no-console-window
behaviour. Scoped mutation uses the stronger suspended AppContainer path below:
CreateProcessW(CREATE_SUSPENDED) -> no-breakaway kill-on-close Job assignment ->
caller-owned durable spawn evidence -> ResumeThread.
"""
from __future__ import annotations

import ctypes
import os
import subprocess
import sys
import uuid
from ctypes import wintypes
from dataclasses import dataclass
from typing import Any

CREATE_SUSPENDED = 0x00000004
CREATE_UNICODE_ENVIRONMENT = 0x00000400
EXTENDED_STARTUPINFO_PRESENT = 0x00080000
CREATE_NO_WINDOW = 0x08000000
PROC_THREAD_ATTRIBUTE_SECURITY_CAPABILITIES = 0x00020009
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
JOB_OBJECT_LIMIT_BREAKAWAY_OK = 0x00000800
JOB_OBJECT_LIMIT_SILENT_BREAKAWAY_OK = 0x00001000
WAIT_OBJECT_0 = 0
WAIT_TIMEOUT = 258
STILL_ACTIVE = 259


class WindowsSpawnError(RuntimeError):
    code = "HostMutationSandboxContainmentFailed"


def spawn_kwargs(**extra: Any) -> dict[str, Any]:
    """Keyword arguments for asyncio/subprocess ordinary child creation."""
    kwargs = dict(extra)
    if sys.platform == "win32":
        kwargs["creationflags"] = kwargs.get("creationflags", 0) | CREATE_NO_WINDOW
    return kwargs


class _SID_AND_ATTRIBUTES(ctypes.Structure):
    _fields_ = [("Sid", ctypes.c_void_p), ("Attributes", wintypes.DWORD)]


class _SECURITY_CAPABILITIES(ctypes.Structure):
    _fields_ = [
        ("AppContainerSid", ctypes.c_void_p),
        ("Capabilities", ctypes.POINTER(_SID_AND_ATTRIBUTES)),
        ("CapabilityCount", wintypes.DWORD),
        ("Reserved", wintypes.DWORD),
    ]


class _STARTUPINFOW(ctypes.Structure):
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


class _STARTUPINFOEXW(ctypes.Structure):
    _fields_ = [("StartupInfo", _STARTUPINFOW), ("lpAttributeList", ctypes.c_void_p)]


class _PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("hProcess", wintypes.HANDLE),
        ("hThread", wintypes.HANDLE),
        ("dwProcessId", wintypes.DWORD),
        ("dwThreadId", wintypes.DWORD),
    ]


class _IO_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("ReadOperationCount", ctypes.c_ulonglong),
        ("WriteOperationCount", ctypes.c_ulonglong),
        ("OtherOperationCount", ctypes.c_ulonglong),
        ("ReadTransferCount", ctypes.c_ulonglong),
        ("WriteTransferCount", ctypes.c_ulonglong),
        ("OtherTransferCount", ctypes.c_ulonglong),
    ]


class _JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_longlong),
        ("PerJobUserTimeLimit", ctypes.c_longlong),
        ("LimitFlags", wintypes.DWORD),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", wintypes.DWORD),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", wintypes.DWORD),
        ("SchedulingClass", wintypes.DWORD),
    ]


class _JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", _JOBOBJECT_BASIC_LIMIT_INFORMATION),
        ("IoInfo", _IO_COUNTERS),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


class _JOBOBJECT_BASIC_ACCOUNTING_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("TotalUserTime", ctypes.c_longlong),
        ("TotalKernelTime", ctypes.c_longlong),
        ("ThisPeriodTotalUserTime", ctypes.c_longlong),
        ("ThisPeriodTotalKernelTime", ctypes.c_longlong),
        ("TotalPageFaultCount", wintypes.DWORD),
        ("TotalProcesses", wintypes.DWORD),
        ("ActiveProcesses", wintypes.DWORD),
        ("TotalTerminatedProcesses", wintypes.DWORD),
    ]


def _windows_only() -> ctypes.WinDLL:
    if sys.platform != "win32":
        raise WindowsSpawnError("Windows suspended Job spawning is unavailable on this platform")
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.InitializeProcThreadAttributeList.argtypes = [
        ctypes.c_void_p,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.POINTER(ctypes.c_size_t),
    ]
    k32.InitializeProcThreadAttributeList.restype = wintypes.BOOL
    k32.UpdateProcThreadAttribute.argtypes = [
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.c_size_t,
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.c_void_p,
        ctypes.c_void_p,
    ]
    k32.UpdateProcThreadAttribute.restype = wintypes.BOOL
    k32.DeleteProcThreadAttributeList.argtypes = [ctypes.c_void_p]
    k32.CreateProcessW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.LPWSTR,
        ctypes.c_void_p,
        ctypes.c_void_p,
        wintypes.BOOL,
        wintypes.DWORD,
        ctypes.c_void_p,
        wintypes.LPCWSTR,
        ctypes.POINTER(_STARTUPINFOW),
        ctypes.POINTER(_PROCESS_INFORMATION),
    ]
    k32.CreateProcessW.restype = wintypes.BOOL
    k32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    k32.CreateJobObjectW.restype = wintypes.HANDLE
    k32.SetInformationJobObject.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
    ]
    k32.SetInformationJobObject.restype = wintypes.BOOL
    k32.QueryInformationJobObject.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
    ]
    k32.QueryInformationJobObject.restype = wintypes.BOOL
    k32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    k32.AssignProcessToJobObject.restype = wintypes.BOOL
    k32.IsProcessInJob.argtypes = [
        wintypes.HANDLE,
        wintypes.HANDLE,
        ctypes.POINTER(wintypes.BOOL),
    ]
    k32.IsProcessInJob.restype = wintypes.BOOL
    k32.ResumeThread.argtypes = [wintypes.HANDLE]
    k32.ResumeThread.restype = wintypes.DWORD
    k32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    k32.WaitForSingleObject.restype = wintypes.DWORD
    k32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    k32.GetExitCodeProcess.restype = wintypes.BOOL
    k32.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
    k32.TerminateJobObject.restype = wintypes.BOOL
    k32.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
    k32.TerminateProcess.restype = wintypes.BOOL
    k32.CloseHandle.argtypes = [wintypes.HANDLE]
    k32.CloseHandle.restype = wintypes.BOOL
    return k32


def _win_error(prefix: str) -> WindowsSpawnError:
    code = ctypes.get_last_error()
    return WindowsSpawnError(f"{prefix}: WinError {code}: {ctypes.FormatError(code)}")


def _environment_block(env: dict[str, str] | None):
    if env is None:
        return None, None
    merged = {str(k): str(v) for k, v in env.items()}
    body = "\0".join(f"{key}={merged[key]}" for key in sorted(merged, key=str.upper)) + "\0\0"
    buffer = ctypes.create_unicode_buffer(body)
    return buffer, ctypes.cast(buffer, ctypes.c_void_p)


@dataclass
class SuspendedJobProcess:
    """One root process sealed inside a kill-on-close, no-breakaway Job."""

    pid: int
    job_ref: str
    _process: int
    _thread: int
    _job: int
    _resumed: bool = False
    _closed: bool = False
    _last_exit_code: int | None = None

    @property
    def contained(self) -> bool:
        if self._closed:
            return False
        k32 = _windows_only()
        result = wintypes.BOOL()
        if not k32.IsProcessInJob(self._process, self._job, ctypes.byref(result)):
            raise _win_error("IsProcessInJob failed")
        return bool(result.value)

    @property
    def breakaway_allowed(self) -> bool:
        """The scoped mutation Job never enables either breakaway flag."""
        if self._closed:
            return False
        k32 = _windows_only()
        info = _JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        returned = wintypes.DWORD()
        if not k32.QueryInformationJobObject(
            self._job, 9, ctypes.byref(info), ctypes.sizeof(info), ctypes.byref(returned)
        ):
            raise _win_error("QueryInformationJobObject limits failed")
        flags = info.BasicLimitInformation.LimitFlags
        return bool(flags & (JOB_OBJECT_LIMIT_BREAKAWAY_OK | JOB_OBJECT_LIMIT_SILENT_BREAKAWAY_OK))

    @property
    def active_process_count(self) -> int:
        if self._closed:
            return 0
        k32 = _windows_only()
        info = _JOBOBJECT_BASIC_ACCOUNTING_INFORMATION()
        returned = wintypes.DWORD()
        if not k32.QueryInformationJobObject(
            self._job, 1, ctypes.byref(info), ctypes.sizeof(info), ctypes.byref(returned)
        ):
            raise _win_error("QueryInformationJobObject accounting failed")
        return int(info.ActiveProcesses)

    def resume(self) -> None:
        if self._closed:
            raise WindowsSpawnError("cannot resume a closed Job process")
        if self._resumed:
            raise WindowsSpawnError("scoped mutation root process was already resumed")
        k32 = _windows_only()
        previous = k32.ResumeThread(self._thread)
        if previous == 0xFFFFFFFF:
            raise _win_error("ResumeThread failed")
        self._resumed = True

    def wait(self, timeout_ms: int | None = None) -> bool:
        if self._closed:
            return True
        k32 = _windows_only()
        timeout = 0xFFFFFFFF if timeout_ms is None else max(0, int(timeout_ms))
        result = k32.WaitForSingleObject(self._process, timeout)
        if result == WAIT_OBJECT_0:
            return True
        if result == WAIT_TIMEOUT:
            return False
        raise _win_error("WaitForSingleObject failed")

    @property
    def exit_code(self) -> int | None:
        if self._closed:
            # Fail-closed diagnostic readback: the raw child status sampled
            # while the process handle was still open (PR-026 S01).
            return self._last_exit_code
        k32 = _windows_only()
        code = wintypes.DWORD()
        if not k32.GetExitCodeProcess(self._process, ctypes.byref(code)):
            raise _win_error("GetExitCodeProcess failed")
        if code.value == STILL_ACTIVE:
            return None
        return int(code.value)

    def terminate(self, exit_code: int = 1) -> None:
        if self._closed:
            return
        k32 = _windows_only()
        if self.active_process_count:
            if not k32.TerminateJobObject(self._job, int(exit_code)):
                raise _win_error("TerminateJobObject failed")
            if not self.wait(5000):
                raise WindowsSpawnError("Job termination did not quiesce the root process")
        if self.active_process_count != 0:
            raise WindowsSpawnError("Job still reports active processes after termination")

    def close(self) -> None:
        if self._closed:
            return
        k32 = _windows_only()
        try:
            # Closing the Job is itself a kill boundary because KILL_ON_JOB_CLOSE
            # is mandatory. Explicit termination gives deterministic read-back.
            if self.active_process_count:
                self.terminate()
        finally:
            # Sample the raw child exit status while the process handle is
            # still open, so startup-failure diagnostics survive handle
            # closure (PR-026 S01). Unavailable status stays explicitly None.
            try:
                self._last_exit_code = self.exit_code
            except Exception:
                self._last_exit_code = None
            for handle in (self._thread, self._process, self._job):
                if handle:
                    k32.CloseHandle(handle)
            self._closed = True


def create_suspended_appcontainer_job_process(
    *,
    appcontainer_sid: int,
    argv: list[str],
    cwd: str,
    env: dict[str, str] | None = None,
) -> SuspendedJobProcess:
    """Create an AppContainer root suspended, then seal it into a Job.

    The returned process has executed **zero untrusted instructions**. The
    caller must durably record PROCESS_SPAWNED and only then call ``resume``.
    """
    if not argv or not all(isinstance(value, str) and value for value in argv):
        raise ValueError("argv must contain non-empty strings")
    if not appcontainer_sid:
        raise ValueError("appcontainer_sid is required")
    if not os.path.isdir(cwd):
        raise WindowsSpawnError(f"sandbox cwd is not an existing directory: {cwd}")

    k32 = _windows_only()
    size = ctypes.c_size_t(0)
    k32.InitializeProcThreadAttributeList(None, 1, 0, ctypes.byref(size))
    if not size.value:
        raise _win_error("InitializeProcThreadAttributeList sizing failed")
    attribute_buffer = ctypes.create_string_buffer(size.value)
    if not k32.InitializeProcThreadAttributeList(attribute_buffer, 1, 0, ctypes.byref(size)):
        raise _win_error("InitializeProcThreadAttributeList failed")

    security = _SECURITY_CAPABILITIES(ctypes.c_void_p(appcontainer_sid), None, 0, 0)
    process_info = _PROCESS_INFORMATION()
    job = 0
    created = False
    try:
        if not k32.UpdateProcThreadAttribute(
            attribute_buffer,
            0,
            PROC_THREAD_ATTRIBUTE_SECURITY_CAPABILITIES,
            ctypes.byref(security),
            ctypes.sizeof(security),
            None,
            None,
        ):
            raise _win_error("UpdateProcThreadAttribute security capabilities failed")

        startup = _STARTUPINFOEXW()
        startup.StartupInfo.cb = ctypes.sizeof(startup)
        startup.lpAttributeList = ctypes.cast(attribute_buffer, ctypes.c_void_p)
        command_line = ctypes.create_unicode_buffer(subprocess.list2cmdline(argv))
        env_buffer, env_pointer = _environment_block(env)
        _ = env_buffer  # keep the UTF-16 block alive through CreateProcessW
        flags = (
            CREATE_SUSPENDED
            | CREATE_NO_WINDOW
            | EXTENDED_STARTUPINFO_PRESENT
            | (CREATE_UNICODE_ENVIRONMENT if env is not None else 0)
        )
        if not k32.CreateProcessW(
            None,
            command_line,
            None,
            None,
            False,
            flags,
            env_pointer,
            str(cwd),
            ctypes.byref(startup.StartupInfo),
            ctypes.byref(process_info),
        ):
            raise _win_error("CreateProcessW(AppContainer) failed")
        created = True

        job = k32.CreateJobObjectW(None, None)
        if not job:
            raise _win_error("CreateJobObjectW failed")
        limits = _JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        limits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not k32.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            raise _win_error("SetInformationJobObject kill-on-close failed")
        if not k32.AssignProcessToJobObject(job, process_info.hProcess):
            raise _win_error("AssignProcessToJobObject failed")
        in_job = wintypes.BOOL()
        if not k32.IsProcessInJob(process_info.hProcess, job, ctypes.byref(in_job)):
            raise _win_error("IsProcessInJob verification failed")
        if not in_job.value:
            raise WindowsSpawnError("root process was not observed in the mutation Job")

        result = SuspendedJobProcess(
            pid=int(process_info.dwProcessId),
            job_ref=f"sxjob_{uuid.uuid4().hex}",
            _process=int(process_info.hProcess),
            _thread=int(process_info.hThread),
            _job=int(job),
        )
        # Read back the exact policy: kill-on-close present, no breakaway flags.
        if result.breakaway_allowed:
            raise WindowsSpawnError("mutation Job unexpectedly permits process breakaway")
        return result
    except Exception:
        if created and process_info.hProcess:
            if job:
                k32.TerminateJobObject(job, 1)
            else:
                k32.TerminateProcess(process_info.hProcess, 1)
        if process_info.hThread:
            k32.CloseHandle(process_info.hThread)
        if process_info.hProcess:
            k32.CloseHandle(process_info.hProcess)
        if job:
            k32.CloseHandle(job)
        raise
    finally:
        k32.DeleteProcThreadAttributeList(attribute_buffer)
