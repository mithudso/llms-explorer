import { readFileSync } from "node:fs";
import { defineConfig } from "astro/config";

// Concepts merged in the hub leave their old slug on the survivor
// (`slugAliases`); gen_tree.py turns those into this map so old
// /tree/<slug>/ links keep working. Static output: Astro writes a
// meta-refresh page with a canonical link at each old path.
const tree = JSON.parse(readFileSync(new URL("./src/data/tree.json", import.meta.url), "utf8"));
const redirects = Object.fromEntries(
  Object.entries(tree.redirects || {}).map(([from, to]) => [`/tree/${from}/`, `/tree/${to}/`]));
export default defineConfig({
  site: process.env.SITE_URL || "https://llms-explorer.com",
  trailingSlash: "always",
  build: { format: "directory" },
  redirects,
});
