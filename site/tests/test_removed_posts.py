"""Removed employer and customer posts must not come back.

On 2026-10-18 the owner removed blog posts, scheduled posts and drafts whose
subject was customer data or an internal employer process (PRs #191 and #193),
plus the pre-edit originals of posts that were neutralised. On 2026-10-19 a
backlog restore (PR #198) put every one of them back from a diverged local
checkout, and the publish-scheduled workflow then published the scheduled ones.
They were removed again on 2026-11-07 (Stele KNOW-1222, TASK-1223).

This guard fails CI if a file with any of those names reappears anywhere a post
can be published from. It stores truncated SHA-256 digests of the file stems,
not the titles, so the guard does not republish the names it protects against.
"""
import hashlib
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PUBLISHABLE = (
    REPO / "site" / "src" / "content" / "blog",
    REPO / "site" / "scheduled-posts",
    REPO / "docs" / "future_posts",
)
REMOVED = {
    "00a77d502c492bf4", "0687999b5c9d67a3", "19d51ffa1dd77564", "21b6efca06c74a0a",
    "25a5de045223b72e", "2b72b9d3bbaba602", "3e0ebd7f60095c66", "5029276e675dbabc",
    "512bd54672a25fcd", "51c5ce07225a6fd3", "5bbb2d3b5708e989", "6d03142d2b13d7c7",
    "705ff0dd48e94da4", "773431be74e715a5", "799cf23b91ea4f9d", "7b4e41624a957dca",
    "7cd8fa7068e6cea6", "7d611c74ef8db4de", "7f6992f6ff7dccba", "83ff15de7a83c09b",
    "875435fb48b7e6a0", "8f2a5b628a020d0d", "9219678635a4802b", "94dfdec91cd191ef",
    "9aeda3dd32f317c0", "9d989562cc258a82", "9e4a472a0f1c6a80", "9f25b73b16ee8713",
    "a24f9063ef85af3a", "a3db2ac8b3cfe154", "b5b9c119207e862d", "ce7bc5c31065b92b",
    "cf6490abe3cea67b", "d0d8d8592d465a09", "d3c36d604634f510", "dc06e134b50968d8",
    "dc7dd2dc30660815", "eca0f975f436059b", "ffb356142c28ce80",
}


def _digest(path: Path) -> str:
    stem = unicodedata.normalize("NFC", path.stem)
    return hashlib.sha256(stem.encode("utf-8")).hexdigest()[:16]


def test_removed_posts_and_drafts_stay_removed():
    back = [str(p.relative_to(REPO))
            for root in PUBLISHABLE if root.is_dir()
            for p in root.rglob("*.md") if _digest(p) in REMOVED]
    assert not back, (
        "removed employer/customer posts reappeared; delete them again and check "
        f"whatever restored them (see this file's docstring): {back}")


def test_the_guard_recognises_a_removed_name(tmp_path):
    # A digest computed the same way as the guard must match: proves the hash
    # recipe in the test agrees with the one that produced REMOVED.
    probe = tmp_path / "from-discovery-to-the-board.md"
    probe.write_text("x")
    assert _digest(probe) in REMOVED


MIDDLEWARE = REPO / "site" / "functions" / "_middleware.ts"


def test_middleware_rejects_the_same_removed_posts():
    """Pages can serve a deleted page from a cache that neither a deploy nor a
    zone purge clears (2026-11-07: a removed post kept answering 200, age 10h),
    so the middleware answers 410 before the asset lookup. Its digest set must
    be this file's set, or a post could be guarded in source but served live."""
    import json
    import re
    import subprocess
    source = MIDDLEWARE.read_text(encoding="utf-8")
    block = source.split("export const REMOVED_POSTS = new Set([", 1)[1].split("]);", 1)[0]
    assert set(re.findall(r'"([0-9a-f]{16})"', block)) == REMOVED
    script = f"""
      const {{ onRequest }} = await import({json.dumps(MIDDLEWARE.as_uri())});
      const rules = JSON.stringify({{ rules: [], tokens: {{}} }});
      const env = {{ ASSETS: {{ fetch: async () => new Response(rules) }} }};
      const out = {{}};
      for (const path of ["/blog/from-discovery-to-the-board/", "/blog/from-discovery-to-the-board",
                          "/blog/from-discovery-to-the-board.md", "/blog/keyword-plus-vector/",
                          "/blog/%E0%A4%A/", "/blog/"]) {{
        const res = await onRequest({{ request: new Request("https://llmsx.org" + path), env,
          next: async () => new Response("page") }});
        out[path] = [res.status, res.headers.get("Cache-Control")];
      }}
      console.log(JSON.stringify(out));
    """
    run = subprocess.run(["node", "--input-type=module", "-e", script],
                         capture_output=True, text=True, check=True)
    out = json.loads(run.stdout.strip().splitlines()[-1])
    for path in ("/blog/from-discovery-to-the-board/", "/blog/from-discovery-to-the-board",
                 "/blog/from-discovery-to-the-board.md"):
        assert out[path] == [410, "no-store"], path
    for path in ("/blog/keyword-plus-vector/", "/blog/%E0%A4%A/", "/blog/"):
        assert out[path][0] == 200, path


def test_pre_push_hook_flags_purged_paths_only():
    """`.githooks/pre-push` refuses a push that would re-upload purged files
    (the way PR #198 undid the 2026-10-18 rewrite). It matches the purged set
    only: drafts deleted at the tip but kept in history must not trip it."""
    from importlib.machinery import SourceFileLoader
    from importlib.util import module_from_spec, spec_from_loader
    loader = SourceFileLoader("pre_push", str(REPO / ".githooks" / "pre-push"))
    hook = module_from_spec(spec_from_loader("pre_push", loader))
    loader.exec_module(hook)
    assert hook.purged("site/src/content/blog/from-discovery-to-the-board.md")
    assert hook.purged("site/scheduled-posts/from-discovery-to-the-board.md")
    assert hook.purged("docs/verification/blog-ddo-2026-09-30/summary.json")
    assert not hook.purged("docs/future_posts/18 - State That Survives the Session.md")
    assert not hook.purged("site/src/content/blog/keyword-plus-vector.md")
    assert (REPO / ".githooks" / "pre-push").stat().st_mode & 0o111, "hook must be executable"
