"""Independent bounded source consumers. Never execute an operational tail."""
from pathlib import Path
import ast, copy, datetime, hashlib, json, os, stat, types

OUT = Path(__file__).absolute().parent
ROOT = Path('/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-downstream-preparation-v125')
FREEZE_SHA = '72cbc7231b2379afb82ad60d8bd9b3efac55aa1ee31bef4ef8fb6a2d62d30925'
DRAFT_SHA = '71d7fda85e639bc99562aa0213bcf92a35cb5b704706e1c1596c8acf389f2f5e'
checks = []

def check(name, value, detail=None):
    if not value:
        raise AssertionError(name)
    checks.append({'name': name, 'passed': True, 'detail': detail})

def hold(path, expected, mode=0o600):
    path = Path(path)
    assert path.is_absolute() and path.resolve(strict=True) == path
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        a = os.fstat(stream.fileno())
        assert stat.S_ISREG(a.st_mode) and a.st_uid == 501
        assert stat.S_IMODE(a.st_mode) == mode and 0 < a.st_size <= 16 * 1024**2
        raw = stream.read(16 * 1024**2 + 1)
        b = os.fstat(stream.fileno())
    key = lambda s: (s.st_dev, s.st_ino, s.st_uid, s.st_gid, stat.S_IMODE(s.st_mode), s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    assert key(a) == key(b) == key(path.lstat())
    assert hashlib.sha256(raw).hexdigest() == expected
    return raw

def module(path, raw, name, prefix_only=False):
    m = types.ModuleType(name)
    m.__file__ = str(path)
    tree = ast.parse(raw, str(path))
    if prefix_only:
        selected = []
        for node in tree.body:
            if isinstance(node, (ast.Expr, ast.Import, ast.ImportFrom, ast.Assign, ast.AnnAssign, ast.FunctionDef)):
                if isinstance(node, ast.Expr) and not (isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)):
                    break
                selected.append(node)
            else:
                break
        tree.body = selected
    exec(compile(tree, str(path), 'exec'), m.__dict__)
    return m

observed_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
freeze = json.loads(hold(ROOT/'DOWNSTREAM-FREEZE.json', FREEZE_SHA))
frozen = {}
launchers = {'claude_candidate', 'egpu_research_agent', 'litellm_gateway'}
for name, digest in freeze['frozen_sources'].items():
    path = Path(name)
    frozen[name] = hold(path, digest, 0o700 if path.name in launchers else 0o600)
check('actual immutable freeze bytes, canonical paths, exact owner/modes and stable reads', len(frozen) == 65)
review = json.loads(frozen[str(ROOT/'DOWNSTREAM-REVIEW-DRAFT.json')])
check('exact source draft and source-only no acceptance flags',
      hashlib.sha256(frozen[str(ROOT/'DOWNSTREAM-REVIEW-DRAFT.json')]).hexdigest() == DRAFT_SHA
      and review['actual_session_identity'] is None
      and all(review[k] is False for k in ('passed', 'actual_numerical_acceptance', 'full_qualification', 'physical_launch_ready', 'coding_verified', 'standard_research_verified')))
production = json.loads(frozen[str(ROOT/'production/static-inputs/INDEPENDENT-REVIEW.json')])
old = production['source_pins']
check('retained production pin values unchanged, without replaying old hashes',
      all(review['source_pins'].get(p) == digest for p, digest in old.items()), len(old))
check('4752 retained plus16462 added current source pins', len(old) == 4752 and len(review['source_pins']) == 21214)
check('retained1748 external identities preserved',
      all(review['external_source_bindings'].get(p) == v for p, v in production['external_source_bindings'].items()), len(production['external_source_bindings']))

cpath = ROOT/'downstream_common.py'
c = module(cpath, frozen[str(cpath)], 'independent_downstream_common')
r = c.renderer()
r.configure_source_bindings(review)
consumed = []
for path, raw in frozen.items():
    if path in review['source_pins']:
        actual = r.verified_file(path, review['source_pins'][path], limit=16*1024**2)['data']
        assert actual == raw
        consumed.append(path)
