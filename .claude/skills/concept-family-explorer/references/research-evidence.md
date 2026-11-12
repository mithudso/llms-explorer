## Evidence required before publication

Apply this contract to every factual assertion, including summaries, inherited parent
facts, disagreements, open-question premises and final dossiers. Discovery leads and
coverage labels do not establish support.

- Keep each atomic claim's exact statement, immutable claim ID, source URL, source
  snapshot hash, exact quoted passage and locator together. For v4, author an `evidence`
  list of spans with `url`, `source_id`, `snapshot_sha256`, `start`, `end`, `quote` and
  `extraction_status: complete`. Mark complete only after reading a usable source;
  the attestation never overrides a missing identifier or invalid span. Read the snapshot;
  a URL, reference list, cache hash or model recollection supplies no evidence credit.
- Run deterministic integrity checks over **all** claims before paid semantic review.
  Require each quote to exist in the pinned body and belong to the cited source.
  Check exact technical identifiers, values, units and applicability against the
  passage. Missing identifiers or an incomplete Markdown derivative require readable
  rendered HTML, original RST/source or another complete primary source; withhold the
  assertion until reacquisition succeeds. A keyword match alone does not prove support.
- A semantic judge decides whether the passage supports the complete assertion,
  including negation, version, scope and caveats. It cannot override a failed integrity
  check. In research-gate/v4, review every new or changed factual assertion once.
  Reuse a prior validated SUPPORTED verdict only when the exact assertion and bound
  source snapshots are unchanged. Structural binding alone cannot qualify publication.
  Do not turn structural failures into expensive blanket multi-model reruns.
- Preserve contradictory claims with both source passages and their applicability.
  Record the conflict explicitly and block an unconditional conclusion. Resolve it
  with source evidence or publish only an accurately scoped, qualified conflict.
  Never average opposing claims, silently choose the preferred source, lower confidence
  to bypass a failure, or treat absence from an incomplete extract as proof of absence.
- Build prose and every persisted projection from canonical claim records. Validate
  citation and evidence bindings through concept packs, reader JSON, context and facts
  downloads before completion. Missing bindings or changed assertions stop publication;
  a dossier or tree update alone cannot bypass the shared /dr completion gate.
- Repair only failed claim/source pairs. Keep successful claims, snapshots and paid
  attempts. Allow one bounded evidence repair followed by a fresh bound gate; residual
  substantive dissent stops that claim. An unchanged failed evidence packet must not
  incur another paid judgment; one malformed-JSON repair is allowed. Retry recognized
  transport failures at most twice within the original deadline. Do not repeat discovery, whole-family research
  or successful website generation to repair a citation.
- Before shipping changes to this workflow, exercise real failure regressions:
  uncited claims, wrong-source quotes, incomplete derivatives, missing field names,
  negation or version conflicts, stale snapshot hashes and dropped output citations.
  Verify canonical, installed and runtime-specific skill copies with their sync check;
  equal version numbers alone do not establish parity. Report loaded state separately.
