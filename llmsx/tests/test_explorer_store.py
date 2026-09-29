# llmsx/tests/test_explorer_store.py — every write path of `llmsx explorer`, no terminal.
# ruff: noqa: E501
from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import INJECTION, TESTS_DIR, _git, make_repo

from llmsx import explorer_store as es

# --------------------------------------------------------------------------- #
# tree

def test_raw_tree_round_trips_and_edit_touches_only_named_fields(tmp_path, home):
    repo = make_repo(tmp_path, git=False)
    before = es.load_raw_tree(repo / es.TREE_REL)
    snapshot = json.loads(json.dumps(before))
    es.edit_node(before, "Kid Concept", summary="new summary", aliases=["kiddo", " k2 ", ""], add_child="Brand New Child")
    es.save_raw_tree(before, repo / es.TREE_REL)
    after = es.load_raw_tree(repo / es.TREE_REL)
    assert after[0] == snapshot[0], "the untouched node must be byte-identical (extraKey kept)"
    kid = after[1]
    assert kid["summary"] == "new summary"
    assert kid["aliases"] == ["kiddo", "k2"]
    assert kid["childConcepts"] == ["Brand New Child"]
    for key in ("skillId", "researchedAt", "sourcesCount", "conceptsCount", "slug", "parentConcept"):
        assert kid[key] == snapshot[1][key]
    text = (repo / es.TREE_REL).read_text()
    assert text.endswith("\n") and text.startswith("[\n  {\n")
    assert not list((repo / "concept-tree").glob(".tree.json.*")), "no temp file left behind"


def test_outline_roots_frontier_parents_and_self_parent_nodes(tmp_path, home):
    repo = make_repo(tmp_path, git=False)
    o = es.build_outline(es.load_raw_tree(repo / es.TREE_REL))
    assert o.roots == ["Root Domain"]
    assert o.children["Root Domain"] == ["Kid Concept", "Ghost Concept"]
    assert o.is_frontier("Ghost Concept") and not o.is_frontier("Kid Concept")
    assert o.parent_of("Ghost Concept") == "Root Domain"
    # a node naming itself as parent, and a pair naming each other, still render as roots
    weird = [{"concept": "Self", "slug": "self", "parentConcept": "Self", "childConcepts": ["Self"]},
             {"concept": "A", "slug": "a", "parentConcept": "B", "childConcepts": ["B"]},
             {"concept": "B", "slug": "b", "parentConcept": "A", "childConcepts": ["A"]}]
    o2 = es.build_outline(es.validate_raw_tree(weird))
    assert o2.roots == ["Self", "A"], "a mutual cycle is promoted once, B renders under A"


def test_validate_rejects_wrong_shapes_duplicates_and_bad_slugs(tmp_path):
    with pytest.raises(ValueError):
        es.validate_raw_tree({"nodes": {}})
    with pytest.raises(ValueError):
        es.validate_raw_tree([{"concept": "x"}])
    with pytest.raises(ValueError, match="duplicate concept"):
        es.validate_raw_tree([{"concept": "Dup", "slug": "a", "parentConcept": None, "childConcepts": []},
                              {"concept": "Dup", "slug": "b", "parentConcept": None, "childConcepts": []}])
    with pytest.raises(ValueError, match="duplicate slug"):
        es.validate_raw_tree([{"concept": "A", "slug": "a", "parentConcept": None, "childConcepts": []},
                              {"concept": "B", "slug": "a", "parentConcept": None, "childConcepts": []}])
    with pytest.raises(ValueError, match="is not a slug"):
        es.validate_raw_tree([{"concept": "A", "slug": "../../etc", "parentConcept": None, "childConcepts": []}])
    with pytest.raises(ValueError, match="list of strings"):
        es.validate_raw_tree([{"concept": "A", "slug": "a", "parentConcept": None, "childConcepts": [1]}])
    with pytest.raises(ValueError, match="skillId"):
        es.validate_raw_tree([{"concept": "A", "slug": "a", "parentConcept": None, "childConcepts": [], "skillId": 5}])
    with pytest.raises(ValueError, match="aliases"):
        es.validate_raw_tree([{"concept": "A", "slug": "a", "parentConcept": None, "childConcepts": [], "aliases": [1]}])
    assert es.skill_target(tmp_path, 5) is None
    with pytest.raises(FileNotFoundError):
        es.load_raw_tree(tmp_path / "nope.json")


# --------------------------------------------------------------------------- #
# marks, notes, queue

