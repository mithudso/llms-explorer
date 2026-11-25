const maxBody = 65536;
const encoder = new TextEncoder();
const namePattern = /^[a-z][a-z0-9_-]{0,95}$/;
const idPattern = /^[a-zA-Z0-9_-]{1,96}$/;

async function digest(value) {
  return new Uint8Array(await crypto.subtle.digest("SHA-256", encoder.encode(value)));
}

async function validSecret(request, secret) {
  const provided = request.headers.get("cf-webhook-auth");
  if (!secret || !provided || provided.length > 256) return false;
  const [actual, expected] = await Promise.all([digest(provided), digest(secret)]);
  let difference = 0;
  for (let i = 0; i < expected.length; i++) difference |= actual[i] ^ expected[i];
  return difference === 0;
}

async function readJson(request) {
  const reader = request.body?.getReader();
  if (!reader) throw new Error("invalid_body");
  const data = new Uint8Array(maxBody);
  let size = 0;
  try {
    while (true) {
      const {value, done} = await reader.read();
      if (done) return JSON.parse(new TextDecoder().decode(data.subarray(0, size)));
      if (size + value.length > maxBody) throw new RangeError("body_limit");
      data.set(value, size);
      size += value.length;
    }
  } finally {
    await reader.cancel();
    reader.releaseLock();
  }
}

const actionFor = {
  tunnel_health_event: "inspect_tunnel",
  tunnel_update_event: "inspect_tunnel",
  universal_ssl_event_type: "inspect_certificate",
  leaked_service_token_alert: "inspect_service_token",
  expiring_service_token_alert: "inspect_service_token",
};

function normalizeSynthetic(events) {
  if (!Array.isArray(events) || events.length < 1 || events.length > 50) throw new Error("invalid_events");
  return events.map(event => {
    const {name, state, ts, status} = event ?? {};
    if (typeof name !== "string" || !namePattern.test(name) || !["firing", "resolved"].includes(state) ||
        !Number.isSafeInteger(ts) || ts <= 0 || !Number.isInteger(status) || status < 0 || status > 599) {
      throw new Error("invalid_event");
    }
    return {id: `synthetic:${name}:${ts}:${state}`, source: "synthetic", type: "probe", subject: name, state, ts, status,
      action: state === "firing" ? "verify_probe" : "close_incident"};
  });
}

async function normalizeCloudflare(input, env) {
  if (!input || typeof input !== "object" || Array.isArray(input)) throw new Error("invalid_event");
  const {text, account_id: accountId, alert_type: suppliedType, alert_event: event, policy_id: suppliedPolicy, alert_correlation_id: correlation, ts} = input;
  if (typeof text === "string" && !suppliedType && !suppliedPolicy && text.includes("test message sent from https://cloudflare.com")) {
    return [{id: "cloudflare:destination-test", source: "cloudflare", type: "destination_test", subject: "", state: "test",
      ts: Math.floor(Date.now() / 1000), status: 0, action: "none"}];
  }
  if ((accountId !== undefined && accountId !== env.CLOUDFLARE_ACCOUNT_ID) ||
      (suppliedType !== undefined && (typeof suppliedType !== "string" || !namePattern.test(suppliedType))) ||
      (suppliedPolicy !== undefined && (typeof suppliedPolicy !== "string" || !idPattern.test(suppliedPolicy))) ||
      !Number.isSafeInteger(ts) || ts <= 0 ||
      (!suppliedType && !suppliedPolicy && (typeof text !== "string" || !text.trim()))) throw new Error("invalid_event");
  const type = suppliedType ?? "unspecified";
  const policyId = suppliedPolicy ?? "";
  const state = ["ALERT_STATE_EVENT_END", "ALERT_STATE_EVENT_RESOLVED"].includes(event) ? "resolved" : "firing";
  const resource = input.data?.tunnel_id ?? input.data?.tunnel?.id ?? input.data?.zone_id ??
    input.data?.zone_tag ?? input.data?.token_id ?? input.data?.certificate_id ?? input.data?.health_check_id;
  const subject = typeof resource === "string" && idPattern.test(resource) ? resource : policyId;
  const episode = typeof correlation === "string" && idPattern.test(correlation) ? correlation : subject;
  const fingerprintSource = [policyId, episode, type, state, ts, !episode ? text : undefined];
  const fingerprint = Array.from(await digest(JSON.stringify(fingerprintSource)), byte => byte.toString(16).padStart(2, "0")).join("");
  return [{id: "cloudflare:" + fingerprint, source: "cloudflare", type, subject, state, ts, status: 0,
    action: state === "resolved" ? "close_incident" : Object.hasOwn(actionFor, type) ? actionFor[type] : "review_account_event"}];
}

export async function receiveAlert(request, env) {
  const {pathname} = new URL(request.url);
  if (pathname === "/health" && request.method === "GET") return Response.json({status: "ok", revision: env.RELEASE_SHA}, {headers: {"Cache-Control": "no-store"}});
  if (!["/cloudflare", "/synthetic"].includes(pathname)) return new Response("Not found", {status: 404});
  if (request.method !== "POST") return new Response("Method not allowed", {status: 405});
  const synthetic = pathname === "/synthetic";
  if (!(await validSecret(request, synthetic ? env.SYNTHETIC_WEBHOOK_TOKEN : env.CLOUDFLARE_WEBHOOK_TOKEN))) return new Response("Unauthorized", {status: 401});
  if (!request.headers.get("content-type")?.toLowerCase().startsWith("application/json")) return new Response("Expected JSON", {status: 415});
  let events;
  try {
    const payload = await readJson(request);
    events = synthetic ? normalizeSynthetic(payload?.events) : await normalizeCloudflare(payload, env);
  } catch (error) {
    const tooLarge = error instanceof RangeError;
    return new Response(tooLarge ? "Payload too large" : "Invalid alert", {status: tooLarge ? 413 : 400});
  }
  await env.DB.prepare(`
    INSERT OR IGNORE INTO webhook_events(id, source, type, subject, state, event_at, status, triage_action, received_at)
    SELECT json_extract(value,'$.id'), json_extract(value,'$.source'), json_extract(value,'$.type'),
      json_extract(value,'$.subject'), json_extract(value,'$.state'), json_extract(value,'$.ts'),
      json_extract(value,'$.status'), json_extract(value,'$.action'), ?1 FROM json_each(?2)
  `).bind(Math.floor(Date.now() / 1000), JSON.stringify(events)).run();
  return Response.json({accepted: events.length}, {status: 202});
}

export default {fetch: receiveAlert};
