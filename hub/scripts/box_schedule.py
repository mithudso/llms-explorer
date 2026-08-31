#!/usr/bin/env python3
"""box_schedule.py — when a box may be given hub work.

Some boxes are not the hub's to saturate. 192.168.4.113 is a work laptop: on
weekday business hours it belongs to its owner, and a background distill or a
30B model resident in RAM is the difference between a usable machine and an
unusable one.

One policy, consulted by every dispatcher, so a box cannot be quiet for the
crawl queue while still serving embeddings:

  * pipeline_manager.discover_boxes()  — no mirror/distill placement
  * embed_core._parse_hosts()          — no embedding traffic

Times are the LOCAL time of whichever box evaluates this, which is the hub
box in every current path. Configure in hub-manager.json:

    "quiet_hours": {
      "192.168.4.113": {"days": "mon-fri", "start": "09:00", "end": "17:00"}
    }

A host key matches an ssh_targets label or any Ollama URL containing it.

Quiet hours can be suspended — on vacation, or any day the box is not being
used — without editing the schedule. An override is stored alongside it and
expires on its own, so "back Monday" never turns into a box that stayed idle
for a month:

    box_schedule.py off --days 7          suspend for a week
    box_schedule.py off --until 2026-09-08
    box_schedule.py off                   suspend until explicitly re-enabled
    box_schedule.py on                    cancel the suspension now

Usage:
  box_schedule.py status                  who is quiet right now, and why
  box_schedule.py check HOST              exit 0 if HOST may take work
  box_schedule.py off [--days N | --until YYYY-MM-DD] [--host H]
  box_schedule.py on [--host H]
"""

from __future__ import annotations

import argparse
import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

DAY_NAMES = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
DEFAULT_QUIET: dict[str, dict] = {
    "192.168.4.113": {"days": "mon-fri", "start": "09:00", "end": "17:00"},
}


def _load_quiet() -> dict[str, dict]:
    try:
        from hub_manager import settings as hm_settings
        configured = hm_settings.load().get("quiet_hours")
    except Exception:  # noqa: BLE001 — a bad config must not stop the pipeline
        configured = None
    return configured if isinstance(configured, dict) and configured else DEFAULT_QUIET


def _parse_days(spec: str) -> set[int]:
    """'mon-fri', 'sat,sun', 'daily' -> weekday indices (Monday = 0)."""
    spec = (spec or "mon-fri").strip().lower()
    if spec in ("daily", "all", "*"):
        return set(range(7))
    days: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, _, b = part.partition("-")
            if a in DAY_NAMES and b in DAY_NAMES:
                i, j = DAY_NAMES.index(a), DAY_NAMES.index(b)
                days.update(range(i, j + 1) if i <= j
                            else list(range(i, 7)) + list(range(0, j + 1)))
        elif part in DAY_NAMES:
            days.add(DAY_NAMES.index(part))
    return days or set(range(5))


def _parse_time(spec: str, fallback: str) -> datetime.time:
    try:
        hh, _, mm = (spec or fallback).partition(":")
        return datetime.time(int(hh), int(mm or 0))
    except (ValueError, TypeError):
        hh, _, mm = fallback.partition(":")
        return datetime.time(int(hh), int(mm))


OVERRIDE_PATH = Path.home() / ".global-ai-hub" / "quiet_hours_override.json"


def _read_override() -> dict:
    try:
        import json
        data = json.loads(OVERRIDE_PATH.read_text())
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _write_override(data: dict) -> None:
    import json
    OVERRIDE_PATH.parent.mkdir(parents=True, exist_ok=True)
    OVERRIDE_PATH.write_text(json.dumps(data, indent=2) + "\n")


def suspension(host: str, now: datetime.datetime | None = None) -> str | None:
    """Why `host`'s quiet hours are suspended right now, or None.

    An expired suspension is simply ignored rather than deleted, so `status`
    can still show what it was and when it lapsed.
    """
    now = now or datetime.datetime.now()
    data = _read_override()
    for key in ("*", host):
        entry = data.get(key)
        if not isinstance(entry, dict) or not entry.get("suspended"):
            continue
        until = entry.get("until")
        if not until:
            return f"suspended indefinitely (since {entry.get('since', '?')})"
        try:
            end = datetime.datetime.fromisoformat(until)
        except ValueError:
            continue
        if now < end:
            return f"suspended until {end:%a %Y-%m-%d %H:%M}"
    return None


def set_suspended(host: str, on: bool, until: datetime.datetime | None,
                  now: datetime.datetime | None = None) -> dict:
    now = now or datetime.datetime.now()
    data = _read_override()
    if on:
        data[host] = {"suspended": True, "since": now.isoformat(timespec="minutes"),
                      "until": until.isoformat(timespec="minutes") if until else None}
    else:
        data.pop(host, None)
    _write_override(data)
    return data


