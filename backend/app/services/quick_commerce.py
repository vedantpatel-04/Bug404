"""
Quick-Commerce Integration Stub — Blinkit, Zepto, Swiggy Instamart.

Provides a unified interface for:
- Real-time inventory sync (push stock levels to QC platforms)
- Order ingestion (pull QC orders back into demand data)
- Dark store mapping (map ShelfIQ aisles to QC fulfillment zones)

This is a stub — actual API keys and endpoints are platform-specific
and require partnership agreements.
"""
from datetime import datetime
from typing import Optional

import httpx

from backend.app.core.config import settings


class QuickCommerceHub:
    """
    Unified adapter for Indian quick-commerce platforms.

    Supported (stub):
    - Blinkit (Zomato)
    - Zepto
    - Swiggy Instamart
    - BigBasket Now
    """

    PLATFORMS = {
        "blinkit": {
            "name": "Blinkit",
            "base_url": "https://api.blinkit.com/v1",
            "sync_endpoint": "/inventory/sync",
            "orders_endpoint": "/orders/list",
        },
        "zepto": {
            "name": "Zepto",
            "base_url": "https://api.zeptonow.com/v1",
            "sync_endpoint": "/stock/update",
            "orders_endpoint": "/orders/recent",
        },
        "swiggy_instamart": {
            "name": "Swiggy Instamart",
            "base_url": "https://api.swiggy.com/instamart/v1",
            "sync_endpoint": "/catalog/stock",
            "orders_endpoint": "/orders/fetch",
        },
        "bigbasket": {
            "name": "BigBasket Now",
            "base_url": "https://api.bigbasket.com/v2",
            "sync_endpoint": "/inventory/push",
            "orders_endpoint": "/orders/pull",
        },
    }

    def __init__(self):
        # API keys would come from per-org settings in production
        self.api_keys: dict[str, str] = {}

    async def sync_inventory(
        self,
        platform: str,
        store_id: str,
        items: list[dict],
    ) -> dict:
        """
        Push current stock levels to a quick-commerce platform.

        Args:
            platform: One of 'blinkit', 'zepto', 'swiggy_instamart', 'bigbasket'
            store_id: ShelfIQ store ID
            items: List of {'sku_id': str, 'stock_count': int, 'price': float}
        """
        if platform not in self.PLATFORMS:
            return {"status": "error", "message": f"Unknown platform: {platform}"}

        config = self.PLATFORMS[platform]
        api_key = self.api_keys.get(platform)

        if not api_key:
            # Stub mode — simulate sync
            return {
                "status": "stub",
                "platform": config["name"],
                "store_id": store_id,
                "items_synced": len(items),
                "synced_at": datetime.now().isoformat(),
                "message": f"Stub: would sync {len(items)} items to {config['name']}. Set API key to enable.",
            }

        # Real API call (when keys are configured)
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{config['base_url']}{config['sync_endpoint']}",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "store_id": store_id,
                        "items": items,
                        "timestamp": datetime.now().isoformat(),
                    },
                )
                return {
                    "status": "synced" if response.status_code == 200 else "error",
                    "platform": config["name"],
                    "response_code": response.status_code,
                    "items_synced": len(items),
                }
        except Exception as e:
            return {"status": "error", "platform": config["name"], "error": str(e)}

    async def fetch_orders(
        self,
        platform: str,
        store_id: str,
        since_hours: int = 24,
    ) -> dict:
        """
        Pull recent QC orders to feed into demand forecasting.

        Returns order data that can be ingested into the Prophet model.
        """
        if platform not in self.PLATFORMS:
            return {"status": "error", "message": f"Unknown platform: {platform}"}

        config = self.PLATFORMS[platform]
        api_key = self.api_keys.get(platform)

        if not api_key:
            # Stub: generate sample QC order data
            import random
            sample_orders = [
                {
                    "order_id": f"QC-{random.randint(10000, 99999)}",
                    "platform": config["name"],
                    "sku_id": f"SKU{random.randint(1, 20):03d}",
                    "quantity": random.randint(1, 5),
                    "price_inr": round(random.uniform(20, 500), 0),
                    "ordered_at": datetime.now().isoformat(),
                    "delivery_minutes": random.choice([10, 15, 20, 30]),
                }
                for _ in range(random.randint(5, 15))
            ]
            return {
                "status": "stub",
                "platform": config["name"],
                "store_id": store_id,
                "orders": sample_orders,
                "total_orders": len(sample_orders),
                "message": "Stub data. Set API key for real orders.",
            }

        # Real API call
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{config['base_url']}{config['orders_endpoint']}",
                    headers={"Authorization": f"Bearer {api_key}"},
                    params={"store_id": store_id, "since_hours": since_hours},
                )
                return {
                    "status": "fetched",
                    "platform": config["name"],
                    "orders": response.json().get("orders", []),
                }
        except Exception as e:
            return {"status": "error", "platform": config["name"], "error": str(e)}

    def get_supported_platforms(self) -> list[dict]:
        """List all supported QC platforms with connection status."""
        return [
            {
                "key": key,
                "name": config["name"],
                "connected": key in self.api_keys,
                "base_url": config["base_url"],
            }
            for key, config in self.PLATFORMS.items()
        ]


# Singleton
qcommerce = QuickCommerceHub()
