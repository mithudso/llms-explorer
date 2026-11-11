"""Daily publication and full-review pins over real temporary article files."""
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

import pytest

SITE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SITE / "tools"))
import promote_scheduled_posts as scheduler
from publication import is_published, metadata, publication_day, verify_research_review


def clock(day=12, hour=14):
    return dt.datetime(2026, 11, day, hour, tzinfo=dt.UTC)


@pytest.fixture
def site(tmp_path):
    root = tmp_path / "site"
    (root / "src/content/blog").mkdir(parents=True)
    return root


def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def article(site, slug="first", date="2026-11-12"):
    path = site / "scheduled-posts/research" / f"{slug}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f'---\ntitle: "Paper {slug}"\ndescription: "A bounded study"\n'
                    f'date: "{date}"\ncategory: research\n---\n\nA paper body.\n')
    report = site.parent / "docs/publication-reviews" / f"{slug}.md.ddo-report.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("# Test review fixture\n\n"
                      "Full review completed with no unresolved findings.\n")
    review = {"schema": "research-publication-review/v1", "status": "approved", "depth": "full",
              "document_sha256": checksum(path), "report_sha256": checksum(report),
              "report_path": report.relative_to(site.parent).as_posix(),
              "reviewed_at": "2026-11-11T16:00:00Z",
              "unresolved": {"blocking": 0, "major": 0, "medium": 0}}
    approval = site / "research-reviews" / f"{slug}.json"
    approval.parent.mkdir(parents=True, exist_ok=True)
    approval.write_text(json.dumps(review))
    return path, approval, report


def test_backlog_publishes_one_each_day_and_rerun_keeps_the_slot(site):
    first, _, _ = article(site, "first", "2026-11-10")
    second, _, _ = article(site, "second", "2026-11-11")
    third, _, _ = article(site, "third", "2026-11-12")
    original = first.read_bytes()
    promoted = scheduler.promote(site, now=clock())
    assert [p["slug"] for p in promoted] == ["research/first"]
    assert promoted[0]["published_on"] == "2026-11-12"
    assert promoted[0]["scheduled_for"] == "2026-11-10"
    assert (site / "src/content/blog/research/first.md").read_bytes() == original
    assert not first.exists() and second.exists() and third.exists()
    assert scheduler.promote(site, now=clock(hour=20)) == []
    # UTC has moved to the 13th, but New York still has the same daily slot.
    assert scheduler.promote(site, now=clock(day=13, hour=3)) == []
    assert [p["slug"] for p in scheduler.promote(site, now=clock(day=13))] == ["research/second"]
    assert [p["slug"] for p in scheduler.promote(site, now=clock(day=14))] == ["research/third"]
    assert len(scheduler.read_ledger(site)["entries"]) == 3


def test_before_nine_and_future_articles_do_not_publish(site):
    path, _, _ = article(site)
    assert scheduler.promote(site, now=clock(hour=13)) == []
    assert path.exists() and not scheduler.ledger_path(site).exists()
    future, _, _ = article(site, "future", "2026-11-20")
    assert [p["slug"] for p in scheduler.promote(site, now=clock())] == ["research/first"]
    assert future.exists()


def test_manually_published_today_article_consumes_the_daily_slot(site):
    pending, _, _ = article(site)
    live = site / "src/content/blog/manual.md"
    live.write_text('---\ntitle: "Manual"\ndate: "2026-11-12"\n---\nBody.\n')
    assert scheduler.promote(site, now=clock()) == []
    assert pending.exists()


@pytest.mark.parametrize("change", ["document", "report", "depth", "status", "findings", "missing"])
def test_only_exact_full_approved_research_can_publish(site, change):
    path, approval, report = article(site)
    review = json.loads(approval.read_text())
    if change == "document":
        path.write_text(path.read_text() + "Changed after review.\n")
    elif change == "report":
        report.write_text(report.read_text() + "Changed report.\n")
    elif change == "depth":
        review["depth"] = "quick"
    elif change == "status":
        review["status"] = "partial"
    elif change == "findings":
        review["unresolved"]["medium"] = 1
    if change == "missing":
        approval.unlink()
    else:
        approval.write_text(json.dumps(review))
    with pytest.raises(ValueError):
        scheduler.promote(site, now=clock())
    assert path.exists()
    assert not (site / "src/content/blog/research/first.md").exists()
    assert not scheduler.ledger_path(site).exists()


def test_destination_conflict_preserves_both_sources(site):
    path, _, _ = article(site)
    destination = site / "src/content/blog/research/first.md"
    destination.parent.mkdir(parents=True)
    destination.write_text("Already published different content.\n")
    with pytest.raises(ValueError, match="refusing overwrite"):
        scheduler.promote(site, now=clock())
    assert path.exists() and destination.read_text() == "Already published different content.\n"
    assert not scheduler.ledger_path(site).exists()


def test_edit_after_review_verification_cannot_replace_the_approved_pin(site, monkeypatch):
    path, approval, _ = article(site)
    approved = json.loads(approval.read_text())["document_sha256"]
    verify = scheduler.verify_research_review

    def edit_after_verification(*args):
        review = verify(*args)
        path.write_text(path.read_text() + "Unreviewed concurrent edit.\n")
        return review

    monkeypatch.setattr(scheduler, "verify_research_review", edit_after_verification)
    with pytest.raises(ValueError, match="changed"):
        scheduler.promote(site, now=clock())
    assert path.exists() and checksum(path) != approved
    assert not (site / "src/content/blog/research/first.md").exists()
    assert not scheduler.ledger_path(site).exists()


