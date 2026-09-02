"""Pages in, anchored knowledge units out — deterministically.

A *unit* is one atomic thing a page says, carrying the source and anchor it came
from. The llms family's facts file is a list of them; the topical files of
component 19 are them grouped; the coverage score counts them. Everything after
ingestion is arithmetic over this list.

**Deterministic on purpose.** Every rule below is a regex or a shape test, no
model is called, and the same corpus always yields the same units in the same
order. That is what makes the free tier possible (no tokens are spent), what
makes the output diffable across runs, and what makes the metered model passes —
which polish wording and classify the genuinely borderline — an *improvement* on
a working result rather than a prerequisite for one. Component 19 §8 records
that seam.

The type vocabulary is the hub's ``docset_refine.UNIT_TYPES``, not a second one:
``concept``, ``fact``, ``actionable``, ``question``, ``problem``, ``statement``,
``quote``, ``idea``, ``snippet``, ``parameter``, ``definition``, ``change``. A
new type here would be a type the hub's exporter cannot render.

The one judgement call the module makes is the *order* of the classifiers.
``definition`` beats ``fact`` beats ``actionable`` beats ``statement``, because
a sentence that both defines a term and quotes a number is more useful filed
under the term. :data:`CLASSIFIERS` is that order, written once.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Sequence
from dataclasses import dataclass, field

from .ingest import Corpus, Page

#: `docset_refine.UNIT_TYPES`. Kept identical so an export renders.
UNIT_TYPES: tuple[str, ...] = (
    "concept", "fact", "actionable", "question", "problem", "statement",
    "quote", "idea", "snippet", "parameter", "definition", "change",
)

#: Shorter than this and a "sentence" is a fragment, a caption or a stray label.
MIN_UNIT_CHARS = 25
#: Longer than this and it is a paragraph pretending to be a unit; it gets split
#: at sentence boundaries first, and only survives whole if it cannot be.
MAX_UNIT_CHARS = 600

_FENCE_RE = re.compile(r"^(?P<fence>```|~~~)(?P<lang>[\w+-]*)\s*$")
_HEADING_LINE_RE = re.compile(r"^#{1,6}\s+(.+?)\s*#*$")
_BULLET_RE = re.compile(r"^\s{0,6}(?:[-*+]|\d{1,3}[.)])\s+(?P<text>.+)$")
_TABLE_ROW_RE = re.compile(r"^\s*\|(?P<cells>.+)\|\s*$")
_QUOTE_RE = re.compile(r"^\s{0,3}>\s?(?P<text>.+)$")

# A sentence end: terminal punctuation, then whitespace, then something that
# starts a new sentence. The lookbehind excludes the common abbreviations that
# would otherwise cut "e.g. this" in half.
_SENTENCE_SPLIT_RE = re.compile(
    r"(?<![A-Z])(?<!\be\.g)(?<!\bi\.e)(?<!\bcf)(?<!\bvs)(?<!\bNo)(?<!\betc)"
    r"(?<=[.!?])[ \t]+(?=[\"'(\[]?[A-Z0-9])"
)

# --- the classifier patterns --------------------------------------------------

_DEFINITION_RE = re.compile(
    r"^(?P<term>[A-Z][\w .`'\-/()]{1,60}?)\s+"
    r"(?:is|are|means|refers to|denotes|describes|stands for)\s+"
    r"(?:a|an|the|any|two|three|not|when|how|what|where|why)\b",
)
_DEFINITION_DASH_RE = re.compile(r"^(?P<term>[`\w][\w .`'\-/()]{1,60}?)\s+[—–-]{1,2}\s+\S")
_DEFINITION_COLON_RE = re.compile(r"^\*\*(?P<term>[^*]{2,60})\*\*\s*[:—–-]\s*\S")

_NUMBER_RE = re.compile(
    r"(?<![\w.])(?:\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s*"
    r"(?:%|ms|s\b|kb|mb|gb|tb|k\b|x\b|×|/s|per\b)?",
    re.IGNORECASE,
)
_VERSION_RE = re.compile(r"\bv?\d+\.\d+(?:\.\d+)?\b")
_DATE_RE = re.compile(
    r"\b(?:19|20)\d{2}(?:-\d{2}-\d{2})?\b|"
    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}\b",
)

# Written as one string and split, not as a list literal: a hundred one-word
# list items is a hundred lines of quotes and commas to review, and the point
# of the set is that it reads as a word list.
_IMPERATIVE_WORDS = """
add allow apply avoid build call cancel check choose clear clone close commit
configure confirm connect copy create declare define delete deploy disable
download drop edit enable ensure enter export extract fetch fix follow generate
grant import include increase initialise initialize inspect install invoke keep
launch limit list load lock log make measure merge migrate mount move never open
pass pick pin prefer prepare provide publish pull push read rebuild record
refresh register reject reload remove rename render replace request require
reset resolve restart restore retry return revoke rotate run save scale select
send set setup ship show sign skip sort split start stop store submit switch
sync tag test throttle track treat trim update upgrade upload use validate
verify wait wrap write
audit batch benchmark cache emit enforce escalate flush index invalidate patch
poll profile prune purge queue seed snapshot subscribe unsubscribe
"""
_IMPERATIVE_VERBS = frozenset(_IMPERATIVE_WORDS.split())

_PROBLEM_MARKERS = re.compile(
    r"\b(?:fail(?:s|ed|ure)?|error|breaks?|broken|cannot|can't|won't|does not|"
    r"doesn't|is not|isn't|bug|crash(?:es|ed)?|leak|regress(?:ion|es)?|"
    r"unsupported|deprecated|warning|refus(?:es|ed)|reject(?:s|ed)|timeout|"
    r"exceeds?|conflict|mismatch|missing|invalid|unsafe|risk)\b",
    re.IGNORECASE,
)
_CHANGE_MARKERS = re.compile(
    r"\b(?:added|removed|renamed|deprecated|introduced|dropped|replaced|"
    r"changed|moved|since v?\d|as of|no longer|now (?:returns|requires|uses)|"
    r"breaking change|migrat(?:ed|ion))\b",
    re.IGNORECASE,
)
_IDEA_MARKERS = re.compile(
    r"\b(?:could|might|perhaps|consider(?:ing)?|proposal|propose[ds]?|"
    r"we should|worth (?:doing|trying|considering)|future|one option|"
    r"an alternative|idea)\b",
    re.IGNORECASE,
)
_PARAMETER_RE = re.compile(
    r"^[`*]{0,2}(?P<name>[A-Za-z_][\w.\-]{1,48})[`*]{0,2}\s*"
    r"(?:\((?P<type>[^)]{1,40})\))?\s*[:—–-]\s+(?P<desc>\S.{4,})$",
)

_STOP_TOKEN_RE = re.compile(r"[a-z][a-z0-9+.#/_-]{1,}", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class Unit:
    """One atomic thing a page says, with the source that says it."""

    type: str
    text: str
    source: str
    anchor: str
    #: The nearest heading's text, kept for topic seeding and for the reader.
    heading: str = ""
    #: The page title, so a unit can name its document without a second lookup.
    document: str = ""
    #: Language of a `snippet`; empty for everything else.
    language: str = ""
    #: Lowercased content tokens, computed once, used by coverage and dedup.
    tokens: frozenset[str] = field(default_factory=frozenset)

    @property
    def url(self) -> str:
        return f"{self.source}#{self.anchor}"

    @property
    def key(self) -> str:
        """Identity for deduplication: the normalised text, not the source.

        Two pages saying the same sentence are one unit with two witnesses, and
        counting them twice inflates every depth measure in `coverage`.
        """
        return hashlib.sha256(_normalise(self.text).encode("utf-8")).hexdigest()[:16]

    def as_dict(self) -> dict[str, object]:
        return {"type": self.type, "text": self.text, "source": self.source,
                "anchor": self.anchor, "url": self.url, "heading": self.heading,
                "document": self.document, "language": self.language}


def _normalise(text: str) -> str:
    """Casefolded, punctuation-light form used for identity only."""
    return re.sub(r"[^a-z0-9 ]+", " ", text.casefold()).strip()


def tokenize(text: str) -> frozenset[str]:
    """Content tokens of ``text``, lowercased, stopwords removed.

    A set, not a list: every consumer asks "does this unit mention X", never
    "how often". Frequency lives in :mod:`llmsx.coverage`, computed across
    units, where it means something.
    """
    return frozenset(
        token.lower() for token in _STOP_TOKEN_RE.findall(text)
        if len(token) > 2 and token.lower() not in STOPWORDS
    )


#: English function words plus the handful of doc-boilerplate words that appear
#: in every corpus and therefore distinguish nothing in any of them.
_STOPWORD_TEXT = """
the and for that with this from you your are was were will would can could
should have has had not but they them their there here when what which who whom
whose why how all any both each few more most other some such only own same than
too very just about above after again against because been before being below
between during into once over under until while these those then they're its
it's don't doesn't isn't aren't wasn't weren't cannot may might must shall also
one two three four five six seven eight nine ten new old get got make made see
seen use used using like via per etc eg ie note noted following follows example
examples section sections page pages document documents doc docs file files
"""
STOPWORDS: frozenset[str] = frozenset(_STOPWORD_TEXT.split())


# --- classifiers ---------------------------------------------------------------


def _is_definition(text: str) -> bool:
    return bool(
        _DEFINITION_COLON_RE.match(text)
        or _DEFINITION_RE.match(text)
        or (_DEFINITION_DASH_RE.match(text) and len(text) <= 300)
    )


def _is_question(text: str) -> bool:
    return text.rstrip().endswith("?")


def _is_change(text: str) -> bool:
    return bool(_CHANGE_MARKERS.search(text))


def _is_problem(text: str) -> bool:
    return bool(_PROBLEM_MARKERS.search(text))


def _is_fact(text: str) -> bool:
    """A claim with something checkable in it: a number, a version, a date."""
    return bool(_VERSION_RE.search(text) or _DATE_RE.search(text)
                or _NUMBER_RE.search(text))


def _is_actionable(text: str) -> bool:
    """Starts with an imperative, or tells the reader to do something."""
    first = re.sub(r"^[^A-Za-z]+", "", text).split(" ", 1)[0].lower().strip(".,:;")
    if first in _IMPERATIVE_VERBS:
        return True
    return bool(re.match(r"^(?:you (?:should|must|can)|to \w+,)\b", text, re.IGNORECASE))


def _is_idea(text: str) -> bool:
    return bool(_IDEA_MARKERS.search(text))


#: Order is the precedence rule of the module docstring. First match wins.
CLASSIFIERS: tuple[tuple[str, object], ...] = (
    ("question", _is_question),
    ("definition", _is_definition),
    ("change", _is_change),
    ("problem", _is_problem),
    ("fact", _is_fact),
    ("actionable", _is_actionable),
    ("idea", _is_idea),
)


def classify(text: str) -> str:
    """The unit type of one sentence. ``statement`` is the honest fallback."""
    for name, test in CLASSIFIERS:
        if test(text):                                        # type: ignore[operator]
            return name
    return "statement"


# --- extraction ----------------------------------------------------------------


def split_sentences(text: str) -> list[str]:
    """``text`` into sentences, keeping list markers and inline code intact."""
    parts = [p.strip() for p in _SENTENCE_SPLIT_RE.split(text.strip()) if p.strip()]
    return parts or ([text.strip()] if text.strip() else [])


def _clean(text: str) -> str:
    """Collapse whitespace and drop markdown scaffolding a reader does not need."""
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"^[#>*\-+\s]+", "", text)
    return text.strip(" \t*_")


def _emit(bucket: list[Unit], *, type_: str, text: str, page: Page, offset: int,
          heading: str, language: str = "") -> None:
    text = _clean(text) if type_ != "snippet" else text.rstrip()
    if type_ != "snippet" and not (MIN_UNIT_CHARS <= len(text) <= MAX_UNIT_CHARS):
        return
    if type_ == "snippet" and len(text) < MIN_UNIT_CHARS:
        return
    bucket.append(Unit(type=type_, text=text, source=page.source,
                       anchor=page.anchor_at(offset), heading=heading,
                       document=page.title, language=language,
                       tokens=tokenize(f"{heading} {text}")))


def units_of_page(page: Page) -> list[Unit]:
    """Every unit :func:`build_corpus` made this page able to yield.

    Walks the body once, line by line, tracking the current heading and whether
    it is inside a fence, so an anchor is always the heading the reader would
    scroll to and a code block is never sentence-split.
    """
    out: list[Unit] = []
    heading = ""
    offset = 0
    fence: str | None = None
    fence_lang = ""
    fence_start = 0
    fence_lines: list[str] = []
    paragraph: list[str] = []
    paragraph_start = 0

    def flush_paragraph() -> None:
        nonlocal paragraph
        if not paragraph:
            return
        joined = " ".join(paragraph).strip()
        paragraph = []
        for sentence in split_sentences(joined):
            _emit(out, type_=classify(sentence), text=sentence, page=page,
                  offset=paragraph_start, heading=heading)

    for raw in page.body.splitlines(keepends=True):
        line = raw.rstrip("\n")
        stripped = line.strip()

        fence_match = _FENCE_RE.match(stripped)
        if fence is not None:
            if stripped.startswith(fence):
                _emit(out, type_="snippet", text="\n".join(fence_lines), page=page,
                      offset=fence_start, heading=heading, language=fence_lang)
                fence, fence_lang, fence_lines = None, "", []
            else:
                fence_lines.append(line)
            offset += len(raw)
            continue
        if fence_match:
            flush_paragraph()
            fence = fence_match.group("fence")
            fence_lang = fence_match.group("lang")
            fence_start = offset
            fence_lines = []
            offset += len(raw)
            continue

        head = _HEADING_LINE_RE.match(stripped)
        if head:
            flush_paragraph()
            heading = head.group(1).strip()
            # The heading itself is a `concept` unit: it is the corpus telling
            # us a topic exists, which is exactly what coverage needs seeded.
            _emit(out, type_="concept", text=f"{heading} — {page.title}",
                  page=page, offset=offset, heading=heading)
            offset += len(raw)
            continue

        if not stripped:
            flush_paragraph()
            offset += len(raw)
            continue

        quote = _QUOTE_RE.match(line)
        if quote:
            flush_paragraph()
            _emit(out, type_="quote", text=quote.group("text"), page=page,
                  offset=offset, heading=heading)
            offset += len(raw)
            continue

        table = _TABLE_ROW_RE.match(line)
        if table:
            flush_paragraph()
            cells = [c.strip() for c in table.group("cells").split("|")]
            if len(cells) >= 2 and not all(set(c) <= {"-", ":"} for c in cells):
                name, rest = cells[0], " — ".join(c for c in cells[1:] if c)
                if rest:
                    _emit(out, type_="parameter", text=f"{name} — {rest}", page=page,
                          offset=offset, heading=heading)
            offset += len(raw)
            continue

        bullet = _BULLET_RE.match(line)
        if bullet:
            flush_paragraph()
            text = bullet.group("text").strip()
            param = _PARAMETER_RE.match(text)
            type_ = "parameter" if param else classify(text)
            _emit(out, type_=type_, text=text, page=page, offset=offset, heading=heading)
            offset += len(raw)
            continue

        if not paragraph:
            paragraph_start = offset
        paragraph.append(stripped)
        offset += len(raw)

    flush_paragraph()
    if fence is not None:                       # an unterminated fence still says something
        _emit(out, type_="snippet", text="\n".join(fence_lines), page=page,
              offset=fence_start, heading=heading, language=fence_lang)
    return out


@dataclass(frozen=True, slots=True)
class UnitPool:
    """Every unit in a corpus, deduplicated, with the witnesses kept.

    ``witnesses[key]`` is every source that said it. Two documents agreeing is
    evidence; the pool keeps that rather than throwing the second away, because
    :mod:`llmsx.coverage` scores a topic higher when independent material
    corroborates it.
    """

    units: Sequence[Unit]
    witnesses: dict[str, tuple[str, ...]] = field(default_factory=dict)
    #: Units dropped as near-duplicates, with the key they collapsed into.
    merged: int = 0

    def by_type(self, type_: str) -> list[Unit]:
        return [u for u in self.units if u.type == type_]

    @property
    def sources(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(u.source for u in self.units))

    def counts(self) -> dict[str, int]:
        out = dict.fromkeys(UNIT_TYPES, 0)
        for u in self.units:
            out[u.type] = out.get(u.type, 0) + 1
        return out


def _near_duplicate(a: Unit, b: Unit, *, threshold: float = 0.9) -> bool:
    """Jaccard over content tokens, for the same type.

    Guards the common case in loosely related material: two READMEs describing
    the same install step in almost the same words. Exact-hash dedup misses it;
    an embedding would catch more but costs a model, and this pipeline's free
    tier has none.
    """
    if a.type != b.type or not a.tokens or not b.tokens:
        return False
    shared = len(a.tokens & b.tokens)
    if not shared:
        return False
    return shared / len(a.tokens | b.tokens) >= threshold


def extract(corpus: Corpus) -> UnitPool:
    """Every unit in ``corpus``, deduplicated, witnesses preserved."""
    raw: list[Unit] = []
    for page in corpus.pages:
        raw.extend(units_of_page(page))

    kept: list[Unit] = []
    witnesses: dict[str, list[str]] = {}
    by_key: dict[str, Unit] = {}
    merged = 0
    # Bucketed by a cheap signature so near-duplicate checking stays linear-ish
    # rather than comparing every unit with every other one.
    buckets: dict[tuple[str, int], list[Unit]] = {}

    for unit in raw:
        key = unit.key
        if key in by_key:
            merged += 1
            if unit.source not in witnesses[key]:
                witnesses[key].append(unit.source)
            continue
        signature = (unit.type, len(unit.tokens) // 4)
        neighbours = buckets.setdefault(signature, [])
        duplicate = next((n for n in neighbours if _near_duplicate(unit, n)), None)
        if duplicate is not None:
            merged += 1
            if unit.source not in witnesses[duplicate.key]:
                witnesses[duplicate.key].append(unit.source)
            continue
        by_key[key] = unit
        witnesses[key] = [unit.source]
        neighbours.append(unit)
        kept.append(unit)

    return UnitPool(units=tuple(kept),
                    witnesses={k: tuple(v) for k, v in witnesses.items()},
                    merged=merged)


__all__ = [
    "CLASSIFIERS",
    "MAX_UNIT_CHARS",
    "MIN_UNIT_CHARS",
    "STOPWORDS",
    "UNIT_TYPES",
    "Unit",
    "UnitPool",
    "classify",
    "extract",
    "split_sentences",
    "tokenize",
    "units_of_page",
]
