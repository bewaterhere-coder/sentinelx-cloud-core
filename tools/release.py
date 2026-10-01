"""Build and verify immutable SentinelX release artifacts.

The release version is derived from an exact ``vX.Y.Z`` Git tag.  This tool
never edits source version constants: it validates tag/ref identity, builds an
isolated worktree, verifies wheel metadata and an isolated install, hashes the
artifact, and writes a provenance manifest bound to the exact source commit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
import venv
import zipfile


MANIFEST_SCHEMA = "sentinelx.release.v1"
INSTALL_PLAN_SCHEMA = "sentinelx.install-plan.v1"
PUBLISH_PLAN_SCHEMA = "sentinelx.publish-plan.v1"
TOOL_VERSION = "1"
PACKAGE_NAME = "sentinelx-cloud-core"
VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


class ReleaseError(RuntimeError):
    """A fail-closed release contract violation."""


def _run(argv: list[str], *, cwd: Path | None = None) -> str:
    proc = subprocess.run(
        argv,
        cwd=str(cwd) if cwd is not None else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip() or f"exit {proc.returncode}"
        raise ReleaseError(f"command failed: {' '.join(argv)}: {detail}")
    return proc.stdout.strip()


def _git(repo: Path, *args: str) -> str:
    return _run(["git", "-C", str(repo), *args])


def _normalized_version(value: str) -> str:
    version = value[1:] if value.startswith("v") else value
    if not VERSION_RE.fullmatch(version):
        raise ReleaseError(f"invalid release version: {value!r}")
    return version


def _commit_for(repo: Path, ref: str) -> str:
    try:
        return _git(repo, "rev-parse", "--verify", f"{ref}^{{commit}}")
    except ReleaseError as exc:
        raise ReleaseError(f"release ref does not resolve to a commit: {ref}") from exc


def resolve_release_identity(repo: Path, version: str, ref: str | None = None) -> dict[str, str]:
    repo = repo.resolve()
    version = _normalized_version(version)
    tag = f"v{version}"
    tag_commit = _commit_for(repo, f"refs/tags/{tag}")
    requested_ref = ref or tag
    ref_commit = _commit_for(repo, requested_ref)
    if ref_commit != tag_commit:
        raise ReleaseError(
            f"release ref/tag mismatch: {requested_ref} -> {ref_commit}, {tag} -> {tag_commit}"
        )
    return {
        "version": version,
        "tag": tag,
        "requested_ref": requested_ref,
        "source_commit": tag_commit,
    }


def _wheel_metadata_version(wheel: Path) -> str:
    with zipfile.ZipFile(wheel) as archive:
        candidates = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
        if len(candidates) != 1:
            raise ReleaseError(f"wheel has {len(candidates)} METADATA files: {wheel.name}")
        metadata = archive.read(candidates[0]).decode("utf-8")
    for line in metadata.splitlines():
        if line.startswith("Version: "):
            return line.removeprefix("Version: ").strip()
    raise ReleaseError(f"wheel metadata has no Version field: {wheel.name}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _venv_python(root: Path) -> Path:
    if os.name == "nt":
        return root / "Scripts" / "python.exe"
    return root / "bin" / "python"


def _installed_agent_version(wheel: Path) -> str:
    with tempfile.TemporaryDirectory(prefix="sentinelx-release-install-") as temp:
        env_root = Path(temp) / "venv"
        venv.EnvBuilder(with_pip=True, clear=True).create(env_root)
        python = _venv_python(env_root)
        _run([str(python), "-m", "pip", "install", "--no-deps", str(wheel)])
        return _run(
            [
                str(python),
                "-c",
                "from sentinelx_core import AGENT_VERSION; print(AGENT_VERSION)",
            ]
        ).splitlines()[-1].strip()


def _build_wheel(repo: Path, source_commit: str) -> Path:
    worktree_root = Path(tempfile.mkdtemp(prefix="sentinelx-release-source-"))
    source = worktree_root / "source"
    wheel_dir = worktree_root / "wheel"
    wheel_dir.mkdir()
    added = False
    try:
        _git(repo, "worktree", "add", "--detach", str(source), source_commit)
        added = True
        _run(
            [
                sys.executable,
                "-m",
                "pip",
                "wheel",
                "--no-deps",
                "--wheel-dir",
                str(wheel_dir),
                str(source),
            ]
        )
        wheels = sorted(wheel_dir.glob("*.whl"))
        if len(wheels) != 1:
            raise ReleaseError(f"expected exactly one wheel, found {len(wheels)}")
        staged_dir = Path(tempfile.mkdtemp(prefix="sentinelx-release-wheel-"))
        staged = staged_dir / wheels[0].name
        shutil.copy2(wheels[0], staged)
        return staged
    finally:
        if added:
            try:
                _git(repo, "worktree", "remove", "--force", str(source))
            except ReleaseError:
                pass
        shutil.rmtree(worktree_root, ignore_errors=True)


def _verify_wheel(wheel: Path, expected_version: str) -> dict[str, str]:
    metadata_version = _wheel_metadata_version(wheel)
    if metadata_version != expected_version:
        raise ReleaseError(
            f"wheel metadata version mismatch: expected {expected_version}, got {metadata_version}"
        )
    installed_version = _installed_agent_version(wheel)
    if installed_version != expected_version:
        raise ReleaseError(
            f"installed AGENT_VERSION mismatch: expected {expected_version}, got {installed_version}"
        )
    return {
        "wheel_metadata_version": metadata_version,
        "installed_agent_version": installed_version,
    }


def build_release(repo: Path, version: str, output: Path, ref: str | None = None) -> Path:
    identity = resolve_release_identity(repo, version, ref)
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / "release-manifest.json"
    if manifest_path.exists():
        raise ReleaseError(f"release manifest already exists: {manifest_path}")
    staged_wheel = _build_wheel(repo.resolve(), identity["source_commit"])
    try:
        verification = _verify_wheel(staged_wheel, identity["version"])
        destination = output / staged_wheel.name
        if destination.exists():
            raise ReleaseError(f"release artifact already exists: {destination}")
        shutil.copy2(staged_wheel, destination)
    finally:
        staged_wheel.unlink(missing_ok=True)

    manifest = {
        "schema": MANIFEST_SCHEMA,
        "tool_version": TOOL_VERSION,
        "state": "built",
        **identity,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "artifact": {
            "filename": destination.name,
            "size": destination.stat().st_size,
            "sha256": _sha256(destination),
        },
        "verification": {**verification, "passed": True},
    }
    manifest_tmp = output / ".release-manifest.json.tmp"
    try:
        manifest_tmp.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        manifest_tmp.replace(manifest_path)
    except Exception:
        destination.unlink(missing_ok=True)
        manifest_tmp.unlink(missing_ok=True)
        raise
    return manifest_path


def _load_manifest_artifact(
    manifest_path: Path,
) -> tuple[dict[str, object], Path, str, str]:
    manifest_path = manifest_path.resolve()
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReleaseError(f"cannot read release manifest: {manifest_path}") from exc
    if not isinstance(manifest, dict):
        raise ReleaseError("release manifest must be a JSON object")
    if manifest.get("schema") != MANIFEST_SCHEMA:
        raise ReleaseError("unsupported release manifest schema")
    version = _normalized_version(str(manifest.get("version", "")))
    if manifest.get("tag") != f"v{version}":
        raise ReleaseError("manifest tag/version mismatch")
    artifact = manifest.get("artifact")
    if not isinstance(artifact, dict) or not isinstance(artifact.get("filename"), str):
        raise ReleaseError("manifest artifact is invalid")
    if Path(artifact["filename"]).name != artifact["filename"]:
        raise ReleaseError("manifest artifact filename must be a basename")
    wheel = manifest_path.parent / artifact["filename"]
    if not wheel.is_file():
        raise ReleaseError(f"manifest artifact is missing: {wheel}")
    actual_hash = _sha256(wheel)
    if actual_hash != artifact.get("sha256"):
        raise ReleaseError("release artifact SHA-256 mismatch")
    if wheel.stat().st_size != artifact.get("size"):
        raise ReleaseError("release artifact size mismatch")
    if manifest.get("state") != "built":
        raise ReleaseError("manifest state is not built")
    verification_record = manifest.get("verification")
    if not isinstance(verification_record, dict) or verification_record.get("passed") is not True:
        raise ReleaseError("manifest verification is not passed")
    source_commit = manifest.get("source_commit")
    if not isinstance(source_commit, str) or not source_commit:
        raise ReleaseError("manifest source commit is invalid")
    return manifest, wheel, version, actual_hash


def verify_manifest(manifest_path: Path, repo: Path | None = None) -> dict[str, object]:
    manifest, wheel, version, actual_hash = _load_manifest_artifact(manifest_path)
    verification = _verify_wheel(wheel, version)
    if repo is not None:
        identity = resolve_release_identity(repo, version, str(manifest.get("requested_ref") or ""))
        if identity["source_commit"] != manifest.get("source_commit"):
            raise ReleaseError("manifest source commit does not match repository release identity")
    return {"ok": True, "version": version, "sha256": actual_hash, **verification}


def install_plan(manifest_path: Path, python_executable: str) -> dict[str, object]:
    manifest, wheel, version, actual_hash = _load_manifest_artifact(manifest_path)
    if not python_executable.strip():
        raise ReleaseError("python executable must be supplied by the operator")
    return {
        "schema": INSTALL_PLAN_SCHEMA,
        "state": "planned",
        "version": version,
        "source_commit": manifest["source_commit"],
        "artifact": {
            "path": str(wheel),
            "filename": wheel.name,
            "sha256": actual_hash,
            "size": wheel.stat().st_size,
        },
        "argv": [
            python_executable,
            "-m",
            "pip",
            "install",
            "--upgrade",
            "--force-reinstall",
            str(wheel),
        ],
        "requires_restart": True,
        "mutates_host": False,
        "notes": "This plan does not execute pip or restart a service.",
    }


def _publish_identity(manifest_path: Path) -> dict[str, object]:
    manifest_path = manifest_path.resolve()
    manifest, wheel, version, actual_hash = _load_manifest_artifact(manifest_path)
    return {
        "tag": f"v{version}",
        "target_commitish": manifest["source_commit"],
        "assets": [
            {
                "filename": wheel.name,
                "sha256": actual_hash,
                "size": wheel.stat().st_size,
            },
            {
                "filename": manifest_path.name,
                "sha256": _sha256(manifest_path),
                "size": manifest_path.stat().st_size,
            },
        ],
    }


def publication_plan(
    manifest_path: Path,
    repository: str,
    existing_release: dict[str, object] | None = None,
) -> dict[str, object]:
    if not REPOSITORY_RE.fullmatch(repository):
        raise ReleaseError("repository must be in owner/name form")
    identity = _publish_identity(manifest_path)
    action = "create"
    if existing_release is not None:
        release_record = existing_release.get("release")
        if isinstance(release_record, dict):
            existing_tag = release_record.get("tag")
            existing_target = release_record.get("target_commitish")
        else:
            existing_tag = existing_release.get("tag") or existing_release.get("tag_name")
            existing_target = existing_release.get("target_commitish")
        comparable = {
            "tag": existing_tag,
            "target_commitish": existing_target,
            "assets": existing_release.get("assets"),
        }
        if comparable != identity:
            raise ReleaseError("conflicting same-version release identity")
        action = "noop"
    return {
        "schema": PUBLISH_PLAN_SCHEMA,
        "state": "planned",
        "action": action,
        "repository": repository,
        "release": {
            "tag": identity["tag"],
            "target_commitish": identity["target_commitish"],
            "name": f"{PACKAGE_NAME} {identity['tag']}",
            "draft": False,
            "prerelease": False,
        },
        "assets": identity["assets"],
        "side_effects": {
            "publishes_release": False,
            "installs_on_host": False,
            "restarts_service": False,
        },
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build", help="build and verify one exact tagged release")
    build.add_argument("--version", required=True)
    build.add_argument("--ref")
    build.add_argument("--output", required=True, type=Path)
    build.add_argument("--repository-root", type=Path, default=Path.cwd())
    verify = sub.add_parser("verify", help="re-verify one built release manifest")
    verify.add_argument("--manifest", required=True, type=Path)
    verify.add_argument("--repository-root", type=Path)
    install = sub.add_parser("install-plan", help="emit an exact-artifact install plan without executing it")
    install.add_argument("--manifest", required=True, type=Path)
    install.add_argument("--python", required=True, dest="python_executable")
    publish = sub.add_parser("publish-plan", help="emit deterministic publication intent without publishing")
    publish.add_argument("--manifest", required=True, type=Path)
    publish.add_argument("--repository", required=True)
    publish.add_argument("--existing-release", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "build":
            path = build_release(args.repository_root, args.version, args.output, args.ref)
            print(path)
        elif args.command == "verify":
            result = verify_manifest(args.manifest, args.repository_root)
            print(json.dumps(result, sort_keys=True))
        elif args.command == "install-plan":
            result = install_plan(args.manifest, args.python_executable)
            print(json.dumps(result, sort_keys=True))
        else:
            existing = None
            if args.existing_release is not None:
                try:
                    existing = json.loads(args.existing_release.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError) as exc:
                    raise ReleaseError("cannot read existing release identity") from exc
                if not isinstance(existing, dict):
                    raise ReleaseError("existing release identity must be a JSON object")
            result = publication_plan(args.manifest, args.repository, existing)
            print(json.dumps(result, sort_keys=True))
    except ReleaseError as exc:
        print(f"release_error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
