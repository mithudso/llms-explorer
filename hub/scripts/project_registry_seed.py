#!/usr/bin/env python3
"""project_registry_seed.py — discover repos and auto-populate project_registry.db
with objective, verifiable facts only (remote URL, README/CLAUDE.md opening line,
memory/llms files present, launchd/package.json activation commands found on
disk). Never invents purpose prose or outstanding items — those need a human
or an agent that actually reads the project, not a glob.

This is what project-registrar (the maintainer agent) re-runs to pick up new
or moved repos; it is safe to re-run any time (idempotent upserts).

Usage:
  ~/.global-ai-hub/.venv/bin/python scripts/project_registry_seed.py [--apply]
  (default is a dry-run report; --apply writes to project_registry.db)
"""

from __future__ import annotations

import argparse
import json
import plistlib
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import project_manager as pm  # noqa: E402

HOME = Path.home()

# Scan order matters: earlier roots win when the same git remote shows up
# twice (e.g. a ~/dev canonical clone and a ~/Downloads worktree/scratch copy).
SCAN_ROOTS = [
    (HOME / "dev", 2),
    (HOME / ".claude", 1),
    (HOME / ".global-ai-hub", 2),
    # A second, older working-repo tree (MongoDB support-tools ecosystem:
    # ts-tools-*, atlas-tools, mtools, triage-scripts, ...) that predates
    # ~/dev and was never added to the hub's watch_dirs.txt — found missing
    # entirely on the first seed pass.
    (HOME / "Documents" / "GitHub", 2),
    # Depth 2 only: Downloads also holds dated project archives several
    # levels deeper (10_Projects_and_Bundles/2026/Projects/<name>/.git, e.g.
    # customer-dashboard-ext) and stray nested Drive-download folders that
    # happen to contain a .git — a depth-4 pass found both, with no reliable
    # way to tell a real relocated project from download noise by path shape
    # alone. Known deep-archive projects are registered by hand (or by a
    # future targeted pass); this stays shallow to keep the auto-seed clean.
    (HOME / "Downloads", 2),
]

# Third-party clones that are reference material, not the user's own work —
# tracked would-be noise: no purpose/outstanding/activation of theirs to keep.
EXTERNAL_SKIP_REMOTES = {
    "github.com/tinygrad/tinygrad",
    "github.com/DataDog/dd-agent",
    "github.com/rueckstiess/mtools",
    "github.com/aheckmann/m",
}

NAME_OVERRIDES = {
    # ~/.claude's origin remote IS github.com/mithudso/skills.git — it's a
    # checkout of the "skills" repo at the Claude Code config path, not a
    # distinct "claude-config" project. ~/.global-ai-hub/skills is a second
    # checkout of the same remote and gets deduped away by _normalize_remote;
    # both paths are recorded as separate "checkout" activations below.
    str(HOME / ".claude"): "skills",
    str(HOME / ".global-ai-hub"): "global-ai-hub",
}

def _git(repo: Path, *args: str) -> str:
    try:
        out = subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                             text=True, timeout=10)
        return out.stdout.strip() if out.returncode == 0 else ""
    except Exception:
        return ""


# Full-home sweep (in addition to SCAN_ROOTS above): basenames pruned entirely
# rather than just filtered afterward, so `find` never descends into them —
# these are exactly the directories that make a whole-disk-style git-repo
# search slow and noisy (dependency trees, caches, build output, ephemeral
# per-session worktrees already covered by their parent repo).
NOISE_DIR_NAMES = {
    "node_modules", ".venv", "venv", "env", "vendor", "Library", ".Trash",
    ".cache", "site-packages", "target", "build", "dist", ".npm", ".cargo",
    ".rustup", ".gem", ".tox", ".gradle", ".m2", "Pods", ".git",
    ".claude", ".global-ai-hub",  # already covered by dedicated SCAN_ROOTS entries
}


