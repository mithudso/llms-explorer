import pytest

from skill_registry.catalog import Catalog
from skill_registry.service import Service


def test_aliases_preserved_without_name_deduplication(skill, roots, tmp_path):
    alias = tmp_path / "aliases"
    alias.mkdir()
    (alias / "one").symlink_to(skill, target_is_directory=True)
    (alias / "two").symlink_to(skill, target_is_directory=True)
    other = tmp_path / "different"
    other.mkdir()
    (other / "SKILL.md").write_bytes((skill / "SKILL.md").read_bytes())
    catalog = Catalog(tmp_path / "state", roots + [{"path": str(alias)}, {"path": str(other)}])
    status = catalog.refresh()
    assert status["counts"] == {"skills": 2, "installations": 4, "invalid_skills": 0}
    hits = catalog.lookup("example", refresh=False)["hits"]
    assert len(hits) == 2
    assert sorted(len(h["installations"]) for h in hits) == [1, 3]
    assert len({h["id"] for h in hits}) == 2


def test_incremental_freshness_and_bounded_exact_load(skill, roots, tmp_path):
    catalog = Catalog(tmp_path / "state", roots)
    assert catalog.refresh()["updated"] == 1
    assert catalog.refresh()["updated"] == 0
    hit = catalog.lookup("evidence", refresh=False)["hits"][0]
    span = catalog.load(hit["id"], max_chars=10)
    assert span["text"] == (skill / "SKILL.md").read_text()[:10]
    assert span["truncated"] and span["next_offset"] == 10
    (skill / "SKILL.md").write_text((skill / "SKILL.md").read_text() + "Late vocabulary: quuxflorp.\n")
    with pytest.raises(ValueError, match="REVISION_CONFLICT"):
        catalog.load(hit["id"])
    assert catalog.lookup("quuxflorp")["hits"][0]["id"] == hit["id"]
    (skill / "SKILL.md").unlink()
    assert catalog.refresh()["counts"]["skills"] == 0


def test_invalid_metadata_is_reported_not_routed(skill, roots, tmp_path):
    (skill / "SKILL.md").write_text("no frontmatter")
    catalog = Catalog(tmp_path / "state", roots)
    assert catalog.refresh()["counts"]["invalid_skills"] == 1
    assert not catalog.lookup("frontmatter")["hits"]


@pytest.mark.parametrize("query,top", [("", 5), ("word", True), ("word", 21), ("x" * 2001, 5)])
def test_search_bounds(tmp_path, query, top):
    with pytest.raises(ValueError):
        Catalog(tmp_path / "state", []).lookup(query, top)


def test_cycles_do_not_prevent_alias_coverage(skill, roots, tmp_path):
    (skill / "loop").symlink_to(skill.parent, target_is_directory=True)
    status = Catalog(tmp_path / "state", roots).refresh()
    assert status["counts"]["skills"] == 1
    assert not status["partial"]


def test_lookup_preserves_explicit_disable_without_enabling_sources(skill, roots, tmp_path, monkeypatch):
    config = tmp_path / "codex"
    config.mkdir()
    (config / "config.toml").write_text(
        '[[skills.config]]\npath = ' + repr(str(skill / "SKILL.md")) + '\nenabled = false\n')
    monkeypatch.setenv("CODEX_HOME", str(config))
    result = Catalog(tmp_path / "state", roots).lookup("evidence")["hits"][0]
    assert result["activation"] == "unknown" and result["routing_candidate_only"]
    assert result["disabled_in"] == ["Codex"]
    assert result["installations"][0]["codex_activation"] == "explicitly-disabled"
    assert "enabled = false" in (config / "config.toml").read_text()


def test_exact_optimizer_beats_many_mentions_and_drives_policy_schedule(skill, roots, tmp_path,
                                                                       monkeypatch):
    def create(folder, name, description, body):
        folder.mkdir(parents=True)
        path = folder / "SKILL.md"
        path.write_text(f"---\nname: {name}\ndescription: {description}\n---\n{body}\n")
        return path.resolve()

    # Long installed definitions legitimately score below many short topical
    # references under OR-token BM25. Exact identity must bypass that cutoff.
    optimizer = create(skill.parent / "native/skill-optimizer", "skill-optimizer",
                       "Inspect and improve a selected skill", "Long native guidance. " * 5000)
    slug_copy = create(skill.parent / "other/skill-optimizer", "Alternative Guidance",
                       "Inspect a selected artifact", "Long alternate guidance. " * 5000)
    for index in range(40):
        create(skill.parent / f"generic-{index}", f"generic-{index}",
               "skill optimizer", "skill optimizer " * 20)
    alias = skill.parent / "optimizer-alias"
    alias.symlink_to(optimizer.parent, target_is_directory=True)
    service = Service(tmp_path / "state", {"roots": roots})
    catalog = service.catalog
    catalog.refresh()
    with catalog.connect() as db:
        baseline = db.execute("SELECT s.path FROM skills_fts f JOIN skills s ON s.id=f.id "
            "WHERE skills_fts MATCH ? ORDER BY bm25(skills_fts,0,5,3,1) LIMIT 20",
            ('"skill" OR "optimizer"',)).fetchall()
    assert str(optimizer) not in {row["path"] for row in baseline}
    hits = catalog.lookup("skill-optimizer", top=2, refresh=False)["hits"]
    assert [row["path"] for row in hits] == [str(optimizer), str(slug_copy)]
    assert [row["match_kind"] for row in hits] == ["exact-name", "exact-path-slug"]
    assert len(hits[0]["installations"]) == 2
    assert catalog.lookup("optimizer-alias", top=1, refresh=False)["hits"][0]["id"] == hits[0]["id"]
    assert catalog.lookup(str(optimizer), top=1, refresh=False)["hits"][0]["match_kind"] == "exact-path"
    selected = catalog.resolve_exact("example", refresh=False)
    # Native resolution must not filter an arbitrary lexical top-20 window.
    monkeypatch.setattr(catalog, "lookup", lambda *args, **kwargs: {"hits": []})
    assert service.definition("skill") == optimizer
    service.jobs.policy(selected["id"], enabled=True)
    scheduled = service.jobs.schedule(catalog)
    assert scheduled["errors"] == []
    assert len(scheduled["queued"]) == 1
    assert service.jobs.get(scheduled["queued"][0])["params"]["definition"] == str(optimizer)


def test_exact_resolution_excludes_invalid_metadata_and_rechecks_source(skill, roots, tmp_path):
    catalog = Catalog(tmp_path / "state", roots)
    catalog.refresh()
    original = (skill / "SKILL.md").read_text()
    (skill / "SKILL.md").write_text(original + "A concurrent edit.\n")
    with pytest.raises(ValueError, match="REVISION_CONFLICT"):
        catalog.resolve_exact("example", refresh=False)
    (skill / "SKILL.md").write_text("Invalid frontmatter")
    catalog.refresh()
    assert catalog.resolve_exact("example", refresh=False) is None
    assert not catalog.lookup("example", refresh=False)["hits"]
