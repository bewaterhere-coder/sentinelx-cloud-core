"""Immutable transport identity passed to context-aware handlers.

Payload is untrusted operation input. RequestContext is built only from the
validated wire RequestMessage so payload keys can never mint or replace
transport identity/correlation fields.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Awaitable, Callable, TypeVar

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
    ) -> "RequestContext":
        """Create authoritative context from transport fields only."""
        return cls(
            request_id=str(request.id),
            op=str(request.op),
            opaque_ref=(str(request.opaque_ref) if request.opaque_ref is not None else None),
            received_at=received_at or datetime.now(UTC),
        )


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
