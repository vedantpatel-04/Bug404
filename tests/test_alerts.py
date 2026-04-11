"""Tests for alert system."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unittest
from alerts.alert_models import Alert, AlertType, SUGGESTED_ACTIONS
from alerts.alert_manager import AlertManager
from alerts.redis_publisher import RedisPublisher, InMemoryPubSub
from alerts.notification_channels import DashboardNotifier, NotificationRouter


class TestAlertModels(unittest.TestCase):
    """Tests for alert data models."""

    def test_alert_creation(self):
        alert = Alert(
            alert_type="STOCKOUT",
            severity=5,
            store_id="STORE01",
            message="Test alert",
        )
        self.assertEqual(alert.alert_type, "STOCKOUT")
        self.assertEqual(alert.severity, 5)

    def test_alert_to_dict(self):
        alert = Alert(alert_type="LOW_STOCK", severity=3, store_id="STORE01", message="Low stock")
        d = alert.to_dict()
        self.assertIsInstance(d, dict)
        self.assertEqual(d["alert_type"], "LOW_STOCK")

    def test_alert_from_dict(self):
        data = {"alert_type": "STOCKOUT", "severity": 5, "store_id": "STORE01", "message": "Test"}
        alert = Alert.from_dict(data)
        self.assertEqual(alert.alert_type, "STOCKOUT")

    def test_suggested_actions(self):
        self.assertIn("STOCKOUT", SUGGESTED_ACTIONS)
        self.assertGreater(len(SUGGESTED_ACTIONS["STOCKOUT"]), 0)


class TestAlertManager(unittest.TestCase):
    """Tests for the AlertManager."""

    def setUp(self):
        self.manager = AlertManager()

    def test_create_alert(self):
        alert = self.manager.create_alert(
            alert_type="STOCKOUT",
            store_id="STORE01",
            message="Product out of stock",
            revenue_impact=150,
        )
        self.assertIsNotNone(alert)
        self.assertEqual(alert.alert_type, "STOCKOUT")
        self.assertGreater(alert.priority_score, 0)

    def test_dedup_suppression(self):
        """Duplicate alerts within cooldown should be suppressed."""
        alert1 = self.manager.create_alert("STOCKOUT", "STORE01", "Test", sku_id="SKU001")
        alert2 = self.manager.create_alert("STOCKOUT", "STORE01", "Test", sku_id="SKU001")
        self.assertIsNotNone(alert1)
        self.assertIsNone(alert2)  # Should be suppressed

    def test_different_alerts_not_suppressed(self):
        """Different alerts should not be suppressed."""
        alert1 = self.manager.create_alert("STOCKOUT", "STORE01", "Test1", sku_id="SKU001")
        alert2 = self.manager.create_alert("STOCKOUT", "STORE01", "Test2", sku_id="SKU002")
        self.assertIsNotNone(alert1)
        self.assertIsNotNone(alert2)

    def test_prioritize_alerts(self):
        alerts = self.manager.generate_sample_alerts("STORE01", 5)
        self.assertEqual(len(alerts), 5)
        # Should be sorted by priority score
        for i in range(len(alerts) - 1):
            self.assertGreaterEqual(alerts[i].priority_score, alerts[i + 1].priority_score)


class TestInMemoryPubSub(unittest.TestCase):
    """Tests for in-memory pub/sub fallback."""

    def test_publish_and_get(self):
        pubsub = InMemoryPubSub()
        pubsub.publish("test_channel", '{"message": "hello"}')
        messages = pubsub.get_messages("test_channel")
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["data"], '{"message": "hello"}')

    def test_subscriber_callback(self):
        pubsub = InMemoryPubSub()
        received = []
        pubsub.subscribe("test", lambda msg: received.append(msg))
        pubsub.publish("test", "message1")
        self.assertEqual(len(received), 1)

    def test_max_messages(self):
        pubsub = InMemoryPubSub()
        for i in range(1100):
            pubsub.publish("test", f"msg_{i}")
        messages = pubsub.get_messages("test")
        self.assertLessEqual(len(messages), 1000)


class TestDashboardNotifier(unittest.TestCase):
    """Tests for dashboard notification system."""

    def test_push_notification(self):
        notifier = DashboardNotifier()
        alert = Alert(alert_type="STOCKOUT", severity=5, store_id="STORE01", message="Test")
        result = notifier.push(alert)
        self.assertTrue(result)
        self.assertEqual(notifier.count, 1)

    def test_get_and_clear(self):
        notifier = DashboardNotifier()
        alert = Alert(alert_type="STOCKOUT", severity=5, store_id="STORE01", message="Test")
        notifier.push(alert)
        pending = notifier.get_pending(clear=True)
        self.assertEqual(len(pending), 1)
        self.assertEqual(notifier.count, 0)


class TestRedisPublisher(unittest.TestCase):
    """Tests for Redis publisher."""

    def test_publisher_initialization(self):
        publisher = RedisPublisher()
        status = publisher.get_status()
        self.assertIn("backend", status)
        self.assertIn(status["backend"], ["Redis", "In-Memory"])

    def test_publish_alert(self):
        publisher = RedisPublisher()
        alert = Alert(alert_type="STOCKOUT", severity=5, store_id="STORE01", message="Test")
        result = publisher.publish_alert(alert)
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
