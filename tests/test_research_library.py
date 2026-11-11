"""Keep successful wrapper ingests bound to their own immutable source version."""

import hashlib
import importlib.util
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from pathlib import Path
from threading import Barrier, BrokenBarrierError, Event
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def source_id(url):
    # The wrapper must use the upstream identity, including its alias policy.
    return "src:" + digest(url.partition("#")[0])[:16]


def fake_library(root, urls):
    metadata = {}
    for url in urls:
        sid = source_id(url)
        path = root / (sid[4:] + ".txt")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("old")
        metadata[sid] = {
            "id": sid, "url": url.partition("#")[0],
            "text_path": str(path), "sha256": digest("old"),
        }

    def write(url, body):
        entry = metadata[source_id(url)]
        Path(entry["text_path"]).write_text(body)
        entry["sha256"] = digest(body)
        return {"ok": True, "id": entry["id"], "version": body}

    library = SimpleNamespace(
        lib_dir=lambda: root,
        dr=SimpleNamespace(
            source_id=source_id,
            lib_find=lambda url: deepcopy(metadata[source_id(url)]),
        ),
    )
    return library, write


def run_wrapper(monkeypatch, library):
    wrapper = load("reviewed_research_library", ROOT / "scripts/research_library.py")
    provenance = load("reviewed_library_provenance", ROOT / "scripts/research_provenance.py")
    monkeypatch.setattr(
        wrapper, "load",
        lambda name, path: provenance if name == "library_provenance" else library,
    )
    return wrapper.main(["fake-command"])


@pytest.mark.parametrize("alias", [False, True])
def test_concurrent_ingests_preserve_each_successful_version(tmp_path, monkeypatch, alias):
    urls = ["https://example.org/source", "https://example.org/source"]
    if alias:
        urls[1] += "#another-citation"
    library, write = fake_library(tmp_path, urls)
    overlap = Barrier(2)
    first_written, second_written = Event(), Event()

    def ingest(url, *, payload):
        try:
            # In the broken wrapper both fetches enter together. A correct
            # wrapper serializes this source, so the first bounded rendezvous
            # expires and both fetches proceed serially. Real OS synchronization
            # is the behavior under test; no network or inference is involved.
            overlap.wait(timeout=0.25)
        except BrokenBarrierError:
            return write(url, payload)
        if payload == "A":
            result = write(url, payload)
            first_written.set()
            assert second_written.wait(timeout=2)
            return result
        assert first_written.wait(timeout=2)
        result = write(url, payload)
        second_written.set()
        return result

    library.ingest = ingest

    def main(argv):
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(library.ingest, url, payload=body)
                       for url, body in zip(urls, ("A", "B"), strict=True)]
            library.results = [future.result(timeout=3) for future in futures]
        return 0

    library.main = main
    assert run_wrapper(monkeypatch, library) == 0
    archived = {path.read_text() for path in (tmp_path / "provenance/snapshots").glob("*.txt")}
    assert archived == {"old", "A", "B"}
    for result in library.results:
        assert result["provenance"]["snapshot_sha256"] == digest(result["version"])


def test_different_sources_can_ingest_concurrently(tmp_path, monkeypatch):
    urls = ["https://example.org/first", "https://example.org/second"]
    library, write = fake_library(tmp_path, urls)
    overlap = Barrier(2)

    def ingest(url, *, payload):
        overlap.wait(timeout=2)
        return write(url, payload)

    library.ingest = ingest

    def main(argv):
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(library.ingest, url, payload=body)
                       for url, body in zip(urls, ("A", "B"), strict=True)]
            results = [future.result(timeout=3) for future in futures]
        assert {row["provenance"]["snapshot_sha256"] for row in results} == {
            digest("A"), digest("B"),
        }
        return 0

    library.main = main
    assert run_wrapper(monkeypatch, library) == 0


def test_ingest_failure_releases_source_guard(tmp_path, monkeypatch):
    url = "https://example.org/source"
    library, write = fake_library(tmp_path, [url])

    def ingest(url, *, payload):
        if payload == "fail":
            raise OSError("temporary provider failure")
        return write(url, payload)

    library.ingest = ingest

    def main(argv):
        with pytest.raises(OSError, match="temporary provider failure"):
            library.ingest(url, payload="fail")
        with ThreadPoolExecutor(max_workers=1) as pool:
            result = pool.submit(library.ingest, url, payload="recovered").result(timeout=2)
        assert result["provenance"]["snapshot_sha256"] == digest("recovered")
        return 0

    library.main = main
    assert run_wrapper(monkeypatch, library) == 0
