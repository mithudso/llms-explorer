"""Tests for the concept tree (scripts/concept_tree.py) and its Concepts tab.

The live tree currently has ZERO frontier concepts, so greying-out — the whole
point of the feature — would be untested against real data. Every frontier case
here is therefore driven from a fixture.
"""

import json

import pytest

import concept_tree as ct

# Two researched roots. Deliberately includes both frontier sources:
#   "Vector Stores"   — named as a child, no node of its own
#   "Graph Databases" — only in the research queue
NODES = [
    {"concept": "Retrieval", "skillId": "ai-rag-retrieval", "parentConcept": None,
     "childConcepts": ["Chunking", "Vector Stores"],
     "researchedAt": "2026-08-01", "sourcesCount": 4, "conceptsCount": 9},
    {"concept": "Chunking", "skillId": "ai-rag-retrieval", "parentConcept": "Retrieval",
     "childConcepts": [], "researchedAt": "2026-08-02", "sourcesCount": 2,
     "conceptsCount": 3},
    {"concept": "Serving", "skillId": "ai-llm-model-layer", "parentConcept": None,
     "childConcepts": [], "researchedAt": "2026-08-03", "sourcesCount": 1,
     "conceptsCount": 1},
]

QUEUE = """# Concept Research Queue

- [x] Concept: `Chunking` | Parent: `Retrieval`
- [ ] Concept: `Graph Databases` | Parent: `Retrieval`
- [ ] Concept: `Orphan Idea`
"""


@pytest.fixture
def tree(tmp_path, monkeypatch):
    tp = tmp_path / "tree.json"
    qp = tmp_path / "RESEARCH_QUEUE.md"
    tp.write_text(json.dumps(NODES))
    qp.write_text(QUEUE)
    monkeypatch.setattr(ct, "TREE_PATH", tp)
    monkeypatch.setattr(ct, "QUEUE_PATH", qp)
    return ct.ConceptTree.load()


# ------------------------------------------------------------- frontier ---

def test_a_child_with_no_node_is_frontier(tree):
    """The tree names it, so it is known — but nothing researched it."""
    assert tree.status("Vector Stores") == ct.FRONTIER
    assert tree.frontier["Vector Stores"]["source"] == "child-reference"
    assert tree.frontier["Vector Stores"]["parentConcept"] == "Retrieval"


def test_an_unchecked_queue_item_is_frontier(tree):
    assert tree.status("Graph Databases") == ct.FRONTIER
    assert tree.frontier["Graph Databases"]["source"] == "research-queue"


def test_a_checked_queue_item_is_not_frontier(tree):
    """Chunking is both queued-done and a real node; it must not be greyed."""
    assert tree.status("Chunking") == ct.RESEARCHED
    assert "Chunking" not in tree.frontier


def test_researched_nodes_are_not_frontier(tree):
    assert tree.status("Retrieval") == ct.RESEARCHED
    assert tree.status("nonexistent concept") is None


# ------------------------------------------------------------- traversal --

def test_children_include_frontier_so_they_render_under_their_parent(tree):
    kids = tree.children("Retrieval")
    assert "Chunking" in kids            # researched child
    assert "Vector Stores" in kids       # frontier via child-reference
    assert "Graph Databases" in kids     # frontier adopted from the queue


def test_walk_yields_status_per_node(tree):
    seen = {c: s for c, _lvl, s in tree.walk()}
    assert seen["Retrieval"] == ct.RESEARCHED
    assert seen["Vector Stores"] == ct.FRONTIER


def test_walk_depth_limits(tree):
    assert {c for c, _l, _s in tree.walk(depth=1)} == {"Retrieval", "Serving"}


def test_walk_survives_a_cycle(tree):
    """Links are by NAME, so a tree edit can make one; traversal must not hang."""
    tree.by_concept["Chunking"]["childConcepts"] = ["Retrieval"]
    out = list(tree.walk())
    assert len(out) == len({c for c, _l, _s in out})


def test_orphan_frontier_is_surfaced_not_dropped(tree):
    """A frontier concept with no known parent renders nowhere in the tree --
    it would be invisible rather than absent."""
    assert "Orphan Idea" in tree.orphan_frontier()


# ---------------------------------------------------------------- detail --

