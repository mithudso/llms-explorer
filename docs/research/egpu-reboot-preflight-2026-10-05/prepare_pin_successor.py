"""Offline v107 namespace successor; explicitly snapshot the changed live skill."""
import hashlib
import json
import os
from pathlib import Path
import re

VERSION = "1.0.2"
BASE = Path('/Users/mitch/.cache/claude-egpu/experiments')
ROOT = Path(__file__).absolute().parent
OLD_REVIEW = BASE / 'qwen36-27b-iq2-static-inputs-v106/INDEPENDENT-REVIEW.json'
OLD_REVIEW_SHA = '2d6111ec6ca005c98f6815c4f6c31cc7a320da6fed3e5a5c99c1d579f1d462b0'
OLD_SKILL = '/Users/mitch/.agents/skills/skill-optimizer/SKILL.md'
OLD_SKILL_SHA = '3232d5a05c59a0a1fa2c822364ab9d232ebb4b18c1fa99345d884c0df1506a7c'
CURRENT_SKILL = Path('/Users/mitch/dev/skills/skill-optimizer/SKILL.md')
CURRENT_SKILL_SHA = 'ac023e9d2dc44df5ed4905bc6bfd8e386fea901d16d5b06c7f7e011225783e42'
SNAPSHOT = ROOT / 'skill-optimizer-current-snapshot.md'
FAMILIES = ('renderer-preparation', 'startup-preparation', 'static-inputs', 'cold-root-operation', 'cold-runtime')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024**2), b''):
            h.update(block)
    return h.hexdigest()


def relocate(text):
    for family in FAMILIES:
        text = text.replace(f'qwen36-27b-iq2-{family}-v106', f'qwen36-27b-iq2-{family}-v107')
    return text.replace(OLD_SKILL, str(SNAPSHOT))


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def read_expected(path, expected, message):
    """Use the same captured bytes for the digest and all later transformations."""
    path = Path(path)
    require(path.resolve(strict=True) == path, 'Canonical predecessor required: ' + str(path))
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == expected, message)
    return raw


def put(path, data):
    raw = data if isinstance(data, bytes) else (json.dumps(data, indent=2) + '\n').encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)


def main():
    os.umask(0o077)
    old = json.loads(read_expected(OLD_REVIEW, OLD_REVIEW_SHA, 'Sealed predecessor changed'))
    require(old['source_pins'][OLD_SKILL] == OLD_SKILL_SHA, 'Unexpected replaced skill binding')
    captured = {}
    for name, expected in old['source_pins'].items():
        if name == OLD_SKILL:
            continue
        p = Path(name)
        require(p.resolve(strict=True) == p, 'Canonical predecessor required: ' + name)
        if '-v106/' in name:
            captured[p] = read_expected(p, expected, 'Unexpected predecessor drift: ' + name)
        else:
            require(sha(p) == expected, 'Unexpected predecessor drift: ' + name)
    current_skill_bytes = read_expected(CURRENT_SKILL, CURRENT_SKILL_SHA, 'Current skill changed')
    directories = [BASE / f'qwen36-27b-iq2-{f}-v107' for f in FAMILIES[:-1]]
    require(all(not p.exists() and not p.is_symlink() for p in directories), 'Successor namespace already exists')
    runtime = BASE / 'qwen36-27b-iq2-cold-runtime-v107'
    require(not runtime.exists() and not runtime.is_symlink(), 'Future runtime already exists')
    put(SNAPSHOT, current_skill_bytes)
    require(sha(SNAPSHOT) == CURRENT_SKILL_SHA, 'Snapshot digest differs')
    for p in directories:
        p.mkdir(mode=0o700)
    planned = {}
    for name in old['source_pins']:
        if '-v106/' in name:
            p = Path(name)
            planned[Path(relocate(name))] = p
    active = set()
    created = []

    def materialize(path):
        if path not in planned or path in created:
            digest = sha(path)
            if path not in created:
                expected = CURRENT_SKILL_SHA if path == SNAPSHOT else old['source_pins'].get(str(path))
                require(expected is not None and digest == expected, 'Unexpected predecessor drift: ' + str(path))
            return digest
        require(path not in active, 'Unexpected hash-binding cycle')
        active.add(path)
        source = planned[path]
        raw = captured[source]
        if source.name == 'expected-inventory.json':
            # This is an exact parser result. It cannot carry provenance metadata.
            put(path, raw)
        elif source.suffix == '.json':
            def rebind(value):
                if isinstance(value, dict):
                    result = {relocate(k): rebind(v) for k, v in value.items()}
                    if 'source_pins' in result:
                        result['source_pins'] = {p: materialize(Path(p)) for p in result['source_pins']}
                    if set(result) == {'path', 'sha256'} and result['path'] != value.get('path'):
                        result['sha256'] = materialize(Path(result['path']))
                    return result
                if isinstance(value, list):
                    return [rebind(v) for v in value]
                return relocate(value) if isinstance(value, str) else value
            data = rebind(json.loads(raw))
            if isinstance(data.get('version'), str) and re.fullmatch(r'\d+\.\d+\.\d+', data['version']):
                a, b, c = data['version'].split('.')
                data['version'] = f'{a}.{b}.{int(c)+1}'
            data['delta'] = 'Namespace successor; changed live skill explicitly snapshotted. F32 model, native build and all original acceptance controls remain unchanged.'
            put(path, data)
        else:
            text = relocate(raw.decode())
            if source.name == 'start_once.py':
                renderer = Path(relocate(str(BASE / 'qwen36-27b-iq2-renderer-preparation-v106/experimental_27b.py')))
                old_sha = old['source_pins'][str(planned[renderer])]
                new_sha = materialize(renderer)
                require(text.count(old_sha) == 1, 'Expected one renderer hash literal')
                text = text.replace(old_sha, new_sha)
            put(path, text.encode())
        active.remove(path)
        created.append(path)
        return sha(path)

    for path in planned:
        materialize(path)
    delta = {'version': VERSION, 'predecessor_review': {'path': str(OLD_REVIEW), 'sha256': OLD_REVIEW_SHA}, 'old_reference': {'path': OLD_SKILL, 'sha256': OLD_SKILL_SHA}, 'new_reference': {'path': str(SNAPSHOT), 'sha256': CURRENT_SKILL_SHA}, 'historical_bytes_recovered': False, 'global_skill_modified': False, 'model_or_native_build_changed': False, 'GPU_initializations': 0, 'created': [str(p) for p in created]}
    put(ROOT / 'NAMESPACE-DELTA.json', delta)
    pins = {relocate(name): materialize(Path(relocate(name))) for name in old['source_pins']}
    pins[str(ROOT / 'NAMESPACE-DELTA.json')] = sha(ROOT / 'NAMESPACE-DELTA.json')
    pins[str(Path(__file__).absolute())] = sha(Path(__file__).absolute())
    draft = {k: v for k, v in old.items() if k not in ('source_pins', 'independent_final_audit')}
    draft.update(version='1.0.0', delta='Namespace/reference successor requires fresh independent review.', source_pins=pins, source_pin_count=len(pins), passed=False, seal_pending=True, independent_review_pending=True, independent_static_review=False, full_qualification=False)
    put(BASE / 'qwen36-27b-iq2-static-inputs-v107/REVIEW-DRAFT.json', draft)
    print(json.dumps({'version': VERSION, 'draft_pins': len(pins), 'created_files': len(created)+3, 'GPU_initializations': 0, 'authority_issued': False}, indent=2))


if __name__ == '__main__':
    main()
