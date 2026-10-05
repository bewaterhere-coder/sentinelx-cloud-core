from __future__ import annotations

import asyncio

from tests.test_verification_scoped_execution import _fixture


def test_profiled_python_root_runs_npm_with_compile_cache_disabled(tmp_path) -> None:
    profile, verification, handler, context, _store, _record, mutation, lineage, repo = _fixture(tmp_path)
    node = str(profile.resolve_node())
    npm_cli = profile.resolve_npm_cli()
    npm_root = npm_cli.parent.parent
    probes = [
        (
            "require-cli",
            [
                node,
                "--preserve-symlinks",
                "--preserve-symlinks-main",
                "-e",
                "require(process.argv[1]); console.log('REQUIRE_CLI_OK')",
                str(npm_root / "lib" / "cli.js"),
            ],
        ),
        (
            "npm-version",
            [
                node,
                "--preserve-symlinks",
                "--preserve-symlinks-main",
                str(npm_cli),
                "--version",
            ],
        ),
    ]
    content = (
        "import os, subprocess\n"
        f"probes = {probes!r}\n"
        "os.environ['NODE_DISABLE_COMPILE_CACHE'] = '1'\n"
        "print('PY_ROOT_CWD=' + os.getcwd())\n"
        "print('NODE_DISABLE_COMPILE_CACHE=' + os.environ['NODE_DISABLE_COMPILE_CACHE'])\n"
        "failed = False\n"
        "for label, argv in probes:\n"
        "    print('PROBE_START=' + label)\n"
        "    try:\n"
        "        completed = subprocess.run(argv, cwd=os.getcwd(), capture_output=True, text=True, timeout=12)\n"
        "        print('PROBE_DONE=' + label + ':' + str(completed.returncode))\n"
        "        print('PROBE_OUT=' + label + ':' + completed.stdout.strip())\n"
        "        print('PROBE_ERR=' + label + ':' + completed.stderr.strip())\n"
        "        failed = failed or completed.returncode != 0\n"
        "    except subprocess.TimeoutExpired as exc:\n"
        "        failed = True\n"
        "        print('PROBE_TIMEOUT=' + label)\n"
        "        print('PROBE_TIMEOUT_OUT=' + label + ':' + repr(exc.stdout))\n"
        "        print('PROBE_TIMEOUT_ERR=' + label + ':' + repr(exc.stderr))\n"
        "raise SystemExit(1 if failed else 0)\n"
    )
    result = asyncio.run(handler(context, {
        "interpreter": "python3",
        "content": content,
        "timeout": 40,
        "cleanup": True,
        "verification": verification,
        "mutation": mutation,
        "lineage": lineage,
        "repository": repo,
    }))
    print("S03_NPM_COMPILE_CACHE_DISABLED_RESULT=" + repr(result))
    assert result["ok"] is True, result
    assert result["cwd"] == "source", result
    assert "REQUIRE_CLI_OK" in result["output"], result
    assert "PROBE_DONE=npm-version:0" in result["output"], result
    assert result["terminal_state"] == "terminal", result
