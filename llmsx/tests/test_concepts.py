# llmsx/tests/test_concepts.py
"""Offline: every fixture here is a fake pack directory under tmp_path — no
test in this file touches the real ~/.global-ai-hub/llms-concepts."""
import json

import pytest

from llmsx import concepts


def _write_pack(root, slug, concept, *, kind="concept", summary="A summary.",
                facets=None, related=None, files=None):
    pack_dir = root / f"{slug}.llms"
    pack_dir.mkdir(parents=True)
    manifest = {
        "slug": slug, "concept": concept, "kind": kind, "summary": summary,
        "facets": facets or {}, "files": files or {},
    }
    (pack_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    if related is not None:
        graph = {
            "concept": concept, "slug": slug,
            "nodes": [
                {"term": concept, "relation": "self", "hits": 999},
                *[{"term": t, "relation": "related", "hits": len(related) - i}
                  for i, t in enumerate(related)],
            ],
        }
        (pack_dir / "concept-graph.json").write_text(json.dumps(graph), encoding="utf-8")
    (pack_dir / "llms.txt").write_text(f"# {concept}\n", encoding="utf-8")
    return pack_dir


# --- iter_packs ---------------------------------------------------------- #

def test_iter_packs_yields_slug_dir_manifest(tmp_path):
    _write_pack(tmp_path, "rsl", "Really Simple Licensing")
    _write_pack(tmp_path, "robots-txt", "robots.txt")
    got = sorted(slug for slug, _dir, _manifest in concepts.iter_packs(tmp_path))
    assert got == ["robots-txt", "rsl"]


def test_iter_packs_returns_pack_dir_and_manifest(tmp_path):
    pack_dir = _write_pack(tmp_path, "rsl", "Really Simple Licensing")
    [(slug, got_dir, manifest)] = list(concepts.iter_packs(tmp_path))
    assert slug == "rsl"
    assert got_dir == pack_dir
    assert manifest["concept"] == "Really Simple Licensing"


def test_iter_packs_skips_unparseable_manifest_silently(tmp_path):
    _write_pack(tmp_path, "rsl", "RSL")
    broken = tmp_path / "broken.llms"
    broken.mkdir()
    (broken / "manifest.json").write_text("{not valid json", encoding="utf-8")
    got = [slug for slug, *_ in concepts.iter_packs(tmp_path)]
    assert got == ["rsl"]


def test_iter_packs_skips_pack_with_no_manifest(tmp_path):
    _write_pack(tmp_path, "rsl", "RSL")
    (tmp_path / "no-manifest.llms").mkdir()
    got = [slug for slug, *_ in concepts.iter_packs(tmp_path)]
    assert got == ["rsl"]


def test_iter_packs_on_missing_directory_yields_nothing(tmp_path):
    assert list(concepts.iter_packs(tmp_path / "does-not-exist")) == []


# --- resolve_pack --------------------------------------------------------- #

def test_resolve_pack_exact_slug_wins_outright(tmp_path):
    _write_pack(tmp_path, "rsl", "Really Simple Licensing")
    slug, pack_dir, manifest = concepts.resolve_pack("rsl", tmp_path)
    assert slug == "rsl"
    assert pack_dir == tmp_path / "rsl.llms"
    assert manifest["concept"] == "Really Simple Licensing"


def test_resolve_pack_substring_match_is_case_insensitive(tmp_path):
    _write_pack(tmp_path, "robots-txt-content-signals", "robots.txt Content Signals")
    slug, _dir, _manifest = concepts.resolve_pack("ROBOTS", tmp_path)
    assert slug == "robots-txt-content-signals"


def test_resolve_pack_matches_against_concept_name_too(tmp_path):
    _write_pack(tmp_path, "agents-md-ucp", "agents.md and the Universal Commerce Protocol")
    slug, _dir, _manifest = concepts.resolve_pack("universal commerce", tmp_path)
    assert slug == "agents-md-ucp"


def test_resolve_pack_ambiguous_raises_with_candidates(tmp_path):
    _write_pack(tmp_path, "llms-txt", "llms.txt")
    _write_pack(tmp_path, "llms-txt-family", "llms.txt family")
    with pytest.raises(KeyError) as excinfo:
        concepts.resolve_pack("llms", tmp_path)
    message = str(excinfo.value)
    assert "llms-txt" in message
    assert "llms-txt-family" in message


def test_resolve_pack_no_match_raises_and_names_the_query(tmp_path):
    _write_pack(tmp_path, "rsl", "RSL")
    with pytest.raises(KeyError) as excinfo:
        concepts.resolve_pack("zzz-nonexistent", tmp_path)
    assert "zzz-nonexistent" in str(excinfo.value)


# --- serve / servable-file allowlist --------------------------------------- #

def test_serve_returns_file_text(tmp_path):
    _write_pack(tmp_path, "rsl", "RSL")
    text = concepts.serve("rsl", "llms.txt", tmp_path)
    assert text == "# RSL\n"


def test_serve_rejects_a_file_outside_the_allowlist(tmp_path):
    _write_pack(tmp_path, "rsl", "RSL")
    with pytest.raises(ValueError):
        concepts.serve("rsl", "not-a-real-servable-file.txt", tmp_path)


def test_serve_raises_file_not_found_when_pack_lacks_the_file(tmp_path):
    _write_pack(tmp_path, "rsl", "RSL")
    with pytest.raises(FileNotFoundError):
        concepts.serve("rsl", "llms-full.txt", tmp_path)


def test_serve_propagates_ambiguous_resolution(tmp_path):
    _write_pack(tmp_path, "llms-txt", "llms.txt")
    _write_pack(tmp_path, "llms-txt-family", "llms.txt family")
    with pytest.raises(KeyError):
        concepts.serve("llms", "llms.txt", tmp_path)


# --- library / query filter ------------------------------------------------ #

def test_library_synthesizes_useful_for_and_related_terms(tmp_path):
    _write_pack(tmp_path, "rsl", "RSL", facets={"facts": 10, "examples": 2},
               related=["licensing", "robots.txt"],
               files={"llms.txt": {"tokens": 500, "bytes": 2000}})
    entries = concepts.library("", tmp_path)
    assert len(entries) == 1
    entry = entries[0]
    assert entry["slug"] == "rsl"
    assert entry["kind"] == "concept"
    assert "facts (10)" in entry["useful_for"]
    assert "licensing" in entry["related_terms"]
    assert entry["files"] == {"llms.txt": 500}


def test_library_useful_for_falls_back_when_no_metadata(tmp_path):
    _write_pack(tmp_path, "bare", "Bare Concept")
    [entry] = concepts.library("", tmp_path)
    assert entry["useful_for"] == "no facet/relation metadata available"
    assert entry["related_terms"] == []


def test_library_query_filters_by_name_summary_slug_or_related_term(tmp_path):
    _write_pack(tmp_path, "rsl", "Really Simple Licensing",
               summary="licensing for AI crawlers")
    _write_pack(tmp_path, "agents-md", "agents.md",
               summary="agent discovery file", related=["commerce protocol"])
    assert [e["slug"] for e in concepts.library("licensing", tmp_path)] == ["rsl"]
    assert [e["slug"] for e in concepts.library("discovery", tmp_path)] == ["agents-md"]
    assert [e["slug"] for e in concepts.library("commerce", tmp_path)] == ["agents-md"]
    assert concepts.library("no-such-term-anywhere", tmp_path) == []


def test_library_sorts_by_concept_name(tmp_path):
    _write_pack(tmp_path, "zzz", "Zebra Thing")
    _write_pack(tmp_path, "aaa", "Aardvark Thing")
    assert [e["concept"] for e in concepts.library("", tmp_path)] == \
        ["Aardvark Thing", "Zebra Thing"]


def test_library_files_restricted_to_servable_allowlist(tmp_path):
    _write_pack(tmp_path, "rsl", "RSL", files={
        "llms.txt": {"tokens": 100},
        "units.jsonl": {"tokens": 9999},   # not servable — must be dropped
    })
    [entry] = concepts.library("", tmp_path)
    assert entry["files"] == {"llms.txt": 100}


# --- related_terms ---------------------------------------------------------- #

def test_related_terms_excludes_self_and_ranks_by_hits(tmp_path):
    pack_dir = _write_pack(tmp_path, "rsl", "RSL", related=["b", "a"])
    assert concepts.related_terms(pack_dir) == ["b", "a"]


def test_related_terms_empty_when_no_graph_file(tmp_path):
    pack_dir = _write_pack(tmp_path, "rsl", "RSL")
    assert concepts.related_terms(pack_dir) == []


# --- default_concepts_path -------------------------------------------------- #

def test_default_concepts_path_env_var_wins(tmp_path, monkeypatch):
    monkeypatch.setenv("LLMSX_CONCEPTS_PATH", str(tmp_path))
    assert concepts.default_concepts_path() == tmp_path


def test_default_concepts_path_raises_a_clear_error_when_nothing_found(tmp_path, monkeypatch):
    monkeypatch.delenv("LLMSX_CONCEPTS_PATH", raising=False)
    monkeypatch.setattr(concepts, "DEFAULT_CONCEPTS_DIR", tmp_path / "no-such-dir")
    with pytest.raises(FileNotFoundError) as excinfo:
        concepts.default_concepts_path()
    assert "$LLMSX_CONCEPTS_PATH" in str(excinfo.value)


# --- CLI surface ------------------------------------------------------------ #

def test_cli_concepts_list_and_show_and_serve(tmp_path, capsys):
    from llmsx.__main__ import main

    _write_pack(tmp_path, "rsl", "Really Simple Licensing",
               facets={"facts": 5}, related=["licensing"])

    assert main(["concepts", "--data", str(tmp_path), "list"]) == 0
    assert "rsl" in capsys.readouterr().out

    assert main(["concepts", "--data", str(tmp_path), "show", "rsl"]) == 0
    out = capsys.readouterr().out
    assert "Really Simple Licensing" in out
    assert "licensing" in out

    assert main(["concepts", "--data", str(tmp_path), "serve", "rsl"]) == 0
    assert capsys.readouterr().out == "# Really Simple Licensing\n"


def test_cli_concepts_serve_bad_file_is_a_clean_error(tmp_path, capsys):
    from llmsx.__main__ import main

    _write_pack(tmp_path, "rsl", "RSL")
    code = main(["concepts", "--data", str(tmp_path), "serve", "rsl", "--file", "nope.txt"])
    assert code == 2
    assert "llmsx:" in capsys.readouterr().err


def test_cli_concepts_show_ambiguous_is_a_clean_error(tmp_path, capsys):
    from llmsx.__main__ import main

    _write_pack(tmp_path, "llms-txt", "llms.txt")
    _write_pack(tmp_path, "llms-txt-family", "llms.txt family")
    code = main(["concepts", "--data", str(tmp_path), "show", "llms"])
    assert code == 2
    err = capsys.readouterr().err
    assert "llms-txt" in err and "llms-txt-family" in err


def test_cli_concepts_list_empty_query_no_match_is_nonzero(tmp_path, capsys):
    from llmsx.__main__ import main

    _write_pack(tmp_path, "rsl", "RSL")
    code = main(["concepts", "--data", str(tmp_path), "list", "--query", "zzz-nope"])
    assert code == 1
