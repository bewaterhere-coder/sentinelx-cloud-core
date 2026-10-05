from __future__ import annotations

import asyncio

from sentinelx_core.handlers import scoped_script as scoped_script_module
from tests.test_verification_scoped_execution import _fixture


def test_profiled_pwsh_root_with_sanitized_base_environment(tmp_path, monkeypatch) -> None:
    _profile, verification, handler, context, _store, _record, mutation, lineage, repo = _fixture(tmp_path)

    def keep_sanitized_base_environment(base_environment, _caller_environment, _materialized):
        return dict(base_environment)

    monkeypatch.setattr(
        scoped_script_module,
        "build_verification_environment",
        keep_sanitized_base_environment,
    )
    result = asyncio.run(handler(context, {
        "interpreter": "pwsh",
        "content": "Write-Output 'PWSH_ROOT_OK'; exit 0",
        "timeout": 20,
        "cleanup": True,
        "verification": verification,
        "mutation": mutation,
        "lineage": lineage,
        "repository": repo,
    }))
    print("S03_SANITIZED_BASE_ENV_PWSH_RESULT=" + repr(result))
    assert result["ok"] is True, result
    assert result["returncode"] == 0, result
    assert "PWSH_ROOT_OK" in result["output"], result