def is_quiet(host: str, now: datetime.datetime | None = None) -> bool:
    """True when `host` must not be given work right now.

    `host` may be an ssh_targets label ("192.168.4.113") or an Ollama URL
    ("http://192.168.4.113:11434"); a configured key matches if it appears
    anywhere in the string, so both dispatchers can pass what they have.
    """
    now = now or datetime.datetime.now()
    if suspension(host, now):
        return False
    for key, window in _load_quiet().items():
        if key not in host:
            continue
        if not isinstance(window, dict):
            continue
        if now.weekday() not in _parse_days(window.get("days", "mon-fri")):
            continue
        start = _parse_time(window.get("start"), "09:00")
        end = _parse_time(window.get("end"), "17:00")
        current = now.time()
        # an end earlier than start means the window wraps past midnight
        inside = (start <= current < end) if start <= end else (
            current >= start or current < end)
        if inside:
            return True
    return False


def quiet_hosts(now: datetime.datetime | None = None) -> list[str]:
    return [k for k in _load_quiet() if is_quiet(k, now)]


def cmd_status(args) -> int:
    now = datetime.datetime.now()
    print(f"now: {now:%a %Y-%m-%d %H:%M} (local)")
    quiet = _load_quiet()
    if not quiet:
        print("no quiet hours configured")
        return 0
    for key, window in quiet.items():
        why = suspension(key, now)
        state = "QUIET (no hub work)" if is_quiet(key, now) else "available"
        line = (f"  {key}: {state}  [{window.get('days','mon-fri')} "
                f"{window.get('start','09:00')}-{window.get('end','17:00')}]")
        if why:
            line += f"\n      schedule {why}"
        print(line)
    return 0


def _resolve_until(args) -> datetime.datetime | None:
    if getattr(args, "until", None):
        try:
            d = datetime.datetime.fromisoformat(args.until)
        except ValueError:
            print(f"could not read --until {args.until!r}; expected YYYY-MM-DD",
                  file=sys.stderr)
            raise SystemExit(2) from None
        # a bare date means through the END of that day
        return d if d.time() != datetime.time(0, 0) else d.replace(hour=23, minute=59)
    if getattr(args, "days", None):
        return datetime.datetime.now() + datetime.timedelta(days=args.days)
    return None


def _enforce(action: str) -> None:
    """Apply the new state to the boxes themselves.

    Suspending the schedule only changes what the dispatchers decide; the
    box's hub services are still stopped from the last eviction, so without
    this a vacation suspension would leave it idle rather than working.
    Best-effort: the schedule change stands even if a box is unreachable.
    """
    try:
        import quiet_hours_enforce
        quiet_hours_enforce.main([action])
    except Exception as exc:  # noqa: BLE001
        print(f"  (could not {action} boxes now: {exc}; "
              f"run quiet_hours_enforce.py {action} when they are reachable)")


def cmd_off(args) -> int:
    host = args.host or "*"
    until = _resolve_until(args)
    set_suspended(host, True, until)
    target = "every box" if host == "*" else host
    when = f"until {until:%a %Y-%m-%d %H:%M}" if until else "until re-enabled"
    print(f"quiet hours suspended for {target} {when}")
    print(f"  the hub will use {target} normally; 'box_schedule.py on' cancels this")
    if not getattr(args, "no_resume", False):
        _enforce("resume")
    return 0


def cmd_on(args) -> int:
    host = args.host or "*"
    set_suspended(host, False, None)
    # clearing the wildcard should not leave a stale per-host entry behind
    if host == "*":
        for key in list(_read_override()):
            set_suspended(key, False, None)
    print(f"quiet hours back in force for {'every box' if host == '*' else host}")
    # re-apply immediately if we are inside a window right now, so cancelling a
    # suspension mid-morning hands the box back without waiting for tomorrow
    if not getattr(args, "no_resume", False) and quiet_hosts():
        _enforce("quiet")
    return cmd_status(args)


def cmd_check(args) -> int:
    return 1 if is_quiet(args.host) else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status", help="who is quiet right now")
    c = sub.add_parser("check", help="exit 1 if HOST is quiet")
    c.add_argument("host")
    off = sub.add_parser("off", help="suspend quiet hours (vacation, away)")
    off.add_argument("--host", help="one box (default: all)")
    g = off.add_mutually_exclusive_group()
    g.add_argument("--days", type=int, help="suspend for N days")
    g.add_argument("--until", help="suspend until YYYY-MM-DD")
    off.add_argument("--no-resume", action="store_true",
                     help="change the schedule only; do not touch the boxes now")
    on = sub.add_parser("on", help="cancel a suspension")
    on.add_argument("--host")
    on.add_argument("--no-resume", action="store_true",
                    help="change the schedule only; do not touch the boxes now")
    args = ap.parse_args(argv)
    return {"status": cmd_status, "check": cmd_check,
            "off": cmd_off, "on": cmd_on}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
