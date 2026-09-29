#!/usr/bin/env python3
"""Repair known Codex plugin packaging defects. Version 1.0.0.

Back up every changed file. Re-run after reinstalling these plugin versions.
Changed Semgrep commands require review and renewed trust in Codex's hooks UI.
"""
import argparse
import copy
import datetime
import json
from pathlib import Path
import platform
import re
import shlex
import shutil
import tomllib

VERSION = "1.0.0"


def repair_semgrep(document):
    result = copy.deepcopy(document)
    for groups in result.get("hooks", {}).values():
        for group in groups:
            for hook in group.get("hooks", []):
                if hook.get("command") == "${CLAUDE_PLUGIN_ROOT}/scripts/hook" and hook.get("args"):
                    hook["command"] = '"${CLAUDE_PLUGIN_ROOT}/scripts/hook" ' + shlex.join(hook.pop("args"))
    return result


def disable_windows_hooks(config):
    events = ["pre_tool_use", "post_tool_use", "user_prompt_submit", "post_compact", "stop"]
    for event in events:
        key = f"ai-software-architect@openai-curated-remote:hooks/hooks.json:{event}:0:0"
        header = f'[hooks.state."{key}"]'
        pattern = re.compile(re.escape(header) + r"\n(.*?)(?=^\[|\Z)", re.M | re.S)
        match = pattern.search(config)
        if match:
            body = match.group(1)
            if re.search(r"^enabled\s*=", body, re.M):
                body = re.sub(r"^enabled\s*=.*$", "enabled = false", body, flags=re.M)
            else:
                body = "enabled = false\n" + body
            config = config[:match.start(1)] + body + config[match.end(1):]
        else:
            config += f"\n{header}\nenabled = false\n"
    tomllib.loads(config)
    return config


def save(path, content):
    if path.read_text() == content:
        return
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup = path.with_name(path.name + ".backup-hook-repair-" + stamp)
    shutil.copy2(path, backup)
    path.write_text(content)
    print(f"Repaired {path}; backup: {backup}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-dir", type=Path, default=Path.home() / ".codex")
    args = parser.parse_args()
    root = args.codex_dir
    manifest = root / "plugins/cache/claude-plugins-official/semgrep/2.3.0/hooks/hooks.json"
    if manifest.exists():
        document = json.loads(manifest.read_text())
        repaired = repair_semgrep(document)
        if repaired != document:
            save(manifest, json.dumps(repaired, indent=2) + "\n")
    if platform.system() == "Darwin":
        config = root / "config.toml"
        save(config, disable_windows_hooks(config.read_text()))


if __name__ == "__main__":
    main()
