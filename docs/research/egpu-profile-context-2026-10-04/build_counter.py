#!/opt/homebrew/bin/python3
"""Link only already-built CPU archives; never rebuild the pinned GPU candidate."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.output.resolve()
    root.mkdir(mode=0o700, parents=True, exist_ok=False)
    source = Path(__file__).resolve().with_name("count_payload.cpp")
    tree = Path("/Users/mitch/dev/macuda/llama.cpp")
    build = tree / "build-null"
    cache = (build / "CMakeCache.txt").read_text()
    for flag in (
        "GGML_CUDA",
        "GGML_METAL",
        "GGML_RPC",
        "GGML_VULKAN",
        "GGML_SYCL",
        "GGML_OPENCL",
        "GGML_HIP",
        "GGML_WEBGPU",
        "GGML_BACKEND_DL",
    ):
        if flag + ":BOOL=OFF" not in cache:
            raise ValueError("CPU build flag is not off: " + flag)
    libraries = [
        build / x
        for x in (
            "tools/server/libserver-context.a",
            "common/libllama-common.a",
            "common/libllama-common-base.a",
            "tools/mtmd/libmtmd.a",
            "src/libllama.a",
            "ggml/src/libggml.a",
            "ggml/src/libggml-cpu.a",
            "ggml/src/libggml-base.a",
            "vendor/hash/libvendor-hash.a",
            "vendor/cpp-httplib/libcpp-httplib.a",
        )
    ]
    headers = [
        tree / x
        for x in (
            "include",
            "ggml/include",
            "common",
            "vendor",
            "tools/server",
            "tools/mtmd",
            "vendor/cpp-httplib",
        )
    ]
    binary = root / "count-payload"
    command = [
        "/usr/bin/c++",
        "-std=c++17",
        "-O2",
        "-arch",
        "arm64",
        *["-I" + str(p) for p in headers],
        str(source),
        *map(str, libraries),
        "-lm",
        "-framework",
        "Accelerate",
        "/opt/homebrew/lib/libssl.dylib",
        "/opt/homebrew/lib/libcrypto.dylib",
        "-framework",
        "CoreFoundation",
        "-framework",
        "Security",
        "-o",
        str(binary),
    ]
    inputs = [source, build / "CMakeCache.txt", *libraries]
    pins = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    result = subprocess.run(
        command, capture_output=True, text=True, timeout=60, check=False
    )
    (root / "build.log").write_text(result.stdout + result.stderr)
    after = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    if after != pins:
        raise ValueError("CPU source archive changed during link")
    receipt = {
        "version": "1.0.0",
        "command": command,
        "exit_code": result.returncode,
        "input_pins": pins,
        "sources_unchanged": True,
        "candidate_binary_rebuilt": False,
        "gpu_actions": 0,
    }
    if result.returncode == 0:
        binary.chmod(0o700)
        deps = subprocess.run(
            ["/usr/bin/otool", "-L", str(binary)],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        if any(
            term in deps for term in ("Metal.framework", "CUDA", "tinynv", "TinyGPU")
        ):
            raise ValueError("Unexpected GPU dependency")
        receipt.update(
            binary_path=str(binary),
            binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
            dependencies=deps,
        )
    (root / "BUILD.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
