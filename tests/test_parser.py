import unittest
from pathlib import Path

from starbucks_monitor.monitor import parse_stock_statuses, parse_stock_statuses_rendered


class ParseStockStatusesTest(unittest.TestCase):
    def test_detects_two_target_products_as_out_of_stock_from_fixture(self):
        html = Path("tests/fixtures/reward_page_sample.html").read_text(encoding="utf-8")
        result = parse_stock_statuses(
            html,
            ["スターマグ ブラウン 296ml", "スターマグ グリーン 296ml"],
        )
        self.assertEqual(result["スターマグ ブラウン 296ml"], "OUT_OF_STOCK")
        self.assertEqual(result["スターマグ グリーン 296ml"], "OUT_OF_STOCK")

    def test_handles_in_stock_unknown_and_not_found(self):
        html = """
        <div>スターマグ ブラウン 296ml ... 交換可能</div>
        <div>スターマグ グリーン 296ml ... 状態表示なし</div>
        """
        result = parse_stock_statuses(
            html,
            [
                "スターマグ ブラウン 296ml",
                "スターマグ グリーン 296ml",
                "スターマグ ブラック 296ml",
            ],
        )
        self.assertEqual(result["スターマグ ブラウン 296ml"], "IN_STOCK")
        self.assertEqual(result["スターマグ グリーン 296ml"], "UNKNOWN")
        self.assertEqual(result["スターマグ ブラック 296ml"], "NOT_FOUND")

    def test_parse_rendered_status_from_button_visibility(self):
        html = """
        <form class="js-cartform" data-jan="1">
          <button class="exchange-btn js-cartform-instock hide" data-name="スターマグ ブラウン 296ml">交換に進む</button>
          <button class="exchange-btn soldOut-btn js-cartform-outofstock">在庫切れ</button>
          <button class="exchange-btn soldOut-btn js-cartform-disable hide">在庫切れ</button>
        </form>
        <form class="js-cartform" data-jan="2">
          <button class="exchange-btn js-cartform-instock" data-name="スターマグ グリーン 296ml">交換に進む</button>
          <button class="exchange-btn soldOut-btn js-cartform-outofstock hide">在庫切れ</button>
          <button class="exchange-btn soldOut-btn js-cartform-disable hide">在庫切れ</button>
        </form>
        """
        result = parse_stock_statuses_rendered(
            html,
            ["スターマグ ブラウン 296ml", "スターマグ グリーン 296ml", "未出現商品"],
        )
        self.assertEqual(result["スターマグ ブラウン 296ml"], "OUT_OF_STOCK")
        self.assertEqual(result["スターマグ グリーン 296ml"], "IN_STOCK")
        self.assertEqual(result["未出現商品"], "NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
