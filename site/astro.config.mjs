import { readFileSync } from "node:fs";
import { defineConfig } from "astro/config";
const ORIGIN = JSON.parse(readFileSync(new URL("./site-origin.json", import.meta.url), "utf8"));
const requestedSite = (process.env.SITE_URL || ORIGIN.canonical).trim().replace(/\/+$/, "");
const canonicalSite = ORIGIN.legacy.includes(requestedSite) ? ORIGIN.canonical : requestedSite;

// Concepts merged in the hub leave their old slug on the survivor
// (`slugAliases`); gen_tree.py turns those into this map so old
// /tree/<slug>/ links keep working. Static output: Astro writes a
// meta-refresh page with a canonical link at each old path.
const tree = JSON.parse(readFileSync(new URL("./src/data/tree.json", import.meta.url), "utf8"));
const redirects = Object.fromEntries(
  Object.entries(tree.redirects || {}).map(([from, to]) => [`/tree/${from}/`, `/tree/${to}/`]));
export default defineConfig({
  site: canonicalSite,
  trailingSlash: "always",
  // Keep instructional comments readable at ordinary code sizes (WCAG 1.4.3).
  markdown: { shikiConfig: { theme: "github-dark-high-contrast" } },
  build: { format: "directory" },
  redirects,
});
