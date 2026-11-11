"""BYOK validation must close its owned HTTP client on every result."""
import logging
from types import SimpleNamespace

import anthropic
import httpx
import pytest

from explorer_api import anthropic_keys


class FakeClient:
    def __init__(self, outcome):
        self.outcome = outcome
        self.closed = False
        self.calls = 0
        self.models = SimpleNamespace(list=self.list_models)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        self.closed = True

    async def list_models(self):
        self.calls += 1
        if self.outcome:
            raise self.outcome
        return []


@pytest.mark.parametrize("outcome", ["success", "auth", "service"])
async def test_client_closes_and_events_never_contain_key(monkeypatch, caplog, outcome):
    key = "private-key-value"
    response = httpx.Response(401, request=httpx.Request("GET", "https://provider.example.test/models"))
    error = None if outcome == "success" else (
        anthropic.AuthenticationError("private upstream body", response=response, body=None)
        if outcome == "auth" else anthropic.APIConnectionError(request=response.request)
    )
    client = FakeClient(error)
    monkeypatch.setattr(anthropic, "AsyncAnthropic", lambda **_kwargs: client)
    with caplog.at_level(logging.INFO):
        if error is None:
            await anthropic_keys.real_validator(key)
        else:
            with pytest.raises(anthropic_keys.InvalidApiKey):
                await anthropic_keys.real_validator(key)
    assert client.calls == 1
    assert client.closed
    assert "anthropic_key_validation_started" in caplog.text
    expected = (
        "anthropic_key_validation_succeeded" if error is None else "anthropic_key_validation_failed"
    )
    assert expected in caplog.text
    assert key not in caplog.text
    assert "private upstream body" not in caplog.text
