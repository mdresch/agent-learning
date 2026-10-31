"""Contract tests for Epic 34, Story 34.3.

ADR-034 Invariants 1, 4, and 6; BRD-034 BRU-034-01, BRU-034-04, BRU-034-06;
FDD-034 §§2 and 3.4; Story 34.3 AC_0–AC_4.

Interpretation I1 (FDD-034 §5 item 3, confirmed by Menno on 2026-10-31):
retry counts and exponential-backoff parameters are caller-supplied. The
jitter callback returns additive seconds, is called once per delay, and its
value is added to the exponential delay.

Interpretation I2: the standard-library client sends the prompt as UTF-8
request data and returns the UTF-8 response body. The FDD specifies a URL and
prompt but no API-specific request envelope or response parsing.
"""

from __future__ import annotations

import ast
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request

import pytest

ROOT = Path(__file__).resolve().parent.parent
CLIENT_SOURCE = ROOT / "src" / "agent_learning" / "pmbok_runtime" / "client.py"
PMBOK_PACKAGE = ROOT / "src" / "agent_learning" / "pmbok"


def test_ac0_backoff_delays_are_exponential_with_additive_jitter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import time

    from agent_learning.pmbok_runtime.client import backoff_delays

    jitter_calls = 0
    sleep_calls: list[float] = []
    monkeypatch.setattr(time, "sleep", sleep_calls.append)

    def zero_jitter() -> float:
        nonlocal jitter_calls
        jitter_calls += 1
        return 0.0

    assert backoff_delays(3, 0.5, 2.0, zero_jitter) == [0.5, 1.0, 2.0]
    assert jitter_calls == 3
    assert backoff_delays(3, 0.5, 2.0, lambda: 0.25) == [0.75, 1.25, 2.25]
    assert sleep_calls == []


def test_ac1_retries_transient_http_errors_and_raises_last_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from agent_learning.pmbok_runtime import client

    sleeps: list[float] = []
    requests: list[Request] = []
    request_data: list[bytes | None] = []
    responses = iter(
        [
            HTTPError("https://example.test/llm", 429, "busy", None, None),
            BytesIO(b"complete"),
        ]
    )

    def open_after_rate_limit(request: Request) -> BytesIO:
        requests.append(request)
        request_data.append(request.data)
        response = next(responses)
        if isinstance(response, BaseException):
            raise response
        return response

    monkeypatch.setattr(client, "urlopen", open_after_rate_limit)
    llm = client.urllib_client("https://example.test/llm", sleeps.append, [0.5])
    assert llm.complete("prompt") == "complete"
    assert sleeps == [0.5]
    assert request_data == [b"prompt", b"prompt"]
    assert requests[0] is not requests[1]

    sleeps.clear()
    network_errors = iter([URLError("temporary network failure"), BytesIO(b"complete")])

    def open_after_network_error(request: Request) -> BytesIO:
        del request
        response = next(network_errors)
        if isinstance(response, BaseException):
            raise response
        return response

    monkeypatch.setattr(client, "urlopen", open_after_network_error)
    assert client.urllib_client("https://example.test/llm", sleeps.append, [0.125]).complete(
        "prompt"
    ) == "complete"
    assert sleeps == [0.125]

    sleeps.clear()
    bad_request = HTTPError("https://example.test/llm", 400, "bad request", None, None)

    def raise_bad_request(request: Request) -> None:
        del request
        raise bad_request

    monkeypatch.setattr(client, "urlopen", raise_bad_request)
    with pytest.raises(HTTPError) as caught:
        client.urllib_client("https://example.test/llm", sleeps.append, [0.5]).complete("prompt")
    assert caught.value is bad_request
    assert sleeps == []

    server_errors = iter(
        [
            HTTPError("https://example.test/llm", 500, "server error", None, None),
            HTTPError("https://example.test/llm", 503, "unavailable", None, None),
        ]
    )

    def raise_until_exhausted(request: Request) -> None:
        del request
        raise next(server_errors)

    monkeypatch.setattr(client, "urlopen", raise_until_exhausted)
    with pytest.raises(HTTPError) as caught:
        client.urllib_client("https://example.test/llm", sleeps.append, [0.25]).complete("prompt")
    assert caught.value.code == 503
    assert sleeps == [0.25]


def test_ac2_credential_is_read_at_call_time_and_not_exposed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from agent_learning.pmbok.run_state import RunSnapshot, build_run_fields
    from agent_learning.pmbok_runtime import client

    credential_name = "OPENAI_API_KEY"
    secret = "test-secret-value"
    monkeypatch.delenv(credential_name, raising=False)
    captured_headers: dict[str, str] = {}
    failure = HTTPError("https://example.test/llm", 400, "bad request", None, None)

    def raise_without_echoing_credential(request: Request) -> None:
        captured_headers.update(request.headers)
        raise failure

    monkeypatch.setattr(client, "urlopen", raise_without_echoing_credential)
    llm = client.urllib_client(
        "https://example.test/llm",
        lambda _: None,
        [],
        credential_env_var=credential_name,
    )
    with pytest.raises(ValueError, match=credential_name):
        llm.complete("prompt")
    monkeypatch.setenv(credential_name, secret)
    with pytest.raises(HTTPError) as caught:
        llm.complete("prompt")

    assert captured_headers["Authorization"] == f"Bearer {secret}"
    assert secret not in str(caught.value)
    fields = build_run_fields(
        RunSnapshot(
            run_id="00000000-0000-4000-8000-000000000001",
            sequence_number=1,
            created_at="2026-10-31T00:00:00Z",
            phase="planning",
            processes={},
            baseline_hash=None,
            gate_episode_ids={},
            route_episode_ids={},
        ),
        "run completed",
    )
    assert secret not in repr(fields)


def test_ac3_mock_client_does_not_sleep_or_open_a_socket(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import time

    from agent_learning.pmbok_runtime import client

    calls: list[str] = []
    monkeypatch.setattr(client, "urlopen", lambda _: calls.append("urlopen"))
    monkeypatch.setattr(time, "sleep", lambda _: calls.append("sleep"))

    assert client.mock_client("hello").complete("prompt") == "hello"
    assert calls == []


def test_ac4_client_uses_only_stdlib_and_stays_out_of_pure_domain() -> None:
    assert CLIENT_SOURCE.is_file(), f"Missing PMBOK runtime client: {CLIENT_SOURCE}"
    tree = ast.parse(CLIENT_SOURCE.read_text(encoding="utf-8"))
    imported_modules: set[str] = set()
    imported_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
            imported_names.update(alias.name for alias in node.names)

    assert not any(
        module in {"tenacity", "agent_learning.storage"}
        or module.startswith(("tenacity.", "agent_learning.storage."))
        for module in imported_modules
    )
    assert "LearningStore" not in imported_names

    for path in PMBOK_PACKAGE.rglob("*.py"):
        assert path.is_file(), f"Missing PMBOK domain source: {path}"
        package_tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(package_tree):
            if isinstance(node, ast.Import):
                assert all(
                    alias.name != "agent_learning.pmbok_runtime.client"
                    and not alias.name.startswith("agent_learning.pmbok_runtime.client.")
                    for alias in node.names
                )
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                assert node.module != "agent_learning.pmbok_runtime.client"
                assert not node.module.startswith("agent_learning.pmbok_runtime.client.")
                if node.module in {"agent_learning.pmbok_runtime", "pmbok_runtime"}:
                    assert all(alias.name != "client" and alias.name != "*" for alias in node.names)
