"""The empty command prefix must not crash the capabilities report.

`allowed_commands: [""]` is how an operator grants any command within the host
account: matching is `cmd.startswith(allowed)`, so "" matches everything. The
unusable-commands scan called `c.split()[0]` on every entry, and "".split() is
[], so on a NoNewPrivileges host the whole capabilities report died with an
IndexError -- the hub simply never heard back. Reported by danshapiro with the
traceback and the fix (issue #47).
"""

from __future__ import annotations

from unittest.mock import patch

from sentinelx_core.handlers.basic import _unusable_commands


class _Policy:
    def __init__(self, cmds):
        self.allowed_commands = cmds


def _on_nnp(cmds):
    with patch("sentinelx_core.handlers.basic._no_new_privileges", return_value=True):
        return _unusable_commands(_Policy(cmds))


def test_the_empty_prefix_alone_does_not_crash():
    assert _on_nnp([""]) == {}


def test_the_empty_prefix_beside_others_does_not_crash():
    assert _on_nnp(["", "ls", "sudo systemctl"]).get("commands") == ["sudo systemctl"]


def test_the_empty_prefix_is_not_itself_reported_as_unusable():
    """It grants everything, but it is not a sudo command."""
    assert "" not in _on_nnp(["", "sudo -n /usr/local/sbin/audit"]).get("commands", [])


def test_whitespace_only_entries_are_survivable_too():
    """Same shape of input, same failure mode: ' '.split() is also []."""
    assert _on_nnp([" ", "\t"]) == {}


def test_real_sudo_entries_are_still_caught():
    assert len(_on_nnp(["sudo", "sudo systemctl restart x", "/usr/bin/sudo -n t"]).get("commands", [])) == 3


def test_nothing_is_reported_off_a_nnp_host():
    with patch("sentinelx_core.handlers.basic._no_new_privileges", return_value=False):
        assert _unusable_commands(_Policy(["", "sudo x"])) == {}
