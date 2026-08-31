"""usage.py — token-usage accounting + hub-leverage savings estimates.

Sources:
- Claude Code transcripts (~/.claude/projects/**/*.jsonl): every assistant
  entry carries message.model + message.usage (input / output /
  cache_creation / cache_read tokens) and any tool_use blocks. Records are
  deduped on requestId — the same request can be journaled more than once.
- Hub leverage = calls to the hub's semantic surfaces (mcp__global_ai_hub__*
  tools) and Skill invocations of locally installed skills.

Cost model: PRICES maps model-substring -> (input, output) USD per MTok;
cache reads bill at 10% of input, cache writes at 125% (5m TTL) / 200%
(1h TTL). Edit PRICES when Anthropic pricing changes.

Savings model (estimates, clearly labeled in the UI):
- A semantic query (hub_query_docset / hub_search_codebase /
  hub_memory_search) returns ~CHUNK_TOKENS of context. The naive
  alternative is ingesting the whole corpus document — approximated by the
  mean mirror-file size in tokens (bytes/4), capped at NAIVE_CAP_TOKENS.
- A skill invocation loads the skill's markdown (~size/4 tokens) instead of
  re-deriving from its source corpus (same mirror-size approximation).
Savings are priced at the calling model's uncached input rate.
"""

from __future__ import annotations

import datetime
import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from . import core

CLAUDE_DIR = Path(os.environ.get("CLAUDE_HOME", Path.home() / ".claude"))
PROJECTS_DIR = CLAUDE_DIR / "projects"
SKILLS_DIR = CLAUDE_DIR / "skills"

HUB_TOOL_PREFIX = "mcp__global_ai_hub__"
SEMANTIC_TOOLS = {"hub_query_docset", "hub_search_codebase", "hub_memory_search"}

CHUNK_TOKENS = 800          # ~top-5 retrieved chunks
NAIVE_CAP_TOKENS = 150_000  # naive full-doc ingestion capped by context window
MAX_FILES = 400             # newest transcript files scanned per report
MAX_LINE_BYTES = 2_000_000  # skip pathological lines (embedded blobs)

# USD per MTok (input, output) — verify against current Anthropic pricing.
PRICES = {
    "fable": (15.0, 75.0),
    "mythos": (15.0, 75.0),
    "opus": (15.0, 75.0),
    "sonnet": (3.0, 15.0),
    "haiku": (1.0, 5.0),
}
CACHE_READ_MULT = 0.10
CACHE_WRITE_5M_MULT = 1.25
CACHE_WRITE_1H_MULT = 2.00


@dataclass
class ModelUsage:
    model: str
    requests: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read: int = 0
    cache_write_5m: int = 0
    cache_write_1h: int = 0

    @property
    def cost(self) -> float:
        pin, pout = price_for(self.model)
        return (self.input_tokens * pin
                + self.output_tokens * pout
                + self.cache_read * pin * CACHE_READ_MULT
                + self.cache_write_5m * pin * CACHE_WRITE_5M_MULT
                + self.cache_write_1h * pin * CACHE_WRITE_1H_MULT) / 1e6


@dataclass
class LeverageEvent:
    kind: str    # "tool" | "skill"
    name: str
    model: str
    count: int = 0
    saved_tokens: int = 0

    def saved_cost(self) -> float:
        return self.saved_tokens * price_for(self.model)[0] / 1e6


@dataclass
class UsageReport:
    days: int
    files_scanned: int
    models: dict[str, ModelUsage] = field(default_factory=dict)
    leverage: dict[tuple[str, str], LeverageEvent] = field(default_factory=dict)

    @property
    def total_cost(self) -> float:
        return sum(m.cost for m in self.models.values())

    @property
    def total_saved(self) -> float:
        return sum(e.saved_cost() for e in self.leverage.values())


def price_for(model: str) -> tuple[float, float]:
    low = model.lower()
    for key, pair in PRICES.items():
        if key in low:
            return pair
    return PRICES["sonnet"]  # unknown model: mid-tier assumption


