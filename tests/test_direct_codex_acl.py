"""PR-015 R7 repair: exact-workspace Windows ACL handoff for the real Codex
workspace-write sandbox.

Physical Windows tests (real NTFS owner/DACL APIs, no mocks):

- the handoff transfers ownership of the exact provider workspace subtree to
  the active interactive user and grants that user full control there only;
- the parent workspace root, a canonical-like protected sibling and unrelated
  directories keep their owner and receive no explicit grant ACE;
- new children inside the workspace inherit the grant (so the execution
  checkout, Codex files and provider state all stay writable);
- revocation restores the broker owner and removes the granted authority;
- the handoff is idempotent and fails closed when the active user cannot be
  resolved.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from sentinelx_core import windows_integrity
from sentinelx_core.direct_codex_acl import (
    DirectCodexAclError,
    handoff_workspace_to_active_user,
    revoke_workspace_handoff,
)

WINDOWS_ONLY = pytest.mark.skipif(
    not sys.platform.startswith("win"), reason="Windows ACL handoff substrate"
)


@pytest.fixture()
def _workspace_tree(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    """Provider workspace root, exact derived workspace, sibling, unrelated."""
    root = tmp_path / "devforge-workspaces" / "repo-digest"
    workspace = root / "attempt-digest"
    workspace.mkdir(parents=True)
    sibling = root / "sentinelx-protected-sibling.txt"
    sibling.write_text("protected", encoding="utf-8")
    unrelated = tmp_path / "unrelated"
    unrelated.mkdir()
    return root, workspace, sibling, unrelated


@WINDOWS_ONLY
def test_handoff_transfers_owner_and_grant_on_exact_workspace_only(
    _workspace_tree: tuple[Path, Path, Path, Path],
) -> None:
    root, workspace, sibling, unrelated = _workspace_tree
    user_sid = windows_integrity.active_console_user_sid()
    assert user_sid  # tests run inside the active interactive session

    evidence = handoff_workspace_to_active_user(workspace)

    assert evidence["version"] == 1
    assert evidence["user_sid"] == user_sid
    assert evidence["owner_verified"] is True
    assert evidence["grant_verified"] is True
    assert evidence["objects"] >= 1
    # Ownership and explicit grant exist exactly on the workspace subtree.
    assert windows_integrity.object_owner(workspace) == user_sid
    assert windows_integrity.has_grant_ace(workspace, user_sid, explicit_only=True)

    # Scope containment: nothing outside the exact workspace was touched.
    for foreign in (root, sibling, unrelated, sibling.parent):
        assert not windows_integrity.has_grant_ace(foreign, user_sid, explicit_only=True), (
            f"handoff leaked an explicit grant onto {foreign}"
        )


@WINDOWS_ONLY
def test_handoff_grant_is_inherited_by_new_children(
    _workspace_tree: tuple[Path, Path, Path, Path],
) -> None:
    root, workspace, _sibling, _unrelated = _workspace_tree
    user_sid = windows_integrity.active_console_user_sid()
    assert user_sid

    handoff_workspace_to_active_user(workspace)

    # Objects the transport bootstrap / Codex would create later inherit the
    # handoff authority: the checkout stays writable for the active user.
    child_dir = workspace / ".git"
    child_dir.mkdir()
    child_file = child_dir / "config"
    child_file.write_text("x", encoding="utf-8")
    assert windows_integrity.has_grant_ace(child_dir, user_sid)
    assert windows_integrity.has_grant_ace(child_file, user_sid)


@WINDOWS_ONLY
def test_revoke_restores_broker_authority_and_removes_grant(
    _workspace_tree: tuple[Path, Path, Path, Path],
) -> None:
    root, workspace, _sibling, _unrelated = _workspace_tree
    user_sid = windows_integrity.active_console_user_sid()
    assert user_sid
    broker_sid = windows_integrity.current_process_sid()

    handoff_workspace_to_active_user(workspace)
    (workspace / "checkout.txt").write_text("work", encoding="utf-8")

    revocation = revoke_workspace_handoff(workspace)

    assert revocation["revoked"] is True
    assert revocation["owner_restored"] is True
    assert revocation["grant_removed"] is True
    for obj in (workspace, workspace / "checkout.txt"):
        assert windows_integrity.object_owner(obj) == broker_sid
        assert not windows_integrity.has_grant_ace(obj, user_sid)


@WINDOWS_ONLY
def test_handoff_is_idempotent(
    _workspace_tree: tuple[Path, Path, Path, Path],
) -> None:
    root, workspace, _sibling, _unrelated = _workspace_tree
    user_sid = windows_integrity.active_console_user_sid()
    assert user_sid

    first = handoff_workspace_to_active_user(workspace)
    second = handoff_workspace_to_active_user(workspace)

    assert first["objects"] == second["objects"]
    assert windows_integrity.object_owner(workspace) == user_sid
    assert windows_integrity.has_grant_ace(workspace, user_sid, explicit_only=True)


@WINDOWS_ONLY
def test_revoke_without_handoff_is_a_safe_noop(
    _workspace_tree: tuple[Path, Path, Path, Path],
) -> None:
    root, workspace, _sibling, _unrelated = _workspace_tree
    broker_sid = windows_integrity.current_process_sid()

    revocation = revoke_workspace_handoff(workspace)

    assert revocation["revoked"] is True
    assert windows_integrity.object_owner(workspace) == broker_sid


@WINDOWS_ONLY
def test_handoff_fails_closed_without_active_user(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "ws"
    workspace.mkdir()
    monkeypatch.setattr(windows_integrity, "active_console_user_sid", lambda: None)

    with pytest.raises(DirectCodexAclError) as exc:
        handoff_workspace_to_active_user(workspace)
    assert exc.value.code == "direct_codex_active_user_unavailable"
    # No partial authority was left behind.
    broker_sid = windows_integrity.current_process_sid()
    assert windows_integrity.object_owner(workspace) == broker_sid


@WINDOWS_ONLY
def test_handoff_low_mandatory_label_is_preserved(
    _workspace_tree: tuple[Path, Path, Path, Path],
) -> None:
    """The MIC containment boundary is untouched by the ACL handoff."""
    root, workspace, _sibling, _unrelated = _workspace_tree
    windows_integrity.set_low_mandatory_label_tree(workspace)
    assert windows_integrity.mandatory_label(workspace) == "low"

    handoff_workspace_to_active_user(workspace)

    assert windows_integrity.mandatory_label(workspace) == "low"
    revoke_workspace_handoff(workspace)
    assert windows_integrity.mandatory_label(workspace) == "low"
