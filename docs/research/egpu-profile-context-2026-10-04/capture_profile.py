#!/opt/homebrew/bin/python3
"""Capture the pinned full coding profile with canned, loopback-only responses."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import ClassVar

VERSION = "1.0.3"
PROFILE = Path(
    "/Users/mitch/.cache/claude-egpu/experiments/qwen35-9b-admission/coding-summary-prompt-v109/egpu_coding_profile.py"
)
CLIENT = Path(
    "/Users/mitch/.cache/claude-egpu/experiments/qwen35-9b-admission/qwen35-reasoning-fixed-protocol-client-v100/claude_qwen35.py"
)
FOLLOWUP = Path(
    "/Users/mitch/.cache/claude-egpu/experiments/qwen35-27b-coding-experiment-v102/claude_27b.py"
)
CLAUDE = Path(
    "/Users/mitch/.cache/claude-egpu/experiments/egpu-pinned-client-2.1.286-v100/claude"
)
MODEL = "qwen3.6:27b-iq2-xxs"
PINNED = {
    PROFILE: "c54853fc45c73d385e627e4924b04195152073d9417a12b1533c2d0307cadd33",
    CLIENT: "9c7cc876531e6bc1554389b4ff206dc065c72c8b618063811774ceec7ce025f4",
    CLAUDE: "75e3016e9d2570767b08e43a7467d4817a4f149232c169ca295f2c95fef21433",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def put(root, name, value):
    with (root / name).open("x") as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True) + "\n")
    (root / name).chmod(0o600)


class Capture(BaseHTTPRequestHandler):
    requests: ClassVar[list] = []
    unexpected: ClassVar[list] = []

    def log_message(self, *_args):
        pass

    def do_GET(self):
        if self.path == "/guard-positive":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"GUARD_OK")
        else:
            self.unexpected.append({"method": "GET", "path": self.path})
            self.send_response(403)
            self.end_headers()

    def do_POST(self):
        size = int(self.headers.get("Content-Length", "0"))
        if not 0 < size <= 2_000_000:
            self.send_response(413)
            self.end_headers()
            return
        body = json.loads(self.rfile.read(size))
        if self.path.split("?", 1)[0] != "/v1/messages":
            self.unexpected.append({"method": "POST", "path": self.path})
            self.send_response(403)
            self.end_headers()
            return
        self.requests.append(body)
        message = {
            "id": "msg_capture_only",
            "type": "message",
            "role": "assistant",
            "model": body["model"],
            "content": [],
            "stop_reason": None,
            "stop_sequence": None,
            "usage": {"input_tokens": 0, "output_tokens": 0},
        }
        self.send_response(200)
        if body.get("stream"):
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            events = [
                ("message_start", {"type": "message_start", "message": message}),
                (
                    "content_block_start",
                    {
                        "type": "content_block_start",
                        "index": 0,
                        "content_block": {"type": "text", "text": ""},
                    },
                ),
                (
                    "content_block_delta",
                    {
                        "type": "content_block_delta",
                        "index": 0,
                        "delta": {"type": "text_delta", "text": "MOCK_CAPTURE_ONLY"},
                    },
                ),
                ("content_block_stop", {"type": "content_block_stop", "index": 0}),
                (
                    "message_delta",
                    {
                        "type": "message_delta",
                        "delta": {"stop_reason": "end_turn", "stop_sequence": None},
                        "usage": {"output_tokens": 0},
                    },
                ),
                ("message_stop", {"type": "message_stop"}),
            ]
            for event, value in events:
                self.wfile.write(
                    (
                        "event: " + event + "\ndata: " + json.dumps(value) + "\n\n"
                    ).encode()
                )
                self.wfile.flush()
        else:
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            message.update(
                content=[{"type": "text", "text": "MOCK_CAPTURE_ONLY"}],
                stop_reason="end_turn",
            )
            self.wfile.write(json.dumps(message).encode())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cache-seed-from", type=Path)
    parser.add_argument(
        "--client-version", choices=("2.1.286", "2.1.289"), default="2.1.286"
    )
    args = parser.parse_args()
    os.umask(0o077)
    root = args.output.resolve()
    root.mkdir(mode=0o700, parents=True, exist_ok=False)
    (root / "source.py").write_bytes(Path(__file__).read_bytes())
    client_path = CLAUDE
    pins = dict(PINNED)
    if args.client_version == "2.1.289":
        pins.pop(CLAUDE)
        client_path = Path("/Users/mitch/.local/share/claude/versions/2.1.289")
        pins[client_path] = (
            "03d66745e3bb69ec727d66023696f3820bc0a00a8a5ba725eb6706d0c67cbe69"
        )
    for path, digest in pins.items():
        if path.is_symlink() or sha(path) != digest:
            raise ValueError("Pinned input changed: " + str(path))
    profile = load(PROFILE, "pinned_full_coding_profile")
    client = load(CLIENT, "pinned_pure_client_preparer")
    followup = load(FOLLOWUP, "pinned_summary_instruction")
    fixture = {"directory": root / "project"}
    fixture["directory"].mkdir(mode=0o700)
    prompt = profile.coding_prompt(fixture)
    config = root / "client-config"
    config.mkdir(mode=0o700)
    cache_seed = None
    if args.cache_seed_from:
        original = json.loads(args.cache_seed_from.read_text())
        fields = (
            "cachedGrowthBookFeatures",
            "cachedGrowthBookFeaturesAt",
            "cachedExperimentFeatures",
            "cachedExperimentData",
        )
        selected = {key: original[key] for key in fields if key in original}
        put(config, ".claude.json", selected)
        cache_seed = {
            "source": str(args.cache_seed_from.resolve()),
            "copied_fields": list(selected),
            "selected_cache_sha256": sha(config / ".claude.json"),
            "credentials_copied": False,
            "values_in_public_receipt": False,
        }
    mock = ThreadingHTTPServer(("127.0.0.1", 0), Capture)
    deny = ThreadingHTTPServer(("127.0.0.1", 0), Capture)
    for server in (mock, deny):
        threading.Thread(target=server.serve_forever, daemon=True).start()
    port = mock.server_address[1]
    sandbox = f'(version 1) (allow default) (deny network*) (allow network-outbound (remote ip "localhost:{port}"))'
    guard_results = []
    for server, allowed in [(mock, True), (deny, False)]:
        url = f"http://127.0.0.1:{server.server_address[1]}/guard-positive"
        test = subprocess.run(
            [
                "/usr/bin/sandbox-exec",
                "-p",
                sandbox,
                "/usr/bin/curl",
                "--noproxy",
                "*",
                "--max-time",
                "2",
                url,
            ],
            capture_output=True,
            text=True,
            env={"PATH": "/usr/bin:/bin"},
            timeout=5,
            check=False,
        )
        guard_results.append(
            {
                "allowed": allowed,
                "exit_code": test.returncode,
                "expected_body": test.stdout == "GUARD_OK",
            }
        )
        if (test.returncode == 0) != allowed:
            raise ValueError("Loopback-only network guard failed")
    client.ALIAS = MODEL
    client.CLAUDE = client_path
    client.CLIENT_CAPS = {
        **client.CLIENT_CAPS,
        "CLAUDE_CODE_MODEL_CAPABILITIES": MODEL
        + "=-adaptive_thinking,-mid_conv_system",
    }
    base_env = {
        "HOME": "/Users/mitch",
        "USER": "mitch",
        "LOGNAME": "mitch",
        "PATH": "/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin",
        "LANG": "en_US.UTF-8",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    invocation = client.prepare_invocation(
        [
            MODEL,
            *profile.coding_arguments(bounded_context=True),
            "--max-turns",
            "24",
            "--output-format",
            "stream-json",
            "--verbose",
            "-p",
            prompt,
        ],
        base_env,
    )
    argv, env = invocation["argv"], invocation["env"]
    system_index = argv.index("--system-prompt") + 1
    argv[system_index] += "\n\n" + followup.SUMMARY_RULE
    env.update(
        CLAUDE_CONFIG_DIR=str(config),
        ANTHROPIC_BASE_URL=f"http://127.0.0.1:{port}",
        ANTHROPIC_API_KEY="MOCK_ONLY_NO_PROVIDER_CREDENTIAL",
        ANTHROPIC_AUTH_TOKEN="MOCK_ONLY_NO_PROVIDER_CREDENTIAL",
        DISABLE_AUTOUPDATER="1",
    )
    command = ["/usr/bin/sandbox-exec", "-p", sandbox, *argv]
    put(
        root,
        "PROMPTS.json",
        {
            "version": VERSION,
            "goal": "Measure original full23 coding payload; no model qualification",
            "system": argv[system_index],
            "user": prompt,
        },
    )
    put(
        root,
        "COMMAND.json",
        {
            "argv": command,
            "environment": env,
            "cwd": str(fixture["directory"]),
            "mock_only": True,
            "isolated_client_config": True,
        },
    )
    try:
        start = time.monotonic()
        process = subprocess.run(
            command,
            cwd=fixture["directory"],
            env=env,
            capture_output=True,
            text=True,
            timeout=45,
            check=False,
        )
        elapsed = time.monotonic() - start
    finally:
        for server in (mock, deny):
            server.shutdown()
            server.server_close()
    (root / "stdout.jsonl").write_text(process.stdout)
    (root / "stderr.log").write_text(process.stderr)
    put(root, "REQUESTS.json", Capture.requests)
    names = [
        [tool["name"] for tool in request.get("tools", [])]
        for request in Capture.requests
    ]
    expected_wire_names = {
        "Agent" if name == "Task" else name for name in profile.FULL_CODING_TOOLS
    }
    passed = (
        process.returncode == 0
        and len(names) == 1
        and set(names[0]) == expected_wire_names
        and not Capture.unexpected
    )
    sources = {
        str(path): sha(path) for path in [*pins, FOLLOWUP, Path(__file__).resolve()]
    }
    receipt = {
        "version": VERSION,
        "scope": "actual pinned client capture; canned response only",
        "passed": passed,
        "client_version": args.client_version,
        "model_alias": MODEL,
        "client_exit_code": process.returncode,
        "elapsed_seconds": elapsed,
        "api_request_count": len(names),
        "api_tool_names": names,
        "required_tool_names": list(profile.FULL_CODING_TOOLS),
        "sdk_builtin_alias": {"Task": "Agent"},
        "schema_count": len(names[0]) if names else 0,
        "request_bytes": [
            len(json.dumps(row, ensure_ascii=False).encode())
            for row in Capture.requests
        ],
        "loopback_guard": guard_results,
        "unexpected_http": Capture.unexpected,
        "sources": sources,
        "cache_seed": cache_seed,
        "real_model_calls": 0,
        "gpu_actions": 0,
        "provider_calls": 0,
        "qualification": False,
        "profile_delta": "Candidate alias; selected pinned client version; mock endpoint/credentials; isolated config with optional real cache-only seed; empty fixture before any tool work. Original full23 request and reviewed summary instruction retained. Fidelity is accepted only if all actual API schemas are present.",
    }
    put(root, "RESULT.json", receipt)
    print(json.dumps(receipt, indent=2))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
