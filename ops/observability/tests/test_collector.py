import importlib.util
import json
import tempfile
import threading
import time
import unittest
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("fleet_collector", ROOT / "collector.py")
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)


class Upstream(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/ads-missing":
            self.send_error(404)
            return
        if self.path in {"/ads-google", "/ads-other"}:
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(
                b"# fixture\nGoogle.com, pub-0000000000000000, DIRECT"
                if self.path == "/ads-google"
                else b"example.org, partner-42, RESELLER"
            )
            return
        if self.path == "/login-redirect":
            self.send_response(302)
            self.send_header("Location", "/login")
            self.end_headers()
            return
        self.send_response(200)
        self.send_header(
            "Content-Type", "text/html" if self.path == "/login" else "application/json"
        )
        self.end_headers()
        self.wfile.write(
            b"<html>Cloudflare Access</html>"
            if self.path == "/login"
            else json.dumps({"status": "ready", "billing": False}).encode()
        )

    def do_POST(self):
        self.server.payloads.append(
            json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        )
        self.send_response(204)
        self.end_headers()

    def log_message(self, *_):
        pass


class FleetChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Upstream)
        cls.server.payloads = []
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def test_access_login_is_never_backend_health(self):
        for path in ["/login", "/login-redirect"]:
            ok, _, _, _ = collector.check_http(
                {"url": self.base + path, "expect": {"status": "ready"}}
            )
            self.assertFalse(ok)

    def test_public_seller_states_distinguish_google_missing_and_html(self):
        for path, state in (("/ads-missing", 0), ("/ads-google", 1), ("/ads-other", 2)):
            with self.subTest(path=path):
                self.assertEqual(collector.google_seller_file(self.base + path), state)
        with self.assertRaises(ValueError):
            collector.google_seller_file(self.base + "/login")

    def test_valid_json_with_wrong_state_fails(self):
        ok, _, _, _ = collector.check_http(
            {"url": self.base + "/", "expect": {"status": "ok"}}
        )
        self.assertFalse(ok)

    def test_disabled_capability_is_preserved(self):
        ok, status, _, flags = collector.check_http(
            {
                "url": self.base + "/",
                "expect": {"status": "ready"},
                "capabilities": ["billing"],
            }
        )
        self.assertTrue(ok)
        self.assertEqual(status, 200)
        self.assertEqual(flags, {"billing": 0})

    def test_metric_labels_cannot_inject_new_series(self):
        result = collector.render_metrics(
            [collector.sample("test", 1, project='bad"\nvalue\\')]
        ).decode()
        self.assertIn('project="bad\\"\\nvalue\\\\"', result)
        self.assertEqual(len(result.splitlines()), 3)
        with self.assertRaises(ValueError):
            collector.sample("test", float("nan"))

    def event(self, n=0):
        return {
            "timestamp": time.time(),
            "severity": "info",
            "service_name": "fleet-collector",
            "service_version": "test",
            "project": "fleet",
            "environment": "production",
            "event": "test.event",
            "duration_ms": n,
        }

    def test_log_allowlist_removes_secrets_and_validates_values(self):
        clean = collector.validate_log(
            {
                **self.event(),
                "authorization": "private",
                "payload": {"secret": "private"},
            }
        )
        self.assertNotIn("authorization", clean)
        self.assertNotIn("payload", clean)
        with self.assertRaises(ValueError):
            collector.validate_log({**self.event(), "error_type": "Bearer secret"})

    def test_durable_spool_survives_failure_and_delivers_to_real_http_receiver(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "queue.sqlite"
            spool = collector.LogSpool(path, limit=2)
            for n in range(3):
                spool.append(self.event(n))
            self.assertEqual(spool.stats(), (2, 1))
            with self.assertRaises(OSError):
                spool.push("http://127.0.0.1:1")
            reopened = collector.LogSpool(path, limit=2)
            self.assertEqual(reopened.stats(), (2, 1))
            self.assertTrue(reopened.push(self.base))
            self.assertEqual(reopened.stats(), (0, 1))
            self.assertEqual(
                [
                    json.loads(v[1])["duration_ms"]
                    for v in self.server.payloads[-1]["streams"][0]["values"]
                ],
                [1, 2],
            )

    def test_missing_ads_authorization_never_emits_zero_money(self):
        with tempfile.TemporaryDirectory() as tmp:
            c = collector.Collector({"sites": []}, Path(tmp))
            rows = c.ads()
            self.assertNotIn("fleet_ads_estimated_earnings", [r[0] for r in rows])
            configured = {
                labels["source"]: value
                for name, value, labels in rows
                if name == "fleet_integration_configured"
            }
            self.assertEqual(configured, {"adsense": 0, "adsense-sites": 0, "ezmob": 0})
            self.assertNotIn("fleet_adsense_site_status", [r[0] for r in rows])

    def test_morelube_settlement_metrics_exclude_owner_test_orders(self):
        import sqlite3

        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            db_path = state / "store.sqlite"
            with closing(sqlite3.connect(db_path)) as db, db:
                db.executescript(
                    "CREATE TABLE orders(id INTEGER, is_test INTEGER);"
                    "CREATE TABLE payments(order_id INTEGER, amount_cents INTEGER, currency TEXT, settled_at TEXT);"
                    "INSERT INTO orders VALUES (1, 0), (2, 1), (3, 0);"
                    "INSERT INTO payments VALUES"
                    "(1, 1299, 'USD',strftime('%Y-%m-%dT%H:%M:%fZ','now','-1 minute')),"
                    "(2, 4500, 'USD',strftime('%Y-%m-%dT%H:%M:%fZ','now','-2 minutes')),"
                    "(3, 1200, 'USD',strftime('%Y-%m-%dT%H:%M:%fZ','now','-2 days'));"
                )
            (state / "morelube-db-path").write_text(str(db_path))
            result = collector.Collector({}, state).commerce("morelube")
            values = {name: value for name, value, _ in result}
            self.assertEqual(values["fleet_morelube_gross_usd_cents_day"], 1299)
            self.assertEqual(values["fleet_morelube_purchases_day"], 1)
            self.assertEqual(values["fleet_morelube_purchases_recent"], 1)

    def test_stripe_account_mismatch_emits_unavailable_without_financial_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            key = state / "stripe"
            key.write_text("rk_live_fixture")
            c = collector.Collector({}, state)
            with patch.object(
                collector, "request_json", return_value={"id": "acct_other"}
            ) as call:
                rows = c.stripe(
                    "test", {"account_id": "acct_expected", "key_file": str(key)}
                )
            call.assert_called_once()
            values = {name: value for name, value, _ in rows}
            self.assertEqual(values["fleet_integration_success"], 0)
            self.assertFalse(any(name.startswith("fleet_stripe_") for name in values))

    def test_no_rows_from_cloudflare_is_not_zero_traffic(self):
        inv = {
            "sites": [{"project": "test", "zone_id": "zone"}],
            "workers": [],
            "databases": [],
            "tunnels": [],
        }
        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.object(collector, "cf_json", return_value=[]),
        ):
            c = collector.Collector(inv, Path(tmp))
            c.graphql = lambda q: (
                {"zones": [{"httpRequests1dGroups": []}]}
                if "zones(" in q
                else {"accounts": [{"workersInvocationsAdaptive": []}]}
            )
            rows = c.cloudflare()
            self.assertFalse(any(r[0] == "fleet_cloudflare_requests" for r in rows))
            self.assertTrue(
                any(
                    r[0] == "fleet_integration_data_present" and r[1] == 0 for r in rows
                )
            )

    def test_empty_watchdog_history_exposes_never_observed_targets(self):
        inventory = {
            "watchdog_url": "https://watchdog.example/status",
            "watchdog_targets": [{"name": "test", "phase": "production"}],
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "watchdog-token").write_text("fixture-secret")
            c = collector.Collector(inventory, root / "state")
            with patch.object(collector, "request_json", return_value={"checks": []}):
                rows = c.watchdog()
            self.assertTrue(
                any(
                    name == "fleet_watchdog_checked_timestamp_seconds" and value == 0
                    for name, value, _ in rows
                )
            )
            self.assertFalse(
                any(name == "fleet_watchdog_success" for name, _, _ in rows)
            )

    def test_snapshots_are_replaced_on_failure_and_readiness_expires(self):
        inventory = {
            k: [] for k in ["sites", "checks", "launchd", "databases", "tunnels"]
        }
        with tempfile.TemporaryDirectory() as tmp:
            c = collector.Collector(inventory, Path(tmp))
            self.assertFalse(c.ready())
            c.cycles["fast"] = time.time()
            self.assertTrue(c.ready())
            c.cycles["fast"] = time.time() - 181
            self.assertFalse(c.ready())
            c.snapshots["fast"] = [collector.sample("untrustworthy_old_value", 1)]

            def fail():
                c.stop.set()
                raise ValueError("secret must never be logged")

            c.loop("fast", fail)
            self.assertNotIn(b"untrustworthy_old_value", c.metrics())
            self.assertNotIn(
                "secret must never be logged",
                (Path(tmp) / "collector.jsonl").read_text(),
            )


if __name__ == "__main__":
    unittest.main()
