# Fleet operations

Private dashboard: https://ops.llmsx.org

Policy, coverage boundaries, credential requirements and incident runbooks:
[`docs/operations/observability.md`](../../docs/operations/observability.md).

`inventory.json` is the service register. `generate.py` writes the Grafana
dashboard, blackbox modules and Prometheus scrape/alert configuration. Commit
both inventory and generated files. The native collector uses existing private
Google/Cloudflare grants; it never changes application data or launch gates.

Validation:

```sh
python3 -m unittest discover -s ops/observability/tests -v
uvx ruff check ops/observability
python3 ops/observability/generate.py
docker compose -f ops/observability/compose.yaml config --quiet
docker build --target prometheus -t llmsx-fleet-prometheus:check ops/observability
docker run --rm --entrypoint /bin/promtool llmsx-fleet-prometheus:check check config /etc/prometheus/prometheus.yml
```

Install reviewed, committed source on macOS:

```sh
python3 ops/observability/manage.py install --revision HEAD --publish
```

The installer prints the private runtime directory, never the password.
It starts an isolated Compose project and three owned user LaunchAgents. An
existing dashboard hostname or tunnel without matching owned credentials is
refused, never overwritten. Local metrics and logs are not exposed publicly.
Do not use `docker compose down --volumes`: it destroys monitoring history.

## Domain and application contracts

The off-host Worker accepts a private `WATCHDOG_EXTRA_TARGETS` JSON array. Each
entry has a unique name, a `production` or `staging` phase and a 2, 5 or 10 minute
interval. A DNS target supplies a hostname and either its exact delegated NS set
or a required address record type. An HTTPS target can require a JSON subset,
page text, status, a canonical or sign-in redirect, or a latency ceiling. Only
explicit canonical redirects are followed. Monitoring uses GET and HEAD.

The authentication boundary test passes when a protected route returns its
expected denial or sign-in redirect. It does not reuse a person's browser or
perform checkout, trades, order changes or writes. The Worker stores outcomes and
latency without response bodies or OAuth redirect parameters. The authenticated
status response declares the target intervals and includes the latest samples.

Apply the idempotent watchdog schema before enabling an email destination. With
the `WATCHDOG_MAIL` binding and private sender and recipient settings, production
checks send one grouped email after three consecutive failures or two consecutive
recovery passes. The D1 state suppresses repeat notifications until a state
change. Delivery failures leave the transition pending and are logged as a coded
error. Staging results remain visible without notifying the recipient.
