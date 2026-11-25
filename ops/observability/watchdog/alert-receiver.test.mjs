import assert from "node:assert/strict";
import test from "node:test";
import {receiveAlert} from "./alert-receiver.mjs";

const p = {account_id: "test-account", alert_type: "tunnel_health_event", policy_id: "test-policy", ts: 1730000000, data: {tunnel_id: "test-tunnel"}, text: "Ignored"};
const setup = () => {
  const events = new Map();
  const env = {
    CLOUDFLARE_ACCOUNT_ID: "test-account",
    CLOUDFLARE_WEBHOOK_TOKEN: "cloud-fixture",
    SYNTHETIC_WEBHOOK_TOKEN: "synthetic-fixture",
    DB: {prepare() {return {bind(now, value) {return {async run() {
      for (const event of JSON.parse(value)) if (!events.has(event.id)) events.set(event.id, event);
    }};}};}},
  };
  return {events, env};
};

const req = (path, token, payload) => new Request("https://example.com" + path, {
  method: "POST", headers: {"cf-webhook-auth": token, "content-type": "application/json"},
  body: typeof payload === "string" ? payload : JSON.stringify(payload),
});

test("rejects unauthenticated callbacks, the wrong account, and excess body data", async () => {
  const {env, events} = setup();
  assert.equal((await receiveAlert(req("/cloudflare", "synthetic-fixture", p), env)).status, 401);
  assert.equal((await receiveAlert(req("/cloudflare", "cloud-fixture", {...p, account_id: "other"}), env)).status, 400);
  assert.equal((await receiveAlert(req("/cloudflare", "cloud-fixture", " ".repeat(65537)), env)).status, 413);
  assert.equal(events.size, 0);
});

test("records one actionable Cloudflare receipt when the provider retries", async () => {
  const {env, events} = setup();
  for (let i = 0; i < 2; i++) assert.equal((await receiveAlert(req("/cloudflare", "cloud-fixture", p), env)).status, 202);
  assert.equal(events.size, 1);
  const [event] = events.values();
  assert.equal(event.subject, "test-tunnel");
  assert.equal(event.action, "inspect_tunnel");
  assert.equal(event.text, undefined);
});

test("uses distinct transition receipts for synthetic failures and recoveries", async () => {
  const {env, events} = setup();
  const event = {name: "example-check", state: "firing", ts: 1730000000, status: 530};
  const payload = {events: [event, {...event, state: "resolved", status: 200}]};
  for (let i = 0; i < 2; i++) assert.equal((await receiveAlert(req("/synthetic", "synthetic-fixture", payload), env)).status, 202);
  assert.deepEqual([...events.values()].map(row => row.action), ["verify_probe", "close_incident"]);
});

test("accepts the provider verification callback without queuing a remediation action", async () => {
  const {env, events} = setup();
  const payload = {text: "Hello World! This is a test message sent from https://cloudflare.com."};
  assert.equal((await receiveAlert(req("/cloudflare", "cloud-fixture", payload), env)).status, 202);
  const [event] = events.values();
  assert.equal(event.action, "none");
});

test("retains authenticated notifications that omit optional provider metadata", async () => {
  const {env, events} = setup();
  const payload = {text: "Status changed", ts: 1730000000};
  for (const item of [payload, payload, {...payload, text: "Maintenance scheduled"}]) {
    assert.equal((await receiveAlert(req("/cloudflare", "cloud-fixture", item), env)).status, 202);
  }
  assert.equal(events.size, 2);
  for (const event of events.values()) {
    assert.equal(event.type, "unspecified");
    assert.equal(event.action, "review_account_event");
    assert.equal(event.text, undefined);
  }
});
