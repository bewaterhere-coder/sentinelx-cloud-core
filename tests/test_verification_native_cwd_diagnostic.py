from __future__ import annotations

import asyncio
from pathlib import Path

from tests.test_verification_scoped_execution import _fixture


def _run_descendant_probe(tmp_path: Path, *, use_shim: bool) -> dict[str, object]:
    profile, verification, handler, context, _store, _record, mutation, lineage, repo = _fixture(tmp_path)
    direct_node = str(profile.resolve_node(require_exists=True))
    if use_shim:
        body = '''\
import os
from pathlib import Path
import subprocess

argv = [os.environ.get("COMSPEC", r"C:\\Windows\\System32\\cmd.exe"), "/d", "/s", "/c", "node.cmd --version"]
out = Path.cwd() / "shim-node.stdout"
err = Path.cwd() / "shim-node.stderr"
with out.open("wb") as stdout, err.open("wb") as stderr:
    completed = subprocess.run(argv, stdin=None, stdout=stdout, stderr=stderr, check=False)
print("SHIM_RETURN=" + str(completed.returncode))
raise SystemExit(completed.returncode)
'''
    else:
        body = f'''\
from pathlib import Path
import subprocess

argv = [{direct_node!r}, "--version"]
out = Path.cwd() / "direct-node.stdout"
err = Path.cwd() / "direct-node.stderr"
with out.open("wb") as stdout, err.open("wb") as stderr:
    completed = subprocess.run(argv, stdin=None, stdout=stdout, stderr=stderr, check=False)
print("DIRECT_RETURN=" + str(completed.returncode))
raise SystemExit(completed.returncode)
'''
    return asyncio.run(handler(context, {
        "interpreter": "python3",
        "content": body,
        "timeout": 20,
        "cleanup": True,
        "verification": verification,
        "mutation": mutation,
        "lineage": lineage,
        "repository": repo,
    }))


def test_profiled_direct_provider_node_descendant_completes(tmp_path: Path) -> None:
    result = _run_descendant_probe(tmp_path, use_shim=False)
    print("S03_DIRECT_DESCENDANT_RESULT=" + repr(result))
    assert result["ok"] is True, result
    assert result["returncode"] == 0, result
    assert "DIRECT_RETURN=0" in result["output"], result


def test_profiled_workspace_shim_node_descendant_completes(tmp_path: Path) -> None:
    result = _run_descendant_probe(tmp_path, use_shim=True)
    print("S03_SHIM_DESCENDANT_RESULT=" + repr(result))
    assert result["ok"] is True, result
    assert result["returncode"] == 0, result
    assert "SHIM_RETURN=0" in result["output"], result
