"""Assemble exact current source dependencies; no imports, services or model read."""
from pathlib import Path
import hashlib,json,os,stat,types,datetime
R=Path(__file__).absolute().parent;P=R/'production'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(4*1024**2),b''):h.update(block)
 return h.hexdigest()
def write(p,d):
 fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'w') as f:json.dump(d,f,indent=2,sort_keys=True);f.write('\n')
# Only source files owned by this preparation may be finalized here.
common_sha=sha(R/'downstream_common.py')
for p in R.iterdir():
 if p.is_file() and p.name not in ('PROMPT.md','MEMORY.json'):
  if p.suffix=='.py' or p.name in ('claude_candidate','egpu_research_agent','litellm_gateway'):
   t=p.read_text()
   if "COMMON_SHA='bb144de159e83520305a37528697a70273a2fdbbcac539e55e612f6dd4ac1d6b'" in t:
    p.write_text(t.replace("COMMON_SHA='bb144de159e83520305a37528697a70273a2fdbbcac539e55e612f6dd4ac1d6b'","COMMON_SHA='"+common_sha+"'"))
   p.chmod(0o700 if p.name in ('claude_candidate','egpu_research_agent','litellm_gateway') else 0o600)
base=P/'static-inputs/INDEPENDENT-REVIEW.json';prep=P/'capture-response-preparation/PREPARATION.json'
assert sha(base)=='2c3b3b95c6aab23523c7885dea7281d52e029c7ccbc14a066ae1197e11fbc11c'
assert sha(prep)=='371b73eafb27429f86ea3ae658bcb7e29d85fa0d54fd6ea5021fd04027d19d2a'
d=json.loads(base.read_bytes());d.update(version='1.0.0',passed=False,seal_pending=True,independent_review_pending=True,issuer='author-source-draft-only',physical_launch_ready=False,cold_admission_issued=False)
d.pop('sealed_at',None);d['independent_audit']=None;d['source_draft']=None
d['scope']='Source-only fresh same-owner full coding pair/canonical standard DR; original production numerical admission and actual independent root activation remain mandatory.'
m=types.ModuleType('held_closure_renderer');m.__file__=str(P/'renderer-preparation/experimental_27b.py');exec(compile((P/'renderer-preparation/experimental_27b.py').read_bytes(),m.__file__,'exec'),m.__dict__)
pins=d['source_pins'];aliases={};added=[]
def add(value,alias=False):
 lexical=Path(value).absolute();canonical,chain=m.alias_chain(str(lexical));p=Path(canonical)
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_uid in (0,501) and not s.st_mode&0o022
 digest=sha(p)
 if str(p) in pins:assert pins[str(p)]==digest,('Accepted dependency drift',str(p))
 else:pins[str(p)]=digest;added.append(str(p))
 if m.external_input(str(p)):d['external_source_bindings'][str(p)]={'canonical':str(p),'sha256':digest,'metadata':m.metadata(s),'aliases':[]}
 if str(lexical)!=str(p) or alias:aliases[str(lexical)]={'canonical':str(p),'sha256':digest,'metadata':m.metadata(s),'aliases':chain}
for p in sorted(R.iterdir()):
 if p.is_file() and p.name not in ('MEMORY.json','PROMPT.md','PRODUCTION-FREEZE.json') and (p.suffix in ('.py','.json','.txt') or p.name in ('claude_candidate','egpu_research_agent','litellm_gateway')):add(p)
add(base);add(prep)
# Exact reused helper closure, not paths guessed from a canonical folder name.
for root in (Path('/Users/mitch/dev/llms-explorer/llmsx'),Path('/Users/mitch/.cache/claude-egpu/experiments/qwen35-9b-admission/read-binding-diagnostics-preparation-v100')):
 for p in sorted(root.rglob('*')):
  if p.is_file() and p.suffix=='.py' and '__pycache__' not in p.parts:add(p)
old_plan=json.loads(Path('/Users/mitch/.cache/claude-egpu/experiments/qwen35-27b-standard-dr-experiment-v125/PLAN.json').read_bytes())
for name in old_plan['source_pins']:
 p=Path(name)
 if p.is_file() and '/site-packages/' not in name and p.suffix in ('.py','.md','.mjs') and not any(x in name for x in ('gateway-config','gateway-key','PLAN.json')):add(p)
