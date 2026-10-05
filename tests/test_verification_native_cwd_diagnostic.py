from __future__ import annotations

import asyncio

from tests.test_verification_scoped_execution import _fixture


def _run_python_probe(tmp_path, *, mode: str):
    profile, verification, handler, context, _store, _record, mutation, lineage, repo = _fixture(tmp_path)
    node = str(profile.resolve_node())
    npm_cli = str(profile.resolve_npm_cli())
    if mode == "direct-node":
        argv = [node, "--version"]
    elif mode == "shim-node":
        argv = ["cmd.exe", "/d", "/s", "/c", "node --version"]
    elif mode == "direct-npm":
        argv = [node, npm_cli, "--version"]
    else:
        raise AssertionError(f"unsupported probe mode: {mode}")

    content = (
        "import json, os, subprocess\n"
        f"argv = {argv!r}\n"
        "print('PY_ROOT_CWD=' + os.getcwd())\n"
        "print('PROBE_ARGV=' + json.dumps(argv))\n"
        "try:\n"
        "    completed = subprocess.run(argv, cwd=os.getcwd(), capture_output=True, text=True, timeout=12)\n"
        "except subprocess.TimeoutExpired as exc:\n"
        "    print('PROBE_TIMEOUT=' + repr(exc))\n"
        "    raise SystemExit(124)\n"
        "print('PROBE_RETURN=' + str(completed.returncode))\n"
        "print('PROBE_STDOUT=' + completed.stdout.strip())\n"
        "print('PROBE_STDERR=' + completed.stderr.strip())\n"
        "raise SystemExit(completed.returncode)\n"
    )
    result = asyncio.run(handler(context, {
        "interpreter": "python3",
        "content": content,
        "timeout": 30,
        "cleanup": True,
        "verification": verification,
        "mutation": mutation,
        "lineage": lineage,
        "repository": repo,
    }))
    print(f"S03_{mode.upper().replace('-', '_')}_RESULT=" + repr(result))
    return result


def _assert_probe_success(result) -> None:
    assert result["ok"] is True, result
    assert result["returncode"] == 0, result
    assert result["cwd"] == "source", result
    assert "PY_ROOT_CWD=" in result["output"], result
    assert "PROBE_RETURN=0" in result["output"], result
    assert result["terminal_state"] == "terminal", result


def test_profiled_python_root_launches_direct_sealed_node(tmp_path) -> None:
    _assert_probe_success(_run_python_probe(tmp_path, mode="direct-node"))


def test_profiled_python_root_launches_workspace_node_shim(tmp_path) -> None:
    _assert_probe_success(_run_python_probe(tmp_path, mode="shim-node"))


def test_profiled_python_root_launches_direct_npm_cli(tmp_path) -> None:
    _assert_probe_success(_run_python_probe(tmp_path, mode="direct-npm"))
