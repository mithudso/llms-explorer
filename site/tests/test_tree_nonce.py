"""Exercise the Pages Function's fresh challenge nonce and policy boundaries."""
import base64
import json
import re
import subprocess
from pathlib import Path


MIDDLEWARE = Path(__file__).resolve().parents[1] / "functions" / "_middleware.ts"


def test_tree_nonce_is_fresh_per_response_and_preserves_the_cached_policy():
    policy = "default-src 'self'; script-src 'self' 'sha256-test=' https: 'wasm-unsafe-eval'; object-src 'none'"
    script = f"""
      const {{ onRequest }} = await import({json.dumps(MIDDLEWARE.as_uri())});
      const policy = {json.dumps(policy)};
      const edge = {{ rules: [{{ pattern: '/*', headers: [['Content-Security-Policy', policy]] }}], tokens: {{}} }};
      let fetches = 0;
      const env = {{ ASSETS: {{ fetch: async () => {{
        fetches++;
        return new Response(JSON.stringify(edge));
      }} }} }};
      const out = [];
      for (const [path, type] of [
        ['/tree/', 'text/html; charset=utf-8'], ['/tree/', 'text/html'],
        ['/account/', 'text/html'], ['/tree/concept/', 'text/html'],
        ['/tree/', 'text/markdown'], ['/tree.md', 'text/markdown'],
      ]) {{
        const res = await onRequest({{
          request: new Request('https://llms-explorer.com' + path), env,
          next: async () => new Response('body', {{ headers: {{ 'Content-Type': type }} }}),
        }});
        out.push({{ path, type, policy: res.headers.get('Content-Security-Policy'), body: await res.text() }});
      }}
      console.log(JSON.stringify({{ out, fetches, edge }}));
    """
    run = subprocess.run(["node", "--input-type=module", "-e", script],
                         capture_output=True, text=True, check=True)
    data = json.loads(run.stdout)
    first, second, *untouched = data["out"]
    nonces = []
    for response in (first, second):
        nonce = re.search(r" 'nonce-([^']+)'", response["policy"]).group(1)
        assert len(base64.b64decode(nonce, validate=True)) == 16
        assert response["policy"].replace(f" 'nonce-{nonce}'", "") == policy
        assert response["body"] == "body"
        nonces.append(nonce)
    assert nonces[0] != nonces[1]
    assert all(response["policy"] == policy for response in untouched)
    assert data["fetches"] == 1
    assert data["edge"]["rules"][0]["headers"][0][1] == policy


def test_nonce_does_not_invent_a_missing_script_policy():
    script = f"""
      const {{ authorizeTreeChallenge }} = await import({json.dumps(MIDDLEWARE.as_uri())});
      const out = [];
      for (const policy of [null, "default-src 'self'; object-src 'none'"]) {{
        const headers = {{ 'Content-Type': 'text/html' }};
        if (policy !== null) headers['Content-Security-Policy'] = policy;
        const res = authorizeTreeChallenge('/tree/', new Response('body', {{ headers }}));
        out.push(res.headers.get('Content-Security-Policy'));
      }}
      console.log(JSON.stringify(out));
    """
    run = subprocess.run(["node", "--input-type=module", "-e", script],
                         capture_output=True, text=True, check=True)
    assert json.loads(run.stdout) == [None, "default-src 'self'; object-src 'none'"]
