"""Owner-local byte archives and exhaustive source reconciliation.

This adapter writes only fenced run artifacts. It neither researches nor promotes
imported prose, verdicts, units, or manifests into qualified claims. Inventory
paths are owner-local inputs; they are never exposed as an MCP filesystem API.
"""
from __future__ import annotations

import base64
import codecs
import hashlib
import json
import os
import re
import time
from collections import Counter, defaultdict
from itertools import zip_longest
from pathlib import Path

SCHEMA = "local-research-reconciliation/v1"
BUNDLE_BYTES = 7 * 1024 * 1024
READ_BYTES = 1024 * 1024
ACTOR = "local-reconciliation"
HEX = re.compile(r"[0-9a-f]{64}\Z")
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"mongodb(?:\+srv)?://[^\s/:@]+:[^\s/@]+@", re.I),
    re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|sk-(?:proj-)?[A-Za-z0-9_-]{32,})"),
    re.compile(r"(?i)[\"']?(?:api[_-]?key|access[_-]?token|bearer[_-]?token|"
               r"lease[_-]?token|password|secret)[\"']?\s*[:=]\s*[\"']"
               r"(?![<$])[^\s\"']{16,}[\"']"),
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def digest(value):
    return sha(canonical(value))


def private_dir(path):
    path = Path(path)
    if path.is_symlink():
        raise ValueError("Private output cannot be a symlink")
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.chmod(0o700)
    return path


def save(path, value):
    path = Path(path)
    private_dir(path.parent)
    if path.is_symlink():
        raise ValueError("Private output cannot be a symlink")
    temporary = path.with_name(path.name + ".tmp")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(canonical(value) + b"\n")
    temporary.chmod(0o600)
    temporary.replace(path)


def json_lines(path):
    with Path(path).open("rb") as stream:
        for line in stream:
            if line.strip():
                row = json.loads(line)
                if not isinstance(row, dict):
                    raise ValueError("Inventory rows must be objects")
                yield row


def line_writer(path):
    private_dir(Path(path).parent)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    return os.fdopen(fd, "wb")


def write_line(stream, row):
    stream.write(canonical(row) + b"\n")


def signature(path):
    stat = Path(path).stat()
    return [stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns]


