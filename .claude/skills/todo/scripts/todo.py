#!/usr/bin/env python3
"""Personal to-do list: one markdown file, fed by manual adds, braindumps, lingering session
tasks, the StickySites browser extension, and peer boxes over SSH.

Usage:
  todo.py add "text" [--source manual|braindump:<path:line>]
  todo.py done <id-or-substring>
  todo.py list [--all]
  todo.py sync [--tiers 2,3] [--since-days N] [--session ID] [--quiet]
  todo.py peer-sync [TARGET ...] [--quiet]   # default targets: lines of .peers next to the list
  todo.py export-json                         # used by peer-sync on the remote side
  todo.py import-json --expect HASH < doc     # used by peer-sync on the remote side
  todo.py native-host                         # Chrome native-messaging bridge for StickySites
  todo.py install-native-host                 # register the bridge with every browser running StickySites
  todo.py install-launchd [--interval SEC]    # periodic sync + peer-sync
  todo.py hook-session-end                    # SessionEnd hook; reads hook JSON on stdin

The list lives at $PERSONAL_TODO (default ~/dev/personal/Areas/todo/TODO.md). Every item carries
a stable id in an HTML comment. .todo-seen.json keeps every id ever seen, so an id that is seen
but no longer present was dismissed and stays dismissed across sources and peers.
.todo-sync-state.json keeps, per replica (extension or peer), the item snapshot from the last
successful sync; that snapshot is the base of a three-way merge, which is how a deletion or an
edit on one side is told apart from an item the other side has not seen yet.
"""
import argparse
import datetime as dt
import fcntl
import glob
import hashlib
import json
import os
import re
import shlex
import struct
import subprocess
import sys
import time

HOME = os.path.expanduser("~")
TODO_FILE = os.environ.get("PERSONAL_TODO", os.path.join(HOME, "dev/personal/Areas/todo/TODO.md"))
TODO_DIR = os.path.dirname(TODO_FILE)
SEEN_FILE = os.path.join(TODO_DIR, ".todo-seen.json")
STATE_FILE = os.path.join(TODO_DIR, ".todo-sync-state.json")
LOCK_FILE = os.path.join(TODO_DIR, ".todo.lock")
PEERS_FILE = os.path.join(TODO_DIR, ".peers")
LOG_FILE = os.path.join(TODO_DIR, ".todo-sync.log")
LLMS_DIR = os.environ.get("MEMORY_CENTRAL_DIR", os.path.join(HOME, ".llms"))
TASKS_DIR = os.path.join(HOME, ".claude/tasks")
PROJECTS_DIR = os.path.join(HOME, ".claude/projects")
SCRIPT = os.path.abspath(__file__)

HOST_NAME = "com.mitch.todo_bridge"
MERGE_FIELDS = ("text", "done")
ITEM_RE = re.compile(r"^- \[( |x|X)\] (.*?)\s*<!-- id:([0-9A-Za-z_-]{1,40}) src:(\S+)(?: proj:(\S+))? -->\s*$")
SESSION_SECTION_PREFIX = "Sessions · "


def today():
    return dt.date.today().isoformat()


def log(msg):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{dt.datetime.now().isoformat(timespec='seconds')} {msg}\n")
    except OSError:
        pass


def make_id(text, scope):
    norm = re.sub(r"\W+", " ", text.lower()).strip()
    return hashlib.sha1(f"{scope}|{norm}".encode()).hexdigest()[:8]


def new_item(text, src="manual", proj=None, meta="", item_id=None, done=False):
    text = " ".join(str(text).split())
    return {"id": item_id or make_id(text, proj or group_of({"src": src, "proj": proj})),
            "text": text, "meta": meta, "done": bool(done), "src": src, "proj": proj}


def group_of(item):
    if item.get("src") == "braindump":
        return "From braindumps"
    if item.get("proj"):
        return "From sessions"
    return "Manual"


# Markdown file <-> flat item list

