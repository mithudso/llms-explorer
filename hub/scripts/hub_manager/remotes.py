"""remotes.py — remote Ollama host monitoring + model-load management.

Answers "why is that box screaming": /api/ps shows exactly which models are
resident in a host's VRAM and when their keep-alive expires. unload() posts
keep_alive:0 so the model is evicted after any in-flight request — the
remote-task kill switch for runaway inference loads. (Process-level remote
control would need SSH; this module is HTTP-API only.)
"""

from __future__ import annotations

import json
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field

from . import core

TIMEOUT = 5
REPO_PATH = "~/.global-ai-hub"
DAEMON_PATTERNS = ("hub-daemon.py", "idle-indexer.py", "pipeline_manager.py")


@dataclass
class LoadedModel:
    name: str
    vram_gb: float
    context: int
    expires_at: str


@dataclass
class HostStatus:
    url: str
    weight: int
    alive: bool = False
    latency_ms: float = 0.0
    error: str = ""
    models_available: int = 0
    loaded: list[LoadedModel] = field(default_factory=list)
    has_embed_model: bool = False
    # ssh-derived readiness (populated by enrich_readiness()); None/[]/""
    # mean "not checked", not "checked and empty" — ssh may not be configured
    ssh_ok: bool | None = None
    daemons_up: list[str] = field(default_factory=list)
    last_activity: str = ""
    # hub.db indexed-file/embedding counts on that box (None = not checked)
    indexed_files: int | None = None
    indexed_embeddings: int | None = None

    @property
    def vram_gb(self) -> float:
        return sum(m.vram_gb for m in self.loaded)

    @property
    def ready(self) -> bool:
        """Alive + has the configured embed model — this host can actually
        serve an embed request right now."""
        return self.alive and self.has_embed_model


def _get(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode())


def host_status(url: str, weight: int) -> HostStatus:
    status = HostStatus(url=url, weight=weight)
    started = time.monotonic()
    try:
        tags = _get(f"{url}/api/tags")
        status.latency_ms = (time.monotonic() - started) * 1000
        status.alive = True
        names = [m.get("name", "") for m in tags.get("models", [])]
        status.models_available = len(names)
        status.has_embed_model = any(n.startswith(core.embed_model())
                                     for n in names)
    except (OSError, ValueError) as exc:
        status.error = str(exc)
        return status
    try:
        ps = _get(f"{url}/api/ps")
        for m in ps.get("models", []):
            status.loaded.append(LoadedModel(
                name=m.get("name", "?"),
                vram_gb=(m.get("size_vram") or m.get("size") or 0) / 1024 ** 3,
                context=m.get("context_length", 0),
                expires_at=(m.get("expires_at") or "")[:19].replace("T", " "),
            ))
    except (OSError, ValueError) as exc:
        status.error = f"/api/ps failed: {exc}"
    return status


def all_hosts() -> list[HostStatus]:
    return [host_status(url, weight) for url, weight in core.ollama_hosts()]


def unload(url: str, model: str) -> str:
    """Evict one model from a host's VRAM (keep_alive: 0). The model reloads
    on its next request — this stops the fans, not the requester."""
    payload = json.dumps({"model": model, "keep_alive": 0}).encode()
    req = urllib.request.Request(
        f"{url}/api/generate", data=payload,
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30):
            pass
        return f"unload requested: {model} on {url}"
    except urllib.error.HTTPError as exc:
        # embedding-only models reject /api/generate; /api/embed unloads them
        if exc.code == 400:
            payload = json.dumps({"model": model, "input": "",
                                  "keep_alive": 0}).encode()
            req = urllib.request.Request(
                f"{url}/api/embed", data=payload,
                headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=30):
                    pass
                return f"unload requested (embed): {model} on {url}"
            except OSError as exc2:
                return f"unload failed: {exc2}"
        return f"unload failed: HTTP {exc.code}"
    except OSError as exc:
        return f"unload failed: {exc}"


