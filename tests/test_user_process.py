"""PR-015/S02 Task 3: provider-owned low-integrity process launch and
integrity/session read-back in ``sentinelx_core.user_process``.

These tests exercise ``run_user_scoped_process`` directly (not through the
direct-Codex handler) so the Task 3 contract stands on its own:

- the provider can request the child to start at a lowered Mandatory Integrity
  Control level;
- the OS-visible integrity level and Windows session of the running child are
  read back from the live process and surfaced on the result, so the containment
  is an observed fact rather than a passed-through promise;
- only the provider-owned ``None`` (active user) and ``low`` levels are accepted;
  any other level is rejected fail-closed;
- the process cwd is still contained to the provider-owned workspace root.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from sentinelx_core import windows_integrity
from sentinelx_core.user_process import (
    UserProcessError,
    UserProcessRequest,
    active_console_session,
    run_user_scoped_process,
)

WINDOWS_ONLY = pytest.mark.skipif(
    not sys.platform.startswith("win"), reason="Windows active-user process substrate"
)


def _request(cwd: Path, *, integrity_level: str | None = None) -> UserProcessRequest:
    return UserProcessRequest(
        executable=sys.executable,
        argv=[sys.executable, "-c", "import sys; sys.stdout.write('child-ok')"],
        cwd=cwd,
        timeout_seconds=30,
        max_output_bytes=65536,
        integrity_level=integrity_level,
    )


@WINDOWS_ONLY
@pytest.mark.asyncio
async def test_default_launch_reads_back_active_integrity_and_session(tmp_path: Path) -> None:
    result = await run_user_scoped_process(_request(tmp_path))
    assert result.returncode == 0
    assert "child-ok" in result.stdout
    # Job containment is always applied by the provider-owned runner.
    assert result.job_contained is True
    assert result.process_tree_closed is True
    # Read-back reflects the OS-visible identity, not a promise.
    assert result.integrity_level is not None
    assert result.session_id is not None
    expected_session = active_console_session()
    if expected_session is not None:
        assert result.session_id == expected_session


@WINDOWS_ONLY
@pytest.mark.asyncio
async def test_low_integrity_launch_reads_back_low_level(tmp_path: Path) -> None:
    result = await run_user_scoped_process(
        _request(tmp_path, integrity_level=windows_integrity.LOW_INTEGRITY)
    )
    assert result.returncode == 0
    assert "child-ok" in result.stdout
    # The child started at the lowered MIC level: the read-back is the real
    # token integrity, not the requested value echoed back.
    assert result.integrity_level == windows_integrity.LOW_INTEGRITY
    expected_session = active_console_session()
    if expected_session is not None:
        assert result.session_id == expected_session
    # Provider-owned job containment is still applied for the low child.
    assert result.job_contained is True
    assert result.process_tree_closed is True


@WINDOWS_ONLY
@pytest.mark.asyncio
async def test_unsupported_integrity_level_rejected(tmp_path: Path) -> None:
    # Only None (active user) and "low" are provider-owned levels; anything
    # else must fail closed before any child is spawned.
    with pytest.raises(UserProcessError) as exc:
        await run_user_scoped_process(_request(tmp_path, integrity_level="high"))
    assert exc.value.code == "user_process_invalid_integrity_level"


@WINDOWS_ONLY
@pytest.mark.asyncio
async def test_process_cwd_outside_workspace_is_refused(tmp_path: Path) -> None:
    foreign = tmp_path.parent / "foreign-workspace"
    foreign.mkdir()
    request = UserProcessRequest(
        executable=sys.executable,
        argv=[sys.executable, "-c", "pass"],
        cwd=tmp_path,
        timeout_seconds=10,
        allowed_root=foreign,
    )
    with pytest.raises(UserProcessError) as exc:
        await run_user_scoped_process(request)
    assert exc.value.code == "user_process_workspace_escape"
