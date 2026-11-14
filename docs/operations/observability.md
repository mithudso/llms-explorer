# Fleet observability standard

Version: 1.0.0. Effective: 2026-11-14. Owner: platform operator.

This standard applies to LLMSX, legacy LLMS-Explorer, Oraclebot, That's What She
Said, MoreLube and SKaaS, including their websites, APIs, databases, background
jobs and hosting. The private operating console is https://ops.llmsx.org .
The deployment inventory and conformance register are
`ops/observability/inventory.json`. A listed gap is unfinished work, not coverage.

## Architecture and hosting

Grafana OSS is the console. Prometheus stores metrics and evaluates alerts.
Blackbox Exporter performs HTTPS checks without executing advertising scripts.
Loki stores central logs. A native host collector performs bounded, read-only
JSON checks, database pings and provider reporting, and measures the origin Mac.
The chosen versions were checked against upstream releases on 2026-11-14.
Grafana and Loki use AGPLv3; Prometheus and Blackbox Exporter use Apache 2.0.

Grafana is available through a dedicated Cloudflare Tunnel and hostname.
Anonymous access and registration are disabled. Metrics, Loki ingestion and
collector endpoints bind to loopback. Cloudflare and Google credentials stay
on the host; they are not mounted in Grafana or committed to Git. The installer
creates its own tunnel and LaunchAgents and preserves the existing API and store
tunnels. It installs immutable source releases from a committed revision.

The initial host is the Mac that already serves the LLMSX API and MoreLube.
Docker Desktop and the signed-in user session must stay running. This is a
single-host deployment, not high availability. Mac power/network failure can
take the dashboard down with those origins. The independent Cloudflare watchdog checks the six websites, the dashboard
and two backend readiness endpoints every minute. It retains seven days of
results in its own D1 database. Its metrics/history API requires a private bearer
token. A dedicated Access application scopes the exception to this new Worker;
the existing All Workers policy is preserved. The native collector reads this
independent history and alerts on failures or stale checks.
Offline workstations are not assumed to be production servers.

## Service identity and ownership

Every signal carries `project`, `environment` and `service_name` (or `service`
on legacy monitoring metrics). Use `production`, `staging` or `development` for
environment. Use the project IDs in the inventory. Use a stable service name,
such as `account-api`, `oraclebot-analysis-runtime` or `store`. Deployment logs
and application resource attributes also carry `service_version`, ideally the
full Git revision. OpenTelemetry adapters map these to `service.name`,
`service.version` and `deployment.environment.name` resource attributes.

The inventory must include every origin, public hostname, proxy/tunnel,
database, queue, object store, Durable Object, scheduled job and critical
external API on which a project depends. New services must add their check,
owner, runbook, lifecycle phase and logging plan before launch. Never list a
staging Worker or local development database as a verified production service.

## What a successful check establishes

Keep these measurements distinct:

- **Public HTTP:** HTTPS and expected page content, including intended domain
  redirects. An Access sign-in page, bot challenge, error page or SPA fallback
  is not a successful public website check.
- **Liveness:** the process can answer. It need not contact dependencies.
- **Readiness:** a bounded, read-only query actually reaches each critical
  dependency. A boolean saying a binding exists is configuration only.
- **User journey:** an isolated synthetic user can perform the intended
  operation. It requires dedicated fixtures and cleanup; never perform real
  payments, place trades, submit supplier orders, click ads or join real game
  sessions as a health check.
- **Business capability:** launch flags, credentials and approvals are recorded
  independently. A disabled checkout/trading gate is preserved and clearly
  labeled. It is not an outage and does not prove a transaction works.

Probe public websites every 60 seconds, host/origin/process checks every
60 seconds, provider and D1/tunnel checks every 5 minutes, and Google Analytics
every 15 minutes. Bound HTTP calls to 12 seconds. Record probe success, status,
duration, sample time and the expected inventory. Keep missing checks visible
with the expected-minus-observed alert. Record zero only when actually measured.

Historical availability uses observed intervals only. Display the observation
window and missing intervals. Do not claim a complete 24-hour or 30-day SLO from
a newly installed monitor or interpolate missing samples as healthy.

## Metrics and cardinality

Applications should expose OpenTelemetry or Prometheus metrics. Use seconds,
bytes and monotonically increasing counters with `_total` suffixes. HTTP
instrumentation should supply request counts, duration histograms and in-flight
requests. Use route templates; never label with user IDs, raw URLs, query
strings, request/trace IDs, wallet addresses or exception messages. Limit labels
to project, environment, service, normalized route, method, status class and a
small documented set of operation/error codes. Set explicit histogram buckets
before measuring latency SLOs.

Monitor CPU, available memory, disk capacity, process state, connection pools,
database latency/errors, queue depth/oldest-item age, job last success and
duration, replication where applicable, TLS expiry and telemetry freshness.
Scheduled jobs must emit start, completion, failure and last-success signals;
alert after two missed expected intervals plus the normal execution allowance.
Never infer job success solely from a live scheduler or a successful process exit.

Cloudflare's request totals include bots and monitors. Google Analytics reflects
consent, blockers and its own session/user definitions. Do not add these sources
together or sum distinct users across properties. Provider date-window totals
are gauges, not counters. Worker request/error metrics describe a sliding
five-minute window; do not apply `rate()` or add overlapping windows.

## Traffic and advertising revenue

Google Analytics uses hostname-filtered GA4 reports for the previous calendar
day in the property's timezone. Cloudflare uses the previous complete UTC day.
Show the period, source, last acquisition time, authorization state and whether
the provider returned any rows. Empty rows remain unknown in this dashboard.
This can understate a true zero; it prevents an access/data gap appearing as
measured zero. GA4 is presently configured only for the LLMSX/legacy property;
the other projects need property mapping and authorized access.

