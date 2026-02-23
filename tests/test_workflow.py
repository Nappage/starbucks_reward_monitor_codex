import tempfile
import unittest
from pathlib import Path

from starbucks_monitor.workflow import process_records


class _FakeNotifier:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def send(self, message: str) -> None:
        self.messages.append(message)


class WorkflowTest(unittest.TestCase):
    def test_process_records_detects_restock_and_sends_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_file = str(Path(tmp) / "state.json")
            history_file = str(Path(tmp) / "notify.json")
            notifier = _FakeNotifier()

            out_of_stock_records = [
                {"product": "A", "status": "OUT_OF_STOCK"},
                {"product": "B", "status": "OUT_OF_STOCK"},
            ]
            first = process_records(
                out_of_stock_records,
                state_file=state_file,
                notification_history_file=history_file,
                notifier=notifier,
            )
            self.assertEqual(first["restocks"], 0)
            self.assertEqual(first["notifications_sent"], 0)

            restock_records = [
                {"product": "A", "status": "IN_STOCK"},
                {"product": "B", "status": "OUT_OF_STOCK"},
            ]
            second = process_records(
                restock_records,
                state_file=state_file,
                notification_history_file=history_file,
                notifier=notifier,
            )
            self.assertEqual(second["restocks"], 1)
            self.assertEqual(second["notifications_sent"], 1)
            self.assertEqual(len(notifier.messages), 1)

            third = process_records(
                restock_records,
                state_file=state_file,
                notification_history_file=history_file,
                notifier=notifier,
            )
            self.assertEqual(third["restocks"], 0)
            self.assertEqual(third["notifications_sent"], 0)
            self.assertEqual(len(notifier.messages), 1)


if __name__ == "__main__":
    unittest.main()
