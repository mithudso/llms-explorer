"""skills — load a skill's markdown spec and run it against a model.

A *skill* here is the `SKILL.md` file this repo and `~/.claude/skills` already
use: YAML frontmatter (name, description, model, …) over a markdown body of
instructions written to be followed by an agent.

**What this module is, and is not.** It is a thin invocation layer: find the
file, parse it, build a system prompt from it, send the caller's task as the
user turn, hand back what the model said. It is *not* a reimplementation of
what those skills describe. Most of them orchestrate multi-pass loops, fan out
subagents, take filesystem locks and write back to a concept tree — behaviour
that belongs to an agent harness with tools, not to a library function. Running
`concept-family-explorer` through :func:`run_skill` gets you one model turn
holding those instructions, not a saturation loop; a caller who needs the loop
has to drive it. Saying otherwise in a docstring would be the expensive kind of
wrong, so it is said here instead.

The transport is injected (``client=``) for the same reason the rest of this
package takes its data path as an argument: the tests must run offline, and
they do — no test in `llmsx/tests` opens a socket.

**A `SKILL.md` is not trusted input.** `load_skill(name)` searches every
`skills/` directory at or above the current working directory before falling
back to `~/.claude/skills` — deliberately, so this repo's own skills win when
running from inside it. That also means running `llmsx family` / `llmsx
optimize` inside *any* directory that happens to contain a `skills/<name>/
SKILL.md` — a cloned repo, a downloaded archive — runs that file's
instructions as the system prompt of a real, billed API call, using whatever
model its frontmatter names. `_run_skill_cli` in `__main__.py` prints the
resolved `SKILL.md` path to stderr before every call for exactly this reason:
there is no way to tell a legitimate repo-local skill from a planted one
except by looking. `run_skill` additionally refuses to let `**create_kwargs`
silently replace the computed `system`/`model`/`messages`/`max_tokens` (see
its docstring), which closes the other half of the same risk — a caller (or a
future HTTP layer forwarding kwargs) cannot use that path to redirect the
outbound request regardless of which skill file was loaded.
"""
from __future__ import annotations

import logging
import os
import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

#: Used when neither the caller nor the skill's frontmatter names a model.
DEFAULT_MODEL = "claude-sonnet-5"

#: Bounded by default: a skill body is long, and an unbounded reply on a
#: 15k-token system prompt is the kind of bill nobody predicted.
DEFAULT_MAX_TOKENS = 4096

#: Cap on the combined size of a skill's `references/*.md` files folded into
#: a system prompt (see `Skill.read_references`). References are included
#: whether or not the body cites them, and this estate has skills whose
#: references/ directory alone runs past a million characters — a budget
#: keeps one oversized skill from silently producing an enormous, expensive
#: request.
DEFAULT_MAX_REFERENCE_CHARS = 200_000

#: A generous ceiling on a `SKILL.md`'s own size, checked before any parsing.
#: Real skill files run from a few hundred bytes to tens of kilobytes; this
#: exists to fail fast and clearly on a corrupted or hostile file rather than
#: read an unbounded amount of text into memory first.
MAX_SKILL_FILE_BYTES = 2_000_000

#: Where `load_skill` looks, in order. `$LLMSX_SKILL_PATH` (os.pathsep-joined)
#: comes first when set, so a checkout or a test can redirect the whole search.
SKILLS_REL = Path("skills")
USER_SKILLS = Path("~/.claude/skills")

#: A skill name is a single path component, never a path: this is what keeps
#: `load_skill("../../etc/passwd")` (or an absolute path) from walking a
#: search directory anywhere the caller did not intend. Leading underscore is
#: allowed because real directories like `__pycache__` exist alongside skills
#: on some search paths and must not raise a validation error just for being
#: looked up (they still fail as "not found", which is correct).
_SKILL_NAME_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9._-]*$")


class SkillNotFoundError(LookupError):
    """No `SKILL.md` for that name on any search path.

    Carries the paths tried, because "skill not found" is nearly always a
    search-path problem and the list is the fix.
    """

    def __init__(self, name: str, tried: Iterable[Path]):
        self.name = name
        self.tried = [Path(p) for p in tried]
        joined = "\n  ".join(str(p) for p in self.tried) or "(no search paths)"
        super().__init__(f"no skill named {name!r}. Looked for SKILL.md under:\n  {joined}")


