from __future__ import annotations

import asyncio

from tests.test_verification_scoped_execution import _fixture


def test_profiled_pwsh_launches_root_from_workspace_then_enters_source(tmp_path) -> None:
    _profile, verification, handler, context, _store, _record, mutation, lineage, repo = _fixture(tmp_path)
    result = asyncio.run(handler(context, {
        "interpreter": "pwsh",
        "content": "Write-Output ('LOGICAL_CWD=' + (Get-Location).Path); exit 0",
        "timeout": 20,
        "cleanup": True,
        "verification": verification,
        "mutation": mutation,
        "lineage": lineage,
        "repository": repo,
    }))
    print("S03_PROFILED_PWSH_RUNNER_CWD_RESULT=" + repr(result))
    assert result["ok"] is True, result
    assert result["returncode"] == 0, result
    assert result["cwd"] == "source", result
    assert "LOGICAL_CWD=" in result["output"], result
    assert result["terminal_state"] == "terminal", result
