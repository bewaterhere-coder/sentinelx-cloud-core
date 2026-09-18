"""Git's own diagnostics must not depend on the host's language.

The --recount retry branches on the text of git's stderr, looking for "corrupt
patch". Git translates that text, so on a localized host the branch never
fired and the recovery silently stopped existing. Reported from a pl_PL.UTF-8
host, where git says "uszkodzona łatka w wierszu 8"; reproduced in a container
with the Polish translation installed, where the old environment misses the
condition and the pinned one catches it.

The same fix is applied to project_snapshot.py, which git_ops was copied from
and which the module header says must not diverge.
"""

from __future__ import annotations

import pytest

from sentinelx_core.handlers import git_ops, project_snapshot


@pytest.mark.parametrize("module", [git_ops, project_snapshot])
def test_the_language_of_git_messages_is_pinned(module):
    assert module._GIT_ENV.get("LC_ALL") == "C"


@pytest.mark.parametrize("module", [git_ops, project_snapshot])
def test_it_survives_a_localized_environment(module, monkeypatch):
    """_GIT_ENV is merged over os.environ, so it has to WIN over an inherited
    LANG/LC_ALL rather than merely be present."""
    monkeypatch.setenv("LANG", "pl_PL.UTF-8")
    monkeypatch.setenv("LC_ALL", "pl_PL.UTF-8")
    monkeypatch.setenv("LC_MESSAGES", "pl_PL.UTF-8")
    import os

    env = {**os.environ, **module._GIT_ENV}
    assert env["LC_ALL"] == "C", "an inherited locale must not win"


def test_the_two_modules_have_not_diverged():
    """git_ops copied its security substrate from project_snapshot verbatim and
    the header says not to diverge. A key added to one and not the other is
    exactly how the next locale-style bug gets in."""
    assert git_ops._GIT_ENV == project_snapshot._GIT_ENV


def test_the_recount_branch_still_looks_for_the_english_text():
    """If someone localizes OUR side later, this test should fail loudly rather
    than the recovery going quiet again."""
    import inspect

    src = inspect.getsource(git_ops)
    assert b"corrupt patch".decode() in src
