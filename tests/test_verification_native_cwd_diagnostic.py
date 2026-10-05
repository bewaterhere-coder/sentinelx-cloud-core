from __future__ import annotations

import asyncio

from tests.test_verification_scoped_execution import _fixture


def test_profiled_trivial_cmd_descendant_completes(tmp_path) -> None:
    _profile, verification, handler, context, _store, _record, mutation, lineage, repo = _fixture(tmp_path)
    body = '''\
import os
from pathlib import Path
import subprocess

argv = [os.environ.get("COMSPEC", r"C:\\Windows\\System32\\cmd.exe"), "/d", "/s", "/c", "exit 0"]
out = Path.cwd() / "cmd-exit.stdout"
err = Path.cwd() / "cmd-exit.stderr"
with out.open("wb") as stdout, err.open("wb") as stderr:
    completed = subprocess.run(argv, stdin=None, stdout=stdout, stderr=stderr, check=False)
print("CMD_RETURN=" + str(completed.returncode))
raise SystemExit(completed.returncode)
'''
    result = asyncio.run(handler(context, {
        "interpreter": "python3",
        "content": body,
        "timeout": 20,
        "cleanup": True,
        "verification": verification,
        "mutation": mutation,
        "lineage": lineage,
        "repository": repo,
    }))
    print("S03_TRIVIAL_CMD_DESCENDANT_RESULT=" + repr(result))
    assert result["ok"] is True, result
    assert result["returncode"] == 0, result
    assert "CMD_RETURN=0" in result["output"], result
