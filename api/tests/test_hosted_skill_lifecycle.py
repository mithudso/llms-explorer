"""Owned model transports close even when a showcase pass fails or is cancelled."""
import asyncio
from types import SimpleNamespace

import anthropic
import pytest

from explorer_api.routes.skills import AnthropicClient, LlmUnavailable


@pytest.mark.parametrize("outcome", ["success", "error", "empty", "cancel"])
async def test_owned_provider_transport_closes(monkeypatch, outcome):
    clients = []

    class Provider:
        def __init__(self, **_kwargs):
            self.closed = False
            self.messages = SimpleNamespace(create=self.create)
            clients.append(self)

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            self.closed = True

        async def create(self, **_kwargs):
            if outcome == "error":
                raise RuntimeError("upstream failed")
            if outcome == "cancel":
                raise asyncio.CancelledError
            return SimpleNamespace(
                content=[] if outcome == "empty" else [SimpleNamespace(type="text", text="ok")],
                usage=SimpleNamespace(input_tokens=1, output_tokens=2),
            )

    monkeypatch.setattr(anthropic, "AsyncAnthropic", Provider)
    client = AnthropicClient("fake-key")
    if outcome == "success":
        for _ in range(2):
            result = await client.complete(system="s", prompt="p", max_tokens=10)
            assert result.text == "ok"
    else:
        kind = {"error": RuntimeError, "empty": LlmUnavailable,
                "cancel": asyncio.CancelledError}[outcome]
        with pytest.raises(kind):
            await client.complete(system="s", prompt="p", max_tokens=10)
    assert all(provider.closed for provider in clients)
    if outcome == "success":
        assert len(clients) == 2


async def test_showcase_timeout_bounds_the_whole_call_and_closes_transport(monkeypatch):
    clients = []

    class Provider:
        def __init__(self, **_kwargs):
            self.closed = False
            self.messages = SimpleNamespace(create=self.create)
            clients.append(self)

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            self.closed = True

        async def create(self, **_kwargs):
            await asyncio.Event().wait()

    monkeypatch.setattr(anthropic, "AsyncAnthropic", Provider)
    client = AnthropicClient("fake-key", timeout=0.01)
    task = asyncio.create_task(client.complete(system="s", prompt="p", max_tokens=1))
    await asyncio.sleep(0.05)
    if not task.done():
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        pytest.fail("showcase wall-clock timeout did not stop the provider call")
    with pytest.raises(TimeoutError):
        await task
    assert len(clients) == 1 and clients[0].closed
