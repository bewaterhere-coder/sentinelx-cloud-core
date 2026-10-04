from __future__ import annotations

import asyncio
from pathlib import Path

from tests.test_verification_scoped_execution import _fixture


def test_profiled_native_node_observes_exact_source_cwd(tmp_path: Path) -> None:
    _profile, verification, handler, context, store, record, mutation, lineage, repo = _fixture(tmp_path)
    result = asyncio.run(handler(context, {
        "interpreter": "pwsh",
        "content": "node -e \"console.log('NATIVE_CWD='+process.cwd())\"; exit $LASTEXITCODE",
        "timeout": 30,
        "cleanup": True,
        "verification": verification,
        "mutation": mutation,
        "lineage": lineage,
        "repository": repo,
    }))
    assert result["ok"] is True, result
    expected = str(Path(record.exact_workspace) / "source").casefold()
    assert ("NATIVE_CWD=" + expected) in result["output"].casefold(), result
