from __future__ import annotations

import json
from pathlib import Path
from typing import Callable
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def build_restock_message(events: list[dict[str, str]]) -> str:
    lines = ["[Starbucks Reward Monitor] Restock detected"]
    for event in events:
        lines.append(f"- {event['product']}: {event['previous_status']} -> {event['current_status']}")
    return "\n".join(lines)


def _default_request_sender(request: Request) -> None:
    with urlopen(request, timeout=20):
        return


class TelegramNotifier:
    def __init__(
        self,
        bot_token: str,
        chat_id: str,
        request_sender: Callable[[Request], None] = _default_request_sender,
    ) -> None:
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.request_sender = request_sender

    def send(self, message: str) -> None:
        endpoint = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        body = urlencode({"chat_id": self.chat_id, "text": message}).encode("utf-8")
        request = Request(
            endpoint,
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        self.request_sender(request)


class NotificationHistoryStore:
    def __init__(self, path: str) -> None:
        self.path = Path(path)

    def load_ids(self) -> set[str]:
        if not self.path.exists():
            return set()
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return set()
        values = payload.get("sent_event_ids", [])
        if not isinstance(values, list):
            return set()
        return {str(v) for v in values}

    def save_ids(self, ids: set[str]) -> None:
        payload = {"sent_event_ids": sorted(ids)}
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def event_id(event: dict[str, str]) -> str:
        return f"{event['product']}|{event['previous_status']}|{event['current_status']}"

    def filter_unsent_events(self, events: list[dict[str, str]]) -> list[dict[str, str]]:
        sent = self.load_ids()
        return [event for event in events if self.event_id(event) not in sent]

    def mark_sent(self, events: list[dict[str, str]]) -> None:
        sent = self.load_ids()
        for event in events:
            sent.add(self.event_id(event))
        self.save_ids(sent)