def test_marks_persist_next_to_the_tree(tmp_path, home):
    repo = make_repo(tmp_path, git=False)
    assert es.load_marks(repo) == {}
    marks = es.set_mark(repo, "kid-concept", "needs-review")
    assert marks["kid-concept"]["state"] == "needs-review"
    assert json.loads((repo / es.MARKS_REL).read_text())["kid-concept"]["state"] == "needs-review"
    es.set_mark(repo, "kid-concept", "further-research", note="dig deeper")
    assert es.load_marks(repo)["kid-concept"]["note"] == "dig deeper"
    assert es.set_mark(repo, "kid-concept", None) == {}
    with pytest.raises(ValueError):
        es.set_mark(repo, "kid-concept", "bogus")
    with pytest.raises(ValueError, match="not a slug"):
        es.set_mark(repo, "../x", "needs-review")
    (repo / es.MARKS_REL).write_text("[1, 2]")
    assert es.load_marks(repo) == {}, "a marks file of the wrong shape is treated as empty"


def test_notes_live_under_llmsx_home_never_the_repo_and_refuse_traversal(tmp_path, home):
    repo = make_repo(tmp_path, git=False)
    p = es.write_note("kid-concept", "my private note\n")
    assert p == home / "notes" / "kid-concept.md"
    assert es.read_note("kid-concept") == "my private note\n"
    assert not any("kid-concept.md" in str(f) for f in repo.rglob("*"))
    es.write_note("kid-concept", "   ")
    assert not p.exists(), "an emptied note is removed"
    victim = tmp_path / "victim.md"
    victim.write_text("keep me")
    with pytest.raises(ValueError, match="not a slug"):
        es.write_note("../../victim", "")
    with pytest.raises(ValueError):
        es.note_path("../../../victim")
    assert victim.read_text() == "keep me"
    assert es.read_note("../../victim") == ""


def test_queue_row_is_the_exact_regex_format_and_never_rewrites(tmp_path, home):
    repo = make_repo(tmp_path, git=False)
    assert es.queue_concept(repo, "Already Queued") is False
    assert es.queue_concept(repo, "Ghost Concept", "Root Domain", "deep") is True
    text = (repo / es.QUEUE_REL).read_text()
    assert text.startswith("# Queue\n\n- [ ] Concept: `Already Queued` | Parent: `Root Domain`\n")
    assert text.endswith("- [ ] Concept: `Ghost Concept` | Parent: `Root Domain` | Mode: `deep`\n")
    rows = es.load_queue(repo)
    assert rows[-1] == {"concept": "Ghost Concept", "parent": "Root Domain", "mode": "deep", "done": False}
    assert es.queue_concept(repo, "Plain") is True
    assert (repo / es.QUEUE_REL).read_text().endswith("- [ ] Concept: `Plain`\n")
    with pytest.raises(ValueError):
        es.queue_concept(repo, "bad`tick")
    with pytest.raises(ValueError):
        es.queue_concept(repo, "Fine", None, "dr`")

def test_highlights_crud_and_rendering(home):
    assert es.load_highlights() == []
    hl = es.add_highlight("Kid Concept", "Crucial line about concepts", "important note")
    assert hl["concept"] == "Kid Concept"
    assert hl["text"] == "Crucial line about concepts"
    assert hl["note"] == "important note"
    assert es.highlights_path().is_file()

    loaded = es.load_highlights()
    assert len(loaded) == 1
    assert loaded[0]["id"] == hl["id"]

    for_kid = es.highlights_for_concept("Kid Concept")
    assert len(for_kid) == 1
    assert es.highlights_for_concept("other") == []

    md = es.highlights_markdown(loaded, "Kid Concept")
    assert "Crucial line about concepts" in md
    assert "Annotation: important note" in md

    with pytest.raises(ValueError, match="cannot be empty"):
        es.add_highlight("Kid", "   ")

    assert es.remove_highlight(hl["id"]) is True
    assert es.remove_highlight("no-such-id") is False
    assert es.load_highlights() == []

    es.add_highlight("Kid", "Snippet 1")
    es.add_highlight("Kid", "Snippet 2")
    assert len(es.load_highlights()) == 2
    es.clear_highlights()
    assert es.load_highlights() == []

