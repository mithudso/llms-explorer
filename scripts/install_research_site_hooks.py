#!/usr/bin/env python3
"""Install backed-up website/source-library hooks in the local research runtime."""
from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path

from sync_codex_research_skills import LIBRARY_REFERENCE

START, END = "<!-- shared-research-completion:start -->", "<!-- shared-research-completion:end -->"


def library_policy(text: str) -> str:
    text = re.sub(r"(?m)^1b\. \*\*Website tree.*$",
        "1b. **Website completion.** `finish` refreshes concept packs and generated website content automatically. Orchestrated runs use the same completion path. CFE Step 9d refreshes final placement again. A refresh error leaves persistence unfinished.", text)
    text = text.replace("and state that `/dr` Phase 3 step 1b (website-tree sync) is skipped: Step 9d owns it.",
                        "and require `/dr finish` to refresh the website after each concept. Step 9d refreshes final placement again.")
    block = START + "\n" + LIBRARY_REFERENCE + "\n" + END
    if START in text:
        before, rest = text.split(START, 1)
        _, after = rest.split(END, 1)
        return before + block + after
    return text.rstrip() + "\n\n" + block + "\n"


def install(repo: Path, hub: Path, claude: Path, check=False) -> dict:
    outputs = {hub / "scripts/research_site_hook.py": (repo / "hub/scripts/research_site_hook.py").read_text()}
    tree = hub / "scripts/concept_tree.py"
    text = tree.read_text()
    if 'glob("*/.agents/skills")' not in text:
        old = '''SKILLS_DIRS = (Path.home() / ".claude" / "skills", HUB_DIR / "skills",
               *sorted((Path.home() / "dev").glob("*/.claude/skills")))'''
        new = '''SKILLS_DIRS = (Path.home() / ".claude" / "skills", HUB_DIR / "skills",
               Path.home() / ".codex" / "skills",
               *sorted((Path.home() / "dev").glob("*/.claude/skills")),
               *sorted((Path.home() / "dev").glob("*/.agents/skills")))'''
        if old not in text:
            raise ValueError("Concept tree skill roots changed; inspect before installing")
        text = text.replace(old, new)
    if "    from research_site_hook import refresh\n    refresh(p, HUB_DIR)" not in text:
        start = text.index("def save_nodes(")
        position = text.index("    tmp.replace(p)\n", start) + len("    tmp.replace(p)\n")
        text = text[:position] + "    from research_site_hook import refresh\n    refresh(p, HUB_DIR)\n" + text[position:]
    outputs[tree] = text
    runtime = hub / "scripts/dr_run.py"
    text = runtime.read_text()
    if "# shared website completion hook" not in text:
        anchor = "    return 0\n\n\ndef build_gate_brief"
        if text.count(anchor) != 1:
            raise ValueError("DR finish hook anchor changed; inspect cmd_finish before installing")
        replacement = '''    # shared website completion hook
    if a.status in ("COMPLETED", "BUDGET_EXHAUSTED") and not globals().get("CODEX_SITE_SYNC_HANDLED"):
        from research_site_hook import refresh
        try:
            refresh(HUB_DIR / "concept-tree/tree.json", HUB_DIR, run=a.slug)
        except (OSError, RuntimeError) as error:
            _print({"ok": False, "website_refresh_failed": str(error), "run": a.slug})
            return 1
    return 0


def build_gate_brief'''
        text = text.replace(anchor, replacement)
    outputs[runtime] = text
    template = hub / "scripts/dr_assets/brief.md"
    text = template.read_text()
    worker_start, worker_end = "<!-- shared-source-library:start -->", "<!-- shared-source-library:end -->"
    worker = worker_start + "\n" + LIBRARY_REFERENCE.split("\nEvery persisted concept run", 1)[0] + "\n" + worker_end
    if worker_start in text:
        before, rest = text.split(worker_start, 1)
        _, after = rest.split(worker_end, 1)
        text = before + worker + after
    else:
        text = worker + "\n\n" + text
    outputs[template] = text
    canonical_tree_sync = claude / "skills/concept-family-explorer/scripts/sync_trees.py"
    if canonical_tree_sync.is_file():
        outputs[claude / "skills/concept-family-explorer/references/tree-sync.md"] = (
            repo / "scripts/codex_research_assets/concept-family-explorer/references/tree-sync.md").read_text()
        text = canonical_tree_sync.read_text()
        local = (repo / "scripts/codex_research_assets/concept-family-explorer/scripts/sync_trees.py").read_text()
        start, end = text.index("def regen("), text.index("def main(")
        replacement = local[local.index("def regen("):local.index("def main(")]
        text = text[:start] + replacement + text[end:]
        old = '''        if label == "site" and a.apply and _branch(repo) in ("main", "master"):
            print(f"[site] REFUSED: {repo} is on {_branch(repo)} — use a branch or worktree")
            ok_all = False
            continue
'''
        text = text.replace(old, "")
        old_call = '        if label == "site" and ok and a.apply and a.regen:\n            print("\\n".join(regen(repo, hub, s)))'
        new_call = '        if label == "site" and ok and a.apply and a.regen:\n            try:\n                print("\\n".join(regen(repo, hub, s)))\n            except (OSError, RuntimeError) as error:\n                print(str(error), file=sys.stderr)\n                ok_all = False'
        text = text.replace(old_call, new_call)
        outputs[canonical_tree_sync] = text
    for target in (repo / ".claude/skills/llms-concept-abstractor/scripts/concept_abstract.py",
                   claude / "skills/llms-txt-tooling/references/llms-concept-abstractor/scripts/concept_abstract.py"):
        if not target.is_file():
            continue
        text = target.read_text()
        if "# shared website completion hook" not in text:
            start = text.index("def compile_pack(")
            end = text.index("\n# --------------------------------------------------------------------------- #\n# semantic", start)
            hook = '''    # shared website completion hook
    hub = Path(os.environ.get("HUB_DIR", str(Path.home() / ".global-ai-hub"))).expanduser()
    if (hub / "research/.site-sync.json").is_file():
        sys.path.insert(0, str(hub / "scripts"))
        from research_site_hook import refresh
        refresh(out, hub)


'''
            text = text[:end].rstrip() + "\n" + hook + text[end:]
        outputs[target] = text
    for target in [*(repo / ".claude/skills" / skill / "SKILL.md" for skill in ("dr", "concept-family-explorer", "rabbithole")),
                   claude / "commands/dr.md", claude / "skills/concept-family-explorer/SKILL.md",
                   claude / "skills/rabbithole/SKILL.md"]:
        if target.is_file():
            outputs[target] = library_policy(target.read_text())
    outputs[hub / "research/.site-sync.json"] = json.dumps({"repo": str(repo), "version": 1}, indent=2) + "\n"
    changes = {path: text for path, text in outputs.items() if not path.exists() or path.read_text() != text}
    result = {"ok": not changes if check else True, "check": check, "changed": [str(path) for path in changes]}
    if check or not changes:
        return result
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
    backup = hub / "research/.site-sync-backups" / stamp
    for index, path in enumerate(changes):
        if path.exists():
            saved = backup / f"{index}-{path.name}"
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, saved)
    for path, text in changes.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    result["backup"] = str(backup)
    (backup / "receipt.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--hub", type=Path, default=Path.home() / ".global-ai-hub")
    parser.add_argument("--claude", type=Path, default=Path.home() / ".claude")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    result = install(args.repo, args.hub, args.claude, args.check)
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