def test_failed_receipt_write_rolls_back_only_its_new_destination(site, monkeypatch):
    path, _, _ = article(site)
    before = path.read_bytes()

    def fail(*_):
        raise OSError("simulated ledger write failure")

    monkeypatch.setattr(scheduler, "_write_ledger", fail)
    with pytest.raises(OSError, match="simulated"):
        scheduler.promote(site, now=clock())
    assert path.read_bytes() == before
    assert not (site / "src/content/blog/research/first.md").exists()


def test_interrupted_unlink_recovers_acknowledged_bytes_before_next_day(site):
    path, _, _ = article(site, "first", "2026-11-10")
    article(site, "second", "2026-11-11")
    scheduler.promote(site, now=clock())
    destination = site / "src/content/blog/research/first.md"
    path.write_bytes(destination.read_bytes())  # Simulate a crash before source unlink.
    promoted = scheduler.promote(site, now=clock(day=13))
    assert [p["slug"] for p in promoted] == ["research/second"]
    assert not path.exists()
    assert len(scheduler.read_ledger(site)["entries"]) == 2


def test_dry_run_retains_every_file_and_receipt_state(site):
    path, _, _ = article(site)
    assert len(scheduler.promote(site, now=clock(), dry_run=True)) == 1
    assert path.exists() and not scheduler.ledger_path(site).exists()
    assert not (site / "src/content/blog/research/first.md").exists()


def test_review_cannot_point_to_a_report_outside_repository(site):
    path, approval, _ = article(site)
    review = json.loads(approval.read_text())
    review["report_path"] = "../outside.md"
    approval.write_text(json.dumps(review))
    with pytest.raises(ValueError, match="repository file"):
        verify_research_review(site, Path("first.md"), path)


def test_frontmatter_scope_and_shared_future_predicate():
    data = metadata('---\ntitle: "Future"\ndate: "2099-01-01"\n---\ndate: "2000-01-01"\n')
    assert data["date"] == "2099-01-01"
    assert not is_published(data, dt.date(2026, 11, 12))
    assert not is_published({"draft": "true"}, dt.date(2026, 11, 12))
    assert is_published({}, dt.date(2026, 11, 12))
    assert publication_day(clock(day=13, hour=3)).isoformat() == "2026-11-12"
    with pytest.raises(ValueError, match="timezone"):
        publication_day(dt.datetime(2026, 11, 12))


def pinned_image(site, approval, slug="first"):
    source = site / "scheduled-assets/research" / slug / "figure.png"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(b"\x89PNG\r\n\x1a\nexact reviewed image fixture")
    row = {"path": f"research/{slug}/figure.png", "sha256": checksum(source),
           "bytes": source.stat().st_size}
    review = json.loads(approval.read_text())
    review["assets"] = [row]
    approval.write_text(json.dumps(review))
    return source, site / "public/downloads" / row["path"], row


def test_images_wait_for_the_paper_day_and_keep_exact_pins(site):
    paper, approval, _ = article(site)
    source, destination, row = pinned_image(site, approval)
    expected = source.read_bytes()
    assert scheduler.promote(site, now=clock(day=11)) == []
    assert source.exists() and not destination.exists()
    result = scheduler.promote(site, now=clock())
    assert result[0]["assets"] == [row]
    assert destination.read_bytes() == expected
    assert not source.exists() and not paper.exists()
    assert scheduler.promote(site, now=clock(hour=20)) == []


@pytest.mark.parametrize("change", ["changed", "missing", "foreign-paper"])
def test_bad_image_bindings_cannot_publish_a_paper(site, change):
    paper, approval, _ = article(site)
    source, destination, _ = pinned_image(site, approval)
    if change == "changed":
        source.write_bytes(b"changed after review")
    elif change == "missing":
        source.unlink()
    else:
        review = json.loads(approval.read_text())
        review["assets"][0]["path"] = "research/another/figure.png"
        approval.write_text(json.dumps(review))
    with pytest.raises(ValueError):
        scheduler.promote(site, now=clock())
    assert paper.exists() and not destination.exists()
    assert not (site / "src/content/blog/research/first.md").exists()


def test_image_and_article_rollback_preserves_queued_sources(site, monkeypatch):
    paper, approval, _ = article(site)
    source, destination, _ = pinned_image(site, approval)

    def fail(*_):
        raise OSError("receipt failure")

    monkeypatch.setattr(scheduler, "_write_ledger", fail)
    with pytest.raises(OSError, match="receipt failure"):
        scheduler.promote(site, now=clock())
    assert paper.exists() and source.exists() and not destination.exists()
    assert not (site / "src/content/blog/research/first.md").exists()


def test_image_destinations_never_replace_an_existing_file(site):
    paper, approval, _ = article(site)
    source, destination, _ = pinned_image(site, approval)
    destination.parent.mkdir(parents=True)
    expected = source.read_bytes()
    destination.write_bytes(expected)
    with pytest.raises(ValueError, match="new destinations"):
        scheduler.promote(site, now=clock())
    assert paper.exists() and source.exists() and destination.read_bytes() == expected


def test_postbuild_rejects_early_publication_of_a_reviewed_image(site):
    from check_publication import check
    import shutil

    _, approval, _ = article(site)
    source, destination, _ = pinned_image(site, approval)
    destination.parent.mkdir(parents=True)
    shutil.copyfile(source, destination)
    with pytest.raises(ValueError, match="images leaked"):
        check(site / "dist", site=site)
