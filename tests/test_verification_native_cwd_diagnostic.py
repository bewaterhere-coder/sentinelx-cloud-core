from __future__ import annotations

import asyncio

from sentinelx_core.handlers import scoped_script as scoped_script_module
from tests.test_verification_scoped_execution import _fixture


def test_profiled_materialization_with_base_environment_descendant(tmp_path, monkeypatch) -> None:
    _profile, verification, handler, context, _store, _record, mutation, lineage, repo = _fixture(tmp_path)

    def keep_base_environment(base_environment, _caller_environment, _materialized):
        return dict(base_environment)

    monkeypatch.setattr(
        scoped_script_module,
        "build_verification_environment",
        keep_base_environment,
    )
    body = '''\
import os
import subprocess

argv = [os.environ.get("COMSPEC", r"C:\\Windows\\System32\\cmd.exe"), "/d", "/s", "/c", "exit 0"]
completed = subprocess.run(argv, stdin=None, stdout=None, stderr=None, check=False)
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
    print("S03_PROFILED_BASE_ENV_CMD_RESULT=" + repr(result))
    assert result["ok"] is True, result
    assert result["returncode"] == 0, result
    assert "CMD_RETURN=0" in result["output"], result
