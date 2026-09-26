"""transfer/upload can land at the real destination when it is rw -- opt-in.

transfer_file resolved destination_path under upload staging, always. A paying-
quality report asked for it to honour the requested absolute path when the
destination host permits writing there. Made additive: with land_in_place set
AND the target under an rw file_ops entry, the file lands at the real path; in
every other case it falls back to staging exactly as before, so no existing flow
breaks. The rw check is policy.resolve_path(need_write=True) -- the same gate
move and delete use -- so this opens nothing the operator has not.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import tempfile
from pathlib import Path

import pytest

from sentinelx_core.handlers.upload import make_upload_init_handler
from sentinelx_core.policy import FileOpsPath, Policy


def _uid(seed: str) -> str:
    return hashlib.sha256(seed.encode()).hexdigest()[:32]


async def _init(handler, base: Path, target: str, land: bool):
    r = await handler({"target_path": target, "total_size": 10,
                       "upload_id": _uid(target + str(land)), "land_in_place": land})
    meta = json.loads((base / ".sentinelx_uploads" / r["upload_id"] / "meta.json").read_text())
    return meta["target_path"], meta.get("landed_in_place")


@pytest.fixture
def env():
    base = Path(tempfile.mkdtemp()) / "uploads"; base.mkdir()
    rw = Path(tempfile.mkdtemp()) / "ws"; rw.mkdir()
    pol = dataclasses.replace(Policy.empty(),
                              file_ops_paths=(FileOpsPath(path=str(rw), access="rw"),))
    return base, rw, pol


async def test_lands_in_place_under_rw(env):
    base, rw, pol = env
    h = make_upload_init_handler(base, pol)
    tp, landed = await _init(h, base, str(rw / "canary.txt"), True)
    assert landed is True
    assert tp == str(rw / "canary.txt")
    assert str(base) not in tp


async def test_falls_back_to_staging_outside_rw(env):
    base, rw, pol = env
    h = make_upload_init_handler(base, pol)
    tp, landed = await _init(h, base, "/srv/elsewhere/x.txt", True)
    assert landed is False
    assert str(base) in tp  # staged, not the requested absolute path


async def test_default_is_staging_even_when_rw(env):
    """Without the flag, behaviour is unchanged: staging, even for an rw path."""
    base, rw, pol = env
    h = make_upload_init_handler(base, pol)
    tp, landed = await _init(h, base, str(rw / "y.txt"), False)
    assert landed is False
    assert str(base) in tp


async def test_read_only_path_does_not_land(env):
    """An r (not rw) entry must not be a land target -- same as move refusing it."""
    base, rw, pol = env
    ro = Path(tempfile.mkdtemp()) / "readonly"; ro.mkdir()
    pol2 = dataclasses.replace(pol,
        file_ops_paths=pol.file_ops_paths + (FileOpsPath(path=str(ro), access="r"),))
    h = make_upload_init_handler(base, pol2)
    tp, landed = await _init(h, base, str(ro / "z.txt"), True)
    assert landed is False
    assert str(base) in tp


async def test_no_policy_falls_back(env):
    """Older wiring passes no policy; land_in_place then simply cannot apply."""
    base, rw, pol = env
    h = make_upload_init_handler(base)  # no policy
    tp, landed = await _init(h, base, str(rw / "w.txt"), True)
    assert landed is False
    assert str(base) in tp


async def test_traversal_outside_rw_still_refused(env):
    """A '..' target that is neither rw nor safe under base must still be refused,
    not silently landed."""
    base, rw, pol = env
    h = make_upload_init_handler(base, pol)
    from sentinelx_core.executor import HandlerError
    with pytest.raises(HandlerError):
        await _init(h, base, "../../etc/passwd", True)
