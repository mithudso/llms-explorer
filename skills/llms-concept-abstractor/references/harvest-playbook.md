# Harvest playbook — resolving scope and running the three retrieval passes

<!-- llms-concept-abstractor · references/harvest-playbook.md · 2026-08-31 -->

**Contents** 1. Scope kinds → files · 2. Discovering scope (`--match`, `--estate`) ·
3. The three retrieval passes · 4. Precision / recall levers · 5. Size and cost guidance ·
6. Commands cheat-sheet

Paths are on this estate: hub `~/.global-ai-hub` (scripts run as
`cd ~/.global-ai-hub && PYTHONPATH=scripts .venv/bin/python scripts/<x>.py`), mirrors and
exports under `~/.claude/skills/web-text-mirror/text-mirror/`, the script
`PY="python3 ~/.claude/skills/llms-concept-abstractor/scripts/concept_abstract.py"`.

## 1. Scope kinds → files

| scope | what to pass to `--from` | reader | notes |
|---|---|---|---|
| **hub docset export** `<host>.llms/` | `<host>.llms/llms-facts.txt` | facts | best default: typed, anchored, deduped; ≈ 5–15 % of the raw text |
| — with code / more units | `<host>.reference/all_units.jsonl` (or `units.jsonl`) | units | includes `snippet` bodies and extractor units; 2–4× the facts file |
| — raw pages | `<host>.md` (banner mirror) | pages | every paragraph is a candidate `passage`; use when the facts layer is missing or thin |
| **mirrored third-party llms-full** | `~/.global-ai-hub/llms-full/files/<key>.txt` (`hub_llms_full_list` → key) | pages | grammar varies: `Source:` lines split pages; `# Title (/path)` H1s need `--base-url https://host`; rights = extractive |
| **topical / concept pack** | `llms-topical/<slug>.llms/llms-facts.txt`, `llms-concepts/<slug>.llms/llms-facts.txt` | facts | re-abstracting a sub-concept out of a parent pack |
| **/dr research spoke** | `~/.claude/skills/<skill>/references/<x>.md` | pages | anchors are headings; sources are the spoke's footnote URLs only if you pre-convert; treat as owned text |
| **local textbook / manual** (PDF, EPUB, DOCX) | convert first: `document-conversion` (pandoc / pdftotext) → `book.md`; then `--from book.md --context 1 --rights quote` | pages | one file per chapter gives better anchors; heading-based anchors carry the +0.25 |
| **URL / site** | `web-text-mirror` (depth per need) → `<host>.md`; optionally `docset_refine export` to get a facts layer | pages/facts | do not fetch live pages in the loop; mirror once |
| **pasted text** | write it to the scratchpad as `.md` | pages | anchor = paragraph index |
| **directory** | the dir itself | auto | picks `units.jsonl` → `all_units.jsonl` → `llms-facts.txt` → else every `.md/.txt/.jsonl` under it |
| **glob** | `'text-mirror/*.llms/llms-facts.txt'` | auto | quote it |

Every reader emits the same unit shape (`id, type, text, source_url, anchor, heading_path,
keywords, origin, source_kind`), so mixed scopes are fine in one harvest. IDs are
`s<NN>u<NNNNNN>` — `s` numbers the input file, which is how the report attributes hits.

## 2. Discovering scope

`--match "<theme>"`:
1. `hub_llms_full_list(query="<theme>")` and `hub_llms_full_list(category="<theme>")` — mirrored sites by host/title/category (e.g. `database` → drizzle, prisma, thenile…).
2. `hub_list_docsets()` / `docset_indexer.py list` — indexed hub docsets; match on key and `source_path`.
3. `ls text-mirror/*.llms` — exported docsets; match host names and the `title` in each `manifest.json`.
4. The hub root index `http://127.0.0.1:8788/llms.txt` — categorical H2s list docsets per category.
5. `hub_concept_lookup` — a tree node's `skillId` names a skill whose `references/` are in scope too.

