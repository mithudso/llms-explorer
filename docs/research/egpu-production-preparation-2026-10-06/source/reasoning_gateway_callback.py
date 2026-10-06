"""Normalize text, compact tool prose and bind explicit coding sampler experiments."""

import copy
import hashlib
import json
import os
import re

from litellm.integrations.custom_logger import CustomLogger
from raw_compaction import compact_anthropic_tools, validate_raw_route

VERSION = "1.3.2-reasoning1024-raw-compact-private"
DELTA = (
    "Compact raw Anthropic top-level tool descriptions on the exact reasoning1024 route; preserve schemas and converted controls."
)
PROFILE_KEY = "egpu_tool_description_profile"
RECEIPT_KEY = "egpu_tool_description_compaction"
GENERATION_PROFILE_KEY = "egpu_generation_profile"
GENERATION_MODEL_KEY = "egpu_generation_profile_model"
GENERATION_RECEIPT_KEY = "egpu_generation_profile_pin"
GENERATION_MODEL_SHA_KEY = "egpu_generation_profile_model_sha256"
GENERATION_TEMPLATE_SHA_KEY = "egpu_generation_profile_template_sha256"
QWEN35_ALIAS = "qwen3.6:27b-iq2-xxs"
QWEN35_PROFILE = "qwen36-27b-iq2-reasoning-1024"
QWEN35_MODEL_SHA256 = "17021537cebf7c9750efd5413e5f3d1c4cbe4282798cb92a2201b25674d39688"
QWEN35_TEMPLATE_SHA256 = (
    "e84f32a23fdda27689f868aa4a1a5621f41133e51a48d7f3efcbea2839574259"
)
EXPERIMENT_MODEL = "qwen3:4b-instruct-2507"
CODING_EXPERIMENT_PROFILES = {
    "qwen3-coding-sampling-control": 0.7,
    "qwen3-coding-lowtemp-experiment": 0.15,
}
OTHER_SAMPLER_CONTROLS = {
    "frequency_penalty",
    "repeat_penalty",
    "repeat_last_n",
    "samplers",
    "dynatemp_range",
    "dynatemp_exponent",
    "mirostat",
    "mirostat_tau",
    "mirostat_eta",
    "dry_multiplier",
    "dry_base",
    "dry_allowed_length",
    "dry_penalty_last_n",
    "xtc_probability",
    "xtc_threshold",
    "typical_p",
    "top_n_sigma",
    "adaptive_target",
    "adaptive_decay",
    "logit_bias",
}
CORE_DESCRIPTIONS = {
    "Bash": (
        "Execute a shell command; return stdout, stderr, and exit status. Use an "
        "absolute project path for tests. timeout is in milliseconds."
    ),
    "Edit": (
        "Replace exact old_string with new_string in an existing file_path. Read the "
        "file first. old_string must match the current file. Use replace_all only when intended."
    ),
    "Read": (
        "Read an existing file_path and return its contents. Use an absolute path. "
        "Optional offset and limit select the line range."
    ),
    "Write": (
        "Create or overwrite file_path with the supplied content. Read existing files "
        "before replacing them. Use an absolute path."
    ),
    "Glob": (
        "Find paths matching pattern under path. Set path to the absolute project "
        "directory; never assume the filesystem root is the project."
    ),
    "Grep": (
        "Search pattern within path. Set path to the absolute project directory or "
        "file. Use output_mode content to return matching lines."
    ),
}
SCHEMA_MAPS = (
    "properties",
    "patternProperties",
    "$defs",
    "definitions",
    "dependentSchemas",
    "dependencies",
)
SCHEMA_SINGLE = (
    "items",
    "additionalProperties",
    "unevaluatedProperties",
    "additionalItems",
    "unevaluatedItems",
    "propertyNames",
    "contains",
    "not",
    "if",
    "then",
    "else",
    "contentSchema",
)
SCHEMA_LISTS = ("allOf", "anyOf", "oneOf", "prefixItems")


