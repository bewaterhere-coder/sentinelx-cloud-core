"""An unreadable parent gives permission_denied, not internal_error.

read/list resolve, stat (safely, via _stat_safe), and on None probe with
Path.exists() to tell "missing" from "no permission". But exists() traverses
parents too, so on a directory the agent cannot enter the PROBE raised
PermissionError and escaped as a bare "internal_error: [Errno 13]" -- losing the
detailed permission_denied guidance sitting two lines below it.

Reported by an operator whose target sat under a directory the agent's user
could not traverse: 18 reads and 20 lists all surfaced as internal_error.
"""

from __future__ import annotations

import dataclasses
import os
import tempfile
from pathlib import Path

import pytest

from sentinelx_core.executor import HandlerError
from sentinelx_core.handlers.fileops import (
    _probably_missing,
    make_list_handler,
    make_read_handler,
)
from sentinelx_core.policy import FileOpsPath, Policy


@pytest.fixture
def locked(tmp_path):
    """A readable root containing a directory with no traverse permission."""
    root = tmp_path / "root"
    inner = root / "locked" / "inner"
    inner.mkdir(parents=True)
    (inner / "f.json").write_text("{}")
    os.chmod(root / "locked", 0o000)
    pol = dataclasses.replace(
        Policy.empty(), file_ops_paths=(FileOpsPath(path=str(root), access="r"),)
    )
    yield root, pol
    os.chmod(root / "locked", 0o755)  # so tmp cleanup can run


def test_probe_reports_not_missing_when_it_cannot_look(locked):
    root, _ = locked
    # Cannot traverse -> cannot prove absence -> must not claim missing.
    assert _probably_missing(root / "locked" / "inner" / "f.json") is False


def test_probe_still_detects_a_genuinely_absent_path(tmp_path):
    assert _probably_missing(tmp_path / "definitely-not-here") is True


@pytest.mark.skipif(os.geteuid() == 0, reason="root traverses anything")
async def test_read_under_unreadable_parent_is_permission_denied(locked):
    root, pol = locked
    with pytest.raises(HandlerError) as e:
        await make_read_handler(pol)({"path": str(root / "locked" / "inner" / "f.json")})
    assert e.value.code == "permission_denied"


@pytest.mark.skipif(os.geteuid() == 0, reason="root traverses anything")
async def test_list_under_unreadable_parent_is_permission_denied(locked):
    root, pol = locked
    with pytest.raises(HandlerError) as e:
        await make_list_handler(pol)({"path": str(root / "locked" / "inner")})
    assert e.value.code == "permission_denied"


async def test_read_of_absent_path_is_still_not_found(locked):
    root, pol = locked
    with pytest.raises(HandlerError) as e:
        await make_read_handler(pol)({"path": str(root / "nope.json")})
    assert e.value.code == "not_found"


async def test_list_of_absent_path_is_still_not_found(locked):
    root, pol = locked
    with pytest.raises(HandlerError) as e:
        await make_list_handler(pol)({"path": str(root / "nope")})
    assert e.value.code == "not_found"


@pytest.mark.skipif(os.geteuid() == 0, reason="root traverses anything")
async def test_the_error_is_actionable(locked):
    """The message must say it is a Unix permission issue, not an allowlist one."""
    root, pol = locked
    with pytest.raises(HandlerError) as e:
        await make_read_handler(pol)({"path": str(root / "locked" / "inner" / "f.json")})
    msg = str(e.value).lower()
    assert "unix permission" in msg
