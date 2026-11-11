"""Fork snapshot regression using temporary storage and actual PostgreSQL."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from explorer_api import models as m, trees
from explorer_api.settings import Settings


async def test_fork_copies_the_same_snapshot_that_it_hashes(session, database_url, tmp_path,
                                                          monkeypatch):
    source = tmp_path / "public-tree.json"
    old_bytes = b'  [{"concept": "Original", "parentConcept": null, "childConcepts": []}]\n'
    source.write_bytes(old_bytes)
    replacement = json.dumps([{"concept": "PublishedLater"}]).encode()
    monkeypatch.setenv("EXPLORER_PUBLIC_TREE", str(source))
    read_bytes = Path.read_bytes

    def publish_after_read(path):
        result = read_bytes(path)
        if path == source:
            source.write_bytes(replacement)
        return result

    monkeypatch.setattr(Path, "read_bytes", publish_after_read)
    settings = Settings.load({"DATABASE_URL": database_url, "SESSION_SECRET": "s" * 32,
                              "STRIPE_SECRET_KEY": "sk_fake", "STRIPE_WEBHOOK_SECRET": "wh_fake",
                              "STORES_ROOT": str(tmp_path / "stores")})
    user = m.User(email="fork-audit@example.test")
    session.add(user)
    await session.flush()
    fork = await trees.fork(session, user, settings=settings)
    private_bytes = read_bytes(trees.resolve_path(settings, fork))
    assert private_bytes == old_bytes
    assert fork.forked_from_sha == hashlib.sha256(private_bytes).hexdigest()
    assert read_bytes(source) == replacement