def _mirror_avg_tokens() -> int:
    """Mean mirror-file size in tokens across both mirror dirs (bytes/4)."""
    sizes = []
    for d in (core.MIRROR_OUT_DIR, core.MIRROR_SKILL_DIR / "text-mirror"):
        if not d.is_dir():
            continue
        for f in d.glob("*.md"):
            try:
                sizes.append(f.stat().st_size)
            except OSError:
                continue
    if not sizes:
        return 40_000  # conservative default when no mirrors exist
    return min(NAIVE_CAP_TOKENS, int(sum(sizes) / len(sizes) / 4))


def _skill_tokens(skill: str) -> int:
    d = SKILLS_DIR / skill
    if not d.is_dir():
        return 0
    total = 0
    for f in d.rglob("*.md"):
        try:
            total += f.stat().st_size
        except OSError:
            continue
    return total // 4


def _transcript_files(cutoff: float) -> list[Path]:
    files = []
    if not PROJECTS_DIR.is_dir():
        return files
    for f in PROJECTS_DIR.glob("*/*.jsonl"):
        try:
            if f.stat().st_mtime >= cutoff:
                files.append(f)
        except OSError:
            continue
    files.sort(key=lambda f: -f.stat().st_mtime)
    return files[:MAX_FILES]


def scan(days: int = 7) -> UsageReport:
    """Aggregate token usage + hub-leverage events over the last N days."""
    cutoff_dt = datetime.datetime.now(datetime.UTC) - \
        datetime.timedelta(days=days)
    cutoff_iso = cutoff_dt.isoformat()
    report = UsageReport(days=days, files_scanned=0)
    naive_tokens = _mirror_avg_tokens()
    seen_requests: set[str] = set()
    skill_cache: dict[str, int] = {}

    for path in _transcript_files(cutoff_dt.timestamp()):
        report.files_scanned += 1
        try:
            fh = path.open("r", errors="replace")
        except OSError:
            continue
        with fh:
            for line in fh:
                if len(line) > MAX_LINE_BYTES or '"assistant"' not in line:
                    continue  # cheap prefilter before the real JSON parse
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if entry.get("type") != "assistant":
                    continue
                ts = entry.get("timestamp", "")
                if ts and ts.replace("Z", "+00:00") < cutoff_iso:
                    continue
                msg = entry.get("message") or {}
                model = msg.get("model", "unknown")
                req = entry.get("requestId") or entry.get("uuid", "")
                usage = msg.get("usage") or {}
                if usage and req and req not in seen_requests:
                    seen_requests.add(req)
                    mu = report.models.setdefault(model, ModelUsage(model))
                    mu.requests += 1
                    mu.input_tokens += usage.get("input_tokens", 0) or 0
                    mu.output_tokens += usage.get("output_tokens", 0) or 0
                    mu.cache_read += usage.get("cache_read_input_tokens", 0) or 0
                    breakdown = usage.get("cache_creation") or {}
                    if breakdown:
                        mu.cache_write_5m += breakdown.get(
                            "ephemeral_5m_input_tokens", 0) or 0
                        mu.cache_write_1h += breakdown.get(
                            "ephemeral_1h_input_tokens", 0) or 0
                    else:
                        mu.cache_write_5m += usage.get(
                            "cache_creation_input_tokens", 0) or 0
                for block in msg.get("content") or []:
                    if not isinstance(block, dict) or \
                            block.get("type") != "tool_use":
                        continue
                    name = block.get("name", "")
                    if name.startswith(HUB_TOOL_PREFIX):
                        tool = name.removeprefix(HUB_TOOL_PREFIX)
                        ev = report.leverage.setdefault(
                            ("tool", tool), LeverageEvent("tool", tool, model))
                        ev.count += 1
                        if tool in SEMANTIC_TOOLS:
                            ev.saved_tokens += max(0, naive_tokens - CHUNK_TOKENS)
                    elif name == "Skill":
                        skill = (block.get("input") or {}).get("skill", "")
                        if not skill:
                            continue
                        if skill not in skill_cache:
                            skill_cache[skill] = _skill_tokens(skill)
                        if skill_cache[skill] == 0:
                            continue  # not an installed skill dir
                        ev = report.leverage.setdefault(
                            ("skill", skill),
                            LeverageEvent("skill", skill, model))
                        ev.count += 1
                        ev.saved_tokens += max(
                            0, naive_tokens - skill_cache[skill])
    return report
