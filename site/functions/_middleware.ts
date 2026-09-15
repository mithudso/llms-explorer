// Pages Function: the site's response headers, applied at the edge.
//
// Cloudflare applies `_headers` only to responses it serves itself, never to a
// response that passed through a Pages Function. This middleware handles every
// route `public/_routes.json` does not exclude, so it must set those headers
// itself or every page would lose its Content-Security-Policy. It reads
// `dist/edge-headers.json`, which `tools/twins.py` writes at postbuild from the
// same rule list as `_headers`: the six wildcard rules (security policy, the
// text/markdown type and describedby link for twins and llms*.txt) plus the
// per-file `X-Markdown-Tokens` map that no longer fits under the 100-rule
// `_headers` cap (it crossed it at 103 files).
//
// Only DOM types on purpose: `astro check` type-checks this file with the
// site's tsconfig, which has no @cloudflare/workers-types.
type Fetcher = { fetch: (input: Request | string | URL) => Promise<Response> };
type Context = {
  request: Request;
  env: { ASSETS: Fetcher };
  next: () => Promise<Response>;
};
type Rule = { pattern: string; headers: [string, string][] };
type EdgeHeaders = { rules: Rule[]; tokens: Record<string, number> };

export const EDGE_HEADERS_PATH = "/edge-headers.json";
const TOKENS_HEADER = "X-Markdown-Tokens";

// `_headers` pattern semantics: `*` matches any run of characters, slashes
// included, and every matching rule applies (`/*` and `/*.md` both hit a twin).
export function patternToRegExp(pattern: string): RegExp {
  const escaped = pattern.replace(/[.+?^${}()|[\]\\]/g, "\\$&").replace(/\*/g, ".*");
  return new RegExp(`^${escaped}$`);
}

export function applyHeaders(pathname: string, res: Response, edge: EdgeHeaders): Response {
  const out = new Response(res.body, res);
  for (const { pattern, headers } of edge.rules) {
    if (!patternToRegExp(pattern).test(pathname)) continue;
    for (const [name, value] of headers) out.headers.set(name, value);
  }
  const tokens = edge.tokens[pathname];
  if (typeof tokens === "number") out.headers.set(TOKENS_HEADER, String(tokens));
  return out;
}

// One fetch of the rules per isolate; a deploy replaces the isolate, so the
// rules can never outlive the build that wrote them.
let edgePromise: Promise<EdgeHeaders> | null = null;

async function loadEdgeHeaders(assets: Fetcher, origin: string): Promise<EdgeHeaders> {
  const res = await assets.fetch(new URL(EDGE_HEADERS_PATH, origin));
  if (!res.ok) throw new Error(`${EDGE_HEADERS_PATH}: ${res.status}`);
  return (await res.json()) as EdgeHeaders;
}

export async function onRequest(context: Context): Promise<Response> {
  const { request, env, next } = context;
  const url = new URL(request.url);
  const res = await next();
  edgePromise ??= loadEdgeHeaders(env.ASSETS, url.origin).catch((err: unknown) => {
    edgePromise = null;           // the next request retries the fetch
    throw err;
  });
  let edge: EdgeHeaders;
  try {
    edge = await edgePromise;
  } catch {
    // The rules file is part of the same deploy as the page, so this is a
    // broken build, not a transient. Serving the page bare is the lesser harm
    // versus a 500 on every route; log it so the miss is visible in the
    // Function logs, and the next request retries.
    console.error(`${EDGE_HEADERS_PATH} unavailable; serving ${url.pathname} without edge headers`);
    return res;
  }
  return applyHeaders(url.pathname, res, edge);
}
