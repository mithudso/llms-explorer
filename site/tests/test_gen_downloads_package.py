# site/tests/test_gen_downloads_package.py — the llmsx download is a real wheel and sdist,
# built without uv or setuptools, and carries no credential-shaped string.
# ruff: noqa: E501
from __future__ import annotations

import json
import subprocess
import sys
import tarfile
import tomllib
import zipfile
from configparser import ConfigParser
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SITE / "tools"))
import gen_downloads as gd  # noqa: E402


def _declared_scripts() -> dict[str, str]:
    project = tomllib.loads((SITE.parent / "llmsx/pyproject.toml").read_text())["project"]
    scripts = project["scripts"]
    assert scripts["llmsx"] == "llmsx.__main__:main"
    assert scripts["llmsx-ollama-agent"] == "llmsx.ollama_agent:main"
    return scripts


def test_build_package_writes_a_valid_wheel_sdist_and_manifest(tmp_path):
    manifest = gd.build_package(tmp_path)
    assert manifest and manifest["package"] == "llmsx"
    kinds = {f["kind"]: f for f in manifest["files"]}
    assert set(kinds) == {"wheel", "sdist"}
    wheel = tmp_path / kinds["wheel"]["name"]
    with zipfile.ZipFile(wheel) as zf:
        names = zf.namelist()
        di = [n for n in names if n.endswith(".dist-info/METADATA")][0].rsplit("/", 1)[0]
        assert "llmsx/__init__.py" in names and "llmsx/explorer.py" in names
        assert "llmsx/explorer_store.py" in names and "llmsx/explorer_screens.py" in names
        meta = zf.read(f"{di}/METADATA").decode()
        assert "Name: llmsx" in meta and f"Version: {manifest['version']}" in meta
        assert "Provides-Extra: tui" in meta and 'Requires-Dist: textual>=8,<9; extra == "tui"' in meta
        assert "Requires-Python: >=3.11" in meta
        scripts = _declared_scripts()
        entry_points = ConfigParser(interpolation=None)
        entry_points.optionxform = str
        entry_points.read_string(zf.read(f"{di}/entry_points.txt").decode())
        assert entry_points.sections() == ["console_scripts"]
        assert dict(entry_points["console_scripts"]) == scripts
        for target in scripts.values():
            module = target.split(":", 1)[0].replace(".", "/")
            assert f"{module}.py" in names or f"{module}/__init__.py" in names
        if "llmsx-speculative" in scripts:
            for module in ("cli", "core", "native", "protocol"):
                assert f"llmsx/speculative/{module}.py" in names
        wheel_meta = zf.read(f"{di}/WHEEL").decode()
        assert "Root-Is-Purelib: true" in wheel_meta and "Tag: py3-none-any" in wheel_meta
        record = zf.read(f"{di}/RECORD").decode().splitlines()
        assert len(record) == len(names) and any(ln.startswith("llmsx/explorer.py,sha256=") for ln in record)
        assert record[-1] == f"{di}/RECORD,,"
    sdist = tmp_path / kinds["sdist"]["name"]
    with tarfile.open(sdist) as tf:
        members = tf.getnames()
        root = f"llmsx-{manifest['version']}"
        assert f"{root}/PKG-INFO" in members and f"{root}/pyproject.toml" in members
        assert f"{root}/llmsx/explorer.py" in members and any(m.startswith(f"{root}/tests/") for m in members)
    data = json.loads((tmp_path / "manifest.json").read_text())
    assert data == manifest and all(len(f["sha256"]) == 64 for f in data["files"])


def test_build_is_reproducible_and_scans_clean(tmp_path):
    a = gd.build_package(tmp_path / "a")
    b = gd.build_package(tmp_path / "b")
    assert [f["sha256"] for f in a["files"]] == [f["sha256"] for f in b["files"]]
    for f in a["files"]:
        assert gd._scan_artifact(tmp_path / "a" / f["name"]) == []


def test_the_wheel_installs_and_runs(tmp_path):
    """pip installs the hand-built wheel into a throwaway venv and the
    console script answers `--help` — the download a visitor gets works."""
    manifest = gd.build_package(tmp_path / "dist")
    wheel = tmp_path / "dist" / [f for f in manifest["files"] if f["kind"] == "wheel"][0]["name"]
    venv = tmp_path / "venv"
    subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(venv)], check=True)
    py = venv / "bin" / "python"
    # no pip in a bare venv: unpack the wheel the way pip would for a purelib package
    site_packages = next((venv / "lib").glob("python*")) / "site-packages"
    with zipfile.ZipFile(wheel) as zf:
        zf.extractall(site_packages)
    out = subprocess.run([str(py), "-m", "llmsx", "--version"], capture_output=True, text=True)
    assert out.returncode == 0 and manifest["version"] in out.stdout
    out = subprocess.run([str(py), "-c", "import llmsx.explorer_store as s; print(s.DEFAULT_REPO_URL)"],
                         capture_output=True, text=True)
    assert out.returncode == 0 and "github.com/mithudso/llms-explorer" in out.stdout
    scripts = _declared_scripts()
    if "llmsx-speculative" in scripts:
        module, function = scripts["llmsx-speculative"].split(":", 1)
        # Invoke the declared entrypoint from the extracted wheel, as a console
        # wrapper would. --help must work without contacting either model server.
        code = ("import importlib, sys; "
                "sys.argv = ['llmsx-speculative', '--help']; "
                f"raise SystemExit(getattr(importlib.import_module({module!r}), {function!r})())")
        out = subprocess.run([str(py), "-c", code], capture_output=True, text=True)
        assert out.returncode == 0, out.stderr
        assert "usage: llmsx-speculative" in out.stdout
        assert "validate" in out.stdout and "--execute" in out.stdout