def _find_repos() -> list[Path]:
    seen: set[Path] = set()
    repos: list[Path] = []

    def _add_from(out: str) -> None:
        for line in out.splitlines():
            repo = Path(line).parent.resolve()
            if repo not in seen:
                seen.add(repo)
                repos.append(repo)

    for root, maxdepth in SCAN_ROOTS:
        if not root.is_dir():
            continue
        try:
            out = subprocess.run(
                ["find", str(root), "-maxdepth", str(maxdepth), "-type", "d", "-name", ".git"],
                capture_output=True, text=True, timeout=30,
            ).stdout
        except Exception:
            continue
        _add_from(out)

    # Broad sweep: every git repo anywhere else under $HOME. Runs after the
    # SCAN_ROOTS pass above (whose results already seeded `seen`), so a repo
    # under e.g. ~/dev is never re-processed here even though ~/dev is itself
    # a descendant of $HOME. `-name X -prune` stops find from ever entering a
    # noise directory, which is what keeps this fast and quiet rather than an
    # unbounded `find /` — this is still scoped to the user's own home, never
    # system paths, other users, or mounted volumes (find doesn't follow
    # symlinks by default, so a mounted volume symlinked into $HOME is listed
    # but not descended into).
    if HOME.is_dir():
        prune_expr: list[str] = []
        for name in NOISE_DIR_NAMES:
            prune_expr += ["-name", name, "-o"]
        prune_expr = prune_expr[:-1]  # drop the trailing dangling -o
        argv = (["find", str(HOME), "("] + prune_expr + [")", "-prune", "-o",
                "-type", "d", "-name", ".git", "-print"])
        try:
            out = subprocess.run(argv, capture_output=True, text=True, timeout=180).stdout
        except Exception:
            out = ""
        _add_from(out)

    return repos


def _normalize_remote(url: str) -> str:
    """git@github.com:org/repo.git and https://github.com/org/repo(.git) both
    normalize to github.com/org/repo, so dedup-by-remote isn't fooled by
    protocol choice."""
    m = re.search(r"github\.com[:/]([^/]+/[^/.]+)", url)
    return f"github.com/{m.group(1)}" if m else url


def _readme_opening_line(repo: Path) -> str:
    for fname in ("README.md", "CLAUDE.md", "AGENTS.md"):
        f = repo / fname
        if not f.is_file():
            continue
        try:
            for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.strip()
                if not line or line.startswith(("#", "---", "```")):
                    continue
                line = re.sub(r"[*_`]", "", line)
                return line[:300]
        except OSError:
            continue
    return ""


def _find_files(repo: Path) -> list[tuple[str, str]]:
    """(file_type, relative_path) for memory files and llms.txt exports found
    at shallow depth — deep scans belong to the agent's targeted follow-up,
    not a blind seed pass."""
    found = []
    for pattern, ftype in (
        ("MEMORY.md", "memory"), ("memory-*.md", "memory"), (".remember/*.md", "memory"),
        ("llms.txt", "llms_txt"), ("llms-full.txt", "llms_txt"),
        ("*.llms/manifest.json", "llms_txt"), ("*.llms/llms.txt", "llms_txt"),
        ("README.md", "readme"), ("CLAUDE.md", "doc"), ("AGENTS.md", "doc"),
    ):
        for f in repo.glob(pattern):
            if f.is_file():
                found.append((ftype, str(f.relative_to(repo))))
    return found


