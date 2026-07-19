from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from urllib.request import Request, urlopen

BLUESKY_MAX_GRAPHEMES = 300


def build_restock_message(events: list[dict[str, str]]) -> str:
    lines = ["[Starbucks Reward Monitor] Restock detected"]
    for event in events:
        lines.append(f"- {event['product']}: {event['previous_status']} -> {event['current_status']}")
    return "\n".join(lines)


def build_status_snapshot_message(records: list[dict[str, str]]) -> str:
    lines = ["[Starbucks Reward Monitor] Test notification (current statuses)"]
    for record in records:
        lines.append(f"- {record['product']}: {record['status']}")
    return "\n".join(lines)


def truncate_for_bluesky(message: str, limit: int = BLUESKY_MAX_GRAPHEMES) -> str:
    if len(message) <= limit:
        return message
    ellipsis = "…"
    return message[: limit - len(ellipsis)] + ellipsis


def _default_json_request_sender(request: Request) -> dict:
    with urlopen(request, timeout=20) as response:
        payload = response.read()
        if not payload:
            return {}
        return json.loads(payload.decode("utf-8"))


class BlueskyNotifier:
    """Posts stock status messages to Bluesky via the AT Protocol.

    Auth flow: `com.atproto.server.createSession` (identifier + app password)
    to obtain an access token, then `com.atproto.repo.createRecord` to create
    an `app.bsky.feed.post` record.
    """

    def __init__(
        self,
        identifier: str,
        app_password: str,
        service: str = "https://bsky.social",
        request_sender: Callable[[Request], dict] = _default_json_request_sender,
        now_fn: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        self.identifier = identifier
        self.app_password = app_password
        self.service = service.rstrip("/")
        self.request_sender = request_sender
        self.now_fn = now_fn

    def send(self, message: str) -> None:
        session = self._create_session()
        self._create_post(session, message)

    def _create_session(self) -> dict:
        endpoint = f"{self.service}/xrpc/com.atproto.server.createSession"
        body = json.dumps({"identifier": self.identifier, "password": self.app_password}).encode("utf-8")
        request = Request(
            endpoint,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        return self.request_sender(request)

    def _create_post(self, session: dict, message: str) -> None:
        endpoint = f"{self.service}/xrpc/com.atproto.repo.createRecord"
        created_at = self.now_fn().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        record = {
            "$type": "app.bsky.feed.post",
            "text": truncate_for_bluesky(message),
            "createdAt": created_at,
        }
        body = json.dumps(
            {
                "repo": session["did"],
                "collection": "app.bsky.feed.post",
                "record": record,
            }
        ).encode("utf-8")
        request = Request(
            endpoint,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {session['accessJwt']}",
            },
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
