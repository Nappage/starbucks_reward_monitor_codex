from __future__ import annotations

import re
from datetime import datetime
from html.parser import HTMLParser
from typing import Callable
from urllib.request import Request, urlopen

DEFAULT_URL = "https://www.starbucks.co.jp/mystarbucks/reward/exchange/original_goods/"
DEFAULT_PRODUCTS = ["スターマグ ブラウン 296ml", "スターマグ グリーン 296ml"]

OUT_OF_STOCK_KEYWORDS = ["在庫なし", "在庫切れ", "欠品", "SOLD OUT"]
IN_STOCK_KEYWORDS = ["在庫あり", "交換可能"]


class _BlockTextExtractor(HTMLParser):
    TARGET_TAGS = {"section", "div", "li", "article"}

    def __init__(self) -> None:
        super().__init__()
        self._stack: list[tuple[str, list[str]]] = []
        self.blocks: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:  # noqa: ARG002
        if tag in self.TARGET_TAGS:
            self._stack.append((tag, []))

    def handle_data(self, data: str) -> None:
        for _, fragments in self._stack:
            fragments.append(data)

    def handle_endtag(self, tag: str) -> None:
        if not self._stack:
            return
        current_tag, fragments = self._stack[-1]
        if tag == current_tag:
            self._stack.pop()
            text = " ".join(fragment.strip() for fragment in fragments if fragment.strip())
            if text:
                self.blocks.append(text)


def fetch_html(url: str, timeout: int = 20) -> str:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 (stock-monitor-bot)"})
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="ignore")


def fetch_rendered_html(url: str, timeout_ms: int = 30_000) -> str:
    """Fetch browser-rendered HTML via Playwright.

    This mode is needed for pages where stock state is finalized in client-side JavaScript.
    """

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:  # pragma: no cover - depends on runtime env
        raise RuntimeError(
            "Rendered mode requires playwright. Install with: pip install playwright "
            "&& playwright install chromium"
        ) from exc

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        try:
            page.goto(url, wait_until="networkidle", timeout=timeout_ms)
            return page.content()
        finally:
            browser.close()


def _extract_product_context(html: str, product: str, window: int = 120) -> str | None:
    if product not in html:
        return None

    parser = _BlockTextExtractor()
    parser.feed(html)
    for block in parser.blocks:
        if product in block:
            return block

    idx = html.find(product)
    start = max(0, idx - window)
    end = min(len(html), idx + len(product) + window)
    return html[start:end]


def parse_stock_statuses(html: str, products: list[str], window: int = 120) -> dict[str, str]:
    results: dict[str, str] = {}
    for product in products:
        context = _extract_product_context(html, product, window=window)
        if context is None:
            results[product] = "NOT_FOUND"
            continue

        if any(keyword in context for keyword in OUT_OF_STOCK_KEYWORDS):
            results[product] = "OUT_OF_STOCK"
        elif any(keyword in context for keyword in IN_STOCK_KEYWORDS):
            results[product] = "IN_STOCK"
        else:
            results[product] = "UNKNOWN"
    return results


def parse_stock_statuses_rendered(html: str, products: list[str]) -> dict[str, str]:
    """Parse status from rendered DOM button visibility classes.

    Uses `button.js-cartform-instock[data-name="..."]` and sibling out-of-stock buttons.
    """

    results: dict[str, str] = {}
    for product in products:
        name = re.escape(product)
        instock_pattern = re.compile(
            rf'<button[^>]*class="(?P<class>[^"]*js-cartform-instock[^"]*)"[^>]*data-name="{name}"[^>]*>',
            re.IGNORECASE,
        )
        instock_match = instock_pattern.search(html)
        if not instock_match:
            results[product] = "NOT_FOUND"
            continue

        form_start = html.rfind("<form", 0, instock_match.start())
        form_end = html.find("</form>", instock_match.end())
        if form_start == -1 or form_end == -1:
            results[product] = "UNKNOWN"
            continue

        form_html = html[form_start : form_end + len("</form>")]
        instock_hidden = "js-cartform-instock hide" in form_html
        out_hidden = "js-cartform-outofstock hide" in form_html
        disable_hidden = "js-cartform-disable hide" in form_html

        if not instock_hidden and out_hidden:
            results[product] = "IN_STOCK"
        elif instock_hidden and (not out_hidden or not disable_hidden):
            results[product] = "OUT_OF_STOCK"
        else:
            # Fallback for ambiguous markup
            if "在庫切れ" in form_html and "交換に進む" not in form_html:
                results[product] = "OUT_OF_STOCK"
            elif "交換に進む" in form_html and "在庫切れ" not in form_html:
                results[product] = "IN_STOCK"
            else:
                results[product] = "UNKNOWN"
    return results


def run_monitor(
    url: str,
    products: list[str],
    fetcher: Callable[[str], str] = fetch_html,
    parser: Callable[[str, list[str]], dict[str, str]] = parse_stock_statuses,
    now_fn: Callable[[], datetime] = datetime.now,
) -> list[dict[str, str]]:
    html = fetcher(url)
    statuses = parser(html, products)
    timestamp = now_fn().replace(microsecond=0).isoformat()
    records: list[dict[str, str]] = []
    for product in products:
        records.append(
            {
                "timestamp": timestamp,
                "product": product,
                "status": statuses[product],
            }
        )
    return records


def format_log_line(record: dict[str, str]) -> str:
    return f"{record['timestamp']}\t{record['product']}\t{record['status']}"
