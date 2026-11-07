"""One public domain: llms-explorer.com content redirects to llmsx.org.

AdSense and search judge one domain at a time. A legacy domain that answers 200
with every page canonicalized elsewhere looks like a duplicate site, so content
routes there answer 301. Account routes stay on llms-explorer.com because the
API session cookie (SameSite=Lax on api.llms-explorer.com) is not sent from a
llmsx.org page; llmsx.org sends them back with a temporary 302."""
import json
import subprocess
from pathlib import Path

MIDDLEWARE = Path(__file__).resolve().parents[1] / "functions" / "_middleware.ts"


def _requests(urls):
    script = f"""
      const {{ onRequest }} = await import({json.dumps(MIDDLEWARE.as_uri())});
      const rules = JSON.stringify({{ rules: [], tokens: {{}} }});
      const env = {{ ASSETS: {{ fetch: async () => new Response(rules) }} }};
      const out = [];
      for (const url of {json.dumps(urls)}) {{
        const res = await onRequest({{ request: new Request(url), env,
          next: async () => new Response("page") }});
        out.push({{ url, status: res.status, location: res.headers.get("Location"),
          cache: res.headers.get("Cache-Control") }});
      }}
      console.log(JSON.stringify(out));
    """
    run = subprocess.run(["node", "--input-type=module", "-e", script],
                         capture_output=True, text=True, check=True)
    return {r["url"]: r for r in json.loads(run.stdout.strip().splitlines()[-1])}


def test_legacy_content_routes_move_permanently_with_path_and_query():
    out = _requests([
        "https://llms-explorer.com/",
        "https://llms-explorer.com/tree/prompt-caching/?q=1",
        "https://www.llms-explorer.com/blog/post/",
        "https://llms-explorer.com/llms.txt",
        "https://www.llms-explorer.com/login/",
    ])
    assert out["https://llms-explorer.com/"]["status"] == 301
    assert out["https://llms-explorer.com/"]["location"] == "https://llmsx.org/"
    assert out["https://llms-explorer.com/tree/prompt-caching/?q=1"]["location"] == \
        "https://llmsx.org/tree/prompt-caching/?q=1"
    assert out["https://www.llms-explorer.com/blog/post/"]["location"] == "https://llmsx.org/blog/post/"
    assert out["https://llms-explorer.com/llms.txt"]["location"] == "https://llmsx.org/llms.txt"
    # www keeps account routes on the apex, where the API session works.
    assert out["https://www.llms-explorer.com/login/"]["location"] == "https://llms-explorer.com/login/"


def test_account_routes_stay_where_the_session_cookie_works():
    out = _requests([
        "https://llms-explorer.com/login/",
        "https://llms-explorer.com/account/",
        "https://llms-explorer.com/playground/optimizer/",
        "https://llms-explorer.com/.well-known/webauthn",
        "https://llmsx.org/login/",
        "https://llmsx.org/keys/?new=1",
    ])
    for url in ("https://llms-explorer.com/login/", "https://llms-explorer.com/account/",
                "https://llms-explorer.com/playground/optimizer/",
                "https://llms-explorer.com/.well-known/webauthn"):
        assert out[url]["status"] == 200, url
    assert out["https://llmsx.org/login/"]["status"] == 302
    assert out["https://llmsx.org/login/"]["location"] == "https://llms-explorer.com/login/"
    assert out["https://llmsx.org/login/"]["cache"] == "no-store"
    assert out["https://llmsx.org/keys/?new=1"]["location"] == "https://llms-explorer.com/keys/?new=1"


def test_canonical_previews_and_lookalike_routes_are_served():
    out = _requests([
        "https://llmsx.org/",
        "https://llmsx.org/tree/prompt-caching/",
        "https://llmsx.org/login-help/",
        "https://llmsx.org/.well-known/security.txt",
        "https://abc123.llms-explorer.pages.dev/",
        "http://127.0.0.1:8788/blog/",
    ])
    assert all(r["status"] == 200 for r in out.values()), out
