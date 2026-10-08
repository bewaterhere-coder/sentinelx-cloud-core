"""A directory the agent cannot enter is not "not a git repository".

Same shape as test_git_dubious_ownership: git exits 128 for an EACCES exactly
as it does for "there is no repo here", and reading only the rc collapsed the
two. The resulting message told the caller the directory was not a checkout and
that retrying was pointless -- false, and true-for-the-wrong-reason
respectively. It sent people looking for a repository that was never missing.

Found where the agent's own account could not traverse a 0750 home directory.
sentinel_read on a file inside the same tree reported "Permission denied"
correctly, so two tools disagreed about one cause. stderr is what separates
them, and it always said so.
"""

from __future__ import annotations

from sentinelx_core.handlers.git_ops import (
    _agent_user,
    _dubious_ownership,
    _permission_denied,
)


def test_the_traversal_refusal_is_recognised():
    err = (b"fatal: cannot change to "
           b"'/home/carlos/projects/sentinelx-cloud': Permission denied\n")
    assert _permission_denied(err) is True


def test_the_access_wording_is_recognised_too():
    # git words this differently depending on which syscall failed first.
    assert _permission_denied(b"fatal: cannot access '/srv/x': Permission denied\n") is True


def test_capitalisation_does_not_matter():
    # _GIT_ENV pins LC_ALL=C, but git capitalises the phrase and we match lower.
    assert _permission_denied(b"error: PERMISSION DENIED\n") is True


def test_a_plain_directory_is_not_mistaken_for_it():
    # This one must still reach not_a_git_repo, which is the correct answer.
    assert _permission_denied(b"fatal: not a git repository (or any parent)\n") is False


def test_empty_stderr_is_not_it():
    assert _permission_denied(b"") is False


def test_other_git_failures_are_not_it():
    for err in (b"fatal: your current branch appears to be broken\n",
                b"error: object file is empty\n",
                b"fatal: unable to read tree\n"):
        assert _permission_denied(err) is False


def test_an_ssh_key_rejection_is_not_a_filesystem_problem():
    # "Permission denied (publickey)" is a transport failure from the network
    # operations. Reporting it as a local-permissions problem would send the
    # operator to chmod when the answer is a deploy key.
    err = b"git@github.com: Permission denied (publickey).\nfatal: Could not read\n"
    assert _permission_denied(err) is False


def test_the_two_refusals_stay_distinct():
    # Both are "the repo is fine, something else refused", but the remedies are
    # different: one is a chmod or a group, the other is safe.directory.
    eacces = b"fatal: cannot change to '/x': Permission denied\n"
    dubious = b"fatal: detected dubious ownership in repository at '/x'\n"
    assert _permission_denied(eacces) and not _dubious_ownership(eacces)
    assert _dubious_ownership(dubious) and not _permission_denied(dubious)


def test_the_error_names_the_account_to_grant():
    # The operator's next action is "grant WHICH user?", so the message has to
    # answer it. Empty or a bare "unknown" would make the error non-actionable,
    # which is the whole defect being fixed here.
    who = _agent_user()
    assert who and who != "unknown"


# ---------------------------------------------------------------------------
# The behavioural half. The predicate tests above would pass on a build where
# the helper exists but nothing calls it; these are what actually fail on the
# pre-fix handler, where every one of them came back as not_a_git_repo.
# ---------------------------------------------------------------------------

import pytest

from sentinelx_core.executor import HandlerError
from sentinelx_core.handlers import git_ops

EACCES = b"fatal: cannot change to '/home/carlos/projects': Permission denied\n"
NO_REPO = b"fatal: not a git repository (or any of the parent directories): .git\n"
DUBIOUS = b"fatal: detected dubious ownership in repository at '/srv/x'\n"


def _git_failing_with(stderr: bytes):
    async def fake(root, *args, stdin=None, timeout=None):
        return 128, b"", stderr

    return fake


async def test_eacces_is_reported_as_permission_denied(monkeypatch):
    # THE REGRESSION. Pre-fix this raised not_a_git_repo.
    monkeypatch.setattr(git_ops, "_run_git", _git_failing_with(EACCES))
    with pytest.raises(HandlerError) as excinfo:
        await git_ops._revalidate_git_root(None, "/home/carlos/projects", "/home/carlos/projects")
    assert excinfo.value.code == "permission_denied"


async def test_the_message_says_it_is_the_host_and_not_the_allowlist(monkeypatch):
    # The allowlist is the first thing an operator suspects, and it is the
    # wrong place to look: naming the path in file_ops changes nothing here.
    monkeypatch.setattr(git_ops, "_run_git", _git_failing_with(EACCES))
    with pytest.raises(HandlerError) as excinfo:
        await git_ops._revalidate_git_root(None, "/home/carlos", "/home/carlos")
    message = str(excinfo.value)
    assert "file_ops" in message
    assert "sentinel_exec" in message


async def test_a_genuine_non_repo_still_says_not_a_git_repo(monkeypatch):
    # The new branch must not swallow the case it sits in front of.
    monkeypatch.setattr(git_ops, "_run_git", _git_failing_with(NO_REPO))
    with pytest.raises(HandlerError) as excinfo:
        await git_ops._revalidate_git_root(None, "/tmp", "/tmp")
    assert excinfo.value.code == "not_a_git_repo"


async def test_ownership_still_wins_its_own_branch(monkeypatch):
    monkeypatch.setattr(git_ops, "_run_git", _git_failing_with(DUBIOUS))
    with pytest.raises(HandlerError) as excinfo:
        await git_ops._revalidate_git_root(None, "/srv/x", "/srv/x")
    assert excinfo.value.code == "git_dubious_ownership"
