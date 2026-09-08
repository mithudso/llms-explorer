#!/usr/bin/env python3
"""Restore a local Codex skill archive. Defaults to a read-only preflight."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--rpc-dir', type=Path, default=Path.home() / 'dev/codex-local-ai-setup/scripts')
    args = parser.parse_args()
    entries = json.loads(args.manifest.read_text())['entries']
    for entry in entries:
        source = Path(entry['archived_path'])
        target = Path(entry['path'])
        if target.resolve() != target:
            raise SystemExit(f'Refusing non-canonical target: {target}')
        if hashlib.sha256(source.read_bytes()).hexdigest() != entry['sha256']:
            raise SystemExit(f'Archive hash mismatch: {source}')
        if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() != entry['sha256']:
            raise SystemExit(f'Refusing to overwrite changed file: {target}')
        if target.is_symlink():
            raise SystemExit(f'Refusing symlink target: {target}')
    print(f'Preflight passed for {len(entries)} skills.')
    if not args.apply:
        print('No changes made. Add --apply to restore files and prior enablement.')
        return
    sys.path.insert(0, str(args.rpc_dir))
    from codex_rpc import CodexRPC
    with CodexRPC() as client:
        for entry in entries:
            target = Path(entry['path'])
            target.parent.mkdir(parents=True, exist_ok=True)
            # Publish without replacing a file created since preflight.
            with tempfile.NamedTemporaryFile(dir=target.parent) as staged:
                shutil.copyfile(entry['archived_path'], staged.name)
                try:
                    os.link(staged.name, target)
                except FileExistsError:
                    if target.is_symlink() or hashlib.sha256(target.read_bytes()).hexdigest() != entry['sha256']:
                        raise SystemExit(f'Refusing changed target: {target}')
            result = client.call('skills/config/write', {
                'path': str(target), 'enabled': entry['prior_enabled'],
            })
            if result['effectiveEnabled'] != entry['prior_enabled']:
                raise SystemExit(f'Failed to restore enablement: {target}')
            print(f'Restored: {target}')
    print(f'Restored {len(entries)} skills. Archive retained.')


if __name__ == '__main__':
    main()
