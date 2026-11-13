"""Exact public SK kit inventory, shared by its builder and offline installer."""

from pathlib import PurePosixPath

FORMAT = "sk-mongodb-research-kit/v1"
VERSION = "1.0.0"
ARCHIVE_ROOT = "SK-MongoDB-Research-Kit"
MARKETPLACE = "sk-research"
MODES = ("dr", "cfe", "rabbithole", "full-suite")
REFERENCES = ("mongo-protocol", "evidence", *MODES)
PLUGIN = PurePosixPath("plugins/sk")
ROUTER = PurePosixPath(".agents/skills/sk")
DISTRIBUTION = PurePosixPath("hub/research-library/distribution/sk")
ROUTER_FILES = ("SKILL.md", "agents/openai.yaml",
                *(f"references/{name}.md" for name in REFERENCES))


def source_map() -> dict[str, PurePosixPath]:
    """Do not scan directories or let a manifest choose the files to export."""
    files = {name: DISTRIBUTION / name for name in
             ("README.md", "SETUP.md", "install_sk.py", "package_contract.py")}
    files.update({"LICENSE": PurePosixPath("LICENSE"),
                  "library_client.py": PurePosixPath(
                      "hub/research-library/client/library_client.py")})
    for name in (".claude-plugin/marketplace.json", ".agents/plugins/marketplace.json"):
        files[name] = PurePosixPath(name)
    for name in ("README.md", ".claude-plugin/plugin.json", ".codex-plugin/plugin.json"):
        files[str(PLUGIN / name)] = PLUGIN / name
    for client in ("claude", "codex"):
        for mode in MODES:
            files[str(PLUGIN / f"{client}-skills/{mode}/SKILL.md")] = (
                PLUGIN / f"{client}-skills/{mode}/SKILL.md")
        for name in REFERENCES:
            relative = PLUGIN / f"{client}-skills/_shared/references/{name}.md"
            files[str(relative)] = relative
    for name in ROUTER_FILES:
        files[str(ROUTER / name)] = ROUTER / name
    return files


PACKAGE_FILES = frozenset(source_map())
