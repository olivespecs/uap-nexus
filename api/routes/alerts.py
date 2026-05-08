"""Alerts API routes."""
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

router = APIRouter()


class AlertSubscription(BaseModel):
    """Alert subscription request."""

    channel_type: str  # "telegram", "discord", "email"
    channel_id: str
    filters: dict = {}


class SubscriptionResponse(BaseModel):
    """Subscription response."""

    id: str
    channel_type: str
    channel_id: str
    filters: dict
    created_at: str


# In-memory subscriptions
_subscriptions: dict[str, dict] = {}


@router.get("/channels")
async def get_channels():
    """List available alert channels."""
    import os

    return {
        "channels": {
            "telegram": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
            "discord": bool(os.getenv("DISCORD_WEBHOOK_URL")),
            "email": bool(os.getenv("SENDGRID_API_KEY")),
        }
    }


@router.get("/subscriptions")
async def list_subscriptions():
    """List all subscriptions."""
    return {"subscriptions": list(_subscriptions.values())}


@router.post("/subscribe")
async def subscribe(subscription: AlertSubscription):
    """Create alert subscription."""
    if subscription.channel_type not in ["telegram", "discord", "email"]:
        raise HTTPException(status_code=400, detail="Invalid channel_type")

    from datetime import datetime

    sub_id = str(uuid4())
    sub_dict = subscription.model_dump()
    sub_dict["id"] = sub_id
    sub_dict["created_at"] = datetime.utcnow().isoformat()

    _subscriptions[sub_id] = sub_dict

    return SubscriptionResponse(**sub_dict)


@router.delete("/subscriptions/{sub_id}")
async def unsubscribe(sub_id: str):
    """Delete subscription."""
    if sub_id not in _subscriptions:
        raise HTTPException(status_code=404, detail="Subscription not found")

    del _subscriptions[sub_id]

    return {"deleted": True}


@router.post("/test")
async def test_alert(channel_type: str, channel_id: str):
    """Test send alert to channel."""
    from crawler.alert_dispatch import (
        AlertDispatcher,
        TelegramChannel,
        DiscordChannel,
        EmailChannel,
    )

    payload = AlertPayload(
        event_type="test",
        source="TEST",
        title="Test Alert from UAP NEXUS",
        url="https://uapnexus.com",
    )

    if channel_type == "telegram":
        channel = TelegramChannel(channel_id, [channel_id])
    elif channel_type == "discord":
        channel = DiscordChannel(channel_id)
    elif channel_type == "email":
        channel = EmailChannel(channel_id, "test@uapnexus.com", [channel_id])
    else:
        raise HTTPException(status_code=400, detail="Invalid channel_type")

    success = await channel.send(payload)

    return {"success": success}


from crawler.alert_dispatch import AlertPayload