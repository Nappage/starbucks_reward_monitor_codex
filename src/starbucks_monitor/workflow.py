from __future__ import annotations

from typing import Protocol

from .notify import NotificationHistoryStore, build_restock_message
from .state import detect_restock_events, detect_status_changes, load_previous_statuses, save_current_statuses


class Notifier(Protocol):
    def send(self, message: str) -> None: ...


def process_records(
    records: list[dict[str, str]],
    state_file: str,
    notification_history_file: str,
    notifier: Notifier | None = None,
) -> dict[str, int]:
    previous = load_previous_statuses(state_file)
    current = {record["product"]: record["status"] for record in records}
    changes = detect_status_changes(previous, current)
    restocks = detect_restock_events(changes)

    sent_count = 0
    if notifier is not None and restocks:
        history = NotificationHistoryStore(notification_history_file)
        unsent_events = history.filter_unsent_events(restocks)
        if unsent_events:
            notifier.send(build_restock_message(unsent_events))
            history.mark_sent(unsent_events)
            sent_count = len(unsent_events)

    save_current_statuses(state_file, records)

    return {
        "changes": len(changes),
        "restocks": len(restocks),
        "notifications_sent": sent_count,
    }
