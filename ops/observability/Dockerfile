FROM grafana/grafana:13.3.1 AS grafana
COPY --chown=472:0 grafana/provisioning /etc/grafana/provisioning
COPY --chown=472:0 grafana/dashboards /opt/fleet/dashboards

FROM prom/prometheus:v3.16.0 AS prometheus
COPY prometheus /etc/prometheus

FROM prom/blackbox-exporter:v0.29.1 AS blackbox
COPY blackbox.yml /etc/blackbox/blackbox.yml

FROM grafana/loki:3.7.10 AS loki
COPY loki.yml /etc/loki/loki.yml
