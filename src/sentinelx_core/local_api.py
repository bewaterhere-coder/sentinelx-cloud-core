"""Talk to a host-local endpoint that already speaks a structured protocol.

WHY THIS EXISTS. To read something a local tool already knows, the assistant
goes through `exec`: build a command line, spawn a process, and parse output
written for human eyes. Docker is the clearest case, at 568 distinct users in a
week, and its most-run subcommands are READS that /var/run/docker.sock already
answers in JSON.

WHAT IT KNOWS. Open a socket, speak HTTP or JSON-RPC, make the declared request,
keep the declared fields. Nothing about Docker or any other product lives here;
that knowledge is in the host's YAML. Same shape as `services:`, where the agent
holds a generic systemctl mechanism and no nginx profile in code.

PROJECTION IS NOT COSMETIC. Measured against nine real containers: `docker ps`
text 712 bytes, raw socket JSON for the same question 20,336, curated projection
1,457. Passing the raw body through would be 28x worse than the text it replaces,
so every action declares what to keep.

NO SHELL. With transport "unix" there is no process, no argv and no shell, so
the entire shell-injection class simply cannot occur on this path. In the audit,
"command_not_allowed: contains shell operator" is among the most frequent
failures on the exec path.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

# A body larger than this is refused rather than buffered. The far side is
# opaque to us: it can answer with anything, and a container log endpoint can
# stream indefinitely.
MAX_RESPONSE_BYTES = 8 * 1024 * 1024


class LocalApiError(Exception):
    """Something went wrong talking to a local endpoint."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def project(data: Any, select: tuple[str, ...]) -> Any:
    """Keep only `select` from a dict, or from every dict in a list.

    Supports dotted paths ("Config.Image") because the interesting field is
    often nested. An empty `select` returns the data untouched, which is the
    escape hatch for endpoints whose answers are already small.
    """
    if not select:
        return data
    if isinstance(data, list):
        return [project(item, select) for item in data]
    if not isinstance(data, dict):
        return data
    out: dict[str, Any] = {}
    for spec in select:
        cur: Any = data
        for part in spec.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                cur = None
                break
        if cur is not None:
            out[spec] = cur
    return out


def _render(template: str, params: dict[str, Any]) -> str:
    """Substitute {name} placeholders from `params`.

    Values are quoted for a URL path, not for a shell: there is no shell here.
    A missing placeholder is an error rather than an empty string, because
    silently requesting /containers//json is worse than refusing.
    """
    from urllib.parse import quote

    out = template
    for key, value in (params or {}).items():
        out = out.replace("{" + str(key) + "}", quote(str(value), safe=""))
    if "{" in out and "}" in out:
        missing = out[out.index("{") + 1 : out.index("}")]
        raise LocalApiError(
            "missing_param", f"the action needs a value for '{missing}'"
        )
    return out


async def _read_http_response(reader: asyncio.StreamReader) -> bytes:
    """Read one HTTP/1.1 response body. Handles both framings Docker uses."""
    header_blob = await reader.readuntil(b"\r\n\r\n")
    head = header_blob.decode("latin-1")
    status_line = head.split("\r\n", 1)[0]
    try:
        status = int(status_line.split(" ")[1])
    except (IndexError, ValueError) as exc:
        raise LocalApiError("bad_response", f"unparseable status: {status_line!r}") from exc

    headers = {}
    for line in head.split("\r\n")[1:]:
        if ":" in line:
            k, v = line.split(":", 1)
            headers[k.strip().lower()] = v.strip()

    if headers.get("transfer-encoding", "").lower() == "chunked":
        chunks = bytearray()
        while True:
            size_line = (await reader.readuntil(b"\r\n")).strip()
            size = int(size_line.split(b";")[0] or b"0", 16)
            if size == 0:
                await reader.readuntil(b"\r\n")
                break
            chunks += await reader.readexactly(size)
            await reader.readexactly(2)
            if len(chunks) > MAX_RESPONSE_BYTES:
                raise LocalApiError("too_large", "endpoint response exceeded the cap")
        body = bytes(chunks)
    else:
        length = int(headers.get("content-length") or 0)
        if length > MAX_RESPONSE_BYTES:
            raise LocalApiError("too_large", "endpoint response exceeded the cap")
        body = await reader.readexactly(length) if length else b""

    if status >= 400:
        raise LocalApiError(
            "endpoint_error",
            f"endpoint answered HTTP {status}: {body[:200].decode('utf-8', 'replace')}",
        )
    return body


