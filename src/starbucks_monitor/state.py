from __future__ import annotations

import json
from pathlib import Path


def load_previous_statuses(path: str) -> dict[str, str]:
    file_path = Path(path)
    if not file_path.exists():
        return {}
    payload = json.loads(file_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return {}
    statuses = payload.get("statuses", {})
    if not isinstance(statuses, dict):
        return {}
    return {str(k): str(v) for k, v in statuses.items()}


def save_current_statuses(path: str, records: list[dict[str, str]]) -> None:
    statuses = {record["product"]: record["status"] for record in records}
    payload = {"statuses": statuses}
    Path(path).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def detect_status_changes(previous: dict[str, str], current: dict[str, str]) -> list[dict[str, str]]:
    changes: list[dict[str, str]] = []
    for product, current_status in current.items():
        previous_status = previous.get(product)
        if previous_status != current_status:
            changes.append(
                {
                    "product": product,
                    "previous_status": previous_status or "NONE",
                    "current_status": current_status,
                }
            )
    return changes


def detect_restock_events(changes: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        change
        for change in changes
        if change["previous_status"] == "OUT_OF_STOCK" and change["current_status"] == "IN_STOCK"
    ]
