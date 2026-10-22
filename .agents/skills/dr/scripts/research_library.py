#!/usr/bin/env python3
"""Compatibility CLI for the shared library, preserving immutable source history.

All existing source_library subcommands remain available. Extra commands:
  annotate --url URL --origin-id ID [--derived-from src:...] [--version VERSION]
  audit [--repair]    Check current bodies, archive current versions on repair.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    provenance = load('library_provenance', Path(__file__).with_name('research_provenance.py'))
    path = Path(os.environ.get('DR_SOURCE_LIBRARY', '~/.global-ai-hub/scripts/source_library.py')).expanduser()
    library = load('canonical_source_library', path)
    root = library.lib_dir()
    original = library.ingest
    def ingest(url, *args, **kwargs):
        provenance.archive(root, provenance.origin_metadata(root, library.dr.lib_find(url)))
        result = original(url, *args, **kwargs)
        if result.get('ok'):
            result['provenance'] = provenance.archive(root, provenance.origin_metadata(root, library.dr.lib_find(url)))
        return result
    library.ingest = ingest
    if argv and argv[0] == 'annotate':
        parser = argparse.ArgumentParser(description='Record explicit source ownership and derivation')
        parser.add_argument('--url', required=True)
        parser.add_argument('--origin-id', required=True)
        parser.add_argument('--derived-from', nargs='*', default=[])
        parser.add_argument('--version')
        args = parser.parse_args(argv[1:])
        provenance.annotate(root, library.dr.source_id(args.url), args.origin_id, args.derived_from, args.version)
        print(json.dumps({'ok': True}))
        return 0
    if argv and argv[0] == 'audit':
        parser = argparse.ArgumentParser(description='Check stored source hashes and preserve current versions')
        parser.add_argument('--repair', action='store_true')
        args = parser.parse_args(argv[1:])
        total, archived, errors = 0, 0, []
        for path in sorted((root / 'sources').glob('*.json')):
            total += 1
            try:
                metadata = library.dr.lib_get('src:' + path.stem)
                if not metadata.get('text_path'):
                    raise ValueError('missing source body')
                if provenance.digest(Path(metadata['text_path']).read_bytes()) != metadata['sha256']:
                    raise ValueError('source hash mismatch')
                if args.repair:
                    provenance.archive(root, provenance.origin_metadata(root, metadata))
                    archived += 1
            except (OSError, ValueError, KeyError) as error:
                errors.append({'source_id': 'src:' + path.stem, 'error': str(error)})
        print(json.dumps({'ok': not errors, 'sources': total, 'archived': archived, 'errors': errors}, indent=2))
        return int(bool(errors))
    return library.main(argv)


if __name__ == '__main__':
    raise SystemExit(main())