def _package_json_activation(repo: Path) -> tuple[str, str] | None:
    pkg = repo / "package.json"
    if not pkg.is_file():
        return None
    try:
        data = json.loads(pkg.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    scripts = data.get("scripts") or {}
    for key in ("start", "dev"):
        if key in scripts:
            cmd = "npm run start" if key == "start" else "npm run dev"
            return cmd, f"package.json scripts.{key}"
    return None


def _launchd_activation(repo: Path) -> list[tuple[str, str, str]]:
    """(label, command, description) for every LaunchAgents plist whose
    ProgramArguments array references this repo's path — parsed structurally
    (plistlib) rather than by regexing raw XML, so the extracted command is
    exactly ProgramArguments, never a stray Label/EnvironmentVariables string
    that happens to also contain a path."""
    out = []
    la_dir = HOME / "Library" / "LaunchAgents"
    if not la_dir.is_dir():
        return out
    repo_str = str(repo)
    for plist in la_dir.glob("*.plist"):
        try:
            data = plistlib.loads(plist.read_bytes())
        except Exception:  # malformed plist (ExpatError), unreadable, or not a dict
            continue
        args = data.get("ProgramArguments") or []
        if not any(repo_str in str(a) for a in args):
            continue
        label = data.get("Label") or plist.stem
        cmd = " ".join(str(a) for a in args) if args else f"launchctl start {label}"
        out.append((f"launchd:{label}", cmd, str(plist)))
    return out


def survey_one(repo: Path) -> dict:
    name = NAME_OVERRIDES.get(str(repo), repo.name)
    remote = _git(repo, "remote", "get-url", "origin")
    last_commit_epoch = _git(repo, "log", "-1", "--format=%ct")
    last_commit_iso = ""
    status = "active"
    if last_commit_epoch.isdigit():
        age_days = (time.time() - int(last_commit_epoch)) / 86400
        last_commit_iso = time.strftime("%Y-%m-%d", time.gmtime(int(last_commit_epoch)))
        status = "active" if age_days < 90 else ("stable" if age_days < 365 else "paused")
    purpose = _readme_opening_line(repo)
    files = _find_files(repo)
    activations = []
    pkg_act = _package_json_activation(repo)
    if pkg_act:
        activations.append(("npm-" + pkg_act[0].split()[-1], pkg_act[0], pkg_act[1]))
    activations.extend(_launchd_activation(repo))
    return {
        "name": name, "path": str(repo), "remote": remote,
        "last_commit": last_commit_iso, "status": status, "purpose": purpose,
        "files": files, "activations": activations,
    }


def run_discovery(apply: bool = False) -> list[dict]:
    """Discover every repo under the SCAN_ROOTS + full-home sweep, dedup by
    remote and disambiguate name collisions, and — if apply — upsert each
    into project_registry.db. Returns the survey records either way, so a
    caller (CLI or an MCP tool) can report on a dry run too. This is the
    callable form of what main() below drives from argv."""
    by_remote: dict[str, Path] = {}
    extra_checkouts: dict[str, list[Path]] = {}
    records = []
    for repo in _find_repos():
        remote = _normalize_remote(_git(repo, "remote", "get-url", "origin"))
        if remote in EXTERNAL_SKIP_REMOTES:
            continue
        if remote and remote in by_remote:
            # Duplicate clone/worktree of an already-scanned repo — not a
            # separate project, but its path is worth surfacing so "how do I
            # get to the other checkout" doesn't require a filesystem hunt.
            extra_checkouts.setdefault(remote, []).append(repo)
            continue
        if remote:
            by_remote[remote] = repo
        records.append(survey_one(repo))

    # project_manager.upsert_project keys on name alone — two distinct repos
    # sharing a basename (common under scratch/download folders) would
    # otherwise silently overwrite each other's record on --apply. Disambiguate
    # with the parent directory name rather than dropping either one.
    by_name: dict[str, list[dict]] = {}
    for rec in records:
        by_name.setdefault(rec["name"], []).append(rec)
    for name, group in by_name.items():
        if len(group) > 1:
            for rec in group:
                rec["name"] = f"{name} ({Path(rec['path']).parent.name})"

    for rec in records:
        remote = _normalize_remote(rec["remote"])
        for i, other in enumerate(extra_checkouts.get(remote, []), start=1):
            rec["activations"].append(
                (f"checkout-{i}", f"cd {other}", "additional working copy on disk"))

    if not apply:
        return records

    pm.init_db()
    for rec in records:
        pm.upsert_project(rec["name"], kind="repo", path=rec["path"], remote=rec["remote"],
                          purpose=rec["purpose"], status=rec["status"])
        for ftype, relpath in rec["files"]:
            pm.add_file(rec["name"], relpath, ftype)
        for label, command, desc in rec["activations"]:
            pm.set_activation(rec["name"], command, label=label, description=desc)
        pm.log_action(rec["name"], "seeded", f"auto-survey, last_commit={rec['last_commit']}")
    return records


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true",
                    help="write to project_registry.db (default: dry-run report)")
    args = ap.parse_args()
    records = run_discovery(apply=args.apply)
    if not args.apply:
        print(json.dumps(records, indent=2, ensure_ascii=False))
        print(f"\n{len(records)} repos found (dry run — pass --apply to write)", file=sys.stderr)
        return
    print(f"seeded {len(records)} projects into {pm.DB_FILE}")


if __name__ == "__main__":
    main()