def test_research_prompt_only_takes_safe_names_and_never_summaries(tmp_path, home):
    p = es.research_prompt("Kid Concept", "dr", "Root Domain")
    assert "`Kid Concept`" in p and "`Root Domain`" in p and INJECTION not in p
    assert "--depth quick" in p and "--budget-minutes 8" in p
    assert "Scope guardrails:" in p and "npm run build" in p
    for mode in ("family", "deep", "crawl", "full"):
        assert "Kid Concept" in es.research_prompt("Kid Concept", mode)
    with pytest.raises(ValueError):
        es.research_prompt("x`script`", "dr")
    assert "`Train->infer weight resync (NCCL <=8)`" in es.research_prompt("Train->infer weight resync (NCCL <=8)", "dr")
    with pytest.raises(ValueError):
        es.research_prompt("Kid", "dr", "bad`parent")
    with pytest.raises(ValueError):
        es.research_prompt("Kid", "nope")
    assert not es.safe_name(INJECTION + "\n`rm -rf`")
    assert not es.safe_name("Trailing newline\n") and not es.SLUG_RE.match("slug\n")
    assert not es.REMOTE_NAME_RE.match("origin\n") and not es.TOKEN_RE.match("ghp_abcdefgh\n")
    assert es.safe_name("Rust's Ownership (v2), &/+ Borrowing")
    assert es.safe_name("Diátaxis Tutorial Quadrant") and es.safe_name("Agentic RL — Reinforcement Learning: LLM Agents")
    assert es.safe_name("x" * es.SAFE_NAME_MAX) and not es.safe_name("x" * (es.SAFE_NAME_MAX + 1))
    assert not es.safe_name("-flag") and not es.safe_name(" leading space") and not es.safe_name("tab\there")
    assert es.unsafe_name_reason("Kid") is None
    assert "longer than" in es.unsafe_name_reason("k" * 500)
    assert "character" in es.unsafe_name_reason("a`b")


def test_research_argv_is_none_without_claude(monkeypatch):
    monkeypatch.setattr(es.shutil, "which", lambda _name: None)
    assert es.research_argv("Kid Concept", "dr") is None


def test_snapshot_restored_when_a_job_leaves_a_broken_tree(tmp_path, home):
    repo = make_repo(tmp_path, git=False)
    snap = es.snapshot_tree(repo)
    (repo / es.TREE_REL).write_text("{not json")
    ok, msg = es.verify_tree_after_run(repo, snap)
    assert not ok and "restored" in msg
    assert (repo / es.TREE_REL).read_text() == snap
    (repo / es.TREE_REL).write_text(json.dumps(["not", "a", "dict"]))
    ok, msg = es.verify_tree_after_run(repo, snap)
    assert not ok and "invalid tree" in msg and (repo / es.TREE_REL).read_text() == snap
    (repo / es.TREE_REL).write_text(json.dumps([{"concept": "x", "slug": "x", "parentConcept": None, "childConcepts": []}]))
    ok, msg = es.verify_tree_after_run(repo, snap)
    assert ok and "+1 added, -2 removed" in msg
    ok, msg = es.verify_tree_after_run(repo, "{}")
    assert not ok and "snapshot" in msg


# --------------------------------------------------------------------------- #
# rendering is display-only

def test_rendered_markdown_keeps_injection_text_literal(tmp_path, home):
    repo = make_repo(tmp_path, git=False)
    md = es.facts_markdown(es.load_pack(repo, "kid-concept"), "Kid Concept")
    assert INJECTION in md and "[source](https://ex.dev/a#1)" in md
    assert es.facts_markdown(None, "Nope").count("not available") == 1
    assert "no facets" in es.facts_markdown({"facets": ["a", "b"]}, "X")
    o = es.build_outline(es.load_raw_tree(repo / es.TREE_REL))
    node = dict(o.nodes["Kid Concept"], skillId="<b>evil</b>")
    ov = es.overview_markdown(node, "Kid Concept", o, {"kid-concept": {"state": "needs-review", "at": "2026-01-03"}}, "note <b>x</b>", False)
    assert "needs-review" in ov and "note &lt;b>x&lt;/b>" in ov and INJECTION in ov
    assert "<b>evil" not in ov and "&lt;b>evil" in ov
    fr = es.overview_markdown(None, "Ghost Concept", o, {}, "", True)
    assert "frontier" in fr and "queued" in fr
    assert es.describe_file(repo / es.SKILLS_REL / "kidskill" / "SKILL.md") == "Kid skill does kid things."
    assert es.describe_file(repo / es.SKILLS_REL / "kidskill" / "references" / "depth.md").startswith("First paragraph")


def test_describe_file_edge_cases(tmp_path, home):
    assert es.describe_file(tmp_path / "missing.md") == ""
    assert es.describe_file(tmp_path) == ""
    j = tmp_path / "x.json"
    j.write_text('{"slug": "x"}')
    assert es.describe_file(j) == ""
    j.write_text("{not json")
    assert es.describe_file(j) == ""
    lit = tmp_path / "lit.md"
    lit.write_text("---\ndescription: |-\n  literal block\n  scalar\n---\n# H\n")
    assert es.describe_file(lit) == "literal block scalar"


