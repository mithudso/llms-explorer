"""units — LLM knowledge units for prose pages, on the local Ollama pool.

The deterministic passes carry the tables and code; this pass carries the
"X does Y because Z" knowledge that only reading the prose yields. One
generate() call per page section, JSON out, resumable per page, embedding
dedup at the end. PROMPT is a named constant so /pdo can optimize it.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import time
from pathlib import Path

from . import UNIT_TYPES, mirror_io, new_unit, reference_dir, slug

LLM_TYPES = ("concept", "fact", "actionable", "problem", "question", "idea")
DEFAULT_CLASSES = ("reference", "guide")
MAX_SECTION_CHARS = 12_000
MIN_PROSE_CHARS = 300          # less prose than this: deterministic passes only
CHARS_PER_TOKEN = 3.2          # markdown averages ~3.2 chars/token on qwen tokenizers
MIN_CTX = 8192
MAX_PREDICT = 1500
MAX_UNITS_PER_SECTION = 25
FAIL_PCT_LIMIT = 5.0
DEDUP_THRESHOLD = 0.9

PROMPT = """You extract atomic, source-faithful knowledge units from ONE documentation page.

Page URL: {url}

Rules:
- Output ONLY a JSON array. No prose before or after it.
- Each item: {{"type": <type>, "text": <one or two sentences>, "keywords": [<1-4 short terms>]}}
- Allowed types: {types}
  concept = what something is / how it works
  fact = a specific, checkable statement (defaults, limits, versions, behaviors)
  actionable = a concrete step or command the reader can run
  problem = a limitation, pitfall, error, or gotcha
  question = an open question the page raises but does not answer
  idea = a recommendation or best practice
- Preserve exact spellings of commands, flags, env vars, file names, error strings and
  version numbers. Put the exact token in "keywords".
- Never invent. Never generalize beyond the page. Skip marketing sentences, navigation,
  and anything already fully expressed by a table row or a code block on the page.
- At most {max_units} items. Prefer fewer, denser units over many thin ones.

