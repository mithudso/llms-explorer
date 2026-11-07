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