check('actual renderer hash/metadata consumers of frozen pinned sources', len(consumed) > 50, len(consumed))

alias_results = []
for alias in review['runtime_alias_bindings']:
    binding = c.runtime_alias(alias, review, r)
    alias_results.append({'path': alias, 'canonical': binding['canonical'], 'sha256': binding['sha256'], 'passed': True})
check('existing actual runtime_alias consumer accepts all ten exact current aliases', len(alias_results) == 10)

def unexpected(*_args, **_kwargs):
    raise AssertionError('Operational observation forbidden in source review')
c.observe = unexpected
c.passive_owner = unexpected
try:
    c.admission({})
except ValueError as error:
    check('actual missing activation prefix refuses before observations', 'authority' in str(error))
else:
    raise AssertionError('Missing authority admitted')
original_private_bytes = c.private_bytes
c.private_bytes = lambda *_: json.dumps({'actual': False, 'root_authorized': False, 'seal_pending': True}).encode()
try:
    c.admission({'EGPU_DOWNSTREAM_AUTHORITY': str(ROOT/'ROOT-ACTIVATION.json'), 'EGPU_DOWNSTREAM_AUTHORITY_SHA256': '0'*64})
except ValueError as error:
    check('actual pending activation fixture refuses before observations', 'pending' in str(error), 'Only authority bytes are an in-memory fixture; no physical identity asserted')
else:
    raise AssertionError('Pending authority admitted')
finally:
    c.private_bytes = original_private_bytes

entrypoints = ('claude_candidate', 'egpu_research_agent', 'litellm_gateway', 'start_gateway.py', 'run_coding_pair.py', 'run_standard_dr.py', 'verify_downstream_receipts.py')
for name in entrypoints:
    path = ROOT/name
    m = module(path, frozen[str(path)], 'independent_prefix_'+name.replace('.', '_'), prefix_only=True)
    held = m.common()
    assert held.BINARY_SHA == review['identity']['binary_sha256']
    try:
        held.admission({})
    except ValueError as error:
        assert 'authority' in str(error)
    else:
        raise AssertionError('Protected entrypoint admitted absent activation')
check('seven actual held common-loader entry prefixes refuse unactivated input', True,
      'Only imports/constants/functions compiled; no top-level operational tail or main called')

profile_path = Path('/Users/mitch/.cache/claude-egpu/experiments/qwen35-9b-admission/coding-summary-prompt-v109/egpu_coding_profile.py')
profile = c.load_source(profile_path, review, r, 'independent_original_profile')
check('original full23 coding schema retained', len(profile.FULL_CODING_TOOLS) == 23)
client_path = ROOT/'claude_candidate.py'
client = module(client_path, frozen[str(client_path)], 'independent_argument_client')
argument_common = module(cpath, frozen[str(cpath)], 'independent_argument_common')
argument_common.admission = lambda env: (None, review, {}, r)
argument_common.passive_owner = lambda _: True
client.common = lambda: argument_common
actual_verify_pins = r.verify_pins
r.verify_pins = lambda _: None
try:
    args = profile.coding_arguments(bounded_context=True) + ['-p', 'Implement actual task', '--model', c.ALIAS, '--output-format', 'json']
    inv = client.prepare(args, {})
    check('actual client keeps original full coding prefix and exact candidate gateway',
          inv['mode'] == 'coding' and inv['env']['ANTHROPIC_BASE_URL'] == c.GATEWAY
          and inv['env']['EGPU_CLAUDE_BIN'] == str(ROOT/'claude_candidate')
          and inv['env']['DR_CLAUDE_BIN'] == str(ROOT/'egpu_research_agent'),
          'Argument-only fixture stubs actual owner and full retained closure rehash; no actual acceptance')
