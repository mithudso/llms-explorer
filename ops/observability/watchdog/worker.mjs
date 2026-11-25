// Independent of the origin Mac. Read-only HTTP probes; no browser/ad execution.
export const targets = [
  {name: "llmsx", url: "https://llmsx.org/", phase: "production"},
  {name: "llms-explorer", url: "https://llms-explorer.com/", redirectHost: "llmsx.org", phase: "production"},
  {name: "oraclebot", url: "https://oraclebot.io/", phase: "production"},
  {name: "twss", url: "https://thatswhatshesaid.games/", phase: "production"},
  {name: "morelube", url: "https://morelube.com/", phase: "production"},
  {name: "skaas", url: "https://skaas.io/", phase: "production"},
  {name: "netdnsmonitor", url: "https://netdnsmonitor.com/", phase: "production"},
  {name: "skaas-app", url: "https://app.skaas.io/", phase: "production"},
  {name: "skaas-readiness", url: "https://api.skaas.io/ready", phase: "production", expect: {status: "ready"}},
  {name: "skaas-mcp", url: "https://mcp.skaas.io/health", phase: "production", expect: {status: "ok"}},
  {name: "dashboard", url: "https://ops.llmsx.org/api/health", phase: "production", expect: {database: "ok"}},
  {name: "llmsx-readiness", url: "https://api.llms-explorer.com/ready", phase: "production", expect: {status: "ready"}},
  {name: "morelube-readiness", url: "https://morelube.com/health", phase: "production", expect: {status: "ok"}},
];

async function boundedText(response) {
  const reader = response.body?.getReader();
  if (!reader) return "";
  const chunks = [];
  let size = 0;
  try {
    while (size < 65536) {
      const {value, done} = await reader.read();
      if (done) break;
      const part = value.subarray(0, 65536 - size);
      chunks.push(part);
      size += part.length;
    }
  } finally {
    await reader.cancel();
    reader.releaseLock();
  }
  const result = new Uint8Array(size);
  let offset = 0;
  for (const chunk of chunks) {result.set(chunk, offset); offset += chunk.length;}
  return new TextDecoder().decode(result);
}

const namePattern = /^[a-z][a-z0-9-]{0,79}$/;
const hostnamePattern = /^(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,63}$/;
const redirectStatuses = [301, 302, 303, 307, 308];

function publicHttps(input) {
  const url = new URL(input);
  if (url.protocol !== "https:" || url.port || url.username || url.password || url.search || url.hash || !hostnamePattern.test(url.hostname)) {
    throw new Error("invalid_watchdog_url");
  }
  return url;
}

export function configuredTargets(raw) {
  if (!raw) return targets;
  const rows = JSON.parse(raw);
  if (!Array.isArray(rows) || rows.length > 100) throw new Error("invalid_watchdog_targets");
  const names = new Set(targets.map(target => target.name));
  for (const target of rows) {
    if (!target || !namePattern.test(target.name) || names.has(target.name) || !["production", "staging"].includes(target.phase) || ![2, 5, 10].includes(target.interval)) {
      throw new Error("invalid_watchdog_target");
    }
    names.add(target.name);
    if (target.dns) {
      if (!hostnamePattern.test(target.dns) || !["NS", "A", "AAAA"].includes(target.rrtype ?? "NS")) throw new Error("invalid_watchdog_dns");
      if ((!target.rrtype || target.rrtype === "NS") && (!Array.isArray(target.nameservers) || target.nameservers.length === 0 || target.nameservers.some(host => !hostnamePattern.test(host)))) throw new Error("invalid_watchdog_nameservers");
      if (target.url || target.redirect || target.expect || target.bodyIncludes || target.method) throw new Error("ambiguous_watchdog_dns");
    } else {
      publicHttps(target.url);
      if (target.method && target.method !== "HEAD") throw new Error("invalid_watchdog_method");
      if (target.status && (!Array.isArray(target.status) || target.status.length === 0 || target.status.some(code => !Number.isInteger(code) || code < 200 || code >= 500))) throw new Error("invalid_watchdog_status");
      if (target.maxDurationMs !== undefined && (!Number.isInteger(target.maxDurationMs) || target.maxDurationMs < 250 || target.maxDurationMs > 12000)) throw new Error("invalid_watchdog_latency");
      if (target.bodyIncludes !== undefined && (typeof target.bodyIncludes !== "string" || target.bodyIncludes.length === 0)) throw new Error("invalid_watchdog_body");
      if (target.redirect) {
        if (!hostnamePattern.test(target.redirect.host) || (target.redirect.path && !target.redirect.path.startsWith("/")) || (target.redirect.follow !== undefined && typeof target.redirect.follow !== "boolean")) throw new Error("invalid_watchdog_redirect");
      }
    }
  }
  return [...targets, ...rows];
}