def schema_without_descriptions(schema):
    """Remove annotations at schema nodes, never keys in arbitrary literal data."""
    if not isinstance(schema, dict):
        return copy.deepcopy(schema)
    result = {
        key: copy.deepcopy(value)
        for key, value in schema.items()
        if key != "description"
    }
    for key in SCHEMA_MAPS:
        if isinstance(result.get(key), dict):
            result[key] = {
                name: schema_without_descriptions(value)
                for name, value in result[key].items()
            }
    for key in SCHEMA_SINGLE:
        if isinstance(result.get(key), dict):
            result[key] = schema_without_descriptions(result[key])
        elif key == "items" and isinstance(result.get(key), list):
            result[key] = [schema_without_descriptions(value) for value in result[key]]
    for key in SCHEMA_LISTS:
        if isinstance(result.get(key), list):
            result[key] = [schema_without_descriptions(value) for value in result[key]]
    return result


def tools_without_descriptions(tools):
    """Project every tool field except the two approved description locations."""
    result = copy.deepcopy(tools)
    for tool in result:
        function = tool["function"]
        function.pop("description", None)
        function["parameters"] = schema_without_descriptions(function["parameters"])
    return result


def json_digest(value):
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()
    ).hexdigest()


def pin_experiment_generation(kwargs, profile, model_info):
    """Validate routed controls, then pin one trusted experimental request."""
    if (
        not isinstance(model_info, dict)
        or model_info.get(GENERATION_PROFILE_KEY) != profile
        or model_info.get(GENERATION_MODEL_KEY) != EXPERIMENT_MODEL
        or kwargs.get("model") not in {EXPERIMENT_MODEL, "openai/" + EXPERIMENT_MODEL}
    ):
        raise ValueError(
            "The coding generation profile/model differs from the pinned gateway."
        )
    metadata = kwargs.get("metadata", {})
    if not isinstance(metadata, dict):
        raise TypeError("Coding generation experiments require object metadata.")
    extra = kwargs.get("extra_body")
    if extra is None:
        extra = {}
    if not isinstance(extra, dict):
        raise TypeError("Coding generation experiments require object extra_body.")
    expected = {
        "temperature": CODING_EXPERIMENT_PROFILES[profile],
        "top_p": 0.8,
        "presence_penalty": 0.0,
        "seed": 42,
        "top_k": 20,
        "min_p": 0.0,
        "cache_prompt": False,
    }
    for location in (kwargs, extra):
        for name, value in expected.items():
            supplied = location.get(name)
            if supplied is None:
                continue
            if name == "cache_prompt":
                matches = type(supplied) is bool and supplied is value
            elif name in {"seed", "top_k"}:
                matches = type(supplied) is int and supplied == value
            else:
                matches = type(supplied) in {int, float} and supplied == value
            if not matches:
                raise ValueError(
                    f"Caller {name} conflicts with the coding generation profile."
                )
        for name in OTHER_SAMPLER_CONTROLS:
            if location.get(name) is not None:
                raise ValueError(
                    f"Caller {name} cannot alter the coding experiment sampler."
                )
    result = {**kwargs, "extra_body": dict(extra)}
    for name, value in expected.items():
        result.pop(name, None)
        result["extra_body"].pop(name, None)
        if name in {"top_k", "min_p", "cache_prompt"}:
            result["extra_body"][name] = value
        else:
            result[name] = value
    result["metadata"] = {
        **metadata,
        GENERATION_RECEIPT_KEY: {
            "profile": profile,
            "model": EXPERIMENT_MODEL,
            "callback_version": VERSION,
            "request_controls": expected,
            "request_controls_sha256": json_digest(expected),
        },
    }
    return result