finally:
    r.verify_pins = actual_verify_pins

contract = json.loads(frozen[str(ROOT/'ACCEPTANCE-CONTRACT.json')])
check('original unchanged numerical contract explicitly retained',
      contract['numerical'] == {'requests':2,'cache_prompt':False,'tokens':64,'compared_positions':21,'include_eos':True,'absolute_selected_logprob_threshold':0.05,'reference':'current-OS CPUv111','production_capture_key_absent':True})
check('original two-session21-gate coding contract and six research tools retained',
      contract['coding']['original_gates'] == 21 and contract['coding']['sessions'] == 2
      and len(contract['research']['worker_tools']) == 6)
check('five concepts, three origins, negation, quote/read/source, blind10/refetch15/full A-O retained',
      len(contract['research']['concepts']) == 5 and contract['research']['organizations_each'] == 3
      and contract['research']['negation'] and contract['research']['typed_literal_quote_read_source_bindings']
      and contract['research']['blind_sample'] == 10 and contract['research']['refetch_cap'] == 15
      and contract['research']['sko_passes'] == list('ABCDEFGHIJKLMNO')
      and contract['research']['canonical_finish_required'] and contract['research']['both_trees_required'])
check('original profile/verifier/current canonical skill references in exact closure',
      all(str(p) in review['source_pins'] for p in (
          profile_path, Path(contract['coding']['reused_verifier']),
          Path('/Users/mitch/.global-ai-hub/scripts/dr_run.py'),
          Path('/Users/mitch/.agents/skills/claude-command-dr/SKILL.md'),
          Path('/Users/mitch/dev/skills/skill-optimizer/SKILL.md'))))

text = lambda name: frozen[str(ROOT/name)].decode()
check('prior witness/session mismatch corrected at actual common reader',
      all(s in text('downstream_common.py') for s in ('Witness path differs','Completed witness identity differs','copy_completed','compute_completed')))
check('post-workflow source directly bound after workers',
      "c.private_bytes(ROOT/'FULL-DR-POST-WORKFLOW.txt',review['source_pins']" in text('run_standard_dr.py'))
check('gateway listener-child binding and held preloads corrected',
      'Gateway metadata listener differs' in text('start_gateway.py')
      and 'Gateway listener differs from admitted child' in text('downstream_common.py')
      and 'sys.modules[name]=c.load_source' in text('litellm_gateway'))
check('all seven future receiver/authority paths remain absent',
      all(not (ROOT/p).exists() and not (ROOT/p).is_symlink() for p in (
          'ROOT-ACTIVATION.json','ROOT-QUALITY-REVIEW.json','execution','production/cold-runtime',
          'production/capture-inference','DOWNSTREAM-INDEPENDENT-REVIEW.json','production/cold-root-operation/RESULT.json')))

for path, raw in frozen.items():
    assert hold(path, freeze['frozen_sources'][path], 0o700 if Path(path).name in launchers else 0o600) == raw
assert hold(ROOT/'DOWNSTREAM-FREEZE.json', FREEZE_SHA)

