#!/usr/bin/env python3
"""Read-only fleet checks and provider metrics. Private credentials stay on the host.

The HTTP handler only reads completed snapshots. Collection never runs on a scrape.
Failures replace previous measurements, so stale values cannot look current.
"""

import argparse
import concurrent.futures
import datetime as dt
import json
import logging
import logging.handlers
import math
import os
import re
import sqlite3
import subprocess
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from contextlib import closing, contextmanager
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import ClassVar

VERSION = "1.1.1"
ROOT = Path(__file__).resolve().parent
MAX_BODY = 2 * 1024 * 1024
ACCOUNT = "b41ba4dc457dce7653c93af955ecc462"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request_json(url, payload=None, headers=None, method=None):
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={
            "User-Agent": "LLMSX-Operations/" + VERSION,
            "Accept": "application/json",
            **(headers or {}),
        },
        method=method,
    )
    if payload is not None:
        request.add_header("Content-Type", "application/json")
    with urllib.request.build_opener(NoRedirect()).open(
        request, timeout=12
    ) as response:
        if "application/json" not in response.headers.get("Content-Type", "").lower():
            raise ValueError("expected JSON, received non-JSON response")
        raw = response.read(MAX_BODY + 1)
        if len(raw) > MAX_BODY:
            raise ValueError("response exceeds size limit")
        return json.loads(raw)


def cf_json(*args):
    """Use the configured cf CLI, including its OAuth refresh, without logging output."""
    result = subprocess.run(
        [os.environ.get("CF_CLI", "/opt/homebrew/bin/cf"), *args],
        capture_output=True,
        text=True,
        timeout=35,
        check=True,
    )
    # cf prints result_info before its JSON value on list endpoints.
    raw = result.stdout
    if raw.startswith("result_info:"):
        raw = raw.split("\n", 1)[1]
    return json.loads(raw)


def check_http(spec):
    started = time.monotonic()
    status = 0
    ok = False
    capabilities = {}
    try:
        if expected_type := spec.get("head_content_type"):
            request = urllib.request.Request(
                spec["url"],
                method="HEAD",
                headers={"User-Agent": "LLMSX-Operations/" + VERSION},
            )
            with urllib.request.build_opener(NoRedirect()).open(
                request, timeout=12
            ) as response:
                status = response.status
                ok = (
                    status == 200
                    and response.headers.get_content_type() == expected_type
                    and int(response.headers.get("Content-Length", 0)) > 0
                )
            return ok, status, time.monotonic() - started, capabilities
        value = request_json(spec["url"])
        status = 200
        ok = isinstance(value, dict) and all(
            value.get(k) == v for k, v in spec.get("expect", {}).items()
        )
        for name in spec.get("capabilities", []):
            if isinstance(value, dict) and isinstance(value.get(name), bool):
                capabilities[name] = int(value[name])
    except urllib.error.HTTPError as error:
        status = error.code
        error.close()
    except (OSError, ValueError, TimeoutError):
        pass
    return ok, status, time.monotonic() - started, capabilities


def google_seller_file(url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "LLMSX-Operations/" + VERSION, "Accept": "text/plain"},
    )
    try:
        with urllib.request.build_opener(NoRedirect()).open(
            request, timeout=12
        ) as response:
            if (
                response.status != 200
                or response.headers.get_content_type() != "text/plain"
            ):
                raise ValueError("expected a public text seller file")
            body = response.read(524289)
    except urllib.error.HTTPError as error:
        error.close()
        if error.code in {404, 410}:
            return 0
        raise
    if len(body) > 524288:
        raise ValueError("seller file exceeds size limit")
    text = body.decode("utf-8-sig")
    if text.lstrip().startswith("<"):
        raise ValueError("seller file returned HTML")
    for line in text.splitlines():
        fields = [field.strip().lower() for field in line.split("#", 1)[0].split(",")]
        if (
            len(fields) in {3, 4}
            and fields[0] == "google.com"
            and re.fullmatch(r"pub-[0-9]{16}", fields[1])
            and fields[2] in {"direct", "reseller"}
        ):
            return 1
    return 2


def sample(name, value, **labels):
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("metrics must be finite")
    return name, value, {k: str(v) for k, v in labels.items()}


def render_metrics(batches):
    def escape(value):
        return value.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')

    lines = []
    seen = set()
    for name, value, labels in batches:
        if name not in seen:
            lines.extend(
                [
                    f"# HELP {name} Fleet observation; see operating standards for scope and period.",
                    f"# TYPE {name} gauge",
                ]
            )
            seen.add(name)
        suffix = (
            "{"
            + ",".join(f'{k}="{escape(v)}"' for k, v in sorted(labels.items()))
            + "}"
            if labels
            else ""
        )
        lines.append(f"{name}{suffix} {value}")
    return ("\n".join(lines) + "\n").encode()