def validate_qwen35_caller_identity(kwargs):
    """Check both SDK metadata channels before Anthropic conversion drops fields."""
    identity = {
        GENERATION_PROFILE_KEY: QWEN35_PROFILE,
        GENERATION_MODEL_KEY: QWEN35_ALIAS,
        GENERATION_MODEL_SHA_KEY: QWEN35_MODEL_SHA256,
        GENERATION_TEMPLATE_SHA_KEY: QWEN35_TEMPLATE_SHA256,
    }
    locations = [kwargs]
    for key in ("extra_body", "metadata", "litellm_metadata", "model_info"):
        location = kwargs.get(key)
        if location is None:
            continue
        if not isinstance(location, dict):
            raise TypeError("Caller 9B identity metadata must be an object.")
        locations.append(location)
        nested = location.get("model_info")
        if nested is not None:
            if not isinstance(nested, dict):
                raise TypeError("Caller 9B model_info must be an object.")
            locations.append(nested)
    for location in locations:
        for name, value in identity.items():
            if name in location and location[name] != value:
                raise ValueError(
                    "Caller 9B identity conflicts with the pinned gateway."
                )


def pin_qwen35_generation(kwargs, model_info):
    """Reject conflicting caller data before late-pinning the exact separately declared reasoning1024 route."""
    identity = {
        GENERATION_PROFILE_KEY: QWEN35_PROFILE,
        GENERATION_MODEL_KEY: QWEN35_ALIAS,
        GENERATION_MODEL_SHA_KEY: QWEN35_MODEL_SHA256,
        GENERATION_TEMPLATE_SHA_KEY: QWEN35_TEMPLATE_SHA256,
    }
    validate_qwen35_caller_identity(kwargs)
    if (
        not isinstance(model_info, dict)
        or any(model_info.get(key) != value for key, value in identity.items())
        or type(model_info.get("max_input_tokens")) is not int
        or model_info["max_input_tokens"] != 32768
        or kwargs.get("model") not in {QWEN35_ALIAS, "openai/" + QWEN35_ALIAS}
    ):
        raise ValueError(
            "The 9B model/template/context differs from the pinned gateway."
        )
    metadata = kwargs.get("metadata", {})
    extra = kwargs.get("extra_body")
    if not isinstance(metadata, dict) or (
        extra is not None and not isinstance(extra, dict)
    ):
        raise TypeError("The 9B gateway requires object metadata and extra_body.")
    extra = {} if extra is None else extra
    for location in (kwargs, extra):
        if "enable_thinking" in location and location["enable_thinking"] is not True:
            raise ValueError("Caller enable_thinking conflicts with the 9B profile.")
        if "model" in location and location["model"] not in {
            QWEN35_ALIAS,
            "openai/" + QWEN35_ALIAS,
        }:
            raise ValueError("Caller 9B model conflicts with the pinned gateway.")
        if "chat_template" in location or "repetition_penalty" in location:
            raise ValueError("Caller 9B template/sampler override is unsupported.")
        if location.get("reasoning_effort") not in {None, "low"}:
            raise ValueError(
                "Caller 9B reasoning conflicts with the reasoning1024 profile."
            )
        if "chat_template_kwargs" in location:
            supplied = location["chat_template_kwargs"]
            if (
                not isinstance(supplied, dict)
                or set(supplied) != {"enable_thinking"}
                or supplied["enable_thinking"] is not True
            ):
                raise ValueError(
                    "Caller enable_thinking conflicts with the 9B profile."
                )
    expected = {
        "temperature": 0.6,
        "top_p": 0.95,
        "presence_penalty": 0.0,
        "seed": 42,
        "top_k": 20,
        "min_p": 0.0,
        "repeat_penalty": 1.0,
        "cache_prompt": False,
        "max_tokens": 4096,
        "reasoning_effort": "low",
        "reasoning_format": "deepseek",
        "reasoning_budget_tokens": 1024,
    }
    for location in (kwargs, extra):
        for name, value in expected.items():
            supplied = location.get(name)
            if supplied is None:
                continue
            if name == "cache_prompt":
                matches = type(supplied) is bool and supplied is value
            elif name in {"seed", "top_k", "max_tokens", "reasoning_budget_tokens"}:
                matches = type(supplied) is int and supplied == value
            elif isinstance(value, str):
                matches = type(supplied) is str and supplied == value
            else:
                matches = type(supplied) in {int, float} and supplied == value
            if not matches:
                raise ValueError(f"Caller {name} conflicts with the 9B profile.")
        for forbidden in ("thinking_budget_tokens", "reasoning_control", "reasoning_budget_message", "max_completion_tokens", "n_predict"):
            if forbidden in location:
                raise ValueError("Caller cannot override the reasoning budget/output contract.")
        for name in OTHER_SAMPLER_CONTROLS - {"repeat_penalty"}:
            if location.get(name) is not None:
                raise ValueError(f"Caller {name} cannot alter the 9B sampler.")
    result = {**kwargs, "extra_body": dict(extra)}
    for name, value in expected.items():
        result.pop(name, None)
        result["extra_body"].pop(name, None)
        if name in {"top_k", "min_p", "repeat_penalty", "cache_prompt", "reasoning_format", "reasoning_budget_tokens"}:
            result["extra_body"][name] = value
        else:
            result[name] = value
    result.pop("chat_template_kwargs", None)
    result.pop("enable_thinking", None)
    result["extra_body"].pop("enable_thinking", None)
    result["extra_body"].pop("model", None)
    result["extra_body"]["chat_template_kwargs"] = {"enable_thinking": True}
    receipt_controls = {**expected, "chat_template_kwargs": {"enable_thinking": True}}
    result["metadata"] = {
        **metadata,
        GENERATION_RECEIPT_KEY: {
            "profile": QWEN35_PROFILE,
            "model": QWEN35_ALIAS,
            "model_sha256": QWEN35_MODEL_SHA256,
            "template_sha256": QWEN35_TEMPLATE_SHA256,
            "callback_version": VERSION,
            "request_controls": receipt_controls,
            "request_controls_sha256": json_digest(receipt_controls),
            "experimental_reproducibility_controls": ["seed", "cache_prompt"],
        },
    }
    return result



