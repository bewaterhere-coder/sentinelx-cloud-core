from __future__ import annotations

import sys

import pytest

from sentinelx_core.executor import HandlerError
from sentinelx_core.handlers.git_ops import _credential_context_for_remote
from sentinelx_core.policy import Policy
from sentinelx_core.user_git import (
    FEATURE_NAME,
    LEGACY_FEATURE_NAME,
    classify_result,
    redact_git_output,
    user_scoped_git_supported,
)


def test_authenticated_git_policy_defaults_fail_closed() -> None:
    p = Policy.empty()
    assert p.authenticated_git_enabled is False
    assert p.authenticated_git_allow_push is False
    assert p.authenticated_git_timeout_seconds == 20


def test_authenticated_git_policy_explicit_opt_in() -> None:
    p = Policy.from_dict({"authenticated_git": {"enabled": True, "allow_push": True, "timeout_seconds": 17}})
    assert p.authenticated_git_enabled is True
    assert p.authenticated_git_allow_push is True
    assert p.authenticated_git_timeout_seconds == 17


def test_authenticated_git_timeout_is_bounded() -> None:
    low = Policy.from_dict({"authenticated_git": {"enabled": True, "timeout_seconds": 1}})
    high = Policy.from_dict({"authenticated_git": {"enabled": True, "timeout_seconds": 999}})
    assert low.authenticated_git_timeout_seconds == 5
    assert high.authenticated_git_timeout_seconds == 50


def test_automatic_context_requires_no_tool_schema_field() -> None:
    p = Policy.from_dict({"authenticated_git": {"enabled": True}})
    assert _credential_context_for_remote(p, {}, "ls_remote") == "user_scoped"
    assert _credential_context_for_remote(p, {}, "fetch") == "user_scoped"
    assert _credential_context_for_remote(p, {}, "push") == "current"


def test_push_is_second_opt_in() -> None:
    p = Policy.from_dict({"authenticated_git": {"enabled": True, "allow_push": True}})
    assert _credential_context_for_remote(p, {}, "push") == "user_scoped"


def test_explicit_user_scoped_fails_closed_when_policy_off() -> None:
    with pytest.raises(HandlerError) as e:
        _credential_context_for_remote(Policy.empty(), {"credential_context": "user_scoped"}, "fetch")
    assert e.value.code == "GitExecutionContextUnavailable"


def test_secret_url_is_redacted() -> None:
    text = "fatal: https://alice:super-secret@example.com/private.git failed"
    redacted = redact_git_output(text)
    assert "super-secret" not in redacted
    assert "alice" not in redacted


@pytest.mark.parametrize(("stderr", "expected"), [
    (b"fatal: Authentication failed for x", "GitCredentialRejected"),
    (b"Permission denied (publickey).", "GitCredentialRejected"),
    (b"fatal: could not read Username for 'https://github.com': terminal prompts disabled", "GitCredentialInteractiveRequired"),
    (b"Recv failure: Connection was reset", "GitTransportReset"),
    (b"Failed to connect to github.com:443 after 20000 ms", "GitTransportTimeout"),
    (b"Could not resolve host: github.com", "GitRemoteTemporarilyUnavailable"),
])
def test_failure_classification(stderr: bytes, expected: str) -> None:
    assert classify_result(1, stderr) == expected


def test_feature_names() -> None:
    assert FEATURE_NAME == "host_runtime.git_execution_context_v1"
    assert LEGACY_FEATURE_NAME == "host_runtime.git_authenticated_v1"


def test_support_is_windows_only() -> None:
    assert user_scoped_git_supported() is (sys.platform == "win32")
