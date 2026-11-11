"""Mail transport stays bounded and logs outcomes without subscriber identifiers."""
import asyncio
import logging
from types import SimpleNamespace

import pytest

from explorer_api import notify


class FakeSMTP:
    def __init__(self, host, port, *, timeout=None):
        self.host, self.port, self.timeout = host, port, timeout
        self.closed = False
        self.sent = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.closed = True

    def starttls(self):
        pass

    def send_message(self, message):
        self.sent.append(message)


def settings(**overrides):
    return SimpleNamespace(
        **dict(smtp_host=None, smtp_port=587, smtp_user=None, smtp_password=None,
               smtp_from="sender@example.test", smtp_timeout_seconds=15) | overrides
    )


def test_disabled_mail_does_not_log_recipient_subject_or_body(caplog):
    with caplog.at_level(logging.INFO):
        notify.send_email("private-recipient@example.test", "private subject", "private body",
                          settings())
    assert "private-recipient" not in caplog.text
    assert "private subject" not in caplog.text
    assert "private body" not in caplog.text
    assert "smtp_delivery_skipped" in caplog.text


def test_smtp_uses_configured_timeout_closes_and_reports_success(monkeypatch, caplog):
    smtp = FakeSMTP("mail.example.test", 587)
    arguments = {}

    def construct(host, port, **kwargs):
        arguments.update(host=host, port=port, **kwargs)
        return smtp

    monkeypatch.setattr(notify.smtplib, "SMTP", construct)
    with caplog.at_level(logging.INFO):
        notify.send_email("private-recipient@example.test", "subject", "body",
                          settings(smtp_host="mail.example.test", smtp_timeout_seconds=3))
    assert arguments["timeout"] == 3
    assert smtp.closed
    assert len(smtp.sent) == 1
    assert smtp.sent[0]["To"] == "private-recipient@example.test"
    assert "smtp_delivery_started" in caplog.text
    assert "smtp_delivery_succeeded" in caplog.text
    assert "private-recipient" not in caplog.text


def test_transport_failure_reports_only_error_type_and_propagates(monkeypatch, caplog):
    def fail(*_args, **_kwargs):
        raise TimeoutError("sensitive transport detail")

    monkeypatch.setattr(notify.smtplib, "SMTP", fail)
    with caplog.at_level(logging.INFO), pytest.raises(TimeoutError):
        notify.send_email("private-recipient@example.test", "subject", "body",
                          settings(smtp_host="mail.example.test"))
    assert "smtp_delivery_failed" in caplog.text
    assert "TimeoutError" in caplog.text
    assert "sensitive transport detail" not in caplog.text
    assert "private-recipient" not in caplog.text


async def test_notice_dispatch_uses_thread_offload(monkeypatch):
    subscriber = SimpleNamespace(email="private-recipient@example.test",
                                 unsubscribe_token="private-token")
    rows = SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: [subscriber]))

    class Session:
        async def execute(self, _statement):
            return rows

    observed = []

    async def offload(function, *args):
        observed.append((function, args))

    monkeypatch.setattr(asyncio, "to_thread", offload)
    count = await notify.notify_new_post(Session(), settings(api_public_url="https://api.example.test"),
                                         title="post", url="https://example.test/post")
    assert count == 1
    assert len(observed) == 1
    assert observed[0][0] is notify.send_email
    assert observed[0][1][0] == subscriber.email
    assert "private-token" in observed[0][1][2]
