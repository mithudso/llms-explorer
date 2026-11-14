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
