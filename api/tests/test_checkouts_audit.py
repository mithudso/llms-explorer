"""Malformed local metadata cannot hide valid sibling research reservations."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from explorer_api import checkouts


def _write(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


@pytest.fixture(autouse=True)
def roots(tmp_path, monkeypatch):
    monkeypatch.setenv("HUB_DIR", str(tmp_path / "hub"))
    monkeypatch.setenv("LLMSX_HOME", str(tmp_path / "llmsx"))
    checkouts.clear_cache()
    yield tmp_path
    checkouts.clear_cache()


@pytest.mark.parametrize("source", ["dr", "explorer-batch", "suite"])
@pytest.mark.parametrize("malformed", [7, "private-concept-body", {"private": "body"}])
def test_bad_collection_does_not_hide_valid_sibling(source, malformed, roots, caplog):
    caplog.set_level(logging.WARNING, logger="explorer_api.checkouts")
    if source == "dr":
        base = roots / "hub/research"
        _write(base / "bad/manifest.json", {"status": "researching", "concepts": malformed})
        _write(base / "good/manifest.json", {"status": "researching", "topic": "Held concept"})
    elif source == "explorer-batch":
        base = roots / "llmsx/jobs/batches"
        _write(base / "bad/run.json", {"status": "in-progress", "concepts": malformed})
        _write(base / "good/run.json", {"status": "in-progress", "concepts": ["Held concept"]})
    else:
        _write(roots / "hub/research/.pipeline/suite/batches.json", [
            {"id": "bad", "concepts": malformed}, {"id": "good", "concepts": ["Held concept"]},
        ])
    assert checkouts.held_by("Held concept") is not None
    found, held = checkouts.snapshot()
    assert len(found) == 1 and set(held) == {"held concept"}
    assert "checkout_metadata_invalid" in caplog.text
    assert f"source={source}" in caplog.text
    assert "private-concept-body" not in caplog.text
    assert str(roots) not in caplog.text
