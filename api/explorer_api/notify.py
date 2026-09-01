"""Email delivery for the subscribers mailing list.

No provider is wired in by default: with ``smtp_host`` unset (the default),
:func:`send_email` logs the message instead of sending it, so a dev environment
or a deploy that has not configured SMTP still runs — it just does not mail
anyone. Set ``SMTP_HOST``/``SMTP_PORT``/``SMTP_USER``/``SMTP_PASSWORD``/
``SMTP_FROM`` to send for real (see ``api/.env.example``).
"""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from typing import TYPE_CHECKING

from sqlalchemy import select

from .models import Subscriber
from .settings import Settings

if TYPE_CHECKING:  # pragma: no cover - typing only
    from sqlalchemy.ext.asyncio import AsyncSession

log = logging.getLogger(__name__)


def send_email(to: str, subject: str, body: str, settings: Settings) -> None:
    """Send one email, or log it if no SMTP provider is configured."""
    if not settings.smtp_host:
        log.info("smtp not configured; would send %r to %s", subject, to)
        return
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.smtp_from
    message["To"] = to
    message.set_content(body)
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
        smtp.starttls()
        if settings.smtp_user and settings.smtp_password:
            smtp.login(settings.smtp_user, settings.smtp_password.get_secret_value())
        smtp.send_message(message)


async def notify_new_post(
    session: AsyncSession, settings: Settings, *, title: str, url: str
) -> int:
    """Mail every confirmed, still-subscribed address about a new post.

    Returns the number of subscribers notified. Run this after staging a post
    (see ``scripts/notify_new_post.py``); it is not triggered automatically by
    anything in this service.
    """
    rows = (
        await session.execute(
            select(Subscriber).where(
                Subscriber.confirmed_at.is_not(None),
                Subscriber.unsubscribed_at.is_(None),
            )
        )
    ).scalars().all()
    for subscriber in rows:
        unsubscribe_url = (
            f"{settings.api_public_url}/api/subscribers/unsubscribe"
            f"?token={subscriber.unsubscribe_token}"
        )
        body = f"New post: {title}\n{url}\n\nUnsubscribe: {unsubscribe_url}"
        send_email(subscriber.email, f"New post: {title}", body, settings)
    return len(rows)


__all__ = ["notify_new_post", "send_email"]
