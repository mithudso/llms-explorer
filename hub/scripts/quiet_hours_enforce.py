#!/usr/bin/env python3
"""quiet_hours_enforce.py — hand a box back to its owner, and take it back.

Excluding a box from future dispatch (box_schedule, wired into
pipeline_manager and embed_core) does nothing about what is ALREADY running on
it: a distill started at 08:50 keeps every core busy until 17:00, and a 30B
model stays resident in RAM regardless. This does the eviction.

On `quiet` for a box now inside its window:
  1. kill in-flight hub work (text_mirror.py / distill_offline.py)
  2. unload every loaded Ollama model, freeing its RAM/VRAM
  3. stop the background hub daemons (idle-indexer, hub-daemon, MCP HTTP)

On `resume`, the daemons are started again. Models are NOT preloaded — Ollama
pulls them into memory on the next request, so there is nothing to restore.

Both directions are idempotent and safe to run on a box that is already in the
requested state.

Usage:
  quiet_hours_enforce.py quiet  [--host H] [--dry-run]
  quiet_hours_enforce.py resume [--host H] [--dry-run]
  quiet_hours_enforce.py status
"""

from __future__ import annotations

import argparse
import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import box_schedule  # noqa: E402

# Work the hub starts on a remote box; killed by pattern, never by blanket
# pkill, so nothing of the owner's is touched.
WORK_PATTERNS = ("text_mirror.py", "distill_offline.py")
# Hub services are DISCOVERED on the box, not hardcoded. A hardcoded list of
# three labels missed two real jobs on the first run here
# (com.global-ai.artifact-sync and com.global-ai.indexer), and the `|| true`
# on each command meant the misses reported success while the box stayed busy.
# Which background jobs count as "hub work" on a box. Configurable, because
# the set is not knowable from here: com.antigravity.skills-autosync was
# copying the entire 4.7GB text-mirror corpus on a loop and matched no
# global-ai pattern at all.
DEFAULT_LAUNCHD_PATTERNS = ("*global-ai*", "*antigravity.skills-autosync*")
SYSTEMD_PATTERNS = ("hub-daemon", "idle-indexer", "hub-mcp-http",
                    "hub-", "global-ai")


def _launchd_patterns() -> tuple[str, ...]:
    try:
        from hub_manager import settings as hm_settings
        configured = hm_settings.load().get("quiet_hours_launchd_patterns")
    except Exception:  # noqa: BLE001
        configured = None
    if isinstance(configured, list) and configured:
        return tuple(str(c) for c in configured)
    return DEFAULT_LAUNCHD_PATTERNS


def _remotes():
    from hub_manager import remotes as hm_remotes
    return hm_remotes


def _target_for(host: str) -> str | None:
    import pipeline_manager as pm
    for label, target in pm.remote_targets():
        if label == host or host in label:
            return target
    return None


def _is_macos(target: str) -> bool:
    ok, out = _remotes().run_ssh(target, "uname -s", timeout=20)
    return ok and "Darwin" in out


def discover_services(target: str) -> list[str]:
    """Hub service labels/units actually present on the box."""
    hm = _remotes()
    if _is_macos(target):
        globs = " ".join(f'$HOME/Library/LaunchAgents/{g}.plist'
                         for g in _launchd_patterns())
        ok, out = hm.run_ssh(
            target,
            f'for f in {globs}; do [ -f "$f" ] && basename "$f" .plist; done',
            timeout=30)
        return [ln.strip() for ln in out.splitlines() if ln.strip().startswith("com.")] if ok else []
    pattern = "|".join(SYSTEMD_PATTERNS)
    ok, out = hm.run_ssh(
        target,
        f"systemctl --user list-unit-files --no-legend 2>/dev/null "
        f"| grep -E '{pattern}' | awk '{{print $1}}'", timeout=30)
    return [ln.strip() for ln in out.splitlines() if ln.strip().endswith(".service")] if ok else []


def _service_cmds(target: str, action: str) -> list[tuple[str, str]]:
    """(label, command) pairs to stop/start every hub service on the box."""
    services = discover_services(target)
    if not services:
        return [("services", "true  # none discovered")]
    if _is_macos(target):
        if action == "stop":
            return [(s, f"launchctl bootout gui/$(id -u)/{s}") for s in services]
        return [(s, f"launchctl bootstrap gui/$(id -u) "
                    f"$HOME/Library/LaunchAgents/{s}.plist") for s in services]
    return [(s, f"systemctl --user {action} {s}") for s in services]


