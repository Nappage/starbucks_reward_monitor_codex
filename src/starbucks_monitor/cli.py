from __future__ import annotations

import argparse
import sys

from .monitor import (
    DEFAULT_PRODUCTS,
    DEFAULT_URL,
    fetch_html,
    fetch_rendered_html,
    format_log_line,
    parse_stock_statuses,
    parse_stock_statuses_rendered,
    run_monitor,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Starbucks reward stock monitor")
    parser.add_argument("--url", default=DEFAULT_URL, help="Target page URL")
    parser.add_argument(
        "--product",
        action="append",
        dest="products",
        help="Product name to monitor (repeatable). If omitted, defaults are used.",
    )
    parser.add_argument(
        "--mode",
        choices=["static", "rendered"],
        default="static",
        help=(
            "static: parse fetched HTML text only. "
            "rendered: run browser rendering (Playwright) then parse DOM visibility."
        ),
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    products = args.products or DEFAULT_PRODUCTS

    fetcher = fetch_html if args.mode == "static" else fetch_rendered_html
    status_parser = parse_stock_statuses if args.mode == "static" else parse_stock_statuses_rendered

    try:
        records = run_monitor(url=args.url, products=products, fetcher=fetcher, parser=status_parser)
    except Exception as exc:  # CLI boundary
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    for record in records:
        print(format_log_line(record))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
