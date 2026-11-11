import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from skill_registry.bundles import build_bundle
from skill_registry.client import Remote, token_from_environment


@pytest.mark.parametrize("url", ["http://example.com", "file:///tmp/x", "https://user:pass@example.com", "https://example.com/#fragment"])
def test_remote_urls_do_not_leak_tokens_or_allow_plain_remote_http(tmp_path, url):
    with pytest.raises(ValueError):
        Remote(url, "synthetic-test-token", tmp_path)


def test_private_remote_fetch_is_verified_and_available_offline(skill, tmp_path):
    manifest, data = build_bundle(skill, "usr_test", "example", "1.0.0")
    observed = []
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            assert self.path == "/api/skill-registry/releases/usr_test/example/1.0.0/bundle.zip"
            assert self.headers["User-Agent"].startswith("skill-registry/")
            observed.append(self.headers["Authorization"])
            self.send_response(200)
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *_):
            pass
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        remote = Remote(f"http://127.0.0.1:{server.server_port}", "synthetic-test-token", tmp_path / "cache")
        result = remote.fetch("usr_test", "example", "1.0.0", manifest["release_sha256"])
        assert result["offline_available"]
        with pytest.raises(ValueError, match="pin"):
            remote.fetch("usr_test", "example", "1.0.0", "0" * 64)
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
    remote.install_cached(manifest["release_sha256"], tmp_path / "offline-install")
    assert (tmp_path / "offline-install/SKILL.md").is_file()
    assert observed == ["Bearer synthetic-test-token"] * 2


def test_redirects_are_refused_before_credentials_follow(tmp_path):
    observed = []
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            observed.append(self.path)
            self.send_response(302)
            self.send_header("Location", "/different-origin-surface")
            self.end_headers()

        def log_message(self, *_):
            pass
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        remote = Remote(f"http://127.0.0.1:{server.server_port}", "synthetic-test-token", tmp_path)
        with pytest.raises(ValueError, match="redirects"):
            remote.search("example")
        assert len(observed) == 1
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_credential_file_must_be_private(tmp_path, monkeypatch):
    path = tmp_path / "credential"
    path.write_text("synthetic-test-token")
    monkeypatch.setenv("SKILL_REGISTRY_TOKEN_FILE", str(path))
    path.chmod(0o644)
    with pytest.raises(ValueError, match="mode 600"):
        token_from_environment()
    path.chmod(0o600)
    assert token_from_environment() == "synthetic-test-token"


def test_public_publish_is_explicitly_unavailable(skill, tmp_path):
    _, data = build_bundle(skill, "usr_test", "example", "1.0.0")
    with pytest.raises(ValueError, match="moderation"):
        Remote("http://127.0.0.1", "synthetic-test-token", tmp_path).publish(data, visibility="public")
