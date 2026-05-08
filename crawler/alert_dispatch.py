"""Multi-channel alert dispatcher."""
import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from .scraper import DocumentRelease

logger = logging.getLogger(__name__)


@dataclass
class AlertPayload:
    """Standardized alert payload."""

    event_type: str  # "new_release", "content_update"
    source: str
    title: str
    url: str
    file_type: Optional[str] = None
    formatted_message: str = ""


class AlertChannel(ABC):
    """Base class for alert channels."""

    @abstractmethod
    async def send(self, payload: AlertPayload) -> bool:
        """Send alert. Returns True on success."""
        raise NotImplementedError


class TelegramChannel(AlertChannel):
    """Telegram bot notifications."""

    def __init__(self, bot_token: str, chat_ids: list[str] | None = None):
        self.bot_token = bot_token
        self.chat_ids = chat_ids or []
        self.api_url = f"https://api.telegram.org/bot{bot_token}"

    async def send(self, payload: AlertPayload) -> bool:
        if not self.bot_token or not self.chat_ids:
            logger.debug("Telegram not configured, skipping")
            return False

        import httpx

        message = self._format_message(payload)

        async with httpx.AsyncClient() as client:
            for chat_id in self.chat_ids:
                try:
                    await client.post(
                        f"{self.api_url}/sendMessage",
                        json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"},
                        timeout=10.0,
                    )
                    logger.info(f"Telegram sent to {chat_id[:8]}...")
                except Exception as e:
                    logger.error(f"Telegram send failed: {e}")
                    return False

        return True

    def _format_message(self, payload: AlertPayload) -> str:
        emoji = "🆕" if payload.event_type == "new_release" else "🔄"
        file_info = f" [{payload.file_type}]" if payload.file_type else ""

        return f"""{emoji} <b>UAP NEXUS ALERT</b>

<b>Source:</b> {payload.source}
<b>Event:</b> {payload.event_type.replace("_", " ").title()}

<a href="{payload.url}">{payload.title}</a>{file_info}
"""


class DiscordChannel(AlertChannel):
    """Discord webhook notifications."""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    async def send(self, payload: AlertPayload) -> bool:
        if not self.webhook_url:
            logger.debug("Discord not configured, skipping")
            return False

        import httpx

        color = 0x00FF00 if payload.event_type == "new_release" else 0xFFAA00

        embed = {
            "title": f"{payload.title}",
            "url": payload.url,
            "color": color,
            "fields": [
                {"name": "Source", "value": payload.source, "inline": True},
                {"name": "Event", "value": payload.event_type.replace("_", " ").title(), "inline": True},
            ],
            "footer": {"text": "UAP NEXUS"},
        }

        if payload.file_type:
            embed["fields"].append({"name": "Type", "value": payload.file_type, "inline": True})

        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    self.webhook_url,
                    json={"embeds": [embed]},
                    timeout=10.0,
                )
            return True
        except Exception as e:
            logger.error(f"Discord send failed: {e}")
            return False


class EmailChannel(AlertChannel):
    """SendGrid email notifications."""

    def __init__(self, api_key: str, from_email: str, to_emails: list[str] | None = None):
        self.api_key = api_key
        self.from_email = from_email
        self.to_emails = to_emails or []

    async def send(self, payload: AlertPayload) -> bool:
        if not self.api_key or not self.to_emails:
            logger.debug("Email not configured, skipping")
            return False

        import httpx

        subject = f"[UAP NEXUS] {payload.event_type.replace('_', ' ').title()}: {payload.title}"

        html_content = f"""
        <h2>UAP NEXUS Alert</h2>
        <p><strong>Source:</strong> {payload.source}</p>
        <p><strong>Event:</strong> {payload.event_type}</p>
        <p><a href="{payload.url}">{payload.title}</a></p>
        """

        try:
            async with httpx.AsyncClient() as client:
                for to_email in self.to_emails:
                    await client.post(
                        "https://api.sendgrid.com/v3/mail/send",
                        json={
                            "personalizations": [{"to": [{"email": to_email}]}],
                            "from": {"email": self.from_email},
                            "subject": subject,
                            "content": [{"type": "text/html", "value": html_content}],
                        },
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        timeout=10.0,
                    )
            return True
        except Exception as e:
            logger.error(f"Email send failed: {e}")
            return False


class AlertDispatcher:
    """Routes alerts to configured channels."""

    def __init__(self):
        self.channels: list[AlertChannel] = []

    def add_channel(self, channel: AlertChannel):
        """Register an alert channel."""
        self.channels.append(channel)
        logger.info(f"Registered alert channel: {channel.__class__.__name__}")

    def from_env(self):
        """Configure channels from environment variables."""
        import os

        # Telegram
        telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        telegram_chats = os.getenv("TELEGRAM_CHAT_IDS", "")
        if telegram_token and telegram_chats:
            chat_ids = [c.strip() for c in telegram_chats.split(",") if c.strip()]
            self.add_channel(TelegramChannel(telegram_token, chat_ids))

        # Discord
        discord_url = os.getenv("DISCORD_WEBHOOK_URL", "")
        if discord_url:
            self.add_channel(DiscordChannel(discord_url))

        # Email
        sendgrid_key = os.getenv("SENDGRID_API_KEY", "")
        from_email = os.getenv("ALERT_FROM_EMAIL", "alerts@uapnexus.com")
        to_emails = os.getenv("ALERT_TO_EMAILS", "")
        if sendgrid_key and to_emails:
            emails = [e.strip() for e in to_emails.split(",") if e.strip()]
            self.add_channel(EmailChannel(sendgrid_key, from_email, emails))

        return self

    async def dispatch(self, releases: list[DocumentRelease], event_type: str = "new_release"):
        """Send alert to all configured channels."""
        if not releases:
            return

        for release in releases:
            payload = AlertPayload(
                event_type=event_type,
                source=release.source,
                title=release.title,
                url=release.url,
                file_type=release.file_type,
            )

            tasks = [channel.send(payload) for channel in self.channels]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            success_count = sum(1 for r in results if r is True)
            logger.info(
                f"Dispatched {release.title[:50]}... — {success_count}/{len(self.channels)} channels"
            )
