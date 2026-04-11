"""
Redis Pub/Sub publisher with in-memory fallback.
Publishes alerts to Redis channels for real-time consumption.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import time
from datetime import datetime
from collections import deque
from typing import Optional, Callable

from config.settings import REDIS_HOST, REDIS_PORT


class InMemoryPubSub:
    """In-memory Pub/Sub fallback when Redis is unavailable."""

    def __init__(self):
        self.channels = {}  # channel -> deque of messages
        self.subscribers = {}  # channel -> list of callbacks

    def publish(self, channel: str, message: str) -> int:
        if channel not in self.channels:
            self.channels[channel] = deque(maxlen=1000)
        self.channels[channel].append({
            "type": "message",
            "channel": channel,
            "data": message,
            "timestamp": datetime.now().isoformat(),
        })
        # Notify subscribers
        for callback in self.subscribers.get(channel, []):
            try:
                callback(message)
            except Exception:
                pass
        return len(self.subscribers.get(channel, []))

    def subscribe(self, channel: str, callback: Optional[Callable] = None):
        if channel not in self.subscribers:
            self.subscribers[channel] = []
        if callback:
            self.subscribers[channel].append(callback)

    def get_messages(self, channel: str, count: int = 50) -> list:
        msgs = list(self.channels.get(channel, []))
        return msgs[-count:]


class RedisPublisher:
    """
    Publishes alerts to Redis Pub/Sub channels.
    Falls back to in-memory queue if Redis is not available.
    """

    CHANNEL_ALL = "alerts:all"
    CHANNEL_STOCKOUT = "alerts:stockout"
    CHANNEL_PLANOGRAM = "alerts:planogram"
    CHANNEL_PRICE = "alerts:price"

    def __init__(self):
        self.redis_client = None
        self.fallback = InMemoryPubSub()
        self.use_redis = False
        self._connect()

    def _connect(self):
        """Try to connect to Redis."""
        try:
            import redis
            self.redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                decode_responses=True,
                socket_connect_timeout=2,
            )
            self.redis_client.ping()
            self.use_redis = True
            print(f"  ✓ Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
        except Exception:
            self.use_redis = False
            print("  ℹ Redis unavailable — using in-memory pub/sub fallback")

    def publish_alert(self, alert) -> bool:
        """
        Publish an alert to appropriate channels.

        Args:
            alert: Alert object or dict.

        Returns:
            True if published successfully.
        """
        if hasattr(alert, "to_dict"):
            data = alert.to_dict()
        elif isinstance(alert, dict):
            data = alert
        else:
            data = {"message": str(alert)}

        message = json.dumps(data, default=str)

        # Determine channel
        alert_type = data.get("alert_type", "")
        channels = [self.CHANNEL_ALL]
        if "STOCKOUT" in alert_type or "LOW_STOCK" in alert_type:
            channels.append(self.CHANNEL_STOCKOUT)
        elif "PLANOGRAM" in alert_type:
            channels.append(self.CHANNEL_PLANOGRAM)
        elif "PRICE" in alert_type:
            channels.append(self.CHANNEL_PRICE)

        success = True
        for channel in channels:
            try:
                if self.use_redis:
                    self.redis_client.publish(channel, message)
                else:
                    self.fallback.publish(channel, message)
            except Exception as e:
                print(f"  ⚠ Publish error on {channel}: {e}")
                success = False

        return success

    def get_recent_messages(self, channel: str = None, count: int = 50) -> list:
        """Get recent messages from a channel (fallback only)."""
        channel = channel or self.CHANNEL_ALL
        if not self.use_redis:
            return self.fallback.get_messages(channel, count)
        return []

    def subscribe(self, channel: str, callback: Callable):
        """Subscribe to a channel with a callback."""
        if self.use_redis:
            # For Redis, would use pubsub in a thread
            pass
        else:
            self.fallback.subscribe(channel, callback)

    def get_status(self) -> dict:
        """Get publisher status info."""
        return {
            "backend": "Redis" if self.use_redis else "In-Memory",
            "host": f"{REDIS_HOST}:{REDIS_PORT}" if self.use_redis else "local",
            "connected": self.use_redis,
            "channels": [self.CHANNEL_ALL, self.CHANNEL_STOCKOUT, self.CHANNEL_PLANOGRAM, self.CHANNEL_PRICE],
        }


# Singleton instance
publisher = RedisPublisher()
