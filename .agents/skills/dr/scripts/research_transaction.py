"""Recoverable local projection writes with a durable preimage journal."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


class Transaction:
    def __init__(self, root):
        self.root = Path(root)
        self.entries = []
        self.seen = set()
        self.status = 'running'

    def save(self):
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / 'journal.json'
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps({'status': self.status, 'entries': self.entries}, indent=2) + '\n')
        temporary.replace(path)

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
    transaction = Transaction(root)
    transaction.entries = state['entries']
    transaction.rollback()
    return True