class SkillParseError(ValueError):
    """The file exists but is not a skill spec: no frontmatter, an unclosed
    fence, invalid YAML in the frontmatter, or a file that could not be
    decoded as UTF-8 / read from disk."""


# --------------------------------------------------------------------------- #
# frontmatter
# --------------------------------------------------------------------------- #

def _split_frontmatter(text: str) -> tuple[str, str]:
    """`(frontmatter_source, body)` for a `---`-delimited file.

    A file with no frontmatter is a parse error rather than an empty dict: the
    description and model live there, and silently returning `{}` would send a
    skill to the model stripped of the half that routes it. The closing fence
    may immediately follow the opening one (empty frontmatter is valid, if
    useless) — the inner newline before it is optional for exactly that case.
    """
    if not text.startswith("---"):
        raise SkillParseError("no YAML frontmatter (file does not start with '---')")
    # `---\n` … optionally more … `---\n`; the closing fence must be alone on
    # its line, but may follow the opening fence with nothing between them.
    match = re.match(r"^---[^\S\n]*\n(.*?)\n?---[^\S\n]*(?:\n|$)", text, re.DOTALL)
    if not match:
        raise SkillParseError("frontmatter is not closed by a '---' line")
    return match.group(1), text[match.end():]


def _strip_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def _parse_frontmatter(source: str) -> dict:
    """Parse the frontmatter, preferring PyYAML and falling back to a subset.

    PyYAML is not a dependency of this package (`llmsx` installs with none), so
    the fallback handles exactly what the skill files in this estate actually
    use: top-level scalars, folded/literal block scalars (`>`, `>-`, `|`, `|-`),
    block and inline lists, and one level of nested mapping. Anything deeper is
    kept as raw text rather than guessed at — a mangled value would be worse
    than an unparsed one, and nothing downstream reads past that depth.

    When PyYAML *is* available, aliases (`&anchor` / `*alias`) are refused
    rather than resolved: a `SKILL.md` is not always a trusted file (see the
    module docstring), and unbounded alias expansion turns a few hundred
    bytes of frontmatter into millions of objects in memory — the classic
    "billion laughs" shape, just spelled in YAML instead of XML.
    """
    try:
        import yaml  # noqa: PLC0415 — optional, checked at call time by design
    except ImportError:
        logger.info("PyYAML not installed; parsing frontmatter with the bounded subset parser")
        return _parse_frontmatter_subset(source)
    try:
        data = yaml.load(source, Loader=_NoAliasSafeLoader(yaml))
    except yaml.YAMLError as exc:
        raise SkillParseError(f"invalid YAML frontmatter: {exc}") from exc
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise SkillParseError("frontmatter is not a mapping")
    return data


def _NoAliasSafeLoader(yaml_module):  # noqa: N802 — factory, reads like the class it returns
    """A `SafeLoader` subclass that raises on any YAML alias (`*name`).

    Built lazily inside `_parse_frontmatter` (only once PyYAML is known to be
    importable) rather than at module import time, since `yaml` itself is an
    optional dependency this module must not require just to be imported.
    """
    class _Loader(yaml_module.SafeLoader):
        def compose_node(self, parent, index):
            if self.check_event(yaml_module.AliasEvent):
                event = self.get_event()
                raise yaml_module.constructor.ConstructorError(
                    None, None,
                    f"aliases are not allowed in skill frontmatter (found {event.anchor!r})",
                    event.start_mark)
            return super().compose_node(parent, index)
    return _Loader


