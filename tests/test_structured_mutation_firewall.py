from __future__ import annotations

import base64
import json
from pathlib import Path

import pytest

from sentinelx_core.executor import HandlerError
from sentinelx_core.handlers.fsmutate import make_copy_handler, make_delete_handler
from sentinelx_core.handlers.git_ops import make_git_handler
from sentinelx_core.handlers.upload import (
    make_upload_chunk_handler,
    make_upload_complete_handler,
    make_upload_file_handler,
    make_upload_init_handler,
)
from sentinelx_core.policy import Policy


BLOCKED = "CanonicalRepositoryMutationBlocked"


def _repo_entry(root: Path) -> dict[str, object]:
    return {
        "root": str(root),
        "repository": {
            "vcs": "git",
            "authority": "github.com",
            "path": "owner/repo.git",
        },
        "canonical_branch": "main",
    }


def _policy(tmp_path: Path, canonical: Path, *, upload_base: Path | None = None) -> Policy:
    return Policy.from_dict(
        {
            "file_ops": {
                "paths": [{"path": str(tmp_path), "access": "rw"}],
            },
            "upload_base": str(upload_base or (tmp_path / "uploads")),
            "mutation_execution": {
                "canonical_repository_firewall_enabled": True,
                "canonical_repositories": [_repo_entry(canonical)],
            },
        }
    )


async def test_delete_blocks_before_backup_or_destructive_side_effect(tmp_path: Path) -> None:
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    victim = canonical / "victim.txt"
    victim.write_text("keep", encoding="utf-8")
    handler = make_delete_handler(_policy(tmp_path, canonical))

    with pytest.raises(HandlerError) as exc:
        await handler({"path": str(victim)})

    assert exc.value.code == BLOCKED
    assert victim.read_text(encoding="utf-8") == "keep"
    assert not list(canonical.glob("victim.txt.bak.*"))


async def test_copy_can_read_canonical_source_but_cannot_write_canonical_destination(
    tmp_path: Path,
) -> None:
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    source = canonical / "source.txt"
    source.write_text("readable", encoding="utf-8")
    outside = tmp_path / "workspace"
    outside.mkdir()
    policy = _policy(tmp_path, canonical)
    handler = make_copy_handler(policy)

    result = await handler({"src": str(source), "dst": str(outside / "copied.txt")})
    assert result["ok"] is True
    assert (outside / "copied.txt").read_text(encoding="utf-8") == "readable"

    external = outside / "external.txt"
    external.write_text("outside", encoding="utf-8")
    with pytest.raises(HandlerError) as exc:
        await handler({"src": str(external), "dst": str(canonical / "blocked.txt")})
    assert exc.value.code == BLOCKED
    assert not (canonical / "blocked.txt").exists()


async def test_git_apply_patch_blocks_canonical_root_before_git_apply(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    policy = _policy(tmp_path, canonical)
    calls: list[tuple[str, ...]] = []

    async def fake_run_git(root: Path, *args: str, **_kwargs):
        calls.append(tuple(args))
        if args == ("rev-parse", "--show-toplevel"):
            return 0, str(canonical).encode(), b""
        raise AssertionError(f"material git command reached: {args}")

    monkeypatch.setattr("sentinelx_core.handlers.git_ops._run_git", fake_run_git)
    handler = make_git_handler(policy)

    with pytest.raises(HandlerError) as exc:
        await handler(
            {
                "operation": "apply_patch",
                "path": str(canonical),
                "patch": "--- a/x.txt\n+++ b/x.txt\n@@ -0,0 +1 @@\n+x\n",
            }
        )

    assert exc.value.code == BLOCKED
    assert calls == [("rev-parse", "--show-toplevel")]


async def test_upload_init_blocks_canonical_target_before_chunk_staging(tmp_path: Path) -> None:
    upload_base = tmp_path / "uploads"
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    policy = _policy(tmp_path, canonical, upload_base=upload_base)
    init = make_upload_init_handler(upload_base, policy)

    with pytest.raises(HandlerError) as exc:
        await init(
            {
                "target_path": str(canonical / "blocked.bin"),
                "land_in_place": True,
                "overwrite": True,
                "total_size": 1,
            }
        )

    assert exc.value.code == BLOCKED
    assert not (upload_base / ".sentinelx_uploads").exists()
    assert not (canonical / "blocked.bin").exists()


async def test_upload_complete_revalidates_tampered_final_target(tmp_path: Path) -> None:
    upload_base = tmp_path / "uploads"
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    policy = _policy(tmp_path, canonical, upload_base=upload_base)

    # Factory order intentionally mirrors build_registry: init binds the exact
    # immutable Policy object before complete is constructed.
    init = make_upload_init_handler(upload_base, policy)
    chunk = make_upload_chunk_handler(upload_base)
    complete = make_upload_complete_handler(upload_base)

    started = await init(
        {
            "target_path": "safe.bin",
            "overwrite": True,
            "total_size": 1,
        }
    )
    upload_id = started["upload_id"]
    await chunk(
        {
            "upload_id": upload_id,
            "index": 0,
            "content_base64": base64.b64encode(b"x").decode("ascii"),
        }
    )

    meta_path = upload_base / ".sentinelx_uploads" / upload_id / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["target_path"] = str(canonical / "tampered.bin")
    meta_path.write_text(json.dumps(meta), encoding="utf-8")

    with pytest.raises(HandlerError) as exc:
        await complete({"upload_id": upload_id})

    assert exc.value.code == BLOCKED
    assert not (canonical / "tampered.bin").exists()


async def test_single_upload_blocks_when_provider_staging_is_canonical(tmp_path: Path) -> None:
    upload_base = tmp_path / "uploads"
    canonical = upload_base / ".sentinelx_uploads"
    policy = _policy(tmp_path, canonical, upload_base=upload_base)
    handler = make_upload_file_handler(policy, upload_base)

    with pytest.raises(HandlerError) as exc:
        await handler(
            {
                "target_path": "safe.bin",
                "overwrite": True,
                "content_base64": base64.b64encode(b"x").decode("ascii"),
            }
        )

    assert exc.value.code == BLOCKED
    assert not canonical.exists()
    assert not (upload_base / "safe.bin").exists()


async def test_upload_chunk_revalidates_provider_staging_before_part_write(tmp_path: Path) -> None:
    upload_base = tmp_path / "uploads"
    upload_id = "a" * 32
    upload_dir = upload_base / ".sentinelx_uploads" / upload_id
    canonical = upload_dir / "parts"
    policy = _policy(tmp_path, canonical, upload_base=upload_base)

    # Factory construction mirrors build_registry: upload_init binds the exact
    # Policy before upload_chunk is built. Test setup creates only the metadata
    # precondition; the handler must refuse creating the canonical parts root.
    make_upload_init_handler(upload_base, policy)
    upload_dir.mkdir(parents=True)
    (upload_dir / "meta.json").write_text(
        json.dumps({"target_path": str(upload_base / "safe.bin")}),
        encoding="utf-8",
    )
    chunk = make_upload_chunk_handler(upload_base)

    with pytest.raises(HandlerError) as exc:
        await chunk(
            {
                "upload_id": upload_id,
                "index": 0,
                "content_base64": base64.b64encode(b"x").decode("ascii"),
            }
        )

    assert exc.value.code == BLOCKED
    assert not canonical.exists()