def unload_all(url: str) -> list[str]:
    status = host_status(url, 0)
    if not status.loaded:
        return [f"nothing loaded on {url}"]
    return [unload(url, m.name) for m in status.loaded]


# --------------------------------------------------------------------------- #
# ssh process control (opt-in per host via settings "ssh_targets")
# --------------------------------------------------------------------------- #

SSH_OPTS = ["-o", "BatchMode=yes", "-o", "ConnectTimeout=5"]


def ssh_target(url: str) -> str | None:
    """user@host for a pool URL, from settings ssh_targets
    ("hostip=user@hostip, ..."); None = ssh not configured for this host."""
    from . import settings as settings_mod
    from urllib.parse import urlparse
    host = urlparse(url).hostname or ""
    mapping = {}
    for pair in str(settings_mod.load().get("ssh_targets", "")).split(","):
        if "=" in pair:
            key, value = pair.split("=", 1)
            mapping[key.strip()] = value.strip()
    if host in mapping:
        return mapping[host] or None
    if host in ("localhost", "127.0.0.1", ""):
        return None  # local box: no ssh needed
    return None


def run_ssh(target: str, command: str, timeout: int = 20) -> tuple[bool, str]:
    """Bounded, key-only (BatchMode) ssh command; never prompts."""
    import subprocess
    try:
        out = subprocess.run(["ssh", *SSH_OPTS, target, command],
                             capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return False, f"ssh timed out after {timeout}s"
    except OSError as exc:
        return False, str(exc)
    text = (out.stdout + ("\n" + out.stderr if out.stderr.strip() else "")).strip()
    return out.returncode == 0, text


def rsync_supports_protect_args(target: str) -> bool:
    """Whether the REMOTE rsync understands -s/--protect-args.

    Apple ships `openrsync` (protocol 29) on recent macOS, which does not —
    passing -s to it aborts the transfer with a usage dump. Probe instead of
    assuming, so a mixed fleet keeps working.

    rsync 3.2.4 renamed the long option to --secluded-args (-s still works and
    --protect-args is still accepted, but only the new name appears in --help),
    so match either spelling or a modern release is misread as unsupported.
    """
    ok, out = run_ssh(
        target,
        "rsync --help 2>&1 | grep -c -e --protect-args -e --secluded-args",
        timeout=20)
    try:
        return ok and int(out.strip().splitlines()[-1]) > 0
    except (ValueError, IndexError):
        return False


_LOCAL_PROTECT_ARGS: list[bool] = []


def local_rsync_supports_protect_args() -> bool:
    """Whether the rsync on THIS box understands -s/--protect-args.

    Both ends must support it. Which local rsync gets used depends on PATH:
    an interactive shell finds homebrew's rsync 3.x, but a launchd agent's
    minimal PATH finds Apple's /usr/bin/rsync (openrsync), which does not have
    the flag and answers with a usage dump instead of transferring anything.
    Probing the remote alone is not enough.
    """
    if not _LOCAL_PROTECT_ARGS:
        import subprocess
        try:
            out = subprocess.run(["rsync", "--help"], capture_output=True,
                                 text=True, timeout=20)
            text = out.stdout + out.stderr
        except (OSError, subprocess.TimeoutExpired):
            text = ""
        _LOCAL_PROTECT_ARGS.append(
            "--protect-args" in text or "--secluded-args" in text)
    return _LOCAL_PROTECT_ARGS[0]


def run_rsync(args: list[str], timeout: int = 1800,
              protect_args: bool = True) -> tuple[bool, str]:
    """Bounded rsync over the same key-only ssh the dispatcher uses.

    -s (--protect-args) sends each path to the remote as a single literal
    argument instead of letting the remote shell re-split it, so a path with
    spaces survives. It also means the remote shell does NOT expand `~`, which
    is why every remote path this codebase builds is absolute (see Box.home in
    pipeline_manager). Callers pass protect_args=False for a remote whose
    rsync lacks the flag; those paths must then be shell-safe on their own.
    """
    import subprocess
    use_s = protect_args and local_rsync_supports_protect_args()
    cmd = ["rsync", "-a", "--partial",
           *(["-s"] if use_s else []),
           "-e", "ssh " + " ".join(SSH_OPTS), *args]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return False, f"rsync timed out after {timeout}s"
    except OSError as exc:
        return False, str(exc)
    text = (out.stdout + ("\n" + out.stderr if out.stderr.strip() else "")).strip()
    return out.returncode == 0, text


DIAG_CMD = (
    "echo '=== uptime / load ==='; uptime; "
    "echo; echo '=== top CPU processes ==='; "
    "(ps aux -r 2>/dev/null || ps aux --sort=-%cpu) | head -12; "
    "echo; echo '=== connections into ollama (:11434) ==='; "
    "lsof -nP -i :11434 2>/dev/null | head -12 || ss -tnp sport = :11434 2>/dev/null | head -12; "
    "echo; echo '=== ollama / llama-server processes ==='; "
    "pgrep -fl 'ollama|llama-server' | head -8"
)


def ssh_diagnose(url: str) -> str:
    """Full remote diagnostics: load, top CPU, who is querying ollama."""
    target = ssh_target(url)
    if not target:
        return (f"no ssh target configured for {url} — set Settings > "
                "ssh_targets (e.g. 192.168.4.1=mitch@192.168.4.1)")
    ok, out = run_ssh(target, DIAG_CMD, timeout=25)
    header = f"=== ssh {target} ===\n"
    return header + (out if out else ("ok" if ok else "diagnostics failed"))


def ssh_kill(url: str, pid: int, force: bool = False) -> str:
    """SIGTERM (or SIGKILL with force) one PID on the remote host."""
    target = ssh_target(url)
    if not target:
        return f"no ssh target configured for {url}"
    sig = "-KILL" if force else "-TERM"
    ok, out = run_ssh(target, f"kill {sig} {int(pid)} && echo killed {pid}")
    return out if out else ("kill sent" if ok else "kill failed")


# --------------------------------------------------------------------------- #
# box readiness (ssh-derived: which local daemons also run there, last work)
# --------------------------------------------------------------------------- #

READINESS_CMD = (
    "for p in hub-daemon.py idle-indexer.py pipeline_manager.py; do "
    "pgrep -f \"$p\" >/dev/null 2>&1 && echo \"UP:$p\"; done; "
    "for f in ~/.ollama/logs/server.log "
    "~/Library/Logs/Homebrew/ollama/ollama.log "
    "/opt/homebrew/var/log/ollama.log /usr/local/var/log/ollama.log "
    "/var/log/ollama.log; do "
    "[ -f \"$f\" ] && { stat -f '%m' \"$f\" 2>/dev/null || stat -c '%Y' \"$f\" 2>/dev/null; }; "
    "done | sort -rn | head -1; "
    "sqlite3 ~/.global-ai-hub/hub.db "
    "'SELECT \"FILES:\" || COUNT(*) FROM files' 2>/dev/null; "
    "sqlite3 ~/.global-ai-hub/hub.db "
    "'SELECT \"EMBEDS:\" || COUNT(*) FROM embeddings' 2>/dev/null"
)


def _is_local_url(url: str) -> bool:
    import socket
    from urllib.parse import urlparse
    host = urlparse(url).hostname or ""
    return host in ("localhost", "127.0.0.1", socket.gethostname())


def _local_index_counts(status: HostStatus) -> None:
    """hub.db counts for the local box — no ssh needed, straight sqlite3."""
    import sqlite3
    if not core.HUB_DB.exists():
        return
    try:
        with sqlite3.connect(f"file:{core.HUB_DB}?mode=ro", uri=True, timeout=2) as db:
            status.indexed_files = db.execute("SELECT COUNT(*) FROM files").fetchone()[0]
            status.indexed_embeddings = db.execute(
                "SELECT COUNT(*) FROM embeddings").fetchone()[0]
    except sqlite3.Error:
        pass


def enrich_readiness(status: HostStatus) -> HostStatus:
    """Layer ssh-derived readiness onto an HTTP-checked HostStatus: which of
    the standard hub daemons are also running there, and a best-effort
    last-activity timestamp (a resident model implies "active now"; failing
    that, the remote ollama server log's mtime). No-op (ssh_ok stays None)
    when the host has no ssh_targets entry — HTTP-only hosts just skip this."""
    if status.loaded:
        status.last_activity = "now (model loaded)"
    target = ssh_target(status.url)
    if not target:
        if _is_local_url(status.url):
            _local_index_counts(status)
        return status
    ok, out = run_ssh(target, READINESS_CMD, timeout=10)
    status.ssh_ok = ok
    if not ok:
        return status
    lines = out.splitlines()
    status.daemons_up = [ln.split(":", 1)[1] for ln in lines if ln.startswith("UP:")]
    if not status.last_activity:
        digits = next((ln for ln in lines if ln.strip().isdigit()), "")
        if digits:
            status.last_activity = core.age_str(float(digits))
    for ln in lines:
        if ln.startswith("FILES:") and ln[6:].strip().isdigit():
            status.indexed_files = int(ln[6:].strip())
        elif ln.startswith("EMBEDS:") and ln[7:].strip().isdigit():
            status.indexed_embeddings = int(ln[7:].strip())
    return status


def all_hosts_readiness() -> list[HostStatus]:
    """all_hosts() plus ssh-derived readiness — on-demand only (each ssh
    round-trip is ~seconds; never put this on the fast auto-refresh timer)."""
    return [enrich_readiness(h) for h in all_hosts()]


# --------------------------------------------------------------------------- #
# git repo status across boxes (Repos tab)
# --------------------------------------------------------------------------- #

@dataclass
class RepoStatus:
    label: str
    reachable: bool = False
    branch: str = ""
    ahead: int = 0
    behind: int = 0
    dirty: int = 0
    commit: str = ""
    error: str = ""

    @property
    def summary(self) -> str:
        if not self.reachable:
            return f"unreachable: {self.error}"
        bits = [f"@{self.commit}" if self.commit else ""]
        if self.ahead:
            bits.append(f"{self.ahead} ahead")
        if self.behind:
            bits.append(f"{self.behind} behind")
        if self.dirty:
            bits.append(f"{self.dirty} dirty")
        if not (self.ahead or self.behind or self.dirty):
            bits.append("up to date")
        return " ".join(b for b in bits if b)


_REPO_STATUS_CMD = (
    "cd {path} 2>&1 && git fetch --quiet 2>&1 && "
    "b=$(git rev-parse --abbrev-ref HEAD) && "
    "ab=$(git rev-list --left-right --count \"$b...origin/$b\" 2>/dev/null || echo '0\t0') && "
    "d=$(git status --porcelain | wc -l | tr -d ' ') && "
    "c=$(git rev-parse --short HEAD) && "
    "printf 'REPO_STATUS|%s|%s|%s|%s\\n' \"$b\" \"$ab\" \"$d\" \"$c\""
)


def _parse_repo_status(label: str, out: str) -> RepoStatus:
    rs = RepoStatus(label=label)
    line = next((ln for ln in out.splitlines() if ln.startswith("REPO_STATUS|")), "")
    if not line:
        rs.error = out.strip()[-300:] or "no REPO_STATUS line in output"
        return rs
    _, branch, ab, dirty, commit = (line.split("|", 4) + ["", "", "", ""])[:5]
    ahead, _, behind = ab.partition("\t")
    try:
        rs.ahead, rs.behind = int(ahead or 0), int(behind or 0)
        rs.dirty = int(dirty or 0)
    except ValueError:
        rs.error = f"unparseable counts: {ab!r}/{dirty!r}"
        return rs
    rs.branch, rs.commit, rs.reachable = branch, commit, True
    return rs


def local_repo_status(path: str | None = None) -> RepoStatus:
    path = path or str(core.HUB_DIR)
    try:
        out = subprocess.run(["bash", "-c", _REPO_STATUS_CMD.format(path=path)],
                             capture_output=True, text=True, timeout=25).stdout
    except (OSError, subprocess.TimeoutExpired) as exc:
        return RepoStatus(label="local (this box)", error=str(exc))
    return _parse_repo_status("local (this box)", out)


def remote_repo_status(label: str, target: str, path: str = REPO_PATH) -> RepoStatus:
    ok, out = run_ssh(target, _REPO_STATUS_CMD.format(path=path), timeout=30)
    if not ok:
        return RepoStatus(label=label, error=out or "ssh failed")
    return _parse_repo_status(label, out)


_CLEAN_REPO_CMD = (
    "cd {path} 2>&1 && git fetch --quiet 2>&1 && "
    "b=$(git rev-parse --abbrev-ref HEAD) && "
    "git reset --hard \"origin/$b\" 2>&1 && git clean -fd 2>&1 && "
    "c=$(git rev-parse --short HEAD) && "
    "printf 'CLEAN_DONE|%s|%s\\n' \"$b\" \"$c\""
)


def _parse_clean_result(out: str) -> str:
    line = next((ln for ln in out.splitlines() if ln.startswith("CLEAN_DONE|")), "")
    if not line:
        return f"clean failed: {out.strip()[-300:] or 'no output'}"
    _, branch, commit = (line.split("|", 2) + ["", ""])[:3]
    return f"clean OK — hard-reset + clean, now {branch}@{commit}"


def local_clean_repo(path: str | None = None) -> str:
    """Discard uncommitted changes and hard-reset the local checkout to
    origin/<current-branch>. Destructive — callers must confirm with the
    user first (this just does the work once asked)."""
    path = path or str(core.HUB_DIR)
    try:
        out = subprocess.run(["bash", "-c", _CLEAN_REPO_CMD.format(path=path)],
                             capture_output=True, text=True, timeout=30).stdout
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"clean failed: {exc}"
    return _parse_clean_result(out)


def remote_clean_repo(target: str, path: str = REPO_PATH) -> str:
    """Same as local_clean_repo() but over ssh on a remote box."""
    ok, out = run_ssh(target, _CLEAN_REPO_CMD.format(path=path), timeout=35)
    if not ok:
        return f"clean failed (ssh): {out or 'ssh failed'}"
    return _parse_clean_result(out)


def clean_repo(label: str) -> str:
    """Clean-and-fast-forward a repo previously reported by all_repo_status(),
    dispatching to local or ssh based on its label (matches all_repo_status'
    label scheme: "local (this box)" or an ssh_targets host key)."""
    if label == "local (this box)":
        return local_clean_repo()
    from . import settings as settings_mod
    mapping = {}
    for pair in str(settings_mod.load().get("ssh_targets", "")).split(","):
        if "=" in pair:
            host, target = pair.split("=", 1)
            mapping[host.strip()] = target.strip()
    target = mapping.get(label)
    if not target:
        return f"no ssh target configured for {label!r}"
    return remote_clean_repo(target)


def all_repo_status() -> list[RepoStatus]:
    """local box + every configured ssh_targets host, deduped so a host that
    IS this machine (127.0.0.1/localhost) doesn't get checked twice."""
    from . import settings as settings_mod
    import socket
    results = [local_repo_status()]
    local_names = {"localhost", "127.0.0.1", socket.gethostname()}
    for pair in str(settings_mod.load().get("ssh_targets", "")).split(","):
        if "=" not in pair:
            continue
        host, target = (p.strip() for p in pair.split("=", 1))
        if not target or host in local_names:
            continue
        results.append(remote_repo_status(host, target))
    return results