receipt = {
    'agent': '/root/cold_capture_review', 'definition_version': '1.0.0', 'version': '1.0.0',
    'status': 'complete', 'scope': 'Independent frozen source-delta audit only; conditional readiness for root source authority',
    'observed_at': observed_at, 'passed': True, 'freeze': {'path': str(ROOT/'DOWNSTREAM-FREEZE.json'), 'sha256': FREEZE_SHA},
    'source_draft': {'path': str(ROOT/'DOWNSTREAM-REVIEW-DRAFT.json'), 'sha256': DRAFT_SHA},
    'frozen_files': len(frozen), 'actual_source_consumers': len(consumed), 'source_pins': len(review['source_pins']),
    'retained_pins': len(old), 'retained_external_bindings': len(production['external_source_bindings']),
    'new_dependency_current_hash_replay': False, 'checks': checks, 'runtime_alias_checks': alias_results,
    'operations': {'subprocesses':0,'HTTP':0,'model':0,'native':0,'GPU':0,'service_actions':0,'campaign_initializations':0},
    'evidence': [
        {'source': str(ROOT/'DOWNSTREAM-FREEZE.json'), 'observed_at': observed_at, 'supported_claim':'All65 exact current immutable created sources/proofs held and rechecked without operational tail'},
        {'source': str(cpath), 'observed_at': observed_at, 'supported_claim':'Actual held admission refuses absent/pending activation before observation; ten exact runtime_alias consumers pass now'},
        {'source': str(ROOT/'ACCEPTANCE-CONTRACT.json'), 'observed_at': observed_at, 'supported_claim':'Original numerical/coding/research contracts retained; paused registry/trigger-eval/current physical gaps explicit'}],
    'changes': ['Only this caller-designated audit script and receipt in reviewer private directory'],
    'remaining': ['Root final source authority and exact final prefix readback', 'Fresh physical boot/owner startup, actual independent original numerical acceptance', 'Root ten-alias and exact route preflight before every quality phase, separate raw witness snapshots', 'Two actual full coding sessions then standard five-concept DR/full canonical quality/both trees', 'Explicit paused registry capability remains unavailable; physical peak and long-term stability remain unmeasured'],
    'details': {
        'surface':'Frozen downstream source preparation, not a loaded model/client/gateway',
        'acceptance_condition':'Exact source/helper bindings and retained original contracts; actual physical acceptance must remain false',
        'source_revision':DRAFT_SHA, 'loaded_revision':None, 'process_or_origin':None,
        'configuration_identity':review['identity'], 'observations':checks, 'mismatches':[],
        'unverified_checks':['Actual future session identity/numerical/coding/DR','Full new dependency rehash independently replayed','Aggregate physical peak/long-term stability','Independent raw coding witness recomputation'],
    },
    'operational_conditions': {
        'alias_helper': {'path':str(cpath), 'sha256':freeze['frozen_sources'][str(cpath)], 'signature':'runtime_alias(path, review, r)'},
        'root_alias_procedure':'Immediately before every future quality phase, load exact held downstream_common source and accepted renderer, configure_source_bindings(final_review), then call runtime_alias(path, final_review, r) for all ten runtime_alias_bindings. Refuse any exception; do not use this present snapshot as later alias acceptance.',
        'route_boundary':'Admission applies to intended run_standard_dr.py orchestration, which uses common.environment(auth). The generic protected research bootstrap retains inherited-environment defaults/overrides. Root must bind exact clean environment and argv for every future adapter child; standalone research bootstrap is not certified as enforcing no fallback.',
        'raw_phase_snapshot_helper': {'path':str(ROOT/'production/capture-response-preparation/run_numeric.py'),'sha256':'2dd3fc37e179e83404f423c92749e3dd91c99d8e47ca6aaa10c38dfe59921c75','signature':'evidence_snapshot(name, startup, save)'},
        'raw_snapshot_limit':'Parent may save separate before/after phase raw snapshots through accepted helper after real bound owner exists. Frozen coding helper saves attribution deltas without raw before/after; this review does not independently recompute them.',
    },
    'qualification': {'actual_session_identity':None,'numerical_accepted':False,'coding_accepted':False,'standard_dr_accepted':False,'full_sko_accepted':False,'physical_peak_accepted':False,'full_qualification':False},
}
path = OUT/'TASK620-DOWNSTREAM-SOURCE-REVIEW.json'
with path.open('x') as stream:
    json.dump(receipt, stream, indent=2); stream.write('\n')
path.chmod(0o600)
print(json.dumps({'passed':True,'checks':len(checks),'actual_source_consumers':len(consumed),'runtime_aliases':len(alias_results),'receipt':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}))