def test_detail_of_a_researched_node_carries_its_skill_and_provenance(tree):
    d = ct.detail(tree, "Retrieval")
    assert d["status"] == ct.RESEARCHED
    assert d["skillId"] == "ai-rag-retrieval"
    assert d["researchedAt"] == "2026-08-01" and d["sourcesCount"] == 4
    assert d["children"] == tree.children("Retrieval")


def test_detail_of_a_frontier_node_explains_why_it_is_greyed(tree):
    d = ct.detail(tree, "Vector Stores")
    assert d["status"] == ct.FRONTIER
    assert d["parent"] == "Retrieval"
    assert "never researched" in d["whyGreyed"]
    assert "skillId" not in d          # nothing to claim about an unresearched node


def test_detail_of_an_unknown_concept_says_unknown(tree):
    assert ct.detail(tree, "no such thing")["status"] == "unknown"


def test_related_gives_the_neighbourhood(tree):
    rel = tree.related("Chunking")
    assert rel["parent"] == "Retrieval"
    assert "Vector Stores" in rel["siblings"]
    assert "Chunking" not in rel["siblings"]


def test_search_matches_both_researched_and_frontier(tree):
    assert tree.search("stores") == ["Vector Stores"]
    assert set(tree.search("r")) >= {"Retrieval", "Graph Databases"}
    assert tree.search("") == []


# -------------------------------------------------------------- validate --

def test_validate_is_clean_on_a_consistent_tree(tree, monkeypatch):
    monkeypatch.setattr(ct, "skill_paths", lambda sid: ["/fake"] if sid else [])
    assert tree.validate() == []


def test_validate_catches_a_parent_that_does_not_exist(tree, monkeypatch):
    monkeypatch.setattr(ct, "skill_paths", lambda sid: ["/fake"])
    tree.by_concept["Serving"]["parentConcept"] = "Ghost"
    assert any("parent 'Ghost' has no node" in p for p in tree.validate())


def test_validate_catches_a_non_reciprocal_link(tree, monkeypatch):
    """Parent says nothing about the child -- a traversal loses the subtree."""
    monkeypatch.setattr(ct, "skill_paths", lambda sid: ["/fake"])
    tree.by_concept["Retrieval"]["childConcepts"] = ["Vector Stores"]
    assert any("does not list it as a child" in p for p in tree.validate())


def test_validate_catches_a_skill_that_is_not_installed(tree, monkeypatch):
    """'Click the node, read the skill' silently yields nothing otherwise."""
    monkeypatch.setattr(ct, "skill_paths", lambda sid: [])
    assert any("is not installed" in p for p in tree.validate())


# ----------------------------------------------------------------- queue --

def test_queue_concept_appends_an_unchecked_item(tree, tmp_path, monkeypatch):
    qp = ct.QUEUE_PATH
    assert ct.queue_concept("New Idea", "Retrieval", qp) is True
    text = qp.read_text()
    assert "- [ ] Concept: `New Idea` | Parent: `Retrieval`" in text
    # the existing human-edited content survives -- it appends, never rewrites
    assert "Graph Databases" in text and text.startswith("# Concept Research Queue")


def test_queue_concept_is_idempotent(tree):
    assert ct.queue_concept("Graph Databases", "Retrieval", ct.QUEUE_PATH) is False


def test_a_queued_concept_becomes_frontier_on_reload(tree):
    ct.queue_concept("Later Thing", "Serving", ct.QUEUE_PATH)
    reloaded = ct.ConceptTree.load(ct.TREE_PATH, ct.QUEUE_PATH)
    assert reloaded.status("Later Thing") == ct.FRONTIER
    assert "Later Thing" in reloaded.children("Serving")


# ---------------------------------------------------------------- render --

def test_ascii_render_marks_frontier_so_it_survives_plain_text(tree):
    """MCP output and logs have no colour; the distinction has to be textual."""
    out = "\n".join(ct.render_ascii(tree))
    assert "▪ Retrieval" in out
    assert "Vector Stores   (frontier — not researched)" in out


def test_missing_tree_file_yields_an_empty_tree_not_a_crash(tmp_path, monkeypatch):
    monkeypatch.setattr(ct, "TREE_PATH", tmp_path / "absent.json")
    monkeypatch.setattr(ct, "QUEUE_PATH", tmp_path / "absent.md")
    t = ct.ConceptTree.load()
    assert t.roots() == [] and t.frontier == {}


