"""Mongo-only, evidence-preserving compilation of already qualified research.

Compilation is a derived artifact phase. It cannot complete research, qualify a
claim, install a skill, or establish native search-index coverage.
"""
from __future__ import annotations

import copy
import json
import re
import secrets

from .models import (
    MANAGED_BY,
    Conflict,
    canonical,
    concept_id,
    digest,
    normalize_url,
    revision,
    source_id,
    text,
)
from .publication import CLAIM_FIELDS, pending_family
from .runs import MAX_ARTIFACT_BYTES, _identity

SCHEMA = "research-compilation/v1"
COMPILER = "research-library-compiler/v1"
FAMILY_HEAD = "family--manifest.json"
RENDERED_FILES = {"llms.txt", "llms-full.txt", "llms-small.txt", "llms-facts.txt"}
RELATIONS = ("children_ids", "related_ids", "adjacent_ids", "prerequisite_ids", "dependent_ids")


def _json(value):
    return canonical(value).decode("utf-8") + "\n"


def _reference(artifact):
    return {"artifact_id": artifact["_id"], "name": artifact["name"],
            "body_utf8_sha256": artifact["body_utf8_sha256"],
            "byte_count": artifact["byte_count"]}


def _maintained_renderer(*, title, documents, generated):
    """Import the owner-installed first-party wheel only when compilation needs it."""
    try:
        import llms_txt
        from llms_txt.family import Document, FamilyBuilder
    except ImportError as exc:
        raise ValueError("The maintained first-party llms-txt 0.1.1 renderer is unavailable") from exc
    if llms_txt.__version__ != "0.1.1":
        raise ValueError("Compilation requires the maintained first-party llms-txt 0.1.1 renderer")
    builder = FamilyBuilder(title, generated=generated)
    builder.add_many(Document(**row) for row in documents)
    return builder.render()


