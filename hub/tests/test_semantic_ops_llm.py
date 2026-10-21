"""semantic_ops.llm.generate: pooled Ollama generation over the shared ollama-client library."""

import json
import urllib.error
from unittest import mock

import pytest
from semantic_ops import llm


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.delenv("HUB_LLM_URL", raising=False)
    monkeypatch.delenv("HUB_LLM_MODEL", raising=False)
    monkeypatch.setenv("HUB_OLLAMA_URLS", "http://gpu.example:11434=4,http://local.example:11434=1")
    import embed_core
    monkeypatch.setattr(embed_core, "_quiet", lambda url: False)


def _resp(payload):
    resp = mock.MagicMock()
    resp.read.return_value = json.dumps(payload).encode()
    resp.__enter__ = lambda s: s
    resp.__exit__ = lambda s, *a: False
    return resp


def test_generate_sends_model_options_and_think_to_the_first_host():
    seen = []

    def fake(req, timeout=None):
        seen.append((req.full_url, json.loads(req.data), timeout))
        return _resp({"response": "hello"})

    with mock.patch("urllib.request.urlopen", side_effect=fake):
        out = llm.generate("hi", model="m1", timeout=7, options={"temperature": 0}, think=False)
    assert out == "hello"
    url, body, timeout = seen[0]
    assert url == "http://gpu.example:11434/api/generate"          # highest weight first
    assert body == {"model": "m1", "prompt": "hi", "stream": False,
                    "options": {"temperature": 0}, "think": False}
    assert timeout == 7


def test_generate_fails_over_to_the_next_host_once():
    urls = []

    def fake(req, timeout=None):
        urls.append(req.full_url)
        if "gpu" in req.full_url:
            raise urllib.error.URLError("down")
        return _resp({"response": "from local"})

    with mock.patch("urllib.request.urlopen", side_effect=fake):
        assert llm.generate("hi", model="m") == "from local"
    assert urls == ["http://gpu.example:11434/api/generate",
                    "http://local.example:11434/api/generate"]


def test_generate_raises_llm_unavailable_when_every_host_fails():
    with mock.patch("urllib.request.urlopen", side_effect=urllib.error.URLError("down")), \
            pytest.raises(llm.LLMUnavailable):
        llm.generate("hi", model="m")


def test_an_empty_completion_is_a_failure():
    with mock.patch("urllib.request.urlopen", return_value=_resp({"response": ""})), \
            pytest.raises(llm.LLMUnavailable):
        llm.generate("hi", model="m")


def test_mesh_path_is_unchanged(monkeypatch):
    monkeypatch.setenv("HUB_LLM_URL", "http://mesh.example/v1")
    seen = []

    def fake(req, timeout=None):
        seen.append((req.full_url, json.loads(req.data)))
        return _resp({"choices": [{"message": {"content": "mesh says hi"}}]})

    with mock.patch("urllib.request.urlopen", side_effect=fake):
        assert llm.generate("hi", options={"temperature": 0.2, "num_predict": 9}) == "mesh says hi"
    assert seen[0][0] == "http://mesh.example/v1/chat/completions"
    assert seen[0][1]["model"] == "research" and seen[0][1]["max_tokens"] == 9
