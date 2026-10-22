"""Content-bound local stage receipts. No remote publication or model invocation."""
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def outputs_hash(paths):
    rows = {}
    for path in map(Path, paths):
        if not path.exists():
            return None
        for item in sorted(path.rglob('*')) if path.is_dir() else [path]:
            if item.is_file():
                rows[str(item)] = hashlib.sha256(item.read_bytes()).hexdigest()
    return fingerprint(rows)


def run_stage(path, name, inputs, outputs, action):
    path = Path(path)
    state = json.loads(path.read_text()) if path.exists() else {}
    identity = fingerprint(inputs)
    hashes = outputs_hash(outputs)
    prior = state.get(name, {})
    if hashes is not None and prior.get('inputs') == identity and prior.get('outputs') == hashes and prior.get('status') == 'complete':
        return {'resumed': True, **prior}
    attempt = {'inputs': identity, 'status': 'running', 'started': datetime.now(UTC).isoformat()}
    state[name] = attempt
    def save():
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps(state, indent=2) + '\n')
        temporary.replace(path)
    save()
    try:
        action()
        hashes = outputs_hash(outputs)
        if hashes is None:
            raise ValueError(f'{name} did not create required outputs')
        attempt.update(status='complete', outputs=hashes, finished=datetime.now(UTC).isoformat())
    except Exception as error:
        attempt.update(status='failed', error=str(error), finished=datetime.now(UTC).isoformat())
        save()
        raise
    save()
    return {'resumed': False, **attempt}