class ResearchCompiler:
    """Compile exact gated claims; leave provider use and indexing independently retryable.

    ``renderer`` is an in-process testing boundary with the same keyword arguments
    as ``_maintained_renderer``. No renderer, output path, or command is accepted
    by the remote compile operation.
    """

    def __init__(self, store, runs, indexer, renderer=None):
        self.store, self.runs, self.indexer = store, runs, indexer
        self.renderer = renderer or _maintained_renderer

    @staticmethod
    def _prefix(cid):
        return "concept--" + cid.removeprefix("c:")

    def _head(self, run_id, name, session=None):
        # Do not hide a foreign replacement behind the ownership filter.
        head = self.runs.artifact_heads.find_one(
            {"_id": "head:" + digest([run_id, name])}, session=session)
        if head is None:
            return None
        if head.get("managed_by") != MANAGED_BY or head.get("run_id") != run_id:
            raise Conflict("Compilation artifact head has untrusted ownership")
        artifact, body = self.runs._artifact_text(head["artifact_id"], session)
        provenance = artifact.get("trusted_provenance")
        if (not isinstance(provenance, dict) or provenance.get("compiler") != COMPILER
                or artifact.get("qualification", {}).get("status") != "trusted-archive"
                or artifact.get("name") != name or artifact.get("run_id") != run_id):
            raise Conflict("Compilation artifact head was replaced by an untrusted artifact")
        return artifact, body

    def _verified(self, cid, session=None):
        doc = self.store._get(cid, session, deleted=True)
        completion = doc.get("completion", {})
        if (doc.get("deleted") or doc.get("state") != "complete"
                or doc.get("qualification") != "verified"
                or completion.get("status") != "verified"
                or completion.get("canonical_verified") is not True
                or completion.get("projections_refreshed") is not True
                or type(completion.get("gate_contract")) is not int
                or completion["gate_contract"] < 4
                or not re.fullmatch(r"[0-9a-f]{64}", completion.get("artifact_sha256", ""))
                or pending_family(doc)):
            raise ValueError("Concept requires current canonical v4 qualification and resolved family")
        claims = [row for row in doc.get("claims", []) if not row.get("deleted")]
        if not claims:
            raise ValueError("Concept has no active supported claims")
        for claim in claims:
            if (claim.get("qualification") != "SUPPORTED" or not claim.get("evidence")
                    or claim.get("evidence_integrity") in {"unverified", "invalid", "missing"}):
                raise ValueError("Concept has unsupported claims or unverified evidence")
            supplied = {key: val for key, val in claim.items() if key in CLAIM_FIELDS}
            rebuilt = self.store._claim(doc["slug"], supplied, session, claim["lineage_id"])
            if (rebuilt["claim_id"] != claim.get("claim_id")
                    or rebuilt["identity"] != claim.get("identity")):
                raise ValueError("Claim identity changed from its immutable verified version")
            # _claim verifies every Unicode quote and the complete immutable
            # snapshot hash. Conflict-position evidence is independently pinned too.
            for position in (claim.get("conflict") or {}).get("positions", []):
                for span in position.get("evidence", []):
                    self._span(span, session)
        return doc

    def _span(self, span, session=None):
        source = self.store._source(span["source_id"], session, deleted=True)
        if (source_id(span["url"]) != span["source_id"]
                or normalize_url(source["url"]) != normalize_url(span["url"])):
            raise ValueError("Evidence belongs to a different source identity")
        body, _ = self.store._snapshot_text(span["source_id"], span["snapshot_sha256"], session)
        start, end = span["start"], span["end"]
        if (type(start) is not int or type(end) is not int or not 0 <= start < end <= len(body)
                or body[start:end] != span["quote"] or span.get("extraction_status") != "complete"):
            raise ValueError("Evidence quotation does not match its pinned source span")

    @staticmethod
    def _pin(doc):
        return {"concept_id": doc["_id"], "revision": doc["revision"],
                "concept_sha256": digest(doc),
                "canonical_artifact_sha256": doc["completion"]["artifact_sha256"],
                "claim_ids_sha256": digest(sorted(row["claim_id"] for row in doc["claims"]
                                                  if not row.get("deleted")))}

    def _coverage(self, run_id, session=None):
        rows = self.runs.run_items.find(self.runs._owned({"run_id": run_id,
            "kind": {"$in": ["coverage", "selection"]}}), session=session).sort("_id", 1)
        return [{"item_id": row["_id"], "key": row["key"], "revision": row["revision"],
                 "kind": row["kind"], "data": row["data"],
                 "assessment": row.get("assessment"),
                 "qualification": "unverified-orchestration"} for row in rows]

    def _read_manifest(self, artifact_id, session=None):
        artifact, body = self.runs._artifact_text(artifact_id, session)
        provenance = artifact.get("trusted_provenance")
        if (not isinstance(provenance, dict) or provenance.get("compiler") != COMPILER
                or artifact.get("qualification", {}).get("status") != "trusted-archive"):
            raise Conflict("Compiled manifest does not have trusted compiler provenance")
        value = json.loads(body)
        if value.get("schema") == "research-compilation-partition/v1":
            pieces = []
            for part in value["partitions"]:
                manifest, content = self.runs._artifact_text(part["artifact_id"], session)
                if (manifest["body_utf8_sha256"] != part["body_utf8_sha256"]
                        or manifest["trusted_provenance"] != provenance):
                    raise Conflict("Compiled manifest partition provenance changed")
                pieces.append(content)
            raw = "".join(pieces).encode("utf-8")
            if digest(raw) != value["logical_body_utf8_sha256"]:
                raise Conflict("Compiled manifest partition checksum mismatch")
            value = json.loads(raw)
        if value.get("schema") != SCHEMA:
            raise Conflict("Compiled manifest schema is not trusted")
        return artifact, value

    def _previous(self, run_id, session=None):
        head = self._head(run_id, FAMILY_HEAD, session)
        if head is None:
            return None, []
        artifact, value = self._read_manifest(head[0]["_id"], session)
        if value.get("scope") != "family" or not isinstance(value.get("members"), list):
            raise Conflict("Compiled family manifest is invalid")
        return _reference(artifact), value["members"]

    def _concept_heads(self, run_id, members, session=None):
        """Retain packs from earlier calls even when those calls deferred rollup."""
        retained = {row["concept_id"]: copy.deepcopy(row) for row in members}
        heads = self.runs.artifact_heads.find({"run_id": run_id}, session=session)
        for head in heads:
            name = head.get("name", "")
            if not name.startswith("concept--") or not name.endswith("--manifest.json"):
                continue
            checked = self._head(run_id, name, session)
            artifact, value = self._read_manifest(checked[0]["_id"], session)
            if value.get("scope") != "concept" or len(value.get("source_pins", [])) != 1:
                raise Conflict("Compiled concept manifest is invalid")
            pin = value["source_pins"][0]
            cid = pin["concept_id"]
            if name != self._prefix(cid) + "--manifest.json":
                raise Conflict("Compiled concept head has a different concept identity")
            ref = _reference(artifact)
            old = retained.get(cid)
            history = list((old or {}).get("previous_manifests", []))
            if old and old["manifest"] != ref:
                history.append(old["manifest"])
            retained[cid] = {"concept_id": cid, "pin": pin, "manifest": ref,
                             "previous_manifests": history, "disposition": "included"}
        return [row for _, row in sorted(retained.items())]

    @staticmethod
    def _units(doc):
        rows = []
        for claim in doc["claims"]:
            if claim.get("deleted"):
                continue
            spans = list(claim["evidence"])
            for position in (claim.get("conflict") or {}).get("positions", []):
                spans.extend(position.get("evidence", []))
            rows.append({"concept_id": doc["_id"], "concept_revision": doc["revision"],
                         "canonical_artifact_sha256": doc["completion"]["artifact_sha256"],
                         "claim_id": claim["claim_id"], "lineage_id": claim["lineage_id"],
                         "canonical_claim_id": claim.get("canonical_claim_id"),
                         "text": claim["text"], "sources": claim["sources"],
                         "evidence": [{"evidence_id": "evi:" + digest(span), **span}
                                      for span in spans]})
        return rows

    @classmethod
    def _document(cls, doc):
        units = cls._units(doc)
        facts = [row["text"] + " [claim: " + row["claim_id"] + "; sources: "
                 + ", ".join(row["sources"]) + "]" for row in units]
        summary = doc.get("summary", "")
        return {"title": doc["name"],
                # A logical locator is deliberately a research: URI, never a fabricated HTTP source.
                "url": "research:" + doc["_id"] + "@" + str(doc["revision"]),
                "body": (summary + "\n\n" if summary else "") + "\n\n".join(facts),
                "description": summary or units[0]["text"], "facts": facts}

    @staticmethod
    def _vocabulary(docs, title, generated):
        """Use the maintained vocabulary grammar without inventing definitions.

        The first-party llms renderer supplies four documents. Its vocabulary
        companion uses sourced term/definition/URL tuples and a separate tail
        for names that no in-scope claim defines. Unlike the filesystem adapter,
        this formatter retains the complete immutable definition text.
        """
        defined, undefined = [], []
        for doc in docs:
            term = doc["name"]
            subject = re.compile(r"^(?:(?:a|an|the)\s+)?`?" + re.escape(term)
                + r"`?\s+(?:(?:is|are|means)\s+(?:a|an|the|one|any)\b"
                  r"|(?:refers to|is defined as)\s+)", re.I)
            claim = next((row for row in doc["claims"]
                if not row.get("deleted") and row.get("sources")
                and len(row["text"].splitlines()) == 1 and subject.match(row["text"])), None)
            if claim is None:
                undefined.append(term)
            else:
                defined.append((term, claim))
        lines = [f"# {title} — vocabulary", "",
                 "> Exact sourced definitions from verified claims. Named terms without an "
                 "in-scope definition appear in the research-gap section.", "",
                 f"<!-- generated by {COMPILER} · {len(docs)} terms · {generated} -->", "",
                 "## Terms", ""]
        for term, claim in defined:
            line = f"- **{term}** — {claim['text']} — {claim['sources'][0]}"
            if len(claim["sources"]) > 1:
                line += " · also: " + ", ".join(claim["sources"][1:])
            lines.append(line + " · claim: " + claim["claim_id"])
        if undefined:
            lines += ["", "## Named, not yet defined", "", *["- " + term for term in undefined]]
        return "\n".join(lines).rstrip() + "\n"

    def _outputs(self, docs, title, generated):
        files = self.renderer(title=title, documents=[self._document(row) for row in docs],
                              generated=generated)
        if (not isinstance(files, dict) or set(files) != RENDERED_FILES
                or any(not isinstance(body, str) for body in files.values())):
            raise ValueError("The maintained renderer must return exactly four llms text documents")
        units = [unit for doc in docs for unit in self._units(doc)]
        files["units.jsonl"] = "".join(_json(unit) for unit in units)
        files["llms-vocabulary.txt"] = self._vocabulary(docs, title, generated)
        files["concept-graph.json"] = _json({"schema": SCHEMA, "nodes": [
            {"concept_id": doc["_id"], "name": doc["name"], "revision": doc["revision"],
             "parent_id": doc.get("parent_id"),
             **{field: doc.get(field, []) for field in RELATIONS}} for doc in docs]})
        files["SKILL.md"] = ("---\nname: compiled-research-draft\n"
            "description: Exact verified research excerpts.\n---\n\n"
            "# Compiled research draft\n\n"
            "Skill audit, registry publication, and installation are pending.\n"
            "Research locators identify Mongo research revisions; source citations are the exact "
            "HTTP URLs in the claim units.\n\n" + "\n\n".join(
                "## " + doc["name"] + "\n\n" + self._document(doc)["body"] for doc in docs) + "\n")
        return files

    def _receipt(self, actor, request_id):
        return self.store.receipts.find_one(self.store._owned(
            {"_id": "op:" + digest([actor, request_id])}))

    def _check_pins(self, pins, session=None):
        for pin in pins:
            current = self._verified(pin["concept_id"], session)
            if self._pin(current) != pin:
                raise Conflict("Compiled concept revision changed; start a new compilation request")

    def _check_result_heads(self, run_id, result):
        references = [row for row in result["artifacts"]
                      if row["name"].startswith("concept--")
                      and row["name"].endswith("--manifest.json")]
        if result.get("family_manifest"):
            ref = result["family_manifest"]
            head = self._head(run_id, FAMILY_HEAD)
            if not head or head[0]["_id"] != ref["artifact_id"]:
                raise Conflict("Compiled family manifest is no longer the current trusted head")
            _, family = self._read_manifest(ref["artifact_id"])
            references.extend(row["manifest"] for row in family["members"]
                              if row.get("disposition") == "included")
        for ref in references:
            head = self._head(run_id, ref["name"])
            if not head or head[0]["_id"] != ref["artifact_id"]:
                raise Conflict("Compiled concept manifest is no longer the current trusted head")
        if digest(self._coverage(run_id)) != result["coverage_sha256"]:
            raise Conflict("Compiled coverage ledger is no longer current")

    def compile(self, run_id, concept_ids, expected_revision, lease_token, owner, rollup=True,
                request_id="", actor="agent"):
        rid = _identity(run_id, "run:")
        if not isinstance(concept_ids, list) or not 1 <= len(concept_ids) <= 100:
            raise ValueError("Compile batches require 1..100 concept identities")
        ids = sorted({concept_id(cid) for cid in concept_ids})
        revision(expected_revision)
        owner, actor = text(owner, "run owner", 200), text(actor, "actor", 128)
        if type(rollup) is not bool:
            raise ValueError("Compile rollup must be a Boolean")
        request_id = text(request_id, "request ID", 128) if request_id else secrets.token_hex(16)
        payload = self.runs._fenced_payload(lease_token, run_id=rid, concept_ids=ids,
            expected_revision=expected_revision, owner=owner, rollup=rollup)
        operation = digest([actor, request_id])
        start_id, result_id = "compile-start:" + operation, "compile-result:" + operation
        previous_result = self._receipt(actor, result_id)
        if previous_result:
            if previous_result["result"]["input_sha256"] != digest(payload):
                raise Conflict("Request ID was reused for a different compilation")
            result = self.store._public(previous_result["result"])
            result["request_id"] = request_id
            try:
                self._check_pins(result["pins"])
                self._check_result_heads(rid, result)
            except (KeyError, ValueError):
                result.update(current=False, status="stale")
            return result

        def start(session):
            run = self.runs._edit(rid, expected_revision, lease_token, owner, session)
            prior, members = self._previous(rid, session)
            members = self._concept_heads(rid, members, session)
            pins, excluded = [], []
            for cid in ids:
                try:
                    pins.append(self._pin(self._verified(cid, session)))
                except (KeyError, ValueError) as exc:
                    excluded.append({"concept_id": cid, "status": "excluded",
                                     "reason": str(exc)})
            coverage = self._coverage(rid, session)
            return {"run": run, "pins": pins, "excluded": excluded,
                    "previous_family": prior, "members": members,
                    "coverage_sha256": digest(coverage), "generated": self.store._date()[:10]}

        plan = self.store._mutate("research_compile_start", payload, actor, start_id, start)
        cursor, archived = expected_revision, []
        requested_pins = plan["pins"]
        exclusions = copy.deepcopy(plan["excluded"])
        docs, members = {}, {row["concept_id"]: copy.deepcopy(row) for row in plan["members"]}

        def current_guard(session):
            self._check_pins(all_pins, session)
            if digest(self._coverage(rid, session)) != plan["coverage_sha256"]:
                raise Conflict("Coverage ledger changed during compilation")

        def archive(name, body, provenance, *, kind="compiled"):
            nonlocal cursor
            raw = body.encode("utf-8")
            marker = "compile-file:" + digest([operation, name, digest(raw), provenance])
            prior = self._receipt(actor, marker)
            if prior:
                saved = prior["result"]
                if saved["run"]["revision"] != cursor + 1:
                    raise Conflict("Compilation recovery has a non-contiguous run revision")
                manifest, _ = self.runs._artifact_text(saved["artifact"]["_id"])
                if (manifest["body_utf8_sha256"] != digest(raw)
                        or manifest["trusted_provenance"] != provenance):
                    raise Conflict("Compilation recovery artifact is inconsistent")
            else:
                saved = self.runs._archive_artifact(rid, name, kind, body,
                    provenance=provenance, expected_revision=cursor, lease_token=lease_token,
                    lease_owner=owner, request_id=marker, actor=actor, precondition=current_guard)
            cursor = saved["run"]["revision"]
            ref = _reference(saved["artifact"])
            archived.append(ref)
            return ref

        def bounded(prefix, logical_name, body, provenance, *, manifest=False):
            name = prefix + "--" + logical_name
            if len(name) > 200:
                name = name[:170] + "--" + digest(name.encode())[:20]
            raw = body.encode("utf-8")
            if len(raw) <= MAX_ARTIFACT_BYTES:
                return [archive(name, body, provenance,
                                kind="compiled_manifest" if manifest else "compiled")]
            pieces, position = [], 0
            # Metadata and the partition index state the complete union explicitly.
            while position < len(body):
                piece = body[position:position + MAX_ARTIFACT_BYTES]
                piece = piece.encode("utf-8")[:MAX_ARTIFACT_BYTES].decode("utf-8", "ignore")
                if not piece:
                    raise ValueError("Artifact byte limit cannot retain one Unicode character")
                part_name = (name[:140] + "--" + digest(name.encode())[:16]
                             + ".part-" + str(len(pieces) + 1).zfill(8))
                pieces.append(archive(part_name, piece, provenance))
                position += len(piece)
            index = {"schema": "research-compilation-partition/v1", "logical_name": logical_name,
                     "logical_body_utf8_sha256": digest(raw), "logical_byte_count": len(raw),
                     "join": "concatenate UTF-8 text in partition order without separators",
                     "partitions": pieces}
            if len(canonical(index)) > MAX_ARTIFACT_BYTES:
                raise ValueError("Partition index exceeds the explicit artifact byte limit")
            return [archive(name, _json(index), provenance,
                            kind="compiled_manifest" if manifest else "compiled"), *pieces]

        def provenance(pins, scope):
            return {"compiler": COMPILER, "schema": SCHEMA, "scope": scope,
                    "source_pins_sha256": digest(pins), "input_sha256": digest(payload),
                    "coverage_sha256": plan["coverage_sha256"],
                    **({"source_pin": pins[0]} if scope == "concept" else {
                        "member_artifacts_sha256": digest([
                            row["manifest"] for _, row in sorted(members.items())])})}

        def manifest_outputs(prefix, files, pins, scope, extra):
            prov = provenance(pins, scope)
            output_refs = []
            for name, body in sorted(files.items()):
                output_refs.extend(bounded(prefix, name, body, prov))
            value = {"schema": SCHEMA, "compiler": COMPILER, "scope": scope,
                     "status": "compiled", "research_qualification": "derived-only",
                     "source_pins": pins, "artifacts": output_refs, **extra,
                     "skill_phases": {"audit": "pending", "registry": "pending",
                                      "installation": "pending"},
                     "indexing": {"status": "pending", "authority": "artifact-index-census"}}
            refs = bounded(prefix, "manifest.json", _json(value), prov, manifest=True)
            return refs[0]

        try:
            self._check_pins(requested_pins)
            if digest(self._coverage(rid)) != plan["coverage_sha256"]:
                raise Conflict("Coverage ledger changed during compilation")
            prior, _ = self._previous(rid)
            # A completed replay is handled above. During recovery, our own new family
            # head is allowed only after every earlier output receipt has replayed.
            if prior != plan["previous_family"]:
                head = self._head(rid, FAMILY_HEAD)
                if not head or head[0]["trusted_provenance"].get("input_sha256") != digest(payload):
                    raise Conflict("Compiled family head changed during compilation")
            for pin in requested_pins:
                docs[pin["concept_id"]] = self._verified(pin["concept_id"])
            # No family-size cap: every prior member is retained in the ledger. Only
            # current verified pins and the latest trusted concept heads enter prose.
            for cid, member in members.items():
                if cid in docs:
                    continue
                try:
                    doc = self._verified(cid)
                    if self._pin(doc) != member["pin"]:
                        raise Conflict("Previously compiled member is stale")
                    head = self._head(rid, self._prefix(cid) + "--manifest.json")
                    if not head or head[0]["_id"] != member["manifest"]["artifact_id"]:
                        raise Conflict("Previously compiled concept head is missing or replaced")
                    self._read_manifest(member["manifest"]["artifact_id"])
                    docs[cid] = doc
                    member["disposition"] = "included"
                except (KeyError, ValueError) as exc:
                    member.update(disposition="excluded", reason=str(exc))
                    exclusions.append({"concept_id": cid, "status": "excluded", "reason": str(exc)})
            all_pins = [self._pin(doc) for _, doc in sorted(docs.items())]
            for pin in requested_pins:
                cid = pin["concept_id"]
                # Inspect existing heads before replacing them. An ordinary caller
                # cannot replace a trusted pack and then have compilation accept it.
                self._head(rid, self._prefix(cid) + "--manifest.json")
                doc = docs[cid]
                ref = manifest_outputs(self._prefix(cid), self._outputs(
                    [doc], doc["name"], plan["generated"]), [pin], "concept",
                    {"concept_id": cid, "claim_units": self._units(doc)})
                old = members.get(cid)
                history = list((old or {}).get("previous_manifests", []))
                if old and old["manifest"]["artifact_id"] != ref["artifact_id"]:
                    history.append(old["manifest"])
                members[cid] = {"concept_id": cid, "pin": pin, "manifest": ref,
                                "previous_manifests": history, "disposition": "included"}
            family_ref = None
            if rollup:
                active = [doc for _, doc in sorted(docs.items())]
                files = self._outputs(active, "Compiled research family", plan["generated"]) if active else {}
                family_ref = manifest_outputs("family", files, all_pins, "family",
                    {"members": [row for _, row in sorted(members.items())],
                     "previous_family_manifest": plan["previous_family"],
                     "exclusions": exclusions, "coverage_ledger": self._coverage(rid)})
            # Recheck source pins, coverage, lease and run CAS before issuing a durable
            # phase receipt. Artifacts remain historical, exact revision projections.
            def finish(session):
                current_guard(session)
                run = self.runs._edit(rid, cursor, lease_token, owner, session)
                return {"run": run, "status": "partial" if exclusions else "compiled",
                        "current": True, "input_sha256": digest(payload), "pins": all_pins,
                        "coverage_sha256": plan["coverage_sha256"],
                        "compiled_concept_ids": [pin["concept_id"] for pin in requested_pins],
                        "family_manifest": family_ref, "artifacts": archived,
                        "exclusions": exclusions, "research_verdict": "unchanged",
                        "indexing": {"status": "pending", "artifact_ids": [
                            row["artifact_id"] for row in archived],
                            "keyword_coverage_verified": False, "vector_coverage_verified": False},
                        "skill_phases": {"audit": "pending", "registry": "pending",
                                         "installation": "pending"},
                        "full_suite_complete": False}
            result = self.store._mutate("research_compile_result", {"input_sha256": digest(payload)},
                                        actor, result_id, finish)
            return {**result, "request_id": request_id}
        except (KeyError, ValueError):
            # CAS and lease failures are actionable errors, not successful partial
            # compilation. Earlier immutable artifacts are recoverable by request ID.
            raise
        except Exception as exc:
            return {"run": self.runs.run_get(rid), "status": "partial", "current": False,
                    "artifacts": archived, "error_type": type(exc).__name__,
                    "request_id": request_id, "retry": "repeat the exact request to recover",
                    "indexing": {"status": "pending"}, "research_verdict": "unchanged",
                    "full_suite_complete": False}