# ------------------------------------------------------------ Concepts tab --

def _stub_tabs(monkeypatch):
    from hub_manager import (docsets as dm, health, queue_model,
                             remotes as rm, usage as um)
    monkeypatch.setattr(health, "run_all", lambda disabled=None: [])
    monkeypatch.setattr(health, "check_mcp",
                        lambda: health.HealthCheck("MCP", None, "stub"))
    monkeypatch.setattr(queue_model, "serve_alive", lambda timeout=1.0: False)
    monkeypatch.setattr(um, "scan", lambda days=7: um.UsageReport(days=days,
                                                                 files_scanned=0))
    monkeypatch.setattr(rm, "all_hosts", lambda: [])
    monkeypatch.setattr(rm, "all_hosts_readiness", lambda: [])
    monkeypatch.setattr(rm, "all_repo_status", lambda: [])
    monkeypatch.setattr(dm, "list_docsets", lambda: (True, "[]"))


def _labels(node):
    out = []
    def walk(n):
        for c in n.children:
            out.append(str(c.label))
            walk(c)
    walk(node)
    return out


def test_tab_renders_the_tree_and_dims_frontier_nodes(tree, monkeypatch, hub_tmp):
    """The greying is the point of the feature: a frontier node must be
    visually distinguishable, not merely present."""
    import asyncio

    from textual.widgets import TabbedContent, Tree as TreeWidget

    from hub_manager.app import HubManagerApp

    _stub_tabs(monkeypatch)

    async def drive():
        app = HubManagerApp()
        async with app.run_test(size=(120, 44)) as pilot:
            await pilot.pause()
            app.query_one(TabbedContent).active = "tab-concepts"
            await pilot.pause()
            widget = app.query_one("#concept-tree", TreeWidget)
            styles = {}
            def walk(n):
                for c in n.children:
                    lbl = c.label
                    styles[str(lbl)] = str(getattr(lbl, "spans", "")) + str(
                        lbl.style if hasattr(lbl, "style") else "")
                    walk(c)
            walk(widget.root)
            return styles

    styles = asyncio.run(drive())
    assert any("Retrieval" in k for k in styles)
    frontier = next(k for k in styles if k.startswith("Vector Stores"))
    assert "frontier" in frontier                 # labelled in text too
    assert "dim" in styles[frontier]              # ...and visually dimmed
    assert "dim" not in styles["Retrieval"]


def test_clicking_a_node_shows_its_skill_and_neighbours(tree, monkeypatch, hub_tmp):
    import asyncio

    from textual.widgets import RichLog, TabbedContent, Tree as TreeWidget

    from hub_manager.app import HubManagerApp

    _stub_tabs(monkeypatch)

    async def drive():
        app = HubManagerApp()
        async with app.run_test(size=(120, 44)) as pilot:
            await pilot.pause()
            app.query_one(TabbedContent).active = "tab-concepts"
            await pilot.pause()
            widget = app.query_one("#concept-tree", TreeWidget)
            target = next(n for n in widget.root.children
                          if str(n.label).startswith("Retrieval"))
            widget.select_node(target)
            await pilot.pause()
            return "\n".join(str(line.text) for line in
                             app.query_one("#concept-detail", RichLog).lines)

    detail = asyncio.run(drive())
    assert "Retrieval" in detail
    assert "ai-rag-retrieval" in detail            # the skill
    assert "2026-08-01" in detail                  # the research provenance
    assert "Vector Stores" in detail               # related/children


# ------------------------------------------------------- research launch --

def test_research_modes_are_distinct_not_interchangeable():
    """Breadth and depth are different jobs; the prompts must say so."""
    fam = ct.research_prompt("Vector Stores", "family", "Retrieval")
    deep = ct.research_prompt("Vector Stores", "deep", "Retrieval")
    dr = ct.research_prompt("Vector Stores", "dr", "Retrieval")
    assert "concept-family-explorer" in fam and "MISSING" in fam
    assert "Do NOT go broad" in deep and "saturate" in deep
    assert "/dr" in dr
    assert len({fam, deep, dr}) == 3


