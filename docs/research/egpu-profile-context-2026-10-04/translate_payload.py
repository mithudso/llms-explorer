#!/Users/mitch/.local/pipx/venvs/litellm/bin/python
"""Exercise installed LiteLLM's pure adapter under an OS network-deny profile."""

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    import litellm.llms.anthropic.experimental_pass_through.adapters.transformation as source
    from litellm.llms.anthropic.experimental_pass_through.adapters.transformation import (
        LiteLLMAnthropicMessagesAdapter,
    )

    root = args.output.resolve()
    root.mkdir(mode=0o700, parents=True, exist_ok=False)
    request = json.loads((args.capture / "REQUESTS.json").read_text())[0]
    translated, mapping = (
        LiteLLMAnthropicMessagesAdapter().translate_anthropic_to_openai(
            request, custom_llm_provider="openai"
        )
    )
    assert len(translated["tools"]) == len(request["tools"]) == 23
    assert [tool["function"]["name"] for tool in translated["tools"]] == [
        tool["name"] for tool in request["tools"]
    ]
    assert not mapping
    output = root / "litellm-oai.json"
    output.write_text(json.dumps(translated, indent=2) + "\n")
    receipt = {
        "version": "1.0.0",
        "scope": "installed LiteLLM pure Anthropic adapter; no completion",
        "litellm_version": importlib.metadata.version("litellm"),
        "adapter_source": source.__file__,
        "adapter_sha256": hashlib.sha256(
            Path(source.__file__).read_bytes()
        ).hexdigest(),
        "translated_request_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "tool_count": 23,
        "tool_order_names_preserved": True,
        "messages_roles": [row["role"] for row in translated["messages"]],
        "thinking_translation": translated.get("reasoning_effort"),
        "model_calls": 0,
        "gpu_actions": 0,
    }
    (root / "TRANSLATION.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
