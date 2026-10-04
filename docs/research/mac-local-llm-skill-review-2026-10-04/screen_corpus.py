#!/usr/bin/env python3
"""Screen a local reference corpus without model, network or GPU operations.

This records complete file/section coverage. Tags select dossiers for human
review; they do not establish claim truth or local hardware qualification.
"""

import argparse
import hashlib
import json
import re
import sqlite3
from collections import Counter
from pathlib import Path

SKILL = Path('/Users/mitch/.claude/skills/running-llm-models-locally-on-mac-expert')
PATTERNS = {
    'agent-context-cache-parser': r'claude|codex|coding.agent|tool.call|tool.parser|reasoning|chat.template|prompt.cache|context.checkpoint|context.shift|compaction|prefix.stab',
    'host-memory-stability': r'footprint|memorystatus|jetsam|wired.memory|kernel.panic|watchdog|compressor|memory.pressure|vm.pressure|memory.account',
    'numerical-quality-quant': r'kld|quantization|quantized|self.flip|top.1|tail.risk|numerical|float16|fp16.*overflow|benchmark|parity',
    'speculation-hybrid': r'speculative|mtp|recurrent|gateddeltanet|hybrid.model|checkpoint',
    'apple-backend-only': r'mlx|metal|ane|core.ml|core.ai|foundation.models',
    'cluster-offload-only': r'jaccl|rdma|distributed|exo|engram|expert.offload|ssd|thunderbolt.bridge',
}


