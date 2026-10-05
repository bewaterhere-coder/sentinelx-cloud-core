from __future__ import annotations

import asyncio
import json
from pathlib import Path

from tests.test_verification_scoped_execution import _fixture


def _parse_probe(output: str, name: str) -> dict[str, object]:
    prefix = f"PROBE_{name}="
    for line in output.splitlines():
        if line.startswith(prefix):
            return json.loads(line[len(prefix) :])
    raise AssertionError(f"missing {prefix} in diagnostic output: {output!r}")


def test_profiled_single_root_distinguishes_direct_node_from_shim(tmp_path: Path) -> None:
    profile, verification, handler, context, _store, record, mutation, lineage, repo = _fixture(tmp_path)
    direct_node = str(profile.resolve_node(require_exists=True))
    diagnostic = f'''\
import json
import os
from pathlib import Path
import subprocess

DIRECT_NODE = {direct_node!r}
COMSPEC = os.environ.get("COMSPEC", r"C:\\Windows\\System32\\cmd.exe")
PROBE_ROOT = Path(os.environ["TEMP"])

def probe(name, argv):
    observed = {{"argv0": argv[0], "timeout": False, "returncode": None}}
    stdout_path = PROBE_ROOT / ("probe-" + name.lower() + ".stdout")
    stderr_path = PROBE_ROOT / ("probe-" + name.lower() + ".stderr")
    try:
        with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
            completed = subprocess.run(
                argv,
                stdin=None,
                stdout=stdout,
                stderr=stderr,
                timeout=10,
                check=False,
            )
        observed["returncode"] = completed.returncode
    except subprocess.TimeoutExpired:
        observed["timeout"] = True
    print("PROBE_" + name + "=" + json.dumps(observed, sort_keys=True))

probe("DIRECT", [DIRECT_NODE, "--version"])
probe("SHIM", [COMSPEC, "/d", "/s", "/c", "node.cmd --version"])
'''
    result = asyncio.run(handler(context, {
        "interpreter": "python3",
        "content": diagnostic,
        "timeout": 40,
        "cleanup": True,
        "verification": verification,
        "mutation": mutation,
        "lineage": lineage,
        "repository": repo,
    }))
    print("S03_SINGLE_ROOT_RESULT=" + repr(result))
    assert result["ok"] is True, result
    assert result["cwd"] == "source"

    direct = _parse_probe(result["output"], "DIRECT")
    shim = _parse_probe(result["output"], "SHIM")
    print("S03_DIRECT_PROBE=" + json.dumps(direct, sort_keys=True))
    print("S03_SHIM_PROBE=" + json.dumps(shim, sort_keys=True))

    assert direct["timeout"] is False, direct
    assert direct["returncode"] == 0, direct
    assert shim["timeout"] is False, shim
    assert shim["returncode"] == 0, shim

    expected = Path(record.exact_workspace) / "source"
    assert expected.is_absolute()