def test_every_research_prompt_writes_back_into_the_tree():
    """Research that does not land in tree.json leaves the node greyed out
    forever — the work happens and the map never learns."""
    for mode in ct.RESEARCH_MODES:
        p = ct.research_prompt("X", mode, "Parent")
        assert "concept-tree/tree.json" in p
        assert "childConcepts" in p          # new leads become frontier points


def test_research_prompt_carries_the_parent_for_placement():
    assert "under `Retrieval`" in ct.research_prompt("X", "dr", "Retrieval")
    assert "under" not in ct.research_prompt("X", "dr", None).split("Use the")[1][:40]


def test_research_argv_does_not_bypass_all_permissions(monkeypatch):
    """acceptEdits lets the job write its findings; a blanket bypass would hand
    an unattended agent unrestricted shell access."""
    monkeypatch.setattr(ct, "claude_binary", lambda: "/fake/claude")
    argv = ct.research_argv("X", "dr", None)
    assert argv[:2] == ["/fake/claude", "-p"]
    assert "--permission-mode" in argv and "acceptEdits" in argv
    assert not any("dangerously" in a for a in argv)


def test_research_argv_is_none_when_claude_is_absent(monkeypatch):
    """The tab must say so rather than spawning a broken job."""
    monkeypatch.setattr(ct, "claude_binary", lambda: None)
    assert ct.research_argv("X") is None


def test_claude_binary_prefers_a_real_file_over_a_shell_alias(monkeypatch, tmp_path):
    """`claude` is commonly an ALIAS, which does not exist in a subprocess."""
    fake = tmp_path / "claude"
    fake.write_text("#!/bin/sh\n")
    fake.chmod(0o755)
    monkeypatch.setattr(ct, "_CLAUDE_CANDIDATES", (fake,))
    assert ct.claude_binary() == str(fake)


# --------------------------------------------------- in-progress research --

@pytest.fixture
def state_path(tree, tmp_path, monkeypatch):
    sp = tmp_path / "research_state.json"
    monkeypatch.setattr(ct, "RESEARCH_STATE_PATH", sp)
    return sp


def _reload():
    return ct.ConceptTree.load(ct.TREE_PATH, ct.QUEUE_PATH, ct.RESEARCH_STATE_PATH)


def test_marking_a_concept_in_progress_round_trips(state_path):
    import os
    ct.mark_in_progress("Retrieval", "deep", os.getpid())
    t = _reload()
    assert t.status("Retrieval") == ct.IN_PROGRESS
    assert t.in_progress["Retrieval"]["mode"] == "deep"
    assert ct.clear_in_progress("Retrieval") is True
    assert _reload().status("Retrieval") == ct.RESEARCHED


def test_in_progress_outranks_both_other_statuses(state_path):
    """An agent asking what to pick up next must not be handed something
    already in flight, whether it is settled or frontier."""
    import os
    ct.mark_in_progress("Retrieval", "dr", os.getpid())          # researched
    ct.mark_in_progress("Vector Stores", "dr", os.getpid())      # frontier
    t = _reload()
    assert t.status("Retrieval") == ct.IN_PROGRESS
    assert t.status("Vector Stores") == ct.IN_PROGRESS


def test_a_dead_run_self_heals_on_the_next_read(state_path):
    """A killed agent must not pin a node as 'researching' forever."""
    ct._write_research_state(
        {"Retrieval": {"mode": "dr", "pid": 999999, "started": 0}})
    assert ct.load_research_state() == {}          # pruned
    assert _reload().status("Retrieval") == ct.RESEARCHED
    # and the prune is persisted, not just filtered in memory
    assert json.loads(state_path.read_text()) == {}


def test_state_survives_a_corrupt_file_instead_of_crashing(state_path):
    state_path.write_text("{not json")
    assert ct.load_research_state() == {}


def test_clearing_something_not_running_is_a_no_op(state_path):
    assert ct.clear_in_progress("Retrieval") is False


def test_detail_reports_the_running_mode(state_path):
    import os
    ct.mark_in_progress("Vector Stores", "family", os.getpid())
    d = ct.detail(_reload(), "Vector Stores")
    assert d["status"] == ct.IN_PROGRESS
    assert d["research"]["mode"] == "family"
    assert d["research"]["pid"] == os.getpid()