function targetsFromBindings(env) {
  const groups = [env.WATCHDOG_EXTRA_TARGETS, env.WATCHDOG_EXTRA_TARGETS_2, env.WATCHDOG_EXTRA_TARGETS_3, env.WATCHDOG_EXTRA_TARGETS_4].filter(Boolean);
  if (!groups.length) return targets;
  const rows = groups.map(group => JSON.parse(group));
  if (rows.some(group => !Array.isArray(group))) throw new Error("invalid_watchdog_targets");
  return configuredTargets(JSON.stringify(rows.flat()));
}

function includesJson(value, expected) {
  if (expected === null || typeof expected !== "object") return value === expected;
  if (!value || typeof value !== "object" || Array.isArray(value) !== Array.isArray(expected)) return false;
  return Object.entries(expected).every(([key, item]) => Object.hasOwn(value, key) && includesJson(value[key], item));
}

function redirectMatches(next, contract) {
  return next.protocol === "https:" && next.hostname === contract.host && !next.port && !next.username && !next.password && (!contract.path || next.pathname === contract.path);
}

export async function probe(target, fetcher = fetch) {
  const start = Date.now();
  let status = 0;
  let success = false;
  try {
    const options = {method: target.method ?? "GET", redirect: "manual", signal: AbortSignal.timeout(12000), headers: {"User-Agent": "LLMSX-Offhost-Watchdog/1.0"}};
    if (target.dns) {
      const url = new URL("https://cloudflare-dns.com/dns-query");
      const rrtype = target.rrtype ?? "NS";
      url.search = new URLSearchParams({name: target.dns, type: rrtype});
      const response = await fetcher(url, {...options, headers: {...options.headers, Accept: "application/dns-json"}});
      status = response.status;
      const body = JSON.parse(await boundedText(response));
      const answers = (body.Answer ?? []).filter(row => row.type === {A: 1, NS: 2, AAAA: 28}[rrtype]);
      success = status === 200 && body.Status === 0 && answers.length > 0;
      if (success && rrtype === "NS") {
        const ns = new Set(answers.filter(row => row.name?.replace(/\.$/, "").toLowerCase() === target.dns).map(row => row.data?.replace(/\.$/, "").toLowerCase()));
        success = ns.size === target.nameservers.length && target.nameservers.every(host => ns.has(host));
      }
    } else {
      let response = await fetcher(target.url, options);
      status = response.status;
      const redirect = target.redirect ?? (target.redirectHost ? {host: target.redirectHost, follow: true} : undefined);
      if (redirect) {
        const location = response.headers.get("Location");
        await response.body?.cancel();
        if (!redirectStatuses.includes(status) || !location) throw new Error("expected_redirect");
        const next = new URL(location, target.url);
        if (!redirectMatches(next, redirect)) throw new Error("unexpected_redirect");
        if (redirect.follow) {
          next.search = "";
          response = await fetcher(next.href, options);
          status = response.status;
        } else success = true;
      }
      if (!success) {
        const text = await boundedText(response);
        success = (target.status ?? [200]).includes(status);
        if (success && target.expect !== undefined) success = includesJson(JSON.parse(text), target.expect);
        else if (success && target.bodyIncludes) success = text.includes(target.bodyIncludes) && !/cloudflare access|<title>[^<]*just a moment/i.test(text);
        else if (success && !target.status && target.method !== "HEAD") success = /<html(?:\s|>)/i.test(text) && !/cloudflare access|<title>[^<]*(?:sign in|just a moment)/i.test(text);
      }
    }
  } catch { success = false; /* Never store URLs with tokens or response bodies. */ }
  const elapsed = Date.now() - start;
  if (target.maxDurationMs && elapsed > target.maxDurationMs) success = false;
  return {name: target.name, phase: target.phase, checked_at: Math.floor(Date.now() / 1000), success: success ? 1 : 0, status, duration: elapsed / 1000};
}

export function targetsForMinute(configured, minute) {
  return configured.filter(target => {
    const offset = [...target.name].reduce((sum, char) => sum + char.charCodeAt(0), 0);
    return (minute + offset) % (target.interval ?? 1) === 0;
  });
}

