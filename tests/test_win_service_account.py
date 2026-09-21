"""sc.exe qc's SERVICE_START_NAME parses with or without a colon.

sc.exe aligns its columns with whitespace, and whether a colon separates the
label from the value depends on Windows version and locale:

    SERVICE_START_NAME : LocalSystem
    SERVICE_START_NAME   LocalSystem      <- no colon

The parser required the colon. On a host whose sc.exe omits it, the account came
back None, _win_is_system_account(None) was False, and a LocalSystem service was
pushed into the underprivileged branch and refused with service_restart_unsafe --
a message the host's own `sc.exe qc` flatly contradicts. Reported by a paying
operator with the SCM readback proving LocalSystem, and it blocked a governed
0.14.1 -> 0.18.0 update that fails closed on a refused restart.
"""

from __future__ import annotations

import pytest

from sentinelx_core.handlers import service


def _parse(stdout: str):
    """Drive the real resolver against canned sc.exe output."""
    import asyncio

    async def _fake_shell(cmd, timeout=10.0):
        return {"stdout": stdout, "exit_code": 0}

    orig = service.run_shell_split
    service.run_shell_split = _fake_shell
    try:
        return asyncio.run(service._win_service_account("SentinelX"))
    finally:
        service.run_shell_split = orig


def test_colon_form_parses():
    assert _parse("        SERVICE_START_NAME : LocalSystem") == "LocalSystem"


def test_no_colon_form_parses():
    """The reported case."""
    assert _parse("        SERVICE_START_NAME   LocalSystem") == "LocalSystem"


def test_localservice_still_parses():
    got = _parse("        SERVICE_START_NAME : NT AUTHORITY\\LocalService")
    assert got == "NT AUTHORITY\\LocalService"


def test_missing_line_is_none():
    assert _parse("        START_TYPE : 3 DEMAND_START") is None


@pytest.mark.parametrize("account,expected", [
    ("LocalSystem", True),
    ("localsystem", True),
    ("NT AUTHORITY\\System", True),
    ("S-1-5-18", True),
    ("NT AUTHORITY\\LocalService", False),
    ("NT AUTHORITY\\NetworkService", False),
    (".\\someuser", False),
    (None, False),
])
def test_system_account_classification(account, expected):
    assert service._win_is_system_account(account) is expected


def test_the_reported_host_is_now_privileged():
    """End of the chain: no-colon LocalSystem -> privileged True -> the
    underprivileged refusal branch is never reached."""
    account = _parse("        SERVICE_START_NAME   LocalSystem")
    assert service._win_is_system_account(account) is True
