import test from "node:test";
import assert from "node:assert/strict";
import {createServer} from "node:http";
import {alertTransitions, configuredTargets, probe, handle, targetsForMinute} from "./worker.mjs";

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

const baseTarget = {name: "fixture-monitor", phase: "production", url: "https://example.com/app", interval: 2};

test("validates monitoring configuration and spreads recurring probes across minutes", () => {
  const values = JSON.stringify([baseTarget]);
  const all = configuredTargets(values);
  assert.equal(all.at(-1).name, baseTarget.name);
  assert.equal([0, 1].filter(minute => targetsForMinute(all, minute).some(t => t.name === baseTarget.name)).length, 1);
  assert.throws(() => configuredTargets(JSON.stringify([{...baseTarget, url: "https://example.com/?credential=example"}])), /invalid_watchdog_url/);
  assert.throws(() => configuredTargets(JSON.stringify([baseTarget, baseTarget])), /invalid_watchdog_target/);
});

test("requires explicit access redirects or denial and checks nested readiness", async () => {
  const protectedTarget = {...baseTarget, redirect: {host: "auth.example.com", path: "/login"}};
  const reply = (res) => async () => res;
  assert.equal((await probe(protectedTarget, reply(Response.redirect("https://auth.example.com/login?state=example")))).success, 1);
  assert.equal((await probe(protectedTarget, reply(Response.redirect("https://elsewhere.example.com/login")))).success, 0);
  assert.equal((await probe({...baseTarget, status: [401]}, reply(new Response(null, {status: 401})))).success, 1);
  assert.equal((await probe({...baseTarget, status: [401]}, reply(new Response("leak")))).success, 0);
  const contract = {...baseTarget, expect: {checks: {database: true}}};
  assert.equal((await probe(contract, reply(Response.json({checks: {database: true, extra: true}})))).success, 1);
  assert.equal((await probe(contract, reply(Response.json({checks: {database: false}})))).success, 0);
});

test("checks DNS delegation against the approved nameservers", async () => {
  const target = {name: "fixture-dns", phase: "production", dns: "example.com", nameservers: ["ns1.example.net", "ns2.example.net"]};
  let requested;
  const query = async url => {
    requested = url;
    return Response.json({Status: 0, Answer: target.nameservers.map(data => ({name: "example.com.", type: 2, data: data + "."}))});
  };
  assert.equal((await probe(target, query)).success, 1);
  assert.equal(requested.searchParams.get("type"), "NS");
  assert.equal((await probe({...target, nameservers: ["unapproved.example.net"]}, query)).success, 0);
});

test("alerts after three failures and recovers after two passes, with no repeats", () => {
  const check = {...baseTarget, success: 0, status: 503};
  const checkState = (history, firing, current=check) => alertTransitions([{name: check.name, history, firing}], [current]);
  assert.deepEqual(checkState("00", null), []);
  assert.deepEqual(checkState("000", null).map(c => c.firing), [1]);
  assert.deepEqual(checkState("000", 1), []);
  assert.deepEqual(checkState("100", 1), []);
  assert.deepEqual(checkState("110", 1, {...check, success: 1, status: 200}).map(c => c.firing), [0]);
  assert.deepEqual(checkState("000", null, {...check, phase: "staging"}), []);
});
