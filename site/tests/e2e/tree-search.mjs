// Real model search under the built CSP and Pages middleware. Set
// TREE_SEARCH_URL to verify a deployed site instead of starting the local server.
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createServer } from "node:http";
import { dirname, resolve, extname } from "node:path";
import { fileURLToPath } from "node:url";
import puppeteer from "puppeteer-core";

const site = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const dist = resolve(site, "dist");
const mime = { ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".mjs": "text/javascript",
  ".json": "application/json", ".css": "text/css", ".wasm": "application/wasm", ".svg": "image/svg+xml",
  ".png": "image/png", ".woff2": "font/woff2", ".txt": "text/plain", ".md": "text/markdown" };
let server;
let target = process.env.TREE_SEARCH_URL;
if (!target) {
  const { onRequest } = await import("../../functions/_middleware.ts");
  const asset = async (url) => {
    const path = decodeURIComponent(new URL(url).pathname);
    const file = resolve(dist, `.${path}${path.endsWith("/") ? "index.html" : ""}`);
    if (!file.startsWith(`${dist}/`)) return new Response("Forbidden", { status: 403 });
    try {
      return new Response(await readFile(file), {
        headers: { "Content-Type": mime[extname(file)] ?? "application/octet-stream" },
      });
    } catch { return new Response("Not found", { status: 404 }); }
  };
  server = createServer(async (req, res) => {
    try {
      const request = new Request(`http://127.0.0.1:${server.address().port}${req.url}`);
      const out = await onRequest({ request, env: { ASSETS: { fetch: asset } }, next: () => asset(request.url) });
      res.writeHead(out.status, Object.fromEntries(out.headers));
      res.end(Buffer.from(await out.arrayBuffer()));
    } catch (err) { res.writeHead(500); res.end(String(err)); }
  });
  await new Promise((done) => server.listen(0, "127.0.0.1", done));
  target = `http://127.0.0.1:${server.address().port}/tree/`;
}

const browser = await puppeteer.launch({
  executablePath: process.env.CHROME_BIN ?? "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  headless: true, args: ["--no-first-run", "--no-default-browser-check"],
});
const events = [];
const network = [];
const report = { target, browser: await browser.version(), events, network };
try {
  const page = await browser.newPage();
  page.on("pageerror", (err) => events.push({ type: "pageerror", message: err.message }));
  page.on("console", (msg) => {
    if (["error", "warn"].includes(msg.type())) events.push({ type: msg.type(), message: msg.text() });
  });
  page.on("response", (res) => {
    if (["script", "fetch"].includes(res.request().resourceType())) network.push({ url: res.url(), status: res.status() });
  });
  const response = await page.goto(target, { waitUntil: "domcontentloaded", timeout: 45000 });
  report.csp = response.headers()["content-security-policy"];
  assert.ok(report.csp.includes("'wasm-unsafe-eval'"), "tree CSP must allow WASM compilation");
  assert.ok(/'nonce-[^']+'/.test(report.csp), "tree HTML must carry a challenge nonce");
  assert.ok(!report.csp.match(/(?:^|;)\s*script-src\s+([^;]*)/)[1].includes("'unsafe-inline'"),
    "script-src must retain strict inline restrictions");
  const treeCount = await page.$$eval("#tree-list li", (items) => items.length);
  await page.type("#tree-filter", "caching");
  const matched = await page.$eval("#tree-filter-status", (el) => el.textContent);
  assert.match(matched, /concepts match/);
  const hidden = await page.$$eval("#tree-list li", (items) => items.filter((el) => el.hidden).length);
  assert.ok(hidden > 0 && hidden < treeCount, "filter must hide unrelated branches and keep matching ones");
  await page.$eval("#tree-filter", (el) => { el.value = ""; el.dispatchEvent(new Event("input")); });
  assert.equal(await page.$$eval("#tree-list li[hidden]", (items) => items.length), 0);
  report.filter = { treeCount, matched, hidden, reset: true };
  const query = "How does prompt caching reduce token cost?";
  await page.type("#semantic-search-input", query);
  await page.waitForFunction(() => document.querySelectorAll("#semantic-search-results li").length > 0
    || document.querySelector("#semantic-search-status").textContent.includes("failed"), { timeout: 180000 });
  report.search = await page.evaluate(() => ({
    status: document.querySelector("#semantic-search-status").textContent,
    hits: [...document.querySelectorAll("#semantic-search-results a")].map((el) => ({ title: el.textContent, href: el.href })),
    challengeNonces: [...document.scripts].filter((el) => el.textContent.includes("__CF$cv$params")).map((el) => el.nonce),
  }));
  assert.equal(report.search.hits.length, 8, `expected real semantic results, got ${report.search.status}`);
  assert.ok(report.search.hits.some((hit) => /cach|token|cost/i.test(hit.title)), "query must return relevant results");
  assert.ok(!network.some((item) => item.url.startsWith("blob:")), "runtime must use direct modules");
  assert.deepEqual(events.filter((item) => item.type === "pageerror" || /Content Security Policy|violates.*script-src/i.test(item.message)), []);

  // A failed index download is recoverable without an unhandled focus promise.
  const retry = await browser.newPage();
  const retryErrors = [];
  retry.on("pageerror", (err) => retryErrors.push(err.message));
  await retry.setRequestInterception(true);
  let failures = 0;
  retry.on("request", (req) => {
    if (new URL(req.url()).pathname === "/search-index.bin" && failures++ === 0) {
      void req.respond({ status: 503, contentType: "text/plain", body: "Temporary test failure" });
    } else { void req.continue(); }
  });
  await retry.goto(target, { waitUntil: "domcontentloaded", timeout: 45000 });
  await retry.focus("#semantic-search-input");
  await retry.waitForFunction(() => document.querySelector("#semantic-search-status").textContent.includes("failed to load"), { timeout: 30000 });
  await retry.type("#semantic-search-input", query);
  await retry.waitForFunction(() => document.querySelectorAll("#semantic-search-results li").length === 8, { timeout: 180000 });
  assert.deepEqual(retryErrors, []);
  report.retry = { failedIndexDownload: true, recoveredHits: 8, pageErrors: retryErrors };
  report.passed = true;
} catch (err) {
  report.passed = false;
  report.failure = err.message;
  process.exitCode = 1;
} finally {
  await browser.close();
  if (server) await new Promise((done) => server.close(done));
  console.log(JSON.stringify(report, null, 2));
}
