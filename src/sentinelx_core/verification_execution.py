"""S03 composition helpers for profiled offline Node/npm verification.

This module contains no process executor and grants no authority. It resolves
provider-owned verification inputs, composes a deterministic child environment
for the already-existing scoped executor, confines cwd below the materialized
source root, and projects bounded evidence without Host paths or credentials.
"""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from sentinelx_core.policy import MutationExecutionPolicy
from sentinelx_core.verification_profile import (
    NodeNpmVerificationProfile,
    VerificationAdmission,
    VerificationRequest,
    build_toolchain_manifest,
    build_verification_admission,
    load_dependency_capsule,
    load_source_snapshot,
)
from sentinelx_core.verification_runtime import (
    VerificationMaterialization,
    VerificationRuntimePlan,
    build_verification_runtime_plan,
    launcher_digest,
)

_FILE_ATTRIBUTE_REPARSE_POINT = 0x400

_RESERVED_EXACT = frozenset(
    {
        "PATH",
        "PATHEXT",
        "COMSPEC",
        "SYSTEMROOT",
        "WINDIR",
        "TEMP",
        "TMP",
        "TMPDIR",
        "HOME",
        "USERPROFILE",
        "HOMEDRIVE",
        "HOMEPATH",
        "APPDATA",
        "LOCALAPPDATA",
        "NODE_PATH",
        "NODE_OPTIONS",
    }
)
_RESERVED_PREFIXES = (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "NO_PROXY",
    "NPM_",
    "NPM_CONFIG_",
    "NODE_",
    "YARN_",
    "PNPM_",
    "COREPACK_",
    "GIT_",
    "GH_",
    "GITHUB_",
    "SSH_",
)


@dataclass(frozen=True)
class VerificationExecution:
    request: VerificationRequest
    profile: NodeNpmVerificationProfile
    admission: VerificationAdmission
    plan: VerificationRuntimePlan


def _reserved_environment_key(key: str) -> bool:
    upper = key.upper()
    return upper in _RESERVED_EXACT or any(
        upper.startswith(prefix) for prefix in _RESERVED_PREFIXES
    )


def validate_verification_environment_request(extra: Mapping[str, str]) -> None:
    for key in extra:
        if _reserved_environment_key(key):
            raise ValueError(f"verification environment key {key!r} is provider-owned")


def prepare_verification_execution(
    policy: MutationExecutionPolicy,
    raw_request: object,
) -> VerificationExecution | None:
    if raw_request is None:
        return None
    request = VerificationRequest.from_mapping(raw_request)  # type: ignore[arg-type]
    profile = policy.verification_profile(request.profile)
    if profile is None:
        raise ValueError("verification profile is not configured on this Host")
    source = load_source_snapshot(
        profile.source_snapshot_path(request.source_id),
        limits=profile.limits,
        expected_manifest_sha256=request.source_manifest_sha256,
        expected_revision=request.source_revision,
    )
    capsule = load_dependency_capsule(
        profile.dependency_capsule_path(request.capsule_id),
        limits=profile.limits,
        expected_capsule_id=request.capsule_id,
    )
    toolchain = build_toolchain_manifest(profile)
    admission = build_verification_admission(
        profile=profile,
        request=request,
        source=source,
        capsule=capsule,
        toolchain=toolchain,
    )
    return VerificationExecution(
        request=request,
        profile=profile,
        admission=admission,
        plan=build_verification_runtime_plan(profile, admission),
    )


def planned_verification_cwd(workspace: Path, value: object) -> Path:
    source_root = workspace / "source"
    if value in (None, "", "."):
        return source_root.resolve(strict=False)
    if not isinstance(value, str):
        raise ValueError("verification cwd must be a relative source path")
    relative = Path(value)
    if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
        raise ValueError("verification cwd must remain beneath the materialized source root")
    target = (source_root / relative).resolve(strict=False)
    root = source_root.resolve(strict=False)
    if target == root or not target.is_relative_to(root):
        raise ValueError("verification cwd escaped the materialized source root")
    return target


def verification_cwd(materialized: VerificationMaterialization, value: object) -> Path:
    planned = planned_verification_cwd(materialized.workspace, value)
    try:
        target = planned.resolve(strict=True)
        source_root = materialized.source_root.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValueError("verification cwd is not present in the admitted source snapshot") from exc
    if target != source_root and not target.is_relative_to(source_root):
        raise ValueError("verification cwd escaped the admitted source snapshot")
    if not target.is_dir():
        raise ValueError("verification cwd must be an existing source directory")
    return target


def verification_cwd_label(value: object) -> str:
    if value in (None, "", "."):
        return "source"
    assert isinstance(value, str)
    return f"source/{Path(value).as_posix()}"


