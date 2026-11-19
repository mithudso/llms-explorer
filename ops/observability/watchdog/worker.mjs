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

export async function probe(target, fetcher = fetch) {
  const start = Date.now();
  let status = 0;
  let success = false;
  try {
    const options = {redirect: "manual", signal: AbortSignal.timeout(12000), headers: {"User-Agent": "LLMSX-Offhost-Watchdog/1.0"}};
    let response = await fetcher(target.url, options);
    status = response.status;
    if (target.redirectHost && [301, 302, 307, 308].includes(response.status)) {
      const next = new URL(response.headers.get("Location"), target.url);
      await response.body?.cancel();
      if (next.protocol !== "https:" || next.hostname !== target.redirectHost) throw new Error("unexpected_redirect");
      response = await fetcher(next.href, options);
    }
    status = response.status;
    const text = await boundedText(response);
    success = status === 200 && !/cloudflare access|<title>[^<]*(?:sign in|just a moment)/i.test(text);
    if (success && target.expect) {
      const body = JSON.parse(text);
      success = Object.entries(target.expect).every(([key, value]) => body?.[key] === value);
    } else if (success) success = /<html(?:\s|>)/i.test(text);
  } catch { success = false; /* Never store URLs with tokens or response bodies. */ }
  return {name: target.name, phase: target.phase, checked_at: Math.floor(Date.now() / 1000), success: success ? 1 : 0, status, duration: (Date.now() - start) / 1000};
}

export async function scheduled(_event, env) {
  const checked = await Promise.all(targets.map(target => probe(target)));
  const minute = Math.floor(Date.now() / 60000);
  await env.DB.batch(checked.map(c => env.DB.prepare("INSERT OR IGNORE INTO checks(name,minute,checked_at,success,status,duration,phase) VALUES(?,?,?,?,?,?,?)").bind(c.name, minute, c.checked_at, c.success, c.status, c.duration, c.phase)));
  // A small independent history survives loss of the Mac and its metrics store.
  if (minute % 60 === 0) await env.DB.prepare("DELETE FROM checks WHERE checked_at < ?").bind(Math.floor(Date.now() / 1000) - 7 * 86400).run();
  console.log(JSON.stringify({event: "watchdog.cycle", service_name: "fleet-watchdog", service_version: env.RELEASE_SHA, project: "fleet", environment: "production", timestamp: Date.now() / 1000, severity: checked.some(c => !c.success && c.phase === "production") ? "warn" : "info", outcome: "success"}));
}

export async function handle(request, env) {
  const url = new URL(request.url);
  if (request.method !== "GET") return new Response("Method not allowed", {status: 405});
  if (url.pathname === "/health") return Response.json({status: "ok", revision: env.RELEASE_SHA}, {headers: {"Cache-Control": "no-store"}});
  if (!env.WATCHDOG_TOKEN || request.headers.get("Authorization") !== `Bearer ${env.WATCHDOG_TOKEN}`) return new Response("Unauthorized", {status: 401, headers: {"Cache-Control": "no-store"}});
  if (!["/metrics", "/status"].includes(url.pathname)) return new Response("Not found", {status: 404});
  const result = await env.DB.prepare("SELECT c.* FROM checks c JOIN (SELECT name,MAX(minute) minute FROM checks GROUP BY name) latest ON latest.name=c.name AND latest.minute=c.minute ORDER BY c.name").all();
  if (url.pathname === "/status") return Response.json({revision: env.RELEASE_SHA, checks: result.results}, {headers: {"Cache-Control": "no-store"}});
  const lines = ["# TYPE fleet_watchdog_success gauge", "# TYPE fleet_watchdog_checked_timestamp_seconds gauge", "# TYPE fleet_watchdog_http_status gauge", "# TYPE fleet_watchdog_duration_seconds gauge"];
  for (const target of targets) {
    const labels = `{project="${target.name}",phase="${target.phase}"}`;
    const row = result.results.find(c => c.name === target.name);
    lines.push(`fleet_watchdog_checked_timestamp_seconds${labels} ${row?.checked_at ?? 0}`);
    if (row) {
      lines.push(`fleet_watchdog_success${labels} ${row.success}`, `fleet_watchdog_http_status${labels} ${row.status}`, `fleet_watchdog_duration_seconds${labels} ${row.duration}`);
    }
  }
  return new Response(lines.join("\n") + "\n", {headers: {"Content-Type": "text/plain; version=0.0.4", "Cache-Control": "no-store"}});
}

export default {fetch: handle, scheduled};