def _indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _parse_frontmatter_subset(source: str) -> dict:
    """A deliberately small YAML subset: top-level `key: scalar` / `key:
    [inline, list]` / `key:` + indented block-list or one-level nested
    mapping / folded (`>`, `>-`) or literal (`|`, `|-`) block scalars.
    Anything outside that grammar (deeper nesting, flow mappings, YAML tags,
    multi-document files, …) is left unset rather than mis-parsed — see the
    module docstring for why "unparsed" beats "guessed wrong" here.
    """
    lines = source.split("\n")
    out: dict = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#") or _indent_of(line) > 0:
            i += 1
            continue
        match = re.match(r"^([A-Za-z_][\w.-]*):(.*)$", line)
        if not match:
            i += 1
            continue
        key, rest = match.group(1), match.group(2).strip()

        if rest in (">", ">-", ">+", "|", "|-", "|+"):
            block, i = _collect_indented(lines, i + 1)
            folded = rest.startswith(">")
            out[key] = _fold(block) if folded else "\n".join(block).rstrip("\n")
            if rest.endswith("-"):
                out[key] = out[key].rstrip("\n")
            continue

        if rest.startswith("[") and rest.endswith("]"):
            inner = rest[1:-1].strip()
            out[key] = [_strip_scalar(p) for p in inner.split(",") if p.strip()] if inner else []
            i += 1
            continue

        if rest:
            out[key] = _strip_scalar(rest)
            i += 1
            continue

        # `key:` with nothing after it: a block list, a nested mapping, or empty.
        block, i = _collect_indented(lines, i + 1)
        if not block:
            out[key] = None
        elif block[0].lstrip().startswith("- "):
            out[key] = [_strip_scalar(b.lstrip()[2:]) for b in block if b.lstrip().startswith("- ")]
        else:
            out[key] = _parse_nested(block)
    return out


def _collect_indented(lines: list[str], start: int) -> tuple[list[str], int]:
    """Lines belonging to the block opened at `start`, plus the next index."""
    block: list[str] = []
    i = start
    while i < len(lines):
        line = lines[i]
        if line.strip() and _indent_of(line) == 0:
            break
        block.append(line)
        i += 1
    while block and not block[-1].strip():
        block.pop()
    if not block:
        return [], i
    pad = min(_indent_of(b) for b in block if b.strip())
    return [b[pad:] if len(b) >= pad else b for b in block], i


def _fold(block: list[str]) -> str:
    """YAML folded-scalar semantics: newline joins, blank line breaks."""
    parts: list[str] = []
    current: list[str] = []
    for line in block:
        if line.strip():
            current.append(line.strip())
        else:
            if current:
                parts.append(" ".join(current))
                current = []
    if current:
        parts.append(" ".join(current))
    return "\n\n".join(parts)


def _parse_nested(block: list[str]) -> dict:
    """One level of nested mapping; values kept as raw text."""
    nested: dict = {}
    i = 0
    while i < len(block):
        line = block[i]
        match = re.match(r"^([A-Za-z_][\w.-]*):(.*)$", line)
        if not match or _indent_of(line) > 0:
            i += 1
            continue
        key, rest = match.group(1), match.group(2).strip()
        if rest in (">", ">-", ">+", "|", "|-", "|+"):
            inner, i = _collect_indented(block, i + 1)
            nested[key] = "\n".join(inner)
            continue
        nested[key] = _strip_scalar(rest) if rest else None
        i += 1
    return nested


