"""The published optimizer must run its v3 checks without the private hub."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / ".claude/skills/llms-deep-optimizer"
SINGLE = """# Example

> A small public example.
> Source: https://example.com · Generated: 2026-11-09 by example v1 · Mode: single-file

## Facts
- One fact. [src: https://example.com]

## Sitemap
- https://example.com — Example page

## Resources
### Other
- (none) — no related resources were verified
"""


@pytest.fixture
def installed(tmp_path):
    dest = tmp_path / "installed"
    shutil.copytree(BUNDLE, dest, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return dest


def invoke(installed, tmp_path, *args):
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    env["PYTHONNOUSERSITE"] = "1"
    return subprocess.run(
        [sys.executable, "-S", str(installed / "scripts/llms_lint.py"), *map(str, args)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_single_file_and_legacy_commands_work_without_site_packages(installed, tmp_path):
    target = tmp_path / "llms.txt"
    target.write_text(SINGLE)
    detection = invoke(installed, tmp_path, "detect", target)
    assert detection.returncode == 0, detection.stderr
    assert json.loads(detection.stdout)["kind"] == "single"
    for command in (
        "structure", "links", "descriptions", "size", "full", "facts", "trust", "hygiene"
    ):
        result = invoke(installed, tmp_path, command, target)
        assert result.returncode == 0, (command, result.stdout, result.stderr)
        assert isinstance(json.loads(result.stdout)["findings"], list)
    checked = invoke(installed, tmp_path, "check", target, "--json")
    assert checked.returncode == 0, checked.stderr
    assert json.loads(checked.stdout)[0]["kind"] == "single"


def test_v3_single_size_and_required_sections_are_enforced(installed, tmp_path):
    target = tmp_path / "llms.txt"
    target.write_text(SINGLE.replace("## Resources", "## Notes") + ("x" * 33_000))
    checked = invoke(installed, tmp_path, "check", target, "--json")
    findings = json.loads(checked.stdout)[0]["findings"]
    assert checked.returncode == 1
    assert any(f["pass"] == "P16" and f["attr"] == "O1" for f in findings)
    assert any(f["pass"] == "P16" and f["attr"] == "O3" for f in findings)


def test_sitemap_counts_and_legacy_name_are_reported(installed, tmp_path):
    target = tmp_path / "llms-sitemap.txt"
    target.write_text("""# Example — sitemap

> Source: https://example.com · Generated: 2026-11-09 · Kind: website · Entries: 2

## Pages
- https://example.com — Example

## Resources
### Other
- (none) — no related resources were verified
""")
    result = invoke(installed, tmp_path, "check", target, "--json")
    findings = json.loads(result.stdout)[0]["findings"]
    assert any(f["attr"] == "M3" and "2" in f["msg"] for f in findings)
    legacy = tmp_path / "llms-filemap.txt"
    legacy.write_text(target.read_text())
    result = invoke(installed, tmp_path, "check", legacy, "--json")
    assert any(f["attr"] == "M0" for f in json.loads(result.stdout)[0]["findings"])


def test_missing_optional_mirror_helpers_are_not_a_pass(installed, tmp_path):
    target = tmp_path / "llms-facts.txt"
    target.write_text("# Facts\n\n- [fact] Example. — https://example.com/a#missing\n")
    mirror = tmp_path / "mirror.md"
    mirror.write_text("# Example\nSource: https://example.com/a\n\n## Other\n")
    result = invoke(installed, tmp_path, "facts", target, "--mirror", mirror)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert any(f["severity"] == "na" and "unavailable" in f["message"] for f in data["findings"])
    assert "mirror anchor resolution unavailable" in result.stderr


def test_lint_does_not_fetch_by_default(installed, tmp_path):
    target = tmp_path / "llms.txt"
    target.write_text(SINGLE)
    code = """import sys, urllib.request
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import _ldo_v3
urllib.request.urlopen = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError('network'))
result = _ldo_v3.check(Path(sys.argv[2]))
assert result['kind'] == 'single'
"""
    result = subprocess.run(
        [sys.executable, "-S", "-c", code, str(installed / "scripts"), str(target)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_full_file_parser_is_bundled_and_respects_fences(installed, tmp_path):
    target = tmp_path / "llms-full.txt"
    target.write_text("""# First page
Source: https://example.com/one

```md
# Not a page
Source: https://example.com/not-a-page
```

# Second page
Source: https://example.com/two
""")
    result = invoke(installed, tmp_path, "detect", target)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["kind"] == "full"
    code = """import json, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from llms_acquire import split_llms_full
