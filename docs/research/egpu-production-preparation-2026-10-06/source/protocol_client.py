#!/opt/homebrew/bin/python3
"""Private exact9B services-then-exec client. Physical qualification remains pending."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

VERSION = "1.1.4-reasoning1024-fixed-protocol-private"
DELTA = "Pin exact Qwen adaptive and mid-conversation capability disables; preserve strict native thinking1024 and all coding/research gates."
ROOT = Path(
    "/Users/mitch/dev/worktrees/skills-egpu-full-qualification/rtx5080-egpu-harness"
)
CANDIDATE = Path(
    "/Users/mitch/.cache/claude-egpu/experiments/qwen35-9b-admission/qwen35-reasoning-fixed-protocol-client-v100/claude_qwen35.py"
)
CLAUDE = Path("/Users/mitch/.local/share/claude/versions/2.1.286")
PYTHON = Path("/opt/homebrew/bin/python3")
RELAY_PYTHON = Path("/opt/homebrew/opt/python@3.14/bin/python3.14")
RESEARCH_SOURCE = Path("/Users/mitch/dev/llms-explorer/llmsx")
CONTROLLER = ROOT / "scripts/macuda_service.py"
ADAPTER = Path(
    "/Users/mitch/.cache/claude-egpu/experiments/qwen35-9b-admission/qwen35-reasoning-fixed-protocol-client-v100/egpu_research_agent.py"
)
TYPED_SOURCE_PINS = {
    "/Users/mitch/.cache/claude-egpu/experiments/qwen35-9b-admission/qwen35-reasoning-fixed-protocol-client-v100/egpu_research_agent.py": "54a324cda7e61d39239a42e4afdaa767090cd087930b5224b54616a18cd111a4",
    "/Users/mitch/.cache/claude-egpu/experiments/qwen35-9b-admission/qwen35-reasoning-fixed-protocol-client-v100/egpu_retrieval_proxy.py": "c48e347b533d3630fac72db3376515a93138046054ce1adb3e567ccbfa13c33e",
    "/Users/mitch/.cache/claude-egpu/experiments/qwen35-9b-admission/qwen35-reasoning-fixed-protocol-client-v100/origin-policy.json": "087b9bee04b0c7a0a2022a1a78c5479a753f421f055bb5459634a22ab78e4360",
    "/Users/mitch/.cache/claude-egpu/experiments/qwen35-9b-admission/typed-publication-feedback-preparation-v100/typed_publication.py": "366812406720104f7316f6049de50747b4c2523dc2ca246fcc184e9af73310a3",
    "/Users/mitch/.cache/claude-egpu/experiments/qwen35-9b-admission/typed-publication-feedback-preparation-v100/typed_retrieval_proxy.py": "56cf16a972b1006d758e54e92978a5d76f0af2dbde93b40c704f977a482d0739",
}
TYPED_RELAY = ADAPTER.with_name("egpu_retrieval_proxy.py")
ALIAS = "qwen3.5:9b-q4-k-m"
PROFILE = "qwen35-9b-reasoning-1024"
SOURCE_PINS = {
    "egpu_service.py": "cb983a302407d7da108bd5a8cc411408d748441bfcea94f2ab1f123256457db4",
    "egpu_gateway_callback.py": "4eb03869305638b67d4ee9d77ed132506a4ad66fc68bdf0a335c2298c5d2c93c",
    "macuda_service.py": "2973d8a3080c5830a2196cfc67102f8c1f62bf292f64f8a4b555afcc73d01b1a",
    "macuda_qwen35.py": "f9317b63ab58e20f4f88ace955028cf782ce5bb2471063e5f5862d46bb4e9a9c",
    "macuda_residency.py": "0952905dae90b241d55ef7c6cc51252ccf6665733bbc75ed89d93e8ae294c56d",
    "egpu_research_agent.py": "4caa8e1c2d8d401f09d63c4430776cc0e1a8041eed84e60ed1ca2ea417a7ffea",
    "egpu_retrieval_proxy.py": "4b572616edf1df2cced6d24712f789c9a64487c4264a7da35e3ad1c8099d691e",
    "egpu_coding_profile.py": "c54853fc45c73d385e627e4924b04195152073d9417a12b1533c2d0307cadd33",
}
CLAUDE_SHA256 = "75e3016e9d2570767b08e43a7467d4817a4f149232c169ca295f2c95fef21433"
CLIENT_CAPS = {
    "CLAUDE_CODE_MAX_CONTEXT_TOKENS": "32768",
    "CLAUDE_CODE_MAX_OUTPUT_TOKENS": "4096",
    "CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS": "3000",
    "MAX_MCP_OUTPUT_TOKENS": "3000",
    "BASH_MAX_OUTPUT_LENGTH": "8000",
    "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1",
    "CLAUDE_CODE_DISABLE_1M_CONTEXT": "1",
    "MAX_THINKING_TOKENS": "1024",
    "CLAUDE_CODE_MODEL_CAPABILITIES": "qwen3.5:9b-q4-k-m=-adaptive_thinking,-mid_conv_system",
    "CLAUDE_CODE_FORCE_MID_CONVERSATION_SYSTEM": "",
    "CLAUDE_CODE_GB_DISK_CACHE_WHEN_TELEMETRY_OFF": "1",
}
ROUTE_PINS = {
    "EGPU_HARNESS_DIR": str(ROOT),
    "EGPU_MAX_CONTEXT": "32768",
    "EGPU_GENERATION_PROFILE": PROFILE,
    "EGPU_TOOL_DESCRIPTION_PROFILE": "compact-v1",
    "EGPU_RUNTIME": "macuda",
    "TINY_PORT": "8000",
    "LITELLM_PORT": "14010",
    "EGPU_TINYGRAD_API_BASE": "http://127.0.0.1:8000/v1",
    "EGPU_RESEARCH_MODEL": ALIAS,
    "EGPU_RESEARCH_GATEWAY": "http://127.0.0.1:14010",
    "DR_CLAUDE_BIN": str(ADAPTER),
    "EGPU_CLAUDE_BIN": str(CANDIDATE),
}
FALSE_VALUES = {"", "0", "false", "no", "off"}
DISABLES = {
    "DISABLE_AUTO_COMPACT",
    "DISABLE_COMPACT",
    "DISABLE_UNKNOWN_MODEL_WINDOW_ENFORCEMENT",
    "CLAUDE_CODE_DISABLE_UNKNOWN_MODEL_WINDOW_ENFORCEMENT",
    "CLAUDE_CODE_USE_BEDROCK",
    "CLAUDE_CODE_USE_VERTEX",
    "CLAUDE_CODE_USE_FOUNDRY",
    "CLAUDE_CODE_SIMPLE",
    "CLAUDE_CODE_SAFE_MODE",
}
METADATA_OVERRIDES = {
    "CLAUDE_CODE_MODEL_CATALOG_URL",
    "CLAUDE_CODE_CLIENT_DATA_URL",
}
TRUSTED_SETTINGS = {
    "disableAllHooks": True,
    "autoCompactEnabled": True,
    "bashOutputMaxChars": 8000,
}
FORBIDDEN_FLAGS = {
    "--bare",
    "--fallback-model",
    "--plugin-dir",
    "--agent",
    "--agents",
    "--append-system-prompt",
    "--system-prompt-file",
    "--append-system-prompt-file",
    "--resume",
    "--continue",
    "--fork-session",
    "--dangerously-skip-permissions",
    "--allow-dangerously-skip-permissions",
    "--permission-prompt-tool",
}
SINGLE_FLAGS = {
    "--model",
    "--settings",
    "--setting-sources",
    "--mcp-config",
    "--system-prompt",
    "--output-format",
    "--max-turns",
    "--add-dir",
    "--permission-mode",
    "--effort",
    "-p",
    "--print",
}
MULTI_FLAGS = {
    "--tools",
    "--allowedTools",
    "--disallowedTools",
    "--allowed-tools",
    "--disallowed-tools",
}
BOOLEAN_FLAGS = {
    "--safe-mode",
    "--strict-mcp-config",
    "--no-session-persistence",
    "--disable-slash-commands",
    "--exclude-dynamic-system-prompt-sections",
    "--verbose",
    "--include-partial-messages",
}


def option_values(args: list[str]) -> list[tuple[str, int, str | None, bool]]:
    """Walk CLI options while treating prompt/system text as opaque data."""
    result = []
    index = 0
    while index < len(args):
        flag, separator, value = args[index].partition("=")
        if flag in FORBIDDEN_FLAGS:
            raise ValueError("A caller flag conflicts with the isolated route.")
        if flag in SINGLE_FLAGS or flag in MULTI_FLAGS:
            position = index
            if not separator:
                index += 1
                if index >= len(args):
                    raise ValueError(f"Missing {flag} value.")
                value = args[index]
            result.append((flag, position, value, bool(separator)))
            if flag in MULTI_FLAGS and not separator:
                while index + 1 < len(args) and not args[index + 1].startswith("-"):
                    index += 1
        elif flag in BOOLEAN_FLAGS and not separator:
            result.append((flag, index, None, False))
        else:
            raise ValueError("Unsupported argument in this bounded experiment.")
        index += 1
    return result


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as source:
        while data := source.read(1024 * 1024):
            result.update(data)
    return result.hexdigest()


def verify_source_pins() -> None:
    if len(TYPED_SOURCE_PINS) != 5:
        raise ValueError("Typed source review is not sealed")
    for value, expected in TYPED_SOURCE_PINS.items():
        path = Path(value)
        if path.is_symlink() or not path.is_file() or digest(path) != expected:
            raise ValueError("Typed private source pin differs")
    for name, expected in SOURCE_PINS.items():
        path = ROOT / "scripts" / name
        if path.is_symlink() or not path.is_file() or digest(path) != expected:
            raise ValueError(f"Reviewed source pin differs: {path}")
    if CLAUDE.is_symlink() or not CLAUDE.is_file() or digest(CLAUDE) != CLAUDE_SHA256:
        raise ValueError("The reviewed installed Claude executable differs.")


def object_without_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate settings/MCP object key.")
        result[key] = value
    return result


def parse_object(value: str) -> dict:
    result = json.loads(value, object_pairs_hook=object_without_duplicates)
    if not isinstance(result, dict):
        raise TypeError("An inline JSON object is required.")
    return result


def one_value(args: list[str], name: str) -> tuple[int, str, bool]:
    found = [
        (index, value, inline)
        for flag, index, value, inline in option_values(args)
        if flag == name
    ]
    if len(found) != 1:
        raise ValueError(f"Supply exactly one {name}.")
    return found[0]


def load_coding_profile():
    path = ROOT / "scripts/egpu_coding_profile.py"
    if digest(path) != SOURCE_PINS[path.name]:
        raise ValueError("The reviewed coding profile changed before import.")
    spec = importlib.util.spec_from_file_location("reviewed_9b_coding_profile", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prepare_invocation(args: list[str], environ: dict[str, str]) -> dict:
    """Validate completely before services; never remove a caller settings option."""
    args = list(args)
    if args and not args[0].startswith("-"):
        if args.pop(0) != ALIAS:
            raise ValueError("The experimental entrypoint requires its exact 9B alias.")
        if any(flag == "--model" for flag, *_ in option_values(args)):
            raise ValueError("Do not supply a second model option.")
    else:
        index, model, inline = one_value(args, "--model")
        if model != ALIAS:
            raise ValueError("The experimental entrypoint requires its exact 9B alias.")
        del args[index : index + (1 if inline else 2)]
    flags = {flag for flag, *_ in option_values(args)}
    if (
        one_value(args, "--setting-sources")[1] != ""
        or "--strict-mcp-config" not in flags
    ):
        raise ValueError(
            "The entrypoint requires empty settings sources and strict MCP."
        )
    settings_index, settings_text, inline = one_value(args, "--settings")
    settings = parse_object(settings_text)
    if not set(settings).issubset(TRUSTED_SETTINGS):
        raise ValueError(
            "Only the reviewed client settings are supported by this experiment."
        )
    for name, expected in TRUSTED_SETTINGS.items():
        if name in settings and (
            type(settings[name]) is not type(expected) or settings[name] != expected
        ):
            raise ValueError(f"Caller settings conflict with {name}.")
    if any(
        name in settings
        for name in (
            "env",
            "hooks",
            "model",
            "modelOverrides",
            "disable_unknown_model_window_enforcement",
        )
    ):
        raise ValueError(
            "Caller settings contain an unqualified routing or hook override."
        )
    bounded = {**settings, **TRUSTED_SETTINGS}
    if settings != bounded:
        replacement = json.dumps(bounded, separators=(",", ":"))
        args[settings_index if inline else settings_index + 1] = (
            "--settings=" + replacement if inline else replacement
        )
    _, tools, _ = one_value(args, "--tools")
    profile = load_coding_profile()
    mode = "coding" if tools == ",".join(profile.FULL_CODING_TOOLS) else "research"
    _, mcp_value, _ = one_value(args, "--mcp-config")
    if mode == "coding":
        if "--safe-mode" not in flags or parse_object(mcp_value) != {"mcpServers": {}}:
            raise ValueError(
                "Coding requires safe-mode and the exact empty MCP profile."
            )
        expected = profile.coding_arguments(bounded_context=True)
        if args[: len(expected)] != expected:
            raise ValueError(
                "Coding must retain the exact full23 maintained profile prefix."
            )
    else:
        if (
            tools not in {"Bash,Read,Write,Edit", "Read,Write", "Read"}
            or "--safe-mode" in flags
        ):
            raise ValueError("Research must retain the canonical adapter tool profile.")
        if not {
            "--disable-slash-commands",
            "--exclude-dynamic-system-prompt-sections",
        }.issubset(flags):
            raise ValueError("Research requires the canonical bounded adapter flags.")
        mcp_path = Path(mcp_value)
        if not mcp_path.is_absolute() or not mcp_path.is_file():
            raise ValueError(
                "Research requires its generated absolute MCP config path."
            )
        mcp = parse_object(mcp_path.read_text())
        servers = mcp.get("mcpServers")
        if not isinstance(servers, dict) or set(servers) != {"firecrawl"}:
            raise ValueError("Research requires only the canonical Firecrawl relay.")
        definition = servers["firecrawl"]
        if (
            not isinstance(definition, dict)
            or definition.get("command") != str(RELAY_PYTHON)
            or not isinstance(definition.get("args"), list)
            or not all(isinstance(value, str) for value in definition["args"])
            or definition["args"][:1] != [str(TYPED_RELAY)]
            or not isinstance(definition.get("env"), dict)
            or definition["env"].get("PYTHONPATH") != str(RESEARCH_SOURCE)
            or environ.get("EGPU_LLMSX_SOURCE") != str(RESEARCH_SOURCE)
            or environ.get("PYTHONPATH") != str(RESEARCH_SOURCE)
            or definition["env"].get("PYTHONSAFEPATH") != "1"
            or definition["env"].get("PYTHONDONTWRITEBYTECODE") != "1"
        ):
            raise ValueError("Research requires the maintained source-reading relay.")
    env = dict(environ)
    if (
        mode == "coding"
        and env.get("CLAUDE_CODE_DISABLE_BACKGROUND_TASKS", "0").strip().lower()
        not in FALSE_VALUES
    ):
        raise ValueError("Coding requires the full background argument schemas.")
    for name, expected in {**ROUTE_PINS, **CLIENT_CAPS}.items():
        if name in env and env[name] != expected:
            raise ValueError(f"{name} conflicts with the reviewed experimental route.")
        env[name] = expected
    for name in DISABLES:
        if env.get(name, "").strip().lower() not in FALSE_VALUES:
            raise ValueError(f"{name} conflicts with the bounded route.")
        env.pop(name, None)
    for name in METADATA_OVERRIDES:
        if env.get(name):
            raise ValueError(f"{name} cannot inject model metadata.")
        env.pop(name, None)
    if env.get("CLAUDE_CODE_MODEL_CATALOG", "0").strip().lower() not in FALSE_VALUES:
        raise ValueError("The model catalog must remain disabled.")
    key = env.get("EGPU_LITELLM_KEY", "sk-1234")
    if not key or any(char in key for char in "\r\n\x00"):
        raise ValueError("A valid local gateway credential is required.")
    env.update(
        ANTHROPIC_BASE_URL="http://127.0.0.1:14010",
        ANTHROPIC_AUTH_TOKEN=key,
        ANTHROPIC_API_KEY=key,
        ANTHROPIC_MODEL=ALIAS,
        ANTHROPIC_DEFAULT_SONNET_MODEL=ALIAS,
        ANTHROPIC_DEFAULT_OPUS_MODEL=ALIAS,
        ANTHROPIC_DEFAULT_HAIKU_MODEL=ALIAS,
        ANTHROPIC_SMALL_FAST_MODEL=ALIAS,
        CLAUDE_CODE_SUBAGENT_MODEL=ALIAS,
        CLAUDE_CODE_MODEL_CATALOG="0",
        CLAUDE_CODE_DISABLE_BACKGROUND_TASKS="0" if mode == "coding" else "1",
        DISABLE_ERROR_REPORTING="1",
        DISABLE_TELEMETRY="1",
        DISABLE_NONESSENTIAL_TRAFFIC="1",
        CLAUDE_CODE_AUTO_MODE_SERVER="0",
    )
    for name in (
        "ANTHROPIC_CUSTOM_HEADERS",
        "CLAUDECODE",
        "CLAUDE_CODE_AUTO_COMPACT_WINDOW",
        "PYTHONHOME",
        "PYTHONSTARTUP",
        "PYTHONINSPECT",
    ):
        env.pop(name, None)
    services_env = {
        **env,
        "PYTHONPATH": str(ROOT / "scripts"),
        "PYTHONSAFEPATH": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    return {
        "mode": mode,
        "argv": [str(CLAUDE), "--model", ALIAS, *args],
        "env": env,
        "services_env": services_env,
        "services": [str(PYTHON), "-B", str(CONTROLLER), "services", ALIAS],
    }


def verify_gateway_admission(environ: dict, mode: str):
    """Refuse pending/unreviewed root metadata before exec; never start a backend."""
    import stat
    for key in ("REASONING_PROFILE_REVIEW", "REASONING_GATEWAY_ADMISSION"):
        path = Path(environ.get(key, ""))
        expected = environ.get(key + "_SHA256", "")
        if not path.is_absolute() or path.is_symlink() or not path.is_file() or len(expected) != 64 or digest(path) != expected:
            raise ValueError("Exact private reasoning review/admission is required.")
        info = path.stat()
        if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o600:
            raise ValueError("Reasoning admission must be private and owned.")
        document = parse_object(path.read_text())
        if document.get("passed") is not True or document.get("seal_pending") is not False:
            raise ValueError("Reasoning review/admission is pending.")
        if key == "REASONING_PROFILE_REVIEW":
            pins = document.get("source_pins")
            if not isinstance(pins, dict) or pins.get(str(CANDIDATE)) != digest(CANDIDATE):
                raise ValueError("The reasoning client is not source reviewed.")
            for value, expected_source in pins.items():
                source = Path(value)
                if source.is_symlink() or not source.is_file() or digest(source) != expected_source:
                    raise ValueError("A reasoning review source changed.")
        else:
            required = {"profile": PROFILE, "model": ALIAS, "model_sha256": "d784ce9eda1a5a7b51e8f705a9e6310844bf4f173654d115823c775fdea56d43", "template_sha256": "a4aee8afcf2e0711942cf848899be66016f8d14a889ff9ede07bca099c28f715", "context": 32768, "gateway": "http://127.0.0.1:14010", "native_default_reasoning": "off", "native_state_relabelled": False, "same_retained_native_owner_verified": True, "gateway_metadata_verified": True, "native_pid": 21735, "native_boot_identifier": "1790920214:266510"}
            if mode == "research":
                required["actual_zero_inference_mcp_metadata_verified"] = True
            if any(type(document.get(k)) is not type(v) or document.get(k) != v for k, v in required.items()):
                raise ValueError("The separately admitted reasoning gateway differs.")
            if document.get("profile_source_review_sha256") != environ.get("REASONING_PROFILE_REVIEW_SHA256"):
                raise ValueError("Gateway admission is not bound to the exact source review.")
            if mode == "research":
                proof = Path(document.get("mcp_metadata_path", ""))
                proof_sha = document.get("mcp_metadata_sha256", "")
                if not proof.is_absolute() or proof.is_symlink() or not proof.is_file() or len(proof_sha) != 64 or digest(proof) != proof_sha:
                    raise ValueError("Actual fresh MCP metadata receipt is required.")
                metadata = parse_object(proof.read_text())
                if any(metadata.get(k) is not True for k in ("passed", "initialize_ok", "tools_list_ok")) or type(metadata.get("model_calls")) is not int or metadata["model_calls"] != 0 or type(metadata.get("tools_call_count")) is not int or metadata["tools_call_count"] != 0 or set(metadata.get("advertised_tools", [])) != {"firecrawl_scrape", "firecrawl_search", "read_source", "publish_claims", "observed_research"} or metadata.get("args", [])[:1] != [str(TYPED_RELAY)]:
                    raise ValueError("MCP metadata does not prove the new exact zero-inference route.")
                policy = CANDIDATE.with_name("origin-policy.json")
                if policy.is_symlink() or stat.S_IMODE(policy.stat().st_mode) != 0o600 or policy.stat().st_uid != os.getuid():
                    raise ValueError("The bound origin policy must remain private and owned.")
                claims = Path(document.get("claims_directory", ""))
                if not claims.is_absolute() or claims.is_symlink() or not claims.is_dir() or claims.parent.parent != Path("/Users/mitch/.global-ai-hub/research") or claims.name != "claims" or claims.parent.name != "http-cache-revalidation-egpu-qwen35-9b-reasoning-trial-1" or claims.stat().st_uid != os.getuid() or stat.S_IMODE(claims.stat().st_mode) != 0o700:
                    raise ValueError("Fresh declared reasoning claims directory is not bound.")
            if mode == "research" and document.get("fresh_reasoning_coding_2_of_2_verified") is not True:
                raise ValueError("Research needs fresh reasoning coding; old nonthinking pairs cannot carry over.")


def main(args=None) -> int:
    args = list(sys.argv[1:] if args is None else args)
    if args == ["--version"]:
        print(f"private-qwen35-claude {VERSION}; unqualified reasoning candidate")
        return 0
    try:
        verify_source_pins()
        invocation = prepare_invocation(args, os.environ)
        verify_gateway_admission(invocation["env"], invocation["mode"])
        os.execve(str(CLAUDE), invocation["argv"], invocation["env"])
    except (OSError, ValueError, TypeError) as error:
        print(f"private-reasoning1024 refused: {type(error).__name__}", file=sys.stderr)
        return 1
    return 0



if __name__ == "__main__":
    raise SystemExit(main())
