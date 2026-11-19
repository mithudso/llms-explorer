# Fleet observability standard

Version 1.1.1. Updated 2026-11-19. Owner is the platform operator.
Delta adds a public Google seller-file check alongside AdSense publisher status.

This standard applies to LLMSX, legacy LLMS-Explorer, Oraclebot, That's What She
Said, MoreLube, Net DNS Monitor and SKaaS, including their websites, APIs, databases, background
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

Fedora runs Grafana, Prometheus, Blackbox Exporter, Loki and the public tunnel.
The Mac continues to run the collector and its existing provider grants. The
SSH telemetry bridge forwards collector metrics and Loki writes over the
private connection. Turnover of the Mac collector leaves historical dashboards
and public HTTPS checks available. The independent Cloudflare watchdog keeps
seven days of scheduled results in its own D1 database and requires a bearer
token to read history.

For a Grafana release, build the reviewed revision on Fedora with both the
release Compose file and its existing Fedora override. The override keeps Loki
on its dedicated volume. Preserve all volumes, the SSH bridge, and the
single Cloudflare tunnel. Update the Mac collector with
`python3 ops/observability/manage.py install-collector --revision <merged-sha>`.
For an independent watchdog release, use the watchdog deployment script from
the same clean merged checkout. Verify the deployed image tags and collector
source revision, all target and public health results, rule evaluation and the
absence of anonymous access to dashboards and metrics.

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

## Website status and business signals

The [business dashboard](https://ops.llmsx.org/d/llmsx-business) filters by
domain. It shows GA4 active users, estimated Cloudflare zone unique IPs,
AdSense review and earnings, public Google seller declarations, Cloudflare Security Center findings, firewall
event aggregates where enabled, Stripe activity and net balance movements,
commerce, inbound email activity, and verified forwarding configuration.
Cloudflare estimates can include bots and subdomains. Security Center findings,
daily threat counts and WAF action counts measure different things.

Stripe monitoring requires a private `stripe-accounts.json` mapping in the
collector state directory. Each project entry names an expected live
`account_id` and its private absolute `key_file`. Use a restricted live key
with account, Events and Balance Transactions read access. Enable a mapping
only after the site is proven to have a dedicated settlement account.
A 30-minute lookback alerts on a successful purchase, balance movement or
financial/account change. The dashboard reports a 24-hour total net movement
per currency in minor units. These rules fire in Prometheus. Configure and
verify a notification route before relying on a push alert.

The private `morelube-db-path` file points to the production store database.
The collector reads aggregate settlement counts and their USD-equivalent
gross amount in SQLite read-only mode. It excludes owner test orders. Net DNS
Monitor uses a D1 aggregate of currently paid orders created in the last 24
hours. That view is distinct from provider settlement or a payment event.

The private `mail-destination` file supplies the approved forwarding address.
The collector compares it with current Cloudflare routing without exporting
addresses or message data. Email volume uses the prior UTC day of incoming
Cloudflare events. The legacy Google Workspace domain needs its own mail
routing and activity grant. AdSense Sites and earnings need the separate
`adsense.readonly` grant. Check the provider status and last successful
acquisition when a panel is unavailable.

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
