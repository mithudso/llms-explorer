// Passkey register + sign-in, end to end, in headless Chrome with a virtual
// authenticator. Exercises the real /login/ page against a real API, which is
// the only way to catch a bug like the one this test was written for: on
// browsers that ship PublicKeyCredential.parseCreationOptionsFromJSON (Chrome
// 132+, Safari 18+) the page once passed the parsed options bare to
// navigator.credentials.create, which throws NotSupportedError before any
// prompt. The pytest suite cannot see that; it never runs a browser.
//
// Two rounds run: "native" uses the browser's parse*FromJSON / toJSON helpers,
// then "fallback" deletes all three before the page loads so the page's own
// base64url/ArrayBuffer conversions run in both directions.
//
// Run through ./passkey.sh (or `npm run e2e:passkey`), which boots a
// throwaway Postgres + dev API + astro dev and tears them down. To run against
// servers you already have:
//
//   SITE=http://localhost:4321 API=http://localhost:8791 node passkey.mjs
//
// Both must be on `localhost` (not 127.0.0.1): the session cookie is
// `Secure; SameSite=Lax`, which Chrome accepts on http://localhost and sends
// same-site across ports. CHROME overrides the browser binary (default: the
// first of the macOS app bundle, google-chrome, chromium that exists).
// puppeteer-core is a site devDependency; PUPPETEER_CORE overrides the path.
import { createRequire } from "node:module";
import { existsSync } from "node:fs";

const SITE = process.env.SITE || "http://localhost:4321";
const API = process.env.API || "http://localhost:8791";
const CHROME_CANDIDATES = [
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/usr/bin/google-chrome",
  "/usr/bin/chromium",
];
const CHROME = process.env.CHROME || CHROME_CANDIDATES.find((p) => existsSync(p));
const MIN_CHROME = 132;          // first release with parseCreationOptionsFromJSON
const WATCHDOG_MS = 180_000;     // whole run; a wedged Chrome must not pin the servers
const NAV_TIMEOUT_MS = 20_000;
const CARD_TIMEOUT_MS = 15_000;
const log = (...a) => console.log("[passkey-e2e]", ...a);

if (!CHROME) throw new Error(`no Chrome found; set CHROME (tried ${CHROME_CANDIDATES.join(", ")})`);
const require = createRequire(import.meta.url);
const puppeteer = require(process.env.PUPPETEER_CORE || "puppeteer-core");

const browser = await puppeteer.launch({
  executablePath: CHROME,
  headless: true,
  args: ["--no-first-run", "--no-default-browser-check", "--no-sandbox"],
});
const watchdog = setTimeout(() => {
  log(`TIMEOUT: aborting after ${WATCHDOG_MS / 1000}s`);
  browser.process()?.kill("SIGKILL");
  process.exit(1);
}, WATCHDOG_MS);
watchdog.unref?.();

const chromeMajor = Number((await browser.version()).match(/Chrome\/(\d+)/)?.[1]);
if (!(chromeMajor >= MIN_CHROME)) {
  await browser.close();
  throw new Error(`Chrome ${chromeMajor} predates parseCreationOptionsFromJSON (${MIN_CHROME}); ` +
    "the native round would silently take the fallback path and prove nothing");
}

