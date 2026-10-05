from __future__ import annotations

import asyncio

from sentinelx_core.handlers import scoped_script as scoped_script_module
from tests.test_verification_scoped_execution import _fixture

_PROFILE_PATH_KEYS = (
    "HOME",
    "USERPROFILE",
    "HOMEDRIVE",
    "HOMEPATH",
    "APPDATA",
    "LOCALAPPDATA",
    "TEMP",
    "TMP",
)


def test_profiled_descendant_with_base_profile_paths(tmp_path, monkeypatch) -> None:
    _profile, verification, handler, context, _store, _record, mutation, lineage, repo = _fixture(tmp_path)
    real_builder = scoped_script_module.build_verification_environment

    def keep_base_profile_paths(base_environment, caller_environment, materialized):
        environment = real_builder(base_environment, caller_environment, materialized)
        for key in _PROFILE_PATH_KEYS:
            environment[key] = base_environment[key]
        return environment

    monkeypatch.setattr(
        scoped_script_module,
        "build_verification_environment",
        keep_base_profile_paths,
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
    print("S03_BASE_PROFILE_PATHS_CMD_RESULT=" + repr(result))
    assert result["ok"] is True, result
    assert result["returncode"] == 0, result
    assert "CMD_RETURN=0" in result["output"], result
