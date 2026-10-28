#!/usr/bin/env python3
"""ado_tools.py — deterministic helpers for agent-deep-optimizer (/ado).

Every mechanical check the skill relies on runs here, so its result is a value the
auditor did not author. Each subcommand prints one JSON object tagged
"evidence": "EXECUTED" and exits 0 (ok), 2 (schema: at least one High finding), or
1 (helper error: bad arguments, unreadable target).

  schema  <agent.md> [--project-dir D]       frontmatter contract check + body heuristics
  roster  [--project-dir D]                  every agent across roots: precedence, collisions, budget
  refs    <name> [--project-dir D]           files that mention the agent name (rename-impact set)
  tokens  <agent.md> [--project-dir D]       startup-context estimate: body + preloaded skills + CLAUDE.md
  smoke   <name|agent.md> [--cwd D] [--timeout S] [--agents-json F]
                                             `claude -p --agent <name>` load check (READY probe)
  backup  <path> --run-id ID [--iter N --from FILE]
                                             pre-write snapshot into the family backup dir

Stdlib only. PyYAML parses the frontmatter when importable; otherwise a minimal
key / value / list parser runs and the output carries "yaml_parser": "fallback".
The contract the checks encode lives in ../references/agent-contract.md.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

try:  # optional
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None

HOME = Path.home()
BACKUP_ROOT = HOME / ".claude" / "skill-consolidation" / "backups"

# --- contract tables (keep in sync with references/agent-contract.md) ----------
SUPPORTED_KEYS = {
    "name", "description", "tools", "disallowedTools", "model", "permissionMode",
    "maxTurns", "autoCompactWindow", "skills", "mcpServers", "hooks", "memory",
    "background", "omitClaudeMd", "effort", "isolation", "color", "initialPrompt",
    "experimental",
}
# Keys this roster uses as documentation metadata; the harness ignores them silently.
TOLERATED_KEYS = {"version", "last_reviewed", "updated"}
MODEL_ALIASES = {"sonnet", "opus", "haiku", "fable", "inherit"}
PERMISSION_MODES = {"default", "acceptEdits", "auto", "dontAsk", "bypassPermissions", "plan", "manual"}
EFFORTS = {"low", "medium", "high", "xhigh", "max"}
COLORS = {"red", "blue", "green", "yellow", "purple", "orange", "pink", "cyan"}
MEMORY_SCOPES = {"user", "project", "local"}
CACHE_TTLS = {"5m", "1h"}
BUILTIN_AGENTS = {"Explore", "Plan", "general-purpose", "statusline-setup", "claude-code-guide", "fork"}
# Tools a subagent can be granted. The live list varies by session (MCP tools are
# mcp__<server>__<tool>), so an unknown entry is "unresolved", never "dead", unless
# every entry is unresolved.
KNOWN_TOOLS = {
    "Agent", "Artifact", "ArtifactComments", "ArtifactData", "AskUserQuestion", "Bash", "Edit",
    "Glob", "Grep", "ListAgents", "Monitor", "NotebookEdit", "Read", "SendMessage", "SendUserFile",
    "Skill", "TaskCreate", "TaskUpdate", "TaskList", "TaskGet", "TodoWrite", "ToolSearch",
    "WebFetch", "WebSearch", "Workflow", "Write",
}
WRITE_TOOLS = {"Write", "Edit", "NotebookEdit"}
DESC_SOFT_CHARS = 900     # Pass A Medium
DESC_HARD_CHARS = 1500    # Pass A High
ROSTER_BUDGET_TOKENS = 15000  # Claude Code startup warning threshold (all non-built-in descriptions)
BODY_SOFT_TOKENS = 3000   # Pass N Medium
BODY_HARD_TOKENS = 6000   # Pass N High
PRELOAD_SOFT_TOKENS = 8000
PRELOAD_HARD_TOKENS = 20000

SECRET_PATTERNS = [
    ("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("openai-style-key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b")),
    ("slack-token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("private-key-block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")),
    ("password-assignment", re.compile(r"(?i)\b(password|passwd|secret|api[_-]?key|token)\s*[:=]\s*['\"][^'\"]{6,}['\"]")),
]
ASK_USER_PATTERNS = re.compile(
    r"(?i)\b(ask the user|ask the caller|wait for (the )?(user|confirmation|approval)|AskUserQuestion|prompt the user for)\b"
)


def est_tokens(text: str) -> int:
    return max(0, round(len(text) / 4))


def emit(obj: dict, code: int = 0) -> None:
    obj.setdefault("evidence", "EXECUTED")
    print(json.dumps(obj, indent=1, sort_keys=False))
    sys.exit(code)


def fail(msg: str) -> None:
    print(json.dumps({"error": msg, "evidence": "EXECUTED"}))
    sys.exit(1)


# --- frontmatter ---------------------------------------------------------------
def split_frontmatter(text: str) -> tuple[str | None, str]:
    if not text.startswith("---"):
        return None, text
    m = re.match(r"^---[ \t]*\r?\n(.*?)\r?\n---[ \t]*\r?\n?", text, re.S)
    if not m:
        return None, text
    return m.group(1), text[m.end():]


def fallback_parse(fm: str) -> dict:
    """Minimal YAML: `key: value`, `key:` + `- item` lists, `key: [a, b]`, block scalars folded."""
    out: dict = {}
    key = None
    block: list[str] | None = None
    for raw in fm.splitlines():
        if block is not None:
            if raw.startswith((" ", "\t")) or raw.strip() == "":
                block.append(raw.strip())
                continue
            out[key] = " ".join(x for x in block if x).strip()
            block = None
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", raw)
        if m:
            key, val = m.group(1), m.group(2).strip()
            if val in (">", ">-", "|", "|-"):
                block = []
            elif val == "":
                out[key] = []
            elif val.startswith("[") and val.endswith("]"):
                out[key] = [v.strip().strip("'\"") for v in val[1:-1].split(",") if v.strip()]
            else:
                low = val.lower()
                if low in ("true", "false"):
                    out[key] = low == "true"
                elif re.fullmatch(r"-?\d+", val):
                    out[key] = int(val)
                else:
                    out[key] = val.strip("'\"")
            continue
        m = re.match(r"^\s+-\s*(.*)$", raw)
        if m and key is not None and isinstance(out.get(key), list):
            out[key].append(m.group(1).strip().strip("'\""))
    if block is not None and key is not None:
        out[key] = " ".join(x for x in block if x).strip()
    return out


def parse_frontmatter(fm: str) -> tuple[dict, str, str | None]:
    """Returns (data, parser_name, parse_error)."""
    if yaml is not None:
        try:
            data = yaml.safe_load(fm)
            if not isinstance(data, dict):
                return {}, "pyyaml", "frontmatter is not a mapping"
            return data, "pyyaml", None
        except Exception as exc:  # noqa: BLE001
            return fallback_parse(fm), "fallback-after-pyyaml-error", str(exc).splitlines()[0]
    return fallback_parse(fm), "fallback", None


def top_level_keys(fm: str) -> list[str]:
    return re.findall(r"^([A-Za-z_][A-Za-z0-9_]*):", fm, re.M)


# --- roots ---------------------------------------------------------------------
def project_agent_roots(project_dir: Path) -> list[Path]:
    """`.claude/agents` from project_dir up to the git root (or filesystem root)."""
    roots: list[Path] = []
    cur = project_dir.resolve()
    while True:
        cand = cur / ".claude" / "agents"
        if cand.is_dir():
            roots.append(cand)
        if (cur / ".git").exists() or cur.parent == cur:
            break
        cur = cur.parent
    return roots


def plugin_agent_roots() -> list[Path]:
    cache = HOME / ".claude" / "plugins" / "cache"
    if not cache.is_dir():
        return []
    return [p for p in cache.glob("*/*/*/agents") if p.is_dir()]


def iter_agent_files(root: Path):
    for md in sorted(root.rglob("*.md")):
        if any(part in {"node_modules", ".git", "backups", "evals"} for part in md.relative_to(root).parts):
            continue
        yield md


def load_agent(md: Path) -> dict:
    text = md.read_text(encoding="utf-8", errors="replace")
    fm, body = split_frontmatter(text)
    data, parser, err = parse_frontmatter(fm) if fm is not None else ({}, "none", "no frontmatter")
    return {
        "path": str(md),
        "frontmatter_raw": fm,
        "data": data,
        "body": body,
        "parser": parser,
        "parse_error": err,
        "name": (data.get("name") if isinstance(data, dict) else None) or None,
        "stem": md.stem,
    }


def collect_roster(project_dir: Path) -> list[dict]:
    rows: list[dict] = []
    rank = 3
    for root in project_agent_roots(project_dir):
        for md in iter_agent_files(root):
            a = load_agent(md)
            rows.append({**a, "scope": "project", "rank": rank, "root": str(root)})
    user_root = HOME / ".claude" / "agents"
    if user_root.is_dir():
        for md in iter_agent_files(user_root):
            a = load_agent(md)
            rows.append({**a, "scope": "user", "rank": 4, "root": str(user_root)})
    for root in plugin_agent_roots():
        for md in iter_agent_files(root):
            a = load_agent(md)
            rows.append({**a, "scope": "plugin", "rank": 5, "root": str(root)})
    return rows


def resolve_target(arg: str, project_dir: Path) -> dict | None:
    p = Path(os.path.expanduser(arg))
    if p.is_file():
        a = load_agent(p)
        scope = "user" if str(p.resolve()).startswith(str((HOME / ".claude" / "agents").resolve())) else (
            "plugin" if "/plugins/cache/" in str(p.resolve()) else "project")
        return {**a, "scope": scope, "rank": {"project": 3, "user": 4, "plugin": 5}[scope], "root": str(p.parent)}
    roster = collect_roster(project_dir)
    hits = [r for r in roster if r["name"] == arg or (r["name"] is None and r["stem"] == arg)]
    if not hits:
        hits = [r for r in roster if r["stem"] == arg]
    if not hits:
        return None
    hits.sort(key=lambda r: r["rank"])
    return hits[0]


# --- schema ----------------------------------------------------------------------
def as_list(v) -> list[str]:
    if v is None:
        return []
    if isinstance(v, str):
        return [x.strip() for x in v.split(",") if x.strip()]
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    return []


def skill_path(sid: str, project_dir: Path) -> Path | None:
    cands = [HOME / ".claude" / "skills" / sid / "SKILL.md", project_dir / ".claude" / "skills" / sid / "SKILL.md"]
    cache = HOME / ".claude" / "plugins" / "cache"
    if cache.is_dir():
        cands += list(cache.glob(f"*/*/*/skills/{sid}/SKILL.md"))
    for c in cands:
        if c.is_file():
            return c
    return None


def configured_mcp_servers(project_dir: Path) -> set[str]:
    names: set[str] = set()
    for f in (HOME / ".claude.json", project_dir / ".mcp.json", HOME / ".claude" / "settings.json",
              project_dir / ".claude" / "settings.json", project_dir / ".claude" / "settings.local.json"):
        try:
            d = json.loads(f.read_text())
        except Exception:  # noqa: BLE001
            continue
        if isinstance(d, dict):
            srv = d.get("mcpServers")
            if isinstance(srv, dict):
                names.update(srv.keys())
            projs = d.get("projects")
            if isinstance(projs, dict):
                for pv in projs.values():
                    if isinstance(pv, dict) and isinstance(pv.get("mcpServers"), dict):
                        names.update(pv["mcpServers"].keys())
    return names


def schema(args) -> None:
    project_dir = Path(args.project_dir).resolve()
    path = Path(os.path.expanduser(args.target))
    if not path.is_file():
        fail(f"not a file: {path}")
    a = load_agent(path)
    data, fm, body = a["data"], a["frontmatter_raw"], a["body"]
    findings: list[dict] = []

    def add(p: str, sev: str, check: str, detail: str) -> None:
        findings.append({"pass": p, "severity": sev, "check": check, "detail": detail})

    if fm is None:
        add("L", "High", "frontmatter", "no YAML frontmatter block; the harness cannot read name/description")
    else:
        if "\t" in fm:
            add("L", "High", "frontmatter-tabs", "tab character inside frontmatter (YAML forbids tabs for indentation)")
        keys = top_level_keys(fm)
        dups = sorted({k for k in keys if keys.count(k) > 1})
        if dups:
            add("L", "High", "duplicate-keys", f"duplicate top-level keys: {dups}")
    if a["parse_error"]:
        add("L", "High", "yaml-parse", f"strict parse failed: {a['parse_error']}")

    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        add("B", "High", "name-required", "frontmatter `name` missing or empty (the registry would fall back to the filename stem)")
        name = None
    else:
        if ":" in name:
            add("B", "High", "name-colon", "`name` contains ':' which is reserved for plugin-scoped identifiers")
        if len(name) > 256:
            add("B", "High", "name-length", f"`name` is {len(name)} chars; limit 256")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", name):
            add("B", "Medium", "name-shape", "`name` is not a plain kebab/snake identifier; routing tables and hooks key on it verbatim")
        if name != a["stem"]:
            add("B", "Medium", "name-stem-mismatch", f"`name: {name}` differs from filename stem `{a['stem']}`; roster convention is name == stem")
        if name in BUILTIN_AGENTS:
            add("B", "High", "builtin-name", f"`name: {name}` reuses a built-in agent name")

    desc = data.get("description")
    desc_chars = len(desc) if isinstance(desc, str) else 0
    if not isinstance(desc, str) or not desc.strip():
        add("A", "High", "description-required", "frontmatter `description` missing or empty; the agent cannot be delegated to")
    else:
        if desc_chars > DESC_HARD_CHARS:
            add("A", "High", "description-length", f"description is {desc_chars} chars (> {DESC_HARD_CHARS}); always loaded into every session's context")
        elif desc_chars > DESC_SOFT_CHARS:
            add("A", "Medium", "description-length", f"description is {desc_chars} chars (> {DESC_SOFT_CHARS} soft cap)")
        if re.search(r"(?m)^\s*(\d+\.|-)\s", desc) or re.search(r"\b1\.\s+\S.*\b2\.\s+\S", desc) or re.search(r"\bSteps?\b\s*[:\d]", desc):
            add("A", "Medium", "description-contains-procedure", "description carries numbered or bulleted procedure; move steps to the body")

    unknown = sorted(k for k in data.keys() if k not in SUPPORTED_KEYS and k not in TOLERATED_KEYS)
    for k in unknown:
        add("L", "Medium", "unknown-key", f"frontmatter key `{k}` is not in the supported subagent field table; the harness ignores it silently")

    model = data.get("model")
    if model is not None:
        if not isinstance(model, str) or not (model in MODEL_ALIASES or re.fullmatch(r"claude-[a-z0-9.-]+", model)):
            add("M", "High", "model-value", f"`model: {model!r}` is neither an alias (sonnet/opus/haiku/fable/inherit) nor a claude-* model ID")
    pm = data.get("permissionMode")
    if pm is not None:
        if pm not in PERMISSION_MODES:
            add("I", "High", "permissionMode-value", f"`permissionMode: {pm!r}` not in {sorted(PERMISSION_MODES)}")
        elif pm in {"bypassPermissions", "dontAsk"}:
            add("I", "Medium", "permissionMode-broad", f"`permissionMode: {pm}` needs a stated justification and a narrowed tool grant")
    eff = data.get("effort")
    if eff is not None and eff not in EFFORTS:
        add("M", "High", "effort-value", f"`effort: {eff!r}` not in {sorted(EFFORTS)}")
    col = data.get("color")
    if col is not None and col not in COLORS:
        add("I", "Low", "color-value", f"`color: {col!r}` not in {sorted(COLORS)}")
    mem = data.get("memory")
    if mem is not None and mem not in MEMORY_SCOPES:
        add("I", "High", "memory-value", f"`memory: {mem!r}` not in {sorted(MEMORY_SCOPES)}")
    iso = data.get("isolation")
    if iso is not None and iso != "worktree":
        add("I", "High", "isolation-value", f"`isolation: {iso!r}`; the only supported value is `worktree`")
    for bkey in ("background", "omitClaudeMd"):
        if bkey in data and not isinstance(data[bkey], bool):
            add("L", "High", f"{bkey}-type", f"`{bkey}` must be a YAML boolean, got {data[bkey]!r}")
    mt = data.get("maxTurns")
    if mt is not None and (not isinstance(mt, int) or isinstance(mt, bool) or mt <= 0):
        add("F", "High", "maxTurns-type", f"`maxTurns` must be a positive integer, got {mt!r}")
    acw = data.get("autoCompactWindow")
    if acw is not None and (not isinstance(acw, int) or isinstance(acw, bool) or not 100000 <= acw <= 1000000):
        add("H", "High", "autoCompactWindow-range", f"`autoCompactWindow` must be an integer in 100000..1000000, got {acw!r}")
    exp = data.get("experimental")
    if exp is not None:
        if not isinstance(exp, dict):
            add("H", "Medium", "experimental-type", "`experimental` must be a mapping")
        elif "cacheTtl" in exp and exp["cacheTtl"] not in CACHE_TTLS:
            add("H", "Medium", "cacheTtl-value", f"`experimental.cacheTtl: {exp['cacheTtl']!r}` not in {sorted(CACHE_TTLS)}")
    ip = data.get("initialPrompt")
    if ip is not None and not isinstance(ip, str):
        add("L", "Medium", "initialPrompt-type", "`initialPrompt` must be a string")
    hooks = data.get("hooks")
    if hooks is not None and not isinstance(hooks, dict):
        add("I", "High", "hooks-type", "`hooks` must be a mapping of event name to hook list")

    tools = as_list(data.get("tools")) if "tools" in data else None
    disallowed = as_list(data.get("disallowedTools")) if "disallowedTools" in data else []
    unresolved: list[str] = []
    if tools is not None:
        if not tools:
            add("G", "High", "tools-empty", "`tools` is present but empty; the subagent would spawn with zero tools")
        for t in tools:
            base = t.split("(", 1)[0]
            if base == "Skill":
                add("G", "Medium", "skill-in-tools", "`Skill` listed in `tools`; preload with the `skills:` field instead (the Skill tool is available regardless)")
            if base not in KNOWN_TOOLS and not base.startswith("mcp__"):
                unresolved.append(t)
        if tools and len(unresolved) == len(tools):
            add("G", "High", "tools-unresolved-all", f"no `tools` entry resolves to a known tool: {tools}; the agent fails to launch with zero tools")
        elif unresolved:
            add("G", "Medium", "tools-unresolved", f"unresolved `tools` entries (verify against the live tool list): {unresolved}")
    for t in disallowed:
        if "(" in t:
            add("G", "Medium", "disallowed-specifier", f"`disallowedTools` entry `{t}` carries a specifier; the harness removes the whole tool, not the pattern")
    read_only_claim = bool(re.search(r"(?im)^(mode:\s*read-only|.*\bread-only\b.*)$", body))
    write_grant = tools is None or any(t.split("(")[0] in WRITE_TOOLS for t in tools)
    if read_only_claim and tools is None:
        add("G", "High", "read-only-inherits-all", "body declares read-only but `tools` is omitted (inherits every tool incl. Write/Edit/Bash)")
    elif read_only_claim and write_grant and not any(t.split("(")[0] in WRITE_TOOLS for t in disallowed):
        add("G", "High", "read-only-with-write-tools", "body declares read-only but Write/Edit/NotebookEdit remain granted")

    skills = as_list(data.get("skills"))
    preload_tokens = 0
    for sid in skills:
        sp = skill_path(sid, project_dir)
        if sp is None:
            add("H", "High", "skill-preload-missing", f"`skills:` entry `{sid}` resolves to no SKILL.md under ~/.claude/skills, the project, or the plugin cache")
        else:
            preload_tokens += est_tokens(sp.read_text(encoding="utf-8", errors="replace"))
    if preload_tokens > PRELOAD_HARD_TOKENS:
        add("H", "High", "skills-preload-budget", f"preloaded skills inject ~{preload_tokens} tokens at every start (> {PRELOAD_HARD_TOKENS})")
    elif preload_tokens > PRELOAD_SOFT_TOKENS:
        add("H", "Medium", "skills-preload-budget", f"preloaded skills inject ~{preload_tokens} tokens at every start (> {PRELOAD_SOFT_TOKENS})")

    mcp = data.get("mcpServers")
    if mcp is not None:
        configured = configured_mcp_servers(project_dir)
        entries = mcp if isinstance(mcp, list) else ([mcp] if isinstance(mcp, dict) else [])
        for e in entries:
            if isinstance(e, str):
                if e not in configured:
                    add("H", "Medium", "mcp-server-unknown", f"`mcpServers` entry `{e}` is not configured in ~/.claude.json, .mcp.json or settings")
            elif isinstance(e, dict):
                blob = json.dumps(e)
                for label, rx in SECRET_PATTERNS:
                    if rx.search(blob):
                        add("J", "High", "mcp-inline-secret", f"inline MCP definition contains a {label}; reference an env var instead")
                        break

    # body heuristics
    body_tokens = est_tokens(body)
    if not body.strip():
        add("N", "High", "body-empty", "system-prompt body is empty")
    elif body_tokens > BODY_HARD_TOKENS:
        add("N", "High", "body-length", f"body ~{body_tokens} tokens (> {BODY_HARD_TOKENS}); extract reference material to a preloaded or on-demand skill")
    elif body_tokens > BODY_SOFT_TOKENS:
        add("N", "Medium", "body-length", f"body ~{body_tokens} tokens (> {BODY_SOFT_TOKENS} soft budget)")
    if ASK_USER_PATTERNS.search(body) and (data.get("background") is True):
        add("E", "High", "asks-user-in-background", "body asks the user for input but `background: true` means nobody can answer; return status blocked instead")
    elif ASK_USER_PATTERNS.search(body):
        add("E", "Medium", "asks-user", "body asks the user / waits for confirmation; a subagent should return `blocked` naming the question")
    for label, rx in SECRET_PATTERNS:
        for i, line in enumerate(body.splitlines(), 1):
            if rx.search(line):
                add("J", "High", "secret-in-body", f"{label} at body line {i}; redact and move to the environment")
                break
    if "Agent" in (tools or []) and not re.search(r"(?i)recurs|do not (re-)?delegate|never (spawn|delegate)|delegate only", body):
        add("F", "High", "agent-tool-without-rule", "`Agent` is granted but the body states no delegation rule (when to delegate, never to itself or its caller)")
    has_version = bool(re.search(r"(?im)^(definition version|version):\s*\S+", body)) or "version" in data
    has_receipt = bool(re.search(r"(?i)receipt|final (report|message)|return (a|the) (summary|report|json)", body))

    highs = sum(1 for f in findings if f["severity"] == "High")
    emit({
        "subcommand": "schema",
        "path": str(path),
        "yaml_parser": a["parser"],
        "name": name,
        "scope_guess": "user" if "/.claude/agents/" in str(path.resolve()) and str(path.resolve()).startswith(str(HOME)) else "project-or-other",
        "keys": sorted(data.keys()),
        "unknown_keys": unknown,
        "description_chars": desc_chars,
        "description_tokens_est": est_tokens(desc or ""),
        "body_tokens_est": body_tokens,
        "preload_tokens_est": preload_tokens,
        "tools": tools,
        "disallowedTools": disallowed,
        "has_version_marker": has_version,
        "mentions_output_contract": has_receipt,
        "findings": findings,
        "counts": {"High": highs, "Medium": sum(1 for f in findings if f["severity"] == "Medium"),
                   "Low": sum(1 for f in findings if f["severity"] == "Low")},
    }, 2 if highs else 0)


# --- roster ----------------------------------------------------------------------
def roster(args) -> None:
    project_dir = Path(args.project_dir).resolve()
    rows = collect_roster(project_dir)
    by_name: dict[str, list[dict]] = {}
    non_agents: list[str] = []
    for r in rows:
        if r["name"] is None and not r["data"].get("description"):
            non_agents.append(r["path"])
        key = r["name"] or r["stem"]
        by_name.setdefault(key, []).append(r)
    agents = []
    total_desc_chars = 0
    for key, lst in sorted(by_name.items()):
        lst.sort(key=lambda r: r["rank"])
        winner = lst[0]
        # Several plugin-cache copies of one plugin (different cached versions) sit at the
        # same rank and are not shadowing; only a copy of another scope behind the winner is.
        losers = [x for x in lst[1:] if x["rank"] != winner["rank"] or x["scope"] != "plugin"]
        cache_versions = [x["path"] for x in lst[1:] if x["rank"] == winner["rank"] and x["scope"] == "plugin"]
        d = winner["data"].get("description") or ""
        if winner["scope"] != "plugin":
            total_desc_chars += len(d) if isinstance(d, str) else 0
        agents.append({
            "name": key,
            "winner": winner["path"],
            "scope": winner["scope"],
            "description_chars": len(d) if isinstance(d, str) else 0,
            "shadowed": [x["path"] for x in losers],
            "plugin_cache_versions": cache_versions,
            "builtin_collision": key in BUILTIN_AGENTS,
            "nested": Path(winner["path"]).parent != Path(winner["root"]),
            "model": winner["data"].get("model"),
            "tools": as_list(winner["data"].get("tools")) if "tools" in winner["data"] else None,
            "parse_error": winner["parse_error"],
        })
    emit({
        "subcommand": "roster",
        "project_dir": str(project_dir),
        "roots": {"project": [str(p) for p in project_agent_roots(project_dir)],
                  "user": str(HOME / ".claude" / "agents"),
                  "plugin": [str(p) for p in plugin_agent_roots()]},
        "agent_count": len(agents),
        "description_total_chars": total_desc_chars,
        "description_total_tokens_est": est_tokens("x" * total_desc_chars),
        "description_budget_tokens": ROSTER_BUDGET_TOKENS,
        "over_budget": est_tokens("x" * total_desc_chars) > ROSTER_BUDGET_TOKENS,
        "shadowing": [a for a in agents if a["shadowed"]],
        "builtin_collisions": [a["name"] for a in agents if a["builtin_collision"]],
        "nested_files": [a["winner"] for a in agents if a["nested"]],
        "non_agent_markdown_under_roots": non_agents,
        "agents": agents,
    })


# --- refs ------------------------------------------------------------------------
def refs(args) -> None:
    project_dir = Path(args.project_dir).resolve()
    name = args.name
    targets: list[Path] = []
    for root in [HOME / ".claude" / "agents", HOME / ".claude" / "rules", HOME / ".claude" / "hooks",
                 HOME / ".claude" / "commands", project_dir / ".claude"]:
        if root.is_dir():
            targets += [p for p in root.rglob("*") if p.is_file() and p.suffix in {".md", ".py", ".json", ".mjs", ".js", ".yaml", ".yml", ".sh"}
                        and "node_modules" not in p.parts]
    skills_root = HOME / ".claude" / "skills"
    if skills_root.is_dir():
        targets += list(skills_root.glob("*/SKILL.md"))
        targets += list(skills_root.glob("*/references/*.md"))
    rx = re.compile(r"(?<![A-Za-z0-9_-])" + re.escape(name) + r"(?![A-Za-z0-9_-])")
    hits: list[dict] = []
    for p in targets:
        try:
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:  # noqa: BLE001
            continue
        if p.name == f"{name}.md" and p.parent.name == "agents":
            continue  # the definition itself
        nums = [i for i, ln in enumerate(lines, 1) if rx.search(ln)]
        if nums:
            hits.append({"path": str(p), "lines": nums[:20], "count": len(nums)})
    routing_rule = HOME / ".claude" / "rules" / "workflow-agent-routing.md"
    router_hook = HOME / ".claude" / "hooks" / "workflow-agent-router.py"
    emit({
        "subcommand": "refs",
        "name": name,
        "in_routing_rules_table": bool(routing_rule.is_file() and rx.search(routing_rule.read_text(errors="replace"))),
        "in_router_hook_routes": bool(router_hook.is_file() and rx.search(router_hook.read_text(errors="replace"))),
        "reference_count": sum(h["count"] for h in hits),
        "files": hits,
    })


# --- tokens ----------------------------------------------------------------------
def tokens(args) -> None:
    project_dir = Path(args.project_dir).resolve()
    path = Path(os.path.expanduser(args.target))
    if not path.is_file():
        fail(f"not a file: {path}")
    a = load_agent(path)
    data = a["data"]
    desc_t = est_tokens(data.get("description") or "")
    body_t = est_tokens(a["body"])
    preload = {}
    for sid in as_list(data.get("skills")):
        sp = skill_path(sid, project_dir)
        preload[sid] = est_tokens(sp.read_text(encoding="utf-8", errors="replace")) if sp else None
    claude_md = 0
    if data.get("omitClaudeMd") is not True:
        for f in (HOME / ".claude" / "CLAUDE.md", project_dir / "CLAUDE.md", project_dir / ".claude" / "CLAUDE.md"):
            if f.is_file():
                claude_md += est_tokens(f.read_text(encoding="utf-8", errors="replace"))
    startup = body_t + sum(v or 0 for v in preload.values()) + claude_md
    emit({
        "subcommand": "tokens",
        "path": str(path),
        "description_tokens_est": desc_t,
        "body_tokens_est": body_t,
        "preloaded_skills_tokens_est": preload,
        "claude_md_tokens_est": claude_md,
        "omitClaudeMd": data.get("omitClaudeMd") is True,
        "startup_context_tokens_est": startup,
        "note": "chars/4 estimate; managed policy files and the harness system prompt are not counted",
    })


# --- smoke -----------------------------------------------------------------------
def smoke(args) -> None:
    project_dir = Path(args.cwd).resolve()
    target = args.target
    name = target
    p = Path(os.path.expanduser(target))
    if p.is_file():
        a = load_agent(p)
        name = a["name"] or a["stem"]
    exe = shutil.which("claude")
    if not exe:
        emit({"subcommand": "smoke", "status": "blocked", "reason": "claude CLI not on PATH"}, 1)
    prompt = "Reply with exactly the single word READY and nothing else. Do not use any tool."
    cmd = [exe, "-p", prompt, "--agent", name, "--max-turns", "1", "--output-format", "json"]
    if args.agents_json:
        cmd += ["--agents", args.agents_json]
    # Deny every side-effecting tool for the probe; the question needs none.
    cmd += ["--disallowedTools", "Bash", "Write", "Edit", "NotebookEdit", "WebFetch", "WebSearch", "Agent",
            "SendMessage", "Artifact"]
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, cwd=str(project_dir), capture_output=True, text=True, timeout=args.timeout)
    except subprocess.TimeoutExpired:
        emit({"subcommand": "smoke", "agent": name, "status": "blocked", "reason": f"timeout after {args.timeout}s",
              "command": cmd}, 1)
    out = proc.stdout.strip()
    result_text = None
    cost = None
    try:
        j = json.loads(out)
        if isinstance(j, dict):
            result_text = j.get("result")
            cost = j.get("total_cost_usd")
        elif isinstance(j, list):
            for ev in j:
                if isinstance(ev, dict) and ev.get("type") == "result":
                    result_text, cost = ev.get("result"), ev.get("total_cost_usd")
    except Exception:  # noqa: BLE001
        result_text = out[-500:]
    ready = isinstance(result_text, str) and result_text.strip().strip(".").upper() == "READY"
    emit({
        "subcommand": "smoke",
        "agent": name,
        "status": "ready" if (proc.returncode == 0 and ready) else ("loaded-but-off-script" if proc.returncode == 0 else "failed"),
        "exit_code": proc.returncode,
        "result": result_text,
        "total_cost_usd": cost,
        "seconds": round(time.time() - t0, 1),
        "stderr_tail": proc.stderr.strip()[-800:],
        "command": cmd,
    }, 0 if proc.returncode == 0 else 2)


# --- backup ----------------------------------------------------------------------
def backup(args) -> None:
    src = Path(os.path.expanduser(args.source_override or args.target))
    target = Path(os.path.expanduser(args.target))
    if not src.is_file():
        fail(f"not a file: {src}")
    run_dir = BACKUP_ROOT / f"agent-deep-optimizer-{args.run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)
    dest_name = target.name + (f".iter{args.iter}" if args.iter is not None else "")
    dest = run_dir / dest_name
    shutil.copy2(src, dest)
    emit({
        "subcommand": "backup",
        "backup": str(dest),
        "restore_command": f"cp {dest} {target}",
    })


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("schema"); s.add_argument("target"); s.add_argument("--project-dir", default=os.getcwd()); s.set_defaults(fn=schema)
    s = sub.add_parser("roster"); s.add_argument("--project-dir", default=os.getcwd()); s.set_defaults(fn=roster)
    s = sub.add_parser("refs"); s.add_argument("name"); s.add_argument("--project-dir", default=os.getcwd()); s.set_defaults(fn=refs)
    s = sub.add_parser("tokens"); s.add_argument("target"); s.add_argument("--project-dir", default=os.getcwd()); s.set_defaults(fn=tokens)
    s = sub.add_parser("smoke"); s.add_argument("target"); s.add_argument("--cwd", default=os.getcwd())
    s.add_argument("--timeout", type=int, default=180); s.add_argument("--agents-json", default=None); s.set_defaults(fn=smoke)
    s = sub.add_parser("backup"); s.add_argument("target")
    s.add_argument("--run-id", default=datetime.now().strftime("%Y%m%d-%H%M%S"))
    s.add_argument("--iter", type=int, default=None); s.add_argument("--from", dest="source_override", default=None); s.set_defaults(fn=backup)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
