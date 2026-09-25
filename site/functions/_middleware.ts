// Pages Function: the site's response headers, applied at the edge.
//
// Cloudflare applies `_headers` only to responses it serves itself, never to a
// response that passed through a Pages Function. This middleware handles every
// route `public/_routes.json` does not exclude, so it must set those headers
// itself or every page would lose its Content-Security-Policy. It reads
// `dist/edge-headers.json`, which `tools/twins.py` writes at postbuild from the
// same rule list as `_headers`: the six `_headers` rules (the `/*` security
// policy; the text/markdown type and describedby link for twins and llms*.txt;
// the sitemap and robots types, which never reach this Function because
// `_routes.json` excludes those two paths) plus the per-file `X-Markdown-Tokens`
// map that no longer fits under the 100-rule `_headers` cap (it crossed it at
// 103 files).
//
// Only DOM types on purpose: `astro check` type-checks this file with the
// site's tsconfig, which has no @cloudflare/workers-types. `FALLBACK_RULES`,
// `patternToRegExp` and `compile` are exported for tests/test_twins.py.
type Fetcher = { fetch: (input: Request | string | URL) => Promise<Response> };
type Context = {
  request: Request;
  env: { ASSETS: Fetcher };
  next: () => Promise<Response>;
};
type Header = [string, string];
export type EdgeHeaders = { rules: { pattern: string; headers: Header[] }[]; tokens: Record<string, number> };
type Compiled = { rules: { re: RegExp; headers: Header[] }[]; tokens: Record<string, number> };

export const EDGE_HEADERS_PATH = "/edge-headers.json";
const TOKENS_HEADER = "X-Markdown-Tokens";

// The build-independent part of the rules. If the rules file cannot be read,
// a page is served with these rather than with nothing: the CSP needs the
// build's script hashes and cannot be guessed, but clickjacking and sniffing
// protection, HSTS, and the twin content type and describedby link do not.
// tests/test_twins.py checks each fallback rule is a subset of the rule
// twins.py writes for the same pattern, so they cannot drift from `_headers`.
export const FALLBACK_HEADERS: Header[] = [
  ["Referrer-Policy", "strict-origin-when-cross-origin"],
  ["X-Content-Type-Options", "nosniff"],
  ["X-Frame-Options", "DENY"],
  ["Strict-Transport-Security", "max-age=31536000; includeSubDomains"],
];
const TWIN_HEADERS: Header[] = [
  ["Content-Type", "text/markdown; charset=utf-8"],
  ["Link", '</llms.txt>; rel="describedby"'],
];
// The routes that hold a secret keep `no-referrer` even on the fallback path.
// Mirrors STRICT_ROUTES in tools/twins.py; the subset test fails if they drift.
const STRICT_ROUTES = ["/login/", "/account/", "/keys/", "/usage/", "/contribute/",
                       "/donate/", "/moderate/", "/proposals/", "/playground/"];
export const FALLBACK_RULES: EdgeHeaders["rules"] = [
  { pattern: "/*", headers: FALLBACK_HEADERS },
  ...STRICT_ROUTES.map((r) => ({ pattern: `${r}*`, headers: [["Referrer-Policy", "no-referrer"]] as Header[] })),
  { pattern: "/*.md", headers: TWIN_HEADERS },
  { pattern: "/llms*.txt", headers: TWIN_HEADERS },
  { pattern: "/*/llms.txt", headers: TWIN_HEADERS },
];

// `_headers` pattern semantics: `*` matches any run of characters, slashes
// included, and every matching rule applies (`/*` and `/*.md` both hit a twin).
// `_headers` also allows `:name` single-segment placeholders; twins.py never
// writes one and this matcher does not implement them, so a rule that uses one
// is refused at load time rather than silently never matching at the edge.
export function patternToRegExp(pattern: string): RegExp {
  if (/\/:/.test(pattern)) throw new Error(`${EDGE_HEADERS_PATH}: placeholder patterns are not supported: ${pattern}`);
  const escaped = pattern.replace(/[.+?^${}()|[\]\\]/g, "\\$&").replace(/\*/g, ".*");
  return new RegExp(`^${escaped}$`);
}

