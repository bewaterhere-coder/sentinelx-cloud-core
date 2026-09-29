"""Immutable transport identity passed to context-aware handlers.

Payload is untrusted operation input. RequestContext is built only from the
validated wire RequestMessage so payload keys can never mint or replace
transport identity/correlation fields.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, TypeVar

from sentinelx_protocol import RequestMessage


@dataclass(frozen=True)
class RequestContext:
    request_id: str
    op: str
    opaque_ref: str | None
    received_at: datetime

    @classmethod
    def from_request(
        cls,
        request: RequestMessage,
        *,
        received_at: datetime | None = None,
    ) -> RequestContext:
        """Create authoritative context from transport fields only."""
        return cls(
            request_id=str(request.id),
            op=str(request.op),
            opaque_ref=(str(request.opaque_ref) if request.opaque_ref is not None else None),
            received_at=received_at or datetime.now(UTC),
        )


@dataclass(frozen=True)
class MutationLineage:
    """Untrusted semantic intent kept separate from transport identity.

    These values may originate in a request payload, so they are never
    authority by themselves. Later scoped-mutation slices must verify them
    against provider-owned mutation-scope state before any mutation occurs.
    """

    project_id: str
    task_id: str
    run_id: str
    attempt_id: str
    slice_id: str | None = None

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> MutationLineage:
        if not isinstance(value, Mapping):
            raise ValueError("mutation lineage must be a mapping")

        required: dict[str, str] = {}
        for field in ("project_id", "task_id", "run_id", "attempt_id"):
            raw = value.get(field)
            if not isinstance(raw, str) or not raw.strip():
                raise ValueError(f"mutation lineage requires non-empty {field}")
            required[field] = raw.strip()

        raw_slice = value.get("slice_id")
        if raw_slice is not None and (not isinstance(raw_slice, str) or not raw_slice.strip()):
            raise ValueError("mutation lineage slice_id must be a non-empty string when present")

        return cls(
            **required,
            slice_id=raw_slice.strip() if isinstance(raw_slice, str) else None,
        )

    @property
    def canonical(self) -> tuple[str, str, str, str, str]:
        return (
            self.project_id,
            self.task_id,
            self.run_id,
            self.attempt_id,
            self.slice_id or "",
        )

    @property
    def digest(self) -> str:
        body = json.dumps(self.canonical, separators=(",", ":"), ensure_ascii=True)
        return hashlib.sha256(body.encode("utf-8")).hexdigest()

    def to_audit_dict(self) -> dict[str, str | None]:
        return {
            "project_id": self.project_id,
            "task_id": self.task_id,
            "run_id": self.run_id,
            "attempt_id": self.attempt_id,
            "slice_id": self.slice_id,
            "semantic_digest": self.digest,
        }


_Result = TypeVar("_Result")
ContextAwareHandler = Callable[[RequestContext, dict[str, Any]], Awaitable[_Result]]


def context_aware(handler: ContextAwareHandler[_Result]) -> ContextAwareHandler[_Result]:
    """Mark a handler as consuming ``(RequestContext, payload)``.

    Existing handlers remain payload-only and need no changes. Executor checks
    this provider-owned marker rather than introspecting signatures, keeping the
    compatibility boundary deterministic and explicit.
    """
    setattr(handler, "__sentinelx_request_context__", True)
    return handler


def accepts_request_context(handler: object) -> bool:
    return getattr(handler, "__sentinelx_request_context__", False) is True
