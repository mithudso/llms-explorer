#!/usr/bin/env python3
"""Exercise Explorer's real local-agent completion path for the reviewed DATE run."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import threading
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from llmsx import explorer_store as store


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    run = Path.home() / '.global-ai-hub/research/date-criteria'
    review = json.loads((run / 'gate-independent-review.json').read_text())
    if hashlib.sha256((run / 'gate.json').read_bytes()).hexdigest() != review['gate_sha256']:
        parser.error('The gate changed after independent review')
    if (review.get('sampled') != 10
            or len(review.get('claims', [])) != 10
            or any(c.get('review') != 'confirmed' for c in review['claims'])):
        parser.error('The ten sampled claims need independent confirmation')
    manifest = json.loads((run / 'manifest.json').read_text())
    if args.execute and manifest.get('exit_status') == 'COMPLETED':
        parser.error('This run is finalized; choose another frontier in Explorer')
    if any(c['status'] != 'done' for c in manifest['concepts']):
        parser.error('Research is incomplete')
    argv = store.research_argv('DATE Criteria', 'dr', 'Archive Rules', provider='ollama')
    if not argv:
        parser.error('Local Explorer agent runtime is unavailable')
    model = review['model']
    counts = ', '.join(f'{v} {k}' for k, v in review['counts'].items())
    finish = (f'python3 {Path.home()}/.global-ai-hub/scripts/dr_run.py finish '
              f'date-criteria --status COMPLETED --report {run}/report.md '
              '--agents 6 --stop-reason "Research and independently reviewed gate complete; '
              'indexing deferred by user"')
    instruction = f'''
RESUME THE EXISTING REVIEWED RUN. This instruction supersedes starting a new run.
Run directory: {run}. All five concepts are done. The installed artifact is
{manifest['install_path']}. The fresh {model} gate saved {counts},
two per concept, in {review['gate_seconds']} seconds with {review['gate_fetches']} scrapes.
Independent review confirmed all ten against the complete cited sources. Read
{run / 'gate-independent-review.json'}, manifest.json, gate.json and report.md.
Preserve provenance: the original research used GGUF Qwen; QwenMLX corrected
archival-age bounds; Gemma31 performed this fresh verification and finalization.
Gemma31 separately completed a fresh one-concept research worker and an
evidence-directed correction worker. All six corrected facts were reviewed.
This resumption does not mean Gemma independently researched all five concepts.

Do not initialize, refresh, re-research, rerender or rerun the accepted gate.
Run this exact canonical completion command, without adding --minutes:
{finish}
The helper computes elapsed minutes. This includes interruptions and model
qualification trials; it is not a measurement of continuous Gemma research time.
Do not edit the manifest by hand. Inspect the finish result and report any error.
The operator will merge only the DATE Criteria node into the repository tree
after canonical finish. Do not modify the repo tree or commit any files here.
Indexing is user-paused: do not run embeddings or registry index builds. The
existing offline Atlas metadata checks passed. Report indexing as deferred.
Stop once the helper has actually finalized the run and summarize its result.
'''
    argv[argv.index('-p') + 1] += instruction
    argv += ['--max-turns', '25']
    print('Model:', review['model'])
    print('Action: real Explorer agent finalization of the reviewed standard DATE run')
    if not args.execute:
        if manifest.get('exit_status') == 'COMPLETED':
            print('Already finalized. Inspect explorer-acceptance.json; no inference needed.')
        else:
            print('Dry run. Add --execute to finalize through the local agent.')
        return 0
    os.environ['LLMSX_OLLAMA_MODEL'] = model
    report = f'''# DATE Criteria local research qualification

Standard run: five completed concepts,39claims,16sourceURLs, installed in the
mongodb-atlas-expert hub at {manifest['install_path']}.

Gemma4:31b-mlx (alias {model},65536context) completed the fresh gate
in {review['gate_seconds']} seconds. It saved {counts}, with two samples per
concept. The relay used {review['gate_fetches']} scrapes. Independent review
confirmed the full sampled claims against the complete fetched source bodies,
including clauses omitted from short excerpts. See gate-independent-review.json.
Gemma31 also completed a fresh standard-contract one-concept worker, followed
by an evidence-directed correction worker. All six corrected facts were
independently reviewed. Initial drafts require verification and correction.

Provenance: original five-concept research used GGUFQwen27. QwenMLX corrected
two incorrect archival-age bounds. Gemma31 performed verification and this
finalization. This is a resumed standard workflow qualification, not a fresh
five-concept Gemma-only research benchmark. Elapsed run minutes include user
interruptions, downloads and comparison trials. Claude helper price estimates
are requested-model metadata, not local inference charges.

Atlas hub metadata validation returned0High/0Medium/0Low. All rendered references
and footnote targets were checked. Registry embeddings and semantic queries
remain deferred because the user has paused indexing. The installed reference
was scanned for source-supplied assistant instructions.

The qualification fixture does not establish accuracy for all frontier topics;
source review remains necessary. See the repository HANDOFF for runtime tests.
'''
    (run / 'report.md').write_text(report)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    log = Path.home() / f'.llmsx/jobs/explorer-{model}-acceptance-{stamp}.jsonl'
    print('Log:', log, flush=True)
    result = store.run_claude_job(argv, repo, timeout=1800, log=log,
                                 emit=lambda line: print(line[:350], flush=True),
                                 cancel=threading.Event(), provider='ollama')
    saved = {'model': review['model'], 'result': asdict(result), 'log': str(log)}
    (run / 'explorer-acceptance.json').write_text(json.dumps(saved, indent=2) + '\n')
    print(json.dumps(saved, indent=2))
    return 0 if result.status == 'ok' else 1


if __name__ == '__main__':
    raise SystemExit(main())
