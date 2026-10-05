from __future__ import annotations

import asyncio

from tests.test_verification_scoped_execution import _fixture


def test_profiled_python_root_bisects_npm_module_initialization(tmp_path) -> None:
    profile, verification, handler, context, _store, _record, mutation, lineage, repo = _fixture(tmp_path)
    node = str(profile.resolve_node())
    npm_cli = profile.resolve_npm_cli()
    npm_root = npm_cli.parent.parent
    probes = [
        (
            "read-cli",
            [node, "-e", "const fs=require('fs'); console.log('BYTES='+fs.readFileSync(process.argv[1]).length)", str(npm_cli)],
        ),
        (
            "require-package",
            [node, "--preserve-symlinks", "-e", "require(process.argv[1]); console.log('REQUIRE_PACKAGE_OK')", str(npm_root / "package.json")],
        ),
        (
            "require-validate-engines",
            [node, "--preserve-symlinks", "-e", "require(process.argv[1]); console.log('REQUIRE_VALIDATE_OK')", str(npm_root / "lib" / "cli" / "validate-engines.js")],
        ),
        (
            "require-cli",
            [node, "--preserve-symlinks", "-e", "require(process.argv[1]); console.log('REQUIRE_CLI_OK')", str(npm_root / "lib" / "cli.js")],
        ),
        (
            "require-entry",
            [node, "--preserve-symlinks", "-e", "require(process.argv[1]); console.log('REQUIRE_ENTRY_OK')", str(npm_root / "lib" / "cli" / "entry.js")],
        ),
        (
            "construct-npm",
            [node, "--preserve-symlinks", "-e", "const Npm=require(process.argv[1]); new Npm(); console.log('CONSTRUCT_NPM_OK')", str(npm_root / "lib" / "npm.js")],
        ),
    ]
    content = (
        "import os, subprocess\n"
        f"probes = {probes!r}\n"
        "print('PY_ROOT_CWD=' + os.getcwd())\n"
        "for label, argv in probes:\n"
        "    print('PROBE_START=' + label)\n"
        "    try:\n"
        "        completed = subprocess.run(argv, cwd=os.getcwd(), capture_output=True, text=True, timeout=8)\n"
        "        print('PROBE_DONE=' + label + ':' + str(completed.returncode))\n"
        "        print('PROBE_OUT=' + label + ':' + completed.stdout.strip())\n"
        "        print('PROBE_ERR=' + label + ':' + completed.stderr.strip())\n"
        "    except subprocess.TimeoutExpired as exc:\n"
        "        print('PROBE_TIMEOUT=' + label)\n"
        "        print('PROBE_TIMEOUT_OUT=' + label + ':' + repr(exc.stdout))\n"
        "        print('PROBE_TIMEOUT_ERR=' + label + ':' + repr(exc.stderr))\n"
        "print('BISECT_COMPLETE=1')\n"
    )
    result = asyncio.run(handler(context, {
        "interpreter": "python3",
        "content": content,
        "timeout": 70,
        "cleanup": True,
        "verification": verification,
        "mutation": mutation,
        "lineage": lineage,
        "repository": repo,
    }))
    print("S03_NPM_MODULE_BISECT_RESULT=" + repr(result))
    assert result["ok"] is True, result
    assert result["cwd"] == "source", result
    assert "BISECT_COMPLETE=1" in result["output"], result
    assert result["terminal_state"] == "terminal", result
