"""Email delivery for the subscribers mailing list.

No provider is wired in by default: with ``smtp_host`` unset (the default),
:func:`send_email` records a skipped-delivery event instead of sending, so a dev environment
or a deploy that has not configured SMTP still runs — it just does not mail
anyone. Set ``SMTP_HOST``/``SMTP_PORT``/``SMTP_USER``/``SMTP_PASSWORD``/
``SMTP_FROM`` to send for real (see ``api/.env.example``).
"""

from __future__ import annotations

import asyncio
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
    """Send one email, or record a skipped event if SMTP is not configured."""
    if not settings.smtp_host:
        log.info("smtp_delivery_skipped reason=not_configured")
        return
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.smtp_from
    message["To"] = to
    message.set_content(body)
    log.info("smtp_delivery_started")
    try:
        with smtplib.SMTP(
            settings.smtp_host, settings.smtp_port, timeout=settings.smtp_timeout_seconds,
        ) as smtp:
            smtp.starttls()
            if settings.smtp_user and settings.smtp_password:
                smtp.login(settings.smtp_user, settings.smtp_password.get_secret_value())
            smtp.send_message(message)
    except (OSError, smtplib.SMTPException) as error:
        log.warning("smtp_delivery_failed error_type=%s", type(error).__name__)
        raise
    log.info("smtp_delivery_succeeded")


async def notify_new_post(
    session: AsyncSession, settings: Settings, *, title: str, url: str
) -> int:
    """Mail every confirmed, still-subscribed address about a new post.

    Returns the number of subscribers processed. Call this explicitly after
    staging a post; this module provides no automatic publishing hook.
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
        await asyncio.to_thread(send_email, subscriber.email, f"New post: {title}", body, settings)
    return len(rows)


__all__ = ["notify_new_post", "send_email"]
