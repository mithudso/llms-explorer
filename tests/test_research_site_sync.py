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
        for relative in ("scripts/research_site_sync.py", "scripts/recover_dr_packs.py", "scripts/research_transaction.py", "scripts/publish_scrub.py",
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

    def test_skill_summary_map_and_build_tree_publish_only_sanitized_prose(self):
        private_path = "/Users/" + "operator/private/notes"
        private_name = "Private" + "Workspace"
        text = "Use " + private_path + " for " + private_name + "."
        root = {**node("Root", "root"), "skillId": "root-skill"}
        for base in (self.repo, self.hub):
            (base / "concept-tree/tree.json").write_text(json.dumps([root]))
        summaries = self.repo / "concept-tree/skill-summaries.json"
        summaries.write_text(json.dumps({"inherited-skill": text}))
        skill = self.repo / ".agents/skills/root-skill/SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text("# Root\n" + text)
        with patch.dict("os.environ", {"PRIVACY_DENYLIST": private_name}):
            website.sync(self.repo, self.hub, apply=True)
        values = json.loads(summaries.read_text())
        self.assertEqual(values["inherited-skill"], values["root-skill"])
        self.assertIn("~/private/notes", values["root-skill"])
        for path in (summaries, self.repo / "site/src/data/tree.json"):
            self.assertNotIn(private_path, path.read_text())
            self.assertNotIn(private_name, path.read_text())
        self.assertIn(private_path, skill.read_text(), "private skill evidence stays intact")

    def test_node_summary_is_sanitized_for_publication_without_changing_hub_prose(self):
        home = "/Users/" + "operator/private/notes"
        email = "person@" + "research-customer.dev"
        summary = f"Use {home}. Contact {email}. PrivateWorkspace. " + "Evidence. " * 80
        record = {**node("Root", "root"), "summary": summary}
        (self.hub / "concept-tree/tree.json").write_text(json.dumps([record]))
        with patch.dict("os.environ", {"PRIVACY_DENYLIST": "PrivateWorkspace"}):
            website.sync(self.repo, self.hub, apply=True)
        self.assertEqual(json.loads((self.hub / "concept-tree/tree.json").read_text())[0]["summary"], summary)
        public = json.loads((self.repo / "concept-tree/tree.json").read_text())[0]["summary"]
        self.assertGreater(len(public), 400, "node summaries retain their complete text")
        for path in (self.repo / "concept-tree/tree.json", self.repo / "site/src/data/tree.json"):
            self.assertNotIn(home, path.read_text())
            self.assertNotIn(email, path.read_text())
            self.assertNotIn("PrivateWorkspace", path.read_text())

    def test_newer_alternate_pack_survives_canonical_title_normalization_in_both_orders(self):
        directory = self.repo / "site/src/data/concepts"
        alternate, canonical = directory / "alternate.json", directory / "canonical.json"
        original_glob = Path.glob
        for order in ((alternate, canonical), (canonical, alternate)):
            with self.subTest(order=[path.stem for path in order]):
                record = {**node("Canonical concept", "canonical"), "aliases": ["Old concept"]}
                for root in (self.repo, self.hub):
                    (root / "concept-tree/tree.json").write_text(json.dumps([record]))
                alternate.write_text(json.dumps({**reader("Old concept", "alternate", "Newer evidence."), "generated": "2026-10-21"}))
                canonical.write_text(json.dumps(reader("Canonical concept", "canonical", "Obsolete evidence.")))
                def ordered_glob(path, pattern, *args, order=order, **kwargs):
                    return iter(order) if path == directory and pattern == "*.json" else original_glob(path, pattern, *args, **kwargs)
                with patch.object(Path, "glob", ordered_glob):
                    website.sync(self.repo, self.hub, apply=True)
                pack = json.loads(canonical.read_text())
                self.assertEqual(pack["generated"], "2026-10-21")
                self.assertIn("Newer evidence.", canonical.read_text())
                self.assertNotIn("Obsolete evidence.", canonical.read_text())
                self.assertFalse(alternate.exists())
                self.assertIn("Newer evidence.", (self.repo / "site/public/downloads/concepts/alternate.md").read_text())

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
        self.assertFalse(local_pack.exists(), "excluded pack must not leave an empty destination")
        self.assertTrue((self.hub / "llms-concepts/generic-descendant.llms/manifest.json").exists())
        self.assertEqual(result["website_packs_after"], 0)
        self.assertTrue((self.repo / result["backup"] / "repository/outputs/llms-concepts/generic-descendant.llms/manifest.json").exists())

    def test_legacy_empty_excluded_repository_pack_is_removed(self):
        private = node("Private Topic", "private-topic")
        (self.hub / "concept-tree/tree.json").write_text(json.dumps([private]))
        empty = self.repo / "outputs/llms-concepts/private-topic.llms"
        (empty / "nested").mkdir(parents=True)
        with patch.dict("os.environ", {"PRIVACY_DENYLIST": "Private Topic"}):
            preview = website.sync(self.repo, self.hub)
            self.assertTrue(empty.exists(), "preview must keep the directory")
            self.assertIn("outputs/llms-concepts/private-topic.llms", preview["changed_files"])
            receipt = website.sync(self.repo, self.hub, apply=True)
        self.assertFalse(empty.exists())
        self.assertTrue((self.repo / receipt["backup"] / "repository/outputs/llms-concepts/private-topic.llms/nested").is_dir())

    def test_private_descendant_name_and_slug_aliases_cannot_reenter_publication(self):
        private = node("Private Topic", "private-topic", children=["Canonical child"])
        child = {**node("Canonical child", "canonical-child", parent="Private Topic"),
                 "aliases": ["Old child"], "slugAliases": ["old-child"]}
        (self.hub / "concept-tree/tree.json").write_text(json.dumps([private, child]))
        stale = node("Old child", "old-child", children=["Legacy descendant"])
        descendant = node("Legacy descendant", "legacy-descendant", parent="Old child")
        (self.repo / "concept-tree/tree.json").write_text(json.dumps([stale, descendant]))
        readers = self.repo / "site/src/data/concepts"
        (readers / "old-child.json").write_text(json.dumps(reader("Unrecorded editorial title", "old-child")))
        (readers / "older-editorial.json").write_text(json.dumps(reader("Old child", "older-editorial")))
        self.save_pack("Old child", "old-child")
        repository_pack = self.repo / "outputs/llms-concepts/old-child.llms"
        shutil.copytree(self.hub / "llms-concepts/old-child.llms", repository_pack)
        with patch.dict("os.environ", {"PRIVACY_DENYLIST": "Private Topic"}):
            receipt = website.sync(self.repo, self.hub, apply=True)
        self.assertFalse((readers / "old-child.json").exists())
        self.assertFalse((readers / "older-editorial.json").exists())
        self.assertFalse(repository_pack.exists())
        self.assertTrue((self.hub / "llms-concepts/old-child.llms/manifest.json").is_file())
        self.assertEqual(receipt["website_packs_after"], 0)
        for path in (self.repo / "concept-tree/tree.json", self.repo / "site/src/data/tree.json",
                     self.repo / "site/src/data/context.json", self.repo / "site/public/search-keywords.json"):
            self.assertNotIn("Old child", path.read_text())
            self.assertNotIn("Legacy descendant", path.read_text())

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

    def test_alias_backed_rename_keeps_url_placement_and_tree_references(self):
        old = node("Old name", "stable-url", parent="Root", children=["Child"])
        child = node("Child", "child", parent="Old name")
        root = node("Root", "root", children=["Old name"])
        renamed = {**old, "concept": "New name", "aliases": ["Old name"]}
        for base, nodes in ((self.repo, [root, old, child]),
                            (self.hub, [root, renamed, {**child, "parentConcept": "New name"}])):
            (base / "concept-tree/tree.json").write_text(json.dumps(nodes))
        (self.repo / "site/src/data/concepts/stable-url.json").write_text(json.dumps(reader("Old name", "stable-url")))
        website.sync(self.repo, self.hub, apply=True)
        for base in (self.repo, self.hub):
            nodes = {n["concept"]: n for n in json.loads((base / "concept-tree/tree.json").read_text())}
            self.assertNotIn("Old name", nodes)
            self.assertEqual(nodes["New name"]["slug"], "stable-url")
            self.assertEqual(nodes["New name"]["parentConcept"], "Root")
            self.assertEqual(nodes["Root"]["childConcepts"], ["New name"])
            self.assertEqual(nodes["Child"]["parentConcept"], "New name")
        self.assertEqual(json.loads((self.repo / "site/src/data/concepts/stable-url.json").read_text())["concept"], "New name")
        self.assertEqual(website.sync(self.repo, self.hub)["changed_files"], [])

    def test_fresh_shorter_same_day_correction_replaces_retired_reader_facts(self):
        self.save_pack()
        old = reader("New concept", "new-concept", "Retired unsupported statement.")
        old["facets"][0]["facts"].append({"text": "Another retired fact.", "source": "https://example.test/old"})
        path = self.repo / "site/src/data/concepts/new-concept.json"
        path.write_text(json.dumps(old))
        result = website.sync(self.repo, self.hub, apply=True, authoritative_slugs=["new-concept"])
        self.assertEqual(result["website_totals"]["facts"], 1)
        for target in (path, self.repo / "site/public/downloads/concepts/new-concept.md",
                       self.repo / "site/public/search-keywords.json"):
            self.assertIn("New finding.", target.read_text())
            self.assertNotIn("Retired", target.read_text())
        self.assertEqual(website.sync(self.repo, self.hub)["changed_files"], [])

    def test_canonicalization_retains_old_facts_download_without_duplicate_reader(self):
        for base in (self.repo, self.hub):
            (base / "concept-tree/tree.json").write_text(json.dumps([node("Canonical", "stable")]))
        (self.repo / "site/src/data/concepts/old.json").write_text(json.dumps(reader("Canonical", "old")))
        result = website.sync(self.repo, self.hub, apply=True)
        downloads = self.repo / "site/public/downloads/concepts"
        self.assertEqual((downloads / "old.md").read_text(), (downloads / "stable.md").read_text())
        self.assertFalse((self.repo / "site/src/data/concepts/old.json").exists())
        self.assertEqual(result["website_totals"]["concepts"], 1)
        self.assertEqual(website.sync(self.repo, self.hub)["changed_files"], [])
        with patch.dict("os.environ", {"PRIVACY_DENYLIST": "Canonical"}):
            website.sync(self.repo, self.hub, apply=True)
        self.assertFalse((downloads / "old.md").exists())
        self.assertFalse((downloads / "stable.md").exists())

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