def test_ascii_render_marks_in_progress_distinctly(state_path):
    import os
    ct.mark_in_progress("Retrieval", "dr", os.getpid())
    out = "\n".join(ct.render_ascii(_reload()))
    assert "▸ Retrieval   (researching now)" in out


def test_state_is_written_atomically(state_path, monkeypatch):
    """A reader must never see a half-written file."""
    seen = {}
    real = ct.os.replace
    def spy(src, dst):
        seen["replaced"] = True
        return real(src, dst)
    monkeypatch.setattr(ct.os, "replace", spy)
    ct.mark_in_progress("Retrieval", "dr", 1)
    assert seen.get("replaced") is True
    assert not state_path.with_suffix(".json.tmp").exists()


# ------------------------------------------------------------- slugs -----

def test_slugify_and_ensure_slugs_are_stable_and_unique(tree):
    assert ct.slugify("llms.txt specification v2") == "llms-txt-specification-v2"
    assert ct.slugify("  Weird!!  ") == "weird"
    nodes = [dict(n) for n in tree.nodes] + [{"concept": "retrieval", "childConcepts": []}]
    n = ct.ensure_slugs(nodes)
    assert n == 2 * len(nodes)                     # slug + aliases on every node
    slugs = [x["slug"] for x in nodes]
    assert slugs[0] == "retrieval" and slugs[-1] == "retrieval-2"   # collision suffixed
    assert all(x["aliases"] == [] for x in nodes)
    assert ct.ensure_slugs(nodes) == 0             # idempotent; slugs never drift
    nodes[0]["concept"] = "Retrieval renamed"
    assert ct.ensure_slugs(nodes) == 0 and nodes[0]["slug"] == "retrieval"


def test_validate_catches_a_shared_slug(tree):
    for n in tree.nodes:
        n["slug"] = "same"
    t = ct.ConceptTree(tree.nodes)
    assert any("slug 'same' is shared" in p for p in t.validate())
    assert t.by_slug["same"]["concept"]


def test_slugs_cli_writes_tree(tree, monkeypatch, capsys):
    assert ct.main(["slugs"]) == 0
    assert "added across" in capsys.readouterr().out
    saved = json.loads(ct.TREE_PATH.read_text())
    assert all(n.get("slug") and isinstance(n.get("aliases"), list) for n in saved)
    assert ct.main(["slugs"]) == 0
    assert capsys.readouterr().out.startswith("0 node")


# --------------------------------------------------------------------------- #
# restructuring: reparent / rename / add_domain / apply_layout / relink_skills
# --------------------------------------------------------------------------- #

def _fresh():
    return json.loads(json.dumps(NODES))


def test_reparent_keeps_both_link_directions():
    nodes = _fresh()
    assert ct.reparent(nodes, "Serving", "Retrieval")
    t = ct.ConceptTree(nodes)
    assert t.by_concept["Serving"]["parentConcept"] == "Retrieval"
    assert "Serving" in t.by_concept["Retrieval"]["childConcepts"]
    assert t.validate() == [] or all("skillId" in p for p in t.validate())
    assert t.roots() == ["Retrieval"]


def test_reparent_moves_between_parents_and_keeps_frontier():
    nodes = _fresh()
    ct.reparent(nodes, "Serving", "Retrieval")
    ct.reparent(nodes, "Serving", "Chunking")
    by = {n["concept"]: n for n in nodes}
    assert "Serving" not in by["Retrieval"]["childConcepts"]
    assert by["Retrieval"]["childConcepts"] == ["Chunking", "Vector Stores"]  # frontier ref kept
    assert by["Chunking"]["childConcepts"] == ["Serving"]


def test_reparent_refuses_cycles_and_unknown_names():
    nodes = _fresh()
    with pytest.raises(ct.TreeEditError):
        ct.reparent(nodes, "Retrieval", "Chunking")      # Chunking is inside Retrieval
    with pytest.raises(ct.TreeEditError):
        ct.reparent(nodes, "Serving", "Nope")
    with pytest.raises(ct.TreeEditError):
        ct.reparent(nodes, "Vector Stores", "Serving")   # frontier name, no node