def parse_todo(path=TODO_FILE):
    items = []
    if not os.path.exists(path):
        return items
    section, proj_heading = None, None
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            h2 = re.match(r"^## (.+?)\s*$", line)
            if h2:
                section, proj_heading = h2.group(1), None
                continue
            h3 = re.match(r"^### (.+?)\s*$", line)
            if h3:
                proj_heading = h3.group(1)
                continue
            m = ITEM_RE.match(line)
            if m:
                text, _, meta = m.group(2).partition(" · ")
                items.append({"id": m.group(3), "text": text.strip(), "meta": meta.strip(),
                              "done": m.group(1) != " ", "src": m.group(4), "proj": m.group(5)})
                continue
            # A checkbox typed by hand in Obsidian has no id yet: adopt it.
            bare = re.match(r"^\s*- \[( |x|X)\] (.+?)\s*$", line)
            if bare:
                proj = proj_heading if section == "From sessions" else None
                src = "braindump" if section == "From braindumps" else ("hand" if proj else "manual")
                items.append(new_item(bare.group(2), src=src, proj=proj, meta=f"added {today()}",
                                      done=bare.group(1) != " "))
    return items


def render_todo(items):
    out = ["---", "type: todo", f"updated: {dt.datetime.now().isoformat(timespec='minutes')}", "---", "",
           "# To-do", "",
           "_Tick a box to finish an item; delete a line to dismiss it for good. Maintained by "
           "`todo.py` (skills: /todo, /braindump); synced with StickySites and peer boxes._", ""]

    def line(i):
        body = f"{i['text']} · {i['meta']}" if i.get("meta") else i["text"]
        proj = f" proj:{i['proj']}" if i.get("proj") else ""
        return f"- [{'x' if i['done'] else ' '}] {body} <!-- id:{i['id']} src:{i['src']}{proj} -->"

    open_items = [i for i in items if not i["done"]]
    for sec in ("Manual", "From braindumps", "From sessions"):
        out.append(f"## {sec}")
        members = [i for i in open_items if group_of(i) == sec]
        if sec == "From sessions":
            for proj in sorted({i["proj"] for i in members}):
                out.append(f"### {proj}")
                out.extend(line(i) for i in members if i["proj"] == proj)
        else:
            out.extend(line(i) for i in members)
        out.append("")
    out.append("## Done")
    out.extend(line(i) for i in items if i["done"])
    out.append("")
    return "\n".join(out)


def strip_stamp(text):
    return re.sub(r"(?m)^updated: .*$", "", text)


def atomic_write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)


def read_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


class Store:
    """Locked read-modify-write of the list, the seen-id set and the per-replica sync bases."""

    def __enter__(self):
        os.makedirs(TODO_DIR, exist_ok=True)
        self._lock = open(LOCK_FILE, "w")
        fcntl.flock(self._lock, fcntl.LOCK_EX)
        self.items = parse_todo()
        self.seen = set(read_json(SEEN_FILE, []))
        self.state = read_json(STATE_FILE, {})
        self.seen |= {i["id"] for i in self.items}
        return self

    def dismissed(self):
        return self.seen - {i["id"] for i in self.items}

    def add(self, item):
        if item["id"] in self.seen or not item["text"]:
            return False
        self.items.append(item)
        self.seen.add(item["id"])
        return True

    def save(self):
        rendered = render_todo(self.items)
        try:
            with open(TODO_FILE, encoding="utf-8") as f:
                current = f.read()
        except OSError:
            current = None
        # Skip the write when only the timestamp would change, so Obsidian and peers see no churn.
        if current is None or strip_stamp(current) != strip_stamp(rendered):
            atomic_write(TODO_FILE, rendered)
        atomic_write(SEEN_FILE, json.dumps(sorted(self.seen)))
        atomic_write(STATE_FILE, json.dumps(self.state, indent=1, sort_keys=True))

    def __exit__(self, exc_type, *exc):
        if exc_type is None:
            self.save()
        fcntl.flock(self._lock, fcntl.LOCK_UN)
        self._lock.close()


def content_hash(items):
    return hashlib.sha1(json.dumps(sorted(items, key=lambda i: i["id"]), sort_keys=True).encode()).hexdigest()[:12]


