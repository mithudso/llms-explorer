/**
 * YAML-frontmatter parsing for SKILL.md, without a YAML dependency.
 *
 * This is deliberately a *subset* parser, matching `llmsx/llmsx/skills.py`'s
 * fallback rule for rule: top-level scalars, folded and literal block scalars
 * (`>`, `>-`, `|`, `|-`), block and inline lists, and one level of nested
 * mapping whose values are kept as raw text. Anything deeper is kept raw
 * rather than guessed at — a mangled value is worse than an unparsed one, and
 * nothing downstream reads past that depth.
 *
 * Pulling in js-yaml would buy full fidelity at the cost of the property that
 * makes this package usable anywhere: it installs with no dependencies.
 */

export class SkillParseError extends Error {
  constructor(message) {
    super(message);
    this.name = "SkillParseError";
  }
}

/** `[frontmatterSource, body]` for a `---`-delimited file. */
export function splitFrontmatter(text) {
  if (!text.startsWith("---")) {
    throw new SkillParseError("no YAML frontmatter (file does not start with '---')");
  }
  const match = /^---[^\S\n]*\n([\s\S]*?)\n---[^\S\n]*(?:\n|$)/.exec(text);
  if (!match) {
    throw new SkillParseError("frontmatter is not closed by a '---' line");
  }
  return [match[1], text.slice(match[0].length)];
}

const indentOf = (line) => line.length - line.replace(/^ +/, "").length;

function stripScalar(value) {
  const trimmed = value.trim();
  if (trimmed.length >= 2 && trimmed[0] === trimmed[trimmed.length - 1] &&
      (trimmed[0] === '"' || trimmed[0] === "'")) {
    return trimmed.slice(1, -1);
  }
  return trimmed;
}

/** Lines belonging to the block opened at `start`, dedented; plus next index. */
function collectIndented(lines, start) {
  const block = [];
  let i = start;
  while (i < lines.length) {
    const line = lines[i];
    if (line.trim() && indentOf(line) === 0) break;
    block.push(line);
    i += 1;
  }
  while (block.length && !block[block.length - 1].trim()) block.pop();
  if (!block.length) return [[], i];
  const pad = Math.min(...block.filter((b) => b.trim()).map(indentOf));
  return [block.map((b) => (b.length >= pad ? b.slice(pad) : b)), i];
}

/** YAML folded-scalar semantics: newline joins, blank line breaks. */
function fold(block) {
  const parts = [];
  let current = [];
  for (const line of block) {
    if (line.trim()) {
      current.push(line.trim());
    } else if (current.length) {
      parts.push(current.join(" "));
      current = [];
    }
  }
  if (current.length) parts.push(current.join(" "));
  return parts.join("\n\n");
}

const KEY = /^([A-Za-z_][\w.-]*):([\s\S]*)$/;
const BLOCK_MARKERS = new Set([">", ">-", ">+", "|", "|-", "|+"]);

/** One level of nested mapping; values kept as raw text. */
function parseNested(block) {
  const nested = {};
  let i = 0;
  while (i < block.length) {
    const line = block[i];
    const match = KEY.exec(line);
    if (!match || indentOf(line) > 0) {
      i += 1;
      continue;
    }
    const key = match[1];
    const rest = match[2].trim();
    if (BLOCK_MARKERS.has(rest)) {
      const [inner, next] = collectIndented(block, i + 1);
      nested[key] = inner.join("\n");
      i = next;
      continue;
    }
    nested[key] = rest ? stripScalar(rest) : null;
    i += 1;
  }
  return nested;
}

export function parseFrontmatter(source) {
  const lines = source.split("\n");
  const out = {};
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (!line.trim() || line.trimStart().startsWith("#") || indentOf(line) > 0) {
      i += 1;
      continue;
    }
    const match = KEY.exec(line);
    if (!match) {
      i += 1;
      continue;
    }
    const key = match[1];
    const rest = match[2].trim();

    if (BLOCK_MARKERS.has(rest)) {
      const [block, next] = collectIndented(lines, i + 1);
      let value = rest.startsWith(">") ? fold(block) : block.join("\n").replace(/\n+$/, "");
      if (rest.endsWith("-")) value = value.replace(/\n+$/, "");
      out[key] = value;
      i = next;
      continue;
    }

    if (rest.startsWith("[") && rest.endsWith("]")) {
      const inner = rest.slice(1, -1).trim();
      out[key] = inner ? inner.split(",").filter((p) => p.trim()).map(stripScalar) : [];
      i += 1;
      continue;
    }

    if (rest) {
      out[key] = stripScalar(rest);
      i += 1;
      continue;
    }

    // `key:` with nothing after it: a block list, a nested mapping, or empty.
    const [block, next] = collectIndented(lines, i + 1);
    i = next;
    if (!block.length) {
      out[key] = null;
    } else if (block[0].trimStart().startsWith("- ")) {
      out[key] = block
        .filter((b) => b.trimStart().startsWith("- "))
        .map((b) => stripScalar(b.trimStart().slice(2)));
    } else {
      out[key] = parseNested(block);
    }
  }
  return out;
}