# --------------------------------------------------------------------------- #
# the skill
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Skill:
    """One parsed `SKILL.md`: its frontmatter, its body, and where it came from."""

    name: str
    path: Path
    frontmatter: dict = field(repr=False)
    body: str = field(repr=False)

    @property
    def description(self) -> str:
        return str(self.frontmatter.get("description") or "").strip()

    @property
    def model(self) -> str | None:
        """The model the skill declares it wants to run under, if any.

        Advisory: `run_skill` uses it as a default and the caller overrides it.
        The sibling `effort` key is deliberately *not* forwarded to the API —
        it is a hint for an agent harness, not a Messages API parameter.
        """
        value = self.frontmatter.get("model")
        return str(value) if value else None

    @property
    def effort(self) -> str | None:
        value = self.frontmatter.get("effort")
        return str(value) if value else None

    @property
    def references_dir(self) -> Path:
        return self.path.parent / "references"

    def reference_files(self) -> list[Path]:
        """Every `references/*.md` beside the skill, sorted by name.

        Returns the whole directory rather than only the files the body names:
        the bodies cite them inconsistently (some by full path, some by bare
        filename, some only in prose), so filtering on citations drops files
        the skill genuinely depends on.

        A file resolving outside `references_dir` — a symlink planted
        alongside an otherwise-legitimate skill — is skipped rather than
        folded into a system prompt sent to a remote API: the content such a
        symlink points at would otherwise be exfiltrated to that API and
        potentially echoed back in the model's answer, the same class of
        escape `llmsx.concepts`'s pack-file reads are guarded against.
        """
        directory = self.references_dir
        if not directory.is_dir():
            return []
        directory_r = directory.resolve()
        out = []
        for p in sorted(directory.glob("*.md")):
            if not p.is_file():
                continue
            if not p.resolve().is_relative_to(directory_r):
                logger.warning("skipping reference %s: resolves outside references/ "
                               "(symlink escape?)", p)
                continue
            out.append(p)
        return out

    def read_references(self, *, max_chars: int = DEFAULT_MAX_REFERENCE_CHARS) -> dict[str, str]:
        """Every reference file's text, keyed by filename, capped at
        `max_chars` combined. A file past the remaining budget is truncated
        with a visible marker rather than silently dropped when partial room
        remains, and skipped with a logged warning when none does — either
        way the caller can see, before paying for the request, that the
        prompt was not the full references/ directory."""
        out: dict[str, str] = {}
        total = 0
        for p in self.reference_files():
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                logger.warning("skipping unreadable reference %s: %s", p, exc)
                continue
            remaining = max_chars - total
            if remaining <= 0:
                logger.warning("dropping reference %s: reference budget (%d chars) exhausted",
                               p, max_chars)
                continue
            if len(text) > remaining:
                text = text[:remaining] + "\n[... truncated, reference budget exhausted ...]"
            out[p.name] = text
            total += len(text)
        return out

    def system_prompt(self, *, include_references: bool = False) -> str:
        """The system message: the skill's own instructions, verbatim.

        The body is passed through unedited — it is the artifact under test, and
        a library that paraphrased it would be running something other than the
        skill the caller asked for. Only a short provenance header and, on
        request, the reference files are added around it.
        """
        parts = [f"You are running the skill `{self.name}`."]
        if self.description:
            parts.append(f"Skill description:\n{self.description}")
        parts.append(self.body.strip())
        if include_references:
            for filename, text in self.read_references().items():
                parts.append(f"--- reference: references/{filename} ---\n{text.strip()}")
        return "\n\n".join(p for p in parts if p)


@dataclass(frozen=True)
class SkillRun:
    """What a model returned for one `run_skill` call."""

    text: str
    skill: str
    model: str
    stop_reason: str | None = None
    usage: dict | None = None
    raw: object = field(default=None, repr=False)


# --------------------------------------------------------------------------- #
# loading
# --------------------------------------------------------------------------- #

def _repo_skills_dirs() -> list[Path]:
    """Every `skills/` directory at or above the working directory, then this
    checkout's own — nearest first, but *all* of them, not just the first
    hit. That differs from `tree.default_data_path()`, which walks the same
    ancestors but stops at its first match: this function layers every
    ancestor `skills/` so a repo-local skill can shadow a broader one, while
    `default_data_path()` only ever wants a single tree.json.

    The installed-checkout fallback is only added when it actually exists —
    a wheel install has no such directory, so nothing nonexistent is added
    to the search path (and, in turn, never appears in a `SkillNotFoundError`
    "looked for" list as a path that could not possibly have helped).
    """
    found: list[Path] = []
    cwd = Path.cwd().resolve()
    for base in (cwd, *cwd.parents):
        candidate = base / SKILLS_REL
        if candidate.is_dir():
            found.append(candidate)
    installed = Path(__file__).resolve().parents[2] / SKILLS_REL
    if installed.is_dir() and installed not in found:
        found.append(installed)
    return found


def skill_search_paths() -> list[Path]:
    """Directories searched by `load_skill`, in order.

    `$LLMSX_SKILL_PATH` (os.pathsep-separated) wins when set, then every
    `skills/` at or above the cwd, then `~/.claude/skills`.
    """
    env = os.environ.get("LLMSX_SKILL_PATH")
    paths = [Path(p).expanduser() for p in env.split(os.pathsep) if p.strip()] if env else []
    paths.extend(_repo_skills_dirs())
    user = USER_SKILLS.expanduser()
    if user not in paths:
        paths.append(user)
    return paths


