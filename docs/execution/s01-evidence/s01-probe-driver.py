"""PR-026 S01 real-Windows raw-status probe (diagnostic only).

Spawn real AppContainer children through the PATCHED winspawn primitives and
read the raw child exit status before and after handle closure.

A/B discriminator: cmd.exe (control) vs powershell.exe (subject), both from
System32, same cwd, same profile access.  Environment delta vs the production
scoped pipeline is recorded in the output and must be interpreted in the S01
classification matrix.
"""
from __future__ import annotations

import ctypes
import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from sentinelx_core import windows_mutation_sandbox as wms
from sentinelx_core.winspawn import create_suspended_appcontainer_job_process

SYSTEM32 = Path("C:/Windows/System32")
PROBE_ROOT = Path("C:/Users/liqiu/s01-probe-root")


def run_probe(label: str, argv: list[str]) -> dict:
    profile = f"SentinelX.Mutation.S01Probe.{uuid.uuid4().hex[:12]}"
    cwd = PROBE_ROOT / f"{label}-cwd"
    cwd.mkdir(parents=True, exist_ok=True)
    result: dict = {
        "label": label,
        "argv": argv,
        "profile": profile,
        "cwd": str(cwd),
    }
    sid = wms._ensure_appcontainer_profile(profile)
    result["appcontainer_sid"] = sid
    try:
        wms._set_exact_acl(cwd, wms._current_process_sid(), sid)
        result["cwd_acl"] = "set_exact_acl(broker+appcontainer) applied"
        with wms._appcontainer_sid_pointer(profile) as sid_ptr:
            process = create_suspended_appcontainer_job_process(
                appcontainer_sid=sid_ptr,
                argv=argv,
                cwd=str(cwd),
                env=None,
            )
        result["spawn"] = {
            "pid": process.pid,
            "job_ref": process.job_ref,
            "contained": process.contained,
            "breakaway_allowed": process.breakaway_allowed,
            "resumed": True,
        }
        process.resume()
        done = process.wait(None)
        raw_open = process.exit_code
        result["raw_exit_code_while_open"] = raw_open
        result["wait_completed"] = bool(done)
        process.close()
        result["raw_exit_code_after_close"] = process.exit_code
        result["job_handle_closed"] = process._closed
        result["active_process_count_after_close"] = process.active_process_count
    finally:
        try:
            wms._delete_appcontainer_profile(profile)
            result["profile_deleted"] = True
        except Exception as exc:  # noqa: BLE001
            result["profile_deleted"] = False
            result["profile_delete_error"] = str(exc)
    return result


def main() -> None:
    payload = {
        "probe": "PR-026-S01-raw-status",
        "patch_revision": "workspace pr026-s01-a1 (winspawn close-snapshot)",
        "environment_deltas_vs_production": [
            "cwd under user profile without ancestor FILE_TRAVERSE grants "
            "(production grants traverse on all ancestors as LocalSystem)",
            "child environment inherited from probe driver (production uses "
            "the scoped sanitizer)",
            "no durable audit journal (probe is not a scoped_mutation run)",
        ],
        "runs": [
            run_probe("cmd-control", [str(SYSTEM32 / "cmd.exe"), "/d", "/c", "exit 0"]),
            run_probe(
                "powershell-subject",
                [
                    str(SYSTEM32 / "WindowsPowerShell" / "v1.0" / "powershell.exe"),
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    "Write-Output SCOPED_PS_OK; exit 0",
                ],
            ),
            run_probe(
                "powershell-fileproof",
                [
                    str(SYSTEM32 / "WindowsPowerShell" / "v1.0" / "powershell.exe"),
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    "Set-Content -LiteralPath 'ps-ran.txt' -Value 'SCOPED_PS_OK'",
                ],
            ),
        ],
    }
    proof = PROBE_ROOT / "powershell-fileproof-cwd" / "ps-ran.txt"
    payload["fileproof_artifact"] = {
        "path": str(proof),
        "exists": proof.exists(),
        "content": proof.read_text(encoding="utf-8").strip() if proof.exists() else None,
    }
    out = Path(__file__).parent / "s01-probe-evidence.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    for run in payload["runs"]:
        print(
            run["label"],
            "raw_open=",
            run.get("raw_exit_code_while_open"),
            "raw_closed=",
            run.get("raw_exit_code_after_close"),
            "hex=0x%08X" % run["raw_exit_code_while_open"]
            if isinstance(run.get("raw_exit_code_while_open"), int)
            else "hex=unavailable",
        )


if __name__ == "__main__":
    main()
