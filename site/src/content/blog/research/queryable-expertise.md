---
title: "Queryable expertise: research memory, private skills and checked optimization"
description: "How a local Neo4j research index, provenance-preserving MCP tools and a private skill registry turn existing work into reusable expertise, with implementation details and measured limits."
date: '2026-11-11'
category: research
tags: [research, neo4j, retrieval, mcp, skills, provenance]
---

## Abstract

Useful research becomes expensive when the next task cannot find it, establish which revision it describes, or recover the evidence behind a conclusion. Agent skills have a similar problem: copies accumulate across projects and clients, names collide, and an instruction file alone may omit the scripts and references that make it usable.

This implementation addresses those problems with two connected services. A local research service projects canonical research files into Neo4j, combines full-text and vector retrieval, and returns exact source passages through the Model Context Protocol (MCP). A skill registry indexes installed guides, distributes complete private releases, and brokers optional optimization jobs whose candidates remain separate from their originals.

The November 11, 2026 installation contained 2,318 research documents and 45,786 passage vectors. Its skill catalog described 3,742 sources across 4,342 installations. A repeated research import left all 2,318 documents unchanged and wrote zero passages. Live demonstrations saved and retrieved sourced research, distributed a seven-file skill into a fresh offline installation, and produced code and skill candidates that passed five configured functional cases each. These are bounded implementation results. Imported research remains unreviewed, retrieval has not passed a representative quality benchmark, and the demonstrated optimizer runs did not certify complete native convergence. [The publication evidence extract](#evidence-and-reproducibility) preserves those distinctions.

## The problem: remembering an answer is not enough

A folder of research can preserve text while losing practical access to it. A later agent still has to discover the right file, load enough of it to understand the subject, locate its sources, and determine whether the answer applies to the current task. Repeating a web search is often easier than navigating that history. The result is duplicated acquisition, duplicated summarization and competing versions of the same explanation.

Putting every document into a language model's context changes the cost rather than resolving the organization problem. The reader still needs boundaries around relevance, source identity and uncertainty. Likewise, placing all prose in a vector index answers a narrower question: which stored passages resemble this query? It does not establish whether the source file has changed or whether the passage's claim is supported.

The requirement was therefore more specific than persistent chat memory. Existing work needed to become queryable expertise: discoverable by meaning and exact terms, navigable through explicit relationships, attributable to a particular source revision, and reusable without treating every imported statement as established fact. Skills also needed to travel with their supporting resources, work locally, and remain accessible through a private central service.

The design gives each object a defined authority. It then builds search, graph and distribution services around those authorities. This avoids requiring a user to edit the same research in a file, a graph and a remote catalog whenever a conclusion changes.

## One authority for each kind of object

The implementation uses different stores because research prose, search indexes, executable workflows and published versions have different lifecycles.

| Object | Authority | Derived or distributed representation |
| --- | --- | --- |
| Editable research | Canonical research pack and its source evidence | Neo4j documents, passages, vectors and navigation |
| Editable skill | Canonical skill directory | Local catalog and installation aliases |
| Shared skill version | Immutable release manifest and complete verified bundle | Download cache and new offline installations |
| Optimization input | Immutable input snapshot | Isolated candidate and retained execution records |
| Research qualification | The applicable evidence and validation contract | A label returned alongside retrieved text |

The main data paths are:

```text
Canonical research packs -> Neo4j and passage vectors -> Research MCP
Editable skill trees    -> SQLite catalog            -> Skill MCP
Editable skill trees    -> Immutable private release -> Verified offline copy
Input snapshot          -> Owner-local worker        -> Checked candidate
```

A research pack contains a manifest and prose, with optional navigation and source material. The initial importer reads immediate `.llms` packs, prefers their facts layer, and falls back to the full prose layer. It excludes alternate renderings, backups and staging. This is a defined import scope rather than an assertion that every file on the host has been indexed. [The corpus implementation and package guide](https://github.com/mithudso/llms-explorer/tree/c458299c2b83d276806036f465c8802c32ac29f1/hub/research-expertise) describe that selection.

Neo4j holds a projection that can be rebuilt from those files. The skill catalog is also derived. A changed local guide can be reindexed without changing an already published release. To share a later revision, its owner publishes another version. Keeping that boundary explicit makes both current editing and reproducible installation possible.

The graph stores corpus, document, passage, concept and cited-source nodes. Relationships connect documents to their passages and subjects, and preserve declared concept navigation. A citation URL is a useful edge, but it is not a per-claim entailment judgment. This release does not extract causal assertions or invent community summaries from the prose.

## How research becomes retrievable

### Import files without losing their identity

Ingestion inventories eligible packs and records the hashes that determine their identity. Each document replacement is transactional. Unchanged documents can reuse their existing passage vectors; changed documents receive a new projection. A completed inventory deactivates deleted packs and removes their searchable embeddings.

This last step matters for approximate nearest-neighbor search. Retired vectors can occupy a limited candidate set even when later filtering excludes their documents. The lifecycle audit reproduced that failure and repaired the retirement path. The test establishes a particular stale-candidate defect and its repair; it does not establish that every narrow query will return its requested number of results.

An exclusive ingestion lock rejects overlapping writers. A failed run keeps documents it successfully imported, so a retry can continue from exact file and manifest identities. The importer does not rename old vectors into a new model space merely to make a migration appear finished.

### Bind embeddings to a complete recipe

The dedicated embedding backend runs BGE-small on CPU. The recorded recipe uses `BAAI/bge-small-en-v1.5`, the `Qdrant/bge-small-en-v1.5-onnx-Q` repository, revision `aa8f8b060edb00e03bfdd08813a2949946c8ba55`, and 384 dimensions. Its identity also includes the FastEmbed version and the passage/query route recipe. Token-aware splitting limits passages to 480 content tokens. Oversized queries fail with a request to shorten them rather than silently dropping their end.

Pinning only a model name would leave a reproducibility gap. Two installations could use that name while loading different files or processing routes. The cache, document skip decisions and dense retrieval candidates therefore require the same complete embedding-space identity. A changed recipe requires an explicit refresh; a changed dimension also requires a compatible vector index.

The first model download obtains public model files. Prose embedding happens locally. This service did not require an external embedding API, a GPU or an Ollama process. That choice gives retrieval its own runtime without a dependency on a shared generation server, while accepting CPU time, local storage and a pinned-runtime maintenance obligation. The deployment used Python 3.14 because the locked ONNX runtime did not supply the required Python 3.15 wheel.

### Combine exact terms with semantic candidates

Search obtains one ranked list from Neo4j full-text search and another from its vector index. It combines those ranks using reciprocal rank fusion. In this implementation, a passage contributes `1 / (60 + rank)` from each ranking in which it appears. Combining ranks avoids requiring raw full-text and cosine scores to share a numerical scale.

Full-text retrieval helps with identifiers and explicit terminology. The vector route helps when a reader describes the same subject in different words. Their combination is an implementation choice, not evidence that hybrid retrieval is universally best. A representative evaluation set is still needed to compare methods, filters and candidate depths for this corpus.

Before returning a passage, the application compares the current canonical document and manifest with the recorded hashes. Captured research also checks its declared members. Changed or deleted sources are excluded until refreshed. Results retain exact Unicode character offsets, line spans, content hashes, a canonical source location, the concept and the qualification label. A later caller can request one passage by identifier or follow explicit neighbors without loading the whole corpus.

The official Neo4j MCP remains useful for schema inspection and read-only Cypher. Those direct database reads bypass the expertise application's source-freshness checks. For an answer that needs current cited prose, the bounded expertise interface is the appropriate default. [The search and freshness code](https://github.com/mithudso/llms-explorer/blob/c458299c2b83d276806036f465c8802c32ac29f1/hub/research-expertise/src/research_expertise/store.py) makes this distinction inspectable.

## Capturing new research through the same workflow

Research capture starts after an agent has read its sources. The agent supplies a question, summary, atomic findings, source text and exact quotations. `expertise_save_research` checks the supplied structure and verifies that each required quotation occurs in its supplied source. It writes the canonical pack first, then refreshes its graph and vector projection.

Saving and indexing have separate outcomes. A successful canonical save can remain pending if refresh fails. The returned `indexed` result becomes true only after read-back confirms the specific saved document and complete passage vectors. An identical retry can finish a pending refresh without creating a second paper. Updating an existing owned capture requires its current manifest checksum, and prior revisions remain in private history.

Exact quotation matching is a mechanical check. It cannot decide whether a quotation supports the complete finding, whether the supplied source is trustworthy, or whether the researcher actually performed the reading they describe. The capture stays `unreviewed` until the applicable research qualification process accepts its assertions. A manifest that says `SUPPORTED` or `COMPLETED` is preserved as authored metadata and does not override that qualification.

The [recorded capture demonstration](/downloads/research/queryable-expertise/evidence.json) asked whether a vector index guarantees that retrieved research still matches an edited source file. Four source snapshots supported five qualified findings. The first save changed one document and wrote five passages. Replaying it changed none and wrote none. A subsequent paraphrased search returned the saved capture at rank three, with a matching source span and hash. This demonstrates persistence, idempotent replay and one retrieval path, rather than a general retrieval-accuracy result.

That workflow removes a practical handoff: newly acquired research does not need to be copied into an unrelated memory store before it can be reused. Its canonical source, evidence and retrievable projection remain connected.

## What the research tools do

MCP provides the interface between an agent and these bounded operations. The research server exposes four read tools and one explicit capture tool. It does not expose arbitrary filesystem ingestion or arbitrary Cypher through that interface. [The complete capture schema and bounds](https://github.com/mithudso/llms-explorer/blob/c458299c2b83d276806036f465c8802c32ac29f1/hub/research-expertise/MCP.md) are versioned with the code.

| Tool | Use it for | Why choose it |
| --- | --- | --- |
| `expertise_status` | Coverage, projection state and embedding identity | Establish which corpus and vector space are available |
| `expertise_search` | A question, optional concept filter and bounded top results | Recover relevant source passages before commissioning new research |
| `expertise_passage` | One returned passage identifier | Obtain its complete citation and freshness details |
| `expertise_neighbors` | A concept's explicit directed neighborhood | Follow related subjects and cited sources deliberately |
| `expertise_save_research` | A sourced capture with findings and quotations | Save new research into the canonical workflow and confirm its indexing outcome |

Research tool work serializes on one owner thread. A status call can wait behind a long capture, and cancelling a client wait does not undo canonical writes already running. Inspect the outcome after completion or retry the identical capture; do not assume a cancelled wait rolled back the save.

The separately configured official Neo4j server exposes `get_schema` and `read_cypher`. These support database inspection and diagnostic read queries. The installed upstream Neo4j skills cover Cypher, modeling, vector indexes, GraphRAG, MCP and the Python driver. The project-specific research skill explains when to use the bounded expertise tools and how to retain their qualification. A skill supplies operating guidance; an MCP server supplies callable operations.

## Making scattered skills discoverable

The skill router addresses a different retrieval unit. A guide needs a stable source identity, its installation aliases and a resource base for resolving relative references. The local SQLite FTS catalog stores those fields and hashes the guide's current content. Loading a result rechecks its hash and returns a bounded text span with continuation offsets.

Two guides with the same name remain separate when their canonical sources differ. Multiple installations that resolve to one source remain aliases. Explicit client disable decisions are shown rather than changed. Catalog presence does not prove that a particular native client has loaded or enabled the guide.

The installation found 3,742 sources across 4,342 installations in nineteen configured roots. It reported 135 invalid guides instead of silently repairing them. Those counts describe filesystem coverage. The index covers guide bodies lexically; it does not semantically index every supporting reference. Lookups refresh derived metadata, and an index-only watcher refreshes the configured roots every fifteen minutes in this installation.

An actual automatic-policy test exposed a routing defect: a query for `skill-optimizer` could rank generic mentions above the installed guide and bury the exact result outside the first twenty hits. The repair gives exact names, source paths and alias folder names priority. Native optimizer selection now uses a direct, hash-checked exact resolver rather than depending on a general search result limit. Registry resolution and topical search have related purposes, but they should not share that failure mode.

## Sharing a complete, private skill version

A useful skill often includes scripts, contracts, references and eval assets. Distributing only `SKILL.md` can leave a syntactically valid installation that cannot perform its advertised task. Packaging therefore snapshots the approved regular-file tree and binds every member's path, size, SHA256 and executable flag.

The `skill-release/v1` manifest identifies an account namespace, name and exact semantic version. The release hash derives from canonical manifest JSON independently of ZIP timestamps. Validation enforces bounds of 128 files, 2 MiB per member, 5 MiB expanded and 6 MiB uploaded. It rejects traversal, symlinks, duplicate or case-colliding members, invalid modes, encrypted entries, missing or extra members and checksum mismatches. Packaging rereads the tree to detect concurrent edits.

The hosted adapter uses existing account authentication and scoped `read`, `run` and `publish` keys. A release is private. Its owner can grant another registered account read access to that particular version; that grant does not authorize changing or optimizing the owner's release. Published content is immutable. Public community uploads await a moderation adapter.

Downloads require an exact release pin. The client validates the bundle before caching it; installation then works offline and requires a new destination. This prevents a routine fetch from replacing an existing installation. External absolute resource pointers and dependencies need a portability review because packaging does not automatically gather them. A checksum establishes identity, not redistribution rights or execution trust.

The hosted distribution demonstration used a seven-file Markdown-heading skill. Actual MCP calls packaged it, explicitly published it privately, found it and fetched the exact pin into a fresh cache. Installation succeeded with networking disabled. A wrong pin was rejected, anonymous access returned 401, and a second install into the same directory exited 2. Those observations exercise distribution and overwrite protection without claiming that the skill completed every native quality evaluation.

## Optional optimization that preserves the original

Optimization is an explicit job, not a side effect of search. Supported artifact kinds are skill, code, document, query, prompt and agent. Each maps to its installed native optimizer definition. A missing definition is an explicit limitation. Generic artifact inputs are single UTF-8 files; a full skill input includes its approved supporting resources.

The local worker snapshots the input, creates a separate candidate workspace and records its input identity. Trusted operator configuration selects the worker argv and verification commands. Jobs have a deadline, bounded iteration request, private logs, a lease and cancellation/retry state. Automatic policies require per-skill enablement. The default policy budgets are 600 seconds, three iterations and one job per scheduling cycle; watch mode indexes only unless automatic optimization and a trusted backend are selected.

The remote API brokers a request and its outcome. The owner-local worker claims it, verifies the snapshot, renews its lease, invokes the backend locally and submits exactly the checked candidate. HTTP handlers do not execute uploads or start providers. The built-in Codex adapter disables configured user MCP servers, plugin/App tools and sandbox tool network access per run, and strips registry credentials from worker and check environments. A custom local worker remains trusted code under the operator's account, rather than a multi-tenant sandbox.

The result separates execution, configured checks, native convergence and publication. A provider exit of zero establishes that the process completed successfully. A checker exit of zero establishes the checker result. Neither proves that the native optimizer's independent reviews and full eval suite ran. The service retains the worker's convergence report as unverified, and never automatically overwrites the original or publishes the candidate.

The [retained optimizer observations](/downloads/research/queryable-expertise/evidence.json) show this separation. A code candidate repaired first-seen ordering by replacing `list(set(values))` with `list(dict.fromkeys(values))`. An independent five-case checker failed against the original and passed against the candidate, with the original hash unchanged. The native report remained `PARTIAL`. An automatically scheduled full-skill job repaired heading extraction and passed five functional cases, while retaining `EVALS-MISSING`. A hosted code request completed through the owner-local worker in 86.448 seconds; its returned candidate hash matched the checked local bytes, while native `IMPROVED` remained a report rather than certified convergence.

## What the skill and optimizer tools do

The same stdio server exposes local catalog, private distribution and job operations. This lets an agent find an existing guide, read it deliberately and use a small operation set instead of constructing broad filesystem or shell actions. [The registry MCP contract](https://github.com/mithudso/llms-explorer/blob/c458299c2b83d276806036f465c8802c32ac29f1/hub/skill-registry/MCP.md) specifies its bounds.

| Tool | Use it for | Result boundary |
| --- | --- | --- |
| `skills_status` | Catalog counts and last refresh | Filesystem coverage, not native activation |
| `skill_lookup` | Find task-relevant local guides | Source-bound routing candidates |
| `skill_load` | Read a chosen guide at an expected hash | Bounded source text and resource base |
| `skills_refresh` | Refresh configured roots | Derived metadata; no embeddings or source edits |
| `skill_package` | Build a complete versioned bundle | A local release, still unpublished |
| `skill_remote_search` | Find releases visible to the account | Authorized private metadata |
| `skill_remote_fetch` | Retrieve an exact pinned release | Verified local cache |
| `skill_remote_publish` | Publish a reviewed bundle explicitly | Private publication requiring scope |
| `optimizer_submit` | Queue a bounded input snapshot | No model invocation by itself |
| `optimizer_policy` | Enable or disable one automatic policy | Explicit per-skill scheduling choice |
| `optimizer_schedule` | Queue eligible policy inputs | Cycle-capped queue operations |
| `optimizer_status` | Read job progress and outcomes | Separate execution, checks and convergence |
| `optimizer_cancel` | Cancel or request a running stop | Persisted cancellation state |
| `optimizer_retry` | Recover an interrupted or failed attempt | New workspace, retained prior attempt |
| `optimizer_claim` | Give a local agent a private lease | One authorized input snapshot |
| `optimizer_finish` | Submit an external worker candidate | Checked bytes with reported native outcome |

## Implementing the system

The implementation is available as two standalone packages in the public repository. The commands below use the recorded source revision so readers can compare behavior with this account of the work. They are setup instructions, not evidence that a reader's host has already passed acceptance.

### Prepare the local research service

Use a local Neo4j Community installation with Bolt enabled, `uv`, and a supported Python runtime. The recorded installation used Neo4j 2026.10.2 and Python 3.14. Keep the authenticated database on loopback. Create `$HOME/.config/neo4j-expertise/connection.json` with the connection object below. Replace the password locally and restrict the file to mode 600. Do not commit it or put its password in MCP configuration.

```json
{"uri":"bolt://127.0.0.1:7687","username":"neo4j","password":"SET_LOCALLY","database":"neo4j"}
```

The file-locking and atomic-publication paths target macOS and Linux. The recorded live installation was macOS; Linux package CI is separate from that live acceptance.

```sh
git clone https://github.com/mithudso/llms-explorer.git
git -C llms-explorer checkout c458299c2b83d276806036f465c8802c32ac29f1
cd llms-explorer/hub/research-expertise
uv sync --frozen --python 3.14
uv run --frozen pytest -q
python3 install.py
export PATH="$HOME/.local/bin:$PATH"
```

The installer copies the application to a stable user location outside the checkout and creates the CLI and MCP entrypoints. On macOS, `python3 install.py --schedule` adds an hourly refresh for this corpus. On other hosts, omit that flag and arrange an explicit refresh schedule. The installer locks against an active ingest, retains the previous app and environment, and restores them if setup fails. The recorded failure-injection acceptance verified restoration of 4,139 prior files.

Supply the eligible `.llms` packs before ingestion. Cloning the code does not populate the user directory in this example; create and populate that directory or pass another trusted existing pack root. Counts depend on the supplied corpus snapshot. Then inspect status and a small query:

```sh
research-expertise ingest --root "$HOME/.global-ai-hub/llms-concepts"
research-expertise status
research-expertise search "How do source revisions affect saved embeddings?" --top 5
```

Confirm that the intended corpus is present, the embedding migration flag is clear, and the returned passage points to a source that can be read. Inspect qualification as well as ranking. An empty result can reflect import scope, stale-source exclusion, filters or candidate depth; it does not prove the subject has never been researched.

Configure `research-expertise-mcp` through its absolute installed entrypoint in the chosen MCP client. Reload that client before expecting new tools. Use the official Neo4j server separately for schema and read-query diagnostics. For portable research export, select a concept with `research-expertise export --concept CONCEPT --out OUTPUT.zip`, review the bundle's rights and metadata, then ingest its extracted `packs/` directory on the receiving host.

### Add local skill lookup and private distribution

From the checked-out repository, install the registry with its MCP extra:

```sh
cd "$(git rev-parse --show-toplevel)"
uv tool install './hub/skill-registry[mcp]' --python 3.13
skill-registry refresh
skill-registry lookup 'ai-rag-retrieval'
```

The command assumes the shell is at the repository root. Configure trusted roots, the optional remote URL and locally trusted worker/check argv in `$HOME/.config/skill-registry/config.json`, or set `SKILL_REGISTRY_CONFIG` to another configuration file. The [version-pinned package guide shows the JSON configuration contract](https://github.com/mithudso/llms-explorer/blob/c458299c2b83d276806036f465c8802c32ac29f1/hub/skill-registry/README.md#L44-L58). Add project roots deliberately. A guide lookup returns the local source ID and hash; pass both into the subsequent load. Read references from the returned resource base rather than assuming another copy's directory layout.

For a team service, deploy the existing API with PostgreSQL and apply its additive skill-release migration. Its [declared dependencies](https://github.com/mithudso/llms-explorer/blob/c458299c2b83d276806036f465c8802c32ac29f1/api/pyproject.toml) and [environment contract](https://github.com/mithudso/llms-explorer/blob/c458299c2b83d276806036f465c8802c32ac29f1/api/.env.example) also require shared-library access and the configured account and service secrets. Local lookup and offline installation work without that hosted deployment. Reuse the account/key system rather than adding another credential authority. The recorded private origin is https://api.llms-explorer.com; using it requires an authorized account key. Supply a scoped key through `SKILL_REGISTRY_TOKEN` or a mode-600 file named by `SKILL_REGISTRY_TOKEN_FILE`. Configure the remote origin over HTTPS. The client permits loopback HTTP for local acceptance, refuses redirects and keeps credentials out of bundles.

An owner can package a source with `skill-registry package LOCAL_SKILL_ID --namespace ACCOUNT_ID --name my-skill --version 1.0.0`, publish its returned hash explicitly, and fetch it elsewhere with the exact namespace, name, version and hash. `skill-registry install RELEASE_SHA256 NEW_DIRECTORY` then installs from the local cache. These identifiers come from the owner's actual package and account; substitute those values rather than treating an example as a public release credential.

### Enable optimization only after configuring its checks

Before running either worker example, install and authenticate the Codex CLI used by `--backend codex`. Install the applicable native optimizer guide within the indexed roots: `ddo` for the document example and `skill-optimizer` for automatic skill maintenance. Refresh the catalog and confirm that lookup finds the intended guide. Automatic skill scheduling requires its installed definition; a generic worker completion does not establish native convergence.

In the registry configuration, set `check_commands` to trusted, read-only argv arrays. For example, `["python3", "/absolute/path/to/your-reviewed-checker.py", "{target}"]` invokes a checker that you must provide; `{target}` becomes the candidate path. The default `check_commands: []` provides no configured functional verification. Start with a disposable owned input and a checker that fails the original defect and passes the intended behavior. Do not derive its expected answer from the candidate itself. Queueing is separate from execution:

```sh
skill-registry optimize document --file ./draft.md --timeout 600 --max-iter 3
skill-registry work --backend codex --max-jobs 1
```

For repeated skill maintenance, enable a policy for one owned source, then select automatic work explicitly:

```sh
skill-registry policy LOCAL_SKILL_ID --enable --interval 86400 --timeout 600 --max-iter 3
skill-registry watch --auto-optimize --backend codex --max-jobs 1
```

Inspect the resulting job, candidate and checks before applying an edit or publishing a release. Keep a path to the original snapshot. A successful worker does not remove the need for review of behavior the configured checker did not cover. For hosted work, `remote-optimize` queues the owner's text input and `remote-work JOB_ID --backend codex` executes it through that owner's local runtime; `remote-job JOB_ID` reads the broker's outcome.

## What the implementation saves, and what it costs

The strongest measured saving is avoided repeated indexing work. The recipe migration wrote 45,786 passages for 2,318 documents. An unchanged repeat wrote zero. The small capture demonstration similarly wrote five passages once and zero on replay. These measurements show idempotence and reuse for those runs. They do not quantify money, energy, model tokens or end-to-end research time.

Other savings are structural. Passage retrieval can give an agent the cited section it needs instead of requiring every source document in context. Stable hashes let the caller determine which revision it used. The skill catalog recovers a source and its resource base across multiple installations. A verified release cache allows reuse without another download. A retained optimization attempt avoids losing the original when a proposed change fails.

Each saving has a corresponding obligation. The operator must maintain a database, model files, caches, private logs, backups and refresh behavior. Source-hash checks add filesystem work to retrieval. Complete skill bundles need portability and redistribution review. Owner-local optimization consumes the selected provider's capacity and can create candidate work that still needs human judgment. The project did not measure a universal total-cost reduction or a break-even point.

The system is most useful when research and procedures recur across tasks, when multiple agents need the same source history, or when a team needs a pinned workflow version on more than one host. A small one-off note may need only a file and ordinary search. The additional services earn their place through repeated use and traceable reuse, rather than through the presence of a graph alone.

## Evidence and reproducibility

The source was delivered through [the lifecycle repair PR](https://github.com/mithudso/llms-explorer/pull/329) and [the private registry PR](https://github.com/mithudso/llms-explorer/pull/333). The latter merged as `c458299c2b83d276806036f465c8802c32ac29f1`. The recorded API deployment served that revision, and acceptance compared its actual process working directory and 37 API Python modules with the merged archive. A final fresh stdio invocation compared all twelve installed registry modules with the same source and exercised the sixteen-tool interface.

The [redacted evidence JSON](/downloads/research/queryable-expertise/evidence.json) publishes the selected observations behind the numerical claims here. It includes source-receipt hashes, test outcomes, the capture replay counts and optimizer input/candidate identities. The full retained records contain private local paths and execution material, so this publication does not export them wholesale. The extract is author-recorded evidence, not a signed third-party attestation. Public source and CI provide a separate route for readers to inspect and repeat the checks.

| Recorded check | Result | Limit |
| --- | --- | --- |
| Research package | 130 passed; one normal opt-in skip; exit 0 | Separate live Neo4j integration passed |
| Native research contracts | 445 tests and 15 subtests passed; exit 0 | Bound to that source/check run |
| Registry package | 72 passed; exit 0 | Does not certify arbitrary uploaded skill behavior |
| Full API suite | 307 passed; three existing warnings; exit 0 | Real PostgreSQL fixtures, not every production scenario |
| Live API contract | Seven requests, 25 Postman assertions, zero failures; exit 0 | Selected private distribution/status endpoints |
| Registry delivery CI | Thirteen applicable checks passed; promote skipped | Installed and hosted acceptance were checked separately |
| Corpus refresh | 2,318 documents, 45,786 vectors, 3,218 explicit relations | Imported prose remains unreviewed |

The audit repaired fourteen defects, including embedding identity, retirement, capture revision conflicts, transaction scratch isolation, installer rollback and MCP ownership. Its coverage was 17 of 636 inventoried source files. It retained `BLIND-AUDIT-DISSENT` because a second independent audit found the retired-vector defect; that defect was repaired with an executed failing/passing integration witness, but a third clean blind audit was not run. That history supports the named fixes, while leaving the broader audit explicitly partial.

## Maintenance and remaining limits

The implementation still needs a held-out retrieval evaluation covering exact identifiers, paraphrases, stale sources and narrow filters. It also needs an adapter that binds accepted native research assertions and their evidence into the graph without treating authored status text as proof. Semantic skill ranking, general multi-file repository snapshots, log byte quotas and retention, and public community moderation remain future work.

A version-specific maintenance item also emerged while writing this paper. The delivered store uses `db.index.vector.queryNodes`. Neo4j's 2026.10 source marks its Cypher 25 declaration deprecated since 2026.04 in favor of `SEARCH`; the separate Cypher 5 declaration is not marked deprecated there. The retained deployment records do not establish which query language the run used, so they do not establish that its working route was deprecated or demonstrate a migration to the replacement syntax. [The upstream declarations](https://github.com/neo4j/neo4j/blob/2026.10/community/procedure/src/main/java/org/neo4j/procedure/builtin/VectorIndexProcedures.java#L158-L184) give that maintenance boundary directly.

The useful outcome is a repeatable chain: recover existing work, inspect its exact source and qualification, save new evidence into the same canonical workflow, and share or improve a bounded artifact without losing its history. Start with one corpus and one trusted skill. Confirm actual retrieval, a pinned offline installation and a defect-sensitive checker before extending the system to more material.