def load_skill(name: str, *, search_paths: Iterable[Path] | None = None) -> Skill:
    """Find `<dir>/<name>/SKILL.md` on the search path and parse it.

    Raises `SkillNotFoundError` (never returns None) so a typo fails loudly at
    the call site instead of arriving as an empty prompt at the API. `name`
    must be a single path component — no separator, no `..`, not absolute —
    or it is rejected the same way a genuinely missing name would be, rather
    than being joined onto a search directory and potentially resolving
    outside it.
    """
    if not name or not str(name).strip() or not _SKILL_NAME_RE.match(str(name)):
        raise SkillNotFoundError(str(name), [])
    paths = [Path(p) for p in search_paths] if search_paths is not None else skill_search_paths()
    tried: list[Path] = []
    for directory in paths:
        candidate = Path(directory).expanduser() / name / "SKILL.md"
        tried.append(candidate)
        if candidate.is_file():
            return load_skill_file(candidate, name=name)
    raise SkillNotFoundError(name, tried)


def load_skill_file(path: str | Path, *, name: str | None = None) -> Skill:
    """Parse one `SKILL.md` by path, bypassing the search."""
    p = Path(path).expanduser()
    if not p.is_file():
        raise SkillNotFoundError(name or str(p), [p])
    try:
        size = p.stat().st_size
        if size > MAX_SKILL_FILE_BYTES:
            raise SkillParseError(
                f"{p} is {size} bytes, over the {MAX_SKILL_FILE_BYTES}-byte limit for a SKILL.md")
        text = p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise SkillParseError(f"{p} could not be read: {exc}") from exc
    frontmatter_src, body = _split_frontmatter(text)
    frontmatter = _parse_frontmatter(frontmatter_src)
    resolved = str(frontmatter.get("name") or name or p.parent.name)
    return Skill(name=resolved, path=p, frontmatter=frontmatter, body=body)


def available_skills(*, search_paths: Iterable[Path] | None = None) -> list[str]:
    """Every skill name on the search path, deduped, first-hit order preserved."""
    paths = [Path(p) for p in search_paths] if search_paths is not None else skill_search_paths()
    names: list[str] = []
    seen: set[str] = set()
    for directory in paths:
        directory = Path(directory).expanduser()
        if not directory.is_dir():
            continue
        try:
            children = sorted(directory.iterdir())
        except OSError as exc:
            logger.warning("could not list %s: %s", directory, exc)
            continue
        for child in children:
            if child.name in seen:
                continue
            if (child / "SKILL.md").is_file():
                seen.add(child.name)
                names.append(child.name)
    return names


# --------------------------------------------------------------------------- #
# running
# --------------------------------------------------------------------------- #

#: create()-kwargs `run_skill` computes itself; a caller passing one via
#: **create_kwargs would otherwise silently replace it, which — layered on
#: top of an attacker-controlled skill file (see the module docstring) — is
#: a way to redirect an outbound request's prompt, model, or spend without
#: any visible sign that happened.
_RESERVED_CREATE_KWARGS = frozenset({"model", "system", "messages", "max_tokens"})


def _default_client():
    try:
        import anthropic  # noqa: PLC0415 — optional extra, resolved at call time
    except ImportError as exc:
        raise RuntimeError(
            "no client passed and the `anthropic` package is not installed — "
            "install it with `pip install 'llmsx[skills]'`, or pass client=…"
        ) from exc
    # An explicit budget rather than the SDK's default (connect 5s, everything
    # else 600s, 2 retries) — a hung call should not leave the CLI apparently
    # frozen for up to ten minutes with no output.
    return anthropic.Anthropic(timeout=120.0, max_retries=1)


