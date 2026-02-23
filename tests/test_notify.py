import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs

from starbucks_monitor.notify import (
    NotificationHistoryStore,
    TelegramNotifier,
    build_restock_message,
    build_status_snapshot_message,
)


class NotifyTest(unittest.TestCase):
    def test_build_restock_message(self):
        events = [{"product": "A", "previous_status": "OUT_OF_STOCK", "current_status": "IN_STOCK"}]
        msg = build_restock_message(events)
        self.assertIn("Restock detected", msg)
        self.assertIn("A: OUT_OF_STOCK -> IN_STOCK", msg)

    def test_build_status_snapshot_message(self):
        records = [
            {"product": "A", "status": "OUT_OF_STOCK"},
            {"product": "B", "status": "IN_STOCK"},
        ]
        msg = build_status_snapshot_message(records)
        self.assertIn("Test notification", msg)
        self.assertIn("A: OUT_OF_STOCK", msg)
        self.assertIn("B: IN_STOCK", msg)

    def test_telegram_notifier_posts_form_payload(self):
        captured: dict[str, str] = {}

        def fake_sender(request):
            captured["url"] = request.full_url
            captured["method"] = request.get_method()
            captured["body"] = request.data.decode("utf-8")

        notifier = TelegramNotifier("TOKEN", "12345", request_sender=fake_sender)
        notifier.send("hello")

        self.assertEqual(captured["method"], "POST")
        self.assertEqual(captured["url"], "https://api.telegram.org/botTOKEN/sendMessage")
        body = parse_qs(captured["body"])
        self.assertEqual(body["chat_id"], ["12345"])
        self.assertEqual(body["text"], ["hello"])

    def test_notification_history_dedup(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "history.json")
            store = NotificationHistoryStore(path)
            events = [{"product": "A", "previous_status": "OUT_OF_STOCK", "current_status": "IN_STOCK"}]

            self.assertEqual(store.filter_unsent_events(events), events)
            store.mark_sent(events)
            self.assertEqual(store.filter_unsent_events(events), [])


if __name__ == "__main__":
    unittest.main()