# Three-way merge

def merge3(local, remote, base, dismissed=frozenset()):
    """Merge two item lists against their last common snapshot.

    New on one side: added (unless the id was dismissed). Missing on one side but in base: deleted,
    unless the other side edited it since base. Edited on both sides: text keeps the local version,
    done wins if either side finished it. Other fields come from local when local has the item.
    """
    L = {i["id"]: i for i in local}
    R = {i["id"]: i for i in remote}
    B = {i["id"]: i for i in base}
    order = [i["id"] for i in local] + [i["id"] for i in remote if i["id"] not in L]
    out = []
    for iid in order:
        l, r, b = L.get(iid), R.get(iid), B.get(iid)
        if b is None:
            if l and r:
                merged = dict(l)
                merged["done"] = l["done"] or r["done"]
                out.append(merged)
            elif l:
                out.append(l)
            elif iid not in dismissed:
                out.append(r)
            continue
        if l is None or r is None:
            survivor = l or r
            if any(survivor[f] != b.get(f) for f in MERGE_FIELDS):
                out.append(survivor)
            continue
        merged = dict(l)
        for f in MERGE_FIELDS:
            if l[f] == b.get(f):
                merged[f] = r[f]
            elif r[f] != b.get(f) and f == "done":
                merged[f] = l[f] or r[f]
        if not merged.get("meta") and r.get("meta"):
            merged["meta"] = r["meta"]
        out.append(merged)
    return out


def snapshot(items):
    return [{k: i.get(k) for k in ("id", "text", "done", "src", "proj", "meta")} for i in items]


# Manual adds, braindumps, lingering session tasks

def add_item(text, source="manual"):
    """Public entry point used by braindump.py. Returns the new id, or None if already known."""
    text = " ".join(text.split())
    if not text:
        raise ValueError("empty task text")
    if source.startswith("braindump:"):
        item = new_item(text, src="braindump", meta=f"added {today()} · `{source.split(':', 1)[1]}`")
    else:
        item = new_item(text, src="manual", meta=f"added {today()}")
    with Store() as st:
        return item["id"] if st.add(item) else None


def memory_central_actions(tiers, since_days):
    """Open/blocked rows from ~/.llms/<project>_actions_llms.md (built nightly by memory-central).

    Tier 1 rows come from instruction files (CLAUDE.md, commands) and are standing rules, not
    lingering work, so the default is tier 2 (agent memory) only; tier 3 is raw logs.
    """
    cutoff = (dt.date.today() - dt.timedelta(days=since_days)).isoformat()
    for path in sorted(glob.glob(os.path.join(LLMS_DIR, "*_actions_llms.md"))):
        proj = os.path.basename(path)[: -len("_actions_llms.md")]
        with open(path, encoding="utf-8") as f:
            for line in f:
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if len(cells) != 5 or cells[0] in ("item", "---"):
                    continue
                item, status, first_seen, tier, source = cells
                if status not in ("open", "blocked") or not tier.isdigit():
                    continue
                if int(tier) not in tiers or first_seen < cutoff:
                    continue
                meta = f"since {first_seen}" + (" · blocked" if status == "blocked" else "") + f" · `{source}`"
                yield proj, item, meta


def session_project(session_id):
    """Project name for a session, from the cwd recorded in its transcript."""
    for path in glob.glob(os.path.join(PROJECTS_DIR, "*", f"{session_id}.jsonl")):
        try:
            with open(path, encoding="utf-8") as f:
                for _, line in zip(range(50), f):
                    cwd = json.loads(line).get("cwd")
                    if cwd:
                        return os.path.basename(cwd.rstrip("/")) or "misc"
        except (OSError, ValueError):
            pass
    return "misc"


