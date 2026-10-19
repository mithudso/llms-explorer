# site/tests/test_queue_page.py
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
DIST = SITE / "dist"


def test_queue_page_reads_the_live_monitor_endpoint():
    html = (DIST / "queue" / "index.html").read_text()
    assert 'id="queue-monitor" data-api="https://' in html
    assert "/api/research/queue" in html
    assert "innerHTML" not in html, "concept names are rendered as text, never markup"


def test_queue_page_is_linked_and_has_a_twin():
    assert (DIST / "queue.md").is_file()
    assert 'href="/queue/"' in (DIST / "tree" / "index.html").read_text()
