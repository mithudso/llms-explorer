"""prune_dist: unused onnxruntime-web binaries go, and nothing over the Pages cap ships."""
import sys
from pathlib import Path

import pytest

SITE = Path(__file__).resolve().parents[1]
DIST = SITE / "dist"
sys.path.insert(0, str(SITE / "tools"))
import prune_dist


def test_prune_removes_ort_wasm_and_keeps_everything_else(tmp_path):
    astro = tmp_path / "_astro"
    astro.mkdir()
    (astro / "ort-wasm-simd-threaded.asyncify.CxOG5pUO.wasm").write_bytes(b"\0asm")
    (astro / "ort-wasm-simd-threaded.jsep.abc.wasm").write_bytes(b"\0asm")
    keep = astro / "SearchBox.abc.js"
    keep.write_text("export {}")
    removed = prune_dist.prune(tmp_path)
    assert sorted(p.name for p in removed) == [
        "ort-wasm-simd-threaded.asyncify.CxOG5pUO.wasm",
        "ort-wasm-simd-threaded.jsep.abc.wasm",
    ]
    assert keep.is_file()
    assert not list(astro.glob("*.wasm"))


def test_oversized_reports_files_over_the_pages_cap(tmp_path):
    big = tmp_path / "big.bin"
    with big.open("wb") as fh:
        fh.truncate(prune_dist.PAGES_MAX_BYTES + 1)
    (tmp_path / "small.txt").write_text("ok")
    assert [p.name for p, _ in prune_dist.oversized(tmp_path)] == ["big.bin"]


def test_built_site_fits_cloudflare_pages():
    """After `npm run build`, no deployable file may exceed 25 MiB, or the Pages
    upload fails after an otherwise green build."""
    if not DIST.is_dir():
        pytest.skip("site/dist not built")
    assert prune_dist.oversized(DIST) == []