const checks = {};
try {
  const page = await browser.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push("pageerror: " + e.message));
  const cdp = await page.createCDPSession();
  await cdp.send("WebAuthn.enable", { enableUI: false });
  const { authenticatorId } = await cdp.send("WebAuthn.addVirtualAuthenticator", {
    options: {
      protocol: "ctap2", transport: "internal", hasResidentKey: true,
      hasUserVerification: true, isUserVerified: true, automaticPresenceSimulation: true,
    },
  });
  log("chrome", chromeMajor, "· virtual authenticator", authenticatorId);
  const credentialCount = async () =>
    (await cdp.send("WebAuthn.getCredentials", { authenticatorId })).credentials.length;

  // Click a login button, follow the redirect, read the account card.
  const clickAndReadCard = async (sel) => {
    await Promise.all([
      page.waitForNavigation({ timeout: NAV_TIMEOUT_MS, waitUntil: "domcontentloaded" }).catch(() => null),
      page.click(sel),
    ]);
    const err = await page.$eval("#login-error", (el) => el.textContent).catch(() => "");
    log(`after ${sel}: url = ${page.url()}${err ? ` · login-error = ${JSON.stringify(err)}` : ""}`);
    await page.waitForSelector("#account-card:not([hidden])", { timeout: CARD_TIMEOUT_MS });
    const text = await page.$eval("#account-card", (el) => el.textContent.replace(/\s+/g, " ").trim());
    log("account card:", text.slice(0, 80));
    // The card only unhides after /api/me answered 200; the account id is what
    // ties the sign-in round back to the account the register round created.
    const me = await page.evaluate((api) =>
      fetch(api + "/api/me", { credentials: "include", headers: { accept: "application/json" } }).then((r) => r.json()), API);
    return { url: page.url(), text, id: me?.id ?? null };
  };
  const signedIn = (r) => r.url.endsWith("/account/") && typeof r.id === "string" && r.id.length > 0;
  // Cookie clear + reload must leave the page signed out: /api/me answers 401.
  const openLoginSignedOut = async (round) => {
    const me = page.waitForResponse((r) => r.url() === `${API}/api/me`, { timeout: NAV_TIMEOUT_MS });
    await page.goto(`${SITE}/login/`, { waitUntil: "domcontentloaded" });
    const status = (await me).status();
    if (status !== 401) throw new Error(`${round}: cookie clear did not sign out (/api/me ${status})`);
    await page.waitForSelector("#login-choices:not([hidden])");
  };

  await page.goto(`${SITE}/login/`, { waitUntil: "domcontentloaded" });
  await page.waitForSelector("#passkey-new");
  // The page talks to whatever AccountNav baked in at build time; if that is
  // not the API under test, every call below would go somewhere else.
  const pageApi = await page.$eval(".account-nav", (el) => el.dataset.api);
  if (pageApi !== API) throw new Error(`page targets ${pageApi}, test targets ${API}; start astro dev with PUBLIC_API_URL=${API}`);

  // Control: the pre-fix call shape. If this stops throwing, the wrapper in
  // login.astro is no longer load-bearing — a warning, not a failure, since
  // a browser change is not a regression here. Any credential it mints is
  // removed so the counts below stay attributable to the page's own ceremony.
  const before = await credentialCount();
  const control = await page.evaluate(async (api) => {
    const r = await fetch(api + "/api/auth/passkey/register/options", {
      method: "POST", credentials: "include",
      headers: { accept: "application/json", "content-type": "application/json" }, body: "{}",
    });
    const opts = await r.json();
    try {
      await navigator.credentials.create(PublicKeyCredential.parseCreationOptionsFromJSON(opts));
      return { threw: false };
    } catch (e) { return { threw: true, name: e.name }; }
  }, API);
  log("control (bare parsed options):", JSON.stringify(control));
  if (!control.threw) {
    log("WARNING: bare parsed options were ACCEPTED; the { publicKey } wrapper in login.astro is no longer load-bearing");
    const { credentials } = await cdp.send("WebAuthn.getCredentials", { authenticatorId });
    for (const c of credentials.slice(before)) {
      await cdp.send("WebAuthn.removeCredential", { authenticatorId, credentialId: c.credentialId });
    }
  }
  checks.controlThrew = control.threw;

  for (const round of ["native", "fallback"]) {
    log(`== round: ${round}`);
    if (round === "fallback") {
      await page.evaluateOnNewDocument(() => {
        delete PublicKeyCredential.parseCreationOptionsFromJSON;
        delete PublicKeyCredential.parseRequestOptionsFromJSON;
        delete PublicKeyCredential.prototype.toJSON;
      });
    }
    // One resident credential per round: with two, the discoverable sign-in
    // ceremony (no allowCredentials) picks either, and the round could land on
    // the other round's account.
    await cdp.send("WebAuthn.clearCredentials", { authenticatorId });
    await cdp.send("Network.clearBrowserCookies");
    await openLoginSignedOut(round);
    // Prove which path the page will take, rather than trusting the version
    // number (native) or the delete (fallback).
    const helpers = await page.evaluate(() => [
      typeof PublicKeyCredential.parseCreationOptionsFromJSON,
      typeof PublicKeyCredential.parseRequestOptionsFromJSON,
      typeof PublicKeyCredential.prototype.toJSON,
    ]);
    const want = round === "native" ? "function" : "undefined";
    if (!helpers.every((h) => h === want)) throw new Error(`${round} round: WebAuthn JSON helpers are ${helpers.join(",")}, expected all ${want}`);
    const startCount = await credentialCount();

    const registered = await clickAndReadCard("#passkey-new");
    checks[`${round}.registered`] = signedIn(registered);
    checks[`${round}.oneCredentialMinted`] = (await credentialCount()) - startCount === 1;

    await cdp.send("Network.clearBrowserCookies");
    await openLoginSignedOut(round);
    const again = await clickAndReadCard("#passkey-in");
    checks[`${round}.signedIn`] = signedIn(again) && again.id === registered.id;
  }
  checks.noPageErrors = errors.length === 0;
  if (errors.length) log("page errors:", errors);
} finally {
  // The watchdog stays armed through close(): a wedged Chrome that never
  // closes is exactly the case it exists for.
  try { await browser.close(); } finally { clearTimeout(watchdog); }
}

// controlThrew is reported but not required: see the WARNING above.
const { controlThrew, ...required } = checks;
const ok = Object.values(required).every(Boolean);
log(ok ? "PASS" : "FAIL", JSON.stringify({ controlThrew, ...required }));
process.exitCode = ok ? 0 : 1;
