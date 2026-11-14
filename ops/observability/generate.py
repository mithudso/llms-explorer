#!/usr/bin/env python3
"""Generate Grafana, blackbox and Prometheus configuration from the fleet inventory."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def write(path, data):
    dest = ROOT / path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(data, indent=2) + "\n")


def generate():
    inventory = json.loads((ROOT / "inventory.json").read_text())
    write(
        "blackbox.yml",
        {
            "modules": {
                "website": {
                    "prober": "http",
                    "timeout": "12s",
                    "http": {
                        "preferred_ip_protocol": "ip4",
                        "follow_redirects": True,
                        "fail_if_not_ssl": True,
                        "fail_if_body_not_matches_regexp": ["(?i)<html(?:\\s|>)"],
                        "valid_status_codes": [200],
                        "headers": {
                            "User-Agent": "LLMSX-Operations/1.0 (+https://ops.llmsx.org)"
                        },
                        # A 200 login/challenge page is not a working public website.
                        "fail_if_body_matches_regexp": [
                            "(?i)cloudflare access",
                            "(?i)<title>[^<]*(sign in|just a moment)",
                        ],
                    },
                }
            }
        },
    )
    write(
        "prometheus/prometheus.yml",
        {
            "global": {
                "scrape_interval": "30s",
                "evaluation_interval": "30s",
                "external_labels": {"monitor": "llmsx-fleet"},
            },
            "rule_files": ["/etc/prometheus/alerts.yml"],
            "scrape_configs": [
                {
                    "job_name": "prometheus",
                    "static_configs": [{"targets": ["localhost:9090"]}],
                },
                {
                    "job_name": "fleet",
                    "scrape_interval": "30s",
                    "static_configs": [{"targets": ["host.docker.internal:9321"]}],
                },
                {"job_name": "loki", "static_configs": [{"targets": ["loki:3100"]}]},
                {
                    "job_name": "websites",
                    "metrics_path": "/probe",
                    "scrape_interval": "60s",
                    "scrape_timeout": "15s",
                    "params": {"module": ["website"]},
                    "static_configs": [
                        {
                            "targets": ["https://" + s["domain"] + "/"],
                            "labels": {"project": s["project"], "phase": s["phase"]},
                        }
                        for s in inventory["sites"]
                    ],
                    "relabel_configs": [
                        {
                            "source_labels": ["__address__"],
                            "target_label": "__param_target",
                        },
                        {
                            "source_labels": ["__param_target"],
                            "target_label": "instance",
                        },
                        {"target_label": "__address__", "replacement": "blackbox:9115"},
                    ],
                },
            ],
        },
    )
    rules = [
        (
            "OffhostWatchdogFailure",
            'fleet_watchdog_success{phase="production"} == 0',
            "3m",
            "critical",
            "Independent HTTP monitor reports a production outage",
        ),
        (
            "OffhostWatchdogStale",
            "time() - fleet_watchdog_checked_timestamp_seconds > 180",
            "3m",
            "warning",
            "Independent monitoring history stopped updating",
        ),
        (
            "WebsiteUnavailable",
            'probe_success{job="websites",phase="production"} == 0',
            "3m",
            "critical",
            "Public website is unavailable or returns an access/challenge page",
        ),
        (
            "BackendUnavailable",
            'fleet_check_success{phase="production"} == 0',
            "3m",
            "critical",
            "A backend or origin check failed",
        ),
        (
            "BackendObservationMissing",
            "fleet_check_expected unless on(project, service, kind, phase) fleet_check_success",
            "3m",
            "warning",
            "An expected backend has no observation",
        ),
        (
            "MonitorScrapeFailed",
            "up == 0",
            "2m",
            "critical",
            "Monitoring cannot scrape a configured target",
        ),
        (
            "FleetCollectorMissing",
            'absent(fleet_collector_cycle_timestamp_seconds{collector="fast"})',
            "3m",
            "critical",
            "Fleet collector data is missing",
        ),
        (
            "FleetCollectorStale",
            "time() - fleet_collector_cycle_timestamp_seconds > 2 * fleet_collector_interval_seconds + 120",
            "2m",
            "warning",
            "A collector has stopped updating",
        ),
        (
            "HostDiskLow",
            "fleet_host_disk_free_ratio < 0.15",
            "10m",
            "warning",
            "Production host has less than 15 percent free disk",
        ),
        (
            "HostMemoryHigh",
            "fleet_host_memory_used_ratio > 0.90",
            "10m",
            "warning",
            "Production host memory exceeds 90 percent",
        ),
        (
            "TelemetryIntegrationFailed",
            "fleet_integration_configured == 1 and on(project, source) fleet_integration_success == 0",
            "15m",
            "warning",
            "A configured telemetry integration failed",
        ),
        (
            "TelemetryNotConfigured",
            "fleet_integration_configured == 0",
            "15m",
            "info",
            "A requested telemetry source needs configuration or authorization",
        ),
        (
            "WorkerErrors",
            "fleet_worker_errors_window > 0",
            "5m",
            "warning",
            "A Worker reported errors in its sliding five minute window",
        ),
        (
            "TLSExpirySoon",
            '(probe_ssl_earliest_cert_expiry{job="websites"} - time()) / 86400 < 14',
            "30m",
            "warning",
            "A public TLS certificate expires within fourteen days",
        ),
        (
            "LogsDeliveryFailed",
            "fleet_logs_last_push_success == 0",
            "5m",
            "warning",
            "Central logs have failed delivery",
        ),
    ]
    write(
        "prometheus/alerts.yml",
        {
            "groups": [
                {
                    "name": "fleet",
                    "rules": [
                        {
                            "alert": name,
                            "expr": expr,
                            "for": duration,
                            "labels": {"severity": severity},
                            "annotations": {
                                "summary": summary,
                                "runbook_url": "https://github.com/mithudso/llms-explorer/blob/main/docs/operations/observability.md",
                            },
                        }
                        for name, expr, duration, severity, summary in rules
                    ],
                }
            ]
        },
    )

    panels = []
    y = 0

    def panel(
        title,
        expr=None,
        typ="timeseries",
        width=12,
        height=8,
        text=None,
        unit="short",
        legend="{{project}}",
        description="",
        mappings=None,
    ):
        nonlocal y
        x = (
            0
            if not panels
            or panels[-1]["gridPos"]["x"] + panels[-1]["gridPos"]["w"] + width > 24
            else panels[-1]["gridPos"]["x"] + panels[-1]["gridPos"]["w"]
        )
        if panels and x == 0:
            y = max(p["gridPos"]["y"] + p["gridPos"]["h"] for p in panels)
        p = {
            "id": len(panels) + 1,
            "title": title,
            "description": description,
            "type": typ,
            "gridPos": {"x": x, "y": y, "w": width, "h": height},
            "fieldConfig": {
                "defaults": {
                    "unit": unit,
                    "noValue": "Unknown / no data",
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "red", "value": None},
                            {"color": "green", "value": 1},
                        ],
                    },
                },
                "overrides": [],
            },
            "options": {
                "legend": {"displayMode": "table", "placement": "bottom"},
                "tooltip": {"mode": "multi"},
            },
        }
        if expr:
            p["datasource"] = {"type": "prometheus", "uid": "fleet-prometheus"}
            p["targets"] = [
                {
                    "refId": "A",
                    "expr": expr,
                    "legendFormat": legend,
                    "instant": typ in ("table", "stat"),
                    "format": "table" if typ == "table" else "time_series",
                }
            ]
        if typ == "text":
            p["options"] = {"mode": "markdown", "content": text}
        if typ == "stat":
            p["options"] = {
                "reduceOptions": {"calcs": ["lastNotNull"], "values": False},
                "colorMode": "value",
                "graphMode": "none",
            }
        if mappings:
            p["fieldConfig"]["defaults"]["mappings"] = [
                {"type": "value", "options": mappings}
            ]
        panels.append(p)

    states = {
        "0": {"text": "FAIL / unavailable", "color": "red"},
        "1": {"text": "PASS", "color": "green"},
    }
    panel(
        "Fleet operations",
        typ="text",
        width=24,
        height=4,
        text="## Websites · backends · traffic · revenue · logs\nPrivate operations dashboard. Public HTTP checks run every minute. Host and backend checks run every minute. Provider statistics refresh every 5–15 minutes. **Unknown, missing permissions and prelaunch services remain visible.** A configured dependency is not a successful customer journey. [Operating standards and runbooks](https://github.com/mithudso/llms-explorer/blob/main/docs/operations/observability.md)",
    )
    panel(
        "Public sites responding / 6",
        'sum(probe_success{job="websites"})',
        "stat",
        6,
        4,
    )
    panel(
        "Firing alerts", 'count(ALERTS{alertstate="firing"}) or vector(0)', "stat", 6, 4
    )
    panel(
        "Backend checks failing",
        "count(fleet_check_success == 0) or vector(0)",
        "stat",
        6,
        4,
    )
    panel(
        "Known coverage gaps",
        'count(fleet_dependency_info{coverage=~"gap-.*"})',
        "stat",
        6,
        4,
    )
    panel(
        "Missing backend observations",
        "count(fleet_check_expected unless on(project, service, kind, phase) fleet_check_success) or vector(0)",
        "stat",
        12,
        4,
    )
    panel("Monitoring scrape failures", "count(up == 0) or vector(0)", "stat", 12, 4)
    panel(
        "Independent off-host checks",
        "fleet_watchdog_success",
        "table",
        12,
        7,
        mappings=states,
        description="A Cloudflare cron probes nine public and origin endpoints independently of the Mac. Its D1 history remains available when the Mac is offline. External paging still needs a chosen destination.",
    )
    panel(
        "Independent check age",
        "time() - fleet_watchdog_checked_timestamp_seconds",
        "table",
        12,
        7,
        unit="s",
        description="Stale checks are unknown. This is observation age, not response latency.",
    )
    panel(
        "Public website checks",
        'probe_success{job="websites"}',
        "table",
        12,
        8,
        mappings=states,
        description="Unauthenticated checks. Access redirects and challenges fail; prelaunch sites remain listed. These checks do not create accounts, orders or trades.",
    )
    panel(
        "Public response time",
        'probe_duration_seconds{job="websites"}',
        width=12,
        height=8,
        unit="s",
    )
    panel(
        "Observed website availability",
        'probe_success{job="websites"}',
        "state-timeline",
        24,
        7,
        mappings=states,
        description="Only observed samples; gaps are unknown. History starts at installation. Never interpret this as complete 24-hour coverage until a full day has been collected.",
    )
    panel(
        "Backends, database queries, origins and processes",
        "fleet_check_success",
        "table",
        16,
        10,
        mappings=states,
        description="The kind label distinguishes liveness, readiness, configuration, process and read-only journeys. A process/configuration PASS does not prove business functionality.",
    )
    panel(
        "Launch flags (enabled / disabled)",
        "fleet_capability_enabled",
        "table",
        8,
        10,
        mappings={
            "0": {"text": "Disabled", "color": "orange"},
            "1": {"text": "Enabled", "color": "green"},
        },
        description="Flags are configuration, not a payment, trading or other functional test. Disabled launch gates are preserved.",
    )
    panel(
        "Production host CPU",
        "fleet_host_cpu_ratio",
        width=8,
        height=6,
        unit="percentunit",
        legend="{{host}}",
    )
    panel(
        "Production host memory",
        "fleet_host_memory_used_ratio",
        width=8,
        height=6,
        unit="percentunit",
        legend="{{host}}",
    )
    panel(
        "Production host free disk",
        "fleet_host_disk_free_ratio",
        width=8,
        height=6,
        unit="percentunit",
        legend="{{host}}",
    )
    panel(
        "Worker errors / previous 5 minutes",
        "fleet_worker_errors_window",
        width=12,
        height=7,
        legend="{{project}} / {{service}}",
        description="Provider window gauges. Do not apply rate() or sum values over time. Empty provider data remains unknown.",
    )
    panel(
        "Worker requests / previous 5 minutes",
        "fleet_worker_requests_window",
        width=12,
        height=7,
        legend="{{project}} / {{service}}",
    )
    panel(
        "Telemetry connection status",
        "fleet_integration_success",
        "table",
        12,
        9,
        mappings={
            "0": {"text": "Unavailable / unconfigured", "color": "orange"},
            "1": {"text": "Last fetch succeeded", "color": "green"},
        },
    )
    panel(
        "Provider data age",
        "time() - fleet_integration_last_success_timestamp_seconds",
        "table",
        12,
        9,
        unit="s",
        description="Age of last successful acquisition, not the reporting period. Check reporting period and whether data rows exist separately.",
    )
    panel(
        "Google Analytics page views · yesterday",
        'fleet_ga4_screen_page_views{period="yesterday"}',
        "stat",
        8,
        5,
        description="Hostname-filtered GA4 data in the property's reporting timezone. Consent and blockers limit collection. Google and Cloudflare numbers use different definitions.",
    )
    panel(
        "Google Analytics sessions · yesterday",
        'fleet_ga4_sessions{period="yesterday"}',
        "stat",
        8,
        5,
    )
    panel(
        "Google Analytics active users · yesterday",
        'fleet_ga4_active_users{period="yesterday"}',
        "stat",
        8,
        5,
        description="Do not sum distinct users across hostnames/properties.",
    )
    panel(
        "Cloudflare requests · yesterday UTC",
        'fleet_cloudflare_requests{period="yesterday_utc"}',
        "table",
        12,
        7,
        description="All requests, including bots and monitors; not human page views. Empty provider rows are not reported as zero.",
    )
    panel(
        "Cloudflare page views · yesterday UTC",
        'fleet_cloudflare_page_views{period="yesterday_utc"}',
        "table",
        12,
        7,
    )
    panel(
        "Ads revenue",
        typ="text",
        width=24,
        height=4,
        text="### Publisher earnings\nAdSense requires its own read-only OAuth grant; Analytics read access does not include AdSense. Missing earnings are **unknown, not $0**. Amounts are estimated, per provider and currency. They are not finalized payouts. EZMob reporting needs its own authorized export/API. No ad clicks or impressions are generated by these checks.",
    )
    panel(
        "AdSense estimated earnings · yesterday (USD)",
        'fleet_ads_estimated_earnings{period="yesterday",currency="USD"}',
        "stat",
        12,
        5,
        unit="currencyUSD",
    )
    panel(
        "Revenue source authorization",
        'fleet_integration_configured{source=~"adsense|ezmob"}',
        "table",
        12,
        5,
        mappings={
            "0": {"text": "Authorization needed", "color": "orange"},
            "1": {"text": "Configured", "color": "green"},
        },
    )
    panel(
        "Backend coverage and remaining gaps",
        "fleet_dependency_info",
        "table",
        24,
        11,
        description="A complete list of discovered dependencies. gap-* entries need an actual heartbeat, readiness or synthetic journey before functional coverage can be claimed.",
    )
    panel(
        "Central logs",
        typ="logs",
        width=24,
        height=10,
        description="Structured monitoring events are collected now. Application log migration is tracked in coverage. Unreviewed historical application logs are not ingested.",
    )
    panels[-1]["datasource"] = {"type": "loki", "uid": "fleet-loki"}
    panels[-1]["targets"] = [
        {
            "refId": "A",
            "expr": '{service_name="fleet-collector"} | json',
            "queryType": "range",
        }
    ]
    panel(
        "Active alerts",
        'ALERTS{alertstate="firing"}',
        "table",
        24,
        9,
        description="Prometheus rules run locally. External notifications require an explicitly configured destination; an off-host watchdog remains necessary for Mac/network failure.",
    )
    write(
        "grafana/dashboards/fleet.json",
        {
            "uid": "llmsx-fleet",
            "title": "Fleet operations",
            "version": 1,
            "schemaVersion": 41,
            "editable": False,
            "tags": ["operations", "fleet"],
            "timezone": "browser",
            "refresh": "30s",
            "time": {"from": "now-6h", "to": "now"},
            "panels": panels,
        },
    )


if __name__ == "__main__":
    generate()