async def call_http(endpoint: Any, action: Any, params: dict[str, Any]) -> Any:
    """One HTTP request over a unix socket. Docker's shape."""
    raw = (action.request or "").strip()
    try:
        method, target = raw.split(" ", 1)
    except ValueError as exc:
        raise LocalApiError(
            "bad_action", f"request must look like 'GET /path', got {raw!r}"
        ) from exc
    target = _render(target.strip(), params)

    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_unix_connection(endpoint.path), timeout=endpoint.timeout_s
        )
    except (FileNotFoundError, ConnectionRefusedError, PermissionError) as exc:
        raise LocalApiError(
            "endpoint_unreachable",
            f"cannot open {endpoint.path}: {exc.__class__.__name__}",
        ) from exc
    except (TimeoutError, asyncio.TimeoutError) as exc:
        raise LocalApiError("timeout", f"timed out opening {endpoint.path}") from exc

    try:
        request = (
            f"{method.upper()} {target} HTTP/1.1\r\n"
            "Host: localhost\r\n"
            "Accept: application/json\r\n"
            "Connection: close\r\n\r\n"
        )
        writer.write(request.encode("latin-1"))
        await writer.drain()
        body = await asyncio.wait_for(
            _read_http_response(reader), timeout=endpoint.timeout_s
        )
    except (TimeoutError, asyncio.TimeoutError) as exc:
        raise LocalApiError("timeout", f"{endpoint.name} did not answer in time") from exc
    except asyncio.IncompleteReadError as exc:
        raise LocalApiError("bad_response", "endpoint closed mid-response") from exc
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:  # noqa: BLE001 - closing must not mask the real error
            pass

    if not body:
        return None
    try:
        return json.loads(body)
    except ValueError as exc:
        raise LocalApiError("bad_response", "endpoint did not return JSON") from exc


async def call_jsonrpc(endpoint: Any, action: Any, params: dict[str, Any]) -> Any:
    """One JSON-RPC 2.0 call over a unix socket, newline framed."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": action.method,
        "params": params or {},
    }
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_unix_connection(endpoint.path), timeout=endpoint.timeout_s
        )
    except (FileNotFoundError, ConnectionRefusedError, PermissionError) as exc:
        raise LocalApiError(
            "endpoint_unreachable",
            f"cannot open {endpoint.path}: {exc.__class__.__name__}",
        ) from exc
    except (TimeoutError, asyncio.TimeoutError) as exc:
        raise LocalApiError("timeout", f"timed out opening {endpoint.path}") from exc

    try:
        writer.write((json.dumps(payload) + "\n").encode())
        await writer.drain()
        line = await asyncio.wait_for(reader.readline(), timeout=endpoint.timeout_s)
    except (TimeoutError, asyncio.TimeoutError) as exc:
        raise LocalApiError("timeout", f"{endpoint.name} did not answer in time") from exc
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:  # noqa: BLE001
            pass

    if not line:
        raise LocalApiError("bad_response", "endpoint closed without answering")
    try:
        message = json.loads(line)
    except ValueError as exc:
        raise LocalApiError("bad_response", "endpoint did not return JSON") from exc
    if isinstance(message, dict) and message.get("error"):
        err = message["error"]
        raise LocalApiError(
            "endpoint_error",
            f"{err.get('code')}: {err.get('message')}" if isinstance(err, dict) else str(err),
        )
    return message.get("result") if isinstance(message, dict) else message


async def call_action(endpoint: Any, action_name: str, params: dict[str, Any]) -> Any:
    """Run one ALLOWLISTED action and return its projected result."""
    action = endpoint.actions.get(action_name)
    if action is None:
        # Naming the permitted actions is deliberate: they are already visible
        # through `describe`, and guessing is the failure this avoids.
        raise LocalApiError(
            "action_not_allowed",
            f"'{action_name}' is not an allowed action on '{endpoint.name}'. "
            f"Allowed: {sorted(endpoint.actions)}",
        )
    if endpoint.protocol == "http":
        raw = await call_http(endpoint, action, params)
    else:
        raw = await call_jsonrpc(endpoint, action, params)
    return project(raw, action.select)