def file_hash(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while block := stream.read(READ_BYTES):
            value.update(block)
    return value.hexdigest()


def input_reference(path):
    path = Path(path).absolute()
    before = signature(path)
    result = {"path": str(path), "sha256": file_hash(path), "byte_length": before[2]}
    if before != signature(path):
        raise ValueError("Reconciliation input changed while hashing")
    return result


def check_reference(reference):
    if input_reference(reference["path"]) != reference:
        raise ValueError("Reconciliation proof input checksum mismatch")


def source_record(row):
    path = row.get("path")
    domain = row.get("provenance_domain", row.get("provenance", "unknown"))
    if not isinstance(domain, str):
        domain = digest(domain)
    if not isinstance(path, str) or not Path(path).is_absolute():
        raise ValueError("A source requires its absolute owner-local path")
    identity = row.get("source_identity") or digest([row.get("root_id"), path, domain])
    if not isinstance(identity, str) or not identity:
        raise ValueError("Invalid source identity")
    result = {
        "source_identity": identity, "path": path,
        "canonical_path": row.get("canonical_path", path),
        "provenance_domain": domain, "root_id": row.get("root_id"),
        "original_sha256": row.get("original_sha256", row.get("sha256")),
        "byte_length": row.get("byte_length", row.get("bytes")),
        "mtime_ns": row.get("mtime_ns"), "format": row.get("format"),
        "classification": row.get("classification", row.get("classification_reason")),
        "observed_at": row.get("observed_at"),
        "alias_of_source_identity": row.get("alias_of_source_identity"),
    }
    if row.get("category") != "research":
        return {**result, "status": "excluded", "reason": "inventory-exclusion"}
    if (not isinstance(result["original_sha256"], str)
            or not HEX.fullmatch(result["original_sha256"])
            or type(result["byte_length"]) is not int or result["byte_length"] < 0):
        return {**result, "status": "conflict", "reason": "missing-source-byte-identity"}
    if row.get("stable_during_hash") is False:
        return {**result, "status": "conflict", "reason": "inventory-source-race"}
    result["group_id"] = digest([domain, result["original_sha256"]])
    return {**result, "status": "pending"}


def source_matches(row, *, full_hash=False):
    """Compare actual source bytes; never infer equality from matching counts."""
    try:
        path = row["canonical_path"]
        if Path(row["path"]).resolve(strict=True) != Path(path):
            return False
        before = signature(path)
        if before[2] != row["byte_length"] or (
                type(row.get("mtime_ns")) is int and before[3] != row["mtime_ns"]):
            return False
        if full_hash and file_hash(path) != row["original_sha256"]:
            return False
        return before == signature(path)
    except (OSError, ValueError):
        return False


def screen_source(row, deny_terms=(), *, allow_reviewed_placeholders=False):
    """Read locally without logging matches, preserving the source unchanged."""
    before = signature(row["canonical_path"])
    decoder = codecs.getincrementaldecoder("utf-8")("strict")
    hasher, total, binary, sensitive, nonadmissible = hashlib.sha256(), 0, False, False, False
    tail = ""
    overlap = max([512, *(len(term) for term in deny_terms)])
    with Path(row["canonical_path"]).open("rb") as stream:
        while block := stream.read(READ_BYTES):
            hasher.update(block)
            total += len(block)
            if b"\x00" in block:
                binary = True
            if not binary:
                try:
                    decoded = decoder.decode(block)
                except UnicodeError:
                    binary = True
                    decoded = block.decode("utf-8", "replace")
            else:
                decoded = block.decode("utf-8", "replace")
            probe = tail + decoded
            sensitive |= any(pattern.search(probe) for pattern in SECRET_PATTERNS)
            lowered = probe.casefold()
            denied = any(term.casefold() in lowered for term in deny_terms)
            nonadmissible |= denied or any(SECRET_PATTERNS[index].search(probe) for index in (0, 2))
            sensitive |= denied
            tail = probe[-overlap:]
    if not binary:
        try:
            decoder.decode(b"", final=True)
        except UnicodeError:
            binary = True
    if (before != signature(row["canonical_path"]) or total != row["byte_length"]
            or hasher.hexdigest() != row["original_sha256"]):
        return "conflict", "source-changed-during-preparation"
    if sensitive and (not allow_reviewed_placeholders or nonadmissible):
        return "excluded", "privacy-screening-match-original-not-uploaded"
    return "ready", "base64" if binary else "utf-8"


def source_parts(row, encoding, maximum):
    """Yield exact ordered byte pieces without breaking a Unicode character."""
    if maximum < 4:
        raise ValueError("Source part bound is too small")
    width = maximum if encoding == "utf-8" else max(1, maximum * 3 // 4)
    decoder = codecs.getincrementaldecoder("utf-8")("strict")
    offset, number, yielded = 0, 0, False
    with Path(row["canonical_path"]).open("rb") as stream:
        while raw := stream.read(width):
            if encoding == "utf-8":
                payload = decoder.decode(raw)
                content = payload.encode("utf-8")
            else:
                content, payload = raw, base64.b64encode(raw).decode("ascii")
            if not content:
                continue
            yield number, offset, content, payload
            yielded, offset, number = True, offset + len(content), number + 1
        if encoding == "utf-8":
            remaining = decoder.decode(b"", final=True)
            if remaining:
                content = remaining.encode("utf-8")
                yield number, offset, content, remaining
                yielded = True
    if not yielded:
        yield 0, 0, b"", ""


def frame(group, part, encoding, raw):
    return "\n--local-source-part " + canonical({
        "group_id": group, "part": part, "encoding": encoding,
        "byte_length": len(raw), "sha256": sha(raw),
    }).decode() + "\n"


END_FRAME = "\n--end-local-source-part--\n"


class Bundler:
    def __init__(self, stream, maximum):
        if type(maximum) is not int or not 2048 <= maximum <= BUNDLE_BYTES:
            raise ValueError("Bundle bound must be 2048..7MiB")
        self.stream, self.maximum = stream, maximum
        self.parts, self.raw, self.chars, self.domain, self.encoding = [], bytearray(), 0, None, None
        self.count = 0

    def flush(self):
        if not self.parts:
            return
        body_sha = sha(bytes(self.raw))
        write_line(self.stream, {"name": "source-" + body_sha, "body_sha256": body_sha,
            "byte_length": len(self.raw), "char_length": self.chars,
            "provenance_domain": self.domain, "encoding": self.encoding,
            "search_eligible": self.encoding == "utf-8", "parts": self.parts})
        self.count += 1
        self.parts, self.raw, self.chars = [], bytearray(), 0

    def add(self, row, encoding, number, start, content, payload):
        header = frame(row["group_id"], number, encoding, content)
        raw = (header + payload + END_FRAME).encode()
        if len(raw) > self.maximum:
            raise ValueError("A framed source part exceeds the bundle bound")
        if self.parts and (len(self.raw) + len(raw) > self.maximum
                           or self.domain != row["provenance_domain"] or self.encoding != encoding):
            self.flush()
        self.domain, self.encoding = row["provenance_domain"], encoding
        prefix_bytes = len(header.encode())
        self.parts.append({"group_id": row["group_id"], "part": number,
            "source_path": row["canonical_path"], "source_byte_start": start,
            "source_byte_end": start + len(content), "part_sha256": sha(content),
            "encoding": encoding, "char_start": self.chars + len(header),
            "char_end": self.chars + len(header) + len(payload),
            "byte_start": len(self.raw) + prefix_bytes,
            "byte_end": len(self.raw) + prefix_bytes + len(payload.encode())})
        self.raw.extend(raw)
        self.chars += len(header) + len(payload) + len(END_FRAME)


def _structured_kind(path):
    name = Path(path).name
    if name == "units.jsonl":
        return "units"
    if name in {"concept-graph.json", "tree.json", "manifest.json"}:
        return name.removesuffix(".json")
    if Path(path).suffix == ".json" and any(part in {"canonical", "claims"} for part in Path(path).parts):
        return "canonical"
    return None


def structured_records(row):
    """Retain explicit identifiers and evidence pins, never synthesize claim IDs."""
    kind = _structured_kind(row["canonical_path"])
    if not kind:
        return
    def visit(value, location):
        if isinstance(value, list):
            for index, item in enumerate(value):
                yield from visit(item, location + "/" + str(index))
        elif isinstance(value, dict):
            identities = {key: value[key] for key in (
                "id", "_id", "unit_id", "concept_id", "conceptId", "canonical_concept_id",
                "claim_id", "canonical_claim_id", "lineage_id", "source_id", "snapshot_sha256",
                "artifact_sha256", "schema", "slug", "parent_id")
                if isinstance(value.get(key), str)}
            if identities or kind in {"units", "manifest", "concept-graph", "canonical", "tree"}:
                result = {"group_id": row["group_id"], "record_path": location or "/",
                    "format": kind, "explicit_identities": identities,
                    "qualification": "unverified-retained-input", "status": "artifact-only",
                    "reason": "no-authoritative-existing-record-mapping" if identities
                        else "missing-explicit-record-identity"}
                if isinstance(value.get("text"), str):
                    result["text_sha256"] = sha(value["text"].encode())
                if isinstance(value.get("evidence"), list):
                    result["evidence_sha256"] = digest(value["evidence"])
                    result["evidence_count"] = len(value["evidence"])
                result["applicability"] = {key: value[key] for key in (
                    "verified_as_of", "valid_from", "valid_to", "applicability_version")
                    if key in value and isinstance(value[key], (str, type(None)))}
                yield result
            for key in ("units", "concepts", "nodes", "claims", "sources", "relations", "documents"):
                if isinstance(value.get(key), (list, dict)):
                    yield from visit(value[key], location + "/" + key)
            if not identities:
                for key, item in value.items():
                    if key not in {"units", "concepts", "nodes", "claims", "sources",
                                   "relations", "documents"} and isinstance(item, (list, dict)):
                        yield from visit(item, location + "/" + key)
    try:
        if Path(row["canonical_path"]).suffix == ".jsonl":
            with Path(row["canonical_path"]).open("rb") as stream:
                for number, line in enumerate(stream):
                    if line.strip():
                        try:
                            yield from visit(json.loads(line), "/" + str(number))
                        except (UnicodeError, ValueError, RecursionError):
                            yield {"group_id": row["group_id"], "record_path": "/" + str(number),
                                "format": kind, "status": "artifact-only",
                                "qualification": "unverified-retained-input",
                                "reason": "structured-record-unparseable"}
        else:
            with Path(row["canonical_path"]).open("rb") as stream:
                yield from visit(json.load(stream), "")
    except (UnicodeError, ValueError, OSError, RecursionError):
        yield {"group_id": row["group_id"], "format": kind, "status": "artifact-only",
               "qualification": "unverified-retained-input", "reason": "structured-input-unparseable"}


def prepare(inventory, directory, *, deny_terms=(), maximum=BUNDLE_BYTES, privacy_admissions=None):
    """Build a private reproducible plan; no database, lease, or source mutation."""
    directory, inventory = private_dir(directory), Path(inventory).absolute()
    groups, seen, counts = {}, set(), Counter()
    privacy_admissions = privacy_admissions or {}
    admitted_groups = {row["group_id"] for row in privacy_admissions.values()}
    with line_writer(directory / "source-census.jsonl") as output:
        for original in json_lines(inventory):
            row = source_record(original)
            if row["source_identity"] in seen:
                raise ValueError("Duplicate source identity in inventory")
            seen.add(row["source_identity"])
            if row["status"] == "pending":
                if not source_matches(row):
                    row.update(status="conflict", reason="source-signature-changed")
                else:
                    prior = groups.setdefault(row["group_id"], row)
                    if row["source_identity"] in privacy_admissions and prior[
                            "source_identity"] not in privacy_admissions:
                        groups[row["group_id"]] = row
            write_line(output, row)
            counts[row["status"]] += 1
    group_results = {}
    with line_writer(directory / "groups.jsonl") as group_out, \
            line_writer(directory / "bundles.jsonl") as bundle_out, \
            line_writer(directory / "structured-records.jsonl") as structure_out:
        # Binary files often alternate with text in content-hash order. Keep
        # two bounded buffers so that alternation does not create tiny artifacts.
        bundlers = {encoding: Bundler(bundle_out, maximum)
                    for encoding in ("utf-8", "base64")}
        previous_bucket = None
        for group_number, (gid, row) in enumerate(sorted(groups.items(), key=lambda item: (
                item[1]["provenance_domain"], item[1]["original_sha256"]))):
            if group_number % 1000 == 0:
                save(directory / "progress.json", {"phase": "prepare",
                    "groups_processed": group_number, "groups_total": len(groups),
                    "bundles_written": sum(b.count for b in bundlers.values())})
            try:
                status, detail = screen_source(row, deny_terms,
                    allow_reviewed_placeholders=gid in admitted_groups)
            except OSError:
                status, detail = "conflict", "source-unavailable"
            result = {**row, "status": status}
            if status != "ready":
                result["reason"] = detail
            else:
                result["encoding"] = detail
                bucket = (row["provenance_domain"], row["original_sha256"][:2])
                if previous_bucket != bucket:
                    for bundler in bundlers.values():
                        bundler.flush()
                previous_bucket = bucket
                bundler = bundlers[detail]
                for number, start, content, payload in source_parts(row, detail, maximum - 1024):
                    bundler.add(row, detail, number, start, content, payload)
                if detail == "utf-8":
                    for record in structured_records(row):
                        write_line(structure_out, record)
            group_results[gid] = {key: result[key] for key in ("status", "reason", "encoding")
                                 if key in result}
            write_line(group_out, result)
        for bundler in bundlers.values():
            bundler.flush()
    bundle_count = sum(b.count for b in bundlers.values())
    with line_writer(directory / "mappings.jsonl") as output:
        counts.clear()
        for row in json_lines(directory / "source-census.jsonl"):
            if row["status"] == "pending":
                row.update(group_results[row["group_id"]])
                if row["group_id"] in admitted_groups:
                    evidence = privacy_admissions.get(row["source_identity"])
                    if evidence is None:
                        row.update(status="excluded", reason="privacy-screening-match-original-not-uploaded")
                    elif row["status"] == "ready":
                        row["privacy_admission"] = {"evidence_sha256": digest(evidence),
                            "qualification": "owner-reviewed-privacy-only-not-factual-proof"}
            counts[row["status"]] += 1
            write_line(output, row)
    refs = {name: {"sha256": file_hash(directory / name),
                   "byte_length": (directory / name).stat().st_size}
            for name in ("source-census.jsonl", "mappings.jsonl", "groups.jsonl",
                         "bundles.jsonl", "structured-records.jsonl")}
    plan = {"schema": SCHEMA, "inventory": {"path": str(inventory),
            "sha256": file_hash(inventory)}, "source_count": len(seen), "groups": len(groups),
            "counts": dict(counts), "bundle_count": bundle_count, "bundle_bytes": maximum,
            "files": refs, "qualification": "unverified", "no_database_writes": True,
            "methods": ["exact-source-hash", "content-and-provenance-deduplication",
                        "byte-and-unicode-ranges", "explicit-identity-preservation"]}
    plan["plan_sha256"] = digest(plan)
    save(directory / "plan.json", plan)
    save(directory / "progress.json", {"phase": "prepared", "source_count": len(seen),
        "groups_processed": len(groups), "groups_total": len(groups),
        "bundles_written": bundle_count, "counts": dict(counts)})
    return plan


def load_plan(directory):
    directory = Path(directory)
    if (directory / "SUPERSEDED.json").exists():
        raise ValueError("This local reconciliation plan is superseded")
    plan = json.loads((directory / "plan.json").read_bytes())
    expected = plan.pop("plan_sha256")
    if plan.get("schema") != SCHEMA or digest(plan) != expected:
        raise ValueError("Reconciliation plan checksum mismatch")
    plan["plan_sha256"] = expected
    for name, ref in plan["files"].items():
        if Path(name).name != name or file_hash(directory / name) != ref["sha256"]:
            raise ValueError("Reconciliation plan member checksum mismatch")
    if file_hash(plan["inventory"]["path"]) != plan["inventory"]["sha256"]:
        raise ValueError("Source inventory changed after preparation")
    if plan.get("privacy_admission"):
        check_reference(plan["privacy_admission"]["ledger"])
    return plan


def build_bundle(bundle, groups):
    body, char_count, byte_count = [], 0, 0
    for part in bundle["parts"]:
        row = groups[part["group_id"]]
        with Path(row["canonical_path"]).open("rb") as source:
            source.seek(part["source_byte_start"])
            raw = source.read(part["source_byte_end"] - part["source_byte_start"])
        if sha(raw) != part["part_sha256"]:
            raise ValueError("Source part changed after preparation")
        payload = raw.decode("utf-8") if part["encoding"] == "utf-8" else base64.b64encode(raw).decode()
        header = frame(part["group_id"], part["part"], part["encoding"], raw)
        if (char_count + len(header) != part["char_start"]
                or byte_count + len(header.encode()) != part["byte_start"]
                or part["char_end"] - part["char_start"] != len(payload)
                or part["byte_end"] - part["byte_start"] != len(payload.encode())):
            raise ValueError("Source range manifest mismatch")
        framed = header + payload + END_FRAME
        body.append(framed)
        char_count += len(framed)
        byte_count += len(framed.encode())
    result = "".join(body)
    if sha(result.encode()) != bundle["body_sha256"] or byte_count != bundle["byte_length"]:
        raise ValueError("Reconstructed bundle checksum mismatch")
    return result


class ArchiveSession:
    """A single owner-local writer using only maintained fenced interfaces."""
    def __init__(self, service, directory, parent_run, owner="local-research-reconciliation"):
        self.service, self.runs = service, service.runs
        self.directory, self.owner, self.parent = private_dir(directory), owner, parent_run
        self.state_path = self.directory / "lease-state.json"
        self.last_renewal = 0
        if self.state_path.exists():
            if self.state_path.is_symlink() or self.state_path.stat().st_mode & 0o077:
                raise ValueError("Unsafe private run state permissions")
            self.state = json.loads(self.state_path.read_bytes())
            if self.state["owner"] != owner or self.state["parent_run_id"] != parent_run:
                raise ValueError("Run state belongs to a different operation")
            current = self.runs.run_get(self.state["run_id"])
            if current["owner"] != owner:
                raise ValueError("Run owner changed")
            self.state["revision"] = current["revision"]
            self.renew(acquire=True)
        else:
            parent = self.runs.run_get(parent_run)
            created = self.runs.run_create("queue", "Local research source archive", parent["prompt"],
                owner, options={"no_new_research": True, "no_paid_judges": True,
                    "preserve_historical_vectors": True},
                scope={"kind": "local-source-archive", "parent_run_id": parent_run},
                request_id="local-archive-create-" + digest([str(self.directory), parent_run]),
                actor=ACTOR)
            self.state = {"run_id": created["run"]["_id"], "revision": created["run"]["revision"],
                "lease_token": created["lease_token"], "owner": owner,
                "parent_run_id": parent_run}
            current = self.runs.run_get(self.state["run_id"])
            if current["owner"] != owner:
                raise ValueError("Run owner changed")
            self.state["revision"] = current["revision"]
            self._save()
            self.renew(acquire=True)
        self.heads = {}
        after = ""
        while True:
            page = self.runs.artifact_list(self.run_id, after=after, limit=100)
            self.heads.update({row["name"]: row for row in page["artifacts"]})
            after = page["next_after"]
            if not after:
                break

    @property
    def run_id(self):
        return self.state["run_id"]

    def _save(self):
        # Heads are reconstructed from the authoritative paginated run listing.
        # Keeping every head in this lease file makes each new artifact rewrite
        # the complete census and grows total persistence work quadratically.
        self.state.pop("artifacts", None)
        self.state.pop("indexes", None)
        save(self.state_path, self.state)

    def renew(self, acquire=False):
        from .models import LeaseConflict
        arguments = {"run_id": self.run_id, "owner": self.owner,
            "ttl_seconds": 3600, "expected_revision": self.state["revision"], "actor": ACTOR,
            "request_id": "renew-" + digest([self.run_id, time.time_ns()])}
        try:
            result = self.runs.run_lease(action="renew", token=self.state.get("lease_token", ""),
                                         **arguments)
        except LeaseConflict:
            if not acquire:
                raise
            result = self.runs.run_lease(action="acquire", **arguments)
        self.state["lease_token"] = result["lease_token"]
        self.last_renewal = time.monotonic()
        self._save()

    def tick(self):
        if time.monotonic() - self.last_renewal > 120:
            self.renew()

    def checkpoint(self, phase, **details):
        self.tick()
        result = self.runs.run_checkpoint(self.run_id,
            {"state": "running", "checkpoint": {"phase": phase, **details}},
            self.state["revision"], self.state["lease_token"], self.owner,
            request_id="checkpoint-" + digest([self.run_id, phase, details,
                                               self.state["revision"]]), actor=ACTOR)
        self.state["revision"] = result["run"]["revision"]
        self._save()

    def put(self, name, kind, body, metadata):
        self.tick()
        body_hash = sha(body.encode())
        existing = self.heads.get(name)
        if (existing and existing["body_utf8_sha256"] == body_hash
                and existing["kind"] == kind and existing["metadata"] == metadata):
            self.get(existing["_id"])
            return {**existing, "local_storage_action": "unchanged"}
        from .models import Conflict
        request_id = "put-" + digest([self.run_id, name, body_hash, metadata, self.state["revision"]])
        for attempt in range(3):
            try:
                result = self.runs.artifact_put(self.run_id, name, kind, body,
                    self.state["revision"], self.state["lease_token"], self.owner, metadata=metadata,
                    request_id=request_id, actor=ACTOR)
                break
            except Conflict as exc:
                if (str(exc) != "Concurrent research transaction conflict; retry with the same request ID"
                        or attempt == 2):
                    raise
        manifest = result["artifact"]
        self.state["revision"] = result["run"]["revision"]
        self.heads[name] = manifest
        self._save()
        return {**manifest, "local_storage_action": "new"}

    def get(self, artifact_id):
        # This maintained consumer reconstructs and hash-checks every immutable chunk.
        return self.runs._artifact_text(artifact_id)

    def finish(self):
        if (self.directory / "composition-receipt.json").exists():
            return finish_composition(self)
        plan = load_plan(self.directory)
        archive = _read_receipt(self.directory, self, plan)
        archive_sha = file_hash(self.directory / "archive-receipt.json")
        verification = json.loads((self.directory / "verification-receipt.json").read_bytes())
        indexed = json.loads((self.directory / "index-receipt.json").read_bytes())
        if (verification.get("run_id") != self.run_id or indexed.get("run_id") != self.run_id
                or archive.get("plan_sha256") != plan["plan_sha256"]
                or any(receipt.get("plan_sha256") != plan["plan_sha256"]
                    or receipt.get("archive_receipt_sha256") != archive_sha
                    for receipt in (verification, indexed))
                or not indexed.get("index_written_complete")
                or not indexed.get("native_coverage_complete")
                or indexed.get("index_results_sha256") != file_hash(
                    self.directory / "index-results.jsonl")
                or not verification.get("reconciliation_complete") or not indexed.get("complete")):
            raise ValueError("Complete fresh storage and native-search verification are required")
        self.tick()
        result = self.runs.run_checkpoint(self.run_id, {"state": "finished", "checkpoint": {
            "phase": "source-reconciliation-complete", "factual_qualification_established": False,
            "verification_sha256": file_hash(self.directory / "verification-receipt.json"),
            "index_sha256": file_hash(self.directory / "index-receipt.json")}},
            self.state["revision"], self.state["lease_token"], self.owner,
            request_id="finish-" + digest([self.run_id, self.state["revision"]]), actor=ACTOR)
        self.state["revision"] = result["run"]["revision"]
        self.runs.run_lease(self.run_id, "release", self.owner, self.state["lease_token"],
            expected_revision=self.state["revision"],
            request_id="release-" + digest([self.run_id, self.state["revision"]]), actor=ACTOR)
        self.state.pop("lease_token", None)
        self.state["finished"] = True
        self._save()
        return {"run_id": self.run_id, "complete": True, "state": "finished",
                "factual_qualification_established": False}


def _text_file_parts(path, maximum=BUNDLE_BYTES):
    row = {"canonical_path": str(path)}
    for number, _, _, body in source_parts(row, "utf-8", maximum - 1024):
        yield number, body


def _archive_inputs(directory, plan):
    files = [Path(plan["inventory"]["path"]), directory / "result-mappings.jsonl",
             directory / "structural-mappings.jsonl", directory / "plan.json"]
    if plan.get("privacy_admission"):
        files.append(Path(plan["privacy_admission"]["ledger"]["path"]))
    if len({path.name for path in files}) != len(files):
        raise ValueError("Administrative artifact input filenames must be distinct")
    return files


def map_structured(directory, session):
    """Resolve only explicit existing identities; retain ambiguous units as data."""
    cache, counts = {}, Counter()
    with line_writer(Path(directory) / "structural-mappings.jsonl") as output:
        for row in json_lines(Path(directory) / "structured-records.jsonl"):
            identities = row.get("explicit_identities", {})
            cid = next((identities.get(key) for key in ("concept_id", "canonical_concept_id",
                "conceptId", "id", "_id") if str(identities.get(key, "")).startswith("c:")), None)
            if cid:
                if cid not in cache:
                    try:
                        cache[cid] = session.service.store.concept_get(cid)
                    except (KeyError, ValueError):
                        cache[cid] = None
                doc = cache[cid]
                if doc:
                    row.update(status="mapped-existing-concept", concept_id=cid,
                        concept_revision=doc["revision"], reason="explicit-concept-identity")
                    wanted = {identities.get(key) for key in
                              ("claim_id", "canonical_claim_id", "lineage_id") if identities.get(key)}
                    if wanted:
                        matches = [claim for claim in doc.get("claims", []) if wanted & {
                            claim.get("claim_id"), claim.get("lineage_id"), claim.get("_id")}]
                        if len(matches) == 1 and (not row.get("text_sha256") or
                                sha(matches[0].get("text", "").encode()) == row["text_sha256"]):
                            row.update(status="mapped-existing-claim", claim_id=matches[0].get("claim_id"),
                                lineage_id=matches[0].get("lineage_id"),
                                reason="explicit-existing-claim-and-text-binding")
                        else:
                            row.update(status="artifact-only", reason="claim-identity-or-text-conflict")
            counts[row["status"]] += 1
            write_line(output, row)
    return dict(counts)


def _source_check_cache(directory, session, plan):
    """Reuse owned checks only with exact input rows, frozen proof and fresh stat pins."""
    path, receipt_path = directory / "source-recheck.jsonl", directory / "source-recheck-receipt.json"
    if not path.exists():
        return {}
    if path.is_symlink() or path.stat().st_mode & 0o077:
        raise ValueError("Unsafe source-check cache permissions")
    reference = input_reference(path)
    legacy = not receipt_path.exists()
    if not legacy:
        receipt = json.loads(receipt_path.read_bytes())
        if (receipt.get("run_id") != session.run_id or receipt.get("plan_sha256") != plan["plan_sha256"]
                or receipt.get("source_checks") != reference):
            raise ValueError("Frozen source-check proof checksum mismatch")
    signatures = {}
    if legacy:
        for row in json_lines(plan["inventory"]["path"]):
            normalized = source_record(row)
            values = [row.get("device"), row.get("inode"), normalized["byte_length"],
                      normalized["mtime_ns"]]
            if all(type(value) is int for value in values):
                signatures[normalized["source_identity"]] = values
    cached, counts = {}, Counter()
    for old, row in zip_longest(json_lines(path), json_lines(directory / "mappings.jsonl")):
        if old is None or row is None or any(old.get(key) != value for key, value in row.items()
                if key not in {"status", "reason"}) or old["status"] not in {row["status"], "conflict"}:
            raise ValueError("Source-check cache has another complete source census")
        counts[old["status"]] += 1
        if old["status"] == "ready":
            cached[old["source_identity"]] = old.get("source_check_signature",
                signatures.get(old["source_identity"]))
    if legacy:
        current = session.runs.run_get(session.run_id)
        archive_seen, checkpoint_found = False, False
        for revision in range(current["revision"], max(0, current["revision"] - 256), -1):
            doc = current if revision == current["revision"] else session.runs.run_get(
                session.run_id, revision=revision)
            checkpoint = doc.get("checkpoint", {})
            archive_seen |= checkpoint.get("phase") == "archive-bundles" and checkpoint.get(
                "source_counts") == dict(counts)
            if (archive_seen and checkpoint.get("phase") == "source-recheck"
                    and checkpoint.get("plan_sha256") == plan["plan_sha256"]
                    and checkpoint.get("inventory_sha256") == plan["inventory"]["sha256"]):
                checkpoint_found = True
                break
        if not checkpoint_found:
            raise ValueError("Legacy source checks need owned frozen-checkpoint evidence")
        session.checkpoint("source-recheck-adopted", plan_sha256=plan["plan_sha256"],
            source_checks=reference, source_counts=dict(counts),
            proof="owned-prior-full-hash-phase-and-exact-row-census")
        save(receipt_path, {"run_id": session.run_id, "plan_sha256": plan["plan_sha256"],
            "source_checks": reference, "legacy_owned_checkpoint_verified": True})
    check_reference(reference)
    return cached


def apply(directory, session, *, resume=False):
    directory, plan = Path(directory), load_plan(directory)
    groups = {row["group_id"]: row for row in json_lines(directory / "groups.jsonl")}
    cached = _source_check_cache(directory, session, plan) if resume else {}
    actual, candidates, counts = {}, {}, Counter()
    cache_reused, full_hash_attempts = 0, 0
    session.checkpoint("source-recheck", inventory_sha256=plan["inventory"]["sha256"],
                       plan_sha256=plan["plan_sha256"], source_count=plan["source_count"])
    next_checks = directory / "source-recheck.next.jsonl"
    with line_writer(next_checks) as output:
        for number, row in enumerate(json_lines(directory / "mappings.jsonl")):
            if number % 1000 == 0:
                session.tick()
                save(directory / "progress.json", {"phase": "apply-source-recheck",
                    "source_rows_checked": number, "source_rows_total": plan["source_count"],
                    "counts": dict(counts), "cached_checks_reused": cache_reused,
                    "full_hash_attempts": full_hash_attempts})
            if row["status"] == "ready":
                try:
                    before = signature(row["canonical_path"])
                except OSError:
                    before = None
                reused = bool(before is not None and cached.get(row["source_identity"]) == before
                              and source_matches(row))
                cache_reused += reused
                full_hash_attempts += not reused
                if reused or source_matches(row, full_hash=True):
                    row["source_check_signature"] = signature(row["canonical_path"])
                    if before != row["source_check_signature"]:
                        row.update(status="conflict", reason="source-changed-before-archive")
                    else:
                        candidates.setdefault(row["group_id"], row)
                else:
                    row.update(status="conflict", reason="source-changed-before-archive")
            actual[row["source_identity"]] = row
            counts[row["status"]] += 1
            write_line(output, row)
    next_checks.replace(directory / "source-recheck.jsonl")
    source_proof = {"run_id": session.run_id, "plan_sha256": plan["plan_sha256"],
        "source_checks": input_reference(directory / "source-recheck.jsonl"),
        "source_counts": dict(counts), "cached_checks_reused": cache_reused,
        "full_hash_attempts": full_hash_attempts}
    save(directory / "source-recheck-receipt.json", source_proof)
    for gid, row in candidates.items():
        groups[gid]["canonical_path"] = row["canonical_path"]
        groups[gid]["source_identity"] = row["source_identity"]
    artifacts, failed_groups = {}, set()
    session.checkpoint("archive-bundles", source_counts=dict(counts),
        source_check_proof_sha256=file_hash(directory / "source-recheck-receipt.json"))
    with line_writer(directory / "bundle-results.jsonl") as output:
        for number, bundle in enumerate(json_lines(directory / "bundles.jsonl")):
            if number % 16 == 0:
                save(directory / "progress.json", {"phase": "apply-source-bundles",
                    "bundles_attempted": number, "bundles_total": plan["bundle_count"],
                    "bundles_retained": len(artifacts), "conflicted_groups": len(failed_groups)})
            gids = {part["group_id"] for part in bundle["parts"]}
            kind = "source-bundle-text" if bundle["search_eligible"] else "source-bundle-binary"
            metadata = {"schema": SCHEMA, "encoding": bundle["encoding"],
                "provenance_domain": bundle["provenance_domain"],
                "search_eligible": bundle["search_eligible"]}
            accepted = getattr(session, "heads", {}).get(bundle["name"]) if resume else None
            if (accepted and accepted["body_utf8_sha256"] == bundle["body_sha256"]
                    and accepted["kind"] == kind and accepted["metadata"] == metadata):
                manifest = {**accepted, "local_storage_action": "unchanged"}
            else:
                if not gids <= candidates.keys():
                    failed_groups.update(gids)
                    write_line(output, {"name": bundle["name"], "status": "conflict",
                                        "reason": "source-group-unavailable"})
                    continue
                try:
                    body = build_bundle(bundle, groups)
                except (OSError, UnicodeError, ValueError):
                    failed_groups.update(gids)
                    write_line(output, {"name": bundle["name"], "status": "conflict",
                                        "reason": "source-bundle-reconstruction-failed"})
                    continue
                manifest = session.put(bundle["name"], kind, body, metadata)
            result = {"name": bundle["name"], "status": "retained",
                "artifact_id": manifest["_id"], "sha256": manifest["body_utf8_sha256"],
                "byte_length": manifest["byte_count"], "search_eligible": bundle["search_eligible"],
                "storage_action": manifest["local_storage_action"]}
            artifacts[bundle["name"]] = result
            write_line(output, result)
    spans = defaultdict(list)
    for bundle in json_lines(directory / "bundles.jsonl"):
        if bundle["name"] in artifacts:
            for part in bundle["parts"]:
                spans[part["group_id"]].append({**part,
                    "artifact_id": artifacts[bundle["name"]]["artifact_id"],
                    "bundle_sha256": bundle["body_sha256"]})
    with line_writer(directory / "result-mappings.jsonl") as output:
        counts.clear()
        for row in actual.values():
            if row["status"] == "ready":
                if row["group_id"] in failed_groups or not spans.get(row["group_id"]):
                    row.update(status="conflict", reason="incomplete-archive-group")
                else:
                    row.update(status="retained", parts=spans[row["group_id"]],
                        qualification="unverified-artifact", disposition="verified-duplicate" if
                        row["source_identity"] != groups[row["group_id"]]["source_identity"]
                        else "retained-artifact")
            elif (row["status"] == "conflict" and row.get("group_id") not in failed_groups
                  and spans.get(row.get("group_id"))):
                # Previously committed immutable bytes remain a historical version,
                # even if the live source changed before this resumed apply.
                row.update(parts=spans[row["group_id"]], qualification="unverified-artifact")
            counts[row["status"]] += 1
            write_line(output, row)
    # Original inventory and normalized mappings are retained independently of payloads.
    structural_counts = map_structured(directory, session)
    manifest_refs = []
    for file in _archive_inputs(directory, plan):
        original_hash = file_hash(file)
        for number, body in _text_file_parts(file):
            manifest = session.put("census-" + file.name + "-" + str(number),
                "source-census", body, {"schema": SCHEMA, "source_file_sha256": original_hash,
                                      "part": number, "search_eligible": False})
            manifest_refs.append({"artifact_id": manifest["_id"], "name": manifest["name"],
                "sha256": manifest["body_utf8_sha256"], "byte_length": manifest["byte_count"],
                "search_eligible": False, "exclusion_reason": "administrative-census-not-source-text"})
    receipt = {"schema": SCHEMA, "run_id": session.run_id, "parent_run_id": session.parent,
        "plan_sha256": plan["plan_sha256"], "source_counts": dict(counts),
        "source_count": len(actual), "payload_artifacts": len(artifacts),
        "census_artifacts": manifest_refs, "qualification": "unverified",
        "structural_conversion_counts": structural_counts,
        "storage_written_complete": counts["conflict"] == 0,
        "storage_verified": False, "native_search_verified": False}
    save(directory / "archive-receipt.json", receipt)
    save(directory / "progress.json", {"phase": "archive-written-awaiting-verification",
        "source_count": len(actual), "source_counts": dict(counts),
        "payload_artifacts": len(artifacts)})
    session.checkpoint("archive-written-awaiting-verification", receipt=receipt)
    return receipt


def _read_receipt(directory, session, plan):
    receipt = json.loads((Path(directory) / "archive-receipt.json").read_bytes())
    if receipt["run_id"] != session.run_id or receipt["plan_sha256"] != plan["plan_sha256"]:
        raise ValueError("Archive receipt belongs to another run or prepared plan")
    return receipt


def verify(directory, session, *, check_sources=True, current_inventory=None, scope_receipts=()):
    directory, plan = Path(directory), load_plan(directory)
    receipt = _read_receipt(directory, session, plan)
    fresh_reference = input_reference(current_inventory) if current_inventory is not None else None
    retained = {row["name"]: row for row in json_lines(directory / "bundle-results.jsonl")
                if row["status"] == "retained"}
    group_hashes, group_lengths, next_parts, errors = {}, Counter(), Counter(), []
    expected_spans = defaultdict(list)
    verified_artifacts, expected_artifacts = set(), set()
    for number, bundle in enumerate(json_lines(directory / "bundles.jsonl")):
        if number % 16 == 0:
            save(directory / "progress.json", {"phase": "verify-source-bundles",
                "bundles_attempted": number, "bundles_total": plan["bundle_count"],
                "artifacts_verified": len(verified_artifacts), "errors": len(errors)})
        session.tick()
        result = retained.get(bundle["name"])
        if result is None:
            continue
        aid = result["artifact_id"]
        expected_artifacts.add(aid)
        for part in bundle["parts"]:
            expected_spans[part["group_id"]].append({**part, "artifact_id": aid,
                "bundle_sha256": bundle["body_sha256"]})
        try:
            manifest, body = session.get(aid)
            if (manifest["body_utf8_sha256"] != bundle["body_sha256"]
                    or sha(body.encode()) != bundle["body_sha256"]):
                raise ValueError("Bundle binding mismatch")
            raw_body = body.encode()
            for part in bundle["parts"]:
                gid = part["group_id"]
                payload = body[part["char_start"]:part["char_end"]]
                if raw_body[part["byte_start"]:part["byte_end"]] != payload.encode():
                    raise ValueError("Unicode and byte ranges differ")
                raw = payload.encode() if part["encoding"] == "utf-8" else base64.b64decode(
                    payload, validate=True)
                if (sha(raw) != part["part_sha256"] or next_parts[gid] != part["part"]
                        or len(raw) != part["source_byte_end"] - part["source_byte_start"]
                        or group_lengths[gid] != part["source_byte_start"]):
                    raise ValueError("Source part binding mismatch")
                group_hashes.setdefault(gid, hashlib.sha256()).update(raw)
                group_lengths[gid] += len(raw)
                next_parts[gid] += 1
            verified_artifacts.add(aid)
        except (KeyError, ValueError, OSError, UnicodeError):
            errors.append({"artifact_id": aid, "reason": "artifact-or-range-verification-failed"})
    expected_census = {}
    for file in _archive_inputs(directory, plan):
        for number, body in _text_file_parts(file):
            expected_census["census-" + file.name + "-" + str(number)] = sha(body.encode())
    if {row["name"] for row in receipt["census_artifacts"]} != set(expected_census):
        errors.append({"reason": "incomplete-census-artifact-set"})
    for result in receipt["census_artifacts"]:
        session.tick()
        aid = result["artifact_id"]
        expected_artifacts.add(aid)
        try:
            manifest, body = session.get(aid)
            if (sha(body.encode()) != result["sha256"]
                    or result["sha256"] != expected_census.get(result["name"])
                    or manifest["byte_count"] != result["byte_length"]):
                raise ValueError("Census binding mismatch")
            verified_artifacts.add(aid)
        except (KeyError, ValueError, OSError):
            errors.append({"artifact_id": aid, "reason": "census-verification-failed"})
    expected_ids, actual_ids, expected_rows, counts = set(), set(), {}, Counter()
    for row in json_lines(directory / "source-census.jsonl"):
        expected_ids.add(row["source_identity"])
        expected_rows[row["source_identity"]] = row
    with line_writer(directory / "verification-results.jsonl") as output:
        for number, row in enumerate(json_lines(directory / "result-mappings.jsonl")):
            if number % 1000 == 0:
                session.tick()
                save(directory / "progress.json", {"phase": "verify-source-mappings",
                    "source_rows_checked": number, "source_rows_total": plan["source_count"],
                    "counts": dict(counts)})
            sid, status = row["source_identity"], row["status"]
            if sid in actual_ids:
                status = "conflict"
            actual_ids.add(sid)
            old = expected_rows.get(sid)
            if old is None or any(old.get(key) != row.get(key) for key in (
                    "path", "canonical_path", "provenance_domain", "original_sha256",
                    "byte_length", "mtime_ns", "group_id")):
                status = "failed"
            storage_status = status
            if status == "retained" or (status == "conflict" and row.get("parts")):
                gid = row["group_id"]
                if (gid not in group_hashes or group_hashes[gid].hexdigest() != row["original_sha256"]
                        or group_lengths[gid] != row["byte_length"]
                        or row["parts"] != expected_spans[gid]
                        or not all(p["artifact_id"] in verified_artifacts for p in row["parts"])):
                    status = storage_status = "failed"
                else:
                    storage_status = "retained"
            if status == "retained" and check_sources and not source_matches(row, full_hash=True):
                status = "conflict"
            counts[status] += 1
            write_line(output, {"source_identity": sid, "status": status,
                "storage_status": storage_status,
                "original_sha256": row.get("original_sha256"), "qualification": "unverified"})
    fresh_ids, fresh_changed, fresh_duplicate = None, [], []
    if current_inventory is not None:
        fresh_ids = set()
        for original in json_lines(current_inventory):
            row = source_record(original)
            sid = row["source_identity"]
            if sid in fresh_ids:
                fresh_duplicate.append(sid)
            fresh_ids.add(sid)
            old = expected_rows.get(sid)
            if old and any(old.get(key) != row.get(key) for key in (
                    "path", "canonical_path", "root_id", "alias_of_source_identity",
                    "original_sha256", "byte_length", "mtime_ns", "provenance_domain",
                    "classification", "status")):
                fresh_changed.append(sid)
        check_reference(fresh_reference)
    result = {"schema": SCHEMA, "run_id": session.run_id, "plan_sha256": plan["plan_sha256"],
        "archive_receipt_sha256": file_hash(directory / "archive-receipt.json"),
        "source_counts": dict(counts), "source_set_equal": expected_ids == actual_ids,
        "source_census_sha256": digest(sorted(expected_ids)),
        "actual_source_census_sha256": digest(sorted(actual_ids)),
        "missing_source_ids": sorted(expected_ids - actual_ids),
        "unexpected_source_ids": sorted(actual_ids - expected_ids),
        "expected_artifacts": len(expected_artifacts), "verified_artifacts": len(verified_artifacts),
        "artifact_set_equal": expected_artifacts == verified_artifacts, "errors": errors,
        "current_source_bytes_checked": check_sources, "qualification": "unverified",
        "fresh_inventory": fresh_reference,
        "scope_receipts": [input_reference(path) for path in scope_receipts],
        "result_mappings_sha256": file_hash(directory / "result-mappings.jsonl"),
        "verification_results_sha256": file_hash(directory / "verification-results.jsonl"),
        "bundle_results_sha256": file_hash(directory / "bundle-results.jsonl"),
        "fresh_inventory_compared": fresh_ids is not None,
        "new_source_ids": sorted(fresh_ids - expected_ids) if fresh_ids is not None else [],
        "removed_source_ids": sorted(expected_ids - fresh_ids) if fresh_ids is not None else [],
        "changed_source_ids": sorted(fresh_changed), "duplicate_fresh_source_ids": fresh_duplicate,
        "factual_qualification_established": False,
        "storage_complete": expected_ids == actual_ids and expected_artifacts == verified_artifacts
            and not errors and not counts["failed"] and not counts["conflict"]}
    result["reconciliation_complete"] = bool(result["storage_complete"] and check_sources
        and fresh_ids == expected_ids and not fresh_changed and not fresh_duplicate)
    save(directory / "verification-receipt.json", result)
    save(directory / "progress.json", {"phase": "storage-verified" if result[
        "storage_complete"] else "storage-partial", "source_counts": dict(counts),
        "reconciliation_complete": result["reconciliation_complete"]})
    session.checkpoint("storage-verified" if result["storage_complete"] else "storage-partial",
                       verification=result)
    return result


def index(directory, session, *, write=True):
    """Write bounded immutable units, then verify only pending native coverage."""
    from .artifact_search import TEXT_DEFINITION, TEXT_INDEX, VECTOR_DEFINITION, VECTOR_INDEX
    directory = Path(directory)
    plan = load_plan(directory)
    archive_receipt = _read_receipt(directory, session, plan)
    search = session.service.artifact_search
    wanted = {TEXT_INDEX: ("search", TEXT_DEFINITION),
              VECTOR_INDEX: ("vectorSearch", VECTOR_DEFINITION)}
    binding = {"schema": SCHEMA, "run_id": session.run_id, "plan_sha256": plan["plan_sha256"],
        "archive_receipt_sha256": file_hash(directory / "archive-receipt.json"),
        "native_index_contract_sha256": digest(wanted)}
    existing = {row["name"]: row for row in search.collection.list_search_indexes()}
    if any(name not in existing or existing[name].get("latestDefinition",
            existing[name].get("definition")) != definition
            or existing[name].get("type", kind) != kind
            for name, (kind, definition) in wanted.items()):
        result = {**binding, "complete": False, "index_written_complete": False,
            "native_coverage_complete": False, "reason": "native-index-contract-missing-or-different",
            "definition_changes": 0, "research_or_judges_started": False}
        save(directory / "index-receipt.json", result)
        return result
    prior, valid_prior, previous = {}, False, directory / "index-receipt.json"
    results_path = directory / "index-results.jsonl"
    if previous.exists():
        accepted = json.loads(previous.read_bytes())
        if all(accepted.get(key) == value for key, value in binding.items()) and accepted.get(
                "index_results_sha256"):
            if file_hash(results_path) != accepted["index_results_sha256"]:
                raise ValueError("Native coverage proof checksum mismatch")
            valid_prior = True
            for row in json_lines(results_path):
                if row["artifact_id"] in prior:
                    raise ValueError("Duplicate native artifact proof identity")
                prior[row["artifact_id"]] = row
    if not write and not valid_prior:
        result = {**binding, "complete": False, "index_written_complete": False,
            "native_coverage_complete": False, "reason": "current-index-phase-proof-required",
            "definition_changes": 0, "research_or_judges_started": False}
        save(directory / "index-receipt.json", result)
        return result
    counts, native_complete, written_complete = Counter(), True, True
    counts["administrative_census_artifacts_outside_search_scope"] = len(
        archive_receipt["census_artifacts"])
    counts["administrative_census_bytes_outside_search_scope"] = sum(
        row["byte_length"] for row in archive_receipt["census_artifacts"])
    retained = [row for row in json_lines(directory / "bundle-results.jsonl")
                if row["status"] == "retained"]
    if prior and set(prior) != {row["artifact_id"] for row in retained}:
        raise ValueError("Native coverage proof has another artifact census")
    next_path = directory / "index-results.next.jsonl"
    with line_writer(next_path) as output:
        for number, row in enumerate(retained):
            if number % 16 == 0:
                save(directory / "progress.json", {"phase": "index-units" if write else
                    "verify-pending-native-coverage", "artifacts_attempted": number,
                    "artifacts_total": len(retained), "counts": dict(counts)})
            if not row["search_eligible"]:
                counts["binary_artifacts_outside_search_scope"] += 1
                counts["binary_archive_bytes_outside_search_scope"] += row["byte_length"]
                write_line(output, {"artifact_id": row["artifact_id"], "eligible": False,
                                    "reason": "binary-original-base64-retention"})
                continue
            session.tick()
            old = prior.get(row["artifact_id"])
            if old:
                if (old.get("body_utf8_sha256") != row["sha256"]
                        or old.get("byte_length") != row["byte_length"] or not old.get("written")):
                    raise ValueError("Native coverage proof has another artifact binding")
                expected = old["coverage"]["expected_unit_ids"]
                if (len(set(expected)) != len(expected)
                        or digest(sorted(expected)) != old.get("unit_census_sha256")):
                    raise ValueError("Native coverage proof has another unit census")
                if old["coverage"]["complete"]:
                    coverage = old["coverage"]
                    counts["native_coverage_reused_artifacts"] += 1
                else:
                    coverage = search._coverage(expected)
                    counts["native_coverage_queried_artifacts"] += 1
                counts["index_write_reused_artifacts"] += 1
            else:
                if not write:
                    raise ValueError("Native coverage requires the bounded index phase first")
                manifest, body = session.get(row["artifact_id"])
                if (manifest["run_id"] != session.run_id or manifest["name"] != row["name"]
                        or manifest["body_utf8_sha256"] != row["sha256"]
                        or manifest["byte_count"] != row["byte_length"]):
                    raise ValueError("Native indexing has another artifact binding")
                units = search._units(manifest, body)
                if (sum(unit["byte_count"] for unit in units) != manifest["byte_count"]
                        or sha("".join(unit["search_text"] for unit in units).encode())
                        != manifest["body_utf8_sha256"]):
                    raise ValueError("Artifact search units do not cover the exact body")
                expected = [unit["unit_id"] for unit in units]
                result = search.artifact_index(session.run_id, [row["artifact_id"]],
                    session.state["revision"], session.state["lease_token"], session.owner,
                    request_id="index-" + digest([row["artifact_id"], session.state["revision"]]),
                    actor=ACTOR)
                session.state["revision"] = result["run"]["revision"]
                session._save()
                coverage = result["coverage"]
                counts["index_artifact_writes"] += 1
            if set(coverage["expected_unit_ids"]) != set(expected):
                raise ValueError("Native coverage expected another unit census")
            native_complete &= coverage["complete"]
            counts["eligible_text_artifacts"] += 1
            counts["eligible_text_bytes"] += row["byte_length"]
            counts["expected_text_units"] += len(expected)
            counts["complete_text_artifacts" if coverage["complete"] else "pending_text_artifacts"] += 1
            write_line(output, {"artifact_id": row["artifact_id"], "eligible": True,
                "body_utf8_sha256": row["sha256"], "byte_length": row["byte_length"],
                "written": True, "unit_census_sha256": digest(sorted(expected)), "coverage": coverage})
    next_path.replace(results_path)
    result = {**binding, "complete": bool(written_complete and native_complete),
        "index_written_complete": bool(written_complete),
        "native_coverage_complete": bool(native_complete),
        "index_results_sha256": file_hash(results_path), "counts": dict(counts),
        "reason": "complete" if native_complete else "native-coverage-pending",
        "native_keyword_and_semantic_verified": bool(native_complete),
        "semantic_truncation": False, "binary_search_exclusions_explicit": True,
        "definition_changes": 0, "historical_vector_changes": 0,
        "research_or_judges_started": False}
    save(previous, result)
    save(directory / "progress.json", {"phase": "index-verified" if result["complete"] else
        "index-written-native-pending", "index_written_complete": result["index_written_complete"],
        "native_coverage_complete": result["native_coverage_complete"], "counts": dict(counts)})
    session.checkpoint("index-verified" if result["complete"] else "index-written-native-pending",
                       index=result)
    return result


def _storage_identity(row):
    return tuple(row.get(key) for key in (
        "source_identity", "original_sha256", "byte_length", "provenance_domain"))


def _layer(directory, progress_directory=None):
    """Load hash-bound per-source proof, including valid sources in a partial run."""
    directory = Path(directory).absolute()
    names = ["plan.json", "archive-receipt.json", "verification-receipt.json",
             "result-mappings.jsonl", "verification-results.jsonl", "bundle-results.jsonl",
             "index-receipt.json", "index-results.jsonl"]
    signatures = {name: signature(directory / name) for name in names if (directory / name).exists()}
    plan = load_plan(directory)
    archive = json.loads((directory / "archive-receipt.json").read_bytes())
    verified = json.loads((directory / "verification-receipt.json").read_bytes())
    if (archive["plan_sha256"] != plan["plan_sha256"]
            or verified.get("plan_sha256") != plan["plan_sha256"]
            or verified.get("run_id") != archive["run_id"]
            or verified.get("archive_receipt_sha256") != file_hash(directory / "archive-receipt.json")):
        raise ValueError("Source layer proof belongs to another archive or plan")
    proof_names = ["plan.json", "archive-receipt.json", "verification-receipt.json",
                   "result-mappings.jsonl", "verification-results.jsonl", "bundle-results.jsonl"]
    for name, field in (("result-mappings.jsonl", "result_mappings_sha256"),
                        ("verification-results.jsonl", "verification_results_sha256"),
                        ("bundle-results.jsonl", "bundle_results_sha256")):
        if verified.get(field) != file_hash(directory / name):
            raise ValueError("Source layer needs current hash-bound per-source verification")
    frozen = {}
    for row in json_lines(directory / "source-census.jsonl"):
        sid = row["source_identity"]
        if sid in frozen:
            raise ValueError("Duplicate frozen source census identity")
        frozen[sid] = row
    census_hash = digest(sorted(frozen))
    if (len(frozen) != plan["source_count"] or verified.get("source_set_equal") is not True
            or verified.get("source_census_sha256") != census_hash
            or verified.get("actual_source_census_sha256") != census_hash
            or verified.get("missing_source_ids") != []
            or verified.get("unexpected_source_ids") != []):
        raise ValueError("Source layer has an incomplete frozen source census")
    source_proof = {}
    for row in json_lines(directory / "verification-results.jsonl"):
        if row["source_identity"] in source_proof:
            raise ValueError("Duplicate source proof identity")
        source_proof[row["source_identity"]] = row
    sources, accepted = {}, {}
    for number, row in enumerate(json_lines(directory / "result-mappings.jsonl")):
        sid = row["source_identity"]
        if sid in sources:
            raise ValueError("Duplicate source layer mapping")
        original = frozen.get(sid)
        if (original is None or _storage_identity(original) != _storage_identity(row)
                or any(original.get(key) != row.get(key) for key in
                       ("path", "canonical_path", "root_id", "alias_of_source_identity"))):
            raise ValueError("Source layer mapping differs from its frozen source identity")
        sources[sid] = row
        proof = source_proof.get(sid, {})
        storage = proof.get("storage_status", proof.get("status"))
        if ((storage == "retained" and row["status"] in {"retained", "conflict"}
             or storage == "excluded" and row["status"] == "excluded")
                and proof.get("original_sha256") == row.get("original_sha256")):
            accepted[sid] = storage
        if progress_directory is not None and number % 1000 == 0:
            save(Path(progress_directory) / "progress.json", {"phase": "read-source-layer-proof",
                "source_rows_checked": number, "accepted_source_rows": len(accepted)})
    if set(sources) != set(frozen) or set(source_proof) != set(frozen):
        raise ValueError("Source layer has an incomplete frozen source census")
    artifacts = {row["artifact_id"]: row for row in json_lines(directory / "bundle-results.jsonl")
                 if row["status"] == "retained"}
    native = {}
    native_path = directory / "index-receipt.json"
    if native_path.exists():
        from .artifact_search import TEXT_DEFINITION, TEXT_INDEX, VECTOR_DEFINITION, VECTOR_INDEX
        receipt = json.loads(native_path.read_bytes())
        if (receipt.get("run_id") != archive["run_id"]
                or receipt.get("plan_sha256") != plan["plan_sha256"]
                or receipt.get("archive_receipt_sha256") != verified["archive_receipt_sha256"]):
            raise ValueError("Native layer proof belongs to another archive")
        if receipt.get("index_results_sha256"):
            if receipt.get("native_index_contract_sha256") != digest({
                    TEXT_INDEX: ("search", TEXT_DEFINITION),
                    VECTOR_INDEX: ("vectorSearch", VECTOR_DEFINITION)}):
                raise ValueError("Native layer proof has another index contract")
            if receipt["index_results_sha256"] != file_hash(directory / "index-results.jsonl"):
                raise ValueError("Native layer proof checksum mismatch")
            proof_names += ["index-receipt.json", "index-results.jsonl"]
            for row in json_lines(directory / "index-results.jsonl"):
                aid = row["artifact_id"]
                if aid in native or aid not in artifacts:
                    raise ValueError("Native layer proof has another artifact census")
                if row["eligible"]:
                    expected = row["coverage"]["expected_unit_ids"]
                    if (not row.get("written") or len(set(expected)) != len(expected)
                            or digest(sorted(expected)) != row.get("unit_census_sha256")
                            or row.get("body_utf8_sha256") != artifacts[aid]["sha256"]
                            or row.get("byte_length") != artifacts[aid]["byte_length"]):
                        raise ValueError("Native layer proof has another immutable binding")
                native[aid] = row
    references = [input_reference(directory / name) for name in proof_names]
    if any(name not in signatures or signature(directory / name) != signatures[name]
           for name in proof_names):
        raise ValueError("Source layer proof changed during composition")
    return {"directory": str(directory), "run_id": archive["run_id"], "sources": sources,
        "accepted": accepted, "artifacts": artifacts, "native": native,
        "proof": {"directory": str(directory), "run_id": archive["run_id"],
                  "plan_sha256": plan["plan_sha256"], "files": references,
                  "sha256": digest(references)}}


def _select_source(row, layers):
    for layer in reversed(layers):
        old = layer["sources"].get(row["source_identity"])
        if (old is not None and row["source_identity"] in layer["accepted"]
                and _storage_identity(old) == _storage_identity(row)):
            return layer, old
    return None, None


def _privacy_admissions(path, expected_sha256, denylist_sha256):
    if path is None:
        return {}, None
    reference = input_reference(path)
    if reference["sha256"] != expected_sha256 or not HEX.fullmatch(denylist_sha256 or ""):
        raise ValueError("Reviewed privacy admissions require exact ledger and denylist hashes")
    admissions = {}
    for original in json_lines(path):
        row = source_record(original)
        evidence = original.get("privacy_admission_evidence", {})
        if (row["source_identity"] in admissions or row["status"] != "pending"
                or evidence.get("actual_sha256") != row["original_sha256"]
                or evidence.get("complete_source_scanned") is not True
                or evidence.get("denylist_sha256") != denylist_sha256
                or not isinstance(evidence.get("rule_version"), str)
                or not isinstance(evidence.get("matched_classes"), list)
                or not evidence["matched_classes"]):
            raise ValueError("Invalid reviewed source-specific privacy admission")
        before = signature(row["canonical_path"])
        if (Path(row["path"]).resolve(strict=True) != Path(row["canonical_path"])
                or file_hash(row["canonical_path"]) != row["original_sha256"]
                or before != signature(row["canonical_path"])):
            raise ValueError("Reviewed admission source bytes changed")
        admissions[row["source_identity"]] = {**row, "privacy_admission_evidence": evidence}
    check_reference(reference)
    return admissions, reference


def prepare_delta(current_inventory, directory, layer_directories, *, deny_terms=(),
                  maximum=BUNDLE_BYTES, scope_receipts=(), admission_ledger=None,
                  admission_sha256=None, denylist_sha256=None):
    """Prepare only new, changed, or unverified current source identities."""
    directory = private_dir(directory)
    if (directory / "lease-state.json").exists():
        raise ValueError("A delta preparation needs a new receipt directory")
    full_reference = input_reference(current_inventory)
    scope = [input_reference(path) for path in scope_receipts]
    layers = [_layer(path, directory) for path in layer_directories]
    admissions, admission_reference = _privacy_admissions(
        admission_ledger, admission_sha256, denylist_sha256)
    if not layers:
        raise ValueError("A delta requires at least one verified source layer")
    selected, reused, fresh_ids = 0, 0, set()
    inventory = directory / "delta-inventory.jsonl"
    with line_writer(inventory) as output:
        for number, original in enumerate(json_lines(current_inventory)):
            row = source_record(original)
            sid = row["source_identity"]
            if sid in fresh_ids:
                raise ValueError("Duplicate source identity in the full current census")
            fresh_ids.add(sid)
            layer, _ = _select_source(row, layers)
            admitted = admissions.get(sid)
            if admitted and (_storage_identity(admitted) != _storage_identity(row)
                    or any(admitted.get(key) != row.get(key) for key in (
                        "path", "canonical_path", "root_id"))):
                raise ValueError("Reviewed admission differs from the current census identity")
            if layer is None or row["status"] == "conflict" or admitted is not None:
                selected += 1
                write_line(output, original)
            else:
                reused += 1
            if number % 1000 == 0:
                save(directory / "progress.json", {"phase": "select-delta",
                    "source_rows_checked": number, "selected": selected, "reused": reused})
    previous_ids = {sid for layer in layers for sid in layer["sources"]}
    if set(admissions) - fresh_ids:
        raise ValueError("Reviewed admission is outside the complete current census")
    removed = sorted(previous_ids - fresh_ids)
    with line_writer(directory / "delta-removed-source-ids.jsonl") as output:
        for sid in removed:
            write_line(output, {"source_identity": sid, "status": "removed-from-current-census",
                                "historical_artifacts_deleted": False})
    check_reference(full_reference)
    for reference in scope:
        check_reference(reference)
    plan = prepare(inventory, directory, deny_terms=deny_terms, maximum=maximum,
                   privacy_admissions=admissions)
    check_reference(full_reference)
    plan.pop("plan_sha256")
    plan["delta"] = {"full_inventory": full_reference, "scope_receipts": scope,
        "layer_proofs": [layer["proof"] for layer in layers], "selected_source_count": selected,
        "reused_source_count": reused, "removed_source_count": len(removed),
        "removed_sources": input_reference(directory / "delta-removed-source-ids.jsonl")}
    if admission_reference:
        check_reference(admission_reference)
        plan["privacy_admission"] = {"ledger": admission_reference, "source_count": len(admissions),
            "denylist_sha256": denylist_sha256,
            "qualification": "owner-reviewed-privacy-only-not-factual-proof",
            "default_scanner_rules_changed": False,
            "private_key_header_and_provider_key_overrides": False}
    plan["plan_sha256"] = digest(plan)
    save(directory / "plan.json", plan)
    return plan


def _version_reference(layer, row):
    status = layer["accepted"].get(row["source_identity"])
    return {"layer_directory": layer["directory"], "run_id": layer["run_id"],
        "layer_proof_sha256": layer["proof"]["sha256"], "mapping_sha256": digest(row),
        "original_sha256": row.get("original_sha256"), "byte_length": row.get("byte_length"),
        "provenance_domain": row["provenance_domain"], "original_status": row["status"],
        "retention": "artifact-verified" if status == "retained" else
            "intentional-exclusion" if status == "excluded" else "unretained-" + row["status"],
        "artifact_ids": sorted({part["artifact_id"] for part in row.get("parts", [])})}


def _recover_version(version, recovery):
    if recovery is not None:
        version.update(retention=("accounted-exact-version-exclusion" if recovery["retention"]
            == "intentional-exclusion" else "recovered-exact-original-bytes"), recovery=recovery)
        return 0
    return 1


def _historical_artifacts(versions):
    return {aid for version in versions for ref in (version, version.get("recovery", {}))
            for aid in ref.get("artifact_ids", [])}


def compose(directory, session, layer_directories, current_inventory, *, scope_receipts=(),
            check_sources=True):
    """Reconcile a complete current census from immutable base and delta proofs."""
    directory = private_dir(directory)
    fresh_reference = input_reference(current_inventory)
    scope = [input_reference(path) for path in scope_receipts]
    layers = [_layer(path, directory) for path in layer_directories]
    if not layers:
        raise ValueError("Composition requires verified source layers")
    session.checkpoint("compose-source-proofs", fresh_inventory=fresh_reference,
        layer_proof_sha256=[layer["proof"]["sha256"] for layer in layers])
    prior_ids = {sid for layer in layers for sid in layer["sources"]}
    first_ids = set(layers[0]["sources"])
    artifact_proofs = {aid: (layer, row) for layer in layers for aid, row in layer["artifacts"].items()}
    recovered = {}
    for layer in layers:
        for sid, row in layer["sources"].items():
            if layer["accepted"].get(sid) not in {"retained", "excluded"}:
                continue
            version = _version_reference(layer, row)
            identity = _storage_identity(row)
            if identity not in recovered or version["retention"] == "artifact-verified":
                recovered[identity] = version
    counts, changes, fresh_ids, required_artifacts = Counter(), Counter(), set(), set()
    historical_gaps = 0
    active_path, history_path = directory / "composed-mappings.jsonl", directory / "composed-history.jsonl"
    with line_writer(active_path) as active, line_writer(history_path) as history:
        for number, original in enumerate(json_lines(current_inventory)):
            row = source_record(original)
            sid = row["source_identity"]
            if sid in fresh_ids:
                raise ValueError("Duplicate source identity in the full current census")
            fresh_ids.add(sid)
            versions = []
            for layer in layers:
                old = layer["sources"].get(sid)
                if old is None:
                    continue
                version = _version_reference(layer, old)
                if version["retention"].startswith("unretained-"):
                    historical_gaps += _recover_version(version, recovered.get(_storage_identity(old)))
                versions.append(version)
            required_artifacts.update(_historical_artifacts(versions))
            layer, old = _select_source(row, layers)
            status, reason = "conflict", "no-verified-current-source-mapping"
            mapping = None
            if row["status"] == "excluded":
                status, reason = "excluded", "current-inventory-exclusion"
            elif row["status"] != "conflict" and old is not None:
                status, reason = layer["accepted"][sid], old.get("reason", "verified-source-layer")
                mapping = {"layer_directory": layer["directory"], "run_id": layer["run_id"],
                    "layer_proof_sha256": layer["proof"]["sha256"], "source": old}
                if status == "retained":
                    for part in old["parts"]:
                        aid = part["artifact_id"]
                        if aid not in artifact_proofs or artifact_proofs[aid][1]["sha256"] != part[
                                "bundle_sha256"]:
                            raise ValueError("Composed source references another artifact proof")
                        required_artifacts.add(aid)
            checked = row["status"] != "excluded" and check_sources
            if checked and not source_matches(row, full_hash=True):
                status, reason = "conflict", "source-changed-after-full-census"
            if sid not in first_ids:
                change = "new"
            elif old is not None and layer is layers[0]:
                change = "unchanged"
            else:
                change = "changed-or-repaired"
            counts[status] += 1
            changes[change] += 1
            write_line(active, {"source_identity": sid, "status": status, "reason": reason,
                "current_source": row, "storage_mapping": mapping, "change": change,
                "current_source_bytes_checked": checked, "qualification": "unverified"})
            write_line(history, {"source_identity": sid, "status": "current", "versions": versions})
            if number % 1000 == 0:
                session.tick()
                save(directory / "progress.json", {"phase": "compose-source-checks",
                    "source_rows_checked": number, "counts": dict(counts)})
        for sid in sorted(prior_ids - fresh_ids):
            versions = []
            for layer in layers:
                if sid in layer["sources"]:
                    old = layer["sources"][sid]
                    version = _version_reference(layer, old)
                    if version["retention"].startswith("unretained-"):
                        historical_gaps += _recover_version(version, recovered.get(_storage_identity(old)))
                    versions.append(version)
            required_artifacts.update(_historical_artifacts(versions))
            write_line(history, {"source_identity": sid, "status": "removed-from-current-census",
                "historical_artifacts_deleted": False, "versions": versions})
    check_reference(fresh_reference)
    for layer in layers:
        for reference in layer["proof"]["files"]:
            check_reference(reference)
    for reference in scope:
        check_reference(reference)
    native_counts, native_complete = Counter(), True
    with line_writer(directory / "composed-native-proofs.jsonl") as output:
        for aid in sorted(required_artifacts):
            layer, artifact = artifact_proofs[aid]
            if not artifact["search_eligible"]:
                native_counts["binary_artifacts_outside_search_scope"] += 1
                write_line(output, {"artifact_id": aid, "eligible": False})
                continue
            proof = layer["native"].get(aid)
            complete = bool(proof and proof["coverage"]["complete"])
            native_complete &= complete
            native_counts["complete_text_artifacts" if complete else "pending_text_artifacts"] += 1
            native_counts["eligible_text_bytes"] += artifact["byte_length"]
            write_line(output, {"artifact_id": aid, "eligible": True, "complete": complete,
                "layer_proof_sha256": layer["proof"]["sha256"],
                "unit_census_sha256": proof.get("unit_census_sha256") if proof else None})
    local_files = [fresh_reference, input_reference(active_path), input_reference(history_path),
                   input_reference(directory / "composed-native-proofs.jsonl"), *scope]
    artifact_receipts = []
    for file_number, reference in enumerate(local_files):
        for part_number, body in _text_file_parts(reference["path"]):
            manifest = session.put("composition-" + str(file_number) + "-" + str(part_number),
                "source-census", body, {"schema": SCHEMA, "source_file_sha256": reference["sha256"],
                    "part": part_number, "search_eligible": False})
            stored, received = session.get(manifest["_id"])
            if sha(received.encode()) != sha(body.encode()) or stored["byte_count"] != len(body.encode()):
                raise ValueError("Composed proof artifact readback mismatch")
            artifact_receipts.append({"artifact_id": manifest["_id"],
                "body_utf8_sha256": stored["body_utf8_sha256"], "byte_length": stored["byte_count"]})
            if len(artifact_receipts) % 16 == 0:
                save(directory / "progress.json", {"phase": "compose-proof-artifacts",
                    "artifacts_verified": len(artifact_receipts)})
    current_complete = not counts["conflict"] and check_sources and bool(scope)
    result = {"schema": SCHEMA, "run_id": session.run_id, "parent_run_id": session.parent,
        "fresh_inventory": fresh_reference, "scope_receipts": scope,
        "root_enumeration_evidence_bound": bool(scope), "root_enumeration_performed_by_composer": False,
        "layer_proofs": [layer["proof"] for layer in layers], "source_count": len(fresh_ids),
        "source_counts": dict(counts), "changes": dict(changes),
        "current_source_census_sha256": digest(sorted(fresh_ids)),
        "removed_source_ids": sorted(prior_ids - fresh_ids), "historical_artifacts_deleted": 0,
        "historical_unretained_versions": historical_gaps,
        "historical_retention_complete": historical_gaps == 0,
        "current_source_reconciliation_complete": bool(current_complete),
        "native_coverage_complete": bool(native_complete), "native_counts": dict(native_counts),
        "native_coverage_scope": "complete referenced immutable bundles, including historical parts",
        "reconciliation_complete": bool(current_complete and native_complete and not historical_gaps),
        "factual_qualification_established": False, "source_artifact_uploads": 0,
        "native_unit_insertions": 0, "local_files": local_files,
        "composition_artifacts": artifact_receipts}
    save(directory / "composition-receipt.json", result)
    session.checkpoint("composed-complete" if result["reconciliation_complete"] else "composed-partial",
        composition={key: value for key, value in result.items()
                     if key not in {"removed_source_ids", "composition_artifacts", "layer_proofs"}},
        receipt_sha256=file_hash(directory / "composition-receipt.json"))
    save(directory / "progress.json", {"phase": "composed", "source_count": len(fresh_ids),
        "source_counts": dict(counts), "reconciliation_complete": result["reconciliation_complete"]})
    return result


def finish_composition(session):
    directory = session.directory
    receipt = json.loads((directory / "composition-receipt.json").read_bytes())
    if receipt["run_id"] != session.run_id or not receipt.get("reconciliation_complete"):
        raise ValueError("Complete current composition and historical retention proof are required")
    for reference in receipt["local_files"]:
        check_reference(reference)
    for layer in receipt["layer_proofs"]:
        for reference in layer["files"]:
            check_reference(reference)
    session.tick()
    result = session.runs.run_checkpoint(session.run_id, {"state": "finished", "checkpoint": {
        "phase": "composed-source-reconciliation-complete", "factual_qualification_established": False,
        "composition_receipt_sha256": file_hash(directory / "composition-receipt.json")}},
        session.state["revision"], session.state["lease_token"], session.owner,
        request_id="finish-composition-" + digest([session.run_id, session.state["revision"]]), actor=ACTOR)
    session.state["revision"] = result["run"]["revision"]
    session.runs.run_lease(session.run_id, "release", session.owner, session.state["lease_token"],
        expected_revision=session.state["revision"],
        request_id="release-" + digest([session.run_id, session.state["revision"]]), actor=ACTOR)
    session.state.pop("lease_token", None)
    session.state["finished"] = True
    session._save()
    return {"run_id": session.run_id, "complete": True, "state": "finished",
            "factual_qualification_established": False}
