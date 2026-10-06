"""Version1.0.1: retain Responses sampler values through deployment extra_body."""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ALIAS = "qwen3.6:27b-iq2-xxs"
PROFILE = "qwen36-27b-iq2-reasoning-1024"
MODEL_SHA = "17021537cebf7c9750efd5413e5f3d1c4cbe4282798cb92a2201b25674d39688"
TEMPLATE_SHA = "e84f32a23fdda27689f868aa4a1a5621f41133e51a48d7f3efcbea2839574259"
NATIVE_BASE = "http://127.0.0.1:8000/v1"
GATEWAY_PORT = 14139
CONTROLS = {"temperature": 0.6, "top_p": 0.95, "top_k": 20, "min_p": 0.0, "presence_penalty": 0.0, "repeat_penalty": 1.0, "seed": 42, "cache_prompt": False, "max_tokens": 4096, "reasoning_effort": "low", "reasoning_format": "deepseek", "reasoning_budget_tokens": 1024, "chat_template_kwargs": {"enable_thinking": True}}

def model_info():
    return {"max_input_tokens": 32768, "max_output_tokens": 4096, "supports_function_calling": True, "supports_reasoning": True, "egpu_generation_profile": PROFILE, "egpu_generation_profile_model": ALIAS, "egpu_generation_profile_model_sha256": MODEL_SHA, "egpu_generation_profile_template_sha256": TEMPLATE_SHA, "egpu_tool_description_profile": "compact-v1"}

def gateway_config(master_key: str):
    if not isinstance(master_key, str) or not master_key or any(c in master_key for c in "\x00\r\n"):
        raise ValueError("A private local gateway key is required")
    extra_keys = {"top_k", "min_p", "presence_penalty", "seed", "repeat_penalty", "cache_prompt", "reasoning_format", "reasoning_budget_tokens", "chat_template_kwargs"}
    params = {"model": "openai/" + ALIAS, "api_base": NATIVE_BASE, "api_key": "local-egpu", **{k: v for k,v in CONTROLS.items() if k not in extra_keys}, "extra_body": {k:v for k,v in CONTROLS.items() if k in extra_keys}}
    return {"model_list": [{"model_name": name, "litellm_params": params, "model_info": model_info()} for name in [ALIAS, "claude-sonnet-5", "claude-haiku-4-5-20251001"]], "litellm_settings": {"drop_params": False, "callbacks": ["reasoning_gateway_callback.handler"], "set_verbose": False}, "general_settings": {"master_key": master_key}}

def gateway_environment(environ):
    result = dict(environ)
    required = {"EGPU_GENERATION_PROFILE": PROFILE, "EGPU_TOOL_DESCRIPTION_PROFILE": "compact-v1", "EGPU_TINYGRAD_API_BASE": NATIVE_BASE}
    for key,value in required.items():
        if key in result and result[key] != value: raise ValueError("Gateway profile/environment conflict")
        result[key] = value
    result.update(PYTHONPATH=str(ROOT), PYTHONSAFEPATH="1", PYTHONDONTWRITEBYTECODE="1", LITELLM_LOCAL_MODEL_COST_MAP="true", DEFAULT_REASONING_EFFORT_LOW_THINKING_BUDGET="1024", DEFAULT_REASONING_EFFORT_MEDIUM_THINKING_BUDGET="2048", DEFAULT_REASONING_EFFORT_HIGH_THINKING_BUDGET="4096")
    return result