def compact_bash_description(parameters):
    """Retain timeout units and only a limit stated by the supplied SDK schema."""
    description = CORE_DESCRIPTIONS["Bash"]
    if not isinstance(parameters, dict):
        return description
    properties = parameters.get("properties")
    if not isinstance(properties, dict):
        return description
    timeout = properties.get("timeout")
    if not isinstance(timeout, dict):
        return description
    annotation = timeout.get("description")
    if isinstance(annotation, str):
        # The SDK supplies this operational limit as prose, not JSON Schema
        # maximum. Read the actual request instead of assuming the gateway's
        # environment matches the SDK process or hardcoding its default.
        match = re.fullmatch(
            r"Optional timeout in milliseconds \(max ([1-9][0-9]{0,11}) for a foreground command\)",
            annotation,
        )
        if match:
            description += f" Foreground timeout max {match[1]} ms."
    return description


def compact_tool_descriptions(tools):
    """Preserve tool order, names and validation while bounding descriptive prose."""
    if not isinstance(tools, list):
        raise TypeError("compact-v1 requires a list of OpenAI function tools.")
    for tool in tools:
        if (
            not isinstance(tool, dict)
            or tool.get("type") != "function"
            or not isinstance(tool.get("function"), dict)
            or not isinstance(tool["function"].get("name"), str)
            or not tool["function"]["name"]
            or not isinstance(tool["function"].get("parameters"), (dict, bool))
        ):
            raise ValueError(
                "compact-v1 received an unsupported or malformed function tool."
            )
    original_projection = tools_without_descriptions(tools)
    compacted = copy.deepcopy(tools)
    for tool in compacted:
        function = tool["function"]
        description = function.get("description")
        if isinstance(description, str):
            function["description"] = (
                compact_bash_description(function["parameters"])
                if function["name"] == "Bash"
                else CORE_DESCRIPTIONS.get(function["name"], description[:256])
            )
        function["parameters"] = schema_without_descriptions(function["parameters"])
    if tools_without_descriptions(compacted) != original_projection:
        raise ValueError(
            "compact-v1 changed a tool field other than an approved description."
        )
    receipt = {
        "profile": "compact-v1",
        "callback_version": VERSION,
        "tool_count": len(tools),
        "original_tools_sha256": json_digest(tools),
        "compacted_tools_sha256": json_digest(compacted),
        "validation_projection_sha256": json_digest(original_projection),
        "validation_projection_equal": True,
        "original_tools_characters": len(json.dumps(tools, ensure_ascii=False)),
        "compacted_tools_characters": len(json.dumps(compacted, ensure_ascii=False)),
    }
    return compacted, receipt



