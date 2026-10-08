"""`local_api` op: list, describe and call structured endpoints."""
from __future__ import annotations

import logging
from typing import Any

from sentinelx_core.executor import HandlerError
from sentinelx_core.local_api import LocalApiError, call_action
from sentinelx_core.policy import Policy
from sentinelx_core.request_context import RequestContext, context_aware

logger = logging.getLogger(__name__)


def _param_names(action: Any) -> list[str]:
    schema = getattr(action, "params_schema", None)
    if isinstance(schema, dict):
        props = schema.get("properties")
        if isinstance(props, dict):
            required = [r for r in (schema.get("required") or []) if r in props]
            rest = sorted(k for k in props if k not in required)
            return list(required) + rest
    return sorted({seg.split("}")[0] for seg in (getattr(action, "request", None) or "").split("{")[1:] if "}" in seg})


def make_local_api_handler(policy: Policy, *, builtin_providers: dict[str, Any] | None = None):
    builtins = dict(builtin_providers or {})
    for name in sorted(set(policy.local_apis) & set(builtins)):
        logger.warning("builtin_local_api_name_conflict", extra={"endpoint": name, "resolution": "configured_external_wins"})

    def _builtin(name: str):
        return None if name in policy.local_apis else builtins.get(name)

    @context_aware
    async def handle_local_api(context_or_payload: RequestContext | dict[str, Any], maybe_payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if maybe_payload is None:
            context: RequestContext | None = None
            payload = context_or_payload
            if not isinstance(payload, dict):
                raise HandlerError("invalid_payload", "local_api payload must be a mapping")
        else:
            if not isinstance(context_or_payload, RequestContext):
                raise HandlerError("invalid_payload", "local_api RequestContext is unavailable")
            context = context_or_payload
            payload = maybe_payload

        operation = str(payload.get("operation") or "").strip()
        if operation == "list":
            external_entries = [
                {"name": e.name, "protocol": e.protocol, "transport": e.transport, "action_count": len(e.actions)}
                for e in policy.local_apis.values()
            ]
            builtin_entries = [
                provider.list_entry()
                for name, provider in sorted(builtins.items())
                if name not in policy.local_apis and provider.available_actions()
            ]
            return {"ok": True, "operation": "list", "endpoints": external_entries + builtin_entries}

        name = str(payload.get("endpoint") or "").strip()
        endpoint = policy.local_apis.get(name)
        builtin = _builtin(name)
        if endpoint is None and builtin is None:
            return {"ok": False, "error": "endpoint_not_configured", "message": f"no local endpoint named '{name}' on this host. Configured: {sorted(policy.local_apis)}"}

        if operation == "describe":
            if endpoint is None:
                try:
                    return builtin.describe()
                except HandlerError as exc:
                    return {"ok": False, "error": exc.code, "message": str(exc)}
            return {
                "ok": True,
                "operation": "describe",
                "endpoint": endpoint.name,
                "protocol": endpoint.protocol,
                "actions": {
                    an: {
                        "request": a.request,
                        "method": a.method,
                        "returns": list(a.select) or "the endpoint's own shape",
                        "description": a.description,
                        "params": _param_names(a),
                        **({"params_schema": a.params_schema} if a.params_schema else {}),
                    }
                    for an, a in sorted(endpoint.actions.items())
                },
            }

        if operation == "call":
            action = str(payload.get("action") or "").strip()
            params = payload.get("params") or {}
            if not isinstance(params, dict):
                return {"ok": False, "error": "invalid_payload", "message": "params must be an object"}
            if endpoint is None:
                if context is None:
                    return {"ok": False, "error": "invalid_payload", "message": "builtin local_api calls require transport RequestContext"}
                try:
                    result = await builtin.call(context, action, params)
                except HandlerError as exc:
                    return {"ok": False, "error": exc.code, "message": str(exc)}
                return {"ok": True, "operation": "call", "endpoint": builtin.name, "action": action, "result": result}
            try:
                result = await call_action(endpoint, action, params)
            except LocalApiError as exc:
                logger.warning("local_api call failed: %s/%s: %s", name, action, exc.code)
                return {"ok": False, "error": exc.code, "message": exc.message}
            return {"ok": True, "operation": "call", "endpoint": endpoint.name, "action": action, "result": result}

        return {"ok": False, "error": "invalid_payload", "message": f"unknown operation '{operation}'; expected list, describe or call"}

    return handle_local_api
