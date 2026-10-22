"""The MongoDB inventory is an exhaustive union, never a CVS-filtered sample."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "mongodb_queue", ROOT / "scripts/mongodb_research_queue.py"
)
queue = importlib.util.module_from_spec(spec)
spec.loader.exec_module(queue)


def node(name, parent=None, children=(), **extra):
    return {
        "concept": name,
        "parentConcept": parent,
        "childConcepts": list(children),
        "researchedAt": "2026-10-20",
        "sourcesCount": 3,
        "aliases": [],
        **extra,
    }


def store(root, nodes=(), scores=None, text=""):
    directory = root / "concept-tree"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "tree.json").write_text(json.dumps(list(nodes)))
    (directory / "cvs-scores.json").write_text(json.dumps(scores or {}))
    (directory / "RESEARCH_QUEUE.md").write_text(text)


@pytest.fixture
def roots(tmp_path):
    repo, hub = tmp_path / "repo", tmp_path / "hub"
    store(repo)
    store(hub)
    return repo, hub


def inventory(roots, **kwargs):
    return queue.build_inventory(*roots, reservations=kwargs.pop("reservations", {}), **kwargs)


def by_name(value):
    return {row["concept"]: row for row in value["rows"]}


def test_exhaustive_union_uses_both_edge_directions_and_both_queues(roots):
    repo, hub = roots
    store(
        hub,
        [
            node("MongoDB", children=["Hub gap", "Node without child backlink"]),
            node("Node without child backlink", "MongoDB"),
            node("Parent-edge-only child", "MongoDB", ["Grandchild gap"]),
            node("Unrelated", children=["Do not include"]),
        ],
        text="- [ ] Concept: `Queue ancestor` | Parent: `MongoDB`\n"
        "- [ ] Concept: `Transitive queue child` | Parent: `Queue ancestor`\n"
        "- [x] Concept: `Completed only history` | Parent: `MongoDB`\n",
    )
    store(
        repo,
        [node("MongoDB", children=["Repo gap"]), node("Repo-only node", "MongoDB")],
        text="- [ ] Concept: `Repo queued gap` | Note: arbitrary tag order | Parent: `MongoDB`\n"
        "- [ ] Concept: `Atlas-only queued seed`\n"
        "- [ ] Concept: `Apple queue` | Parent: `Apple`\n",
    )
    result = inventory(roots)
    names = set(by_name(result))
    assert names == {
        "MongoDB",
        "Hub gap",
        "Repo gap",
        "Node without child backlink",
        "Parent-edge-only child",
        "Grandchild gap",
        "Repo-only node",
        "Queue ancestor",
        "Transitive queue child",
        "Repo queued gap",
        "Atlas-only queued seed",
    }
    assert result["stats"]["canonical_rows"] == 11
    assert len(result["gaps"]) == 7
    assert sum(len(c["row_ids"]) for c in result["cohorts"]) == len(names)


def test_alias_case_and_whitespace_preserve_all_labels_and_parent_provenance(roots):
    repo, hub = roots
    store(
        hub,
        [
            node("MongoDB", children=["Transaction Alias", "  TRANSACTIONS "]),
            node("Transactions", "MongoDB", aliases=["Transaction Alias"]),
        ],
        text="- [ ] Concept: `transaction alias` | Parent: `MongoDB Atlas`\n",
    )
    store(repo, [node("mongodb", children=["transactions"]), node("transactions", "mongodb")])
    result = inventory(roots)
    row = by_name(result)["Transactions"]
    assert row["coverage_category"] == "covered"
    assert set(row["original_labels"]) == {
        "Transactions",
        "transactions",
        "Transaction Alias",
        "transaction alias",
        "  TRANSACTIONS ",
    }
    assert {p["parent"] for p in row["parent_provenance"]} == {
        "MongoDB",
        "mongodb",
        "MongoDB Atlas",
    }
    assert len(row["originals"]) == 7
    assert result["stats"]["alias_covered_labels"] >= 4
    assert row["id"] == queue.stable_id("transactions")
    assert len(result["rows"]) == 2


def test_guarded_formatting_equivalence_and_ambiguous_slug_collision(roots):
    repo, hub = roots
    store(
        hub,
        [
            node("MongoDB", children=["`$natural` hint and collection scans", "c", "C++", "C#"]),
            node(
                "natural hint and collection scans",
                "MongoDB",
                slug="natural-hint-and-collection-scans",
            ),
            node("C++", "MongoDB", slug="c"),
            node("C#", "MongoDB", slug="c"),
        ],
    )
    result = inventory(roots)
    rows = by_name(result)
    assert "`$natural` hint and collection scans" not in rows
    assert rows["natural hint and collection scans"]["coverage_category"] == "covered"
    assert rows["natural hint and collection scans"]["formatting_matches"] == [
        {
            "label": "`$natural` hint and collection scans",
            "owner": "natural hint and collection scans",
        }
    ]
    assert rows["c"]["coverage_category"] == "frontier"
    assert rows["c"]["identity_review"] == [{"label": "c", "possible_owners": ["C#", "C++"]}]
    assert rows["C++"]["id"] != rows["C#"]["id"]


def test_score_precedence_alias_inheritance_dates_and_cross_store_union(roots):
    repo, hub = roots
    store(
        hub,
        [
            node("MongoDB", children=["Scored alias", "Hub sidecar only", "Queue scored"]),
            node(
                "Scored canonical",
                "MongoDB",
                aliases=["Scored alias"],
                cvs=2.1,
                cvsScoredAt="2026-09-01",
                cvsDecision="SKIP",
            ),
        ],
        scores={
            "SCORED ALIAS": {"cvs": 4.9, "scoredAt": "2026-10-21"},
            "Repo-only inverse child": {"cvs": 3.9, "scoredAt": "2026-10-15"},
            "Hub sidecar only": {"cvs": 3.7, "scoredAt": "2026-10-22", "decision": "RESEARCH"},
        },
        text="- [ ] Concept: `Queue scored` | Parent: `MongoDB` | Other: `x` | CVS: `1.75`\n",
    )
    store(
        repo,
        [
            node("Scored canonical", "MongoDB", cvs=2.9, cvsScoredAt="2026-10-01"),
            node("Repo-only inverse child", "MongoDB", researchedAt=None),
        ],
        scores={"Hub sidecar only": {"cvs": 2.2, "scoredAt": "2026-10-01"}},
    )
    rows = by_name(inventory(roots))
    assert rows["Scored canonical"]["cvs"] == 2.9
    assert rows["Scored canonical"]["score"]["source"] == "repo"
    assert [r["kind"] for r in rows["Scored canonical"]["score_history"]] == [
        "node",
        "node",
        "sidecar",
    ]
    assert rows["Hub sidecar only"]["cvs"] == 3.7
    assert rows["Hub sidecar only"]["score"]["scoredAt"] == "2026-10-22"
    assert rows["Repo-only inverse child"]["cvs"] == 3.9
    assert rows["Repo-only inverse child"]["score"]["source"] == "hub"
    assert rows["Queue scored"]["cvs"] == 1.75
    assert rows["Queue scored"]["score"]["line"] == 1


def test_unknown_scores_stay_null_and_do_not_inherit_parent_score(roots):
    repo, hub = roots
    store(
        hub,
        [node("MongoDB", children=["Unscored", "Bad score"], cvs=5)],
        scores={"Bad score": {"cvs": float("nan")}},
    )
    rows = by_name(inventory(roots))
    assert rows["Unscored"]["cvs"] is None
    assert rows["Unscored"]["score"] is None
    assert rows["Bad score"]["cvs"] is None
    assert rows["Unscored"]["eligibility"] == "needs-scoring"


def test_review_nodes_and_domain_containers_are_not_completed_by_node_presence(roots):
    repo, hub = roots
    store(
        hub,
        [
            node("MongoDB", kind="domain", sourcesCount=0),
            node("No sources", "MongoDB", sourcesCount=0),
            node("No date", "MongoDB", researchedAt=None),
            node("Covered", "MongoDB"),
            node("Explicit revisit", "MongoDB"),
        ],
        text="- [ ] Concept: `Explicit revisit` | Parent: `MongoDB` | Mode: `revisit`\n",
    )
    rows = by_name(inventory(roots))
    assert rows["MongoDB"]["coverage_category"] == "container-review"
    assert rows["No sources"]["coverage_category"] == "refresh-review"
    assert rows["No date"]["coverage_issues"] == ["missing-research-date"]
    assert rows["Explicit revisit"]["coverage_category"] == "refresh-review"
    assert rows["Covered"]["coverage_category"] == "covered"


def test_low_scores_unscored_alias_covered_and_held_are_rendered(roots):
    repo, hub = roots
    store(
        hub,
        [
            node("MongoDB", children=["Low", "Unknown", "Covered alias"]),
            node("Covered", "MongoDB", aliases=["Covered alias"]),
        ],
        scores={"Low": {"cvs": 1.2}},
    )
    result = inventory(roots, reservations={"covered ALIAS": "suite paused", "low": "run one"})
    rows = by_name(result)
    assert rows["Covered"]["reservation_holder"] == "suite paused"
    assert rows["Covered"]["eligibility"] == "held"
    assert rows["Low"]["cvs"] == 1.2
    markdown = queue.render_markdown(result)
    for value in ("Low", "Unknown", "Covered alias", "suite paused", "run one", "1.20"):
        assert value in markdown
    assert result["stats"]["below_legacy_gate_gaps"] == 1


def test_multiple_alias_reservations_preserve_every_holder(roots):
    repo, hub = roots
    store(
        hub,
        [
            node("MongoDB", children=["Pending"]),
            node("Pending", "MongoDB", aliases=["Alias"], sourcesCount=0),
        ],
    )
    row = by_name(inventory(roots, reservations={"pending": "run B", "ALIAS": "run A"}))["Pending"]
    assert row["reservation_holder"] == "run A; run B"
    assert len(row["reservation_provenance"]) == 2


def test_group_by_specific_source_pool_across_parents_and_prioritize_cvs(roots):
    repo, hub = roots
    store(
        hub,
        [
            node("MongoDB", children=["Query family", "Other query family", "Atlas Security"]),
            node("Query family", "MongoDB", ["Index bounds", "Explain verbosity"]),
            node("Other query family", "MongoDB", ["Compound index ordering"]),
            node("Atlas Security", "MongoDB", ["SAML identity federation"]),
        ],
        scores={
            "Index bounds": {"cvs": 4.1},
            "Compound index ordering": {"cvs": 4.7},
            "Explain verbosity": {"cvs": 4.4},
            "SAML identity federation": {"cvs": 2.2},
        },
    )
    result = inventory(roots)
    rows = by_name(result)
    assert (
        rows["Compound index ordering"]["rank"]
        < rows["Explain verbosity"]["rank"]
        < rows["Index bounds"]["rank"]
    )
    assert rows["Index bounds"]["cohort_id"] == rows["Compound index ordering"]["cohort_id"]
    assert rows["Explain verbosity"]["cohort_id"] != rows["Index bounds"]["cohort_id"]
    assert rows["SAML identity federation"]["source_family"] == "identity-governance"
    assert result == inventory(roots)
    assert result["cohorts"] == sorted(result["cohorts"], key=lambda c: (c["priority"], c["id"]))


def test_source_pool_matching_prefers_specific_product_surface():
    assert (
        queue.source_family("Atlas Search index sync lag", ["MongoDB Query Tools"])["family"]
        == "search-vector"
    )
    assert (
        queue.source_family("Federated Authentication", ["MongoDB Atlas"])["family"]
        == "identity-governance"
    )
    assert (
        queue.source_family("Private endpoints transfer charges", ["MongoDB Atlas"])["family"]
        == "networking"
    )
    assert queue.source_family("Time-Series Bucketing", ["MongoDB"])["family"] == "time-series"


def test_queue_merge_is_append_only_and_preserves_history_and_non_mongodb_rows(roots):
    repo, hub = roots
    existing = "# Queue\n\n- [ ] Concept: `Apple work` | Parent: `Apple`\n- [x] Concept: `Old MongoDB work` | Parent: `MongoDB`\n"
    store(
        hub,
        [
            node("MongoDB", children=["Low", "Unknown", "Alias"]),
            node("Canonical", "MongoDB", aliases=["Alias"]),
        ],
        text=existing,
        scores={"Low": {"cvs": 1.4}},
    )
    result = inventory(roots)
    merged = queue.merge_queue(existing, result)
    assert merged.startswith(existing)
    assert "Concept: `Low`" in merged and "Concept: `Unknown`" in merged
    assert "Concept: `Canonical`" not in merged
    assert queue.merge_queue(merged, result) == merged
    assert "CVS: `1.400`" in merged


def test_ranked_merge_preserves_older_foreign_content_and_is_idempotent(roots):
    original = "# Older ranked queue\n\n| Apple | 4.9 |\n"
    result = inventory(roots)
    merged = queue.merge_ranked(original, result)
    assert merged.startswith(queue.BEGIN)
    assert merged.endswith(original)
    assert "Previous ranked snapshot (retained)" in merged
    assert queue.merge_ranked(merged, result) == merged
    with pytest.raises(ValueError, match="Ambiguous"):
        queue.merge_ranked(queue.BEGIN + queue.BEGIN + queue.END, result)


def test_apply_checks_fingerprints_and_backs_up_changed_queue_without_tree_mutation(
    roots, tmp_path
):
    repo, hub = roots
    original = "# Foreign queue\n\n- [ ] Concept: `Apple`\n"
    store(hub, [node("MongoDB", children=["New gap"])], text=original)
    result = inventory(roots)
    tree = (hub / "concept-tree/tree.json").read_bytes()
    changed = queue.apply_inventory(result, json_path=tmp_path / "inventory.json")
    record = next(r for r in changed if r["path"] == str(hub / "concept-tree/RESEARCH_QUEUE.md"))
    assert Path(record["backup"]).read_text() == original
    assert (hub / "concept-tree/RESEARCH_QUEUE.md").read_text().startswith(original)
    assert (hub / "concept-tree/tree.json").read_bytes() == tree
    assert json.loads((tmp_path / "inventory.json").read_text())["stats"] == result["stats"]
    with pytest.raises(RuntimeError, match="input changed"):
        queue.apply_inventory(result)


def test_cli_defaults_to_read_only_json_and_never_creates_output(roots):
    repo, hub = roots
    store(hub, [node("MongoDB", children=["New gap"])])
    before = {str(p): p.read_bytes() for root in roots for p in root.rglob("*") if p.is_file()}
    process = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/mongodb_research_queue.py"),
            "--repo",
            str(repo),
            "--hub",
            str(hub),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(process.stdout)["stats"]["canonical_gaps"] == 1
    after = {str(p): p.read_bytes() for root in roots for p in root.rglob("*") if p.is_file()}
    assert before == after
    assert not (hub / "research/.global.lock").exists()


def test_rerank_verified_overlay_updates_order_stats_and_gates(roots):
    repo, hub = roots
    store(hub, [node("MongoDB", children=["Index A", "Index B", "Index gate"])])
    result = inventory(roots)
    rows = by_name(result)
    rows["Index B"].update(
        cvs=4.3,
        score={"cvs": 4.3, "axes": {"viability": 5, "relevance": 5, "interest": 3}},
        decision="RESEARCH",
    )
    rows["Index A"].update(
        cvs=4.3,
        score={"cvs": 4.3, "axes": {"viability": 4, "relevance": 5, "interest": 3}},
        decision="RESEARCH",
    )
    rows["Index gate"].update(
        cvs=4.5, score={"cvs": 4.5, "axes": {"viability": 1}}, decision="SKIP"
    )
    queue.rerank_inventory(result)
    assert rows["Index B"]["rank"] < rows["Index A"]["rank"]
    assert rows["Index gate"]["eligibility"] == "hard-gated-review"
    assert result["stats"]["unscored_gaps"] == 0
    assert result["stats"]["scored_gaps"] == 3
    assert result["cohorts"][0]["max_cvs"] == 4.5


def test_queue_backtick_labels_roundtrip_without_losing_formatting(roots):
    repo, hub = roots
    name = "Reading indexed `$or` plans with explain"
    parent = "MongoDB `Planner`"
    store(hub, [node(parent, children=[name, "`$hint`"])])
    result = inventory(roots)
    merged = queue.merge_queue("# Existing\n", result)
    path = hub / "concept-tree/roundtrip.md"
    path.write_text(merged)
    parsed = {row["concept"]: row for row in queue.load_queue(path)}
    assert set(parsed) == {name, "`$hint`"}
    assert parsed[name]["parentConcept"] == parent
    assert queue.merge_queue(merged, result) == merged


def test_apply_preserves_crlf_history_and_refuses_json_over_input(roots):
    repo, hub = roots
    store(hub, [node("MongoDB", children=["Gap"])])
    path = hub / "concept-tree/RESEARCH_QUEUE.md"
    prefix = b"# History\r\n\r\n- [ ] Concept: `Apple`\r\n"
    path.write_bytes(prefix)
    result = inventory(roots)
    with pytest.raises(ValueError, match="must not overwrite"):
        queue.apply_inventory(result, json_path=hub / "concept-tree/tree.json")
    assert path.read_bytes() == prefix
    queue.apply_inventory(result)
    assert path.read_bytes().startswith(prefix)


def marked_score(row, *, rationale="Specific operational value and documented source coverage"):
    row.update(
        cvs=4.725,
        decision="RESEARCH",
        score={
            "kind": "cfe-model",
            "cvs": 4.725,
            "axes": {"rel": 5, "use": 5, "nov": 4, "int": 4.5, "via": 5},
            "rationale": rationale,
            "scoredAt": "2026-10-22",
            "subject": "mongodb",
        },
    )


@pytest.fixture
def checker(tmp_path):
    # Exercise the subprocess handoff without depending on an operator install.
    # The real canonical checker is separately exercised in local verification.
    path = tmp_path / "cvs_check.py"
    path.write_text(
        "import json,sys\nx=json.load(sys.stdin)\n"
        "assert sys.argv[1:] == ['-', '--threshold', '0']\n"
        "assert all(r['cvs'] == 4.725 and r['interest'] == 4.5 for r in x['rows'])\n"
    )
    return path


def test_private_parent_and_generic_descendants_stay_hub_only(roots, monkeypatch):
    repo, hub = roots
    monkeypatch.setenv("PRIVACY_DENYLIST", "Restricted Customer")
    store(
        hub,
        [
            node("MongoDB", children=["Restricted Customer Workflow", "Public gap"]),
            node("Restricted Customer Workflow", "MongoDB", ["Generic child"]),
            node("Generic child", "Restricted Customer Workflow", ["Generic frontier"]),
        ],
        text="- [ ] Concept: `Queued leaf` | Parent: `Generic frontier`\n",
    )
    store(repo, [], text="# Retained\n- [ ] Concept: `Apple`\n")
    result = inventory(roots)
    safe = queue.public_inventory(result)
    assert result["publication"]["withheld_rows"] == 4
    assert set(by_name(safe)) == {"MongoDB", "Public gap"}
    queue.apply_inventory(result, json_path=repo / "concept-tree/mongodb-inventory.json")
    assert "Generic frontier" in (hub / "concept-tree/RESEARCH_QUEUE.md").read_text()
    for name in ("RESEARCH_QUEUE.md", "RESEARCH_QUEUE_RANKED.md", "mongodb-inventory.json"):
        text = (repo / "concept-tree" / name).read_text()
        for private in ("Restricted Customer", "Generic child", "Generic frontier", "Queued leaf"):
            assert private not in text
    assert "Apple" in (repo / "concept-tree/RESEARCH_QUEUE.md").read_text()
    assert (hub / "research/.queue-inventory-backups").is_dir()
    assert not list((repo / "concept-tree").glob("*.bak-mongodb-*"))


def test_public_json_removes_occurrence_paths_and_scrubs_operator_metadata(roots):
    repo, hub = roots
    store(hub, [node("MongoDB", children=["Gap"])])
    result = inventory(roots, reservations={"gap": "/Users/real.operator/private-run"})
    row = by_name(result)["Gap"]
    row["score"] = {
        "path": "/private/raw/library/source.json",
        "rationale": "From /Users/real.operator/private-run",
    }
    safe = queue.public_inventory(result)
    text = json.dumps(safe)
    assert "/Users/real.operator" not in text
    assert "/private/raw/library" not in text
    assert str(hub) not in text and str(repo) not in text
    assert "path" not in by_name(safe)["Gap"]["originals"][0]
    assert "repo" not in safe and "hub" not in safe and "inputs" not in safe


def test_worktree_uses_primary_checkout_private_policy(roots, tmp_path):
    repo, hub = roots
    primary = tmp_path / "primary"
    git_dir = primary / ".git/worktrees/test"
    git_dir.mkdir(parents=True)
    (git_dir / "commondir").write_text("../..")
    (repo / ".git").write_text("gitdir: " + str(git_dir))
    (primary / ".privacy-denylist").write_text("Restricted Customer\n")
    store(hub, [node("MongoDB", children=["Restricted Customer Workflow"])])
    result = inventory(roots)
    assert result["publication"]["withheld_rows"] == 1
    assert set(by_name(queue.public_inventory(result))) == {"MongoDB"}
    (primary / ".privacy-denylist").write_text("Changed Policy\n")
    with pytest.raises(RuntimeError, match="input changed"):
        queue.apply_inventory(result)


def test_historical_slug_alias_and_publication_private_flag_exclude_descendants(roots):
    repo, hub = roots
    store(
        hub,
        [
            node("MongoDB", children=["Private container"]),
            node("Private container", "MongoDB", ["Current child"], publicationPrivate=True),
            node(
                "Current child",
                "Private container",
                aliases=["Old child"],
                slugAliases=["old-child"],
            ),
        ],
    )
    store(repo, [node("Old child", children=["Old grandchild"], slug="old-child")])
    result = inventory(roots)
    assert {"Private container", "Current child", "Old grandchild"} <= set(by_name(result))
    assert set(by_name(queue.public_inventory(result))) == {"MongoDB"}


def test_marked_scores_persist_precision_provenance_history_and_reload_after_queue_completion(
    roots, checker
):
    repo, hub = roots
    old = {
        "Gap": {"cvs": 2.2, "scoredAt": "2026-09-01", "rationale": "Old retained rationale"},
        "Non-Mongo record": {"cvs": 1.3},
    }
    store(hub, [node("MongoDB", children=["Gap"])], scores=old)
    store(repo, scores=old)
    result = inventory(roots)
    marked_score(by_name(result)["Gap"])
    queue.rerank_inventory(result)
    queue.apply_inventory(result, cvs_checker=checker)
    for root in roots:
        saved = json.loads((root / "concept-tree/cvs-scores.json").read_text())
        assert saved["Gap"]["cvs"] == 4.725
        assert saved["Gap"]["axes"]["interest"] == 4.5
        assert saved["Gap"]["scoredAt"] == "2026-10-22"
        assert saved["Gap"]["subject"] == "mongodb"
        assert saved["Gap"]["history"] == [old["Gap"]]
        assert saved["Non-Mongo record"] == old["Non-Mongo record"]
        path = root / "concept-tree/RESEARCH_QUEUE.md"
        path.write_text(path.read_text().replace("- [ ]", "- [x]"))
    fresh = inventory(roots)
    assert by_name(fresh)["Gap"]["cvs"] == 4.725
    assert by_name(fresh)["Gap"]["score"]["rationale"].startswith("Specific operational")
    assert by_name(fresh)["Gap"]["score"]["record_kind"] == "cfe-model"
    assert "4.725" in queue.render_markdown(fresh)


def test_private_score_records_retained_only_in_hub_sidecar(roots, checker, monkeypatch):
    repo, hub = roots
    monkeypatch.setenv("PRIVACY_DENYLIST", "Restricted Customer")
    store(
        hub,
        [
            node("MongoDB", children=["Restricted Customer Workflow", "Public gap"]),
            node("Restricted Customer Workflow", "MongoDB", ["Generic gap"]),
        ],
    )
    store(repo, scores={"Generic gap": {"cvs": 2.0}})
    result = inventory(roots)
    marked_score(by_name(result)["Generic gap"])
    marked_score(
        by_name(result)["Public gap"],
        rationale="Restricted Customer example /Users/real.operator/work",
    )
    queue.apply_inventory(result, cvs_checker=checker)
    hub_scores = json.loads((hub / "concept-tree/cvs-scores.json").read_text())
    public_scores = json.loads((repo / "concept-tree/cvs-scores.json").read_text())
    assert "Generic gap" in hub_scores and "Generic gap" not in public_scores
    assert "Restricted Customer" in hub_scores["Public gap"]["rationale"]
    assert "Restricted Customer" not in public_scores["Public gap"]["rationale"]
    assert "/Users/real.operator" not in json.dumps(public_scores)


def test_unmarked_scores_do_not_persist_and_invalid_marked_scores_fail_before_writes(
    roots, checker
):
    repo, hub = roots
    store(hub, [node("MongoDB", children=["Gap"])])
    result = inventory(roots)
    by_name(result)["Gap"].update(cvs=4.725, decision="RESEARCH", score={"kind": "queue"})
    queue.apply_inventory(result, cvs_checker=checker)
    assert json.loads((hub / "concept-tree/cvs-scores.json").read_text()) == {}
    result = inventory(roots)
    marked_score(by_name(result)["Gap"])
    by_name(result)["Gap"]["score"].pop("rationale")
    before = {
        str(p): p.read_bytes()
        for root in roots
        for p in (root / "concept-tree").glob("*")
        if p.is_file()
    }
    with pytest.raises(ValueError, match="missing rationale"):
        queue.apply_inventory(result, cvs_checker=checker)
    after = {
        str(p): p.read_bytes()
        for root in roots
        for p in (root / "concept-tree").glob("*")
        if p.is_file()
    }
    assert before == after


def test_rejected_canonical_checker_keeps_sources_unchanged(roots, tmp_path):
    repo, hub = roots
    store(hub, [node("MongoDB", children=["Gap"])])
    result = inventory(roots)
    marked_score(by_name(result)["Gap"])
    checker = tmp_path / "reject.py"
    checker.write_text("raise SystemExit(1)\n")
    before = (hub / "concept-tree/cvs-scores.json").read_bytes()
    with pytest.raises(ValueError, match="Canonical CVS checker rejected"):
        queue.apply_inventory(result, cvs_checker=checker)
    assert (hub / "concept-tree/cvs-scores.json").read_bytes() == before


def test_existing_ranked_generated_section_moves_ahead_of_old_bytes(roots):
    old = "# Previous data\n\nOld bytes\n"
    inventory_value = inventory(roots)
    previous_generated = old + queue.BEGIN + "\nold generated\n" + queue.END
    merged = queue.merge_ranked(previous_generated, inventory_value)
    assert merged.startswith(queue.BEGIN)
    assert merged.index("Previous ranked snapshot (retained)") < merged.index(old)
    assert queue.merge_ranked(merged, inventory_value) == merged


def test_rerank_accepts_abbreviated_axes_and_public_projection_cannot_apply(roots):
    repo, hub = roots
    store(hub, [node("MongoDB", children=["Gap"])])
    result = inventory(roots)
    row = by_name(result)["Gap"]
    marked_score(row)
    row["score"]["axes"]["via"] = 1
    queue.rerank_inventory(result)
    assert row["eligibility"] == "hard-gated-review"
    with pytest.raises(ValueError, match="full private"):
        queue.apply_inventory(queue.public_inventory(result))


@pytest.mark.parametrize("size", [0, 9])
def test_invalid_cohort_size_is_rejected(roots, size):
    with pytest.raises(ValueError, match="cohort_size"):
        inventory(roots, cohort_size=size)
