#!/usr/bin/env python3
"""
Privacy gate for files this repository PUBLISHES.

This repo is public and installable (`npx skills add mithudso/llms-explorer`), and
site/src/pages/[...slug].astro renders every skills/<id>/SKILL.md verbatim on its
skill page. Anything written into a published file is therefore on the internet.
A skill authored as if it were an internal note once shipped six named customer
organisations, an absolute path carrying the operator's corporate account, and a
real support case number. This script exists so that cannot happen twice.

It detects by STRUCTURE, not by a list of names — a checked-in denylist of customer
names would itself be the disclosure. Operator-specific names go in a gitignored
`.privacy-denylist` (one term per line, `#` comments) or the PRIVACY_DENYLIST env
var, and are never committed.

Usage:
    check_publish_privacy.py                 # all published paths in the tree
    check_publish_privacy.py --staged        # only staged files (pre-commit hook)
    check_publish_privacy.py FILE [FILE...]  # explicit files

Escape hatch: a line containing `privacy-ok` is skipped. Use it only for a value
that is genuinely synthetic, and prefer an obviously-fake placeholder instead.

Exit 0 clean, 1 on any finding.
"""
import os, re, subprocess, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Paths whose contents reach the public: the installable skills (and the scripts
# that ship beside them), the site's content and pages, the agent commands, and
# the top-level markdown.
PUBLISHED = (
    ("skills/", (".md", ".py", ".sh", ".mjs", ".js", ".json", ".txt", ".yaml", ".yml")),
    ("site/src/content/", (".md", ".mdx")),
    ("site/src/pages/", (".astro", ".ts", ".js")),
    ("commands/", (".md",)),
)
ROOT_MD = ("README.md", "CLAUDE.md", "AGENTS.md", "GEMINI.md", "CONTRIBUTING.md")

SKIP_DIRS = {".git", "node_modules", "dist", ".venv", "__pycache__", ".astro",
             "outputs", "logs", "research", ".claude"}

# Structural patterns. Each is a shape that carries identity regardless of what
# the actual value is, so none of them needs a real example to match.
RULES = [
    ("operator home path",
     r"/Users/[A-Za-z0-9._-]+/",
     "absolute path naming a person's account; read it from an env var instead"),
    ("cloud-drive mount",
     r"CloudStorage|GoogleDrive-|Shared drives/",
     "path naming a private drive; read it from an env var instead"),
    # Not every address is a disclosure — specs and docs legitimately quote public
    # vendor contacts and example.com placeholders. The shape that actually leaked
    # was an address embedded in a filesystem path (a Drive mount named after the
    # operator's account). Employer domains belong in the operator denylist.
    ("email inside a path",
     r"[/\\][A-Za-z0-9._%+-]*[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
     r"|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}[/\\]",
     "an address inside a path names a person and their employer"),
    ("salesforce id",
     r"\b(?:001|003|006|500|a2c|aFw)[A-Za-z0-9]{12,15}\b",
     "CRM record identifier"),
    ("support case number",
     r"\bcase\s+0\d{7}\b|\b01[5-9]\d{5}\b",
     "real support case number"),
    ("tracker key",
     r"\b(?:HELP|AVAIL|TSCRITSIT|TSTOOLS|SERVER)-\d{2,}\b",
     "real ticket key; use <n> in syntax examples"),
    # A real Drive ID is mixed-case with digits; a lowercase hyphenated URL slug of
    # the same length is not one. Require both an uppercase letter and a digit.
    ("google doc id",
     r"\b1(?=[A-Za-z0-9_-]{42,44}\b)(?=[A-Za-z0-9_-]*[A-Z])"
     r"(?=[A-Za-z0-9_-]*[0-9])[A-Za-z0-9_-]{42,44}\b",
     "Drive document identifier"),
    ("slack channel id",
     r"\bC0[A-Z0-9]{8,}\b",
     "Slack channel identifier"),
    ("atlas object id",
     r"\b[0-9a-f]{24}\b",
     "24-hex identifier (Atlas org/project/cluster)"),
]
COMPILED = [(n, re.compile(p), why) for n, p, why in RULES]


def denylist():
    """Operator-supplied names. Never committed: .privacy-denylist is gitignored."""
    terms = []
    p = os.path.join(REPO, ".privacy-denylist")
    if os.path.exists(p):
        terms += [l.strip() for l in open(p) if l.strip() and not l.startswith("#")]
    terms += [t.strip() for t in os.environ.get("PRIVACY_DENYLIST", "").split(",")
              if t.strip()]
    return [t for t in terms if len(t) >= 2]


def published_files():
    out = []
    for prefix, exts in PUBLISHED:
        base = os.path.join(REPO, prefix)
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for fn in filenames:
                if fn.endswith(exts):
                    out.append(os.path.join(dirpath, fn))
    for fn in ROOT_MD:
        p = os.path.join(REPO, fn)
        if os.path.exists(p):
            out.append(p)
    return sorted(out)


def staged_files():
    r = subprocess.run(["git", "-C", REPO, "diff", "--cached", "--name-only",
                        "--diff-filter=ACM"], capture_output=True, text=True)
    keep = []
    for rel in r.stdout.split("\n"):
        rel = rel.strip()
        if not rel:
            continue
        for prefix, exts in PUBLISHED:
            if rel.startswith(prefix) and rel.endswith(exts):
                keep.append(os.path.join(REPO, rel))
        if rel in ROOT_MD:
            keep.append(os.path.join(REPO, rel))
    return [p for p in keep if os.path.exists(p)]


def scan(paths, deny):
    findings = []
    for p in paths:
        try:
            lines = open(p, errors="replace").read().split("\n")
        except OSError:
            continue
        rel = os.path.relpath(p, REPO)
        for i, line in enumerate(lines, 1):
            if "privacy-ok" in line:
                continue
            for name, rx, why in COMPILED:
                m = rx.search(line)
                if m:
                    findings.append((rel, i, name, m.group(0)[:60], why))
            low = line.lower()
            for term in deny:
                if term.lower() in low:
                    findings.append((rel, i, "denylisted term", term,
                                     "operator denylist"))
    return findings


def main(argv):
    deny = denylist()
    if "--staged" in argv:
        paths = staged_files()
        scope = "staged"
    elif [a for a in argv[1:] if not a.startswith("-")]:
        paths = [os.path.abspath(a) for a in argv[1:] if not a.startswith("-")]
        scope = "explicit"
    else:
        paths = published_files()
        scope = "tree"

    findings = scan(paths, deny)
    print(f"privacy gate: {len(paths)} published file(s) [{scope}] · "
          f"{len(deny)} denylist term(s)")
    if not findings:
        print("clean")
        return 0

    print(f"\n{len(findings)} finding(s) — these paths are PUBLISHED:\n")
    for rel, ln, name, val, why in findings:
        print(f"  {rel}:{ln}")
        print(f"      {name}: {val!r}")
        print(f"      {why}")
    print("\nFix the value, or append `privacy-ok` to the line if it is genuinely")
    print("synthetic. Do not add real names to this script — it ships publicly.")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
