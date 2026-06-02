"""
Razorpay Billing Service — UPI-first subscription management.

Implements:
- Plan creation (Starter ₹4,999/mo, Growth ₹12,999/mo, Enterprise custom)
- Subscription creation with UPI autopay
- Payment verification
- Grace period handling (3-day grace → suspend alerts)
"""
import hashlib
import hmac
from datetime import datetime
from typing import Optional

import httpx

from backend.app.core.config import settings


class RazorpayBilling:
    """Razorpay integration for INR subscription billing."""

    BASE_URL = "https://api.razorpay.com/v1"

    # ShelfIQ pricing (INR, monthly, excl. GST)
    PLANS = {
        "starter": {
            "name": "Starter",
            "amount": 499900,   # ₹4,999 in paise
            "period": "monthly",
            "interval": 1,
            "description": "Up to 2 stores, 10 cameras, basic alerts",
            "features": ["2 stores", "10 cameras", "WhatsApp alerts", "Basic forecast"],
        },
        "growth": {
            "name": "Growth",
            "amount": 1299900,  # ₹12,999 in paise
            "period": "monthly",
            "interval": 1,
            "description": "Up to 10 stores, unlimited cameras, full analytics",
            "features": ["10 stores", "Unlimited cameras", "Priority WhatsApp", "Full analytics", "Festival forecasting", "API access"],
        },
        "enterprise": {
            "name": "Enterprise",
            "amount": 0,  # Custom pricing
            "period": "monthly",
            "interval": 1,
            "description": "Unlimited stores, dedicated support, SLA",
            "features": ["Unlimited stores", "Dedicated CSM", "99.9% SLA", "Custom integrations", "On-prem option"],
        },
    }

    def __init__(self):
        self.key_id = settings.RAZORPAY_KEY_ID
        self.key_secret = settings.RAZORPAY_KEY_SECRET
        self.enabled = bool(self.key_id and self.key_secret)

    @property
    def auth(self) -> tuple[str, str]:
        return (self.key_id or "", self.key_secret or "")

    async def create_plan(self, plan_key: str) -> dict:
        """Create a Razorpay plan for a ShelfIQ tier."""
        if not self.enabled:
            return {"status": "disabled", "plan_key": plan_key}

        plan = self.PLANS.get(plan_key)
        if not plan or plan["amount"] == 0:
            return {"status": "custom", "plan_key": plan_key}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/plans",
                auth=self.auth,
                json={
                    "period": plan["period"],
                    "interval": plan["interval"],
                    "item": {
                        "name": f"ShelfIQ {plan['name']}",
                        "amount": plan["amount"],
                        "currency": "INR",
                        "description": plan["description"],
                    },
                },
            )
            return response.json()

    async def create_subscription(
        self,
        plan_id: str,
        org_id: str,
        customer_email: str,
        total_count: int = 12,  # 12 months
    ) -> dict:
        """Create a subscription for an organization."""
        if not self.enabled:
            return {
                "status": "disabled",
                "message": "Razorpay not configured. Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET.",
            }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/subscriptions",
                auth=self.auth,
                json={
                    "plan_id": plan_id,
                    "total_count": total_count,
                    "quantity": 1,
                    "notes": {
                        "org_id": org_id,
                        "platform": "shelfiq",
                    },
                    "notify_info": {
                        "notify_email": customer_email,
                    },
                },
            )
            return response.json()

    async def verify_payment(
        self,
        razorpay_payment_id: str,
        razorpay_subscription_id: str,
        razorpay_signature: str,
    ) -> bool:
        """Verify Razorpay payment signature (HMAC SHA256)."""
        if not self.key_secret:
            return False

        payload = f"{razorpay_payment_id}|{razorpay_subscription_id}"
        expected = hmac.new(
            self.key_secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected, razorpay_signature)

    async def cancel_subscription(self, subscription_id: str, at_cycle_end: bool = True) -> dict:
        """Cancel a subscription (at cycle end or immediately)."""
        if not self.enabled:
            return {"status": "disabled"}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/subscriptions/{subscription_id}/cancel",
                auth=self.auth,
                json={"cancel_at_cycle_end": 1 if at_cycle_end else 0},
            )
            return response.json()

    def check_grace_period(self, plan_expires: Optional[datetime]) -> dict:
        """
        Check if an org is in grace period.
        Grace: 3 days after plan_expires → alerts suspended.
        """
        if not plan_expires:
            return {"status": "no_plan", "alerts_active": False}

        now = datetime.now()
        if now < plan_expires:
            days_left = (plan_expires - now).days
            return {"status": "active", "days_left": days_left, "alerts_active": True}

        days_overdue = (now - plan_expires).days
        if days_overdue <= 3:
            return {
                "status": "grace_period",
                "days_overdue": days_overdue,
                "grace_remaining": 3 - days_overdue,
                "alerts_active": True,
                "message": f"Payment overdue. {3 - days_overdue} days of grace remaining.",
            }

        return {
            "status": "suspended",
            "days_overdue": days_overdue,
            "alerts_active": False,
            "message": "Subscription expired. Alerts suspended. Please renew.",
        }


# Singleton
razorpay = RazorpayBilling()
