"""Recoverable local projection writes with a durable preimage journal."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


class Transaction:
    def __init__(self, root, registry=None):
        self.root = Path(root).absolute()
        self.registry = Path(registry).absolute() if registry is not None else None
        self.entries = []
        self.seen = set()
        self.status = 'running'

    def save(self):
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / 'journal.json'
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps({'status': self.status, 'entries': self.entries,
                                        'registry': str(self.registry) if self.registry else None}, indent=2) + '\n')
        temporary.replace(path)
        if self.registry is not None:
            self.registry.mkdir(parents=True, exist_ok=True)
            marker = self.registry / (hashlib.sha256(str(self.root).encode()).hexdigest() + '.json')
            if self.status == 'running':
                pending = marker.with_suffix('.tmp')
                pending.write_text(json.dumps({'root': str(self.root)}) + '\n')
                pending.replace(marker)
            else:
                marker.unlink(missing_ok=True)

    def remember(self, path):
        path = Path(path).absolute()
        if str(path) in self.seen or any(path.is_relative_to(Path(item)) for item in self.seen):
            return
        saved = self.root / 'preimages' / str(len(self.entries))
        kind = 'absent'
        if path.is_symlink():
            raise ValueError('projection destination cannot be a symlink: ' + str(path))
        if path.exists():
            saved.parent.mkdir(parents=True, exist_ok=True)
            kind = 'directory' if path.is_dir() else 'file'
            if path.is_dir():
                shutil.copytree(path, saved)
            else:
                shutil.copy2(path, saved)
        self.entries.append({'path': str(path), 'kind': kind, 'preimage': str(saved)})
        self.seen.add(str(path))
        self.save()  # Journal the preimage before the first mutation.

    def write(self, path, value):
        path = Path(path)
        self.remember(path)
        if value is None:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink(missing_ok=True)
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(path.name + '.projection-tmp')
        try:
            if isinstance(value, bytes):
                temporary.write_bytes(value)
            else:
                temporary.write_text(value, encoding='utf-8')
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)

    def rollback(self):
        for entry in reversed(self.entries):
            path, saved = Path(entry['path']), Path(entry['preimage'])
            path.with_name(path.name + '.projection-tmp').unlink(missing_ok=True)
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink(missing_ok=True)
            if entry['kind'] != 'absent':
                path.parent.mkdir(parents=True, exist_ok=True)
                if entry['kind'] == 'directory':
                    shutil.copytree(saved, path)
                else:
                    shutil.copy2(saved, path)
        self.status = 'rolled-back'
        self.save()

    def commit(self):
        for entry in self.entries:
            path = Path(entry['path'])
            entry['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        self.status = 'complete'
        self.save()


def recover(root):
    """Restore an interrupted transaction before retrying its projection stage."""
    root = Path(root)
    state = json.loads((root / 'journal.json').read_text())
    if state['status'] != 'running':
        return False
    transaction = Transaction(root, registry=state.get('registry'))
    transaction.entries = state['entries']
    transaction.rollback()
    return True


def registry_dir(research_dir):
    return Path(research_dir) / '.projection-journals'


def recover_pending(research_dir, repo):
    """Recover all shared writers under the caller's research global lock.

    Registered locations cover other checkouts. The two legacy globs also find
    interrupted journals created before registry support was installed.
    """
    research_dir, repo = Path(research_dir), Path(repo)
    journals = set(research_dir.glob('*/artifacts/transactions/*/journal.json'))
    journals.update((repo / 'tmp/research-site-sync-backups').glob('*/transaction/journal.json'))
    markers = list(registry_dir(research_dir).glob('*.json'))
    for marker in markers:
        journal = Path(json.loads(marker.read_text())['root']) / 'journal.json'
        if not journal.is_file():
            raise ValueError('registered projection journal is missing: ' + str(journal))
        journals.add(journal)
    recovered = []
    for journal in sorted(journals, key=lambda path: path.stat().st_mtime_ns, reverse=True):
        if recover(journal.parent):
            recovered.append(str(journal.parent))
    # A process can stop after the terminal journal write and before unlinking
    # its registry marker. Never roll a completed transaction back.
    for marker in markers:
        marker.unlink(missing_ok=True)
    return recovered
