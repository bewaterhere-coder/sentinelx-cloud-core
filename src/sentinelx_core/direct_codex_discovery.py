"""Verified direct-Codex executable chain discovery (PR-015/S02, D5).

The provider never executes a ``.cmd`` shim through a shell. It resolves the
active user's npm package directory, verifies the package identity from
``package.json``, and then executes the fixed chain:

    node.exe <verified @openai/codex>/bin/codex.js exec <provider-owned flags>

Package version is evidence only. V1 fails closed when the installed CLI does
not expose the supported non-interactive contract.
"""
from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from sentinelx_core.policy import DirectCodexPolicy
from sentinelx_core.user_process import (
    UserProcessError,
    UserProcessRequest,
    run_user_scoped_process,
)

_PROBE_SCRIPT = (
    "console.log(JSON.stringify({"
    "appdata: process.env.APPDATA || '',"
    "home: process.env.USERPROFILE || '',"
    "paths: require('module').globalPaths || []"
    "}))"
)

_FALLBACK_NODE_DIRS = (
    r"C:\Program Files\nodejs\node.exe",
    r"C:\Program Files (x86)\nodejs\node.exe",
)


class DirectCodexDiscoveryError(RuntimeError):
    """Fail-closed error for direct-Codex chain discovery."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class CodexChain:
    node_executable: Path
    codex_script: Path
    package_dir: Path
    package_name: str
    package_version: str | None
    npm_root: Path
    json_output_supported: bool
    # The provider only passes a flag the verified CLI actually advertises.
    # Passing an unrecognized flag makes the whole non-interactive run fail.
    approval_flag_supported: bool = False
    sandbox_flag_supported: bool = True


def _absolute(path: Path) -> Path:
    return Path(os.path.abspath(str(path)))


def _real(path: Path) -> Path:
    return Path(os.path.realpath(str(path)))


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        common = os.path.commonpath([str(path).casefold(), str(root).casefold()])
    except ValueError:
        return False
    return common == str(root).casefold()


def resolve_node_executable(policy: DirectCodexPolicy) -> Path:
    if policy.node_executable is not None:
        candidate = _absolute(policy.node_executable)
        if not candidate.is_file():
            raise DirectCodexDiscoveryError(
                "direct_codex_node_missing", "direct_codex.node_executable does not exist"
            )
        return candidate
    found = shutil.which("node")
    if found:
        return _absolute(Path(found))
    for candidate in _FALLBACK_NODE_DIRS:
        path = Path(candidate)
        if path.is_file():
            return _absolute(path)
    raise DirectCodexDiscoveryError(
        "direct_codex_node_missing", "cannot resolve a verified node executable"
    )


async def active_user_npm_roots(
    *,
    node_executable: Path,
    cwd: Path,
    allowed_root: Path,
    timeout: float,
) -> tuple[Path, ...]:
    """Ask node, running as the active user, where its global modules live."""
    request = UserProcessRequest(
        executable=str(node_executable),
        argv=[str(node_executable), "-e", _PROBE_SCRIPT],
        cwd=cwd,
        allowed_root=allowed_root,
        timeout_seconds=timeout,
        max_output_bytes=8192,
    )
    try:
        result = await run_user_scoped_process(request)
    except UserProcessError as exc:
        raise DirectCodexDiscoveryError(
            "direct_codex_user_context_unavailable", str(exc)
        ) from exc
    if result.returncode != 0:
        raise DirectCodexDiscoveryError(
            "direct_codex_user_context_unavailable",
            "the active-user node probe did not produce a usable npm root",
        )
    try:
        payload = json.loads(result.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError) as exc:
        raise DirectCodexDiscoveryError(
            "direct_codex_user_context_unavailable", "cannot parse the active-user npm probe"
        ) from exc

    roots: list[Path] = []
    for key in ("appdata", "home"):
        value = str(payload.get(key) or "").strip()
        if not value:
            continue
        base = Path(value)
        roots.append(base / "npm" / "node_modules")
        roots.append(base / "AppData" / "Roaming" / "npm" / "node_modules")
    for raw in payload.get("paths") or []:
        text = str(raw).strip()
        if text:
            roots.append(Path(text))
    ordered: list[Path] = []
    for root in roots:
        absolute = _absolute(root)
        if absolute not in ordered:
            ordered.append(absolute)
    return tuple(ordered)


def verify_package(
    npm_root: Path,
    package_name: str,
) -> tuple[Path, Path, str | None] | None:
    """Return ``(package_dir, codex_script, version)`` when identity is verified.

    Package identity is pinned and fail closed: the installed manifest must
    declare exactly ``package_name``, the package directory must really live
    inside the active-user npm root, and the executed script must really live
    inside the package directory. Real paths (symlinks/junctions resolved) are
    what decide containment, so a linked package or bin cannot redirect the
    provider onto an executable outside the verified package.
    """
    parts = [part for part in package_name.replace("\\", "/").split("/") if part]
    if not parts or any(part in {".", ".."} for part in parts):
        return None
    npm_root_abs = _absolute(npm_root)
    package_dir = _absolute(npm_root_abs.joinpath(*parts))
    if package_dir == npm_root_abs or not _is_relative_to(package_dir, npm_root_abs):
        return None
    if not package_dir.is_dir():
        return None

    npm_root_real = _real(npm_root_abs)
    package_real = _real(package_dir)
    if package_real == npm_root_real or not _is_relative_to(package_real, npm_root_real):
        return None

    manifest = package_real / "package.json"
    if not manifest.is_file():
        return None
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    if str(data.get("name") or "").strip() != package_name:
        return None

    binary = data.get("bin")
    candidates: list[str] = []
    if binary is None:
        candidates.append("bin/codex.js")
    elif isinstance(binary, str):
        candidates.append(binary)
    elif isinstance(binary, dict):
        for key in ("codex", package_name.split("/")[-1]):
            value = binary.get(key)
            if isinstance(value, str):
                candidates.append(value)
        if not candidates:
            return None
    else:
        return None

    for candidate in candidates:
        if not candidate or os.path.isabs(candidate):
            # An absolute bin cannot be proven to belong to this package.
            continue
        script = _absolute(package_real / candidate)
        script_real = _real(script)
        if script_real.is_file() and _is_relative_to(script_real, package_real):
            return package_dir, script, (str(data.get("version")) if data.get("version") else None)
    return None


async def discover_codex_chain(
    policy: DirectCodexPolicy,
    *,
    cwd: Path,
    allowed_root: Path,
    probe_timeout: float = 30.0,
) -> CodexChain:
    """Resolve and verify the fixed node + codex.js execution chain."""
    node_executable = resolve_node_executable(policy)
    roots = await active_user_npm_roots(
        node_executable=node_executable,
        cwd=cwd,
        allowed_root=allowed_root,
        timeout=probe_timeout,
    )
    for root in roots:
        verified = verify_package(root, policy.codex_package)
        if verified is None:
            continue
        package_dir, codex_script, version = verified
        contract = await probe_cli_contract(
            node_executable=node_executable,
            codex_script=codex_script,
            cwd=cwd,
            allowed_root=allowed_root,
            timeout=probe_timeout,
        )
        if not contract["exec_supported"] or not contract["sandbox_supported"]:
            # Fail closed on the next root rather than executing an unknown CLI.
            continue
        return CodexChain(
            node_executable=node_executable,
            codex_script=codex_script,
            package_dir=package_dir,
            package_name=policy.codex_package,
            package_version=version,
            npm_root=root,
            json_output_supported=contract["json_output_supported"],
            approval_flag_supported=contract["approval_flag_supported"],
            sandbox_flag_supported=contract["sandbox_supported"],
        )
    raise DirectCodexDiscoveryError(
        "direct_codex_chain_unavailable",
        f"no verified {policy.codex_package} installation was found for the active user",
    )


async def probe_cli_contract(
    *,
    node_executable: Path,
    codex_script: Path,
    cwd: Path,
    allowed_root: Path,
    timeout: float,
) -> dict[str, bool]:
    """Probe exactly which ``exec`` flags the verified CLI advertises.

    The provider never guesses a flag: an unrecognized flag makes the whole
    non-interactive run fail, so every optional flag is gated on this probe.
    """
    request = UserProcessRequest(
        executable=str(node_executable),
        argv=[str(node_executable), str(codex_script), "exec", "--help"],
        cwd=cwd,
        allowed_root=allowed_root,
        timeout_seconds=timeout,
        max_output_bytes=65536,
    )
    try:
        result = await run_user_scoped_process(request)
    except UserProcessError:
        return {
            "exec_supported": False,
            "sandbox_supported": False,
            "approval_flag_supported": False,
            "json_output_supported": False,
        }
    if result.returncode != 0:
        return {
            "exec_supported": False,
            "sandbox_supported": False,
            "approval_flag_supported": False,
            "json_output_supported": False,
        }
    help_text = result.stdout
    return {
        "exec_supported": "exec" in help_text.lower(),
        "sandbox_supported": "--sandbox" in help_text,
        "approval_flag_supported": "--ask-for-approval" in help_text,
        "json_output_supported": "--json" in help_text,
    }


async def supports_json_output(
    *,
    node_executable: Path,
    codex_script: Path,
    cwd: Path,
    allowed_root: Path,
    timeout: float,
) -> bool:
    """Probe whether the installed CLI exposes structured ``exec`` output."""
    contract = await probe_cli_contract(
        node_executable=node_executable,
        codex_script=codex_script,
        cwd=cwd,
        allowed_root=allowed_root,
        timeout=timeout,
    )
    return contract["json_output_supported"]


async def verify_cli_contract(
    chain: CodexChain,
    *,
    cwd: Path,
    allowed_root: Path,
    timeout: float = 60.0,
) -> bool:
    """Prove the installed CLI exposes the supported non-interactive contract."""
    contract = await probe_cli_contract(
        node_executable=chain.node_executable,
        codex_script=chain.codex_script,
        cwd=cwd,
        allowed_root=allowed_root,
        timeout=timeout,
    )
    if not contract["exec_supported"]:
        raise DirectCodexDiscoveryError(
            "direct_codex_cli_contract_unavailable",
            "the installed Codex CLI help output does not advertise the exec subcommand",
        )
    if not contract["sandbox_supported"]:
        raise DirectCodexDiscoveryError(
            "direct_codex_cli_contract_unavailable",
            "the installed Codex CLI does not advertise --sandbox, so the "
            "workspace-write execution mode cannot be requested",
        )
    return True