def _extract_text(response: object) -> str:
    """The text of a Messages API response, tolerating a fake that returns str.

    A fake client in a test may hand back a plain string or a dict; the real
    SDK hands back an object whose `.content` is a list of blocks. All three
    are accepted so a caller never has to build an SDK-shaped mock to test
    their own code path.
    """
    if isinstance(response, str):
        return response
    content = response.get("content") if isinstance(response, dict) else getattr(
        response, "content", None)
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    parts: list[str] = []
    for block in content:
        text = block.get("text") if isinstance(block, dict) else getattr(block, "text", None)
        if text:
            parts.append(text)
    return "".join(parts)


def _get(response: object, key: str):
    if isinstance(response, dict):
        return response.get(key)
    return getattr(response, key, None)


def run_skill(
    skill: Skill | str,
    task_input: str,
    *,
    client: object | Callable | None = None,
    model: str | None = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    include_references: bool = False,
    extra_system: str | None = None,
    cache_system: bool = False,
    **create_kwargs,
) -> SkillRun:
    """Run one turn of `skill` over `task_input` and return what came back.

    `client` is anything with `.messages.create(**kwargs)` (the Anthropic SDK
    shape), or a plain callable taking those same kwargs — the callable form is
    what the tests use, and what any caller can use to record, cache or stub the
    call without importing the SDK. Omitted, it builds `anthropic.Anthropic()`
    and raises a clear RuntimeError if the optional extra is not installed.

    One turn: no tool loop, no multi-pass convergence, no filesystem writes. See
    the module docstring for why that is the honest boundary of this function.

    `**create_kwargs` is for genuinely extra `messages.create()` parameters
    (e.g. `temperature=`, `top_p=`) — it may not name `model`, `system`,
    `messages`, or `max_tokens`, which this function computes itself and
    passes as their own named parameters; a `ValueError` names the offending
    key rather than silently letting it overwrite the computed value.

    `cache_system=True` sends the system prompt as a cacheable content block
    (`cache_control: {"type": "ephemeral"}`) instead of a plain string — worth
    it for a skill invoked repeatedly with the same body, since the system
    prompt is the expensive, byte-stable part of the request. Off by default
    so a caller inspecting `system` as a string (as every test in this
    package's own suite does) is not surprised by a shape change.
    """
    if isinstance(skill, str):
        skill = load_skill(skill)
    if not task_input or not str(task_input).strip():
        raise ValueError("task_input is empty — nothing for the skill to act on")
    reserved = _RESERVED_CREATE_KWARGS & create_kwargs.keys()
    if reserved:
        raise ValueError(
            f"run_skill computes {sorted(reserved)} itself — pass them as their own "
            f"keyword arguments (e.g. model=...), not inside the extra create() kwargs")

    system = skill.system_prompt(include_references=include_references)
    if extra_system:
        system = f"{system}\n\n{extra_system}"
    chosen = model or skill.model or DEFAULT_MODEL
    system_field: object = (
        [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]
        if cache_system else system)

    kwargs = {
        "model": chosen,
        "max_tokens": max_tokens,
        "system": system_field,
        "messages": [{"role": "user", "content": task_input}],
        **create_kwargs,
    }

    if client is None:
        client = _default_client()
    if callable(client) and not hasattr(client, "messages"):
        response = client(**kwargs)
    else:
        response = client.messages.create(**kwargs)

    usage = _get(response, "usage")
    if usage is not None and not isinstance(usage, dict):
        usage = getattr(usage, "model_dump", lambda: None)() or {
            "input_tokens": getattr(usage, "input_tokens", None),
            "output_tokens": getattr(usage, "output_tokens", None),
        }
    stop_reason = _get(response, "stop_reason")
    text = _extract_text(response)
    if not text and stop_reason:
        logger.warning("skill %s: model returned no text (stop_reason=%s)", skill.name, stop_reason)
    return SkillRun(
        text=text,
        skill=skill.name,
        model=chosen,
        stop_reason=stop_reason,
        usage=usage,
        raw=response,
    )


__all__ = [
    "DEFAULT_MAX_REFERENCE_CHARS",
    "DEFAULT_MAX_TOKENS",
    "DEFAULT_MODEL",
    "MAX_SKILL_FILE_BYTES",
    "Skill",
    "SkillNotFoundError",
    "SkillParseError",
    "SkillRun",
    "available_skills",
    "load_skill",
    "load_skill_file",
    "run_skill",
    "skill_search_paths",
]