for s in ('/Users/mitch/.cache/claude-egpu/experiments/qwen35-9b-admission/coding-summary-prompt-v109/verify_egpu_coding.py','/Users/mitch/.cache/claude-egpu/experiments/qwen35-9b-admission/coding-summary-prompt-v109/egpu_coding_profile.py','/Users/mitch/.cache/claude-egpu/experiments/egpu-pinned-client-2.1.286-v100/claude','/Users/mitch/.global-ai-hub/scripts/dr_run.py','/Users/mitch/.global-ai-hub/scripts/dr_assets/gate.md','/Users/mitch/.agents/skills/claude-command-dr/SKILL.md','/Users/mitch/.agents/skills/skill-optimizer/SKILL.md','/Users/mitch/.claude/skills/skill-optimizer/SKILL.md','/Users/mitch/.claude/skills/concept-family-explorer/scripts/sync_trees.py','/Users/mitch/.claude/skills/concept-family-explorer/references/tree-sync.md','/Users/mitch/.claude/scripts/skill_optimizer_offline.py','/Users/mitch/.claude/skill-consolidation/convergence-and-severity.md','/Users/mitch/.claude/skill-consolidation/convergence_check.py','/Users/mitch/.claude/skill-consolidation/champion-challenger.md','/Users/mitch/.claude/skill-consolidation/cross-model-gate.md','/Users/mitch/.claude/skill-consolidation/gen-skills-index.mjs','/Users/mitch/.global-ai-hub/scripts/concept_tree.py','/Users/mitch/dev/llms-explorer/site/tools/gen_tree.py','/Users/mitch/.global-ai-hub/scripts/semantic_ops/router.py'):
 add(s)
for p in sorted(Path('/Users/mitch/dev/skills/skill-optimizer/references').glob('*.md')):add(p)
creator=Path('/Users/mitch/.claude/plugins/cache/claude-plugins-official/skill-creator/517b2fcd1b60/skills/skill-creator')
for p in sorted(creator.rglob('*.py')):add(p)
# Actual runtime import bytes/data, including caches that Python can consume.
venv=Path('/Users/mitch/.local/pipx/venvs/litellm')
for p in sorted((venv/'lib').rglob('*')):
 if p.is_file() and (p.suffix in ('.py','.pyc','.so','.json','.yaml','.yml','.pth') or p.name in ('METADATA','RECORD')):add(p)
for s in (str(venv/'pyvenv.cfg'),str(venv/'bin/python'),str(venv/'bin/litellm'),'/opt/homebrew/bin/python3','/usr/bin/node','/usr/bin/sqlite3','/bin/ps','/usr/sbin/sysctl','/usr/sbin/lsof'):
 if Path(s).exists():add(s,alias=s.endswith('/python') or s=='/opt/homebrew/bin/python3')
d['runtime_alias_bindings']=aliases;d['source_pin_count']=len(pins)
d['production_source_authority']={'path':str(base),'sha256':sha(base)};d['production_request_authority']={'path':str(prep),'sha256':sha(prep)}
d['actual_session_identity']=None;d['actual_numerical_acceptance']=False;d['registry_status']='REGISTRY-UNAVAILABLE';d['full_qualification']=False
write(R/'DOWNSTREAM-REVIEW-DRAFT.json',d)
write(R/'DEPENDENCY-ADDITIONS.json',{'version':'1.0.0','observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'new_source_pins':{p:pins[p] for p in added},'runtime_alias_bindings':aliases,'unchanged_production_source_authority':d['production_source_authority'],'new_dependency_count':len(added),'total_count':len(pins),'role':'Current source-only dependency closure; not historical equality or actual loaded/inference identity','native_invocations':0,'model_reads':0})
print(json.dumps({'draft':str(R/'DOWNSTREAM-REVIEW-DRAFT.json'),'sha256':sha(R/'DOWNSTREAM-REVIEW-DRAFT.json'),'source_count':len(pins),'new_count':len(added),'alias_count':len(aliases),'model_reads':0}))
