from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any

CAPABILITY = "host_runtime.git_authenticated_v1"
BASE = Path(__file__).resolve().parent
CONFIG = BASE / "broker-config.json"
RUNTIME = BASE / "runtime"
REQUESTS = RUNTIME / "requests"
RESULTS = RUNTIME / "results"
READY = RUNTIME / "broker-ready.json"

SAFE_REMOTE = re.compile(r"^[A-Za-z0-9._-]+$")
SAFE_BRANCH = re.compile(r"^[A-Za-z0-9._/-]+$")
HEX_SHA = re.compile(r"^[0-9a-fA-F]{40,64}$")
URL_CREDENTIALS = re.compile(r"(https?://)([^/@\s:]+):([^/@\s]+)@", re.I)


class BrokerError(Exception):
    def __init__(self, reason_code: str, message: str, state: str = "BLOCKED") -> None:
        super().__init__(message)
        self.reason_code = reason_code
        self.state = state


def atomic_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + "." + uuid.uuid4().hex + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def sanitize(text: str) -> str:
    text = URL_CREDENTIALS.sub(r"\1***:***@", text or "")
    text = re.sub(
        r"(?i)\b(authorization|access[_-]?token|refresh[_-]?token|password|passwd)\s*[:=]\s*\S+",
        r"\1=***",
        text,
    )
    return text[:32768]


def load_config() -> dict[str, Any]:
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    roots = data.get("allowed_roots")
    if not isinstance(roots, list) or not roots:
        raise BrokerError("GitBrokerPolicyInvalid", "allowed_roots must be non-empty")
    return data


def under_root(path: Path, root: Path) -> bool:
    try:
        p = os.path.normcase(str(path.resolve(strict=False)))
        r = os.path.normcase(str(root.resolve(strict=False)))
        return os.path.commonpath([p, r]) == r
    except (OSError, ValueError):
        return False


def resolve_repo(raw: str, cfg: dict[str, Any]) -> Path:
    if not raw:
        raise BrokerError("GitBrokerInvalidRequest", "repo is required")
    repo = Path(raw).resolve(strict=False)
    if not any(under_root(repo, Path(x)) for x in cfg["allowed_roots"]):
        raise BrokerError("GitBrokerPathNotAllowed", "repo is outside operator-approved roots")
    if not repo.is_dir():
        raise BrokerError("GitBrokerRepositoryMissing", "repo directory does not exist")
    return repo


def git_exe() -> str:
    found = shutil.which("git")
    if found:
        return found
    for candidate in (
        r"C:\Program Files\Git\cmd\git.exe",
        r"C:\Program Files\Git\bin\git.exe",
    ):
        if Path(candidate).is_file():
            return candidate
    raise BrokerError("GitBrokerGitUnavailable", "git executable unavailable")


def classify(stderr: str, timed_out: bool = False) -> tuple[str, str]:
    if timed_out:
        return "INTERRUPTED", "GitTransportTimeout"
    low = (stderr or "").lower()
    if "cannot prompt because user interactivity has been disabled" in low or "terminal prompts disabled" in low or "could not read username" in low:
        return "BLOCKED", "GitCredentialInteractiveRequired"
    if "authentication failed" in low or "permission denied (publickey)" in low or "invalid username or password" in low:
        return "BLOCKED", "GitCredentialRejected"
    if "connection was reset" in low or "recv failure" in low or "connection reset by peer" in low:
        return "INTERRUPTED", "GitTransportReset"
    if "could not resolve host" in low or "failed to connect" in low or "network is unreachable" in low or "temporary failure in name resolution" in low:
        return "INTERRUPTED", "GitRemoteTemporarilyUnavailable"
    return "FAILED", "GitCommandFailed"


def run_git(repo: Path, args: list[str], cfg: dict[str, Any], timeout: int) -> dict[str, Any]:
    timeout = max(1, min(int(timeout), int(cfg.get("max_timeout_seconds", 60))))
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GCM_INTERACTIVE"] = "Never"
    env["GIT_PAGER"] = "cat"
    argv = [git_exe(), "-C", str(repo), "-c", "credential.interactive=never"]
    if cfg.get("force_http_1_1", True):
        argv += ["-c", "http.version=HTTP/1.1"]
    argv += args
    started = time.monotonic()
    try:
        cp = subprocess.run(
            argv,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            timeout=timeout,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "ok": False, "state": "INTERRUPTED", "reason_code": "GitTransportTimeout",
            "returncode": -1, "stdout": "", "stderr": "bounded git timeout",
            "duration": round(time.monotonic() - started, 3),
        }
    out, err = sanitize(cp.stdout), sanitize(cp.stderr)
    result = {
        "ok": cp.returncode == 0, "returncode": cp.returncode,
        "stdout": out, "stderr": err,
        "duration": round(time.monotonic() - started, 3),
    }
    if cp.returncode != 0:
        state, reason = classify(err)
        result.update(state=state, reason_code=reason)
    return result


def validate_remote(value: str) -> str:
    value = value or "origin"
    if not SAFE_REMOTE.fullmatch(value):
        raise BrokerError("GitBrokerInvalidRequest", "invalid remote name")
    return value


