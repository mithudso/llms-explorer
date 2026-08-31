# site/tests/test_gen_demo.py
# ruff: noqa: E501  -- asserted spans are real recorded values; wrapping changes what is tested
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SITE / "tools"))
import gen_demo  # noqa: E402


class FakeStore:
    """The docset's model is NOT the pool default — the bug this file guards."""

    def __init__(self):
        self.calls = []

    def docset_model(self, key):
        return "docset-model"


def test_warm_up_uses_the_model_the_recording_queries_with():
    """The warm-up embedded with `embed_core.embed_model()` (the HUB_EMBED_MODEL
    default) while record() queries with `store.docset_model(key)`. When the two
    differ the wrong weights are loaded and the first recorded vector leg pays
    the model load anyway — a load filed under "vector" is a false claim about
    retrieval latency."""
    seen = []

    def embed(texts, model=None):
        seen.append((tuple(texts), model))
        return [[0.1] for _ in texts]

    questions = [{"q": "a", "kind": "exact-token"}, {"q": "b", "kind": "paraphrase"}]
    model = gen_demo.warm(FakeStore(), "d__facts", questions, embed)
    assert model == "docset-model"
    assert [m for _, m in seen] == ["docset-model", "docset-model"]   # never the pool default
    assert all(texts == ("a", "b") for texts, _ in seen)              # the whole question set


def test_warm_runs_more_than_once_so_connection_setup_is_not_timed():
    """The first call pays the model load AND opening the connection; only the
    second is the steady state the page publishes."""
    seen = []
    gen_demo.warm(FakeStore(), "k", [{"q": "a", "kind": "exact-token"}],
                  lambda texts, model=None: seen.append(model) or [[0.1]])
    assert len(seen) >= 2
    assert gen_demo.warm(FakeStore(), "k", [{"q": "a", "kind": "exact-token"}],
                         lambda texts, model=None: seen.append(model) or [[0.1]], rounds=1)
