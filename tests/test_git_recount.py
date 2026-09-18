"""apply_patch survives hunk headers a model got wrong.

MEASURED over 14 days: ~3,100 apply_patch calls from 240 users failed with
"corrupt patch at line N", clustered on lines 10-22, which is the first hunk.
That is the signature of wrong @@ -a,b +c,d @@ counts, the classic failure of a
model writing a unified diff by hand. Unlike the not_a_git_repo failures, these
were NOT retry loops (8% from loops of 5+), so the model was rewriting the patch
each time rather than repeating it: the work was real and wasted.

The retry is the SECOND attempt on purpose. --recount tells git to trust the
hunk body and redo the arithmetic, so it accepts patches currently rejected. A
patch wrong in some other way could then apply as something slightly different
from what was meant. Keeping it second means everything that works today
behaves identically, and the result says when a recount happened.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from sentinelx_core.handlers import build_registry
from sentinelx_core.policy import Policy

GOOD = """--- a/f.txt
+++ b/f.txt
@@ -3,3 +3,4 @@ line2
 line3
 line4
+INSERTED
 line5
"""

WRONG_COUNTS = """--- a/f.txt
+++ b/f.txt
@@ -3,9 +3,9 @@ line2
 line3
 line4
+INSERTED
 line5
"""

TRUNCATED = """--- a/f.txt
+++ b/f.txt
@@ -3,4 +3,5 @@
 line3
 line4
+INSERTED
"""


@pytest.fixture
def repo(tmp_path: Path):
    (tmp_path / "f.txt").write_text(
        "".join(f"line{i}\n" for i in range(1, 11)), encoding="utf-8"
    )
    for args in (["init", "-q"], ["add", "f.txt"],
                 ["-c", "user.email=t@t", "-c", "user.name=t",
                  "commit", "-qm", "init"]):
        subprocess.run(["git", "-C", str(tmp_path), *args], check=True,
                       capture_output=True)
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        f"allowed_commands: []\nfile_ops:\n  paths:\n"
        f"    - {{path: {tmp_path}, access: rw}}\n",
        encoding="utf-8",
    )
    return tmp_path, build_registry(policy=Policy.from_file(cfg))["git"]


async def _apply(handler, root, patch):
    return await handler({"operation": "apply_patch", "path": str(root),
                          "patch": patch, "dry_run": True})


async def test_a_correct_patch_is_untouched(repo) -> None:
    # The guarantee that matters: nothing that works today changes.
    root, h = repo
    r = await _apply(h, root, GOOD)
    assert r["ok"] is True
    assert "recounted" not in r


async def test_wrong_hunk_counts_now_apply(repo) -> None:
    # This is the 3,100-call failure. git rejects it outright and accepts it
    # once the counts are recomputed.
    root, h = repo
    r = await _apply(h, root, WRONG_COUNTS)
    assert r["ok"] is True
    assert r["recounted"] is True
    assert r["summary"]["insertions"] == 1


async def test_a_recount_is_reported_not_silent(repo) -> None:
    # A patch that only worked because git redid its arithmetic was still
    # malformed as written. Saying so is how that stops being invisible.
    root, h = repo
    r = await _apply(h, root, WRONG_COUNTS)
    assert r.get("recounted") is True


async def test_a_truncated_hunk_still_fails_but_says_what_to_fix(repo) -> None:
    # --recount cannot invent missing lines. What changes is the message: the
    # old one was "corrupt patch at line 7" and nothing else, which the audit
    # shows models retrying blind.
    from sentinelx_core.executor import HandlerError

    root, h = repo
    with pytest.raises(HandlerError) as exc:
        await _apply(h, root, TRUNCATED)
    msg = str(exc.value)
    assert "recomputed" in msg
    assert "leading space" in msg
