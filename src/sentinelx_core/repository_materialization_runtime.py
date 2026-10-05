"""Runtime composition for PR-013 S02 repository materialization.

The S02 runtime keeps endpoint discovery side-effect free: source/materializer
state is created only when ``materialize_repository`` is actually invoked.
It also gives Windows ACL readback an explicit write-bit test and reuses the
already-verified scoped-script environment sanitizer for AppContainer process
creation instead of inventing a second Windows environment contract.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import sentinelx_core.repository_materialization as _materialization
from sentinelx_core.handlers.scoped_script import _scoped_environment
from sentinelx_core.policy import Policy
from sentinelx_core.repository_materialization import (
    CONTROL_NAMESPACE,
    GitRepositorySourceBroker,
    RepositoryMaterializationFailed,
    RepositoryMaterializationProvider,
    RepositoryMaterializationService,
    RepositorySourceSnapshotStore,
    _dacl_entries,
    _run_icacls,
    _set_exact_acl,
)
from sentinelx_core.repository_transaction import RepositoryTransactionStore


# Windows FILE/standard/generic write capabilities.  Do not include READ_CONTROL
# or SYNCHRONIZE: icacls ``(R)`` legitimately carries those standard rights.
_SNAPSHOT_WRITE_MASK = (
    0x00000002  # FILE_WRITE_DATA
    | 0x00000004  # FILE_APPEND_DATA
    | 0x00000010  # FILE_WRITE_EA
    | 0x00000100  # FILE_WRITE_ATTRIBUTES
    | 0x00010000  # DELETE
    | 0x00040000  # WRITE_DAC
    | 0x00080000  # WRITE_OWNER
    | 0x40000000  # GENERIC_WRITE
)


def _runtime_grant_snapshot_read(snapshot_root: Path, broker_sid: str, app_sid: str) -> None:
    _set_exact_acl(snapshot_root, broker_sid, None)
    _run_icacls([str(snapshot_root), "/grant:r", f"*{app_sid}:(OI)(CI)(R)", "/T", "/C"])
    observed = {sid: mask for sid, mask, _flags in _dacl_entries(snapshot_root)}
    if app_sid not in observed:
        raise RepositoryMaterializationFailed("snapshot AppContainer read grant was not installed")
    if observed[app_sid] & _SNAPSHOT_WRITE_MASK:
        raise RepositoryMaterializationFailed("snapshot grant contains write authority")


def _runtime_materializer_environment(workspace: Path) -> dict[str, str]:
    # Reuse the canonical scoped environment baseline: retain Windows process
    # prerequisites, strip Git/SSH/token/profile authority, and place HOME /
    # APPDATA inside the provider control namespace so source-tree readback
    # never mistakes runtime profile bytes for repository content.
    control_root = workspace / CONTROL_NAMESPACE
    return _scoped_environment(
        {
            "PYTHONNOUSERSITE": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
        },
        control_root,
    )


# RepositoryMaterializationService resolves these helpers through its module
# globals.  Runtime composition narrows only S02-specific behavior while
# preserving the canonical generic Windows sandbox and scoped-script paths.
_materialization._grant_snapshot_read = _runtime_grant_snapshot_read
_materialization._materializer_environment = _runtime_materializer_environment


class RuntimeRepositorySourceSnapshotStore(RepositorySourceSnapshotStore):
    """Report an absent snapshot as a cache miss, not as corrupt evidence."""

    def load_verified(
        self,
        transaction_id: str,
        *,
        expected_source_sha: str | None = None,
    ):
        root = self._snapshot_root(transaction_id)
        if not (root / "manifest.json").exists():
            raise FileNotFoundError(transaction_id)
        return super().load_verified(
            transaction_id,
            expected_source_sha=expected_source_sha,
        )


class RuntimeRepositoryMaterializationService(RepositoryMaterializationService):
    def __init__(
        self,
        *,
        policy: Policy,
        transaction_store: RepositoryTransactionStore,
        ref_resolver,
        state_root: Path | None = None,
        source_broker: Any | None = None,
    ) -> None:
        super().__init__(
            policy=policy,
            transaction_store=transaction_store,
            ref_resolver=ref_resolver,
            state_root=state_root,
            source_broker=source_broker,
        )
        if source_broker is None:
            self.snapshot_store = RuntimeRepositorySourceSnapshotStore(self.state_root)
            self.source_broker = GitRepositorySourceBroker(
                policy=policy,
                state_root=self.state_root,
                snapshot_store=self.snapshot_store,
                ref_resolver=ref_resolver,
            )


class LazyRuntimeRepositoryMaterializationService:
    """No filesystem/state materialization until the bounded action is called."""

    def __init__(self, *, base: Any, policy: Policy) -> None:
        self._base = base
        self._policy = policy

    async def materialize(self, *args, **kwargs):
        state_root = (self._policy.upload_base.parent / "state").resolve(strict=False)
        service = RuntimeRepositoryMaterializationService(
            policy=self._policy,
            transaction_store=self._base._repository_transactions,
            ref_resolver=self._base._repository_ref_resolver,
            state_root=state_root,
        )
        return await service.materialize(*args, **kwargs)


def make_runtime_repository_materialization_provider(
    base: Any,
    policy: Policy,
) -> RepositoryMaterializationProvider:
    return RepositoryMaterializationProvider(
        base,
        LazyRuntimeRepositoryMaterializationService(base=base, policy=policy),
    )
