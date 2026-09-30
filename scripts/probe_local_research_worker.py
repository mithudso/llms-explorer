#!/usr/bin/env python3
"""Run one fresh standard-contract worker without installing a test skill or tree node."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--model', default='llmsx-research-gemma31-mlx')
    parser.add_argument('--slug', default='local-gemma31-worker-probe')
    args = parser.parse_args()
    helper = Path.home() / '.global-ai-hub/scripts/dr_run.py'
    slug = args.slug
    if not slug or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in slug):
        parser.error('Use a lowercase slug with letters, numbers and hyphens')
    run = Path.home() / '.global-ai-hub/research' / slug
    print(f'Model: {args.model}; one worker, three sources and a negation query')
    if not args.execute:
        print('Dry run. Existing fixture:', run.exists())
        return 0
    if run.exists():
        parser.error('A probe directory already exists; inspect it before launching another worker')
    runner = shutil.which('llmsx-ollama-agent')
    if not runner:
        parser.error('Install the editable local agent runner first')
    env = dict(os.environ, DR_CLAUDE_BIN=runner,
               LLMSX_OLLAMA_MODEL=args.model,
               LLMSX_OLLAMA_RESEARCH_CONTEXT=json.dumps([
                   'DATE Criteria', 'Archive Rules', 'Online Archive', 'MongoDB Atlas']))
    concepts = ('DATE criteria date format specifications,DATE archival age calculation,'
                'DATE partition fields,DATE time series constraints,DATE custom filtering')
    subprocess.run([sys.executable, str(helper), 'init', 'DATE Criteria',
                    '--slug', slug, '--depth', 'standard', '--hub', 'mongodb-atlas-expert',
                    '--parent', 'Archive Rules', '--concepts', concepts],
                   env=env, check=True, stdout=subprocess.DEVNULL)
    log = Path.home() / '.llmsx/jobs' / f'{slug}.log'
    with log.open('w') as output:
        child = subprocess.Popen([
            sys.executable, str(helper), 'research', slug,
            '--concept', 'DATE criteria date format specifications',
            '--max-parallel', '1', '--max-turns', '90', '--agent-timeout', '1800'],
            env=env, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        print('Owned process group:', child.pid, 'log:', log, flush=True)
        try:
            rc = child.wait()
        except KeyboardInterrupt:
            os.killpg(child.pid, signal.SIGTERM)
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
            return 130
    manifest = json.loads((run / 'manifest.json').read_text())
    concept = manifest['concepts'][0]
    record = manifest.get('agents', {}).get(concept['slug'], {})
    passed = rc == 0 and concept['status'] == 'done' and not record.get('is_error')
    print(json.dumps({'passed': passed, 'worker': record, 'run': str(run)}, indent=2))
    # Deliberately do not render/finish: this is an isolated worker fixture, not
    # a second installed skill or a completed five-worker research run.
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
