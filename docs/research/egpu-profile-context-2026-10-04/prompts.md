# Prompt record

Version: 1.1.0

Delta: Preserve both current and original client capture experiments and their full generated prompts in private receipts.

## User objective

Qualify and deploy a physical RTX 5080 eGPU model that is functional, materially faster than the current 8-token/s Qwen3 baseline, stable across repeated sessions, supports full Claude Code coding tools, and completes a genuine standard /dr with validated artifacts. Continue model, runtime and protocol experiments until this is achieved; retain reproducible prompts, scripts, measurements, failures and continuation state.

## Current experiment

Capture the actual pinned Claude Code 2.1.286 and current2.1.289 full23 coding qualification profile with a loopback-only canned response. Retain all schemas and original instructions. Preserve actual cache-only feature data. Count the rendered payload using the installedLiteLLM pure adapter and candidate model vocabulary without executing weights or initializing a GPU. This measurement does not qualify the model.

The complete system and generated user coding prompts are retained at /Users/mitch/.cache/claude-egpu/experiments/egpu-coding-payload-capture-v102/PROMPTS.json and /Users/mitch/.cache/claude-egpu/experiments/egpu-coding-payload-capture-v103/PROMPTS.json. They include the unchanged fixture-tool sequence and summary instruction.