def test_available_slugs_and_llms_dir_see_the_hub_directory(tmp_path, home, monkeypatch):
    repo = make_repo(tmp_path, git=False)
    hub = tmp_path / "llms-concepts"
    (hub / "kid-concept.llms").mkdir(parents=True)
    (hub / "other-slug").mkdir()
    (hub / "kid-concept.llms" / "llms.txt").write_text("# Kid\n")
    monkeypatch.setenv("LLMSX_CONCEPTS_PATH", str(hub))
    assert es.available_slugs(repo) == {"kid-concept", "other-slug"}
    assert es.llms_dir("kid-concept") == (hub / "kid-concept.llms").resolve()
    assert es.llms_dir("other-slug") == (hub / "other-slug").resolve()
    assert es.llms_dir("nope") is None
    ldir = es.llms_dir("kid-concept")
    assert es.llms_file(ldir, "llms.txt") is not None and es.llms_file(ldir, "llms-full.txt") is None
    outside = tmp_path / "secret.txt"
    outside.write_text("token")
    (ldir / "llms-full.txt").symlink_to(outside)
    assert es.llms_file(ldir, "llms-full.txt") is None, "a symlink out of the .llms dir is never served"


def test_symlinked_skill_files_outside_the_skills_dir_are_refused(tmp_path, home):
    repo = make_repo(tmp_path, git=False)
    secret = tmp_path / "secret.md"
    secret.write_text("ghp_leak")
    refs = repo / es.SKILLS_REL / "kidskill" / "references"
    (refs / "evil.md").symlink_to(secret)
    assert [p.name for p in es.reference_files(repo / es.SKILLS_REL / "kidskill")] == ["depth.md"]
    evil = repo / es.SKILLS_REL / "evilskill"
    evil.mkdir()
    (evil / "SKILL.md").symlink_to(secret)
    assert es.skill_target(repo, "evilskill") is None


def test_pack_and_skill_paths_stay_inside_the_repo(tmp_path, home):
    repo = make_repo(tmp_path, git=False)
    assert es.pack_path(repo, "kid-concept") is not None
    assert es.pack_path(repo, "../tree") is None
    assert es.skill_dir(repo, "kidskill") is not None
    assert es.skill_target(repo, "kidskill/references/depth.md") == (
        repo / es.SKILLS_REL / "kidskill", repo / es.SKILLS_REL / "kidskill" / "references" / "depth.md")
    for bad in ("../kidskill", "C:\\Users\\x", ".hidden", "a/b", "", "kidskill/references/../SKILL.md",
                "kidskill/references/nope.md", "kidskill/SKILL.md"):
        assert es.skill_dir(repo, bad) is None, bad
    assert es.validate_raw_tree([{"concept": "A", "slug": "indexing--databases", "parentConcept": None, "childConcepts": []}])
    assert es.available_slugs(repo) == {"kid-concept"}
    assert es.llms_dir("../x") is None


# --------------------------------------------------------------------------- #
# bundle

def test_bundle_export_pins_markdown_shape_and_json_round_trips(tmp_path, home):
    repo = make_repo(tmp_path, git=False)
    skill = repo / es.SKILLS_REL / "kidskill" / "SKILL.md"
    ref = repo / es.SKILLS_REL / "kidskill" / "references" / "depth.md"
    items = [es.bundle_item(skill, "skill", "Kid Concept"), es.bundle_item(ref, "reference", "Kid Concept"),
             es.bundle_item(repo / es.PACKS_REL / "kid-concept.json", "pack", "Kid Concept")]
    out = es.export_bundle("kid-concept-20260101T000000Z", items)
    assert out == home / "bundles" / "kid-concept-20260101T000000Z"
    md = (out / "bundle.md").read_text()
    assert md.startswith("# Bundle: kid-concept-20260101T000000Z\n\nRead these files in order; each line gives the absolute path, what the file is, and how to use it.\n\n")
    assert f"- **SKILL.md for Kid Concept** — `{skill.resolve()}` — load it as the agent's skill prompt before starting the task\n" in md
    data = json.loads((out / "bundle.json").read_text())
    assert [d["path"] for d in data] == [str(skill.resolve()), str(ref.resolve()), str((repo / es.PACKS_REL / "kid-concept.json").resolve())]
    assert set(data[0]) == {"path", "kind", "concept", "what", "how", "description"}
    assert data[0]["description"] == "Kid skill does kid things."
    assert data[1]["what"] == "reference depth.md for Kid Concept"
    assert data[2]["description"] == "pack summary"
    assert all(Path(d["path"]).is_absolute() for d in data)
    with pytest.raises(ValueError):
        es.bundle_item(skill, "weird", "x")
    assert es.export_bundle("../../escape", items) == home / "bundles" / "escape"


