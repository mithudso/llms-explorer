"""Acquire and reconcile the pinned Awesome TUIs inventory; never run listed tools.

Raw responses are private. Public records contain bounded quotations and source
observations, not an assertion that a program was installed or independently tested.
Uses the Python standard library and optional GitHub CLI authentication.
"""

from __future__ import annotations

import argparse
import base64
import collections
import hashlib
import html
import json
import re
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

VERSION = "1.0.1"
LIST_REPO = "rothgar/awesome-tuis"
PIN = "98a107625c87cca75cd5785afcb61a91e46bb6af"
PRIVATE = Path(
    "/Users/mitch/.global-ai-hub/research/awesome-tuis-2026-10-24/catalog-sources"
)
OUTPUT = Path(__file__).resolve().parent
USER_AGENT = "LLMS-Explorer-awesome-tuis-research/1.0 (read-only source acquisition)"
LOCK = threading.Lock()


def now():
    return datetime.now(UTC).isoformat(timespec="seconds")


def atomic(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temp.replace(path)


def digest(value):
    return hashlib.sha256(value).hexdigest()


def github_token():
    result = subprocess.run(
        ["gh", "auth", "token"], capture_output=True, text=True, check=False
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def fetch(url, token="", retry_failed=False):
    """Checkpoint exact response bytes and metadata; never persist authorization."""
    key = digest(url.encode())
    meta_path = PRIVATE / "responses" / (key + ".json")
    body_path = PRIVATE / "responses" / (key + ".body")
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
        if meta["ok"] or not retry_failed:
            return meta, body_path.read_bytes() if body_path.exists() else b""
    headers = {"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"}
    if token and urlparse(url).hostname == "api.github.com":
        headers["Authorization"] = "Bearer " + token
    meta = {"requested_url": url, "observed_at": now(), "ok": False}
    body = b""
    for attempt in range(3):
        try:
            time.sleep(0.12)
            with urlopen(Request(url, headers=headers), timeout=18) as response:
                body = response.read(6_000_000)
                meta.update(
                    ok=True,
                    status=response.status,
                    final_url=response.url,
                    content_type=response.headers.get("Content-Type"),
                    etag=response.headers.get("ETag"),
                    sha256=digest(body),
                    bytes=len(body),
                )
            break
        except HTTPError as error:
            meta.update(
                status=error.code, error=f"HTTP {error.code}", final_url=error.url
            )
            if error.code in (403, 429):
                wait = min(int(error.headers.get("Retry-After", "8")), 30)
                time.sleep(wait)
            elif error.code not in (408, 500, 502, 503, 504):
                break
        except (URLError, TimeoutError, OSError) as error:
            meta["error"] = f"{type(error).__name__}: {str(error)[:180]}"
            time.sleep(attempt + 1)
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    if body:
        body_path.write_bytes(body)
    atomic(meta_path, meta)
    return meta, body


def json_fetch(url, token="", retry_failed=False):
    meta, raw = fetch(url, token, retry_failed)
    try:
        value = json.loads(raw) if meta["ok"] else {}
    except (json.JSONDecodeError, UnicodeDecodeError):
        meta = {**meta, "ok": False, "error": "Non-JSON API response"}
        value = {}
    return meta, value


def clean(value):
    value = re.sub(r"<[^>]+>", " ", value or "")
    value = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", value)
    value = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", value)
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def short_quote(value, words=12):
    tokens = clean(value).split()
    return " ".join(tokens[:words]) + (" …" if len(tokens) > words else "")


def readme_description(text):
    """Select introductory narrative or a title, never a later procedure."""
    heading = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    html_heading = re.search(r"<h1\b[^>]*>(.*?)</h1>", text, re.IGNORECASE | re.DOTALL)
    title = (
        clean(heading[1]) if heading else clean(html_heading[1]) if html_heading else ""
    )
    procedural_section = re.search(
        r"^#{1,6}\s+(?:installation|install|usage|quick\s*start|getting started|how to build|"
        r"build|compilation|dependencies|requirements|prerequisites|screenshots|features|"
        r"contributing|development|license)\b",
        text,
        re.IGNORECASE | re.MULTILINE,
    )
    introduction = text[: procedural_section.start()] if procedural_section else text
    introduction = re.sub(r"^#{1,6}\s+.*$", "\n", introduction, flags=re.MULTILINE)
    introduction = re.sub(
        r"<h[1-6]\b[^>]*>.*?</h[1-6]>",
        "\n",
        introduction,
        flags=re.IGNORECASE | re.DOTALL,
    )
    for paragraph in re.split(r"\n\s*\n", introduction):
        prose = clean(paragraph)
        if not 3 <= len(prose.split()) <= 100:
            continue
        if paragraph.lstrip().startswith(("!", "[", "|", "```", "-", "*")):
            continue
        if re.match(
            r"(?:when updating|installation|before you|for more information|the primary distribution|a list of mirror|https?://|you can install|if you|run\b|sudo\b|this application has been built)",
            prose,
            re.IGNORECASE,
        ):
            continue
        return short_quote(prose), "document introductory narrative"
    return (short_quote(title), "document title") if title else ("", "unavailable")


def parse_inventory(text):
    category = None
    entries = []
    for line_number, line in enumerate(text.splitlines(), 1):
        heading = re.search(r"<h2>(.*?)</h2>", line)
        if heading:
            category = clean(heading.group(1))
        match = re.match(r"^[-*] \[([^\]]+)\]\((https?://[^)]+)\)\s*(.*)", line)
        if match:
            if not category:
                raise ValueError(f"Project outside a category on line {line_number}")
            entries.append(
                {
                    "entry_id": f"tui-{len(entries) + 1:04d}",
                    "name": match[1],
                    "category": category,
                    "listed_url": match[2],
                    "list_line": line_number,
                }
            )
    return entries


def document_observations(text):
    # These report literal documentation mentions, not inferred support promises.
    lower = text.lower()
    platforms = {
        "Linux": r"\blinux\b",
        "macOS": r"\bmacos\b|\bmac os\b|\bos x\b",
        "Windows": r"\bwindows\b",
        "FreeBSD": r"\bfreebsd\b",
        "OpenBSD": r"\bopenbsd\b",
        "NetBSD": r"\bnetbsd\b",
        "Android": r"\bandroid\b",
        "Unix": r"\bunix\b",
    }
    installers = {
        "Homebrew": r"\bbrew install\b",
        "Cargo": r"\bcargo install\b",
        "pip/pipx/uv": r"\b(?:pip3?|pipx|uv tool) install\b",
        "npm/npx": r"\bnpm (?:install|i)\b|\bnpx\b",
        "Go": r"\bgo install\b",
        "APT": r"\bapt(?:-get)? install\b",
        "Nix": r"\bnix(?:-env| profile| run| shell)\b|\bnixpkgs\b",
        "Pacman": r"\bpacman -S\b",
        "Scoop": r"\bscoop install\b",
        "Chocolatey": r"\bchoco install\b",
        "Snap": r"\bsnap install\b",
        "Docker": r"\bdocker run\b|\bdocker compose\b",
        "Source build": r"\b(?:make install|cargo build|go build|cmake)\b",
    }
    topics = {
        "configuration": r"\bconfigur",
        "keyboard shortcuts": r"\bkeybind|\bshortcuts?\b",
        "mouse input": r"\bmouse\b",
        "themes/colors": r"\bthemes?\b|\bcolou?rs?\b",
        "plugins/extensions": r"\bplugins?\b|\bextensions?\b",
        "SSH/remote use": r"\bssh\b",
        "search/filtering": r"\bsearch\b|\bfiltering\b",
        "accessibility": r"\baccessibility\b|\bscreen reader\b",
        "Unicode": r"\bunicode\b",
        "terminal compatibility": r"\bterminal emulator\b|\bterminfo\b",
        "authentication": r"\bauthenticat|\bapi key\b|\boauth\b",
    }
    return {
        "platform_mentions": [k for k, v in platforms.items() if re.search(v, lower)],
        "documented_install_methods": [
            k for k, v in installers.items() if re.search(v, text, re.IGNORECASE)
        ],
        "documentation_topics": [k for k, v in topics.items() if re.search(v, lower)],
    }


def github_project(url):
    parsed = urlparse(url)
    if parsed.hostname not in ("github.com", "www.github.com"):
        return None
    parts = parsed.path.strip("/").split("/")
    return "/".join(parts[:2]).removesuffix(".git") if len(parts) >= 2 else None


def acquire_github(project, token, retry_failed=False):
    api = "https://api.github.com/repos/" + project
    meta, repo = json_fetch(api, token, retry_failed)
    result = {
        "metadata_url": api,
        "metadata_status": meta.get("status"),
        "observed_at": meta["observed_at"],
        "metadata_sha256": meta.get("sha256"),
        "canonical_url": repo.get("html_url", "https://github.com/" + project),
        "primary_language": repo.get("language"),
        "license_spdx": (repo.get("license") or {}).get("spdx_id"),
        "archived": repo.get("archived"),
        "disabled": repo.get("disabled"),
        "homepage": repo.get("homepage") or None,
        "first_party_description_quote": short_quote(repo.get("description")),
        "description_source_url": api,
        "description_kind": "repository description",
        "source_owner": repo.get("full_name", project).split("/")[0],
        "readme": {},
        "limitations": [],
    }
    if not meta["ok"]:
        result["limitations"].append(
            "GitHub repository metadata unavailable: "
            + meta.get("error", "unknown error")
        )
    readme_meta, readme = json_fetch(api + "/readme", token, retry_failed)
    if readme_meta["ok"] and readme.get("content"):
        raw = base64.b64decode(readme["content"])
        text = raw.decode("utf-8", "replace")
        blob = readme.get("sha")
        source_url = (
            "https://github.com/"
            + repo.get("full_name", project)
            + "/blob/"
            + str(blob)
            + "/"
            + readme.get("path", "README.md")
        )
        # A Git blob SHA pins its bytes but is not a commit. Use the valid blob API
        # as the immutable source URL and keep the branch-based human README URL.
        source_url = readme.get("git_url") or source_url
        path = PRIVATE / "documents" / (digest(api.encode()) + ".txt")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        result["readme"] = {
            "status": "retrieved",
            "url": readme.get("html_url"),
            "immutable_blob_url": source_url,
            "blob_sha": blob,
            "sha256": digest(raw),
            "bytes": len(raw),
            "observed_at": readme_meta["observed_at"],
        }
        if not result["first_party_description_quote"]:
            description, kind = readme_description(text)
            result.update(
                first_party_description_quote=description,
                description_kind=kind,
                description_source_url=readme.get("html_url"),
            )
        result.update(document_observations(text))
        result["acquisition_status"] = "PRIMARY-README"
    else:
        result["readme"] = {
            "status": "unavailable",
            "api_url": api + "/readme",
            "http_status": readme_meta.get("status"),
            "reason": readme_meta.get("error", "No inline README content"),
            "observed_at": readme_meta["observed_at"],
        }
        result["acquisition_status"] = (
            "PRIMARY-METADATA-ONLY" if meta["ok"] else "SOURCE-GAP"
        )
        result["limitations"].append(
            "README unavailable; installation, platform and feature documentation were not assessed."
        )
    if meta["ok"] and not result["first_party_description_quote"] and repo.get("name"):
        result.update(
            first_party_description_quote=short_quote(repo["name"]),
            description_source_url=api,
            description_kind="repository title",
        )
    return result


def acquire_site(url, retry_failed=False):
    meta, raw = fetch(url, retry_failed=retry_failed)
    if not meta["ok"] and url.startswith("http://"):
        meta, raw = fetch("https://" + url[7:], retry_failed=retry_failed)
    if not meta["ok"] and urlparse(url).hostname == "gitlab.com":
        for suffix in (
            "/-/raw/master/README.md",
            "/-/raw/main/README.md",
            "/-/raw/master/README",
            "/-/tree/master",
        ):
            candidate_meta, candidate_raw = fetch(
                url.rstrip("/") + suffix, retry_failed=retry_failed
            )
            if candidate_meta["ok"]:
                meta, raw = candidate_meta, candidate_raw
                break
    if not meta["ok"] and urlparse(url).hostname == "sourceforge.net":
        project = urlparse(url).path.strip("/").split("/")
        if len(project) >= 2 and project[0] == "projects":
            candidate_meta, candidate_raw = fetch(
                f"https://{project[1]}.sourceforge.io/", retry_failed=retry_failed
            )
            if candidate_meta["ok"]:
                meta, raw = candidate_meta, candidate_raw
    if not meta["ok"] and (urlparse(url).hostname or "").endswith(".sourceforge.net"):
        candidate_meta, candidate_raw = fetch(
            url.replace("http://", "https://").replace(
                ".sourceforge.net", ".sourceforge.io"
            ),
            retry_failed=retry_failed,
        )
        if candidate_meta["ok"]:
            meta, raw = candidate_meta, candidate_raw
    if meta["ok"]:
        preview = raw.decode("utf-8", "replace")
        redirect = re.search(r'Redirecting to:\s*(https?://[^\s<"\']+)', preview)
        if redirect:
            redirected_meta, redirected_raw = fetch(
                html.unescape(redirect[1]), retry_failed=retry_failed
            )
            if redirected_meta["ok"]:
                meta, raw = redirected_meta, redirected_raw
    if "NetworkManager/stable/nmtui.html" in url and meta.get("final_url", "").endswith(
        "/docs/api/latest/"
    ):
        candidate_meta, candidate_raw = fetch(
            "https://networkmanager.dev/docs/api/latest/nmtui.html",
            retry_failed=retry_failed,
        )
        if candidate_meta["ok"]:
            meta, raw = candidate_meta, candidate_raw
    result = {
        "canonical_url": meta.get("final_url", url),
        "observed_at": meta["observed_at"],
        "primary_language": None,
        "license_spdx": None,
        "archived": None,
        "disabled": None,
        "first_party_description_quote": "",
        "description_source_url": meta.get("final_url", url),
        "source_owner": urlparse(url).hostname,
        "limitations": [],
        "site": {
            "status": "retrieved" if meta["ok"] else "unavailable",
            "requested_url": meta["requested_url"],
            "url": meta.get("final_url", url),
            "sha256": meta.get("sha256"),
            "http_status": meta.get("status"),
            "bytes": len(raw),
            "observed_at": meta["observed_at"],
        },
    }
    if meta["ok"]:
        text = raw.decode("utf-8", "replace")
        text = re.sub(
            r"<(script|style)\b[^>]*>.*?</\1>",
            " ",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        desc = re.search(
            r'<meta\s+[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)',
            text,
            re.IGNORECASE,
        )
        title = re.search(r"<title[^>]*>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
        result["first_party_description_quote"] = short_quote(
            desc[1] if desc else title[1] if title else ""
        )
        result["description_kind"] = (
            "page description" if desc else "page title" if title else "unavailable"
        )
        if not result["first_party_description_quote"]:
            result["first_party_description_quote"], result["description_kind"] = (
                readme_description(text)
            )
        body = clean(text)
        # Bot challenges and generic repository host login pages are not evidence.
        blocked = any(
            x in body.lower()
            for x in (
                "checking your browser",
                "verify you are human",
                "access denied",
                "making sure you're not a bot",
            )
        )
        title_text = clean(title[1]).lower() if title else ""
        blocked = blocked or title_text in (
            "just a moment...",
            "sign in · gitlab",
            "404 not found",
            "page not found",
        )
        blocked = blocked or "/users/sign_in" in meta.get("final_url", "")
        parked = any(
            host in (urlparse(meta.get("final_url", "")).hostname or "")
            for host in (
                "expireddomains.com",
                "sedo.com",
                "afternic.com",
                "hugedomains.com",
                "dan.com",
            )
        )
        parked = parked or any(
            marker in body.lower()
            for marker in (
                "this domain is for sale",
                "domain available for buy",
                "buy this domain",
                "domain has expired",
            )
        )
        blocked = blocked or parked
        if blocked or len(body) < 100:
            result["acquisition_status"] = "SOURCE-GAP"
            result["site"]["status"] = (
                "domain-parking-rejected" if parked else "challenge-or-thin-page"
            )
            result["first_party_description_quote"] = ""
            result["limitations"].append(
                "The listed domain redirects to a domain-sale/parking service. This is not a project source."
                if parked
                else "The fetched page was a challenge or contained too little readable project text."
            )
        else:
            result["acquisition_status"] = "PRIMARY-SITE"
            result.update(document_observations(body))
        result["limitations"].append(
            "Repository language, license and archive flags were not established from this page."
        )
    else:
        result["acquisition_status"] = "SOURCE-GAP"
        result["site"]["reason"] = meta.get("error", "unknown error")
        result["limitations"].append(
            "Official project page unavailable: " + meta.get("error", "unknown error")
        )
    return result


def acquire_gitlab(url, retry_failed=False):
    """Use GitLab's declared README path; root pages can return false 404s."""
    project = urlparse(url).path.strip("/")
    api = "https://gitlab.com/api/v4/projects/" + quote(project, safe="")
    meta, repo = json_fetch(api, retry_failed=retry_failed)
    if not meta["ok"]:
        return acquire_site(url, retry_failed)
    result = {
        "canonical_url": repo.get("web_url", url),
        "metadata_url": api,
        "metadata_status": meta.get("status"),
        "metadata_sha256": meta.get("sha256"),
        "observed_at": meta["observed_at"],
        "source_owner": "gitlab.com:" + project.split("/")[0],
        "first_party_description_quote": short_quote(repo.get("description")),
        "description_source_url": api,
        "description_kind": "repository description",
        "primary_language": None,
        "license_spdx": None,
        "archived": repo.get("archived"),
        "disabled": None,
        "acquisition_status": "PRIMARY-METADATA-ONLY",
        "limitations": [],
    }
    readme_url = (repo.get("readme_url") or "").replace("/-/blob/", "/-/raw/")
    readme_meta, raw = (
        fetch(readme_url, retry_failed=retry_failed)
        if readme_url
        else ({"ok": False}, b"")
    )
    if readme_meta["ok"]:
        text = raw.decode("utf-8", "replace")
        path = PRIVATE / "documents" / (digest(api.encode()) + ".txt")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        result["readme"] = {
            "status": "retrieved",
            "url": readme_url,
            "sha256": digest(raw),
            "bytes": len(raw),
            "observed_at": readme_meta["observed_at"],
        }
        result.update(document_observations(text))
        result["acquisition_status"] = "PRIMARY-README"
        if not result["first_party_description_quote"]:
            description, kind = readme_description(text)
            result.update(
                first_party_description_quote=description,
                description_kind=kind,
                description_source_url=readme_url,
            )
    else:
        result["readme"] = {
            "status": "unavailable",
            "url": readme_url,
            "reason": readme_meta.get("error", "No declared README"),
        }
        result["limitations"].append(
            "GitLab metadata was retrieved, but the declared README could not be read."
        )
    result["limitations"].append(
        "Primary language, license identifier and any archive flag absent from GitLab's response remain unestablished."
    )
    if not result["first_party_description_quote"] and repo.get("name"):
        result.update(
            first_party_description_quote=short_quote(repo["name"]),
            description_source_url=api,
            description_kind="repository title",
        )
    return result


def acquire_listed_subdirectory(entry, result, token):
    """Bind a listed component to its own README, preserving parent metadata scope."""
    parts = urlparse(entry["listed_url"]).path.strip("/").split("/")
    if len(parts) < 5 or parts[2] != "tree":
        return result
    parent = "/".join(parts[:2])
    branch, subdirectory = parts[3], "/".join(parts[4:])
    api = f"https://api.github.com/repos/{parent}/contents/{subdirectory}/README.md?ref={quote(branch, safe='')}"
    meta, doc = json_fetch(api, token)
    scoped = {
        **result,
        "limitations": list(result["limitations"]),
        "canonical_url": entry["listed_url"],
        "metadata_scope": "parent repository",
        "description_scope": "listed subdirectory",
    }
    if not meta["ok"] or not doc.get("content"):
        scoped["acquisition_status"] = "SOURCE-GAP"
        scoped["first_party_description_quote"] = ""
        scoped["limitations"].append(
            "The listed subdirectory README could not be read. Parent repository information does not establish component-specific behavior."
        )
        return scoped
    raw = base64.b64decode(doc["content"])
    key = digest(api.encode())
    (PRIVATE / "documents" / (key + ".txt")).write_bytes(raw)
    text = raw.decode("utf-8", "replace")
    title = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    description, kind = (
        (short_quote(title[1]), "document title") if title else readme_description(text)
    )
    scoped.update(
        first_party_description_quote=description,
        description_kind=kind,
        description_source_url=doc["html_url"],
        acquisition_status="PRIMARY-README",
    )
    scoped["readme"] = {
        "status": "retrieved",
        "url": doc["html_url"],
        "api_url": api,
        "immutable_blob_url": doc.get("git_url"),
        "blob_sha": doc.get("sha"),
        "sha256": digest(raw),
        "bytes": len(raw),
        "observed_at": meta["observed_at"],
        "document_storage_key": key,
    }
    scoped.update(document_observations(text))
    scoped["limitations"].append(
        "Language, license and archive metadata describe the parent repository. The quoted title and documentation mentions come from the listed subdirectory's own README."
    )
    return scoped


def render(catalog):
    out = [
        "# Awesome TUIs: complete project evidence catalog",
        "",
        f"Version {VERSION}. This is a first-party documentation survey, not installation testing or a claim of depth saturation.",
        "",
        f"Inventory: {catalog['inventory']['url']}",
        "",
        f"Pinned list commit: `{catalog['inventory']['commit']}`; README SHA-256: `{catalog['inventory']['sha256']}`.",
        "",
        (
            "Each short description below is a bounded quotation from project metadata or the official page, not the Awesome list. "
            "Platform names, installation families and documentation topics report literal mentions in the fetched README/page. "
            "A mention does not prove support or successful installation. Missing license fields do not establish permission to use the project. "
            "Archive flags are GitHub API observations at the stated date. Raw bodies remain private."
        ),
        "",
    ]
    categories = list(dict.fromkeys(x["category"] for x in catalog["entries"]))
    out.extend(["## Contents", ""])
    for category in categories:
        anchor = re.sub(r"[^a-z0-9 -]", "", category.lower()).replace(" ", "-")
        out.append(f"- [{category}](#{anchor})")
    for category in categories:
        out.extend(["", "## " + category, ""])
        for entry in (x for x in catalog["entries"] if x["category"] == category):
            out.extend(
                [
                    f"### {entry['entry_id']}: {entry['name']}",
                    "",
                    entry["listed_url"],
                    "",
                ]
            )
            if entry["canonical_url"].rstrip("/") != entry["listed_url"].rstrip("/"):
                out.extend(["Canonical project: " + entry["canonical_url"], ""])
            desc = entry.get("first_party_description_quote")
            out.extend(
                [
                    f"First-party {entry.get('description_kind', 'description/title')}: “{desc}”"
                    if desc
                    else "First-party short description: unavailable.",
                    "",
                ]
            )
            out.append(
                f"Evidence: **{entry['acquisition_status']}**. Observed: {entry['observed_at']}."
            )
            if entry.get("metadata_url"):
                license_id = entry.get("license_spdx") or "not established"
                out.append(
                    f"Primary language: {entry.get('primary_language') or 'not established'}; license identifier: {license_id}; archived: {entry.get('archived')}; disabled: {entry.get('disabled')}."
                )
                out.append("Metadata source: " + entry["metadata_url"])
            doc = entry.get("readme") or entry.get("site") or {}
            if doc.get("url"):
                out.append("Documentation source: " + doc["url"])
            if doc.get("immutable_blob_url"):
                out.append("Immutable README blob: " + doc["immutable_blob_url"])
            if doc.get("sha256"):
                out.append("Document SHA-256: `" + doc["sha256"] + "`.")
            if doc.get("retrieval_method"):
                out.append(
                    f"Retrieval: {doc['retrieval_method']}; cache age reported by web tool: {doc.get('cache_age_days_reported')} days; direct HTTP status: {doc.get('http_status')}."
                )
            for key, label in [
                ("platform_mentions", "Platform mentions"),
                ("documented_install_methods", "Installation families mentioned"),
                ("documentation_topics", "Documentation topics mentioned"),
            ]:
                out.append(
                    label
                    + ": "
                    + (
                        ", ".join(entry.get(key, []))
                        or "not established from fetched documentation"
                    )
                    + "."
                )
            if entry.get("shared_repository_metadata_with"):
                out.append(
                    "Repository metadata is shared with "
                    + entry["shared_repository_metadata_with"]
                    + "; these are distinct listed targets."
                )
            out.extend("Limitation: " + x for x in entry.get("limitations", []))
            out.append("")
    return "\n".join(out) + "\n"


def validate(catalog):
    source = PRIVATE / "inventory.md"
    if not source.exists():
        raise ValueError("Pinned private inventory body is required for reconciliation")
    raw = source.read_bytes()
    if digest(raw) != catalog["inventory"]["sha256"]:
        raise ValueError("Inventory source hash mismatch")
    expected = parse_inventory(raw.decode())
    actual = catalog["entries"]
    verified_source_bodies = set()
    if len(actual) != len(expected):
        raise ValueError("Dropped or extra inventory rows")
    for wanted, got in zip(expected, actual):
        for key in wanted:
            if got.get(key) != wanted[key]:
                raise ValueError(f"Inventory mismatch {wanted['entry_id']} {key}")
        if got.get("acquisition_status") not in (
            "PRIMARY-README",
            "PRIMARY-SITE",
            "PRIMARY-SITE-EXCERPT",
            "PRIMARY-METADATA-ONLY",
            "SOURCE-GAP",
        ):
            raise ValueError("Unaccounted source status: " + wanted["entry_id"])
        if (
            len(got.get("first_party_description_quote", "").replace("…", "").split())
            > 25
        ):
            raise ValueError("Description quotation exceeds 25 words")
        if got["acquisition_status"] == "PRIMARY-README" and not got.get(
            "readme", {}
        ).get("sha256"):
            raise ValueError("README claimed without hash")
        if got["acquisition_status"] == "SOURCE-GAP" and not got.get("limitations"):
            raise ValueError("Source gap without reason")
        if got.get("metadata_sha256"):
            key = digest(got["metadata_url"].encode())
            body = PRIVATE / "responses" / (key + ".body")
            if not body.exists() or digest(body.read_bytes()) != got["metadata_sha256"]:
                raise ValueError("Metadata body hash mismatch: " + wanted["entry_id"])
            verified_source_bodies.add(str(body))
        if got.get("readme", {}).get("status") == "retrieved":
            body = (
                PRIVATE
                / "documents"
                / (
                    got["readme"].get(
                        "document_storage_key", digest(got["metadata_url"].encode())
                    )
                    + ".txt"
                )
            )
            if (
                not body.exists()
                or digest(body.read_bytes()) != got["readme"]["sha256"]
            ):
                raise ValueError("README body hash mismatch: " + wanted["entry_id"])
            verified_source_bodies.add(str(body))
        if got["acquisition_status"] == "PRIMARY-SITE":
            body = (
                PRIVATE
                / "responses"
                / (digest(got["site"]["requested_url"].encode()) + ".body")
            )
            if not body.exists() or digest(body.read_bytes()) != got["site"]["sha256"]:
                raise ValueError(
                    "Official page body hash mismatch: " + wanted["entry_id"]
                )
            verified_source_bodies.add(str(body))
        if got["acquisition_status"] == "PRIMARY-SITE-EXCERPT":
            index = json.loads((PRIVATE / "web-excerpts" / "index.json").read_text())
            item = next(
                x
                for x in index
                if x["listed_host"] == urlparse(got["listed_url"]).hostname
            )
            body = Path(item["text_path"])
            if digest(body.read_bytes()) != got["site"]["sha256"]:
                raise ValueError("Web excerpt hash mismatch: " + wanted["entry_id"])
            verified_source_bodies.add(str(body))
    categories = collections.Counter(e["category"] for e in actual)
    statuses = collections.Counter(e["acquisition_status"] for e in actual)
    gaps = [
        {
            "entry_id": e["entry_id"],
            "name": e["name"],
            "url": e["listed_url"],
            "status": e["acquisition_status"],
            "limitations": e["limitations"],
        }
        for e in actual
        if e["acquisition_status"] in ("SOURCE-GAP", "PRIMARY-METADATA-ONLY")
    ]
    return {
        "schema_version": "1.0.0",
        "validated_at": now(),
        "inventory_commit": PIN,
        "inventory_sha256": digest(raw),
        "inventory_rows": len(expected),
        "catalog_rows": len(actual),
        "missing_rows": 0,
        "extra_rows": 0,
        "mismatched_rows": 0,
        "verified_private_source_bodies": len(verified_source_bodies),
        "categories": dict(categories),
        "source_statuses": dict(statuses),
        "unique_listed_urls": len(
            {e["listed_url"].rstrip("/").lower() for e in actual}
        ),
        "repository_metadata_acquisition_groups": len(
            {github_project(e["listed_url"]) or e["listed_url"] for e in actual}
        ),
        "shared_repository_metadata_rows": [
            e["entry_id"] for e in actual if e.get("shared_repository_metadata_with")
        ],
        "duplicate_rows": [
            e["entry_id"]
            for i, e in enumerate(actual)
            if e["listed_url"] in {p["listed_url"] for p in actual[:i]}
        ],
        "source_gaps": gaps,
        "depth_verdict": "BOUNDARY-BREACH: catalog coverage is a family inventory, not per-project depth saturation",
        "validation": "PASS",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--validate", action="store_true", help="Reconcile existing outputs; no network"
    )
    parser.add_argument("--retry-failed", action="store_true")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if args.validate:
        coverage = validate(json.loads((OUTPUT / "catalog.json").read_text()))
        atomic(OUTPUT / "coverage.json", coverage)
        print(
            json.dumps(
                {
                    k: coverage[k]
                    for k in (
                        "validation",
                        "inventory_rows",
                        "catalog_rows",
                        "source_statuses",
                        "categories",
                    )
                },
                indent=2,
            )
        )
        return
    token = github_token()
    list_url = f"https://raw.githubusercontent.com/{LIST_REPO}/{PIN}/README.md"
    meta, raw = fetch(list_url, token, args.retry_failed)
    if not meta["ok"]:
        raise SystemExit("Pinned inventory retrieval failed")
    PRIVATE.mkdir(parents=True, exist_ok=True)
    (PRIVATE / "inventory.md").write_bytes(raw)
    inventory = parse_inventory(raw.decode())
    projects = {}
    for entry in inventory:
        key = github_project(entry["listed_url"]) or entry["listed_url"]
        projects[key] = entry["listed_url"]
    results = {}
    excerpt_index_path = PRIVATE / "web-excerpts" / "index.json"
    excerpt_index = (
        json.loads(excerpt_index_path.read_text())
        if excerpt_index_path.exists()
        else []
    )
    excerpt_by_host = {item["listed_host"]: item for item in excerpt_index}

    def acquire(item):
        key, url = item
        repo = github_project(url)
        result = (
            acquire_github(repo, token, args.retry_failed)
            if repo
            else acquire_gitlab(url, args.retry_failed)
            if urlparse(url).hostname == "gitlab.com"
            else acquire_site(url, args.retry_failed)
        )
        if (
            urlparse(url).hostname == "meli.delivery"
            and result["acquisition_status"] == "SOURCE-GAP"
        ):
            original_site = result.get("site")
            recovered = acquire_github("meli/meli", token, args.retry_failed)
            if recovered["acquisition_status"] == "PRIMARY-README":
                result = recovered
                result["rejected_listed_site"] = original_site
                result["source_recovery"] = {
                    "reason": "Listed domain is parked. The meli project README identifies this repository as an official mirror.",
                    "authority_url": "https://github.com/meli/meli#readme",
                }
                result["limitations"].append(
                    "The awesome-list website meli.delivery is parked and was rejected. Evidence comes from the project's official GitHub mirror."
                )
        if (
            urlparse(url).hostname == "bombadillo.colorfield.space"
            and result["acquisition_status"] == "SOURCE-GAP"
        ):
            original_site = result.get("site")
            recovered = acquire_site(
                "https://tildegit.org/sloum/bombadillo/raw/branch/master/README.md",
                args.retry_failed,
            )
            if recovered["acquisition_status"] == "PRIMARY-SITE":
                result = recovered
                result["unavailable_listed_site"] = original_site
                result["source_recovery"] = {
                    "reason": "The listed homepage has an expired TLS certificate. Its published project source link identifies the Bombadillo repository.",
                    "authority_url": "https://bombadillo.colorfield.space/",
                }
                result["limitations"].append(
                    "The listed homepage could not be fetched with valid TLS. The official source repository README was retrieved instead."
                )
        if (
            result["acquisition_status"] == "SOURCE-GAP"
            and urlparse(url).hostname in excerpt_by_host
        ):
            excerpt = excerpt_by_host[urlparse(url).hostname]
            excerpt_body = Path(excerpt["text_path"]).read_bytes()
            if digest(excerpt_body) != excerpt["sha256"]:
                raise ValueError("Manual web excerpt hash mismatch: " + url)
            result.update(
                canonical_url=excerpt["url"],
                acquisition_status="PRIMARY-SITE-EXCERPT",
                first_party_description_quote=excerpt["description_quote"],
                description_source_url=excerpt["url"],
                source_owner=excerpt["listed_host"],
                limitations=excerpt["limitations"],
            )
            result["site"] = {
                "status": "web-tool-excerpt-retrieved",
                "requested_url": url,
                "url": excerpt["url"],
                "sha256": excerpt["sha256"],
                "bytes": len(excerpt_body),
                "http_status": result.get("site", {}).get("http_status"),
                "observed_at": now(),
                "retrieval_method": excerpt["retrieval_method"],
                "cache_age_days_reported": excerpt["cache_age_days_reported"],
            }
            result.update(document_observations(excerpt_body.decode("utf-8")))
        with LOCK:
            atomic(PRIVATE / "projects" / (digest(key.encode()) + ".json"), result)
        return key, result

    with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 6))) as pool:
        futures = {pool.submit(acquire, item): item for item in projects.items()}
        for done, future in enumerate(as_completed(futures), 1):
            key, result = future.result()
            results[key] = result
            if done % 25 == 0 or done == len(projects):
                print(f"Acquired {done}/{len(projects)} unique targets", flush=True)
    entries, seen = [], {}
    for entry in inventory:
        key = github_project(entry["listed_url"]) or entry["listed_url"]
        row = {**entry, **acquire_listed_subdirectory(entry, results[key], token)}
        if (
            row.get("metadata_url")
            and row["description_source_url"] == row["metadata_url"]
        ):
            row["description_field"] = (
                "name"
                if row.get("description_kind") == "repository title"
                else "description"
            )
        if entry["name"].lower() == "cfdisk":
            row["description_kind"] = "parent repository description"
            row["description_scope"] = "util-linux parent repository"
            row["limitations"] = [
                *row["limitations"],
                "This source describes the util-linux parent repository. The quoted repository description does not establish cfdisk-specific behavior.",
            ]
        if key in seen:
            row["shared_repository_metadata_with"] = seen[key]
        seen.setdefault(key, entry["entry_id"])
        entries.append(row)
    catalog = {
        "schema_version": "1.0.0",
        "version": VERSION,
        "delta": "1.0.0 to 1.0.1: restrict README descriptions to introductions/titles; distinguish listed targets from shared repository acquisition; bind Square Tic Tac Toe's own README; label parent-repository scope; preserve semantic gate corrections",
        "generated_at": now(),
        "inventory": {
            "url": "https://github.com/" + LIST_REPO,
            "commit": PIN,
            "pinned_readme_url": list_url,
            "sha256": digest(raw),
            "observed_at": meta["observed_at"],
        },
        "method": "Read-only first-party project metadata and README/site acquisition. Mentions are literal documentation observations, not runtime verification. Raw bodies stay private; quotations are at most 25 words per project description.",
        "entries": entries,
    }
    atomic(OUTPUT / "catalog.json", catalog)
    evidence = []
    for entry in entries:
        source_url = (
            entry.get("metadata_url")
            or entry.get("site", {}).get("requested_url")
            or entry["listed_url"]
        )
        key = digest(source_url.encode())
        evidence_body_path = str(PRIVATE / "responses" / (key + ".body"))
        if entry["acquisition_status"] == "PRIMARY-SITE-EXCERPT":
            evidence_body_path = excerpt_by_host[
                urlparse(entry["listed_url"]).hostname
            ]["text_path"]
        evidence.append(
            {
                "entry_id": entry["entry_id"],
                "name": entry["name"],
                "source_owner": entry.get("source_owner"),
                "description_source_url": entry["description_source_url"],
                "description_kind": entry.get("description_kind", "description/title"),
                "description_field": entry.get("description_field"),
                "description_quote": entry["first_party_description_quote"],
                "metadata_or_site_body": evidence_body_path,
                "metadata_or_site_sha256": entry.get("metadata_sha256")
                or entry.get("site", {}).get("sha256"),
                "readme_text": str(
                    PRIVATE
                    / "documents"
                    / (
                        entry["readme"].get(
                            "document_storage_key",
                            digest(entry["metadata_url"].encode()),
                        )
                        + ".txt"
                    )
                )
                if entry.get("metadata_url")
                and entry.get("readme", {}).get("status") == "retrieved"
                else None,
                "readme_sha256": entry.get("readme", {}).get("sha256"),
                "readme_url": entry.get("readme", {}).get("url"),
            }
        )
    atomic(PRIVATE / "evidence-index.json", evidence)
    (OUTPUT / "catalog.md").write_text(render(catalog))
    coverage = validate(catalog)
    atomic(OUTPUT / "coverage.json", coverage)
    print(
        json.dumps(
            {
                k: coverage[k]
                for k in (
                    "validation",
                    "inventory_rows",
                    "catalog_rows",
                    "source_statuses",
                    "categories",
                )
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