AdSense earnings require a separate `adsense.readonly` OAuth grant and an
`accounts/pub-...` account resource. Set `ADSENSE_CREDENTIALS_FILE` and
`ADSENSE_ACCOUNT` in the collector's private LaunchAgent environment. The
default Analytics-only grant cannot read earnings. Reports are hostname scoped,
per provider and currency. Estimated earnings are not finalized payouts.
Preserve original decimal amounts or integer micros; do not perform financial
arithmetic in binary floating point. Prometheus values are visualization only.
EZMob remains unconnected until an authorized provider API/export is available.
Do not treat an installed ad script, approved seller file or GA4 zero as proof
of AdSense approval, ad fill or earnings.

## Structured logging and central collection

The portable contract is `ops/observability/logging.schema.json`. Emit one UTF-8
JSON object per line to stdout. `timestamp` is UTC Unix seconds with subsecond
precision. Require `severity`, `project`, `environment`, `service_name`,
`service_version` and a stable coded `event`. Use `debug`, `info`, `warn`,
`error` or `fatal`. Use `error` when an operation failed, `warn` when it
recovered or needs attention, and `info` for state changes and job receipts.
Use structured, bounded error codes; do not interpolate untrusted input.

Never log credentials, cookies, bearer tokens, authorization headers, OAuth
codes, passkeys, private keys, connection strings, personal data, request or
response bodies, billing details, wallet secrets or full URLs/query strings.
Use request and trace IDs as log fields for correlation, not indexed metric
labels. High-volume success access logs may be sampled; errors, security
decisions and financial reconciliation receipts must not be sampled. Record
sampling policy and rate explicitly. The observability log store does not
replace an append-only financial/audit ledger.

The collector forwards allowlisted monitoring events to Loki now. Its SQLite
queue survives restarts, bounds backlog to 10,000 events, retries after failure,
and exposes pending/dropped events and delivery failure. Local JSONL files
rotate at 5 MiB with three backups. Raw historical application logs are not
silently imported. Application adoption is still tracked as a coverage gap.
Cloudflare Workers need a reviewed tail Worker or supported log export;
Mac services need a reviewed agent/SDK. Add TLS and authenticated ingestion
before accepting logs from another host. Never expose the unauthenticated Loki
port through the tunnel.

Prometheus retains at most 30 days/5 GiB. Loki retains 14 days through its
compactor. Container logs rotate at 10 MiB with three files. Check host free
space; retention is not a backup. Back up persistent Grafana configuration and
the monitoring volumes with a documented restore drill. Include log access,
retention, deletion and backup rules in every project's privacy documentation.

## Detection, incident handling and reporting

The generated Prometheus rules are the source of alert truth. A production
website/backend failure sustained for three minutes is critical. Scrape loss
for two minutes is critical. Stale collectors, provider failures, Worker errors,
low disk, memory pressure, near-expiry TLS and failed log delivery are warnings.
Unconfigured integrations are informational findings. Prelaunch services remain
visible and do not page as production outages. Each alert needs project/service
labels, severity, a runbook and a recovery condition. Route notifications only
to an explicitly chosen destination, with grouping and deduplication.

Alerts are visible in Grafana now through the Prometheus `ALERTS` series. An
external notification receiver has not been selected. The off-host
watchdog keeps recording during a Mac outage, but without external notification
delivery a stopped dashboard cannot notify its owner.
Do not claim paging is configured merely because rules are firing locally.

For an incident: establish affected customer behavior, confirm the external
probe, compare public and origin checks, inspect database and tunnel state,
then inspect request/error logs for the same service/version/time window.
Classify Access redirects separately from origin downtime. Check `skaas.io`
deployment/DNS before expecting readiness. Preserve payment/trading gates.
Record onset, detection, affected services, evidence, mitigation, recovery
verification and follow-up owner. Never restart unrelated services as a first
diagnostic step. Publish a postmortem for material incidents.

Review the dashboard daily. Produce a weekly operations report listing measured
availability and its actual coverage, error/latency changes, incidents and
detection times, capacity, overdue backups/restore drills, job failures,
traffic by source, estimated revenue by currency, and every remaining coverage
gap. Reports must distinguish measured values, configuration and unknowns.
An automated report job and burn-rate SLO paging require further instrumentation;
neither is represented as already installed.

## Deployment, validation and rollback

Run the generator after editing the inventory. Validate with the standard-library
test suite, Ruff, Compose config and the image's own `promtool check config`.
Install only committed source using `python3 ops/observability/manage.py install
--revision HEAD --publish`. This command installs Python dependencies in a
dedicated venv, starts the owned Compose project, and registers its three
LaunchAgents. It never changes payment, trading or advertising launch flags.

Verify all four containers, collector readiness, every Prometheus target,
provisioned Grafana panels and Loki event readback. Verify unauthenticated
dashboard data access returns 401 and the public hostname serves Grafana over
TLS. Compare the installed `deployment.json` revision with the reviewed commit.
Run the saved Postman collection against loopback for repeatable HTTP checks.

To roll back, run the installer with the last verified Git revision. Keep named
volumes and credentials. Grafana major-version downgrades may require restoring
its matching database backup; test restoration before a major upgrade. Do not
delete volumes, reset another checkout, modify the All Workers Access policy or
recreate a tunnel to recover a failed collector. Private state lives under the
operator's `.local/share/llmsx-observability` directory; its admin password and
provider credentials must never be copied into this public repository.