Print the resolved list (file, unit count from a dry `harvest` on the bare name, or the
manifest's counts) and let the user cut it *before* the real rounds. A theme match is a
guess; the user knows which vendors matter.

`--estate`: `text-mirror/*.llms/llms-facts.txt` + `llms-full/files/*.txt` + `llms-topical/*/llms-facts.txt`.
Scanning is cheap (≈ 20k units/s on the facts layer; llms-full mirrors are larger — the 766
files total ≈ 720 MB, so an estate harvest of the mirrors takes minutes, not seconds). Run
round 0 on the facts files only, look at `sources` in the report, then add the mirrors whose
hosts already scored.

## 3. The three retrieval passes

Cheapest first; each later pass catches what the previous one cannot. Passes 1 and 2 both
run on every pack; pass 3 is the model.

1. **Keyword (script, exact)** — `harvest` with the lexicon. Precise, free, recall bounded by
   the lexicon. Word-boundary, case-insensitive, plural-tolerant, hyphen/space tolerant in
   multi-word terms. Heading/anchor matches count (+0.25) because a paragraph under
   "## Coronary circulation" is about the heart even when it names only arteries.
2. **Semantic index (script, meaning)** — `semantic` embeds every unit in scope with
   `mxbai-embed-large` (ollama; the hub's model, so vectors are comparable with the hub's
   docset layers) into an append-only on-disk cache (`~/.global-ai-hub/llms-concepts/.embcache/
   <model>/vectors.f32 + keys.txt`, sha1 of the text → row). Scoring is **centred and
   z-scored**: `raw = max(cos(u, query_i), cos(u, centroid))`, `adj = raw − cos(u, scope_mean)`,
   `z = (adj − mean)/sd` over the scope. Raw cosine is not usable as an absolute floor — mxbai
   sits at ~0.5 for unrelated text and every unit of an API docset is "about the API";
   subtracting the scope mean removes that background and z-scoring makes 3.0 mean the same
   thing on a 400-unit chapter and a 20k-unit estate scan. Outputs: `semantic.jsonl` (adds at
   `z ≥ --z`, capped by `--max-add`), `pool.jsonl` annotated with `semantic_z`,
   `semantic-report.json` (`z_bands_in_scope`, `keyword_suspects` = keyword hits with
   `z < 0.5`, `candidates_by_meaning`, `near_terms`, near-dup folds). Measured on the
   prompt-caching smoke scope (12k units, 3 docsets): `z≥3.5` → 17 adds at ~70 % precision,
   `z≥3.0` → 42 mixed, `z≥2.5` → 95 mostly noise — hence the default 3.0 with the bands
   printed so the model can move it. First embedding of 12k units ≈ 2 min; re-runs are
   seconds. Requires numpy (present in the system python and the hub venv).
   Hub-indexed docsets add a free third signal: `hub_query_docset(<key>, q, mode="hybrid",
   top=20)` per facet phrasing → hits in neither pool go into a hand-written `extra.jsonl`
   (unit schema) for `--from`.
3. **LLM adjudication (Step 5)** — `view` → `classified.jsonl`. The model decides borderline
   inclusion (`keyword_suspects`, `~sem` adds with `z < 3.5`, `score < 1.0`), re-facets prose,
   marks conflicts. It never *finds* units; it judges the ones passes 1–2 found. That keeps
   the model's reading bounded by the pool, not by the corpus.

Ollama: `semantic` checks `GET /api/tags` first; `--restart-ollama` does `pkill -f "ollama
serve"` → `open -a Ollama` / `brew services restart ollama` / `ollama serve` and waits ≤ 40 s.
Env: `OLLAMA_HOST`, `HUB_EMBED_MODEL`, `LCA_EMBED_CACHE` override the defaults.

## 4. Precision / recall levers

| symptom | lever |
|---|---|
| foreign sense in `facts` (index finger, heart of the matter) | read `keyword_suspects` in `semantic-report.json` first — they are exactly these; add `exclude`; if the sense shares the bare word, `--min-score 0.8` |
| semantic pass adds hundreds / adds nothing | `--z 3.5` / `--z 2.5`; read `z_bands_in_scope` before choosing; on a very broad concept the centroid dominates — check `centroid_from_pool_top` and lower `--centroid-top` |
| ollama unreachable | `semantic --restart-ollama`; check `curl localhost:11434/api/tags`; never ship keyword-only without saying so |
| contrast-term pages flood the pool (batch API in a caching pack) | keep the core rule on; lower the contrast term's `weight` to 0.5; drop units in Step 5 |
| too few units, concept clearly present | more `synonym`/`variant`/`part` terms from `candidates`; `--no-require-core` for round 0 only; add `all_units.jsonl` or the raw `.md` |
| zero-hit terms you are sure exist | check spelling variants in `aka`; the pattern needs a word boundary — `cache_control` matches, `cache-control` needs an `aka` |
| pack dominated by one host | it may be right (the concept's home); otherwise add hosts to scope or split |
| textbook paragraphs too long / too short | `--context 1` for short paragraphs; for long ones the extractor split is per paragraph — pre-split with a heading per subsection if the conversion lost them |
| many near-duplicate lines across sources | exact dedupe keeps one and lists the others under `also:`; near-dup folding is `/ldo`'s job (P7) — do not hand-merge |

## 5. Size and cost guidance

- Pool after the final round: 100–800 units is the sweet spot for one concept. > 2000 means a
  family — `split --groups groups.json` by the strongest `part`/`hyponym` term clusters (eval-2:
  2,699 indexing units → 5 children of 254–565 units, 23–49k tokens each; the parent stays the
  union and links them under `## Child packs`).
- The harvest prefilter (`harvest-report.prefiltered`) drops nav link lines, link lists, MDX
  imports, frontmatter and heading-only short fragments; on the prompt-caching smoke scope it
  removed 438 of 18,893 scanned units before scoring and cut the keyword pool 214 → 148 with no
  loss on the question bank. On broad concepts the semantic pass adds little (eval-2: 1 add at
  z ≥ 3.5) — there it earns its keep as the suspects list and the near-dup fold.
- Model reading budget for Step 5 ≈ targeted buckets + 10 % sample; at 140-char `view`
  lines that is ~40 tokens/unit — 500 units ≈ 20k tokens. Use `--limit` and `--facet` to
  page through.
- `llms-small.txt` default 8k tokens; textbooks and multi-vendor packs read better at
  12–16k. `llms-full.txt` at 10–40 % of the scanned *facts* text is normal; > 60k tokens
  triggers the split rule.
- Harvest and compile are sub-second per 20k units; re-running is free — iterate rather
  than reason about what a run would do.

## 6. Commands cheat-sheet

```bash
PY="python3 ~/.claude/skills/llms-concept-abstractor/scripts/concept_abstract.py"
M=~/.claude/skills/web-text-mirror/text-mirror
OUT=~/.global-ai-hub/llms-concepts/<slug>.llms

# round 0 (bare name) → read candidates
$PY harvest --lexicon lexicon.json --out $OUT --from $M/<host>.llms/llms-facts.txt ...
python3 -c "import json;r=json.load(open('$OUT/harvest-report.json'));print(r['kept_units'],r['zero_hit_terms']);print([c['token'] for c in r['candidates'][:40]])"

# leakage check
$PY view $OUT --facet facts --min-score 0.6 --limit 40

# final harvest, then the semantic pass over the same scope (reads/annotates pool.jsonl)
$PY harvest --lexicon lexicon.json --out $OUT --from <files...>
$PY semantic --lexicon lexicon.json --out $OUT --from <files...> [--z 3.0] [--restart-ollama]
python3 -c "import json;r=json.load(open('$OUT/semantic-report.json'));print(r['z_bands_in_scope'],r['added'],len(r['keyword_suspects']))"


# classification pass
$PY view $OUT --min-score 0 --width 140 > view.txt        # read in pages
# → write classified.jsonl

# compile + stats + probe
$PY compile --out $OUT --lexicon lexicon.json --classified classified.jsonl --concept "<name>" --summary "..." --budget-tokens 8000
$PY stats $OUT
$PY probe $OUT --questions bank.jsonl --semantic
$PY query $OUT "how does the cache TTL work" --top 5

# index (optional)
cd ~/.global-ai-hub && PYTHONPATH=scripts .venv/bin/python scripts/docset_indexer.py index $OUT/units.jsonl --units --name concept__<slug>
cd ~/.global-ai-hub && PYTHONPATH=scripts .venv/bin/python scripts/docset_indexer.py keyword-index concept__<slug>
```
