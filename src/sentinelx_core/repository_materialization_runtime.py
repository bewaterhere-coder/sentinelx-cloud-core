"""Runtime composition for PR-013 S02 repository materialization.

The S02 snapshot store deliberately treats an absent transaction snapshot as a
cache miss while preserving fail-closed corruption handling for any snapshot
that already exists.  Keeping that distinction in the runtime composition
avoids weakening the sealed snapshot verifier itself.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from sentinelx_core.policy import Policy
from sentinelx_core.repository_materialization import (
    GitRepositorySourceBroker,
    RepositoryMaterializationProvider,
    RepositoryMaterializationService,
    RepositorySourceSnapshotStore,
)
from sentinelx_core.repository_transaction import RepositoryTransactionStore


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


def make_runtime_repository_materialization_provider(
    base: Any,
    policy: Policy,
) -> RepositoryMaterializationProvider:
    state_root = (policy.upload_base.parent / "state").resolve(strict=False)
    service = RuntimeRepositoryMaterializationService(
        policy=policy,
        transaction_store=base._repository_transactions,
        ref_resolver=base._repository_ref_resolver,
        state_root=state_root,
    )
    return RepositoryMaterializationProvider(base, service)