def validate_reasoning_input(kwargs):
    """Raw Anthropic thinking may be absent or exactly enabled1024; never disabled."""
    thinking = kwargs.get("thinking")
    if thinking is not None and (
        not isinstance(thinking, dict)
        or set(thinking) != {"type", "budget_tokens"}
        or thinking.get("type") != "enabled"
        or type(thinking.get("budget_tokens")) is not int
        or thinking["budget_tokens"] != 1024
    ):
        raise ValueError("Caller thinking conflicts with reasoning1024.")


class TinygradTextMessages(CustomLogger):
    def __init__(self, api_base=None):
        super().__init__()
        self.api_base = api_base or os.environ.get("EGPU_TINYGRAD_API_BASE")
        self.tool_description_profile = os.environ.get(
            "EGPU_TOOL_DESCRIPTION_PROFILE", "default"
        )
        if self.tool_description_profile not in {"default", "compact-v1"}:
            raise ValueError(
                "Unknown EGPU_TOOL_DESCRIPTION_PROFILE; use default or compact-v1."
            )
        self.generation_profile = os.environ.get("EGPU_GENERATION_PROFILE", "default")
        if self.generation_profile not in {
            "default",
            "qwen3-instruct-2507",
            "deterministic-diagnostic",
            QWEN35_PROFILE,
            *CODING_EXPERIMENT_PROFILES,
        }:
            raise ValueError("Unknown EGPU_GENERATION_PROFILE in the gateway callback.")

    async def async_pre_call_deployment_hook(self, kwargs, call_type):
        if self.generation_profile == QWEN35_PROFILE and getattr(
            call_type, "value", call_type
        ) in {"anthropic_messages", "acompletion", "completion"}:
            validate_qwen35_caller_identity(kwargs)
            validate_reasoning_input(kwargs)
        metadata = kwargs.get("metadata", {})
        model_info = metadata.get("model_info") if isinstance(metadata, dict) else None
        if model_info is None:
            model_info = kwargs.get("model_info", {})
        is_completion = getattr(call_type, "value", call_type) in {
            "acompletion",
            "completion",
        }
        is_qwen35 = (
            self.generation_profile == QWEN35_PROFILE
            or (
                isinstance(model_info, dict)
                and model_info.get(GENERATION_PROFILE_KEY) == QWEN35_PROFILE
            )
            or kwargs.get("model") in {QWEN35_ALIAS, "openai/" + QWEN35_ALIAS}
        )
        if (
            getattr(call_type, "value", call_type) == "anthropic_messages"
            and is_qwen35
            and self.tool_description_profile == "compact-v1"
        ):
            if self.generation_profile != QWEN35_PROFILE:
                raise ValueError("The raw 9B route requires its explicit generation profile.")
            routed = validate_raw_route(kwargs, self.api_base, QWEN35_ALIAS, {
                GENERATION_PROFILE_KEY: QWEN35_PROFILE,
                GENERATION_MODEL_KEY: QWEN35_ALIAS,
                GENERATION_MODEL_SHA_KEY: QWEN35_MODEL_SHA256,
                GENERATION_TEMPLATE_SHA_KEY: QWEN35_TEMPLATE_SHA256,
                PROFILE_KEY: "compact-v1",
                "max_input_tokens": 32768,
                "max_output_tokens": 4096,
                "supports_function_calling": True,
                "supports_reasoning": True,
            })
            tools = kwargs.get("tools")
            if tools is None:
                return None
            compacted, receipt = compact_anthropic_tools(
                tools, CORE_DESCRIPTIONS, compact_bash_description, VERSION
            )
            from research_tool_choice import pin_anthropic
            from gate_tool_choice import pin_anthropic as pin_gate_anthropic
            return pin_gate_anthropic(pin_anthropic({**kwargs, "tools": compacted,
                "litellm_metadata": {**routed, RECEIPT_KEY: receipt}}))
        if is_completion and is_qwen35:
            if self.generation_profile != QWEN35_PROFILE:
                raise ValueError(
                    "The 9B model requires its explicit generation profile."
                )
            if not self.api_base or kwargs.get("api_base") != self.api_base:
                raise ValueError("The 9B route differs from the pinned gateway.")
        if (
            isinstance(model_info, dict)
            and model_info.get(GENERATION_PROFILE_KEY)
            in {*CODING_EXPERIMENT_PROFILES, QWEN35_PROFILE}
            and getattr(call_type, "value", call_type) in {"acompletion", "completion"}
            and kwargs.get("api_base") != self.api_base
        ):
            raise ValueError(
                "The coding experiment route differs from the pinned gateway."
            )
        if (
            not self.api_base
            or kwargs.get("api_base") != self.api_base
            or getattr(call_type, "value", call_type)
            not in {"acompletion", "completion"}
        ):
            return None
        configured_profile = (
            model_info.get(PROFILE_KEY, "default")
            if isinstance(model_info, dict)
            else None
        )
        if self.tool_description_profile != "default":
            if not isinstance(metadata, dict):
                raise TypeError("compact-v1 requires object metadata.")
            if configured_profile != self.tool_description_profile:
                raise ValueError(
                    "The tool description profile differs from the pinned gateway profile."
                )
        elif configured_profile not in {"default", None}:
            raise ValueError(
                "The tool description profile differs from the pinned gateway profile."
            )
        messages = kwargs.get("messages")
        if not isinstance(messages, list):
            raise TypeError("The tinygrad text backend requires a list of messages.")
        normalized = []
        for index, message in enumerate(messages):
            if not isinstance(message, dict):
                raise TypeError(
                    f"The tinygrad text backend requires message {index} to be an object."
                )
            content = message.get("content")
            if isinstance(content, list):
                paragraphs = []
                for block in content:
                    if (
                        not isinstance(block, dict)
                        or block.get("type") != "text"
                        or not isinstance(block.get("text"), str)
                    ):
                        raise ValueError(
                            f"The tinygrad text backend supports only text content blocks; "
                            f"message {index} contains an unsupported or malformed block."
                        )
                    paragraphs.append(block["text"])
                content = "\n\n".join(paragraphs)
            elif content is None and message.get("role") == "assistant":
                content = ""
            elif not isinstance(content, str):
                raise ValueError(
                    f"The tinygrad text backend requires string or text-block content; "
                    f"message {index} contains unsupported content."
                )
            normalized.append({**message, "content": content})
        result = {**kwargs, "messages": normalized}
        configured_generation = (
            model_info.get(GENERATION_PROFILE_KEY, "default")
            if isinstance(model_info, dict)
            else "default"
        )
        if self.generation_profile == QWEN35_PROFILE:
            result = pin_qwen35_generation(result, model_info)
        elif configured_generation == QWEN35_PROFILE:
            raise ValueError(
                "The 9B generation profile differs from the pinned gateway."
            )
        elif self.generation_profile in CODING_EXPERIMENT_PROFILES:
            result = pin_experiment_generation(
                result, self.generation_profile, model_info
            )
        elif configured_generation != "default":
            raise ValueError(
                "The coding generation profile differs from the pinned gateway."
            )
        if self.tool_description_profile == "compact-v1":
            tools = kwargs.get("tools")
            if tools is not None:
                result["tools"], receipt = compact_tool_descriptions(tools)
                result["metadata"] = {
                    **result.get("metadata", {}),
                    RECEIPT_KEY: receipt,
                }
        from research_tool_choice import pin as pin_research_tool_choice
        from gate_tool_choice import pin as pin_gate_tool_choice
        return pin_gate_tool_choice(pin_research_tool_choice(result))


handler = TinygradTextMessages()