Page (markdown):
<<<
{page}
>>>
"""

_H2_RE = re.compile(r"^##\s+(.*?)\s*#*\s*$")
_TABLE_LINE_RE = re.compile(r"^\s*\|.*\|\s*$")


def prose_only(text: str) -> str:
    """The page minus fenced code and table rows. Those are already carried
    by the deterministic passes as snippets and parameters; leaving them in
    the prompt costs tokens and tempts the model into restating them. A
    dropped block leaves a one-line marker so the prose around it keeps its
    sense ("run the following:" -> "[code block]")."""
    out: list[str] = []
    in_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            if not in_fence:
                out.append("[code block]")
            in_fence = not in_fence
            continue
        if in_fence or _TABLE_LINE_RE.match(line):
            continue
        out.append(line)
    text = "\n".join(out)
    return re.sub(r"\n{3,}", "\n\n", text).strip()
_ARRAY_RE = re.compile(r"\[.*\]", re.S)
_THINK_RE = re.compile(r"<think>.*?</think>", re.S)


def sections(page: dict, max_chars: int = MAX_SECTION_CHARS) -> list[dict]:
    """The whole page when it fits, else split at H2 boundaries (a section
    that still exceeds the limit is hard-cut — no page is skipped)."""
    text = page["text"]
    if len(text) <= max_chars:
        return [{"anchor": "", "text": text}]
    out: list[dict] = []
    cur, cur_anchor = [], ""
    for line in text.splitlines():
        m = _H2_RE.match(line)
        if m and cur:
            out.append({"anchor": cur_anchor, "text": "\n".join(cur)})
            cur = []
        if m:
            cur_anchor = f"#{slug(m.group(1))}"
        cur.append(line)
    if cur:
        out.append({"anchor": cur_anchor, "text": "\n".join(cur)})
    final: list[dict] = []
    for sec in out:
        t = sec["text"]
        while len(t) > max_chars:
            final.append({"anchor": sec["anchor"], "text": t[:max_chars]})
            t = t[max_chars:]
        final.append({"anchor": sec["anchor"], "text": t})
    return final


def parse_reply(text: str) -> list[dict]:
    """Tolerant: strips <think> blocks, takes the outermost JSON array, keeps
    items with a known type and >= 20 chars of text. [] on any failure."""
    text = _THINK_RE.sub("", text or "")
    m = _ARRAY_RE.search(text)
    if not m:
        return []
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    out = []
    for item in data:
        if not isinstance(item, dict):
            continue
        t = str(item.get("type", "")).strip().lower()
        txt = str(item.get("text", "")).strip()
        if t not in UNIT_TYPES or len(txt) < 20:
            continue
        kws = item.get("keywords") or []
        if not isinstance(kws, list):
            kws = [str(kws)]
        out.append({"type": t, "text": txt, "keywords": [str(k) for k in kws][:6]})
    return out


def llm_options(prompt: str) -> dict:
    """num_ctx sized to the prompt plus the reply — the Ollama default (4096)
    silently truncates a long page, which reads as 'the model missed half
    the facts'. Rounded up to a power of two so the server reuses the same
    allocation across pages."""
    need = int(len(prompt) / CHARS_PER_TOKEN) + MAX_PREDICT + 256
    ctx = MIN_CTX
    while ctx < need:
        ctx *= 2
    return {"num_ctx": ctx, "temperature": 0.2, "num_predict": MAX_PREDICT}


def build_prompt(url: str, text: str) -> str:
    return PROMPT.format(url=url, types=", ".join(LLM_TYPES), max_units=MAX_UNITS_PER_SECTION,
                         page=text)


def extract_page(page: dict, generate=None, model: str | None = None, start: int = 1,
                 timeout: int = 300) -> list[dict]:
    if generate is None:
        from semantic_ops import llm
        generate = llm.generate
    units: list[dict] = []
    seq = start
    prose = prose_only(page["text"])
    if len(prose) < MIN_PROSE_CHARS:
        return units
    for sec in sections({"text": prose}):
        prompt = build_prompt(page["url"], sec["text"])
        reply = generate(prompt, model=model, timeout=timeout,
                         options=llm_options(prompt), think=False)
        for item in parse_reply(reply)[:MAX_UNITS_PER_SECTION]:
            units.append(new_unit(seq, type=item["type"], text=item["text"],
                                  source_url=page["url"], anchor=sec["anchor"],
                                  page_class=page.get("class", ""),
                                  keywords=item["keywords"], origin="llm"))
            seq += 1
    return units


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", "", text.lower()).strip()


def _cos(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(x * x for x in b)) or 1.0
    return dot / (na * nb)


def dedup(units: list[dict], embed=None, threshold: float = DEDUP_THRESHOLD,
          model: str | None = None) -> list[dict]:
    """Exact-normalized dedup, then cosine >= threshold against every kept
    unit (first occurrence wins). O(n^2) on the survivors — fine for the
    low thousands of LLM units a docset produces."""
    seen: set[str] = set()
    firsts: list[dict] = []
    for u in units:
        key = _norm(u["text"])
        if key in seen:
            continue
        seen.add(key)
        firsts.append(u)
    if len(firsts) < 2:
        return firsts
    if embed is None:
        import embed_core
        embed = embed_core.embed_texts
    vecs = embed([u["text"] for u in firsts], model=model)
    kept: list[dict] = []
    kept_vecs: list[list[float]] = []
    for u, v in zip(firsts, vecs, strict=False):
        if any(_cos(v, kv) >= threshold for kv in kept_vecs):
            continue
        kept.append(u)
        kept_vecs.append(v)
    return kept


def _hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", errors="replace")).hexdigest()[:16]


def run(mirror: Path, model: str | None = None, classes=DEFAULT_CLASSES, limit: int = 0,
        generate=None, embed=None, do_dedup: bool = True, log=print) -> dict:
    """Resumable per page: units.state.json records each page's text hash and
    outcome; an unchanged page is never re-generated. Units accumulate in
    units.jsonl and are rewritten deduped at the end. failed_pct > 5 sets
    "_rc": 3 so the pipeline stage fails loudly."""
    mirror = Path(mirror)
    ref = reference_dir(mirror)
    pages = mirror_io.load_json(ref / "pages.json", default=None)
    if pages is None:
        raise SystemExit(f"{ref / 'pages.json'} missing — run `clean` first")
    todo = [p for p in pages if p.get("class") in classes]
    state = mirror_io.load_json(ref / "units.state.json", default={}) or {}
    existing = [u for u in mirror_io.read_jsonl(ref / "units.jsonl")
                if state.get(u.get("source_url"), {}).get("ok")]
    seq = 1 + max((int(u["id"][1:]) for u in existing if u.get("id", "u0")[1:].isdigit()),
                  default=0)
    units = list(existing)
    done = failed = generated = 0
    started = time.time()
    for i, page in enumerate(todo, 1):
        h = _hash(page["text"])
        st = state.get(page["url"])
        if st and st.get("hash") == h and st.get("ok"):
            done += 1
            continue
        if limit and generated >= limit:
            break
        try:
            got = extract_page(page, generate=generate, model=model, start=seq)
            ok = True
        except Exception as e:  # noqa: BLE001 — one bad page must not end the run
            got, ok = [], False
            log(f"[{i}/{len(todo)}] FAILED {page['url']}: {str(e)[:200]}")
        generated += 1
        if ok:
            done += 1
            units.extend(got)
            seq += len(got)
            log(f"[{i}/{len(todo)}] {page['url']}: {len(got)} units "
                f"({time.time() - started:.0f}s elapsed)")
        else:
            failed += 1
        state[page["url"]] = {"hash": h, "n": len(got), "ok": ok, "at": time.time()}
        mirror_io.write_jsonl(units, ref / "units.jsonl")
        mirror_io.save_json(state, ref / "units.state.json")
    before = len(units)
    if do_dedup and units:
        units = dedup(units, embed=embed, model=None)
        mirror_io.write_jsonl(units, ref / "units.jsonl")
    attempted = done + failed
    failed_pct = 100.0 * failed / attempted if attempted else 0.0
    result = {"pages": len(todo), "done": done, "failed": failed, "generated": generated,
              "units": len(units), "deduped": before - len(units),
              "failed_pct": round(failed_pct, 1)}
    if failed_pct > FAIL_PCT_LIMIT:
        result["_rc"] = 3
    return result
