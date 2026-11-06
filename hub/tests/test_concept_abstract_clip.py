"""concept_abstract.clip_text never splits a URL (MongoDB KB correction C2).

llms-full.txt shortens extractive passages to 600 characters. The old cut was `text[:600]`,
which left fragments such as `.../atlas-operator/ak8so-change` that look like real, dead URLs.
"""

import importlib.util
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / ".claude/skills/llms-concept-abstractor/scripts/concept_abstract.py"
spec = importlib.util.spec_from_file_location("concept_abstract_under_test", SCRIPT)
lca = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lca)

URL = "https://www.mongodb.com/docs/atlas/operator/current/ak8so-changelog/"


def urls(text):
    return re.findall(r"https?://\S+", text)


def test_short_text_is_unchanged():
    assert lca.clip_text("short https://a.example/x", 600) == "short https://a.example/x"


def test_plain_text_cuts_at_limit():
    assert lca.clip_text("a" * 50, 10) == "a" * 10


def test_url_straddling_the_cut_is_dropped_whole():
    text = "Deletion protection is the default. Sources: " + URL + " and more words"
    for limit in range(len("Deletion protection is the default. Sources: "), len(text)):
        out = lca.clip_text(text, limit)
        assert len(out) <= limit
        assert all(u in text.split() for u in urls(out)), (limit, out)
        assert not out.endswith(("Sources:", ";", "—"))


def test_url_fully_inside_the_limit_is_kept():
    text = "Claim. " + URL + " tail text that is long"
    assert URL in lca.clip_text(text, len("Claim. " + URL) + 3)


def test_long_passage_keeps_only_complete_urls():
    text = ("x " * 280) + "— " + URL + " ; " + URL.replace("changelog", "import") + " end"
    out = lca.clip_text(text, 600)
    assert len(out) <= 600
    assert set(urls(out)) <= set(urls(text))
