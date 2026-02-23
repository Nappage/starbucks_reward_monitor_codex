import unittest
from datetime import datetime

from starbucks_monitor.monitor import format_log_line, run_monitor


class MonitorBehaviorTest(unittest.TestCase):
    def test_run_monitor_returns_timestamped_records(self):
        def fake_fetcher(_url: str) -> str:
            return "<div>スターマグ ブラウン 296ml 在庫なし</div><div>スターマグ グリーン 296ml 在庫あり</div>"

        fixed_time = datetime(2026, 1, 1, 12, 34, 56)
        records = run_monitor(
            url="https://example.com",
            products=["スターマグ ブラウン 296ml", "スターマグ グリーン 296ml"],
            fetcher=fake_fetcher,
            now_fn=lambda: fixed_time,
        )

        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["timestamp"], "2026-01-01T12:34:56")
        self.assertEqual(records[0]["product"], "スターマグ ブラウン 296ml")
        self.assertEqual(records[0]["status"], "OUT_OF_STOCK")
        self.assertEqual(records[1]["status"], "IN_STOCK")

    def test_run_monitor_accepts_custom_parser(self):
        def fake_fetcher(_url: str) -> str:
            return "<html>...</html>"

        def fake_parser(_html: str, products: list[str]) -> dict[str, str]:
            return {products[0]: "OUT_OF_STOCK", products[1]: "OUT_OF_STOCK"}

        records = run_monitor(
            url="https://example.com",
            products=["A", "B"],
            fetcher=fake_fetcher,
            parser=fake_parser,
            now_fn=lambda: datetime(2026, 1, 1, 0, 0, 0),
        )
        self.assertEqual([r["status"] for r in records], ["OUT_OF_STOCK", "OUT_OF_STOCK"])

    def test_format_log_line(self):
        line = format_log_line(
            {
                "timestamp": "2026-01-01T12:34:56",
                "product": "スターマグ ブラウン 296ml",
                "status": "OUT_OF_STOCK",
            }
        )
        self.assertEqual(
            line,
            "2026-01-01T12:34:56\tスターマグ ブラウン 296ml\tOUT_OF_STOCK",
        )


if __name__ == "__main__":
    unittest.main()