def _kill_work_targeting(quiet_host: str, dry_run: bool) -> None:
    """Stop hub work on OTHER boxes that embeds against the quiet one.

    Silencing a box is not the same as stopping work aimed at it. A distill
    running on box A with OLLAMA_HOST pointed at box B keeps B's llama-server
    resident and its cores busy, no matter what B itself is running — which is
    exactly what was still pinning the work laptop after the first eviction
    reported success on every step.
    """
    import pipeline_manager as pm
    hm = _remotes()
    for label, target in pm.remote_targets():
        if quiet_host in label:
            continue  # the quiet box itself is handled by the caller
        # /proc on Linux; ps -E exposes the environment on macOS
        probe = (
            "for p in $(pgrep -f 'distill_offline|text_mirror' 2>/dev/null); do "
            f"  if tr '\\0' '\\n' < /proc/$p/environ 2>/dev/null | grep -q {quiet_host}; then echo $p; fi; "
            "done 2>/dev/null; "
            f"ps -E -o pid=,command= 2>/dev/null | grep -E 'distill_offline|text_mirror' "
            f"| grep {quiet_host} | awk '{{print $1}}'")
        ok, out = hm.run_ssh(target, probe, timeout=45)
        pids = sorted({ln.strip() for ln in out.splitlines()
                       if ok and ln.strip().isdigit()})
        if not pids:
            continue
        if dry_run:
            print(f"[{label}] would kill {len(pids)} process(es) embedding "
                  f"against {quiet_host}: {' '.join(pids)}")
            continue
        k_ok, k_out = hm.run_ssh(target, f"kill {' '.join(pids)} 2>&1 || true", timeout=30)
        print(f"[{label}] killed {len(pids)} process(es) embedding against "
              f"{quiet_host}: {' '.join(pids)}"
              + ("" if k_ok else f" ({k_out.strip()[:100]})"))


def enforce(host: str, quiet: bool, dry_run: bool) -> int:
    target = _target_for(host)
    if not target:
        print(f"[{host}] no ssh target configured, skipped")
        return 1
    hm = _remotes()
    steps: list[tuple[str, str]] = []
    if quiet:
        for pat in WORK_PATTERNS:
            steps.append((f"kill in-flight {pat}", f"pkill -f {pat} 2>/dev/null || true"))
        steps += [(f"stop {s}", c) for s, c in _service_cmds(target, "stop")]
    else:
        steps += [(f"start {s}", c) for s, c in _service_cmds(target, "start")]

    for label, cmd in steps:
        if dry_run:
            print(f"[{host}] would run: {cmd}")
            continue
        ok, out = hm.run_ssh(target, cmd, timeout=60)
        # bootout/stop on something already stopped is the state we wanted
        already = any(s in out for s in ("No such process", "not loaded",
                                         "not running", "Could not find"))
        status = "ok" if ok else ("already stopped" if already else "failed")
        note = "" if ok or already else f" ({out.strip()[:120]})"
        print(f"[{host}] {label}: {status}{note}")

    if quiet:
        _kill_work_targeting(host, dry_run)
        url = f"http://{host}:11434"
        if dry_run:
            print(f"[{host}] would unload every model on {url}")
        else:
            try:
                for line in hm.unload_all(url):
                    print(f"[{host}] {line}")
            except Exception as exc:  # noqa: BLE001 — ollama being down is fine
                print(f"[{host}] unload skipped: {exc}")
    return 0


def cmd_quiet(args) -> int:
    hosts = [args.host] if args.host else box_schedule.quiet_hosts()
    if not hosts:
        print("no box is inside its quiet window right now")
        return 0
    rc = 0
    for h in hosts:
        rc |= enforce(h, quiet=True, dry_run=args.dry_run)
    return rc


def cmd_resume(args) -> int:
    if args.host:
        hosts = [args.host]
    else:
        # everything configured that is NOT currently quiet
        hosts = [h for h in box_schedule._load_quiet()
                 if not box_schedule.is_quiet(h)]
    if not hosts:
        print("every configured box is still inside its quiet window")
        return 0
    rc = 0
    for h in hosts:
        rc |= enforce(h, quiet=False, dry_run=args.dry_run)
    return rc


def cmd_status(args) -> int:
    box_schedule.cmd_status(args)
    hm = _remotes()
    for host in box_schedule._load_quiet():
        target = _target_for(host)
        if not target:
            continue
        ok, out = hm.run_ssh(
            target, "pgrep -fc 'text_mirror.py|distill_offline.py' 2>/dev/null || echo 0",
            timeout=30)
        running = out.strip().splitlines()[-1] if ok and out.strip() else "?"
        loaded = "?"
        try:
            st = hm.host_status(f"http://{host}:11434", 0)
            loaded = ", ".join(m.name for m in st.loaded) or "none"
        except Exception:  # noqa: BLE001
            loaded = "unreachable"
        print(f"  {host}: hub work processes={running}  models loaded={loaded}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, help_ in (("quiet", "evict hub work and free memory"),
                        ("resume", "restart the hub daemons")):
        s = sub.add_parser(name, help=help_)
        s.add_argument("--host")
        s.add_argument("--dry-run", action="store_true")
    sub.add_parser("status", help="schedule plus what is actually running")
    args = ap.parse_args(argv)
    return {"quiet": cmd_quiet, "resume": cmd_resume, "status": cmd_status}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