def lingering_session_tasks(ended_session=None, idle_minutes=30):
    """Unfinished TaskCreate items from sessions that ended or went idle."""
    now = time.time()
    for d in glob.glob(os.path.join(TASKS_DIR, "*")):
        sid = os.path.basename(d)
        files = glob.glob(os.path.join(d, "*.json"))
        if not files:
            continue
        idle = now - max(os.path.getmtime(p) for p in files) > idle_minutes * 60
        if sid != ended_session and not idle:
            continue
        proj = None
        for p in sorted(files):
            t = read_json(p, {})
            if t.get("status") not in ("pending", "in_progress"):
                continue
            proj = proj or session_project(sid)
            yield proj, t.get("subject", "").strip(), f"session {sid[:8]} · {t.get('status')}"


def sync_sources(tiers=(2,), since_days=60, ended_session=None):
    with Store() as st:
        added = 0
        rows = [("memory-central", r) for r in memory_central_actions(tiers, since_days)]
        rows += [("task", r) for r in lingering_session_tasks(ended_session)]
        for src, (proj, text, meta) in rows:
            if text and st.add(new_item(text, src=src, proj=proj, meta=meta)):
                added += 1
        return added


# Peers over SSH

def ssh(target, cmd, stdin=None, timeout=30):
    remote = f"python3 ~/.claude/skills/todo/scripts/todo.py {cmd}"
    return subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", target, remote],
                          input=stdin, capture_output=True, text=True, timeout=timeout)


def export_doc():
    with Store() as st:
        return {"items": snapshot(st.items), "seen": sorted(st.seen), "hash": content_hash(snapshot(st.items))}


def import_doc(doc, expect):
    with Store() as st:
        if content_hash(snapshot(st.items)) != expect:
            return False
        st.seen |= set(doc.get("seen", []))
        st.items = doc["items"]
        st.seen |= {i["id"] for i in st.items}
        return True


def peer_sync_one(target):
    key = f"peer:{target}"
    for _attempt in range(2):
        res = ssh(target, "export-json")
        if res.returncode != 0:
            raise RuntimeError(f"export failed: {(res.stderr or res.stdout).strip()[:200]}")
        remote = json.loads(res.stdout)
        with Store() as st:
            st.seen |= set(remote["seen"])
            base = st.state.get(key, [])
            merged = merge3(st.items, remote["items"], base, st.dismissed())
            doc = {"items": snapshot(merged), "seen": sorted(st.seen)}
            res = ssh(target, f"import-json --expect {remote['hash']}", stdin=json.dumps(doc))
            if res.returncode == 3:
                continue  # remote changed between export and import; re-read and retry
            if res.returncode != 0:
                raise RuntimeError(f"import failed: {(res.stderr or res.stdout).strip()[:200]}")
            st.items = merged
            st.state[key] = snapshot(merged)
            return len(merged)
    raise RuntimeError("remote kept changing during sync")


def peer_targets(args_targets):
    if args_targets:
        return args_targets
    try:
        with open(PEERS_FILE, encoding="utf-8") as f:
            return [l.strip() for l in f if l.strip() and not l.startswith("#")]
    except OSError:
        return []


# StickySites native-messaging bridge

def ext_to_items(ext_items, section_names):
    """StickySites todo items -> list items. Section names decide the group."""
    out = []
    for e in ext_items:
        sec = section_names.get(e.get("section") or "", "")
        src, proj = "stickysites", None
        if sec == "From braindumps":
            src = "braindump"
        elif sec.startswith(SESSION_SECTION_PREFIX):
            src, proj = "session", sec[len(SESSION_SECTION_PREFIX):]
        text = " ".join(str(e.get("text", "")).split())
        if text:
            out.append({"id": str(e["id"]), "text": text, "meta": str(e.get("note") or ""),
                        "done": bool(e.get("done")), "src": src, "proj": proj})
    return out


def items_to_ext(items):
    out = []
    for i in items:
        g = group_of(i)
        section = f"{SESSION_SECTION_PREFIX}{i['proj']}" if g == "From sessions" else g
        out.append({"id": i["id"], "text": i["text"], "done": i["done"], "note": i.get("meta") or "",
                    "section": "" if section == "Manual" else section})
    return out


