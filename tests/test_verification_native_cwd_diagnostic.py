from __future__ import annotations

import asyncio

from tests.test_verification_scoped_execution import _fixture


def test_unprofiled_pwsh_same_policy_with_nested_source_cwd(tmp_path) -> None:
    _profile, _verification, handler, context, _store, _record, mutation, lineage, repo = _fixture(tmp_path)
    result = asyncio.run(handler(context, {
        "interpreter": "pwsh",
        "content": "Write-Output 'PWSH_NESTED_CWD_OK'; exit 0",
        "cwd": "source",
        "timeout": 20,
        "cleanup": True,
        "mutation": mutation,
        "lineage": lineage,
        "repository": repo,
    }))
    print("S03_UNPROFILED_PWSH_NESTED_CWD_RESULT=" + repr(result))
    assert result["ok"] is True, result
    assert result["returncode"] == 0, result
    assert "PWSH_NESTED_CWD_OK" in result["output"], result
