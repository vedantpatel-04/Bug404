"""
ShelfIQ Backend — WhatsApp Business API Integration.

Core differentiator: alerts via WhatsApp, not email dashboards.

Uses Meta's WhatsApp Business Cloud API (graph.facebook.com/v18.0).
Sends template messages to registered associate phone numbers.

Priority routing:
  CRITICAL → WhatsApp immediately
  HIGH     → WhatsApp within 15 min
  MEDIUM   → WhatsApp digest at shift end
  LOW      → Dashboard only (no WhatsApp)
"""
import hashlib
import hmac
from datetime import datetime
from typing import Optional

import httpx

from backend.app.core.config import settings


# ── WhatsApp Template Names ──────────────────────────────────
# These must be pre-registered in Meta Business Manager.

TEMPLATES = {
    "stockout_alert": "shelfiq_stockout_alert",
    "low_stock_alert": "shelfiq_low_stock_alert",
    "shift_digest": "shelfiq_shift_digest",
    "festival_reminder": "shelfiq_festival_reminder",
    "reorder_confirmation": "shelfiq_reorder_confirmation",
}


class WhatsAppService:
    """
    Sends alert messages via WhatsApp Business Cloud API.
    Falls back to logging if API credentials are not configured.
    """

    def __init__(self):
        self.base_url = f"https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}"
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.access_token = settings.WHATSAPP_ACCESS_TOKEN
        self.is_configured = bool(self.access_token and self.phone_number_id)

    async def send_stockout_alert(
        self,
        to_phone: str,
        store_name: str,
        aisle: str,
        product_name: str,
        action: str,
        time_str: str,
        language: str = "en",
    ) -> dict:
        """
        Send a CRITICAL stockout alert via WhatsApp.

        Message format:
        🛒 *ShelfIQ Alert*
        Store: {store_name}
        Aisle: {aisle}
        Issue: {product_name} is OUT OF STOCK
        Action: {action}
        Time: {time_str}
        [Mark Resolved]
        """
        components = [
            {
                "type": "body",
                "parameters": [
                    {"type": "text", "text": store_name},
                    {"type": "text", "text": aisle},
                    {"type": "text", "text": product_name},
                    {"type": "text", "text": action},
                    {"type": "text", "text": time_str},
                ],
            }
        ]

        return await self._send_template(
            to_phone=to_phone,
            template_name=TEMPLATES["stockout_alert"],
            language=language,
            components=components,
        )

    async def send_low_stock_alert(
        self,
        to_phone: str,
        store_name: str,
        product_name: str,
        current_qty: int,
        hours_until_stockout: int,
        language: str = "en",
    ) -> dict:
        """Send a HIGH priority low stock alert."""
        components = [
            {
                "type": "body",
                "parameters": [
                    {"type": "text", "text": store_name},
                    {"type": "text", "text": product_name},
                    {"type": "text", "text": str(current_qty)},
                    {"type": "text", "text": str(hours_until_stockout)},
                ],
            }
        ]

        return await self._send_template(
            to_phone=to_phone,
            template_name=TEMPLATES["low_stock_alert"],
            language=language,
            components=components,
        )

    async def send_festival_reminder(
        self,
        to_phone: str,
        event_name: str,
        days_until: int,
        at_risk_skus: list[str],
        language: str = "en",
    ) -> dict:
        """Send festival stock reminder 3 days before event."""
        sku_list = ", ".join(at_risk_skus[:5])  # Limit to 5 SKUs in message
        components = [
            {
                "type": "body",
                "parameters": [
                    {"type": "text", "text": event_name},
                    {"type": "text", "text": str(days_until)},
                    {"type": "text", "text": sku_list},
                ],
            }
        ]

        return await self._send_template(
            to_phone=to_phone,
            template_name=TEMPLATES["festival_reminder"],
            language=language,
            components=components,
        )

    async def _send_template(
        self,
        to_phone: str,
        template_name: str,
        language: str = "en",
        components: Optional[list] = None,
    ) -> dict:
        """
        Send a WhatsApp template message via Cloud API.

        Returns:
            API response dict, or error dict if not configured.
        """
        if not self.is_configured:
            # Log the message that would have been sent
            return {
                "status": "skipped",
                "reason": "WhatsApp not configured",
                "template": template_name,
                "to": to_phone[-4:] + "****",  # Masked
                "timestamp": datetime.now().isoformat(),
            }

        # WhatsApp language mapping
        lang_map = {"en": "en_US", "hi": "hi", "gu": "gu"}
        wa_lang = lang_map.get(language, "en_US")

        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": wa_lang},
            },
        }

        if components:
            payload["template"]["components"] = components

        url = f"{self.base_url}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=10.0)

            if response.status_code == 200:
                return {"status": "sent", "response": response.json()}
            else:
                return {
                    "status": "error",
                    "status_code": response.status_code,
                    "error": response.text,
                }

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Validate incoming webhook with X-Hub-Signature-256 header.
        Never process a webhook without verifying this.
        """
        if not settings.WHATSAPP_WEBHOOK_SECRET:
            return True  # Skip validation in dev if secret not set

        expected = hmac.new(
            settings.WHATSAPP_WEBHOOK_SECRET.encode("utf-8"),
            payload,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(f"sha256={expected}", signature)

    def get_alert_channel(self, severity: int) -> str:
        """
        Determine notification channel based on alert severity.

        Returns: "whatsapp_immediate" | "whatsapp_delayed" | "whatsapp_digest" | "dashboard_only"
        """
        if severity >= 4:  # CRITICAL
            return "whatsapp_immediate"
        elif severity >= 3:  # HIGH
            return "whatsapp_delayed"
        elif severity >= 2:  # MEDIUM
            return "whatsapp_digest"
        else:  # LOW
            return "dashboard_only"


# Singleton
whatsapp = WhatsAppService()