def bridge_sync(msg):
    ext_id = str(msg.get("ext") or "unknown")
    key = f"ext:{ext_id}"
    names = {s.get("id"): s.get("name", "") for s in msg.get("sections", []) if isinstance(s, dict)}
    with Store() as st:
        remote = ext_to_items(msg.get("items", []), names)
        merged = merge3(st.items, remote, st.state.get(key, []), st.dismissed())
        st.seen |= {i["id"] for i in merged}
        st.items = merged
        st.state[key] = snapshot(merged)
        return {"ok": True, "items": items_to_ext(merged), "count": len(merged)}


def native_host():
    """Chrome native messaging: 4-byte little-endian length + UTF-8 JSON, both directions."""
    stdin, stdout = sys.stdin.buffer, sys.stdout.buffer
    while True:
        raw_len = stdin.read(4)
        if len(raw_len) < 4:
            return 0
        msg = json.loads(stdin.read(struct.unpack("<I", raw_len)[0]).decode("utf-8"))
        try:
            if msg.get("cmd") == "sync":
                reply = bridge_sync(msg)
            elif msg.get("cmd") == "ping":
                reply = {"ok": True, "file": TODO_FILE}
            else:
                reply = {"ok": False, "error": f"unknown cmd {msg.get('cmd')!r}"}
        except Exception as e:  # noqa: BLE001 - report to the extension instead of dying
            log(f"bridge error: {e}")
            reply = {"ok": False, "error": str(e)}
        data = json.dumps(reply).encode("utf-8")
        stdout.write(struct.pack("<I", len(data)) + data)
        stdout.flush()


BROWSER_DIRS = ["Google/Chrome", "Google/Chrome Beta", "Google/Chrome Canary", "Google/Chrome Dev",
                "Chromium", "BraveSoftware/Brave-Browser", "Microsoft Edge", "Vivaldi"]


def find_stickysites_installs():
    """(browser dir, extension id) for every profile that loads StickySites unpacked from a repo."""
    found = set()
    for bdir in BROWSER_DIRS:
        root = os.path.join(HOME, "Library/Application Support", bdir)
        for prefs in glob.glob(os.path.join(root, "*", "Preferences")) + glob.glob(os.path.join(root, "*", "Secure Preferences")):
            settings = read_json(prefs, {}).get("extensions", {}).get("settings", {})
            for ext_id, s in settings.items():
                if str(s.get("path", "")).rstrip("/").endswith("/stickysites"):
                    found.add((root, ext_id))
    return sorted(found)


def install_native_host():
    wrapper = os.path.join(os.path.dirname(SCRIPT), "todo_host")
    atomic_write(wrapper, f'#!/bin/sh\nexec /usr/bin/python3 "{SCRIPT}" native-host\n')
    os.chmod(wrapper, 0o755)
    installs = find_stickysites_installs()
    by_root = {}
    for root, ext_id in installs:
        by_root.setdefault(root, set()).add(ext_id)
    for root, ids in by_root.items():
        manifest = {"name": HOST_NAME, "description": "Personal to-do list bridge for StickySites",
                    "path": wrapper, "type": "stdio",
                    "allowed_origins": [f"chrome-extension://{i}/" for i in sorted(ids)]}
        path = os.path.join(root, "NativeMessagingHosts", f"{HOST_NAME}.json")
        atomic_write(path, json.dumps(manifest, indent=2) + "\n")
        print(f"registered {HOST_NAME} for {', '.join(sorted(ids))} -> {path}")
    if not installs:
        print("StickySites is not loaded in any browser profile here; load it unpacked from ~/dev/stickysites, then rerun.")
    return 0