def validate_branch(value: str) -> str:
    if not value or not SAFE_BRANCH.fullmatch(value) or value.startswith(("-", ".")) or value.endswith(("/", ".")) or ".." in value or "@{" in value or "//" in value:
        raise BrokerError("GitBrokerInvalidRequest", "invalid branch name")
    return value


def remote_url(repo: Path, remote: str, cfg: dict[str, Any], timeout: int) -> str:
    result = run_git(repo, ["remote", "get-url", remote], cfg, min(timeout, 10))
    if not result["ok"] or not result["stdout"].strip():
        raise BrokerError("GitRemoteIdentityConflict", "canonical remote cannot be resolved")
    return sanitize(result["stdout"].strip())


def handle(request: dict[str, Any], cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = cfg or load_config()
    op = str(request.get("operation") or "").strip()
    if op not in {"preflight", "ls_remote", "fetch", "push"}:
        raise BrokerError("GitBrokerOperationNotAllowed", "operation is not allowed")
    repo = resolve_repo(str(request.get("repo") or ""), cfg)
    remote = validate_remote(str(request.get("remote") or "origin"))
    timeout = int(request.get("timeout_seconds") or cfg.get("timeout_seconds", 20))
    url = remote_url(repo, remote, cfg, timeout)
    base = {
        "schema_version": 1,
        "capability": CAPABILITY,
        "operation": op,
        "context_class": "user_scoped",
        "non_interactive": True,
        "canonical_remote_verified": True,
        "remote": remote,
        "remote_url": url,
        "credential_material_exposed": False,
        "bounded_timeout": True,
        "bounded_retry": True,
    }

    if op == "preflight":
        r = run_git(repo, ["ls-remote", remote, "HEAD"], cfg, min(timeout, 15))
        base.update(r)
        if r["ok"]:
            base.update(
                state="READY", reason_code=None,
                authenticated_read_available=True,
                authenticated_write_declared=bool(cfg.get("allow_push", False)),
            )
        return base

    if op == "ls_remote":
        pattern = str(request.get("pattern") or "HEAD")
        if len(pattern) > 256 or any(ch in pattern for ch in "\r\n\0"):
            raise BrokerError("GitBrokerInvalidRequest", "invalid ls-remote pattern")
        r = run_git(repo, ["ls-remote", remote, pattern], cfg, timeout)
    elif op == "fetch":
        r = run_git(repo, ["fetch", "--prune", remote], cfg, timeout)
    else:
        if not cfg.get("allow_push", False):
            raise BrokerError("GitBrokerPushNotAllowed", "push disabled by broker policy")
        branch = validate_branch(str(request.get("branch") or ""))
        source = str(request.get("source") or "HEAD")
        if source != "HEAD" and not HEX_SHA.fullmatch(source):
            raise BrokerError("GitBrokerInvalidRequest", "source must be HEAD or exact SHA")
        args = ["push", remote]
        if request.get("force", False):
            expected = request.get("expected_remote_sha")
            if not isinstance(expected, str) or not HEX_SHA.fullmatch(expected):
                raise BrokerError("GitBrokerForceRequiresLease", "force push requires expected_remote_sha")
            args.append(f"--force-with-lease=refs/heads/{branch}:{expected}")
        args.append(f"{source}:refs/heads/{branch}")
        r = run_git(repo, args, cfg, timeout)

    base.update(r)
    if r["ok"]:
        base.update(state="COMPLETED", reason_code=None)
    return base


def error_result(request: dict[str, Any], exc: Exception) -> dict[str, Any]:
    if isinstance(exc, BrokerError):
        state, reason = exc.state, exc.reason_code
    else:
        state, reason = "FAILED", "GitBrokerInternalError"
    return {
        "schema_version": 1, "capability": CAPABILITY,
        "operation": request.get("operation"), "ok": False,
        "state": state, "reason_code": reason,
        "message": sanitize(str(exc)),
        "context_class": "user_scoped", "non_interactive": True,
        "credential_material_exposed": False,
        "bounded_timeout": True, "bounded_retry": True,
    }


def process(path: Path, cfg: dict[str, Any]) -> None:
    request: dict[str, Any] = {}
    try:
        request = json.loads(path.read_text(encoding="utf-8"))
        result = handle(request, cfg)
    except Exception as exc:
        result = error_result(request, exc)
    request_id = str(request.get("request_id") or path.stem)
    result["request_id"] = request_id
    atomic_json(RESULTS / f"{request_id}.json", result)


def serve() -> int:
    cfg = load_config()
    REQUESTS.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    next_heartbeat = 0.0
    while True:
        now = time.time()
        if now >= next_heartbeat:
            atomic_json(READY, {
                "schema_version": 1, "capability": CAPABILITY,
                "ready": True, "context_class": "user_scoped",
                "non_interactive": True, "credential_material_exposed": False,
                "pid": os.getpid(), "heartbeat_at": now,
            })
            next_heartbeat = now + 2.0
        for req in sorted(REQUESTS.glob("*.json")):
            work = req.with_suffix(".processing")
            try:
                os.replace(req, work)
            except OSError:
                continue
            try:
                process(work, cfg)
            finally:
                work.unlink(missing_ok=True)
        time.sleep(0.2)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--once")
    args = parser.parse_args()
    if args.serve:
        return serve()
    if args.once:
        process(Path(args.once), load_config())
        return 0
    parser.error("use --serve or --once")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