# --------------------------------------------------------------------------- #
# config, remotes and the token

def test_config_is_0600_and_env_token_wins(tmp_path, home, monkeypatch):
    p = es.set_github_token("ghp_secret123")
    assert p == home / "config.json"
    assert stat.S_IMODE(p.stat().st_mode) == 0o600
    assert es.github_token() == "ghp_secret123"
    monkeypatch.setenv("LLMSX_GITHUB_TOKEN", "env_token_12")
    assert es.github_token() == "env_token_12"
    monkeypatch.delenv("LLMSX_GITHUB_TOKEN")
    es.set_github_token("")
    assert es.github_token() == "" and "github_token" not in es.load_config()
    with pytest.raises(ValueError):
        es.set_github_token("bad token with spaces")
    assert es.repo_url() == es.DEFAULT_REPO_URL and es.push_url() == "origin"
    assert not list(home.glob(".config.json.*")), "no temp file left behind"


def test_remotes_are_validated_before_git_sees_them(tmp_path, home):
    assert es.valid_remote("origin") is None
    assert es.valid_remote("https://github.com/me/fork.git") is None
    for bad in ("", "-c", "--upload-pack=x", "ext::sh -c id", "ssh://x", "https://user:pw@github.com/x", "/tmp/x",
                "https://github.com/x/y.git&calc", 'https://github.com/x/"y'):
        assert es.valid_remote(bad) is not None, bad
    es.set_remotes("https://github.com/me/llms-explorer.git", "https://github.com/me/fork.git")
    assert es.push_url() == "https://github.com/me/fork.git"
    with pytest.raises(ValueError, match="push_url"):
        es.set_remotes("https://github.com/me/x.git", "ext::sh")
    with pytest.raises(ValueError, match="repo_url"):
        es.set_remotes("origin", "origin")
    cfg = es.load_config()
    cfg["push_url"] = "-c"
    es.save_config(cfg)
    assert es.push_url() == "origin", "a bad stored value falls back rather than reaching git"
    repo = make_repo(tmp_path, git=False)
    for fn in (lambda: es.git_push(repo, "https://user:pw@github.com/x", "ghp_tokentoken"),
               lambda: es.test_token(repo, "https://user:pw@github.com/x", "ghp_tokentoken"),
               lambda: es.clone_repo("https://user:pw@github.com/x", tmp_path / "c2")):
        with pytest.raises(es.GitError) as ei:
            fn()
        assert "pw" not in str(ei.value) and "refusing" in str(ei.value), "a refusal never echoes the credential"
    with pytest.raises(es.GitError, match="refusing"):
        es.git_push(repo, "ext::sh -c id", "ghp_tokentoken")
    with pytest.raises(es.GitError, match="refusing"):
        es.test_token(repo, "-c", "ghp_tokentoken")
    with pytest.raises(es.GitError, match="refusing"):
        es.clone_repo("ext::sh", tmp_path / "c")


# --------------------------------------------------------------------------- #
# git

def test_commit_stages_only_the_allowlist(tmp_path, home, git_template):
    repo = make_repo(tmp_path, template=git_template)
    es.set_mark(repo, "kid-concept", "needs-review")
    es.queue_concept(repo, "Ghost Concept", "Root Domain", "dr")
    (repo / "README.md").write_text("not for the explorer\n")
    (repo / "concept-tree" / "stray-note.md").write_text(INJECTION)
    ok, other = es.changed_allowlisted(repo)
    assert sorted(ok) == ["concept-tree/RESEARCH_QUEUE.md", "concept-tree/marks.json"]
    assert sorted(other) == ["README.md", "concept-tree/stray-note.md"]
    assert "not staged (outside the allow-list)" in es.diff_summary(repo)
    sha = es.commit_allowlisted(repo, "explorer: Kid Concept")
    assert len(sha) >= 7
    committed = _git(repo, "show", "--name-only", "--format=", "HEAD").split()
    assert sorted(committed) == ["concept-tree/RESEARCH_QUEUE.md", "concept-tree/marks.json"]
    status = _git(repo, "status", "--porcelain")
    assert "README.md" in status and "stray-note.md" in status, "other files stay untouched and uncommitted"
    with pytest.raises(es.GitError, match="nothing to commit"):
        es.commit_allowlisted(repo, "again")


