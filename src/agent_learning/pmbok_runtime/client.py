"""Standard-library HTTP and offline clients for PMBOK orchestration."""

from __future__ import annotations

import os
from collections.abc import Callable, Sequence
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class LlmClient(Protocol):
    """A synchronous prompt-completion client."""

    def complete(self, prompt: str) -> str: ...


def backoff_delays(
    attempts: int,
    base_seconds: float,
    factor: float,
    jitter: Callable[[], float],
) -> list[float]:
    """Build exponential retry delays with additive jitter in seconds."""
    return [
        base_seconds * factor**index + jitter()
        for index in range(attempts)
    ]


class _UrllibClient:
    def __init__(
        self,
        url: str,
        sleeper: Callable[[float], None],
        delays: Sequence[float],
        credential_env_var: str | None,
    ) -> None:
        self._url = url
        self._sleeper = sleeper
        self._delays = tuple(delays)
        self._credential_env_var = credential_env_var

    def complete(self, prompt: str) -> str:
        headers = {"Content-Type": "text/plain; charset=utf-8"}
        if self._credential_env_var is not None:
            credential = os.environ.get(self._credential_env_var)
            if not credential:
                raise ValueError(
                    f"Credential environment variable {self._credential_env_var!r} is not set"
                )
            headers["Authorization"] = f"Bearer {credential}"

        request = Request(
            self._url,
            data=prompt.encode("utf-8"),
            headers=headers,
            method="POST",
        )
        for attempt in range(len(self._delays) + 1):
            try:
                with urlopen(request) as response:
                    return response.read().decode("utf-8")
            except HTTPError as exc:
                if not _is_retryable_status(exc.code):
                    raise
                last_error: URLError = exc
            except URLError as exc:
                last_error = exc

            if attempt == len(self._delays):
                raise last_error
            self._sleeper(self._delays[attempt])

        raise RuntimeError("HTTP retry loop exited unexpectedly")


def _is_retryable_status(status: int) -> bool:
    return status == 429 or 500 <= status <= 599


def urllib_client(
    url: str,
    sleeper: Callable[[float], None],
    delays: Sequence[float],
    *,
    credential_env_var: str | None = None,
) -> LlmClient:
    """Create an HTTP client using a caller-supplied retry schedule."""
    return _UrllibClient(url, sleeper, delays, credential_env_var)


class _MockClient:
    def __init__(self, body: str) -> None:
        self._body = body

    def complete(self, prompt: str) -> str:
        del prompt
        return self._body


def mock_client(body: str) -> LlmClient:
    """Create an offline client that returns a canned body."""
    return _MockClient(body)
