"""Version1.0.0: compact only raw client-tool prose on an exact routed deployment."""

import copy
import hashlib
import json


def digest(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode()).hexdigest()


def projection(tools):
    result = copy.deepcopy(tools)
    for tool in result:
        tool.pop("description", None)
    return result


def validate_raw_route(kwargs, api_base, alias, expected_model_info):
    """Caller metadata cannot supply deployment authority or override the route."""
    if not api_base or kwargs.get("api_base") != api_base:
        raise ValueError("Raw Anthropic route differs from the pinned gateway.")
    if kwargs.get("model") not in {alias, "openai/" + alias}:
        raise ValueError("Raw Anthropic model differs from the pinned gateway.")
    routed = kwargs.get("litellm_metadata")
    if not isinstance(routed, dict) or routed.get("api_base") != api_base:
        raise ValueError("Raw Anthropic deployment metadata or route is absent.")
    for info in (kwargs.get("model_info"), routed.get("model_info")):
        if not isinstance(info, dict) or any(
            type(info.get(key)) is not type(value) or info[key] != value
            for key, value in expected_model_info.items()
        ):
            raise ValueError("Raw Anthropic deployment profile/model/context differs.")
    return routed


def compact_anthropic_tools(tools, core_descriptions, bash_description, version):
    """Preserve every raw tool field except its top-level string description."""
    if not isinstance(tools, list):
        raise TypeError("Raw compact-v1 requires a list of Anthropic client tools.")
    for tool in tools:
        if (
            not isinstance(tool, dict)
            or not isinstance(tool.get("name"), str)
            or not tool["name"]
            or not isinstance(tool.get("input_schema"), (dict, bool))
            or ("description" in tool and not isinstance(tool["description"], str))
        ):
            raise ValueError("Raw compact-v1 received a malformed client tool.")
    before = projection(tools)
    compacted = copy.deepcopy(tools)
    for tool in compacted:
        if "description" in tool:
            tool["description"] = (
                bash_description(tool["input_schema"])
                if tool["name"] == "Bash"
                else core_descriptions.get(tool["name"], tool["description"][:256])
            )
    if digest(projection(compacted)) != digest(before):
        raise ValueError("Raw compaction changed a field other than tool description.")
    schemas_before = digest([tool["input_schema"] for tool in tools])
    schemas_after = digest([tool["input_schema"] for tool in compacted])
    if schemas_before != schemas_after:
        raise ValueError("Raw compaction changed input_schema.")
    receipt = {
        "profile": "compact-v1",
        "callback_version": version,
        "tool_format": "anthropic-client",
        "changed_locations": ["tool.description"],
        "tool_count": len(tools),
        "original_tools_sha256": digest(tools),
        "compacted_tools_sha256": digest(compacted),
        "validation_projection_sha256": digest(before),
        "validation_projection_equal": True,
        "input_schemas_sha256": schemas_before,
        "input_schemas_equal": True,
        "original_tools_characters": len(json.dumps(tools, ensure_ascii=False)),
        "compacted_tools_characters": len(json.dumps(compacted, ensure_ascii=False)),
    }
    return compacted, receipt
