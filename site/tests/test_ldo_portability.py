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
