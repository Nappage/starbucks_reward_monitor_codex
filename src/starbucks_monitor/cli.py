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
from .notify import TelegramNotifier
from .workflow import process_records


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
    parser.add_argument(
        "--state-file",
        default=".starbucks_monitor_state.json",
        help="Path to JSON file storing latest statuses for diff detection.",
    )
    parser.add_argument(
        "--notification-history-file",
        default=".starbucks_monitor_notifications.json",
        help="Path to JSON file storing sent notification event ids (dedupe).",
    )
    parser.add_argument(
        "--telegram-bot-token",
        default=None,
        help="Telegram bot token. If set with --telegram-chat-id, restock events are notified.",
    )
    parser.add_argument(
        "--telegram-chat-id",
        default=None,
        help="Telegram chat id for restock notifications.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    products = args.products or DEFAULT_PRODUCTS

    fetcher = fetch_html if args.mode == "static" else fetch_rendered_html
    status_parser = parse_stock_statuses if args.mode == "static" else parse_stock_statuses_rendered

    notifier = None
    if args.telegram_bot_token or args.telegram_chat_id:
        if not args.telegram_bot_token or not args.telegram_chat_id:
            print(
                "ERROR: both --telegram-bot-token and --telegram-chat-id are required for Telegram notifications",
                file=sys.stderr,
            )
            return 1
        notifier = TelegramNotifier(args.telegram_bot_token, args.telegram_chat_id)

    try:
        records = run_monitor(url=args.url, products=products, fetcher=fetcher, parser=status_parser)
        summary = process_records(
            records,
            state_file=args.state_file,
            notification_history_file=args.notification_history_file,
            notifier=notifier,
        )
    except Exception as exc:  # CLI boundary
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    for record in records:
        print(format_log_line(record))

    print(
        f"SUMMARY\tchanges={summary['changes']}\trestocks={summary['restocks']}"
        f"\tnotifications_sent={summary['notifications_sent']}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
