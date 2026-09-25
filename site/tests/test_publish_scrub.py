"""publish_scrub — operator-private names and home paths never reach the snapshot."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import publish_scrub as scrub  # noqa: E402
import tree_guard  # noqa: E402


def _node(concept, parent=None, children=(), aliases=()):
    return {"concept": concept, "skillId": None, "parentConcept": parent,
            "childConcepts": list(children), "researchedAt": "2026-08-01",
            "sourcesCount": 1, "conceptsCount": len(children),
            "slug": concept.lower().replace(" ", "-"), "aliases": list(aliases)}


def test_denylisted_node_and_its_whole_subtree_are_dropped():
    nodes = [_node("Root", children=["Acme Account Intelligence", "Public Topic"]),
             _node("Acme Account Intelligence", "Root", children=["Vendor Procurement Signals"]),
             _node("Vendor Procurement Signals", "Acme Account Intelligence"),
             _node("Public Topic", "Root")]

    kept, dropped, refs = scrub.filter_tree(nodes, ["acme"])

    assert [n["concept"] for n in kept] == ["Root", "Public Topic"]
    assert dropped == ["Acme Account Intelligence", "Vendor Procurement Signals"]
    assert kept[0]["childConcepts"] == ["Public Topic"]
    assert refs == 1


def test_denylisted_frontier_names_are_removed_from_child_lists():
    nodes = [_node("Diagnostics", children=["acme-diag and Workflows", "Log Analysis"])]

    kept, dropped, refs = scrub.filter_tree(nodes, ["acme-diag"])

    assert kept[0]["childConcepts"] == ["Log Analysis"]
    assert dropped == [] and refs == 1


def test_slugified_names_are_matched_because_the_site_publishes_slugs():
    nodes = [_node("Case Tracker", children=["TS Tools Support API", "Case Notes"]),
             _node("TS Tools Support API Reference", "Root")]

    kept, dropped, refs = scrub.filter_tree(nodes, ["[redacted]"])

    assert kept[0]["childConcepts"] == ["Case Notes"] and refs == 1
    assert dropped == ["TS Tools Support API Reference"]


def test_alias_match_drops_the_node_and_its_reference():
    nodes = [_node("Root", children=["Big Bank Notes"]),
             _node("Big Bank Notes", "Root", aliases=["ACME notes"])]

    kept, dropped, _ = scrub.filter_tree(nodes, ["acme"])

    assert [n["concept"] for n in kept] == ["Root"]
    assert kept[0]["childConcepts"] == [] and dropped == ["Big Bank Notes"]


def test_matching_is_case_insensitive_and_an_empty_denylist_changes_nothing():
    nodes = [_node("Root", children=["ACME Thing"]), _node("ACME Thing", "Root")]

    assert scrub.filter_tree(nodes, [])[0] == nodes
    assert [n["concept"] for n in scrub.filter_tree(nodes, ["acme"])[0]] == ["Root"]


def test_filter_does_not_mutate_its_input():
    nodes = [_node("Root", children=["Acme X"]), _node("Acme X", "Root")]
    before = json.dumps(nodes)

    scrub.filter_tree(nodes, ["acme"])

    assert json.dumps(nodes) == before


def test_operator_home_paths_become_tilde_relative():
    text = '{"file": "/Users/jane.doe/.global-ai-hub/llms-full/files/a.txt", "n": 1}'

    out, n = scrub.scrub_home_paths(text)

    assert out == '{"file": "~/.global-ai-hub/llms-full/files/a.txt", "n": 1}'
    assert n == 1


def test_cli_tree_writes_the_filtered_copy_and_reports_what_it_dropped(tmp_path, capsys,
                                                                       monkeypatch):
    monkeypatch.setattr(scrub.gate, "denylist", list)
    src = tmp_path / "tree.json"
    dest = tmp_path / "out" / "tree.json"
    src.write_text(json.dumps([_node("Root", children=["Acme X"]), _node("Acme X", "Root")]))

    assert scrub.main(["tree", str(src), str(dest), "--term", "acme"]) == 0

    assert [n["concept"] for n in json.loads(dest.read_text())] == ["Root"]
    assert dest.read_text().endswith("\n")
    assert "dropped 1 node" in capsys.readouterr().out


def test_cli_paths_scrubs_files_walks_dirs_and_never_touches_mirrors(tmp_path, monkeypatch):
    monkeypatch.setattr(scrub.gate, "REPO", str(tmp_path))
    manifest = tmp_path / "outputs" / "llms-full" / "manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text('{"file": "/Users/jane/x.txt"}')
    mirror = tmp_path / "outputs" / "llms-full" / "files" / "x.txt"
    mirror.parent.mkdir()
    mirror.write_text("see /Users/jane/x.txt")
    topical = tmp_path / "outputs" / "llms-topical"
    topical.mkdir()
    (topical / "manifest.json").write_text('["/Users/jane/a.md"]')
    (topical / "keep.py").write_text("'/Users/jane/'")

    assert scrub.main(["paths", str(manifest), str(mirror), str(topical)]) == 0

    assert manifest.read_text() == '{"file": "~/x.txt"}'
    assert mirror.read_text() == "see /Users/jane/x.txt"
    assert (topical / "manifest.json").read_text() == '["~/a.md"]'
    assert (topical / "keep.py").read_text() == "'/Users/jane/'"


def test_cli_without_a_command_is_a_usage_error(capsys):
    assert scrub.main([]) == 2
    assert "Usage" in capsys.readouterr().err


def test_refresh_snapshot_scrubs_the_tree_and_manifests_before_it_stages():
    sh = (ROOT / "scripts" / "refresh_snapshot.sh").read_text()

    assert "publish_scrub.py tree" in sh and "publish_scrub.py paths" in sh
    assert sh.index("publish_scrub.py tree") < sh.index("one_tree \"$")
    assert sh.index("publish_scrub.py paths") < sh.index("git add -A")


# --- tree_guard: the snapshot's refusal checks -------------------------------


def _gnode(name, kids=()):
    return {"concept": name, "childConcepts": list(kids)}


def test_tree_guard_refuses_a_frontier_wipe_with_stable_node_count():
    dest = [_gnode("Root", [f"F{i}" for i in range(100)])]
    src = [_gnode("Root", [])]  # same nodes, every dangling ref stripped

    reason = tree_guard.check(src, dest, node_tol=10, frontier_tol=50)

    assert reason and "frontier" in reason


def test_tree_guard_allows_frontier_drop_explained_by_research():
    dest = [_gnode("Root", [f"F{i}" for i in range(100)])]
    src = dest[:1] + [_gnode(f"F{i}") for i in range(80)]  # 80 researched

    assert tree_guard.check(src, dest, node_tol=10, frontier_tol=50) is None


def test_tree_guard_still_refuses_a_node_shrink():
    dest = [_gnode(f"N{i}") for i in range(50)]
    src = dest[:30]

    reason = tree_guard.check(src, dest, node_tol=10, frontier_tol=50)

    assert reason and "concepts" in reason


def test_refresh_snapshot_runs_tree_guard_before_copying_the_tree():
    sh = (ROOT / "scripts" / "refresh_snapshot.sh").read_text()
    body = sh[sh.index("one_tree() {"):]
    assert body.index("tree_guard.py") < body.index('one "$src" "$dest"')
    assert "FRONTIER_SHRINK_TOLERANCE" in sh


def test_tree_guard_refuses_a_frontier_replaced_wholesale():
    dest = [_gnode("Root", [f"F{i}" for i in range(100)])]
    src = [_gnode("Root", [f"G{i}" for i in range(100)])]  # same count, all names lost

    reason = tree_guard.check(src, dest, node_tol=10, frontier_tol=50)

    assert reason and "frontier" in reason


def test_tree_guard_does_not_credit_unrelated_node_growth():
    dest = [_gnode("Root", [f"F{i}" for i in range(100)])]
    src = [_gnode("Root", [])] + [_gnode(f"Unrelated{i}") for i in range(100)]

    reason = tree_guard.check(src, dest, node_tol=10, frontier_tol=50)

    assert reason and "frontier" in reason


def _run_guard(tmp_path, src, dest):
    import subprocess
    s, d = tmp_path / "src.json", tmp_path / "dest.json"
    if src is not None:
        s.write_text(src if isinstance(src, str) else json.dumps(src))
    if dest is not None:
        d.write_text(dest if isinstance(dest, str) else json.dumps(dest))
    return subprocess.run([sys.executable, str(ROOT / "scripts" / "tree_guard.py"), str(s), str(d)],
                          capture_output=True, text=True, check=False)


def test_tree_guard_cli_refuses_an_unreadable_src(tmp_path):
    result = _run_guard(tmp_path, "{not json", [_gnode("Root")])

    assert result.returncode == 1
    assert "REFUSED" in result.stderr


def test_tree_guard_cli_refuses_a_src_that_is_not_a_node_list(tmp_path):
    result = _run_guard(tmp_path, {"concept": "Root"}, [_gnode("Root")])

    assert result.returncode == 1
    assert "REFUSED" in result.stderr and "Traceback" not in result.stderr


def test_tree_guard_cli_passes_and_says_so_when_dest_is_missing(tmp_path):
    result = _run_guard(tmp_path, [_gnode("Root")], None)

    assert result.returncode == 0
    assert "skipped" in result.stderr


def test_tree_guard_cli_logs_counts_on_pass_and_exits_1_on_refusal(tmp_path):
    ok = _run_guard(tmp_path, [_gnode("Root", ["F"])], [_gnode("Root", ["F"])])
    assert ok.returncode == 0 and "frontier 1 -> 1" in ok.stdout

    bad = _run_guard(tmp_path, [_gnode("Root")], [_gnode("Root", [f"F{i}" for i in range(60)])])
    assert bad.returncode == 1 and "REFUSED" in bad.stderr


def test_tree_guard_cli_refuses_a_string_childconcepts_in_src(tmp_path):
    src = [{"concept": "Root", "childConcepts": "Orphan"}]

    result = _run_guard(tmp_path, src, [_gnode("Root", ["Orphan"])])

    assert result.returncode == 1 and "REFUSED" in result.stderr


def test_tree_guard_cli_refuses_non_hashable_fields_without_a_traceback(tmp_path):
    src = [{"concept": "Root", "childConcepts": [["x"]]}]

    result = _run_guard(tmp_path, src, [_gnode("Root")])

    assert result.returncode == 1
    assert "REFUSED" in result.stderr and "Traceback" not in result.stderr


def test_tree_guard_refuses_over_a_present_but_malformed_dest(tmp_path):
    dest = [{"concept": "Root", "childConcepts": "Orphan"}]

    result = _run_guard(tmp_path, [_gnode("Root")], dest)

    assert result.returncode == 1 and "REFUSED" in result.stderr


def test_tree_guard_counts_unique_concepts_not_padded_duplicates():
    dest = [_gnode(f"N{i}") for i in range(50)]
    src = [_gnode("N0") for _ in range(50)]  # 50 entries, 1 real concept

    reason = tree_guard.check(src, dest, node_tol=10, frontier_tol=50)

    assert reason and "concepts" in reason