def install_launchd(interval):
    label = "com.mitch.todo-sync"
    plist = os.path.join(HOME, "Library/LaunchAgents", f"{label}.plist")
    cmd = f"/usr/bin/python3 {shlex.quote(SCRIPT)} sync --quiet; /usr/bin/python3 {shlex.quote(SCRIPT)} peer-sync --quiet"
    atomic_write(plist, f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>{label}</string>
  <key>ProgramArguments</key><array><string>/bin/sh</string><string>-c</string><string>{cmd}</string></array>
  <key>StartInterval</key><integer>{interval}</integer>
  <key>RunAtLoad</key><true/>
  <key>StandardErrorPath</key><string>{LOG_FILE}</string>
</dict></plist>
""")
    uid = os.getuid()
    subprocess.run(["launchctl", "bootout", f"gui/{uid}", plist], capture_output=True)
    res = subprocess.run(["launchctl", "bootstrap", f"gui/{uid}", plist], capture_output=True, text=True)
    print(f"{'loaded' if res.returncode == 0 else 'FAILED to load'} {plist} (every {interval}s) {res.stderr.strip()}")
    return res.returncode


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("text")
    a.add_argument("--source", default="manual")
    sub.add_parser("done").add_argument("key")
    sub.add_parser("list").add_argument("--all", action="store_true")
    s = sub.add_parser("sync")
    s.add_argument("--tiers", default="2", help="comma list of memory-central tiers, e.g. 2,3")
    s.add_argument("--since-days", type=int, default=60)
    s.add_argument("--session")
    s.add_argument("--quiet", action="store_true")
    p = sub.add_parser("peer-sync")
    p.add_argument("targets", nargs="*")
    p.add_argument("--quiet", action="store_true")
    sub.add_parser("export-json")
    sub.add_parser("import-json").add_argument("--expect", required=True)
    sub.add_parser("native-host")
    sub.add_parser("install-native-host")
    sub.add_parser("install-launchd").add_argument("--interval", type=int, default=300)
    sub.add_parser("hook-session-end")
    args = ap.parse_args()

    if args.cmd == "add":
        item_id = add_item(args.text, args.source)
        print(f"added {item_id}" if item_id else "already on the list (or dismissed earlier)")
    elif args.cmd == "done":
        with Store() as st:
            hits = [i for i in st.items if not i["done"] and (i["id"] == args.key or args.key.lower() in i["text"].lower())]
            if len(hits) != 1:
                print(f"{len(hits)} open items match {args.key!r}; use the id", file=sys.stderr)
                for i in hits[:10]:
                    print(f"  {i['id']}  {i['text']}", file=sys.stderr)
                return 1
            hits[0]["done"] = True
            hits[0]["meta"] = (hits[0].get("meta", "") + f" · done {today()}").strip(" ·")
            print(f"done {hits[0]['id']}")
    elif args.cmd == "list":
        for i in parse_todo():
            if args.all or not i["done"]:
                proj = f"[{i['proj']}] " if i.get("proj") else ""
                print(f"{i['id']}  {group_of(i) if not i['done'] else 'Done':<16} {proj}{i['text']}")
    elif args.cmd == "sync":
        added = sync_sources(tuple(int(t) for t in args.tiers.split(",")), args.since_days, args.session)
        if not args.quiet:
            print(f"sync: {added} new -> {TODO_FILE}")
    elif args.cmd == "peer-sync":
        rc = 0
        for t in peer_targets(args.targets):
            try:
                n = peer_sync_one(t)
                log(f"peer-sync {t}: {n} items")
                if not args.quiet:
                    print(f"peer-sync {t}: ok, {n} items")
            except Exception as e:  # noqa: BLE001 - one unreachable peer must not stop the others
                log(f"peer-sync {t}: {e}")
                print(f"peer-sync {t}: {e}", file=sys.stderr)
                rc = 1
        return rc
    elif args.cmd == "export-json":
        print(json.dumps(export_doc()))
    elif args.cmd == "import-json":
        return 0 if import_doc(json.load(sys.stdin), args.expect) else 3
    elif args.cmd == "native-host":
        return native_host()
    elif args.cmd == "install-native-host":
        return install_native_host()
    elif args.cmd == "install-launchd":
        return install_launchd(args.interval)
    elif args.cmd == "hook-session-end":
        # Never fail a session over the to-do list.
        try:
            payload = json.load(sys.stdin)
            sync_sources(ended_session=payload.get("session_id"))
        except Exception as e:  # noqa: BLE001
            log(f"session-end hook skipped: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
