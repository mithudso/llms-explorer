"""Website currency regressions, isolated from the user's live research."""
from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("research_website", REPO / "scripts/research_site_sync.py")
website = importlib.util.module_from_spec(spec)
spec.loader.exec_module(website)


def node(name, slug, parent=None, children=None):
    return {"concept": name, "slug": slug, "parentConcept": parent,
            "childConcepts": children or [], "skillId": None, "aliases": [],
            "researchedAt": "2026-10-20", "sourcesCount": 1}


def reader(name, slug, text="A source-anchored research finding."):
    return {"slug": slug, "concept": name, "generated": "2026-10-20", "summary": name,
            "facets": [{"title": "Facts", "facts": [{"text": text, "source": "https://example.test/reference", "note": None}]}],
            "related": []}


class SiteSyncTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.repo, self.hub = self.root / "repo", self.root / "hub"
        for relative in ("scripts/research_site_sync.py", "scripts/recover_dr_packs.py", "scripts/publish_scrub.py",
                         "scripts/check_publish_privacy.py", "site/tools/gen_tree.py", "site/tools/gen_concepts.py",
                         "site/tools/gen_context.py", "site/tools/gen_concept_facts.py", "hub/scripts/concept_tree.py",
                         "hub/scripts/research_site_hook.py"):
            dest = self.repo / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO / relative, dest)
        for root in (self.repo, self.hub):
            (root / "concept-tree").mkdir(parents=True, exist_ok=True)
            (root / "concept-tree/tree.json").write_text(json.dumps([node("Root", "root")]))
        (self.repo / "site/src/data/concepts").mkdir(parents=True)

    def save_pack(self, name="New concept", slug="new-concept"):
        directory = self.hub / "llms-concepts" / f"{slug}.llms"
        directory.mkdir(parents=True)
        (directory / "manifest.json").write_text(json.dumps({"kind": "concept", "concept": name, "slug": slug,
                                                              "generated": "2026-10-20", "summary": name,
                                                              "facets": {"facts": 1}}))
        (directory / "llms.txt").write_text(f"# {name}\n\n> Reference.\n")
        (directory / "llms-full.txt").write_text(f"# {name}\n\n## Facts\n\n- [statement] New finding. — https://example.test/primary\n")

    def test_refresh_keeps_legacy_research_and_updates_all_website_surfaces(self):
        legacy = self.repo / "site/src/data/concepts/legacy.json"
        legacy.write_text(json.dumps(reader("Legacy", "legacy")))
        self.save_pack()
        before = (self.repo / "concept-tree/tree.json").read_bytes()
        preview = website.sync(self.repo, self.hub)
        self.assertEqual(before, (self.repo / "concept-tree/tree.json").read_bytes())
        self.assertEqual(preview["website_packs_after"], 2)
        result = website.sync(self.repo, self.hub, apply=True)
        self.assertEqual(result["unfiled_website_packs"], [])
        self.assertTrue(legacy.exists())
        self.assertTrue((self.repo / "site/public/downloads/concepts/new-concept.md").exists())
        tree = json.loads((self.repo / "site/src/data/tree.json").read_text())
        self.assertTrue(tree["nodes"]["new-concept"]["hasPack"])
        context = json.loads((self.repo / "site/src/data/context.json").read_text())
        self.assertEqual(context["totals"]["concepts"], 2)
        self.assertEqual(len(json.loads((self.hub / "concept-tree/tree.json").read_text())), 3)
        self.assertEqual(website.sync(self.repo, self.hub)["changed_files"], [])

    def test_hub_pack_slug_follows_existing_website_identity_and_redirect(self):
        name = "Canonical concept"
        (self.repo / "concept-tree/tree.json").write_text(json.dumps([node(name, "stable-url")]))
        (self.hub / "concept-tree/tree.json").write_text(json.dumps([node(name, "hub-url")]))
        self.save_pack("Earlier editorial title", "hub-url")
        result = website.sync(self.repo, self.hub, apply=True)
        tree = json.loads((self.repo / "site/src/data/tree.json").read_text())
        self.assertEqual(list(tree["nodes"]), ["stable-url"])
        self.assertEqual(tree["redirects"], {"hub-url": "stable-url"})
        self.assertEqual(result["unfiled_website_packs"], [])
        self.assertTrue((self.repo / "site/src/data/concepts/stable-url.json").exists())

    def test_private_concepts_and_source_library_text_do_not_enter_website(self):
        (self.hub / "concept-tree/tree.json").write_text(json.dumps([node("Root", "root"), node("Private Topic", "private-topic")]))
        (self.repo / "concept-tree/tree.json").write_text(json.dumps([node("Root", "root"), node("Private Topic", "private-topic")]))
        (self.repo / "site/src/data/concepts/private-topic.json").write_text(json.dumps(reader("Private Topic", "private-topic")))
        self.save_pack("Private Topic", "private-topic")
        library = self.hub / "research/.library/text/raw.txt"
        library.parent.mkdir(parents=True)
        library.write_text("Third-party raw text must stay private.")
        with patch.dict("os.environ", {"PRIVACY_DENYLIST": "Private Topic"}):
            result = website.sync(self.repo, self.hub, apply=True)
        self.assertEqual(result["excluded_private_nodes"], 1)
        self.assertFalse((self.repo / "site/src/data/concepts/private-topic.json").exists())
        self.assertEqual(library.read_text(), "Third-party raw text must stay private.")
        self.assertNotIn("Private Topic", (self.repo / "concept-tree/tree.json").read_text())

    def test_private_ancestor_removes_generic_descendant_packs_and_repo_exports(self):
        private = node("Private Topic", "private-topic", children=["Generic descendant"])
        child = node("Generic descendant", "generic-descendant", parent="Private Topic")
        (self.hub / "concept-tree/tree.json").write_text(json.dumps([private, child]))
        (self.repo / "site/src/data/concepts/generic-descendant.json").write_text(json.dumps(reader("generic descendant", "generic-descendant")))
        self.save_pack("Generic descendant", "generic-descendant")
        local_pack = self.repo / "outputs/llms-concepts/generic-descendant.llms"
        shutil.copytree(self.hub / "llms-concepts/generic-descendant.llms", local_pack)
        with patch.dict("os.environ", {"PRIVACY_DENYLIST": "Private Topic"}):
            result = website.sync(self.repo, self.hub, apply=True)
        self.assertFalse((self.repo / "site/src/data/concepts/generic-descendant.json").exists())
        self.assertFalse((local_pack / "manifest.json").exists())
        self.assertTrue((self.hub / "llms-concepts/generic-descendant.llms/manifest.json").exists())
        self.assertEqual(result["website_packs_after"], 0)
        self.assertTrue((self.repo / result["backup"] / "repository/outputs/llms-concepts/generic-descendant.llms/manifest.json").exists())

    def test_new_pack_uses_canonical_tree_title_without_prior_reader(self):
        for root in (self.repo, self.hub):
            (root / "concept-tree/tree.json").write_text(json.dumps([node("Canonical title", "stable")]))
        self.save_pack("Older editorial title", "stable")
        website.sync(self.repo, self.hub, apply=True)
        pack = json.loads((self.repo / "site/src/data/concepts/stable.json").read_text())
        self.assertEqual(pack["concept"], "Canonical title")
        self.assertIn("Canonical title", (self.repo / "site/public/search-keywords.json").read_text())

    def test_canonical_pack_replaces_an_older_reader_title_without_a_conflict(self):
        for root in (self.repo, self.hub):
            (root / "concept-tree/tree.json").write_text(json.dumps([node("Canonical title", "stable")]))
        self.save_pack("Canonical title", "stable")
        path = self.repo / "site/src/data/concepts/stable.json"
        path.write_text(json.dumps(reader("Older editorial title", "stable")))
        website.sync(self.repo, self.hub, apply=True)
        self.assertEqual(json.loads(path.read_text())["concept"], "Canonical title")

    def test_tree_slug_collision_stops_before_writing(self):
        (self.hub / "concept-tree/tree.json").write_text(json.dumps([node("Other identity", "root")]))
        before = (self.repo / "concept-tree/tree.json").read_bytes()
        with self.assertRaisesRegex(ValueError, "slug collision"):
            website.sync(self.repo, self.hub, apply=True)
        self.assertEqual(before, (self.repo / "concept-tree/tree.json").read_bytes())

    def test_same_date_recovery_cannot_replace_a_richer_website_reference(self):
        self.save_pack()
        richer = reader("New concept", "new-concept")
        richer["facets"][0]["facts"].append({"text": "Another retained fact.", "source": "https://example.test/other", "note": None})
        (self.repo / "site/src/data/concepts/new-concept.json").write_text(json.dumps(richer))
        result = website.sync(self.repo, self.hub, apply=True)
        self.assertEqual(result["website_totals"]["facts"], 2)

    def test_search_reconciles_existing_vectors_without_embedding_new_packs(self):
        meta = self.repo / "site/src/data/search-meta.json"
        binary = self.repo / "site/public/search-index.bin"
        binary.parent.mkdir(parents=True)
        meta.write_text(json.dumps({"model": "frozen-model", "dim": 1, "count": 2,
                                    "items": [{"slug": "old", "concept": "Old", "summary": ""},
                                              {"slug": "gone", "concept": "Gone", "summary": ""}]}))
        binary.write_bytes(b"12345678")
        writes, report = website.search_writes(self.repo, {"new": reader("New", "new"),
                                                         "fresh": reader("Fresh", "fresh")}, {"old": "new"})
        self.assertEqual(writes[binary], b"1234")
        self.assertEqual(json.loads(writes[meta])["items"][0]["slug"], "new")
        self.assertEqual(json.loads(writes[meta])["items"][0]["summary"], "New")
        self.assertEqual(report["new_embeddings"], 0)
        self.assertEqual(report["keyword_concepts"], 2)
        self.assertEqual(report["deferred_semantic_concepts"], 1)

    def test_public_examples_keep_their_meaning_without_identity_values(self):
        scrub = website.module("publication_test_scrub", REPO / "scripts/publish_scrub.py")
        original = reader("Example", "example", 'Use ObjectId("' + 'f' * 24 + '") with "person@vendor.invalidhost".')
        original["facets"][0]["facts"][0]["source"] = "https://example.test/RestrictedReference"
        safe = website.publication_pack(original, scrub, ["RestrictedReference"])
        fact = safe["facets"][0]["facts"][0]
        self.assertIn("<object-id>", fact["text"])
        self.assertIn("user@example.test", fact["text"])
        self.assertEqual(fact["source"], "archived:private-reference")
        self.assertIn("person@vendor.invalidhost", original["facets"][0]["facts"][0]["text"])
        self.assertFalse((self.repo / "site/src/data/tree.json").exists())


if __name__ == "__main__":
    unittest.main()