print(json.dumps([p['url'] for p in split_llms_full(Path(sys.argv[2]).read_text())]))
"""
    parsed = subprocess.run(
        [sys.executable, "-S", "-c", code, str(installed / "scripts"), str(target)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert parsed.returncode == 0, parsed.stderr
    assert json.loads(parsed.stdout) == ["https://example.com/one", "https://example.com/two"]


def test_hygiene_fix_changes_only_the_requested_file(installed, tmp_path):
    target = tmp_path / "llms.txt"
    target.write_bytes(b"\xef\xbb\xbf# Example\r\n\r\n")
    neighbor = tmp_path / "neighbor.txt"
    neighbor.write_text("preserve\n")
    result = invoke(installed, tmp_path, "hygiene", target, "--fix")
    assert result.returncode == 0, result.stderr
    assert not target.read_bytes().startswith(b"\xef\xbb\xbf")
    assert b"\r" not in target.read_bytes()
    assert neighbor.read_text() == "preserve\n"


def catalogue_fixture(tmp_path, name="llms-small.txt", *, excluded=False, local=False):
    """Build a private canonical sidecar without importing any hub package."""
    import hashlib

    def sha(text):
        return hashlib.sha256(text.encode()).hexdigest()
    statement = "Preserve the complete qualification and its limitations. " * 12
    authored = tmp_path / "authored.json"
    authored.write_text('{}\n')
    row = {"id": "canonical-one", "type": "statement", "text": statement,
           "source_url": authored.as_uri() if local else "https://example.com/source",
           "anchor": "", "also": [],
           "statement_sha256": sha(statement), "provenance": {"claim": {
               "id": "canonical-one", "text": statement}, "validation": {"status": "opaque"}}}
    if excluded:
        row["facts_eligible"] = False
    record = {key: row[key] for key in ("id", "text", "statement_sha256", "provenance")}
    record["record_sha256"] = sha(json.dumps(
        record, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ))
    (tmp_path / "units.jsonl").write_text(json.dumps(row) + "\n")
    (tmp_path / "provenance.json").write_text(json.dumps({"schema": 1, "records": [record]}))
    (tmp_path / "manifest.json").write_text('{"kind":"concept"}')
    tail = " · keywords: qualification" + (" · facts-eligible: false" if excluded else "")
    tail += (" · provenance: provenance.json · claim-id: canonical-one · statement-sha256: "
             + row["statement_sha256"] + " · record-sha256: " + record["record_sha256"])
    line = "- [statement] " + statement.strip() + " — " + row["source_url"] + tail + "\n"
    banner = "<!-- generated by llms-concept-abstractor v1.6.4 · generated 2026-11-09 -->\n"
    target = tmp_path / name
    text = (
        "# Example\n\n> Complete source-scoped qualifications.\n\n"
        + banner + "\n## Guidance\n" + line
    )
    if name == "llms.txt":
        section = "Non-factual guidance" if excluded else "Facts"
        text = ("# Example\n\n> Source: example.com · Generated: 2026-11-09 "
                "by llms-concept-abstractor v1.6.4 · Mode: single-file\n\n"
                + ("## Facts\n- Legacy. [src: https://example.com]\n\n" if excluded else "")
                + "## " + section + "\n" + line + "\n## Sitemap\n- https://example.com — Source\n\n"
                + "## Resources\n### Other\n- (none) — no related resources were verified\n")
    target.write_text(text)
    return target


@pytest.mark.parametrize("name", ["llms-full.txt", "llms-small.txt", "llms-facts.txt", "llms.txt"])
def test_portable_lca_catalogue_qualifications_without_site_packages(installed, tmp_path, name):
    target = catalogue_fixture(tmp_path, name)
    if name == "llms-full.txt":
        (tmp_path / "llms-small.txt").write_text(target.read_text())
    result = invoke(installed, tmp_path, "check", target, "--json")
    data = json.loads(result.stdout)[0]
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert not [f for f in data["findings"] if f["severity"] in ("high", "medium")], data
    assert any(f["severity"] == "na" and "no mirror" in f["msg"] for f in data["findings"])


@pytest.mark.parametrize("fault", [
    None, "units", "provenance", "hash", "text", "flag", "placement", "missing-local", "fake-flag",
])
def test_portable_lca_bindings_and_boolean_placement_fail_closed(installed, tmp_path, fault):
    target = catalogue_fixture(tmp_path, excluded=True, local=True)
    if fault in ("units", "provenance"):
        (tmp_path / ("units.jsonl" if fault == "units" else "provenance.json")).unlink()
    elif fault == "hash":
        target.write_text(target.read_text().replace("record-sha256: ", "record-sha256: fake"))
    elif fault == "text":
        target.write_text(target.read_text().replace(
            "Preserve the complete", "Alter the complete", 1
        ))
    elif fault == "flag":
        unit = json.loads((tmp_path / "units.jsonl").read_text())
        unit["facts_eligible"] = "false"
        (tmp_path / "units.jsonl").write_text(json.dumps(unit))
    elif fault == "placement":
        target.write_text(target.read_text().replace("## Guidance", "## Facts"))
    elif fault == "missing-local":
        (tmp_path / "authored.json").unlink()
    elif fault == "fake-flag":
        target.write_text(target.read_text().replace(
            "facts-eligible: false", "facts-eligible: false-ish"
        ))
    result = invoke(installed, tmp_path, "check", target, "--json")
    assert result.returncode == (0 if fault is None else 1), (fault, result.stdout, result.stderr)
    if fault is not None:
        assert any(f["severity"] == "high" for f in json.loads(result.stdout)[0]["findings"])


def test_portable_ldo_editorial_catalogue_needs_lca_full_sibling(installed, tmp_path):
    target = catalogue_fixture(tmp_path)
    (tmp_path / "llms-full.txt").write_text(target.read_text())
    target.write_text(target.read_text().replace("generated by llms-concept-abstractor v1.6.4",
        "generated by LDO editorial selection · complete canonical full-view lines"))
    result = invoke(installed, tmp_path, "check", target, "--json")
    assert result.returncode == 0, result.stdout
    assert not [f for f in json.loads(result.stdout)[0]["findings"]
                if f["severity"] in ("high", "medium")]
    (tmp_path / "llms-full.txt").unlink()
    result = invoke(installed, tmp_path, "check", target, "--json")
    assert result.returncode == 1, result.stdout