export function alertTransitions(rows, current) {
  const observations = new Map(current.map(check => [check.name, check]));
  return rows.flatMap(row => {
    const check = observations.get(row.name);
    if (!check || check.phase !== "production") return [];
    if (row.firing !== 1 && row.history === "000") return [{...check, firing: 1}];
    if (row.firing === 1 && row.history?.startsWith("11")) return [{...check, firing: 0}];
    return [];
  });
}

async function notify(env, due, checked, minute) {
  const names = due.filter(target => target.phase === "production").map(({name, interval = 1}) => ({name, interval}));
  const {results} = await env.DB.prepare(`
    SELECT json_extract(d.value, '$.name') AS name, a.firing, a.changed_at, a.notified_at,
      (SELECT group_concat(success, '') FROM (
        SELECT success FROM checks
        WHERE name = json_extract(d.value, '$.name')
          AND minute BETWEEN ?1 - 2 * json_extract(d.value, '$.interval') AND ?1
        ORDER BY minute DESC LIMIT 3
      )) AS history
    FROM json_each(?2) d
    LEFT JOIN alert_state a ON a.name = json_extract(d.value, '$.name')
  `).bind(minute, JSON.stringify(names)).all();
  const transitions = alertTransitions(results, checked);
  const changedAt = Math.floor(Date.now() / 1000);
  if (transitions.length) {
    await env.DB.prepare(`
      INSERT INTO alert_state(name, firing, changed_at, notified_at)
      SELECT json_extract(value, '$.name'), json_extract(value, '$.firing'), ?1, 0
      FROM json_each(?2) WHERE true
      ON CONFLICT(name) DO UPDATE SET firing = excluded.firing, changed_at = excluded.changed_at, notified_at = 0
    `).bind(changedAt, JSON.stringify(transitions.map(({name, firing}) => ({name, firing})))).run();
  }
  const mail = env.WATCHDOG_MAIL && env.WATCHDOG_MAIL_FROM && env.WATCHDOG_MAIL_TO;
  const webhook = env.WATCHDOG_INGEST && env.SYNTHETIC_WEBHOOK_TOKEN;
  if (!mail && !webhook) return;
  const recent = new Map(results.map(row => [row.name, row]));
  const changed = new Set(transitions.map(change => change.name));
  const pending = transitions.map(check => ({...check, changedAt})).concat(checked.flatMap(check => {
    const row = recent.get(check.name);
    return row?.notified_at === 0 && !changed.has(check.name) && row.firing === 1 - check.success
      ? [{...check, firing: row.firing, changedAt: row.changed_at}] : [];
  }));
  if (!pending.length) return;
  if (webhook) {
    const response = await env.WATCHDOG_INGEST.fetch("https://fleet-alert-ingest.internal/synthetic", {
      method: "POST",
      headers: {"content-type": "application/json", "cf-webhook-auth": env.SYNTHETIC_WEBHOOK_TOKEN},
      body: JSON.stringify({events: pending.map(({name, firing, changedAt: ts, status}) =>
        ({name, state: firing ? "firing" : "resolved", ts, status}))}),
    });
    if (response.status !== 202) throw new Error("watchdog_webhook_failed");
    await response.body?.cancel();
  }
  const failures = pending.filter(item => item.firing).length;
  if (mail) await env.WATCHDOG_MAIL.send({
    from: env.WATCHDOG_MAIL_FROM,
    to: env.WATCHDOG_MAIL_TO,
    subject: `[Fleet monitoring] ${failures} new failures, ${pending.length - failures} recoveries`,
    text: pending.map(item => `${item.firing ? "FAILED" : "RECOVERED"} ${item.name} (HTTP ${item.status || "unavailable"}, ${item.duration.toFixed(2)}s)`).join("\n") +
      "\n\nOpen Cloudflare Workers Observability to view current checks and investigate.",
  });
  await env.DB.prepare(`
    UPDATE alert_state SET notified_at = ?1
    WHERE name IN (SELECT value FROM json_each(?2))
  `).bind(Math.floor(Date.now() / 1000), JSON.stringify(pending.map(({name}) => name))).run();
  console.log(JSON.stringify({event: "watchdog.notification_sent", sent_count: pending.length}));
}

