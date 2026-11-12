"""Read-only installation evidence for routing a complete archived skill corpus.

Cache presence and marketplace availability do not establish an installation.
Explicit direct user aliases are separate installations of a cached source.
"""

from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import tomllib
from pathlib import Path

from .util import read_bounded


def _json(path: Path) -> dict:
    try:
        value = json.loads(read_bounded(path, 2 * 1024 * 1024))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def _path(value: str | Path) -> Path:
    return Path(value).expanduser().absolute()


class InstallationResolver:
    """Snapshot manifest evidence once before a source ingestion run."""

    def __init__(self, home: Path | None = None, codex_home: Path | None = None,
                 native_plugins: list[dict] | None = None):
        default_home = home is None
        self._native_home_override = codex_home is not None
        self.home = _path(home or Path.home())
        self.codex_home = _path(codex_home or (
            os.environ.get("CODEX_HOME", self.home / ".codex") if default_home
            else self.home / ".codex"))
        self.plugin_bases = [self.home / ".claude/plugins", self.codex_home / "plugins"]
        self.packages: list[dict] = []
        settings = _json(self.home / ".claude/settings.json")
        enabled = settings.get("enabledPlugins", {})
        installed = _json(self.home / ".claude/plugins/installed_plugins.json").get("plugins", {})
        if isinstance(enabled, dict) and isinstance(installed, dict):
            for identity, entries in installed.items():
                if not isinstance(entries, list):
                    continue
                for entry in entries:
                    if isinstance(entry, dict) and isinstance(entry.get("installPath"), str):
                        self._package(_path(entry["installPath"]), enabled.get(identity) is True,
                                      "plugin-disabled" if enabled.get(identity) is False
                                      else "plugin-enablement-unverified")
        try:
            config = tomllib.loads(read_bounded(self.codex_home / "config.toml",
                                               2 * 1024 * 1024).decode())
        except (OSError, ValueError):
            config = {}
        plugins = config.get("plugins", {})
        if isinstance(plugins, dict):
            for identity, entry in plugins.items():
                if not isinstance(identity, str) or "@" not in identity or not isinstance(entry, dict):
                    continue
                name, market = identity.rsplit("@", 1)
                if not name or not market or any(x in name + market for x in ("/", "\\", "..")):
                    continue
                parent = self.codex_home / "plugins/cache" / market / name
                try:
                    candidates = [p for p in parent.iterdir() if p.is_dir()][:65]
                except OSError:
                    continue
                pin = entry.get("version")
                selected = [p for p in candidates if p.name == pin] if isinstance(pin, str) else (
                    candidates if len(candidates) == 1 else [])
                for candidate in candidates:
                    manifest = self._manifest(candidate)
                    verified = (candidate in selected and manifest.get("name") == name
                                and entry.get("enabled") is True)
                    self._package(candidate, verified, "plugin-disabled" if entry.get("enabled")
                                  is False else "plugin-version-unverified")
        # The native installed-only inventory also includes auto-enabled remote
        # app plugins that config.toml does not enumerate. Never use --available.
        native = self._native_plugins() if native_plugins is None and default_home else (
            native_plugins or [])
        for entry in native:
            if not isinstance(entry, dict) or entry.get("installed") is not True:
                continue
            identity, version = entry.get("pluginId"), entry.get("version")
            if not isinstance(identity, str) or "@" not in identity or not isinstance(version, str):
                continue
            name, market = identity.rsplit("@", 1)
            if any(not value or "/" in value or "\\" in value or value in {".", ".."}
                   for value in (name, market, version)):
                continue
            parent = self.codex_home / "plugins/cache" / market / name
            # Native version evidence supersedes a unique-but-old cached guess.
            self.packages = [p for p in self.packages if not p["root"].is_relative_to(parent)]
            enabled = entry.get("enabled") is True
            configured = plugins.get(identity, {}) if isinstance(plugins, dict) else {}
            if isinstance(configured, dict) and configured.get("enabled") is False:
                enabled = False
            self._package(parent / version, enabled, "plugin-disabled")
            source = entry.get("source", {})
            if (isinstance(source, dict) and source.get("source") == "local"
                    and isinstance(source.get("path"), str)):
                self._package(_path(source["path"]), enabled, "plugin-disabled")

    def _native_plugins(self) -> list[dict]:
        # Venv runners can reorder PATH ahead of the user's active CLI and find
        # an older Homebrew Codex that omits installed remote app plugins.
        preferred = self.home / ".local/bin/codex"
        executable = (str(preferred) if preferred.is_file() and os.access(preferred, os.X_OK)
                      else shutil.which("codex"))
        if not executable:
            return []
        try:
            process = subprocess.Popen([executable, "plugin", "list", "--json"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=os.name == "posix",
                env={**os.environ, **({"CODEX_HOME": str(self.codex_home)}
                                      if self._native_home_override else {})})
            try:
                output, _ = process.communicate(timeout=15)
            except subprocess.TimeoutExpired:
                if os.name == "posix":
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                else:
                    process.kill()
                process.communicate()
                return []
            if process.returncode or len(output) > 8 * 1024 * 1024:
                return []
            value = json.loads(output)
            if not isinstance(value, dict):
                return []
            entries = value.get("installed", [])
            return entries if isinstance(entries, list) and len(entries) <= 10000 else []
        except (OSError, ValueError, subprocess.SubprocessError):
            return []

    @staticmethod
    def _manifest(root: Path) -> dict:
        for relative in (".codex-plugin/plugin.json", ".claude-plugin/plugin.json", "plugin.json"):
            value = _json(root / relative)
            if value:
                return value
        return {}

    def _package(self, root: Path, enabled: bool, inactive_reason: str):
        self.packages.append({"root": root, "resolved": root.resolve(), "enabled": enabled,
                              "inactive_reason": inactive_reason, "manifest": self._manifest(root)})

    def _native_entry(self, path: Path, package: dict) -> bool:
        """Native skill discovery reads direct entrypoints, not legacy nested trees."""
        root = package["root"]
        declared = package["manifest"].get("skills", "./skills")
        declarations = [declared] if isinstance(declared, str) else declared
        if not isinstance(declarations, list):
            return False
        for value in declarations[:64]:
            if not isinstance(value, str):
                continue
            relative = Path(value)
            if relative.is_absolute() or ".." in relative.parts:
                continue
            base = root / relative
            try:
                suffix = path.relative_to(base)
            except ValueError:
                continue
            if (len(suffix.parts) in (1, 2) and suffix.name == "SKILL.md"
                    and (len(suffix.parts) == 1 or not (base / "SKILL.md").is_file())):
                return True
        return False

    def _is_plugin(self, path: Path) -> bool:
        return any(path.is_relative_to(base) for base in self.plugin_bases) or any(
            path.is_relative_to(package["root"]) or path.is_relative_to(package["resolved"])
            for package in self.packages)

    def classify(self, source_path: str, installations: list[dict]) -> dict:
        """Annotate installations; never change their source paths or activation choices."""
        source = _path(source_path)
        plugin_source = self._is_plugin(source)
        annotated = []
        for original in installations:
            item = dict(original)
            path = _path(item.get("path", source_path))
            root = _path(item.get("root", path.parent.parent))
            eligible, state = False, "plugin-installation-unverified"
            if item.get("codex_activation") == "explicitly-disabled":
                state = "skill-explicitly-disabled"
            elif not self._is_plugin(path):
                direct = path.name == "SKILL.md" and path.parent.parent == root
                if not plugin_source or direct:
                    eligible, state = True, "active-user-overlay" if plugin_source else "user-source"
                else:
                    state = "indirect-plugin-alias"
            else:
                candidates = [package for package in self.packages
                              if path.is_relative_to(package["root"])]
                for package in sorted(candidates, key=lambda p: -len(p["root"].parts)):
                    state = package["inactive_reason"]
                    if package["enabled"]:
                        if self._native_entry(path, package):
                            eligible, state = True, "enabled-current-plugin"
                            break
                        state = "nested-plugin-archive"
            item.update(routing_eligible=eligible, routing_state=state)
            annotated.append(item)
        searchable = any(item["routing_eligible"] for item in annotated)
        states = sorted({item["routing_state"] for item in annotated})
        return {"searchable": searchable,
                "state": "eligible" if searchable else "retained-nonrouting",
                "installations": annotated, "reasons": states}