// Validate the whole shape once and compile every pattern once; a rules file
// that is valid JSON but not {rules: [{pattern, headers: [[name, value]]}],
// tokens: {}} must fail here, on the load path that logs, falls back and
// retries — never later inside applyHeaders, where a cached bad rule would
// throw on every request for the life of the isolate.
export function compile(data: unknown): Compiled {
  const edge = data as Partial<EdgeHeaders> | null;
  if (!edge || !Array.isArray(edge.rules) || typeof edge.tokens !== "object" || edge.tokens === null) {
    throw new Error(`${EDGE_HEADERS_PATH}: not {rules: [], tokens: {}}`);
  }
  const isHeader = (h: unknown): h is Header =>
    Array.isArray(h) && h.length === 2 && typeof h[0] === "string" && typeof h[1] === "string";
  return {
    rules: edge.rules.map((r, i) => {
      if (!r || typeof r.pattern !== "string" || !Array.isArray(r.headers) || !r.headers.every(isHeader)) {
        throw new Error(`${EDGE_HEADERS_PATH}: rule ${i} is not {pattern, headers: [[name, value]]}`);
      }
      // A name or value the platform rejects (CR/LF, a space in the name) would
      // otherwise throw inside applyHeaders on every request; refuse it here.
      try {
        new Headers(r.headers);
      } catch (err) {
        throw new Error(`${EDGE_HEADERS_PATH}: rule ${i} has an invalid header: ${(err as Error).message}`);
      }
      return { re: patternToRegExp(r.pattern), headers: r.headers };
    }),
    tokens: edge.tokens,
  };
}

const FALLBACK = compile({ rules: FALLBACK_RULES, tokens: {} });

export function applyHeaders(pathname: string, res: Response, edge: Compiled): Response {
  const out = new Response(res.body, res);
  for (const { re, headers } of edge.rules) {
    if (!re.test(pathname)) continue;
    for (const [name, value] of headers) out.headers.set(name, value);
  }
  const tokens = edge.tokens[pathname];
  if (typeof tokens === "number") out.headers.set(TOKENS_HEADER, String(tokens));
  return out;
}

// One fetch of the rules per isolate; a deploy replaces the isolate, so the
// rules can never outlive the build that wrote them.
let edgePromise: Promise<Compiled> | null = null;

// A fetch that never settles would leave every request in the isolate waiting
// on it forever, with nothing to clear the cache; bound it so the timeout
// takes the same reset-fallback-retry path as any other failure.
const LOAD_TIMEOUT_MS = 2000;

async function loadEdgeHeaders(assets: Fetcher, base: string): Promise<Compiled> {
  let timer: ReturnType<typeof setTimeout> | undefined;
  const timeout = new Promise<never>((_, reject) => {
    timer = setTimeout(() => reject(new Error(`${EDGE_HEADERS_PATH}: no answer within ${LOAD_TIMEOUT_MS}ms`)), LOAD_TIMEOUT_MS);
  });
  try {
    const res = await Promise.race([assets.fetch(new URL(EDGE_HEADERS_PATH, base)), timeout]);
    if (!res.ok) throw new Error(`${EDGE_HEADERS_PATH}: ${res.status}`);
    return compile(await Promise.race([res.json(), timeout]));
  } finally {
    clearTimeout(timer);            // or the pending timer keeps a Node test process alive
  }
}

export async function onRequest(context: Context): Promise<Response> {
  const { request, env, next } = context;
  const url = new URL(request.url);
  // Start the rules fetch before awaiting the page so a cold isolate pays the
  // two round-trips in parallel, not in series. On failure the cache is
  // cleared so the next request retries.
  const pending = (edgePromise ??= loadEdgeHeaders(env.ASSETS, request.url).catch((err: unknown) => {
    edgePromise = null;
    throw err;
  }));
  // Attach the rejection handler BEFORE calling next(): a next() that throws
  // synchronously would otherwise leave the shared promise's rejection unhandled.
  const edgeOrNull = pending.then(
    (compiled) => compiled,
    (err: unknown) => {
      // The rules file ships in the same deploy as the page, so this is a
      // broken build, not a transient: log the actual error so the Function
      // logs say which (404, SPA-fallback HTML, bad shape, timeout) and serve
      // the page with the build-independent headers rather than a 500.
      console.error(`${EDGE_HEADERS_PATH} unavailable; serving ${url.pathname} with fallback headers only`, err);
      return null;
    },
  );
  const [res, edge] = await Promise.all([next(), edgeOrNull]);
  return applyHeaders(url.pathname, res, edge ?? FALLBACK);
}
