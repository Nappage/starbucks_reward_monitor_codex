import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from starbucks_monitor.notify import (
    BLUESKY_MAX_GRAPHEMES,
    BlueskyNotifier,
    NotificationHistoryStore,
    build_restock_message,
    build_status_snapshot_message,
    truncate_for_bluesky,
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

    def test_bluesky_notifier_creates_session_then_posts_record(self):
        calls: list[dict] = []

        def fake_sender(request):
            body = json.loads(request.data.decode("utf-8"))
            calls.append(
                {
                    "url": request.full_url,
                    "method": request.get_method(),
                    "headers": dict(request.header_items()),
                    "body": body,
                }
            )
            if request.full_url.endswith("/xrpc/com.atproto.server.createSession"):
                return {"did": "did:plc:example", "accessJwt": "JWT"}
            return {"uri": "at://did:plc:example/app.bsky.feed.post/abc"}

        notifier = BlueskyNotifier(
            "user.bsky.social",
            "app-password",
            request_sender=fake_sender,
            now_fn=lambda: datetime(2026, 7, 19, 12, 0, 0, tzinfo=timezone.utc),
        )
        notifier.send("hello")

        self.assertEqual(len(calls), 2)

        session_call = calls[0]
        self.assertEqual(session_call["method"], "POST")
        self.assertEqual(session_call["url"], "https://bsky.social/xrpc/com.atproto.server.createSession")
        self.assertEqual(session_call["body"], {"identifier": "user.bsky.social", "password": "app-password"})

        post_call = calls[1]
        self.assertEqual(post_call["method"], "POST")
        self.assertEqual(post_call["url"], "https://bsky.social/xrpc/com.atproto.repo.createRecord")
        self.assertEqual(post_call["headers"]["Authorization"], "Bearer JWT")
        self.assertEqual(post_call["body"]["repo"], "did:plc:example")
        self.assertEqual(post_call["body"]["collection"], "app.bsky.feed.post")
        self.assertEqual(post_call["body"]["record"]["text"], "hello")
        self.assertEqual(post_call["body"]["record"]["$type"], "app.bsky.feed.post")
        self.assertEqual(post_call["body"]["record"]["createdAt"], "2026-07-19T12:00:00.000Z")

    def test_truncate_for_bluesky_keeps_short_message_untouched(self):
        message = "short message"
        self.assertEqual(truncate_for_bluesky(message), message)

    def test_truncate_for_bluesky_truncates_long_message(self):
        message = "x" * (BLUESKY_MAX_GRAPHEMES + 50)
        result = truncate_for_bluesky(message)
        self.assertEqual(len(result), BLUESKY_MAX_GRAPHEMES)
        self.assertTrue(result.endswith("…"))

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
