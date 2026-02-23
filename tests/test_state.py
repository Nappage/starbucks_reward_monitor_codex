import json
import tempfile
import unittest
from pathlib import Path

from starbucks_monitor.state import (
    detect_restock_events,
    detect_status_changes,
    load_previous_statuses,
    save_current_statuses,
)


class StateManagementTest(unittest.TestCase):
    def test_load_returns_empty_when_file_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "status.json")
            self.assertEqual(load_previous_statuses(path), {})

    def test_save_and_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "status.json")
            records = [
                {"product": "A", "status": "OUT_OF_STOCK"},
                {"product": "B", "status": "IN_STOCK"},
            ]
            save_current_statuses(path, records)
            loaded = load_previous_statuses(path)
            self.assertEqual(loaded, {"A": "OUT_OF_STOCK", "B": "IN_STOCK"})

            raw = json.loads(Path(path).read_text(encoding="utf-8"))
            self.assertIn("statuses", raw)

    def test_detect_changes_and_restock(self):
        previous = {"A": "OUT_OF_STOCK", "B": "IN_STOCK"}
        current = {"A": "IN_STOCK", "B": "IN_STOCK", "C": "OUT_OF_STOCK"}

        changes = detect_status_changes(previous, current)
        self.assertEqual(len(changes), 2)

        restocks = detect_restock_events(changes)
        self.assertEqual(len(restocks), 1)
        self.assertEqual(restocks[0]["product"], "A")


if __name__ == "__main__":
    unittest.main()