export async function scheduled(event, env) {
  const minute = Math.floor((event.scheduledTime ?? Date.now()) / 60000);
  const currentTargets = targetsForMinute(targetsFromBindings(env), minute);
  // Bound concurrency and keep HTTP plus D1 requests below the Worker subrequest limit.
  if (currentTargets.reduce((count, target) => count + (target.redirect?.follow || target.redirectHost ? 2 : 1), 0) > 46) throw new Error("watchdog_subrequest_budget");
  const checked = [];
  for (let start = 0; start < currentTargets.length; start += 6) {
    checked.push(...await Promise.all(currentTargets.slice(start, start + 6).map(target => probe(target))));
  }
  if (checked.length) await env.DB.batch(checked.map(c => env.DB.prepare("INSERT OR IGNORE INTO checks(name,minute,checked_at,success,status,duration,phase) VALUES(?,?,?,?,?,?,?)").bind(c.name, minute, c.checked_at, c.success, c.status, c.duration, c.phase)));
  if (minute % 60 === 0) {
    const now = Math.floor(Date.now() / 1000);
    await env.DB.batch([
      env.DB.prepare("DELETE FROM checks WHERE checked_at < ?").bind(now - 7 * 86400),
      env.DB.prepare("DELETE FROM webhook_events WHERE received_at < ?").bind(now - 30 * 86400),
    ]);
  }
  try { await notify(env, currentTargets, checked, minute); }
  catch (error) {
    const code = typeof error?.code === "string" && /^E_[A-Z_]+$/.test(error.code) ? error.code : "unclassified";
    console.error(JSON.stringify({event: "watchdog.notification_failed", code}));
  }
  const failed = checked.filter(c => !c.success && c.phase === "production").map(c => c.name);
  console.log(JSON.stringify({event: "watchdog.cycle", service_name: "fleet-watchdog", service_version: env.RELEASE_SHA, project: "fleet", environment: "production", timestamp: Date.now() / 1000, severity: failed.length ? "warn" : "info", outcome: "success", checked_count: checked.length, failed_count: failed.length, failed}));
}

export async function handle(request, env) {
  const url = new URL(request.url);
  if (request.method !== "GET") return new Response("Method not allowed", {status: 405});
  if (url.pathname === "/health") return Response.json({status: "ok", revision: env.RELEASE_SHA}, {headers: {"Cache-Control": "no-store"}});
  if (!env.WATCHDOG_TOKEN || request.headers.get("Authorization") !== `Bearer ${env.WATCHDOG_TOKEN}`) return new Response("Unauthorized", {status: 401, headers: {"Cache-Control": "no-store"}});
  if (!["/metrics", "/status"].includes(url.pathname)) return new Response("Not found", {status: 404});
  const selected = targetsFromBindings(env);
  const info = selected.map(({name, phase, interval = 1}) => ({name, phase, interval}));
  const {results: checks} = await env.DB.prepare(`
    SELECT c.*, COALESCE(a.firing, 0) AS firing
    FROM json_each(?1) target
    JOIN checks c ON c.name = target.value
      AND c.minute = (SELECT MAX(minute) FROM checks WHERE name = target.value)
    LEFT JOIN alert_state a ON a.name = c.name
  `).bind(JSON.stringify(info.map(target => target.name))).all();
  if (url.pathname === "/status") return Response.json({revision: env.RELEASE_SHA, checks, targets: info}, {headers: {"Cache-Control": "no-store"}});
  const lines = ["# TYPE fleet_watchdog_success gauge", "# TYPE fleet_watchdog_checked_timestamp_seconds gauge", "# TYPE fleet_watchdog_http_status gauge", "# TYPE fleet_watchdog_duration_seconds gauge", "# TYPE fleet_watchdog_alert_firing gauge"];
  for (const target of selected) {
    const labels = `{project="${target.name}",phase="${target.phase}"}`;
    const row = checks.find(c => c.name === target.name);
    lines.push(`fleet_watchdog_checked_timestamp_seconds${labels} ${row?.checked_at ?? 0}`);
    if (row) {
      lines.push(`fleet_watchdog_success${labels} ${row.success}`, `fleet_watchdog_http_status${labels} ${row.status}`, `fleet_watchdog_duration_seconds${labels} ${row.duration}`, `fleet_watchdog_alert_firing${labels} ${row.firing}`);
    }
  }
  return new Response(lines.join("\n") + "\n", {headers: {"Content-Type": "text/plain; version=0.0.4", "Cache-Control": "no-store"}});
}

export default {fetch: handle, scheduled};
