// Render the site's icons and social card from the llmsx logo SVGs.
//
// Source of truth: docs/design-system/llmsx/project/assets/Logos/*.svg.
// Writes to site/public/: favicon.svg (copy), favicon.ico (16/32/48 PNG
// entries), apple-touch-icon.png (180), icon-192.png, icon-512.png,
// icon-maskable-512.png (glyph inside the 80% safe zone), og-image.png
// (1200x630). Run after changing a logo file:
//
//   cd site && node tools/gen_brand_icons.mjs
//
// Needs Playwright with a Chromium build (not a site dependency; run it where
// `require("playwright")` resolves). Not part of `npm run build`: the outputs
// are committed.
import { createRequire } from "node:module";
import { copyFileSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const here = dirname(fileURLToPath(import.meta.url));
const site = join(here, "..");
const logos = join(site, "..", "docs", "design-system", "llmsx", "project", "assets", "Logos");
const pub = join(site, "public");

const ACCENT = "#2f5d7c";
const PAPER = "#f5f6f8";
const INK_MUTED = "#4b5462";
const TAGLINE = "Tools, skills and context for AI coding agents.";

const read = (name) => readFileSync(join(logos, name), "utf8");
const fit = (svg) => svg.replace(/width="\d+" height="\d+"/, 'width="100%" height="100%"');
// Full-bleed square for platforms that round or mask the corners themselves.
const square = (svg) => fit(svg).replace('rx="12"', 'rx="0"');

const mark = read("llmsx-mark.svg");
const fav = read("llmsx-favicon.svg");
const lockup = read("llmsx-lockup.svg");

// ICO with PNG-compressed entries (supported by every browser since IE Vista).
function ico(pngs) {
  const header = Buffer.alloc(6 + 16 * pngs.length);
  header.writeUInt16LE(0, 0);
  header.writeUInt16LE(1, 2);
  header.writeUInt16LE(pngs.length, 4);
  let offset = header.length;
  pngs.forEach(({ size, data }, i) => {
    const e = 6 + 16 * i;
    header.writeUInt8(size >= 256 ? 0 : size, e);
    header.writeUInt8(size >= 256 ? 0 : size, e + 1);
    header.writeUInt8(0, e + 2);
    header.writeUInt8(0, e + 3);
    header.writeUInt16LE(1, e + 4);
    header.writeUInt16LE(32, e + 6);
    header.writeUInt32LE(data.length, e + 8);
    header.writeUInt32LE(offset, e + 12);
    offset += data.length;
  });
  return Buffer.concat([header, ...pngs.map((p) => p.data)]);
}

const browser = await chromium.launch();
async function render(html, width, height, transparent = false) {
  const page = await browser.newPage({ viewport: { width, height } });
  await page.setContent(`<html><body style="margin:0;background:transparent">${html}</body></html>`);
  const buf = await page.screenshot({ omitBackground: transparent });
  await page.close();
  return buf;
}
const box = (svg, s) => `<div style="width:${s}px;height:${s}px">${svg}</div>`;

copyFileSync(join(logos, "llmsx-favicon.svg"), join(pub, "favicon.svg"));

const favPngs = [];
for (const size of [16, 32, 48]) favPngs.push({ size, data: await render(box(fit(fav), size), size, size, true) });
writeFileSync(join(pub, "favicon.ico"), ico(favPngs));

writeFileSync(join(pub, "apple-touch-icon.png"), await render(box(square(mark), 180), 180, 180));
for (const size of [192, 512]) writeFileSync(join(pub, `icon-${size}.png`), await render(box(square(mark), size), size, size));
writeFileSync(
  join(pub, "icon-maskable-512.png"),
  await render(`<div style="width:512px;height:512px;background:${ACCENT};display:grid;place-items:center">${box(square(mark), 420)}</div>`, 512, 512),
);

const card =
  `<div style="width:1200px;height:630px;background:${PAPER};position:relative;font-family:-apple-system,'Segoe UI',system-ui,sans-serif">` +
  `<div style="position:absolute;left:96px;top:200px;width:740px;height:160px">${fit(lockup)}</div>` +
  `<p style="position:absolute;left:96px;top:400px;margin:0;font-size:34px;line-height:1.3;color:${INK_MUTED};max-width:900px">${TAGLINE}</p>` +
  `<div style="position:absolute;left:0;right:0;bottom:0;height:16px;background:${ACCENT}"></div></div>`;
writeFileSync(join(pub, "og-image.png"), await render(card, 1200, 630));

await browser.close();
console.log("brand icons written to", pub);
