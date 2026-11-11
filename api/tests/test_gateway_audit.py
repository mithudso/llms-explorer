"""Gateway error accounting and concurrent admission against real PostgreSQL.

The remote hub is controlled; the account locks, quota reads and ledger writes
use this repository's ephemeral database fixture, with one session per caller.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from explorer_api import gateway as gw
from explorer_api import models as m

SENTINEL = "private-provider-token-and-path-must-not-be-logged"


def _text(value: str, *, error: bool = False) -> dict:
    return {"content": [{"type": "text", "text": value}], "isError": error}


async def _owner(session) -> str:
    user = m.User(email=f"gateway-audit-{uuid4().hex}@example.test", plan_id="free")
    session.add(user)
    await session.commit()
    return user.id


async def _principal(session, owner: str) -> gw.Principal:
    user = await session.get(m.User, owner)
    return gw.Principal(user=user, namespace=gw.namespace_for(user),
                        scopes=frozenset({"read", "run"}))


class ReplyHub:
    def __init__(self, reply):
        self.reply = reply

    async def call_tool(self, name, arguments, **kwargs):
        return self.reply


@pytest.mark.parametrize("reply", [
    _text(SENTINEL, error=True),
    _text(f"ERROR: {SENTINEL}"),
    _text(f"EXIT 1\n{SENTINEL}"),
    _text(f"EXIT -9\n{SENTINEL}"),
])
async def test_failed_tool_results_preserve_mcp_error_without_spending_quota(
    session, tmp_path, caplog, reply,
):
    owner = await _owner(session)
    principal = await _principal(session, owner)
    hub = ReplyHub(reply)
    gateway = gw.Gateway(SimpleNamespace(stores_root=tmp_path), hub, gw.Catalogue(hub))
    caplog.set_level(logging.WARNING, logger="explorer_api.gateway")
    result = await gateway._tools_call(session, principal, {
        "name": "hub_query_docset",
        "arguments": {"docset": principal.namespace + "notes", "question": SENTINEL,
                      "mode": "keyword"},
    })
    assert result["isError"] is True
    assert SENTINEL not in json.dumps(result)
    assert not session.in_transaction(), "A failed call must release its account lock"
    assert await session.scalar(select(func.count()).select_from(m.LedgerEntry)) == 0
    records = [record for record in caplog.records if record.name == "explorer_api.gateway"]
    assert len(records) == 1
    assert records[0].operation == "hub_query_docset"
    assert records[0].error_type == "ToolError"
    assert SENTINEL not in caplog.text


@pytest.mark.parametrize("value", [
    "EXIT 0\nnormal successful subprocess output",
    "The reference includes ERROR: as an example of a diagnostic",
    "An ordinary error is still legitimate reference text",
])
async def test_ordinary_text_results_remain_successfully_metered(session, tmp_path, value):
    owner = await _owner(session)
    principal = await _principal(session, owner)
    hub = ReplyHub(_text(value))
    gateway = gw.Gateway(SimpleNamespace(stores_root=tmp_path), hub, gw.Catalogue(hub))
    result = await gateway._tools_call(session, principal, {
        "name": "hub_query_docset",
        "arguments": {"docset": principal.namespace + "notes", "question": "where?",
                      "mode": "keyword"},
    })
    assert result == _text(value)
    assert await session.scalar(select(func.count()).select_from(m.LedgerEntry)) == 1


class ControlledIndexes:
    def __init__(self, *, first_failure: str | None = None):
        self.entries: list[dict] = []
        self.starts: list[str] = []
        self.first_started = asyncio.Event()
        self.release_first = asyncio.Event()
        self.first_failure = first_failure

    async def call_tool(self, name, arguments, **kwargs):
        if name == "hub_list_docsets":
            return _text(json.dumps(self.entries))
        assert name == "hub_index_docset"
        self.starts.append(arguments["name"])
        if len(self.starts) == 1:
            self.first_started.set()
            await self.release_first.wait()
            if self.first_failure == "tool":
                return _text(SENTINEL, error=True)
            if self.first_failure == "transport":
                raise ConnectionError(SENTINEL)
        self.entries.append({"docset": arguments["name"], "chunks": 1})
        return _text(json.dumps({"chunks": 1}))


async def _index(factory, owner, hub, catalogue, store: Path, suffix, *, ready=None):
    async with factory() as session:
        principal = await _principal(session, owner)
        if ready is not None:
            ready.set()
        gateway = gw.Gateway(SimpleNamespace(stores_root=store), hub, catalogue)
        return await gateway._tools_call(session, principal, {
            "name": "hub_index_docset",
            "arguments": {"name": principal.namespace + suffix, "mirror_path": suffix + ".md"},
        })


async def test_concurrent_index_admission_rechecks_usage_under_account_lock(
    session, engine, tmp_path,
):
    owner = await _owner(session)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    hub = ControlledIndexes()
    # Model independent gateway processes whose empty catalogue was cached
    # before either request. A row lock alone cannot repair a stale counter.
    first_catalogue, second_catalogue = gw.Catalogue(hub), gw.Catalogue(hub)
    await first_catalogue.entries()
    await second_catalogue.entries()
    first = asyncio.create_task(_index(factory, owner, hub, first_catalogue, tmp_path, "one"))
    try:
        await asyncio.wait_for(hub.first_started.wait(), 3)
        ready = asyncio.Event()
        second = asyncio.create_task(
            _index(factory, owner, hub, second_catalogue, tmp_path, "two", ready=ready)
        )
        await asyncio.wait_for(ready.wait(), 3)
    finally:
        hub.release_first.set()
    results = await asyncio.wait_for(asyncio.gather(first, second, return_exceptions=True), 5)
    assert len(hub.starts) == 1, "The free account must start only one upstream index"
    assert len(hub.entries) == 1
    assert sum(isinstance(result, gw.QuotaExceeded) for result in results) == 1
    assert sum(isinstance(result, dict) for result in results) == 1
    assert await session.scalar(select(func.count()).select_from(m.LedgerEntry)) == 1


@pytest.mark.parametrize("failure", ["tool", "transport", "cancel"])
async def test_failed_first_index_releases_account_for_waiting_request(
    session, engine, tmp_path, failure,
):
    owner = await _owner(session)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    hub = ControlledIndexes(first_failure=failure)
    first = asyncio.create_task(_index(factory, owner, hub, gw.Catalogue(hub), tmp_path, "one"))
    await asyncio.wait_for(hub.first_started.wait(), 3)
    ready = asyncio.Event()
    second = asyncio.create_task(
        _index(factory, owner, hub, gw.Catalogue(hub), tmp_path, "two", ready=ready)
    )
    try:
        await asyncio.wait_for(ready.wait(), 3)
        if failure == "cancel":
            first.cancel()
    finally:
        hub.release_first.set()
    results = await asyncio.wait_for(asyncio.gather(first, second, return_exceptions=True), 5)
    if failure == "tool":
        assert results[0]["isError"] is True
    elif failure == "transport":
        assert isinstance(results[0], gw.HubUnavailable)
    else:
        assert isinstance(results[0], asyncio.CancelledError)
    assert isinstance(results[1], dict) and not results[1]["isError"]
    assert len(hub.entries) == 1 and hub.entries[0]["docset"].endswith("__two")
    assert await session.scalar(select(func.count()).select_from(m.LedgerEntry)) == 1


async def test_another_account_can_index_while_first_account_is_waiting(
    session, engine, tmp_path,
):
    first_owner, second_owner = await _owner(session), await _owner(session)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    hub = ControlledIndexes()
    first = asyncio.create_task(
        _index(factory, first_owner, hub, gw.Catalogue(hub), tmp_path, "one")
    )
    try:
        await asyncio.wait_for(hub.first_started.wait(), 3)
        other = await asyncio.wait_for(
            _index(factory, second_owner, hub, gw.Catalogue(hub), tmp_path, "two"), 3
        )
        assert other["isError"] is False
        assert len(hub.entries) == 1, "Second account finished before the first was released"
    finally:
        hub.release_first.set()
        await asyncio.wait_for(first, 3)
    assert len(hub.entries) == 2


@pytest.mark.parametrize("operation", ["call", "list"])
async def test_upstream_failure_diagnostic_has_operation_and_class_without_provider_data(
    caplog, operation,
):
    class BrokenHub:
        async def call_tool(self, name, arguments, **kwargs):
            raise ConnectionError(SENTINEL)

        async def list_tools(self):
            raise ConnectionError(SENTINEL)

    caplog.set_level(logging.WARNING, logger="explorer_api.gateway")
    with pytest.raises(gw.HubUnavailable, match="the hub did not answer"):
        if operation == "call":
            await gw.call_hub(BrokenHub(), "hub_query_docset", {"question": SENTINEL})
        else:
            await gw.list_hub_tools(BrokenHub())
    records = [record for record in caplog.records if record.name == "explorer_api.gateway"]
    assert len(records) == 1
    assert records[0].operation == ("hub_query_docset" if operation == "call" else "tools/list")
    assert records[0].error_type == "ConnectionError"
    assert SENTINEL not in caplog.text
    assert records[0].exc_info is None
