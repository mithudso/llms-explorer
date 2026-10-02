#!/usr/bin/env python3
"""Resume the saved DATE Criteria local-model qualification; defaults to read-only."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('status', 'research', 'gate'), nargs='?', default='status')
    parser.add_argument('--execute', action='store_true', help='Run the displayed local-model command')
    args = parser.parse_args()
    home = Path.home()
    run = home / '.global-ai-hub/research/date-criteria'
    manifest = json.loads((run / 'manifest.json').read_text())
    print(json.dumps({k: manifest.get(k) for k in ('status', 'exit_status', 'concepts', 'install_path', 'gate')}, indent=2))
    gate_path = run / 'gate.json'
    if gate_path.is_file():
        from collections import Counter
        try:
            gate = json.loads(gate_path.read_text())
            print('Saved gate progress:', json.dumps({
                'sampled': gate.get('sampled'),
                'counts': dict(Counter(v.get('verdict') for v in gate.get('verdicts', []))),
                'path': str(gate_path),
            }))
        except (ValueError, AttributeError):
            print('Gate write is incomplete; retry status after the current worker saves it.')
    if args.phase == 'status':
        return 0
    if manifest.get('exit_status') == 'COMPLETED':
        parser.error('This saved run is finalized; choose a new frontier in Explorer')
    runner = shutil.which('llmsx-ollama-agent')
    if not runner:
        parser.error('llmsx-ollama-agent is missing; reinstall the editable llmsx package first')
    config = json.loads((home / '.llmsx/config.json').read_text())
    research_models = {'llmsx-research', 'llmsx-research-mlx',
                       'llmsx-research-gemma-mlx', 'llmsx-research-gemma12-mlx',
                       'llmsx-research-gemma31-mlx'}
    if (config.get('provider') != 'ollama'
            or config.get('models', {}).get('ollama') not in research_models):
        parser.error('Local qualification requires provider=ollama and a saved research model alias')
    if config.get('ollama_allow_indexing') is not False:
        parser.error('Restore ollama_allow_indexing=false; indexing remains paused')
    cmd = [sys.executable, str(home / '.global-ai-hub/scripts/dr_run.py'), args.phase, 'date-criteria']
    if args.phase == 'research':
        pending = [c['name'] for c in manifest['concepts'] if c.get('status') != 'done']
        if not pending:
            print('All concepts are done; proceed to render and gate using the handoff.')
            return 0
        for concept in pending:
            cmd += ['--concept', concept]
        cmd += ['--max-parallel', '1']
    else:
        if any(c.get('status') != 'done' for c in manifest['concepts']):
            parser.error('Finish every concept before gating')
        if not manifest.get('install_path') or not Path(manifest['install_path']).is_file():
            parser.error('Render the installed artifact before gating; see handoff')
    cmd += ['--agent-timeout', '1800']
    if args.phase == 'gate':
        cmd += ['--max-turns', '90']
    print('Command:', subprocess.list2cmdline(cmd), flush=True)
    if not args.execute:
        print('Dry run only. Add --execute to run; do not launch a duplicate worker.')
        return 0
    env = dict(os.environ)
    env['DR_CLAUDE_BIN'] = runner
    env['LLMSX_OLLAMA_RESEARCH_CONTEXT'] = json.dumps(['DATE Criteria', 'Archive Rules', 'Online Archive', 'MongoDB Atlas'])
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    log = home / f'.llmsx/jobs/local-standard-dr-{args.phase}-{stamp}.log'
    print('Log:', log, flush=True)
    with log.open('w') as output:
        child = subprocess.Popen(cmd, env=env, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        print('Owned process group:', child.pid, flush=True)
        try:
            return child.wait()
        except KeyboardInterrupt:
            import signal
            os.killpg(child.pid, signal.SIGTERM)
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
            return 130


if __name__ == '__main__':
    raise SystemExit(main())