def test_reparent_is_noop_when_already_there():
    nodes = _fresh()
    assert not ct.reparent(nodes, "Chunking", "Retrieval")


def test_rename_keeps_slug_and_follows_references():
    nodes = _fresh()
    ct.ensure_slugs(nodes)
    assert ct.rename(nodes, "Retrieval", "Retrieval Systems")
    by = {n["concept"]: n for n in nodes}
    assert by["Retrieval Systems"]["slug"] == "retrieval"
    assert "Retrieval" in by["Retrieval Systems"]["aliases"]
    assert by["Chunking"]["parentConcept"] == "Retrieval Systems"
    assert not ct.rename(nodes, "Retrieval", "Retrieval Systems")  # idempotent


def test_apply_layout_is_idempotent_and_marks_domains():
    nodes = _fresh()
    layout = {"domains": [{"concept": "AI", "parent": None, "summary": "s"}],
              "parents": {"Retrieval": "AI", "Serving": "AI"}}
    log = ct.apply_layout(nodes, layout, date="2026-09-25")
    assert log and ct.apply_layout(nodes, layout, date="2026-09-25") == []
    t = ct.ConceptTree(nodes)
    assert t.roots() == ["AI"]
    ai = t.by_concept["AI"]
    assert ai["kind"] == "domain" and ai["sourcesCount"] == 0 and ai["conceptsCount"] == 2
    assert [p for p in t.validate() if "skillId" not in p] == []
    assert "Vector Stores" in t.frontier                 # frontier survives regroup


def test_apply_layout_rejects_typos_before_editing():
    nodes = _fresh()
    before = json.dumps(nodes)
    with pytest.raises(ct.TreeEditError):
        ct.apply_layout(nodes, {"parents": {"Serving": "Retreival"}})
    assert json.dumps(nodes) == before


def test_relink_skills_repoints_folded_skill_or_marks_wanted(monkeypatch):
    nodes = [{"concept": "A", "skillId": "folded", "parentConcept": None, "childConcepts": []},
             {"concept": "B", "skillId": "gone", "parentConcept": None, "childConcepts": []}]
    monkeypatch.setattr(ct, "skill_paths",
                        lambda sid: ["x"] if sid == "hub/references/folded" else [])
    idx = {"folded": ["hub/references/folded"]}
    log = ct.relink_skills(nodes, idx)
    assert len(log) == 2
    assert nodes[0]["skillId"] == "hub/references/folded"
    assert nodes[1]["skillId"] is None and nodes[1]["skillIdWanted"] == "gone"


def test_rename_merges_a_frontier_spelling_of_the_same_concept():
    nodes = _fresh()
    nodes[0]["childConcepts"] = ["Chunking &amp; Splitting", "Chunking & Splitting",
                                 "Vector Stores"]
    nodes[1]["concept"] = "Chunking &amp; Splitting"
    assert ct.rename(nodes, "Chunking &amp; Splitting", "Chunking & Splitting")
    t = ct.ConceptTree(nodes)
    assert t.by_concept["Retrieval"]["childConcepts"] == ["Chunking & Splitting", "Vector Stores"]
    assert "Chunking & Splitting" not in t.frontier


def test_unlist_drops_cross_listing_but_never_frontier_or_real_child():
    nodes = _fresh()
    nodes[2]["childConcepts"] = ["Chunking", "Some Frontier"]   # Serving cross-lists Chunking
    log = ct.apply_layout(nodes, {"unlist": {"Serving": ["Chunking", "Some Frontier"],
                                             "Retrieval": ["Chunking"]}})
    by = {n["concept"]: n for n in nodes}
    assert by["Serving"]["childConcepts"] == ["Some Frontier"]
    assert "Chunking" in by["Retrieval"]["childConcepts"]          # real parent kept
    assert len(log) == 1


def test_relink_skills_restores_a_wanted_skill_once_installed(monkeypatch):
    nodes = [{"concept": "A", "skillId": None, "skillIdWanted": "now-here",
              "parentConcept": None, "childConcepts": []}]
    monkeypatch.setattr(ct, "skill_paths", lambda sid: ["x"] if sid == "now-here" else [])
    assert len(ct.relink_skills(nodes, {})) == 1
    assert nodes[0]["skillId"] == "now-here" and "skillIdWanted" not in nodes[0]
