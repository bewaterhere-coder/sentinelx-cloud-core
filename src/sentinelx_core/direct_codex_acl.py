"""Provider-owned exact-workspace ACL handoff for the real Codex sandbox.

Acceptance R7 root cause: the real Codex Windows ``workspace-write`` sandbox
runs its setup/refresh helper under the active interactive user's *non-elevated*
token, and that helper must modify the workspace DACL
(``READ_CONTROL | WRITE_DAC``) to grant its sandbox capability SID write
access. A provider-created workspace whose NTFS owner is the SentinelX service
identity gives the active user no ``WRITE_DAC``, so the helper's
``SetNamedSecurityInfoW`` fails with error 5 and Codex terminates fail-closed
(``setup refresh had errors``).

The handoff repairs exactly that boundary, inside the provider's own Windows
workspace lifecycle:

1. ownership of the *exact* derived execution workspace subtree is transferred
   to the active interactive user (the SID of the active console session token
   is a token attribute used for ACL grants, never credential material), and
2. that user receives a full-control ACE on the same subtree only.

No other object is touched: the parent workspace root, protected siblings, the
canonical checkout and unrelated directories keep their owner and DACL. The
low mandatory-integrity label (the MIC containment boundary proven by the D9
fixture) is never modified. The handoff is revoked when the attempt lifecycle
closes, so no residual authority survives normal or failed exits beyond the
provider-owned workspace itself.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from sentinelx_core import windows_integrity

DIRECT_CODEX_ACL_VERSION = 1


class DirectCodexAclError(RuntimeError):
    """Fail-closed error for the provider-owned workspace ACL handoff."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _tree(root: Path) -> list[Path]:
    """Provider-owned subtree objects. Reparse points are never followed."""
    entries = [root]
    for directory, subdirectories, files in os.walk(str(root)):
        for name in (*subdirectories, *files):
            entry = Path(directory) / name
            if entry.is_symlink():
                # SetNamedSecurityInfoW would follow a reparse point and touch
                # a foreign object: skip it so authority can never escape the
                # exact workspace. Repository mutation rules already reject
                # symlinks from the implementation candidate set.
                continue
            entries.append(entry)
    return entries


def _require_windows(path: Path) -> None:
    if not windows_integrity.supported():
        raise DirectCodexAclError(
            "direct_codex_acl_platform_unsupported",
            "the exact-workspace ACL handoff requires Windows",
        )
    if not path.is_dir():
        raise DirectCodexAclError(
            "direct_codex_workspace_missing",
            f"the derived execution workspace does not exist: {path}",
        )


def handoff_workspace_to_active_user(path: Path) -> dict[str, Any]:
    """Transfer exact-workspace ownership to the active user and grant write.

    Idempotent: re-applying the handoff merges (never duplicates) the grant
    ACE and re-sets the same owner. Any failure rolls back the objects already
    handled and fails closed.
    """
    root = Path(os.path.abspath(str(path)))
    _require_windows(root)
    user_sid = windows_integrity.active_console_user_sid()
    if user_sid is None:
        raise DirectCodexAclError(
            "direct_codex_active_user_unavailable",
            "cannot resolve the active interactive Windows user for the workspace handoff",
        )
    broker_sid = windows_integrity.current_process_sid()
    objects: list[Path] = []
    try:
        with windows_integrity.owner_write_privileges():
            objects = _tree(root)
            for obj in objects:
                windows_integrity.set_owner_and_grant(obj, owner_sid=user_sid, grant_sid=user_sid)
    except windows_integrity.IntegritySandboxError as exc:
        rollback = _best_effort_revoke(root, reason="handoff_failed")
        raise DirectCodexAclError(
            "direct_codex_acl_handoff_failed",
            f"{exc}; rollback objects revoked: {rollback.get('revoked')}",
        ) from exc
    owner_verified = all(windows_integrity.object_owner(obj) == user_sid for obj in objects)
    grant_verified = all(
        windows_integrity.has_grant_ace(obj, user_sid, explicit_only=True) for obj in objects
    )
    if not (owner_verified and grant_verified):
        rollback = _best_effort_revoke(root, reason="handoff_readback_mismatch")
        raise DirectCodexAclError(
            "direct_codex_acl_handoff_readback_mismatch",
            "exact-workspace ACL handoff did not read back "
            f"(owner={owner_verified}, grant={grant_verified}); "
            f"rollback revoked: {rollback.get('revoked')}",
        )
    return {
        "version": DIRECT_CODEX_ACL_VERSION,
        "user_sid": user_sid,
        "broker_sid": broker_sid,
        "objects": len(objects),
        "owner_verified": True,
        "grant_verified": True,
    }


def revoke_workspace_handoff(path: Path) -> dict[str, Any]:
    """Restore owner and remove the handoff grant across the exact subtree.

    Best effort and never raising: the returned evidence reports whether the
    revocation completed and which objects (if any) could not be restored.
    """
    root = Path(os.path.abspath(str(path)))
    if not windows_integrity.supported() or not root.is_dir():
        return {"version": DIRECT_CODEX_ACL_VERSION, "revoked": True, "objects": 0, "errors": []}
    broker_sid = windows_integrity.current_process_sid()
    user_sid = windows_integrity.active_console_user_sid()
    errors: list[str] = []
    objects: list[Path] = []
    with windows_integrity.owner_write_privileges():
        for obj in _tree(root):
            objects.append(obj)
            try:
                if user_sid is not None:
                    windows_integrity.set_owner_and_grant(
                        obj, owner_sid=broker_sid, revoke_sid=user_sid
                    )
                else:
                    windows_integrity.set_owner_and_grant(obj, owner_sid=broker_sid)
            except windows_integrity.IntegritySandboxError as exc:
                errors.append(str(exc)[:200])
    owner_restored = all(windows_integrity.object_owner(obj) == broker_sid for obj in objects)
    grant_removed = (
        user_sid is None
        or all(not windows_integrity.has_grant_ace(obj, user_sid) for obj in objects)
    )
    complete = not errors and owner_restored and grant_removed
    return {
        "version": DIRECT_CODEX_ACL_VERSION,
        "revoked": complete,
        "objects": len(objects),
        "owner_restored": owner_restored,
        "grant_removed": grant_removed,
        "user_sid": user_sid,
        "broker_sid": broker_sid,
        "errors": errors[:8],
    }


def _best_effort_revoke(root: Path, *, reason: str) -> dict[str, Any]:
    try:
        return revoke_workspace_handoff(root)
    except Exception as exc:  # pragma: no cover - defensive
        return {"version": DIRECT_CODEX_ACL_VERSION, "revoked": False, "reason": reason,
                "errors": [str(exc)[:200]]}
