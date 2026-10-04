from __future__ import annotations

from pathlib import Path

import pytest

from sentinelx_core.executor import HandlerError
from sentinelx_core.handlers.edit import make_edit_handler
from sentinelx_core.handlers.fileops import (
    make_list_handler,
    make_read_handler,
    make_search_handler,
)
from sentinelx_core.handlers.git_ops import make_git_handler
from sentinelx_core.policy import Policy


BLOCKED = "CanonicalRepositoryMutationBlocked"


def _repo_entry(root: Path) -> dict[str, object]:
    return {
        "root": str(root),
        "repository": {
            "vcs": "git",
            "authority": "github.com",
            "path": "bewaterhere-coder/sentinelx-cloud-core",
        },
        "canonical_branch": "main",
    }


def _policy(tmp_path: Path, canonical: Path) -> Policy:
    return Policy.from_dict(
        {
            "file_ops": {
                "paths": [{"path": str(tmp_path), "access": "rw"}],
            },
            "upload_base": str(tmp_path / "uploads"),
            "mutation_execution": {
                "canonical_repository_firewall_enabled": True,
                "canonical_repositories": [_repo_entry(canonical)],
            },
        }
    )


async def test_fake_canonical_sync_claim_cannot_bypass_edit_firewall(tmp_path: Path) -> None:
    canonical = tmp_path / "repos" / "sentinelx-cloud-core"
    canonical.mkdir(parents=True)
    target = canonical / "README.md"
    target.write_text("keep", encoding="utf-8")
    policy = _policy(tmp_path, canonical)
    handler = make_edit_handler(policy, policy.upload_base)

    with pytest.raises(HandlerError) as exc:
        await handler(
            {
                "path": str(target),
                "mode": "write",
                "new_text": "mutated",
                # Caller-provided role/sync claims are deliberately irrelevant.
                "canonical_sync": True,
                "repository_role": "execution_workspace",
                "repository": {
                    "vcs": "git",
                    "authority": "github.com",
                    "path": "bewaterhere-coder/sentinelx-cloud-core",
                },
            }
        )

    assert exc.value.code == BLOCKED
    assert target.read_text(encoding="utf-8") == "keep"
    assert not list(canonical.glob("README.md.bak.*"))


async def test_canonical_read_list_search_remain_available_under_firewall(
    tmp_path: Path,
) -> None:
    canonical = tmp_path / "repos" / "sentinelx-cloud-core"
    canonical.mkdir(parents=True)
    target = canonical / "README.md"
    target.write_text("canonical needle\n", encoding="utf-8")
    policy = _policy(tmp_path, canonical)

    read_result = await make_read_handler(policy)({"path": str(target)})
    assert read_result["ok"] is True
    assert "canonical needle" in read_result["content"]

    list_result = await make_list_handler(policy)({"path": str(canonical)})
    assert list_result["ok"] is True
    assert any(entry["name"] == "README.md" for entry in list_result["entries"])

    search_result = await make_search_handler(policy)(
        {"path": str(canonical), "pattern": "needle"}
    )
    assert search_result["ok"] is True
    assert any(match["file"] == "README.md" for match in search_result["matches"])


async def test_canonical_git_diff_remains_read_only_and_available(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    canonical = tmp_path / "repos" / "sentinelx-cloud-core"
    canonical.mkdir(parents=True)
    policy = _policy(tmp_path, canonical)
    calls: list[tuple[str, ...]] = []

    async def fake_run_git(root: Path, *args: str, **_kwargs):
        calls.append(tuple(args))
        if args == ("rev-parse", "--show-toplevel"):
            return 0, str(canonical).encode(), b""
        if "--numstat" in args or "--name-status" in args:
            return 0, b"", b""
        if args == ("ls-files", "--others", "--exclude-standard", "-z"):
            return 0, b"", b""
        raise AssertionError(f"unexpected git command: {args}")

    monkeypatch.setattr("sentinelx_core.handlers.git_ops._run_git", fake_run_git)
    result = await make_git_handler(policy)(
        {"operation": "diff", "path": str(canonical)}
    )

    assert result["ok"] is True
    assert result["root"] == str(canonical.resolve(strict=False))
    assert calls[0] == ("rev-parse", "--show-toplevel")
    assert not any("apply" in arg for call in calls for arg in call)