def inspect(root):
    files = []
    contents = {}
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            raise ValueError(f'Refuse symlink: {path}')
        if path.is_file():
            raw = path.read_bytes()
            name = path.relative_to(root).as_posix()
            if raw.startswith(b'SQLite format 3\x00'):
                kind = 'sqlite'
            else:
                contents[name] = raw.decode('utf-8')
                kind = 'utf8'
            files.append({'path': str(path), 'bytes': len(raw),
                          'format': kind, 'lines': len(raw.splitlines()) if kind == 'utf8' else None,
                          'sha256': hashlib.sha256(raw).hexdigest()})
    json_files = {name: json.loads(text) for name, text in contents.items() if name.endswith('.json')}
    manifest = json_files['llms/manifest.json']
    install = json_files['.become-expert.json']
    skill_version = re.search(r'^version: "([^"]+)"', contents['SKILL.md'], re.M).group(1)
    clustered = 'clusters' in manifest
    fact_ranges = {}
    correction_ranges = {}
    fact_count = 0
    topic_fact_count = 0
    correction_rows = []
    for name, text in contents.items():
        is_facts = name.endswith('/llms-facts.txt')
        is_corrections = name.endswith('/llms-corrections.txt')
        if not (is_facts or is_corrections):
            continue
        for n, line in enumerate(text.splitlines(), 1):
            if ' :: ' not in line:
                continue
            slug = line.split(' :: ', 1)[0]
            item = {'path': str(root / name), 'line': n}
            if is_facts:
                fact_ranges.setdefault(slug, []).append(item)
                fact_count += 1
                topic_fact_count += int('/topics/' in name)
            if is_corrections or (clustered and name == 'llms/llms-facts.txt'):
                correction_ranges.setdefault(slug, []).append(item)
                correction_rows.append({**item, 'slug': slug,
                    'tags': [tag for tag, pattern in PATTERNS.items() if re.search(pattern, line, re.I)]})
    sections = []
    verdicts = Counter()
    for name, text in contents.items():
        if not name.endswith('/llms-full.txt'):
            continue
        full = text.splitlines()
        anchors = [(i, re.search(r'id="([^"]+)"', line).group(1))
                   for i, line in enumerate(full) if line.startswith('<a id=')]
        cluster = name.split('/')[2] if '/topics/' in name else None
        if cluster and len(anchors) != manifest['clusters'][cluster]['concepts']:
            raise ValueError(f'Cluster coverage mismatch: {cluster}')
        for j, (start, slug) in enumerate(anchors):
            end = anchors[j + 1][0] if j + 1 < len(anchors) else len(full)
            block = '\n'.join(full[start:end])
            heading = next(line[3:] for line in full[start:end] if line.startswith('## '))
            verdict = re.search(r'verdict: (SATURATED-DEPTH|BUDGET_EXHAUSTED)', block)
            verdicts[verdict.group(1) if verdict else 'unclassified'] += 1
            tags = [tag for tag, pattern in PATTERNS.items() if re.search(pattern, heading + ' ' + slug, re.I)]
            terms = {tag: len(re.findall(pattern, block, re.I)) for tag, pattern in PATTERNS.items()}
            sections.append({'slug': slug, 'title': heading, 'cluster': cluster,
                             'source': str(root / name),
                             'start_line': start + 1, 'end_line': end,
                             'tags': tags, 'whole_section_term_counts': terms,
                             'source_url_count': len(set(re.findall(r'\[src: (https?://[^\]]+)\]', block))),
                             'facts_lines': fact_ranges.get(slug, []),
                             'correction_lines': correction_ranges.get(slug, []),
                             'scope': 'screened; material sections receive human source review'})
    unique = len({x['slug'] for x in sections})
    expected = manifest['counts']['done']
    if len(sections) != expected or unique != expected:
        raise ValueError('Manifest/full-dossier coverage mismatch')
    database = None
    db = root / 'llms/facts.db'
    if db.exists():
        connection = sqlite3.connect(db.as_uri() + '?mode=ro&immutable=1', uri=True)
        try:
            clusters = Counter()
            tags = Counter()
            rows = 0
            contradicts = 0
            for claim, concept, cluster, source, tag, contradiction in connection.execute('select claim,concept,cluster,source,tag,contradicts from facts'):
                rows += 1
                clusters[cluster] += 1
                contradicts += int(bool(contradiction))
                for kind, pattern in PATTERNS.items():
                    tags[kind] += int(bool(re.search(pattern, str(claim) + ' ' + str(concept), re.I)))
            database = {'path': str(db), 'read_only': True, 'quick_check': connection.execute('pragma quick_check').fetchone()[0],
                        'rows_screened': rows, 'clusters': dict(clusters), 'relevance_tag_counts': dict(tags),
                        'contradiction_flag_rows': contradicts, 'derived_index_not_independent_evidence': True}
        finally:
            connection.close()
    current_paths = sorted(str(p) for p in root.rglob('*') if p.is_file())
    if current_paths != [f['path'] for f in files]:
        raise ValueError('Source file set changed while screening')
    for item in files:
        if hashlib.sha256(Path(item['path']).read_bytes()).hexdigest() != item['sha256']:
            raise ValueError(f"Source changed while screening: {item['path']}")
    return {'version': '1.1.0', 'method': 'read every file as bytes; parse complete JSON and text; screen all dossier bodies, facts, corrections and SQLite rows; no semantic/model inference',
            'skill_root': str(root), 'files': files, 'skill_version': skill_version,
            'manifest_skill_version': manifest.get('skillVersion'),
            'install_skill_version': install.get('skillVersion'),
            'manifest_generated_at': manifest.get('generatedAt'),
            'rounds': manifest['rounds'], 'counts': manifest['counts'],
            'research_verdicts': dict(verdicts), 'cluster_count': len(manifest.get('clusters', {})), 'json_files_parsed': len(json_files),
            'file_count': len(files), 'full_dossiers': len(sections),
            'facts_rows': fact_count, 'topic_fact_rows': topic_fact_count,
            'correction_rows': len(correction_rows), 'all_sections_screened': True,
            'all_claims_independently_fact_checked': False,
            'hardware_operations': 0, 'model_requests': 0,
            'sections': sections, 'corrections': correction_rows, 'database': database}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skill', type=Path, default=SKILL)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--verify-against', type=Path)
    args = parser.parse_args()
    if not args.output and not args.verify_against:
        parser.error('provide --output or --verify-against')
    result = inspect(args.skill.resolve())
    if args.verify_against:
        baseline = json.loads(args.verify_against.read_text())
        if result != baseline:
            raise SystemExit('Corpus differs from saved inventory; review the delta.')
    if args.output:
        with args.output.open('x') as stream:
            json.dump(result, stream, indent=2)
            stream.write('\n')
    print(json.dumps({k: result[k] for k in ['file_count', 'skill_version', 'full_dossiers', 'facts_rows', 'correction_rows', 'all_sections_screened', 'hardware_operations', 'model_requests']}))


if __name__ == '__main__':
    main()