def test_changed_allowlisted_follows_renames_both_ways(tmp_path, home, git_template):
    repo = make_repo(tmp_path, template=git_template)
    _git(repo, "mv", "concept-tree/tree.json", "concept-tree/tree-moved.json")
    ok, other = es.changed_allowlisted(repo)
    assert "concept-tree/tree.json" in ok and "concept-tree/tree-moved.json" in other
    _git(repo, "mv", "concept-tree/tree-moved.json", "concept-tree/tree.json")
    _git(repo, "mv", "site/src/data/concepts/kid-concept.json", "concept-tree/marks.json")
    ok, other = es.changed_allowlisted(repo)
    assert "concept-tree/marks.json" in ok and "site/src/data/concepts/kid-concept.json" in other
    assert es._porcelain_paths('R  "a b.txt" -> "c d.txt"') == ["a b.txt", "c d.txt"]
    assert es._porcelain_paths(' M "caf\\303\\251.md"') == ["café.md"], "git's octal C-quoting decodes as UTF-8"


def test_push_passes_the_token_only_through_askpass_and_never_forces(tmp_path, home, monkeypatch, git_template):
    repo = make_repo(tmp_path, template=git_template)
    stub = tmp_path / "git-stub"
    log = tmp_path / "argv.log"
    stub.write_text(
        "#!/bin/sh\n"
        f"printf '%s\\n' \"$@\" >> {log}\n"
        "env | grep -E '^GIT_ASKPASS=' >> " + str(log) + "\n"
        "for a in \"$@\"; do [ \"$a\" = \"ls-remote\" ] && printf 'abc\\trefs/heads/main\\n'; done\n"
        "for a in \"$@\"; do [ \"$a\" = \"rev-parse\" ] && printf 'main\\n'; done\n"
        "exit 0\n")
    stub.chmod(0o755)
    monkeypatch.setenv("LLMSX_GIT", str(stub))
    es.set_github_token("ghp_supersecret")
    out = es.git_push(repo, "origin", es.github_token())
    assert out == "pushed"
    assert "ok: 1 branch(es)" in es.test_token(repo, "https://github.com/x/y.git", es.github_token())
    recorded = log.read_text()
    assert "ghp_supersecret" not in recorded, "the token must never be in argv"
    assert "--force" not in recorded and "-f\n" not in recorded
    assert "GIT_ASKPASS=" in recorded
    assert "push\n--\norigin\nHEAD:main" in recorded, "the remote follows a literal --"
    askpass_files = list((home / "tmp").glob("askpass-*"))
    assert askpass_files == [], "the helper script is deleted after each use"
    for f in repo.rglob("*"):
        if f.is_file() and ".git" not in f.parts:
            assert "ghp_supersecret" not in f.read_text(errors="ignore")
    with pytest.raises(es.GitError, match="no GitHub token"):
        es.git_push(repo, "origin", "")


def test_askpass_helper_answers_username_then_password(tmp_path, home):
    script = es._askpass_script("tok-en_123")
    try:
        assert stat.S_IMODE(script.stat().st_mode) == 0o700
        user = subprocess.run([str(script), "Username for 'https://github.com': "], capture_output=True, text=True).stdout
        pw = subprocess.run([str(script), "Password for 'https://x-access-token@github.com': "], capture_output=True, text=True).stdout
        assert user.strip() == "x-access-token" and pw.strip() == "tok-en_123"
    finally:
        script.unlink()
    with pytest.raises(es.GitError, match="not a GitHub token"):
        es._askpass_script("has space")


def test_git_errors_are_verbatim_but_scrubbed(tmp_path, home, git_template):
    repo = make_repo(tmp_path, template=git_template)
    with pytest.raises(es.GitError):
        es.git_pull(repo)   # no remote: git's own message, verbatim
    assert es._scrub("fatal: https://me:pw@github.com/x failed") == "fatal: https://github.com/x failed"


def test_find_repo_walks_up_then_falls_back_to_home(tmp_path, home, monkeypatch):
    repo = make_repo(tmp_path, git=False)
    assert es.find_repo(repo / "site" / "src") == repo
    monkeypatch.chdir(tmp_path)
    assert es.find_repo(tmp_path) is None
    clone = home / "llms-explorer" / "concept-tree"
    clone.mkdir(parents=True)
    (clone / "tree.json").write_text("[]")
    assert es.find_repo(tmp_path) == home / "llms-explorer"