def validate_log(event):
    """Allowlist monitoring fields; never forward payloads, URLs, tokens or raw errors."""
    allowed = {
        "timestamp",
        "severity",
        "service_name",
        "service_version",
        "project",
        "environment",
        "event",
        "collector",
        "outcome",
        "duration_ms",
        "error_type",
    }
    clean = {k: v for k, v in event.items() if k in allowed}
    for key, value in clean.items():
        if key in {"duration_ms", "timestamp"}:
            if not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError("invalid numeric log attribute")
        elif not isinstance(value, str) or not re.fullmatch(
            r"[A-Za-z0-9_.:-]{1,96}", value
        ):
            raise ValueError("invalid log attribute")
    for key in [
        "timestamp",
        "severity",
        "service_name",
        "service_version",
        "project",
        "environment",
        "event",
    ]:
        if key not in clean:
            raise ValueError("missing required log attribute: " + key)
    if clean["severity"] not in {"debug", "info", "warn", "error", "fatal"}:
        raise ValueError("invalid severity")
    return clean


class LogSpool:
    """Bounded durable delivery queue; a Loki outage never blocks application probes."""

    def __init__(self, path, limit=10000):
        self.path, self.limit = path, limit
        self.lock = threading.Lock()
        with self.connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, timestamp TEXT NOT NULL, body TEXT NOT NULL)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS stats(key TEXT PRIMARY KEY, value INTEGER NOT NULL)"
            )
            db.execute("INSERT OR IGNORE INTO stats VALUES('dropped', 0)")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        try:
            with db:
                yield db
        finally:
            db.close()

    def append(self, event):
        event = validate_log(event)
        with self.lock, self.connect() as db:
            db.execute(
                "INSERT INTO events(timestamp,body) VALUES(?,?)",
                (str(int(event["timestamp"] * 1e9)), json.dumps(event)),
            )
            count = db.execute("SELECT count(*) FROM events").fetchone()[0]
            if count > self.limit:
                excess = count - self.limit
                db.execute(
                    "DELETE FROM events WHERE id IN (SELECT id FROM events ORDER BY id LIMIT ?)",
                    (excess,),
                )
                db.execute(
                    "UPDATE stats SET value=value+? WHERE key='dropped'", (excess,)
                )

    def push(self, endpoint):
        with self.lock, self.connect() as db:
            rows = db.execute(
                "SELECT id,timestamp,body FROM events ORDER BY id LIMIT 100"
            ).fetchall()
        if not rows:
            return True
        req = urllib.request.Request(
            endpoint + "/loki/api/v1/push",
            data=json.dumps(
                {
                    "streams": [
                        {
                            "stream": {
                                "service_name": "fleet-collector",
                                "environment": "production",
                                "project": "fleet",
                            },
                            "values": [[stamp, body] for _, stamp, body in rows],
                        }
                    ]
                }
            ).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.build_opener(NoRedirect()).open(req, timeout=5) as response:
            if response.status != 204:
                return False
        with self.lock, self.connect() as db:
            db.executemany("DELETE FROM events WHERE id=?", [(row[0],) for row in rows])
        return True

    def stats(self):
        with self.lock, self.connect() as db:
            return db.execute("SELECT count(*) FROM events").fetchone()[0], db.execute(
                "SELECT value FROM stats WHERE key='dropped'"
            ).fetchone()[0]


class GoogleToken:
    def __init__(self, path):
        self.path = path
        self.token = None
        self.expires = 0

    def get(self, scope):
        config = json.loads(self.path.read_text())
        if scope not in config.get("scopes", []):
            raise PermissionError("required OAuth scope absent")
        if self.token and self.expires > time.time() + 60:
            return self.token
        payload = urllib.parse.urlencode(
            {
                "client_id": config["client_id"],
                "client_secret": config["client_secret"],
                "refresh_token": config["refresh_token"],
                "grant_type": "refresh_token",
            }
        ).encode()
        # A separate access token in memory. Never rewrite shared ADC credentials.
        req = urllib.request.Request(
            "https://oauth2.googleapis.com/token",
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urllib.request.urlopen(req, timeout=12) as response:
            value = json.loads(response.read(65536))
        self.token, self.expires = (
            value["access_token"],
            time.time() + value["expires_in"],
        )
        return self.token


class Collector:
    intervals: ClassVar = {
        "fast": 60,
        "cloudflare": 300,
        "business": 300,
        "google": 900,
        "ads": 3600,
        "logs": 30,
        "watchdog": 60,
    }

    def __init__(self, inventory, state):
        self.inventory = inventory
        self.state = state
        state.mkdir(parents=True, exist_ok=True)
        self.snapshots = {}
        self.cycles = dict.fromkeys(self.intervals, 0)
        self.last_success = {}
        self.lock = threading.Lock()
        self.stop = threading.Event()
        adc = Path(
            os.environ.get(
                "GOOGLE_APPLICATION_CREDENTIALS",
                str(
                    Path.home() / ".config/gcloud/application_default_credentials.json"
                ),
            )
        )
        self.google_token = GoogleToken(adc)
        self.ads_token = GoogleToken(
            Path(
                os.environ.get(
                    "ADSENSE_CREDENTIALS_FILE", str(state / "adsense-credentials.json")
                )
            )
        )
        self.cf_credentials = Path(
            os.environ.get(
                "CF_CREDENTIALS_FILE",
                str(Path.home() / "Library/Preferences/cloudflare/config/default.json"),
            )
        )
        self.spool = LogSpool(state / "logs.sqlite")
        self.logger = logging.getLogger("fleet-collector")
        self.logger.setLevel(logging.INFO)
        handler = logging.handlers.RotatingFileHandler(
            state / "collector.jsonl", maxBytes=5 * 1024 * 1024, backupCount=3
        )
        handler.setFormatter(logging.Formatter("%(message)s"))
        self.logger.addHandler(handler)

    def integration(
        self, rows, project, source, configured, success, data_present=None
    ):
        labels = {"project": project, "source": source}
        rows.extend(
            [
                sample("fleet_integration_configured", int(configured), **labels),
                sample("fleet_integration_success", int(success), **labels),
                sample(
                    "fleet_integration_attempt_timestamp_seconds", time.time(), **labels
                ),
            ]
        )
        key = project, source
        if success:
            self.last_success[key] = time.time()
        if key in self.last_success:
            rows.append(
                sample(
                    "fleet_integration_last_success_timestamp_seconds",
                    self.last_success[key],
                    **labels,
                )
            )
        if data_present is not None:
            rows.append(
                sample("fleet_integration_data_present", int(data_present), **labels)
            )

    def fast(self):
        import psutil

        rows = []
        host = "origin-mac"
        rows.extend(
            [
                sample(
                    "fleet_host_cpu_ratio",
                    psutil.cpu_percent(interval=0.2) / 100,
                    host=host,
                ),
                sample(
                    "fleet_host_memory_used_ratio",
                    psutil.virtual_memory().percent / 100,
                    host=host,
                ),
                sample(
                    "fleet_host_disk_free_ratio",
                    psutil.disk_usage(str(Path.home())).free
                    / psutil.disk_usage(str(Path.home())).total,
                    host=host,
                ),
                sample(
                    "fleet_host_uptime_seconds",
                    time.time() - psutil.boot_time(),
                    host=host,
                ),
            ]
        )
        specs = self.inventory["checks"]
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            for spec, result in zip(specs, pool.map(check_http, specs), strict=True):
                ok, status, duration, capabilities = result
                labels = {
                    "project": spec["project"],
                    "service": spec["service"],
                    "kind": spec["kind"],
                    "phase": spec.get("phase", "production"),
                }
                rows.extend(
                    [
                        sample("fleet_check_success", int(ok), **labels),
                        sample("fleet_check_http_status", status, **labels),
                        sample("fleet_check_duration_seconds", duration, **labels),
                        sample("fleet_check_timestamp_seconds", time.time(), **labels),
                    ]
                )
                for capability, enabled in capabilities.items():
                    rows.append(
                        sample(
                            "fleet_capability_enabled",
                            enabled,
                            project=spec["project"],
                            capability=capability,
                        )
                    )
        for service in self.inventory["launchd"]:
            result = subprocess.run(
                ["/bin/launchctl", "print", f"gui/{os.getuid()}/{service['label']}"],
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            )
            running = result.returncode == 0 and bool(
                re.search(r"\bstate = running\b", result.stdout)
            )
            labels = {
                "project": service["project"],
                "service": service["service"],
                "kind": "process",
                "phase": "production",
            }
            rows.append(sample("fleet_check_success", int(running), **labels))
        for dep in self.inventory["dependencies"]:
            rows.append(sample("fleet_dependency_info", 1, **dep))
        return rows

    def graphql(self, query):
        # cf has no general GraphQL command. Reuse its private refreshed OAuth grant.
        token = json.loads(self.cf_credentials.read_text())["oauth_token"]
        value = request_json(
            "https://api.cloudflare.com/client/v4/graphql",
            {"query": query},
            {"Authorization": "Bearer " + token},
        )
        if value.get("errors"):
            raise ValueError("Cloudflare GraphQL rejected the query")
        return value["data"]["viewer"]

    def cloudflare(self):
        rows = []
        try:
            cf_json("zones", "list")  # Also refresh the existing CLI OAuth session.
        except (OSError, ValueError, subprocess.SubprocessError):
            for site in self.inventory["sites"]:
                self.integration(rows, site["project"], "cloudflare", True, False)
            self.integration(rows, "fleet", "workers", True, False)
            return rows
        yesterday = (dt.datetime.now(dt.UTC) - dt.timedelta(days=1)).date().isoformat()
        for site in self.inventory["sites"]:
            try:
                q = (
                    "{viewer{zones(filter:{zoneTag:"
                    + json.dumps(site["zone_id"])
                    + "}){httpRequests1dGroups(limit:1,filter:{date:"
                    + json.dumps(yesterday)
                    + "}){sum{requests pageViews bytes cachedRequests threats responseStatusMap{edgeResponseStatus requests}}uniq{uniques}}}}}"
                )
                zones = self.graphql(q)["zones"]
                if len(zones) != 1:
                    raise ValueError("expected exactly one accessible zone")
                groups = zones[0]["httpRequests1dGroups"]
                self.integration(
                    rows, site["project"], "cloudflare", True, True, bool(groups)
                )
                if groups:
                    labels = {"project": site["project"], "period": "yesterday_utc"}
                    for key, name in {
                        "requests": "requests",
                        "pageViews": "page_views",
                        "bytes": "response_bytes",
                        "cachedRequests": "cached_requests",
                        "threats": "threats",
                    }.items():
                        rows.append(
                            sample(
                                "fleet_cloudflare_" + name,
                                groups[0]["sum"][key],
                                **labels,
                            )
                        )
                    rows.append(
                        sample(
                            "fleet_cloudflare_zone_uniques",
                            groups[0]["uniq"]["uniques"],
                            **labels,
                        )
                    )
                    for status in groups[0]["sum"].get("responseStatusMap", []):
                        rows.append(
                            sample(
                                "fleet_cloudflare_status_requests",
                                status["requests"],
                                status=status["edgeResponseStatus"],
                                **labels,
                            )
                        )
            except (OSError, ValueError, KeyError, IndexError):
                self.integration(rows, site["project"], "cloudflare", True, False)
        try:
            end = dt.datetime.now(dt.UTC).replace(microsecond=0)
            start = end - dt.timedelta(minutes=5)
            stamp = lambda d: json.dumps(d.isoformat().replace("+00:00", "Z"))
            q = (
                "{viewer{accounts(filter:{accountTag:"
                + json.dumps(ACCOUNT)
                + "}){workersInvocationsAdaptive(limit:500,filter:{datetime_geq:"
                + stamp(start)
                + ",datetime_leq:"
                + stamp(end)
                + "}){dimensions{scriptName status}sum{requests errors}}}}}"
            )
            accounts = self.graphql(q)["accounts"]
            if len(accounts) != 1:
                raise ValueError("expected exactly one accessible account")
            groups = accounts[0]["workersInvocationsAdaptive"]
            totals = {}
            for group in groups:
                name = group["dimensions"]["scriptName"]
                entry = totals.setdefault(name, {"requests": 0, "errors": 0})
                for key in entry:
                    entry[key] += group["sum"][key]
            for worker in self.inventory["workers"]:
                if worker["name"] in totals:
                    for key, value in totals[worker["name"]].items():
                        rows.append(
                            sample(
                                "fleet_worker_" + key + "_window",
                                value,
                                project=worker["project"],
                                service=worker["name"],
                            )
                        )
            self.integration(rows, "fleet", "workers", True, True, bool(groups))
        except (OSError, ValueError, KeyError, IndexError):
            self.integration(rows, "fleet", "workers", True, False)
        for database in self.inventory["databases"]:
            ok = False
            try:
                value = cf_json(
                    "d1", "query", database["id"], "--sql", "SELECT 1 AS ok"
                )
                ok = bool(value) and all(
                    v.get("success") and v.get("results") == [{"ok": 1}] for v in value
                )
            except (OSError, ValueError, subprocess.SubprocessError):
                pass
            rows.append(
                sample(
                    "fleet_check_success",
                    int(ok),
                    project=database["project"],
                    service=database["name"],
                    kind="readiness-query",
                    phase="production",
                )
            )
        try:
            tunnels = {t["name"]: t for t in cf_json("tunnels", "list")}
            for tunnel in self.inventory["tunnels"]:
                rows.append(
                    sample(
                        "fleet_check_success",
                        int(tunnels.get(tunnel["name"], {}).get("status") == "healthy"),
                        project=tunnel["project"],
                        service=tunnel["name"],
                        kind="tunnel",
                        phase="production",
                    )
                )
        except (OSError, ValueError, subprocess.SubprocessError):
            for tunnel in self.inventory["tunnels"]:
                rows.append(
                    sample(
                        "fleet_check_success",
                        0,
                        project=tunnel["project"],
                        service=tunnel["name"],
                        kind="tunnel",
                        phase="production",
                    )
                )
        return rows

    def business_cloudflare(self, site):
        rows = []
        project = site["project"]
        day = (dt.datetime.now(dt.UTC) - dt.timedelta(days=1)).date().isoformat()
        prefix = "{viewer{zones(filter:{zoneTag:" + json.dumps(site["zone_id"]) + "}){"
        configured = self.cf_credentials.is_file()
        if project != "llms-explorer":
            try:
                settings = cf_json(
                    "email-routing", "settings", "get", "--zone", site["zone_id"]
                )
                catchall = cf_json(
                    "email-routing",
                    "rules",
                    "catch-all",
                    "get",
                    "--zone",
                    site["zone_id"],
                )
                recipient_file = self.state / "mail-destination"
                if recipient_file.is_file():
                    recipient = recipient_file.read_text().strip().casefold()
                    expected = any(
                        a["type"] == "forward"
                        and {address.casefold() for address in a.get("value", [])}
                        == {recipient}
                        for a in catchall["actions"]
                    )
                    rows.append(
                        sample(
                            "fleet_mail_forwarding_verified",
                            int(
                                settings.get("enabled") is True
                                and catchall.get("enabled") is True
                                and expected
                            ),
                            project=project,
                        )
                    )
                self.integration(rows, project, "mail-routing", configured, True)
            except (OSError, ValueError, KeyError, subprocess.SubprocessError):
                self.integration(rows, project, "mail-routing", configured, False)
            try:
                dataset = "emailRoutingAdaptiveGroups"
                result = self.graphql(
                    prefix
                    + dataset
                    + "(limit:100,filter:{date:"
                    + json.dumps(day)
                    + ',eventType:"incoming"}){count dimensions{status}}}}}'
                )["zones"]
                groups = result[0][dataset]
                if len(result) != 1 or len(groups) >= 100:
                    raise ValueError("incomplete email analytics response")
                for item in groups:
                    rows.append(
                        sample(
                            "fleet_mail_incoming_window",
                            item["count"],
                            project=project,
                            outcome=item["dimensions"]["status"],
                            period="yesterday_utc",
                        )
                    )
                if not groups:
                    rows.append(
                        sample(
                            "fleet_mail_incoming_window",
                            0,
                            project=project,
                            outcome="none",
                            period="yesterday_utc",
                        )
                    )
                self.integration(
                    rows, project, "mail-activity", configured, True, bool(groups)
                )
            except (OSError, ValueError, KeyError, IndexError):
                self.integration(rows, project, "mail-activity", configured, False)
        else:
            for source in ("mail-routing", "mail-activity"):
                self.integration(rows, project, source, False, False)

        try:
            levels = cf_json(
                "security-insights",
                "count",
                "by-severity",
                "--zone",
                site["zone_id"],
                "--dismissed",
                "false",
            )
            values = {
                level["value"].casefold(): int(level["count"]) for level in levels
            }
            for severity in sorted(
                values.keys() | {"critical", "high", "moderate", "low"}
            ):
                rows.append(
                    sample(
                        "fleet_cloudflare_security_findings",
                        values.get(severity, 0),
                        project=project,
                        severity=severity,
                    )
                )
            self.integration(rows, project, "cloudflare-findings", configured, True)
        except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
            self.integration(rows, project, "cloudflare-findings", configured, False)

        try:
            dataset = "firewallEventsAdaptiveGroups"
            result = self.graphql(
                prefix
                + dataset
                + "(limit:100,filter:{date:"
                + json.dumps(day)
                + "}){count dimensions{action}}}}}"
            )["zones"]
            groups = result[0][dataset]
            if len(result) != 1 or len(groups) >= 100:
                raise ValueError("incomplete firewall analytics response")
            for item in groups:
                rows.append(
                    sample(
                        "fleet_cloudflare_firewall_events",
                        item["count"],
                        project=project,
                        action=item["dimensions"]["action"],
                        period="yesterday_utc",
                    )
                )
            if not groups:
                rows.append(
                    sample(
                        "fleet_cloudflare_firewall_events",
                        0,
                        project=project,
                        action="none",
                        period="yesterday_utc",
                    )
                )
            self.integration(
                rows, project, "cloudflare-firewall", configured, True, bool(groups)
            )
        except (OSError, ValueError, KeyError, IndexError):
            self.integration(rows, project, "cloudflare-firewall", configured, False)
        return rows

    def stripe(self, project, config):
        rows = []
        if config is None:
            self.integration(rows, project, "stripe-live", False, False)
            return rows
        try:
            # Only a specific, independently verified single-site settlement account can be mapped.
            key = Path(config["key_file"]).read_text().strip()
            if not key.startswith("rk_live_"):
                raise ValueError("a restricted live Stripe key is required")
            headers = {"Authorization": "Bearer " + key}
            origin = "https://api.stripe.com/v1/"
            if (
                request_json(origin + "account", headers=headers)["id"]
                != config["account_id"]
            ):
                raise ValueError("Stripe account does not match the expected site")
            now = int(time.time())
            cutoff = now - 1800
            totals = {}
            for route, start in (
                ("events", cutoff),
                ("balance_transactions", now - 86400),
            ):
                params = {"created[gte]": start, "created[lte]": now, "limit": 100}
                entries = []
                for _ in range(5):
                    response = request_json(
                        origin + route + "?" + urllib.parse.urlencode(params),
                        headers=headers,
                    )
                    page = response["data"]
                    entries.extend(page)
                    if not response["has_more"]:
                        break
                    params["starting_after"] = page[-1]["id"]
                else:
                    raise ValueError("incomplete Stripe reporting window")
                if route == "events":
                    if not all(event["livemode"] is True for event in entries):
                        raise ValueError("Stripe returned a test event")
                    groups = {
                        "purchases": {"payment_intent.succeeded"},
                        "refunds": {"charge.refunded"},
                        "disputes": {"charge.dispute.created"},
                        "payouts": {"payout.paid", "payout.failed", "payout.canceled"},
                        "account_changes": {
                            "account.updated",
                            "capability.updated",
                            "account.external_account.created",
                            "account.external_account.updated",
                            "account.external_account.deleted",
                        },
                    }
                    for group, event_types in groups.items():
                        rows.append(
                            sample(
                                "fleet_stripe_events_recent",
                                sum(event["type"] in event_types for event in entries),
                                project=project,
                                kind=group,
                            )
                        )
                else:
                    recent = 0
                    for entry in entries:
                        currency = entry["currency"]
                        if not re.fullmatch(r"[a-z]{3}", currency):
                            raise ValueError("unexpected Stripe currency")
                        totals[currency] = totals.get(currency, 0) + int(entry["net"])
                        recent += int(
                            entry["created"] >= cutoff and int(entry["net"]) != 0
                        )
                    rows.append(
                        sample(
                            "fleet_stripe_balance_movements_recent",
                            recent,
                            project=project,
                        )
                    )
                    for currency, total in totals.items():
                        rows.append(
                            sample(
                                "fleet_stripe_net_movement_minor",
                                total,
                                project=project,
                                currency=currency,
                            )
                        )
        except (OSError, ValueError, KeyError, IndexError, TypeError):
            rows = []
            self.integration(rows, project, "stripe-live", True, False)
        else:
            self.integration(rows, project, "stripe-live", True, True, True)
        return rows

    def commerce(self, project):
        rows = []
        if project == "netdnsmonitor":
            database = next(
                d for d in self.inventory["databases"] if d["project"] == project
            )
            try:
                result = cf_json(
                    "d1",
                    "query",
                    database["id"],
                    "--sql",
                    "SELECT provider, COUNT(*) AS purchases, SUM(cents) AS gross "
                    "FROM orders WHERE state = 'paid' AND created_at >= unixepoch() - 86400 "
                    "GROUP BY provider",
                )
                if len(result) != 1 or result[0]["success"] is not True:
                    raise ValueError("Net DNS Monitor orders query failed")
                values = {r["provider"]: r for r in result[0]["results"]}
                for provider in ("stripe", "paypal", "venmo"):
                    entry = values.get(provider, {"purchases": 0, "gross": 0})
                    for key, metric in (
                        ("purchases", "count"),
                        ("gross", "gross_usd_cents"),
                    ):
                        rows.append(
                            sample(
                                "fleet_netdns_orders_" + metric,
                                entry[key],
                                project=project,
                                provider=provider,
                            )
                        )
            except (
                OSError,
                ValueError,
                KeyError,
                IndexError,
                subprocess.SubprocessError,
            ):
                self.integration(rows, project, "commerce-ledger", True, False)
            else:
                self.integration(rows, project, "commerce-ledger", True, True)
        if project == "morelube":
            config = self.state / "morelube-db-path"
            if not config.is_file():
                self.integration(rows, project, "commerce-ledger", False, False)
                return rows
            try:
                path = Path(config.read_text().strip()).resolve(strict=True)
                now = dt.datetime.now(dt.UTC)
                iso = lambda t: t.isoformat(timespec="milliseconds").replace(
                    "+00:00", "Z"
                )
                with closing(
                    sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=3)
                ) as db:
                    values = db.execute(
                        "SELECT COUNT(*), COALESCE(SUM(p.amount_cents), 0),"
                        "COUNT(CASE WHEN p.settled_at >= ? THEN 1 END) "
                        "FROM payments p JOIN orders o ON o.id = p.order_id "
                        "WHERE o.is_test = 0 AND p.currency = 'USD' AND p.settled_at >= ? AND p.settled_at <= ?",
                        (
                            iso(now - dt.timedelta(minutes=30)),
                            iso(now - dt.timedelta(days=1)),
                            iso(now),
                        ),
                    ).fetchone()
                for name, value in zip(
                    ("purchases_day", "gross_usd_cents_day", "purchases_recent"),
                    values,
                    strict=True,
                ):
                    rows.append(
                        sample("fleet_morelube_" + name, value, project=project)
                    )
            except (OSError, sqlite3.Error, ValueError):
                self.integration(rows, project, "commerce-ledger", True, False)
            else:
                self.integration(rows, project, "commerce-ledger", True, True)
        return rows

    def public_seller(self, site):
        rows = []
        project = site["project"]
        try:
            state = google_seller_file("https://" + site["domain"] + "/ads.txt")
        except (OSError, ValueError):
            self.integration(rows, project, "public-ads-txt", True, False)
        else:
            rows.append(
                sample("fleet_google_seller_file_status", state, project=project)
            )
            self.integration(rows, project, "public-ads-txt", True, True, state != 0)
        return rows

    def business(self):
        sites = [
            s
            for s in self.inventory["sites"]
            if s["project"] in self.inventory["business_projects"]
        ]
        path = self.state / "stripe-accounts.json"
        accounts = json.loads(path.read_text()) if path.is_file() else {}
        # Do not attribute a shared Stripe balance to multiple domains.
        if len({binding["account_id"] for binding in accounts.values()}) != len(
            accounts
        ):
            raise ValueError(
                "Stripe site mappings must use distinct settlement accounts"
            )
        rows = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            pending = [pool.submit(self.business_cloudflare, site) for site in sites]
            pending.extend(
                pool.submit(self.stripe, site["project"], accounts.get(site["project"]))
                for site in sites
            )
            pending.extend(
                pool.submit(self.commerce, project)
                for project in ("netdnsmonitor", "morelube")
            )
            pending.extend(pool.submit(self.public_seller, site) for site in sites)
            for result in pending:
                rows.extend(result.result())
        return rows

    def google(self):
        rows = []
        for site in self.inventory["sites"]:
            property_id = site.get("ga4_property")
            if not property_id:
                self.integration(rows, site["project"], "ga4", False, False)
                continue
            try:
                token = self.google_token.get(
                    "https://www.googleapis.com/auth/analytics.readonly"
                )
                metrics = {
                    "activeUsers": "active_users",
                    "sessions": "sessions",
                    "screenPageViews": "screen_page_views",
                }
                result = request_json(
                    f"https://analyticsdata.googleapis.com/v1beta/properties/{property_id}:runReport",
                    {
                        "dateRanges": [
                            {"startDate": "yesterday", "endDate": "yesterday"}
                        ],
                        "metrics": [{"name": m} for m in metrics],
                        "dimensionFilter": {
                            "filter": {
                                "fieldName": "hostName",
                                "inListFilter": {
                                    "values": [site["domain"], "www." + site["domain"]]
                                },
                            }
                        },
                        "limit": 1,
                        "returnPropertyQuota": True,
                    },
                    {"Authorization": "Bearer " + token},
                )
                values = result.get("rows", [])
                self.integration(rows, site["project"], "ga4", True, True, bool(values))
                if values:
                    for header, value in zip(
                        result["metricHeaders"], values[0]["metricValues"], strict=True
                    ):
                        rows.append(
                            sample(
                                "fleet_ga4_" + metrics[header["name"]],
                                value["value"],
                                project=site["project"],
                                period="yesterday",
                            )
                        )
            except (OSError, ValueError, KeyError, PermissionError):
                self.integration(rows, site["project"], "ga4", True, False)
        return rows

    def ads(self):
        rows = []
        configured = self.ads_token.path.is_file() and bool(
            os.environ.get("ADSENSE_ACCOUNT")
        )
        if configured:
            try:
                token = self.ads_token.get(
                    "https://www.googleapis.com/auth/adsense.readonly"
                )
                account = os.environ["ADSENSE_ACCOUNT"]
                if not re.fullmatch(r"accounts/pub-[0-9]+", account):
                    raise ValueError("invalid AdSense account resource")
                headers = {"Authorization": "Bearer " + token}
                try:
                    body = request_json(
                        f"https://adsense.googleapis.com/v2/{account}/sites?pageSize=10000",
                        headers=headers,
                    )
                    if body.get("nextPageToken"):
                        raise ValueError("incomplete AdSense sites response")
                    registered = {
                        site["domain"]: site for site in body.get("sites", [])
                    }
                except (OSError, ValueError, KeyError):
                    self.integration(rows, "fleet", "adsense-sites", True, False)
                else:
                    states = {
                        "STATE_UNSPECIFIED": 0,
                        "REQUIRES_REVIEW": 1,
                        "GETTING_READY": 2,
                        "READY": 3,
                        "NEEDS_ATTENTION": 4,
                    }
                    for site in self.inventory["sites"]:
                        registration = registered.get(site["domain"])
                        rows.append(
                            sample(
                                "fleet_adsense_site_status",
                                states.get(registration.get("state"), 0)
                                if registration
                                else 5,
                                project=site["project"],
                            )
                        )
                    self.integration(
                        rows, "fleet", "adsense-sites", True, True, bool(registered)
                    )
                params = urllib.parse.urlencode(
                    {
                        "dateRange": "YESTERDAY",
                        "metrics": "ESTIMATED_EARNINGS",
                        "dimensions": "DOMAIN_NAME",
                        "currencyCode": "USD",
                        "limit": 1000,
                    }
                )
                report = request_json(
                    f"https://adsense.googleapis.com/v2/{account}/reports:generate?{params}",
                    headers={"Authorization": "Bearer " + token},
                )
                data = report.get("rows", [])
                if int(report.get("totalMatchedRows", len(data))) > len(data):
                    raise ValueError("truncated AdSense report")
                for row in data:
                    domain, earnings = [cell["value"] for cell in row["cells"]]
                    for site in self.inventory["sites"]:
                        if domain.removeprefix("www.") == site["domain"]:
                            rows.append(
                                sample(
                                    "fleet_ads_estimated_earnings",
                                    Decimal(earnings),
                                    project=site["project"],
                                    provider="adsense",
                                    currency="USD",
                                    period="yesterday",
                                )
                            )
                self.integration(rows, "fleet", "adsense", True, True, bool(data))
            except (OSError, ValueError, KeyError, PermissionError):
                self.integration(rows, "fleet", "adsense", True, False)
                if not any(
                    labels.get("source") == "adsense-sites" for _, _, labels in rows
                ):
                    self.integration(rows, "fleet", "adsense-sites", True, False)
        else:
            self.integration(rows, "fleet", "adsense", False, False)
            self.integration(rows, "fleet", "adsense-sites", False, False)
        self.integration(rows, "fleet", "ezmob", False, False)
        return rows

    def watchdog(self):
        rows = []
        path = Path(
            os.environ.get(
                "WATCHDOG_TOKEN_FILE", str(self.state.parent / "watchdog-token")
            )
        )
        configured = path.is_file() and bool(self.inventory.get("watchdog_url"))
        if not configured:
            self.integration(rows, "fleet", "watchdog", False, False)
            return rows
        try:
            result = request_json(
                self.inventory["watchdog_url"],
                headers={"Authorization": "Bearer " + path.read_text().strip()},
            )
            checks = result["checks"]
            by_name = {check["name"]: check for check in checks}
            for target in self.inventory.get("watchdog_targets", []):
                labels = {"project": target["name"], "phase": target["phase"]}
                check = by_name.get(target["name"])
                rows.append(
                    sample(
                        "fleet_watchdog_checked_timestamp_seconds",
                        check["checked_at"] if check else 0,
                        **labels,
                    )
                )
                if check:
                    for key, metric in {
                        "success": "success",
                        "status": "http_status",
                        "duration": "duration_seconds",
                    }.items():
                        rows.append(
                            sample("fleet_watchdog_" + metric, check[key], **labels)
                        )
            self.integration(rows, "fleet", "watchdog", True, True, bool(checks))
        except (OSError, ValueError, KeyError, TypeError):
            self.integration(rows, "fleet", "watchdog", True, False)
        return rows

    def logs(self):
        ok = False
        try:
            ok = self.spool.push(os.environ.get("LOKI_URL", "http://127.0.0.1:3140"))
        except (OSError, ValueError):
            pass
        pending, dropped = self.spool.stats()
        return [
            sample("fleet_logs_last_push_success", int(ok)),
            sample("fleet_logs_pending_events", pending),
            sample("fleet_logs_dropped_events", dropped),
        ]

    def loop(self, name, callback):
        while not self.stop.is_set():
            start = time.monotonic()
            event = {
                "timestamp": time.time(),
                "severity": "info",
                "service_name": "fleet-collector",
                "service_version": VERSION,
                "project": "fleet",
                "environment": "production",
                "event": "collector.cycle",
                "collector": name,
                "outcome": "success",
            }
            try:
                rows = callback()
                with self.lock:
                    self.snapshots[name] = rows
                    self.cycles[name] = time.time()
            except Exception as error:  # noqa: BLE001 - keep collection threads alive; publish failure and stale-cycle signals
                # Never serialize error text: upstream errors can contain credentials.
                event.update(
                    severity="error", outcome="failure", error_type=type(error).__name__
                )
                with self.lock:
                    self.snapshots[name] = []
            event["duration_ms"] = round((time.monotonic() - start) * 1000)
            self.logger.info(json.dumps(validate_log(event)))
            if name != "logs":
                self.spool.append(event)
            self.stop.wait(max(1, self.intervals[name] - (time.monotonic() - start)))

    def metrics(self):
        with self.lock:
            rows = [row for snapshot in self.snapshots.values() for row in snapshot]
            expected = [
                {
                    "project": s["project"],
                    "service": s["service"],
                    "kind": s["kind"],
                    "phase": s.get("phase", "production"),
                }
                for s in self.inventory["checks"]
            ]
            expected.extend(
                {
                    "project": s["project"],
                    "service": s["service"],
                    "kind": "process",
                    "phase": "production",
                }
                for s in self.inventory["launchd"]
            )
            expected.extend(
                {
                    "project": s["project"],
                    "service": s["name"],
                    "kind": "readiness-query",
                    "phase": "production",
                }
                for s in self.inventory["databases"]
            )
            expected.extend(
                {
                    "project": s["project"],
                    "service": s["name"],
                    "kind": "tunnel",
                    "phase": "production",
                }
                for s in self.inventory["tunnels"]
            )
            rows.extend(
                sample("fleet_check_expected", 1, **labels) for labels in expected
            )
            for name, interval in self.intervals.items():
                rows.append(
                    sample("fleet_collector_interval_seconds", interval, collector=name)
                )
                if name in self.cycles:
                    rows.append(
                        sample(
                            "fleet_collector_cycle_timestamp_seconds",
                            self.cycles[name],
                            collector=name,
                        )
                    )
        return render_metrics(rows)

    def ready(self):
        with self.lock:
            return time.time() - self.cycles.get("fast", 0) < 180


def handler_for(collector):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/metrics":
                status, body, content = (
                    200,
                    collector.metrics(),
                    "text/plain; version=0.0.4; charset=utf-8",
                )
            elif self.path in {"/health", "/ready"}:
                ok = self.path == "/health" or collector.ready()
                status, body, content = (
                    (200 if ok else 503),
                    json.dumps(
                        {"status": "ok" if ok else "stale", "version": VERSION}
                    ).encode(),
                    "application/json",
                )
            else:
                status, body, content = (
                    404,
                    b'{"error":"not_found"}',
                    "application/json",
                )
            self.send_response(status)
            self.send_header("Content-Type", content)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_):
            pass

    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--state",
        type=Path,
        default=Path.home() / ".local/share/llmsx-observability/state",
    )
    parser.add_argument("--inventory", type=Path, default=ROOT / "inventory.json")
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9321)
    args = parser.parse_args()
    os.umask(0o077)
    collector = Collector(json.loads(args.inventory.read_text()), args.state)
    for name in collector.intervals:
        threading.Thread(
            target=collector.loop,
            args=(name, getattr(collector, name)),
            daemon=True,
            name=name,
        ).start()
    server = ThreadingHTTPServer((args.bind, args.port), handler_for(collector))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        collector.stop.set()
        server.server_close()


if __name__ == "__main__":
    main()
