#!/usr/bin/env python3
"""Own a CFE JSON lock without stealing live or uncertain owners.

CLI callers pass the actual orchestrator PID, not this short-lived helper's PID.
A stable sidecar flock serializes acquisition, dead-owner recovery and release.
Only the matching token/PID may release. Age never authorizes recovery.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import datetime as dt
import fcntl
import json
import os
from pathlib import Path
import secrets
import socket


class LockHeld(RuntimeError):
    pass


def owner_alive(record: dict) -> bool | None:
    """None means ownership cannot be disproved; keep the lock."""
    if record.get('host') != socket.gethostname():
        return None
    pid = record.get('pid')
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        return None
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except (PermissionError, OSError):
        return None


@contextmanager
def guard(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    # Keep this inode stable; deleting the guard would allow two flock domains.
    with path.with_name(path.name + '.guard').open('a') as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise LockHeld('another lock operation is in progress') from error
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def acquire(path: Path, subject: str, pid: int, recover_dead: bool = False) -> dict:
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        raise ValueError('owner PID must be a positive integer')
    with guard(path):
        if path.exists():
            try:
                record = json.loads(path.read_text())
            except (OSError, ValueError) as error:
                raise LockHeld('lock ownership is unreadable; retain it for operator recovery') from error
            state = owner_alive(record) if isinstance(record, dict) else None
            if state is not False:
                raise LockHeld('owner is live or cannot be disproved; age does not permit stealing')
            if not recover_dead:
                raise LockHeld('owner is dead; explicit --recover-dead is required')
            path.unlink()
        record = {'pid': pid, 'host': socket.gethostname(), 'subject': subject,
                  'startedAt': dt.datetime.now(dt.timezone.utc).isoformat(),
                  'token': secrets.token_hex(16)}
        with path.open('x') as handle:
            json.dump(record, handle)
            handle.write('\n')
        return record


def release(path: Path, token: str, pid: int) -> None:
    with guard(path):
        try:
            record = json.loads(path.read_text())
        except (OSError, ValueError) as error:
            raise LockHeld('lock ownership is unreadable; nothing released') from error
        if not isinstance(record, dict) or record.get('token') != token or record.get('pid') != pid:
            raise LockHeld('ownership token/PID changed; nothing released')
        path.unlink()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    take = sub.add_parser('acquire')
    take.add_argument('path', type=Path)
    take.add_argument('--subject', required=True)
    take.add_argument('--pid', type=int, required=True)
    take.add_argument('--recover-dead', action='store_true')
    free = sub.add_parser('release')
    free.add_argument('path', type=Path)
    free.add_argument('--token', required=True)
    free.add_argument('--pid', type=int, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'acquire':
            print(json.dumps(acquire(args.path, args.subject, args.pid, args.recover_dead)))
        else:
            release(args.path, args.token, args.pid)
    except LockHeld as error:
        print(json.dumps({'status': 'LOCK-HELD', 'reason': str(error)}))
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
