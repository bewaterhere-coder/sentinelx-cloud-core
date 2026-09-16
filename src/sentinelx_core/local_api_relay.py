"""Relay ONE request to a local socket, as whichever user runs this.

Invoked as `sudo -n -u <run_as> python -m sentinelx_core.local_api_relay <path>
<timeout>`, so the connect() happens under the target Unix identity. That is the
whole point: an endpoint like Herdr creates its socket 0600 and checks the peer
credentials, so reaching it means BEING that user, not having permission to read
its socket. Running the agent as root does not solve it either: root connects
but identifies as uid 0.

DELIBERATELY TINY. This is invoked through sudo, so it is the most sensitive
code in the feature. It takes a socket path and a timeout, writes stdin to the
socket, reads one newline-terminated reply, writes it to stdout. It does not
read config, does not interpret the payload, does not touch the filesystem and
runs nothing. Anything it could be tricked into doing, it also cannot do.

The socket path comes from the agent's own validated config, never from the
caller: the model can pick which configured endpoint to use, not where it points.
"""

from __future__ import annotations

import socket
import sys

MAX_REPLY_BYTES = 8 * 1024 * 1024


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: local_api_relay <socket-path> <timeout-seconds>", file=sys.stderr)
        return 2
    path, timeout = sys.argv[1], float(sys.argv[2])

    payload = sys.stdin.buffer.read()
    if not payload:
        print("nothing to send", file=sys.stderr)
        return 2

    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect(path)
    except OSError as exc:
        print(f"connect failed: {exc}", file=sys.stderr)
        return 3

    try:
        sock.sendall(payload)
        buf = bytearray()
        while not buf.endswith(b"\n"):
            chunk = sock.recv(65536)
            if not chunk:
                break
            buf += chunk
            if len(buf) > MAX_REPLY_BYTES:
                print("reply exceeded the cap", file=sys.stderr)
                return 4
    except OSError as exc:
        print(f"relay failed: {exc}", file=sys.stderr)
        return 3
    finally:
        sock.close()

    sys.stdout.buffer.write(bytes(buf))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
