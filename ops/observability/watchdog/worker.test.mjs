import test from "node:test";
import assert from "node:assert/strict";
import {createServer} from "node:http";
import {probe, handle} from "./worker.mjs";

test("external watchdog detects real HTTP login redirects and verifies JSON readiness", async () => {
  const server = createServer((req, res) => {
    if (req.url === "/redirect") {res.writeHead(302, {location: "/login"}); res.end();}
    else if (req.url === "/login") {res.writeHead(200, {"Content-Type": "text/html"}); res.end("<title>Cloudflare Access</title>");}
    else if (req.url === "/malformed") {res.writeHead(200, {"Content-Type": "application/json"}); res.end("not-json");}
    else {res.writeHead(200, {"Content-Type": "application/json"}); res.end(JSON.stringify({status: "ready"}));}
  });
  await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
  const base = `http://127.0.0.1:${server.address().port}`;
  try {
    assert.equal((await probe({name: "test", url: base + "/redirect", phase: "production"})).success, 0);
    assert.equal((await probe({name: "test", url: base + "/login", phase: "production"})).success, 0);
    assert.equal((await probe({name: "test", url: base + "/malformed", phase: "production", expect: {status: "ready"}})).success, 0);
    assert.equal((await probe({name: "test", url: base, phase: "production", expect: {status: "ready"}})).success, 1);
    assert.equal((await probe({name: "test", url: base, phase: "production", expect: {status: "ok"}})).success, 0);
  } finally {await new Promise(resolve => server.close(resolve));}
});

test("metrics and history require authentication, and missing checks remain unknown", async () => {
  const env = {WATCHDOG_TOKEN: "fixture-secret", RELEASE_SHA: "fixture", DB: {prepare() {return {async all() {return {results: []};}};}}};
  assert.equal((await handle(new Request("https://watchdog.example/metrics"), env)).status, 401);
  assert.equal((await handle(new Request("https://watchdog.example/metrics", {headers: {Authorization: "Bearer wrong"}}), env)).status, 401);
  const response = await handle(new Request("https://watchdog.example/metrics", {headers: {Authorization: "Bearer fixture-secret"}}), env);
  assert.equal(response.status, 200);
  const body = await response.text();
  assert.match(body, /fleet_watchdog_checked_timestamp_seconds\{project="llmsx",phase="production"\} 0/);
  assert.doesNotMatch(body, /fleet_watchdog_success\{/);
});
