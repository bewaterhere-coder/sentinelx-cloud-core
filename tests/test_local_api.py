"""local_api: the parts that hold without a socket.

The security boundary here is the action allowlist, because a socket bridge is
bounded only by whatever the far side exposes and the agent cannot enumerate
that. These tests pin the allowlist, the projection and the config validation;
the transport itself is exercised against a real Docker socket.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from sentinelx_core.local_api import LocalApiError, _render, project
from sentinelx_core.policy import Policy


def _policy(body: str, tmp_path: Path) -> Policy:
    p = tmp_path / "config.yaml"
    p.write_text(textwrap.dedent(body), encoding="utf-8")
    return Policy.from_file(p)


# --- projection -----------------------------------------------------------


def test_projection_keeps_only_what_the_action_declared() -> None:
    # The measurement behind this: raw Docker JSON for "what is running" is
    # 20,340 bytes against 712 for the text it replaces. Passing it through
    # would be a regression, not a feature.
    raw = {"Names": ["/web"], "Image": "nginx", "HostConfig": {"x": 1} }
    assert project(raw, ("Names", "Image")) == {"Names": ["/web"], "Image": "nginx"}


def test_projection_reaches_into_nested_fields() -> None:
    assert project({"Config": {"Image": "nginx"}}, ("Config.Image",)) == {
        "Config.Image": "nginx"
    }


def test_projection_maps_over_a_list() -> None:
    raw = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
    assert project(raw, ("a",)) == [{"a": 1}, {"a": 3}]


def test_an_empty_selection_passes_the_body_through() -> None:
    # The escape hatch for endpoints whose answers are already small.
    raw = {"anything": [1, 2, 3]}
    assert project(raw, ()) == raw


def test_a_missing_field_is_omitted_rather_than_null() -> None:
    assert project({"a": 1}, ("a", "nope")) == {"a": 1}


# --- request rendering ----------------------------------------------------


def test_placeholders_are_filled() -> None:
    assert _render("/v1.44/containers/{id}/json", {"id": "abc"}) == (
        "/v1.44/containers/abc/json"
    )


def test_values_are_url_quoted() -> None:
    # There is no shell on this path, so quoting is for the URL. A slash in a
    # value must not become another path segment.
    assert _render("/c/{id}", {"id": "a/b"}) == "/c/a%2Fb"


def test_a_missing_placeholder_is_an_error_not_an_empty_string() -> None:
    # Silently requesting /containers//json is worse than refusing.
    with pytest.raises(LocalApiError) as exc:
        _render("/v1.44/containers/{id}/json", {})
    assert exc.value.code == "missing_param"
    assert "id" in exc.value.message


# --- config validation ----------------------------------------------------


def test_an_endpoint_without_actions_is_not_registered(tmp_path: Path) -> None:
    # The allowlist IS the boundary. No list, no endpoint.
    pol = _policy(
        """
        local_apis:
          docker:
            transport: unix
            path: /var/run/docker.sock
            protocol: http
        """,
        tmp_path,
    )
    assert pol.local_apis == {}


def test_an_unknown_transport_is_refused(tmp_path: Path) -> None:
    pol = _policy(
        """
        local_apis:
          x:
            transport: telepathy
            path: /tmp/x.sock
            protocol: http
            actions: { a: { request: "GET /" } }
        """,
        tmp_path,
    )
    assert pol.local_apis == {}


def test_one_bad_action_does_not_take_the_endpoint_down(tmp_path: Path) -> None:
    pol = _policy(
        """
        local_apis:
          herdr:
            transport: unix
            path: /run/herdr.sock
            protocol: jsonrpc
            actions:
              agent.list: { method: agent.list }
              broken: { request: "GET /" }
        """,
        tmp_path,
    )
    assert sorted(pol.local_apis["herdr"].actions) == ["agent.list"]


def test_a_host_without_the_block_has_no_endpoints(tmp_path: Path) -> None:
    # This is what makes the feature additive for a fleet that did not opt in.
    assert _policy("allowed_commands: []\n", tmp_path).local_apis == {}


def test_the_compatibility_constraint_is_carried_verbatim(tmp_path: Path) -> None:
    # The agent evaluates a DECLARED constraint and never infers compatibility
    # from new_version >= configured_version.
    pol = _policy(
        """
        local_apis:
          herdr:
            transport: unix
            path: /run/herdr.sock
            protocol: jsonrpc
            compatibility:
              protocol: { exact: 20 }
            actions:
              agent.list: { method: agent.list }
        """,
        tmp_path,
    )
    assert pol.local_apis["herdr"].compatibility == {"protocol": {"exact": 20}}
