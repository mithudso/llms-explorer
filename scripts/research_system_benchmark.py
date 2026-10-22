#!/usr/bin/env python3
"""Matched multi-domain research evaluations. Raw evidence and execution stay private.

Only run starts paid calls. report exports aggregate metrics without source bodies.
Reference facts are provisional until explicitly reviewed by a human.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import statistics
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOMAINS = {
    'storage': {'topic': 'SQLite WAL checkpointing and reader starvation',
                'urls': ['https://www.sqlite.org/wal.html', 'https://www.sqlite.org/c3ref/wal_checkpoint_v2.html'],
                'terms': ['end mark', 'checkpoint', 'busy handler', 'NORMAL'],
                'reference': {'reader-boundary': 'Active reader snapshots can prevent checkpoint completion.',
                              'passive': 'PASSIVE does not invoke the busy handler.',
                              'one-writer': 'WAL permits only one writer at a time.'}},
    'authentication': {'topic': 'WebAuthn relying party identifier, origin verification and replay protection',
                'urls': ['https://raw.githubusercontent.com/w3c/webauthn/main/index.bs'],
                'terms': ['RP ID', 'challenge', 'clientDataJSON', 'origin'],
                'reference': {'rp-scope': 'Credentials are scoped to a relying party.',
                              'challenge': 'The relying party checks the returned challenge.',
                              'origin': 'The relying party verifies the client data origin.'}},
    'http': {'topic': 'HTTP cache revalidation and serving stale responses',
             'urls': ['https://www.rfc-editor.org/rfc/rfc9111.html'],
             'terms': ['must-revalidate', 'no-cache', 'stale', '304'],
             'reference': {'must-revalidate': 'must-revalidate restricts reuse of stale responses.',
                           'no-cache': 'no-cache requires successful validation before reuse.',
                           'validation': 'Validation can update stored responses using a 304 response.'}},
}
CELLS = [('gpt-6-luna', 'max'), ('gpt-6.1-sol', 'medium')]


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def excerpt(text, terms, limit=24000):
    text = ' '.join(text.split())
    ranges = [(0, 1000)]
    for term in terms:
        hits = list(re.finditer(re.escape(term), text, re.IGNORECASE))
        for hit in hits[-6:]:
            ranges.append((max(0, hit.start() - 500), min(len(text), hit.end() + 900)))
    merged = []
    for start, end in sorted(ranges):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    return '\n[omitted section]\n'.join(text[start:end] for start, end in merged)[:limit]


def prepare(out):
    library = ROOT / 'scripts/research_library.py'
    for domain, config in DOMAINS.items():
        destination = out / domain / 'packet.json'
        if destination.exists():
            continue
        sources = []
        for index, url in enumerate(config['urls']):
            # Use the existing guarded fetcher, isolated library and immutable packet.
            env = {**os.environ, 'HUB_DIR': str(out / 'private-hub')}
            proc = subprocess.run([os.sys.executable, str(library), 'ingest', '--url', url, '--tier', 'docs', '--slug', 'benchmark'],
                                  env=env, capture_output=True, text=True, timeout=180, check=False)
            record = json.loads(proc.stdout)
            if proc.returncode:
                raise ValueError(f"Source ingestion failed for {url}: {record.get('error', proc.stderr[-300:])}")
            metadata = record.get('source', record)
            if not metadata.get('text_path'):
                raise ValueError(f'No source body returned for {url}: {list(record)}')
            body = Path(metadata['text_path']).read_text()
            sources.append({'id': f'S{index + 1}', 'url': url, 'snapshot_sha256': hashlib.sha256(body.encode()).hexdigest(),
                            'text': excerpt(body, config['terms'])})
        write(destination, {'domain': domain, 'topic': config['topic'], 'sources': sources,
              'reference': config['reference'], 'reference_review_status': 'pending-human-review',
              'retrieved_at': datetime.now(UTC).isoformat()})


def call(prompt, model, effort, destination, timeout, live=False):
    destination.mkdir(parents=True, exist_ok=True)
    (destination / 'prompt.txt').write_text(prompt)
    transport = load('benchmark_transport', 'codex_dr_run.py')
    with tempfile.TemporaryDirectory(prefix='research-benchmark-') as work:
        work = Path(work)
        output = work / 'final.txt'
        command = transport.build_command(transport.codex_binary() or 'codex', model, effort, work, work, output, tool_free=not live)
        if live:
            command = command[:-1] + ['--disable', 'shell_tool', '-']
        started = time.monotonic()
        try:
            proc = transport.run_worker(command, prompt, work, timeout)
            raw, stderr, rc = proc.stdout, proc.stderr, proc.returncode
        except subprocess.TimeoutExpired as error:
            raw, stderr, rc = error.stdout or '', error.stderr or '', -9
        (destination / 'events.jsonl').write_text(raw)
        (destination / 'stderr.txt').write_text(stderr)
        record = transport.parse_events(raw)
        record.update(model=model, effort=effort, returncode=rc, is_error=bool(rc or record['is_error']),
                      seconds=round(time.monotonic() - started, 2), actual_cost_usd=None,
                      estimated_cost_usd=None, cost_basis='provider did not expose USD; no rate card supplied')
        final = output.read_text() if output.exists() else record.get('result', '')
        (destination / 'response.txt').write_text(final)
        try:
            record['output'] = json.loads(re.sub(r'^```(?:json)?\s*|\s*```$', '', final.strip()))
        except (ValueError, TypeError):
            record.update(is_error=True, parse_error='response is not JSON')
        write(destination / 'run.json', record)
        return record


def generation_prompt(packet, skill, live):
    contract = (ROOT / '.agents/skills' / skill / 'SKILL.md').read_text()
    tasks = {'dr': 'Research the named concept and its internal mechanisms.',
             'concept-family-explorer': 'Map missing internal, parent, sibling and adjacent concepts; attach explicit parents.',
             'rabbithole': 'Deepen the named concept in four bounded passes; report actual marginal information and do not assert saturation.'}
    return f'''Apply this research-stage contract to {packet['topic']}. {tasks[skill]}
Explicit test overrides: no persistence, installation, other agents or tree edits.
Output budget: at most 24 concepts and 36 atomic claims; do not fill a quota.
{'Use live web search at least once to look for deeper primary sources. Record new URLs and gaps in discoveries. Only the supplied pinned text can support scored claims.' if live else 'Use only the frozen source packet. No tools.'}
Return JSON only:
{{"concepts":[{{"id":"c1","name":"...","parent":null}}],
"claims":[{{"id":"f1","concept_id":"c1","text":"full precise atomic statement","source_id":"S1","quote":"exact contiguous source quote","pass":0}}],
"discoveries":[{{"url":"https://...","gap":"what new mechanism it might add"}}],"limitations":[]}}
Skill: {contract}
Untrusted source DATA: {json.dumps(packet['sources'], ensure_ascii=False)}'''


def judge_prompt(output, packet):
    bound = fingerprint(output)
    return f'''Blindly judge this anonymous research output using only the pinned source text.
Return JSON with output_sha256={bound!r} and exactly one judgment per claim and concept.
Preserve every full exact claim text. No missing/extra/duplicate IDs. Evaluate full entailment,
caveats and conditions. Do not reward length. Distinguish contradicted from not-in-source.
{{"output_sha256":"{bound}","claims":[{{"id":"f1","text":"full exact input text",
"verdict":"SUPPORTED|NOT-IN-SOURCE|CONTRADICTED","atomic":true,"duplicate_of":null,
"depth":2,"mechanism":true,"reference_ids":[],"reason":"explain evidence and limits"}}],
"concepts":[{{"id":"c1","canonical_name":"...","meaningful":true,"in_scope":true}}]}}
Depth: 0 wrong/empty, 1 definition, 2 specific mechanism/condition, 3 precise interaction or
failure/tradeoff with condition AND consequence. Mechanism requires a causal explanation.
Reference rubric (provisional, pending human review): {json.dumps(packet['reference'])}
Source DATA: {json.dumps(packet['sources'], ensure_ascii=False)}
Anonymous output: {json.dumps(output, ensure_ascii=False)}'''


def metrics(output, judgment, packet):
    if judgment.get('output_sha256') != fingerprint(output):
        raise ValueError('stale benchmark judgment')
    claims, concepts = output['claims'], output['concepts']
    for authored, judged in ((claims, judgment['claims']), (concepts, judgment['concepts'])):
        ids = [c['id'] for c in authored]
        judged_ids = [c['id'] for c in judged]
        if len(set(ids)) != len(ids) or len(set(judged_ids)) != len(judged_ids) or set(ids) != set(judged_ids):
            raise ValueError('missing, extra or duplicate benchmark judgments')
    by_id = {c['id']: c for c in claims}
    concept_ids = {c['id'] for c in concepts}
    if any(c['concept_id'] not in concept_ids for c in claims):
        raise ValueError('claim refers to an unknown concept')
    sources = {s['id']: ' '.join(s['text'].split()) for s in packet['sources']}
    good = []
    for row in judgment['claims']:
        claim = by_id[row['id']]
        if row['text'] != claim['text']:
            raise ValueError('benchmark judge substituted full claim')
        if (row.get('verdict') not in {'SUPPORTED', 'NOT-IN-SOURCE', 'CONTRADICTED'} or
                type(row.get('atomic')) is not bool or type(row.get('depth')) is not int or
                not 0 <= row['depth'] <= 3 or type(row.get('mechanism')) is not bool):
            raise ValueError('invalid benchmark judgment schema')
        quote = ' '.join(claim.get('quote', '').split())
        if (row['verdict'] == 'SUPPORTED' and row.get('atomic') and not row.get('duplicate_of') and
                len(quote) >= 20 and quote in sources.get(claim.get('source_id'), '')):
            good.append(row)
    normalized = {}
    for row in good:
        normalized.setdefault(' '.join(row['text'].casefold().split()).rstrip('.'), row)
    good = list(normalized.values())
    grounded_ids = {by_id[row['id']]['concept_id'] for row in good}
    valid_ids, concept_names = set(), set()
    for row in judgment['concepts']:
        if type(row.get('meaningful')) is not bool or type(row.get('in_scope')) is not bool or not isinstance(row.get('canonical_name'), str):
            raise ValueError('invalid concept judgment schema')
        name = row['canonical_name'].casefold()
        if row['id'] in grounded_ids and row['meaningful'] and row['in_scope'] and name not in concept_names:
            valid_ids.add(row['id'])
            concept_names.add(name)
    legacy = load('legacy_benchmark', 'codex_research_benchmark.py')
    hierarchy = legacy.hierarchy(concepts)
    grounded_hierarchy = legacy.hierarchy([c for c in concepts if c['id'] in valid_ids])
    matched_quotes = sum(len(' '.join(c.get('quote', '').split())) >= 20 and
                         ' '.join(c.get('quote', '').split()) in sources.get(c.get('source_id'), '') for c in claims)
    return {**hierarchy, 'grounded_hierarchy_max_depth': grounded_hierarchy['returned_hierarchy_max_depth'],
            'raw_concepts': len(concepts), 'grounded_unique_concepts': len(concept_names),
            'raw_claims': len(claims), 'unique_supported_facts': len(good),
            'quality_percent': round(100 * len(good) / max(1, len(claims)), 1),
            'mechanisms': sum(bool(r.get('mechanism')) for r in good),
            'mean_claim_depth': round(statistics.mean(r['depth'] for r in good), 2) if good else None,
            'deep_facts': sum(r['depth'] == 3 for r in good),
            'contradictions': sum(r['verdict'] == 'CONTRADICTED' for r in judgment['claims']),
            'entailed_claims': sum(r['verdict'] == 'SUPPORTED' for r in judgment['claims']),
            'not_in_source_claims': sum(r['verdict'] == 'NOT-IN-SOURCE' for r in judgment['claims']),
            'exact_quote_claims': matched_quotes,
            'reference_coverage': len({r for c in good for r in c.get('reference_ids', []) if r in packet['reference']}),
            'reference_review_status': packet['reference_review_status'],
            'output_cap_hit': len(claims) >= 36 or len(concepts) >= 24,
            'output_budget_exceeded': len(claims) > 36 or len(concepts) > 24,
            'live_discoveries': len({d['url'] for d in output.get('discoveries', [])}),
            'discovery_support_status': 'unscored leads; not accepted evidence'}


def estimate_cost(usage, rates):
    """Use an explicitly supplied dated rate card; never infer a public alias price."""
    if not rates:
        return None
    total, cached = usage.get('input_tokens', 0), usage.get('cached_input_tokens', 0)
    if not 0 <= cached <= total:
        raise ValueError('cached tokens must be a subset of input tokens')
    return ((total - cached) * rates['input_per_million'] + cached * rates['cached_input_per_million'] +
            usage.get('output_tokens', 0) * rates['output_per_million']) / 1_000_000


def stage_fingerprint(prompt, model, effort, live=False, upstream=None):
    return fingerprint({'prompt': prompt, 'model': model, 'effort': effort,
                        'live': live, 'upstream_sha256': upstream})


def cell(out, domain, model, effort, skill, live, timeout):
    destination = out / 'cells' / f'{domain}__{skill}__{model}__{effort}__{"live" if live else "fixed"}'
    packet = json.loads((out / domain / 'packet.json').read_text())
    def valid_generation(output):
        for key in ('claims', 'concepts'):
            rows = output[key]
            if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
                raise ValueError('invalid benchmark ' + key)
            ids = [row['id'] for row in rows]
            if any(not isinstance(value, str) or not value for value in ids) or len(set(ids)) != len(ids):
                raise ValueError('invalid benchmark IDs')
        concepts = {row['id'] for row in output['concepts']}
        for claim in output['claims']:
            if (claim['concept_id'] not in concepts or
                    any(not isinstance(claim[key], str) for key in ('text', 'source_id', 'quote'))):
                raise ValueError('invalid benchmark claim')

    def stage(name, prompt, model, effort, live=False, validate=None, upstream=None):
        path = destination / name / 'run.json'
        binding = stage_fingerprint(prompt, model, effort, live, upstream)
        if path.exists():
            try:
                cached = json.loads(path.read_text())
                if cached['is_error'] is False and cached.get('input_sha256') == binding:
                    if not isinstance(cached['output'], dict):
                        raise TypeError('benchmark response must be an object')
                    validate(cached['output'])
                    return cached
            except (ValueError, KeyError, TypeError):
                pass
        if path.parent.exists():
            # Keep every failed or interrupted attempt, including its raw logs.
            saved = destination / 'attempts' / name / datetime.now(UTC).strftime('%Y%m%dT%H%M%S.%fZ')
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path.parent), str(saved))
        (destination / 'metrics.json').unlink(missing_ok=True)
        record = call(prompt, model, effort, destination / name, timeout, live)
        record['input_sha256'] = binding
        if not record['is_error']:
            try:
                if not isinstance(record['output'], dict):
                    raise TypeError('benchmark response must be an object')
                validate(record['output'])
            except (ValueError, KeyError, TypeError) as error:
                record.update(is_error=True, contract_error=str(error))
        write(path, record)
        return record
    generated = stage('generation', generation_prompt(packet, skill, live), model, effort, live,
                      validate=valid_generation)
    if generated['is_error']:
        return {'cell': destination.name, 'failed': 'generation'}
    judged = stage('judge', judge_prompt(generated['output'], packet), 'gpt-6-astra', 'high',
                   validate=lambda value: metrics(generated['output'], value, packet),
                   upstream=generated['input_sha256'])
    if judged['is_error']:
        return {'cell': destination.name, 'failed': 'judge'}
    result = metrics(generated['output'], judged['output'], packet)
    result.update(domain=domain, skill=skill, model=model, effort=effort, retrieval='live-assisted' if live else 'fixed-evidence',
                  live_search_used=any('search' in tool for tool in generated.get('tools', [])),
                  generation_seconds=generated['seconds'], judge_seconds=judged['seconds'],
                  generation_usage=generated['usage'], judge_usage=judged['usage'],
                  actual_cost_usd=None, estimated_cost_usd=None,
                  cost_basis='provider did not expose USD; no rate card supplied',
                  packet_sha256=fingerprint(packet), output_sha256=fingerprint(generated['output']))
    write(destination / 'metrics.json', result)
    return result


def report(out, public, rate_card=None):
    rows = [json.loads(p.read_text()) for p in sorted((out / 'cells').glob('*/metrics.json'))]
    if rate_card:
        if not rate_card.get('as_of') or not rate_card.get('source_url'):
            raise ValueError('estimated costs require a dated sourced rate card')
        for row in rows:
            generator = rate_card['models'].get(row['model'])
            judge = rate_card['models'].get('gpt-6-astra')
            if generator and judge:
                row['estimated_cost_usd'] = estimate_cost(row['generation_usage'], generator) + estimate_cost(row['judge_usage'], judge)
                row['cost_basis'] = {'kind': 'estimate', 'as_of': rate_card['as_of'], 'source_url': rate_card['source_url']}
    write(public / 'comparison.json', rows)
    lines = ['# Multi-domain research canary', '',
             'One live-assisted trial per domain and configuration. These small samples do not establish a model ranking. Model and effort vary together; this compares configurations.',
             'Primary text is frozen and hashed for scoring. Live search leads are counted separately.',
             'Quality requires full entailment, an atomic unique statement and an exact quote in the supplied packet. A rejected claim is not automatically false.',
             'Astra/high supplies blind judgments; exact quotes and statement bindings are checked deterministically.',
             'Reference facts await human review. Costs remain unknown; tokens are measured. Raw evidence/logs stay private.', '',
             '| Domain | Model / effort | Concepts raw / grounded | Facts raw / supported unique | Quality | Depth / 3 | Mechanisms | Contradictions | Seconds |',
             '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in rows:
        lines.append(f"| {r['domain']} | {r['model']} / {r['effort']} | {r['raw_concepts']} / {r['grounded_unique_concepts']} | {r['raw_claims']} / {r['unique_supported_facts']} | {r['quality_percent']}% | {r['mean_claim_depth']} | {r['mechanisms']} | {r['contradictions']} | {r['generation_seconds']} |")
    (public / 'comparison.md').write_text('\n'.join(lines) + '\n')
    return len(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'run', 'report'])
    parser.add_argument('--private-out', type=Path, required=True)
    parser.add_argument('--public-out', type=Path, default=ROOT / 'docs/research/research-system-hardening-2026-10-22')
    parser.add_argument('--skills', nargs='+', default=['dr'], choices=['dr', 'concept-family-explorer', 'rabbithole'])
    parser.add_argument('--retrieval', choices=['live', 'fixed'], default='live')
    parser.add_argument('--workers', type=int, default=3)
    parser.add_argument('--timeout', type=int, default=600)
    parser.add_argument('--rate-card', type=Path, help='Optional dated sourced per-million token rates for report estimates')
    args = parser.parse_args()
    if args.action == 'prepare':
        prepare(args.private_out)
    elif args.action == 'run':
        failures = []
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = [pool.submit(cell, args.private_out, d, m, e, s, args.retrieval == 'live', args.timeout)
                       for d in DOMAINS for m, e in CELLS for s in args.skills]
            for future in as_completed(futures):
                try:
                    result = future.result()
                except (ValueError, KeyError, TypeError) as error:
                    result = {'failed': 'contract-validation', 'error': str(error)}
                if result.get('failed'):
                    failures.append(result)
                print(json.dumps(result), flush=True)
        write(args.private_out / 'failures.json', failures)
        report(args.private_out, args.public_out)
        return int(bool(failures))
    else:
        card = json.loads(args.rate_card.read_text()) if args.rate_card else None
        print(report(args.private_out, args.public_out, card))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
