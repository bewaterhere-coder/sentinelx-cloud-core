from __future__ import annotations

import argparse
import json
import os
import time
import uuid
from pathlib import Path

BASE = Path(__file__).resolve().parent
RUNTIME = BASE / "runtime"
REQUESTS = RUNTIME / "requests"
RESULTS = RUNTIME / "results"
READY = RUNTIME / "broker-ready.json"


def atomic_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)


def ensure_ready(max_age: float = 6.0) -> None:
    deadline = time.monotonic() + 1.0
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            if not READY.is_file():
                raise RuntimeError("broker readiness file is missing")
            data = json.loads(READY.read_text(encoding="utf-8"))
            if not data.get("ready"):
                raise RuntimeError("broker is not ready")
            heartbeat = float(data.get("heartbeat_at") or 0)
            if time.time() - heartbeat > max_age:
                raise RuntimeError("broker heartbeat is stale")
            return
        except (OSError, ValueError, RuntimeError) as exc:
            last_error = exc
            time.sleep(0.05)
    raise RuntimeError(f"GitCredentialContextUnavailable: {last_error}")


def submit(data: dict, wait_seconds: int) -> dict:
    ensure_ready()
    request_id = uuid.uuid4().hex
    data = dict(data)
    data["request_id"] = request_id
    req = REQUESTS / f"{request_id}.json"
    res = RESULTS / f"{request_id}.json"
    atomic_json(req, data)

    deadline = time.monotonic() + wait_seconds
    while time.monotonic() < deadline:
        if res.is_file():
            result = json.loads(res.read_text(encoding="utf-8"))
            res.unlink(missing_ok=True)
            return result
        time.sleep(0.1)

    req.unlink(missing_ok=True)
    return {
        "schema_version": 1,
        "capability": "host_runtime.git_authenticated_v1",
        "operation": data.get("operation"),
        "ok": False,
        "state": "INTERRUPTED",
        "reason_code": "GitTransportTimeout",
        "message": "bounded broker wait expired",
        "context_class": "user_scoped",
        "non_interactive": True,
        "credential_material_exposed": False,
        "bounded_timeout": True,
        "bounded_retry": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="operation", required=True)

    def common(p):
        p.add_argument("--repo", required=True)
        p.add_argument("--remote", default="origin")
        p.add_argument("--timeout", type=int, default=20)

    p = sub.add_parser("preflight")
    common(p)
    p.add_argument("--write", action="store_true")

    p = sub.add_parser("ls-remote")
    common(p)
    p.add_argument("--pattern", default="HEAD")

    p = sub.add_parser("fetch")
    common(p)

    p = sub.add_parser("push")
    common(p)
    p.add_argument("--branch", required=True)
    p.add_argument("--source", default="HEAD")
    p.add_argument("--force", action="store_true")
    p.add_argument("--expected-remote-sha")

    args = parser.parse_args()
    data = {
        "operation": args.operation.replace("-", "_"),
        "repo": args.repo,
        "remote": args.remote,
        "timeout_seconds": max(1, min(args.timeout, 60)),
    }
    if args.operation == "preflight":
        data["write_required"] = bool(args.write)
    elif args.operation == "ls-remote":
        data["pattern"] = args.pattern
    elif args.operation == "push":
        data.update({
            "branch": args.branch,
            "source": args.source,
            "force": bool(args.force),
            "expected_remote_sha": args.expected_remote_sha,
        })

    try:
        result = submit(data, data["timeout_seconds"] + 8)
    except Exception as exc:
        result = {
            "schema_version": 1,
            "capability": "host_runtime.git_authenticated_v1",
            "operation": data["operation"],
            "ok": False,
            "state": "BLOCKED",
            "reason_code": "GitCredentialContextUnavailable",
            "message": str(exc),
            "context_class": "user_scoped",
            "non_interactive": True,
            "credential_material_exposed": False,
            "bounded_timeout": True,
            "bounded_retry": True,
        }

    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
