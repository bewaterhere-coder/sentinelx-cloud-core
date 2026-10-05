from __future__ import annotations

import asyncio
from pathlib import Path

from tests.test_verification_scoped_execution import _fixture


def _run_profiled_node(tmp_path: Path, *, direct_provider_node: bool):
    profile, verification, handler, context, store, record, mutation, lineage, repo = _fixture(tmp_path)
    if direct_provider_node:
        node = str(profile.resolve_node(require_exists=True)).replace("'", "''")
        command = (
            f"& '{node}' -e \"console.log('DIRECT_CWD='+process.cwd())\"; "
            "exit $LASTEXITCODE"
        )
    else:
        command = "node -e \"console.log('SHIM_CWD='+process.cwd())\"; exit $LASTEXITCODE"
    result = asyncio.run(handler(context, {
        "interpreter": "pwsh",
        "content": command,
        "timeout": 30,
        "cleanup": True,
        "verification": verification,
        "mutation": mutation,
        "lineage": lineage,
        "repository": repo,
    }))
    if result["ok"] is not True:
        print("NODE_DIAGNOSTIC=" + repr(result))
    return result, record


def test_profiled_direct_provider_node_observes_exact_source_cwd(tmp_path: Path) -> None:
    result, record = _run_profiled_node(tmp_path, direct_provider_node=True)
    assert result["ok"] is True, result
    expected = str(Path(record.exact_workspace) / "source").casefold()
    assert ("DIRECT_CWD=" + expected) in result["output"].casefold(), result


def test_profiled_workspace_shim_node_observes_exact_source_cwd(tmp_path: Path) -> None:
    result, record = _run_profiled_node(tmp_path, direct_provider_node=False)
    assert result["ok"] is True, result
    expected = str(Path(record.exact_workspace) / "source").casefold()
    assert ("SHIM_CWD=" + expected) in result["output"].casefold(), result