def test_cli_explorer_subcommand_is_registered():
    out = subprocess.run([sys.executable, "-m", "llmsx", "explorer", "--help"], capture_output=True, text=True,
                         env={**os.environ, "PYTHONPATH": str(TESTS_DIR.parent)})
    assert out.returncode == 0 and "--no-sync" in out.stdout and "--repo" in out.stdout


# --------------------------------------------------------------------------- #
# multi-provider and API key configuration

def test_providers_and_precedence(home, monkeypatch):
    assert "google" in es.PROVIDERS and "codex" in es.PROVIDERS
    assert "copilot" in es.PROVIDERS and "ollama" in es.PROVIDERS
    assert "claude" in es.PROVIDERS

    # Default
    assert es.active_provider() == "claude"

    # Set via config
    p = es.set_provider("google")
    assert p.is_file()
    assert stat.S_IMODE(p.stat().st_mode) == 0o600
    assert es.active_provider() == "google"

    # Environment variable takes precedence over config
    monkeypatch.setenv("LLMSX_PROVIDER", "codex")
    assert es.active_provider() == "codex"

    monkeypatch.setenv("LLMSX_AGENT_ENGINE", "ollama")
    monkeypatch.delenv("LLMSX_PROVIDER", raising=False)
    assert es.active_provider() == "ollama"

    with pytest.raises(ValueError, match="unknown provider"):
        es.set_provider("unsupported-backend")


def test_provider_api_keys_persistence_and_env_precedence(home, monkeypatch):
    assert es.provider_api_key("google") == ""

    # Set in config
    p = es.set_provider_api_key("google", "AIzaSySecret12345")
    assert p.is_file()
    assert stat.S_IMODE(p.stat().st_mode) == 0o600
    assert es.provider_api_key("google") == "AIzaSySecret12345"

    # Env var wins over stored key
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaSyEnvKeyWins")
    assert es.provider_api_key("google") == "AIzaSyEnvKeyWins"

    monkeypatch.delenv("GEMINI_API_KEY")
    monkeypatch.setenv("GOOGLE_API_KEY", "AIzaSyGoogleKeyWins")
    assert es.provider_api_key("google") == "AIzaSyGoogleKeyWins"

    monkeypatch.delenv("GOOGLE_API_KEY")
    assert es.provider_api_key("google") == "AIzaSySecret12345"

    # Clear key with "-"
    es.set_provider_api_key("google", "-")
    assert es.provider_api_key("google") == ""

    # Codex keys
    es.set_provider_api_key("codex", "sk-proj-codexsecret")
    assert es.provider_api_key("codex") == "sk-proj-codexsecret"
    monkeypatch.setenv("OPENAI_API_KEY", "sk-env-openai")
    assert es.provider_api_key("codex") == "sk-env-openai"

    # Copilot and github_token sync
    es.set_provider_api_key("copilot", "ghp_copilot_token_12345")
    assert es.provider_api_key("copilot") == "ghp_copilot_token_12345"
    assert es.github_token() == "ghp_copilot_token_12345"

    # Ollama key
    es.set_provider_api_key("ollama", "ollama-token-secret")
    assert es.provider_api_key("ollama") == "ollama-token-secret"

    # Rejection of bad keys
    with pytest.raises(ValueError, match="control characters"):
        es.set_provider_api_key("google", "bad\nkey")
    with pytest.raises(ValueError, match="starts with '-'"):
        es.set_provider_api_key("codex", "-invalid-option")


def test_provider_models_and_overrides(home, monkeypatch):
    assert es.provider_model("google") == "gemini-2.5-pro"
    assert es.provider_model("codex") == "o3-mini"
    assert es.provider_model("ollama") == "llama3.2"

    es.set_provider_model("google", "gemini-2.5-flash")
    assert es.provider_model("google") == "gemini-2.5-flash"

    monkeypatch.setenv("LLMSX_GOOGLE_MODEL", "gemini-exp-1206")
    assert es.provider_model("google") == "gemini-exp-1206"


