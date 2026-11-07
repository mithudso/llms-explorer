// Build-time only. Minimal compile checks can run before the export generators.
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
export type PackDownload = { slug: string; download: string; tokens: number };
const path = resolve(process.cwd(), "public/downloads/context-packs/index.json");
const rows: PackDownload[] = existsSync(path) ? JSON.parse(readFileSync(path, "utf8")).packs : [];
export const packBySlug = new Map(rows.map(row => [row.slug, row]));
