#!/usr/bin/env python3
"""prune_dist — drop unused bundler output and enforce the Pages file-size cap.

Cloudflare Pages rejects any deployment containing a file over 25 MiB. Vite
copies onnxruntime-web's WASM binary (ort-wasm-simd-threaded*.wasm, ~26 MiB
for the asyncify build) into dist/_astro/ because onnxruntime-web references
it with `new URL(..., import.meta.url)` as a fallback. That fallback is never
taken here: @huggingface/transformers sets `env.backends.onnx.wasm.wasmPaths`
to the jsDelivr copy of the same onnxruntime-web version on import
(src/backends/onnx.js), so SearchBox.astro loads the runtime from the CDN and
the bundled copy is dead weight that only blocks the upload.

This step deletes those binaries, then fails the build if any file in dist/
is still over the cap, so a future oversized asset fails here with its name
instead of at the Pages upload step.

Usage: prune_dist.py [--dist dist]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]  # site/
PAGES_MAX_BYTES = 25 * 1024 * 1024
UNUSED_GLOBS = ("_astro/ort-wasm-simd-threaded*.wasm",)


def prune(dist: Path) -> list[Path]:
    removed = []
    for pattern in UNUSED_GLOBS:
        for path in sorted(dist.glob(pattern)):
            path.unlink()
            removed.append(path)
    return removed


def oversized(dist: Path) -> list[tuple[Path, int]]:
    return [(p, p.stat().st_size) for p in sorted(dist.rglob("*"))
            if p.is_file() and p.stat().st_size > PAGES_MAX_BYTES]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dist", type=Path, default=HERE / "dist")
    args = ap.parse_args()
    removed = prune(args.dist)
    print(f"prune_dist: removed {len(removed)} unused onnxruntime-web binary(ies)")
    big = oversized(args.dist)
    for path, size in big:
        print(f"prune_dist: {path.relative_to(args.dist)} is {size / 2**20:.1f} MiB, "
              f"over the 25 MiB Cloudflare Pages limit", file=sys.stderr)
    return 1 if big else 0


if __name__ == "__main__":
    sys.exit(main())