def test_provider_binary_and_research_argv_generation(home, monkeypatch):
    def fake_which(cmd):
        if cmd in ("gemini", "codex", "gh", "ollama", "claude"):
            return f"/usr/local/bin/{cmd}"
        return None

    monkeypatch.setattr(es.shutil, "which", fake_which)

    assert es.has_provider_binary("google")
    assert es.has_provider_binary("codex")
    assert es.has_provider_binary("copilot")
    assert es.has_provider_binary("ollama")
    assert es.has_provider_binary("claude")

    # Google argv
    g_argv = es.research_argv("Concept A", "dr", provider="google")
    assert g_argv[0] == "/usr/local/bin/gemini"
    assert "--approval-mode" in g_argv and "yolo" in g_argv
    assert "-o" in g_argv and "stream-json" in g_argv

    # Codex argv
    c_argv = es.research_argv("Concept A", "dr", provider="codex")
    assert c_argv[0] == "/usr/local/bin/codex"
    assert "exec" in c_argv and "--dangerously-bypass-approvals-and-sandbox" in c_argv
    assert "--json" in c_argv

    # Copilot argv
    cp_argv = es.research_argv("Concept A", "dr", provider="copilot")
    assert cp_argv[0] == "/usr/local/bin/gh"
    assert "copilot" in cp_argv and "-p" in cp_argv

    # Ollama argv
    o_argv = es.research_argv("Concept A", "dr", provider="ollama")
    assert o_argv[0] == "/usr/local/bin/ollama"
    assert "run" in o_argv and "llama3.2" in o_argv

    # Missing binary returns None
    monkeypatch.setattr(es.shutil, "which", lambda _c: None)
    assert es.research_argv("Concept A", "dr", provider="google") is None


def test_test_provider_key(home, monkeypatch):
    monkeypatch.setattr(es.shutil, "which", lambda _c: None)
    res = es.test_provider_key("google")
    assert "CLI not found on PATH" in res

    monkeypatch.setattr(es.shutil, "which", lambda c: f"/usr/bin/{c}")
    assert "no API key configured" in es.test_provider_key("google")

    es.set_provider_api_key("google", "AIzaSyTestKeyValid12345")
    assert "ready: gemini found on PATH" in es.test_provider_key("google")

    # Ollama is ready without key
    assert "ready: ollama found on PATH (local runner)" in es.test_provider_key("ollama")


def test_summarize_event_across_providers():
    # Claude stream-json assistant event
    claude_ev = json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "Researching topic"}]}})
    assert es.summarize_event(claude_ev) == "assistant: Researching topic"

    # Gemini candidate event
    gemini_ev = json.dumps({"candidates": [{"content": {"parts": [{"text": "Gemini findings"}]}}]})
    assert es.summarize_event(gemini_ev) == "Gemini findings"

    # Codex message event
    codex_ev = json.dumps({"type": "agent_message", "text": "Codex output line"})
    assert es.summarize_event(codex_ev) == "assistant: Codex output line"

    # Ollama response event
    ollama_ev = json.dumps({"response": "Ollama streaming token"})
    assert es.summarize_event(ollama_ev) == "Ollama streaming token"

    # Raw non-JSON text
    assert es.summarize_event("Fatal error occurred in runner") == "Fatal error occurred in runner"


def test_frontier_concepts_ordered_and_deduped(tmp_path, home):
    repo = make_repo(tmp_path, git=False)
    # Default make_repo has "Root Domain" with children "Kid Concept" (researched) and "Ghost Concept" (frontier)
    tree = es.load_raw_tree(repo / es.TREE_REL)
    o = es.build_outline(tree)
    assert es.frontier_concepts(o) == ["Ghost Concept"]

    # Add multiple frontiers across branches
    tree.append({
        "concept": "Branch Two",
        "slug": "branch-two",
        "parentConcept": None,
        "childConcepts": ["Frontier Alpha", "Frontier Beta"],
    })
    es.save_raw_tree(tree, repo / es.TREE_REL)
    o2 = es.build_outline(tree)
    assert es.frontier_concepts(o2) == ["Ghost Concept", "Frontier Alpha", "Frontier Beta"]


def test_most_used_concept_selection(tmp_path, home):
    repo = make_repo(tmp_path, git=False)
    tree = es.load_raw_tree(repo / es.TREE_REL)
    o = es.build_outline(tree)

    # Empty tree returns None
    assert es.most_used_concept(repo, es.Outline({}, {}, [], {})) is None

    # Base tree: Kid Concept has an installed skill (skillId: "kidskill"), alias, and parent reference
    assert es.most_used_concept(repo, o) == "Kid Concept"

    # Boost Root Domain with marks and highlights
    es.save_marks(repo, {"root-domain": {"state": "needs-review", "tags": ["core", "domain", "arch"]}})
    es.save_highlights([
        {"id": "h1", "concept": "Root Domain", "quote": "Domain quote 1"},
        {"id": "h2", "concept": "Root Domain", "quote": "Domain quote 2"},
    ])
    # Now Root Domain should score higher than Kid Concept
    assert es.most_used_concept(repo, o) == "Root Domain"