def build_verification_environment(
    base_environment: Mapping[str, str],
    caller_environment: Mapping[str, str],
    materialized: VerificationMaterialization,
) -> dict[str, str]:
    """Return the deterministic offline environment for the existing sandbox."""
    validate_verification_environment_request(caller_environment)
    environment = {
        key: value
        for key, value in base_environment.items()
        if not _reserved_environment_key(key)
    }

    workspace = materialized.workspace.resolve(strict=True)
    runtime_root = workspace / ".sentinelx-verification" / "runtime"
    home = runtime_root / "home"
    temp = runtime_root / "tmp"
    roaming = home / "AppData" / "Roaming"
    local = home / "AppData" / "Local"
    npm_prefix = runtime_root / "npm-prefix"
    for path in (runtime_root, home, temp, roaming, local, npm_prefix):
        path.mkdir(parents=True, exist_ok=True)
    npmrc = runtime_root / "empty.npmrc"
    if not npmrc.exists():
        npmrc.write_text("", encoding="utf-8")

    system_root = Path(os.environ.get("SystemRoot", r"C:\Windows"))
    safe_path = os.pathsep.join(
        [
            str(materialized.shim_root.resolve(strict=True)),
            str(system_root / "System32"),
            str(system_root),
        ]
    )
    home_text = str(home)
    environment.update(
        {
            "PATH": safe_path,
            "PATHEXT": os.environ.get("PATHEXT", ".COM;.EXE;.BAT;.CMD"),
            "COMSPEC": os.environ.get("ComSpec", str(system_root / "System32" / "cmd.exe")),
            "SYSTEMROOT": str(system_root),
            "WINDIR": str(system_root),
            "HOME": home_text,
            "USERPROFILE": home_text,
            "HOMEDRIVE": workspace.drive or os.environ.get("SystemDrive", "C:"),
            "HOMEPATH": (
                home_text[2:]
                if len(home_text) >= 2 and home_text[1:2] == ":"
                else home_text
            ),
            "APPDATA": str(roaming),
            "LOCALAPPDATA": str(local),
            "TEMP": str(temp),
            "TMP": str(temp),
            "NPM_CONFIG_CACHE": str(materialized.npm_cache_root.resolve(strict=True)),
            "NPM_CONFIG_OFFLINE": "true",
            "NPM_CONFIG_AUDIT": "false",
            "NPM_CONFIG_FUND": "false",
            "NPM_CONFIG_UPDATE_NOTIFIER": "false",
            "NPM_CONFIG_USERCONFIG": str(npmrc),
            "NPM_CONFIG_GLOBALCONFIG": str(npmrc),
            "NPM_CONFIG_PREFIX": str(npm_prefix),
            "COREPACK_ENABLE_DOWNLOAD_PROMPT": "0",
            "CI": "true",
        }
    )
    for key, value in caller_environment.items():
        environment[key] = value
    return environment


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _admitted_source_member(root: Path, relative: str) -> Path:
    canonical_root = root.resolve(strict=True)
    cursor = canonical_root
    for part in relative.split("/"):
        cursor = cursor / part
        attrs = int(getattr(cursor.lstat(), "st_file_attributes", 0))
        if cursor.is_symlink() or attrs & _FILE_ATTRIBUTE_REPARSE_POINT:
            raise ValueError("admitted verification source became a reparse path")
    item = cursor.resolve(strict=True)
    if not item.is_relative_to(canonical_root) or not item.is_file():
        raise ValueError("admitted verification source escaped its materialized root")
    return item


def revalidate_verification_after_run(materialized: VerificationMaterialization) -> None:
    """Re-read immutable source/toolchain identity before projecting success."""
    plan = materialized.plan
    if build_toolchain_manifest(plan.profile) != plan.toolchain:
        raise ValueError("verification toolchain changed during execution")
    for entry in plan.admission.source.files:
        item = _admitted_source_member(materialized.source_root, entry.path)
        if item.stat().st_size != entry.size or _sha256_file(item) != entry.sha256:
            raise ValueError("admitted verification source changed during execution")
    if launcher_digest(
        (name, (materialized.shim_root / name).read_bytes())
        for name, _content in plan.launchers
    ) != plan.audit_intent.launcher_digest:
        raise ValueError("verification launcher identity changed during execution")


def verification_evidence(materialized: VerificationMaterialization) -> dict[str, object]:
    intent = materialized.plan.audit_intent
    evidence: dict[str, object] = intent.audit_dict()
    evidence.update(
        {
            "source_id": materialized.plan.admission.source.source_id,
            "verified_package_lock_sha256": (
                materialized.plan.admission.expected_package_lock_sha256
            ),
            "offline": True,
        }
    )
    return evidence
