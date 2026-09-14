"""Structured append-only event log."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping


class EventLogger:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, event_type: str, payload: Mapping[str, object] | None = None) -> None:
        if not event_type.isupper():
            raise ValueError("event names must be uppercase")
        record = {"event_type": event_type, "timestamp": datetime.now(timezone.utc).isoformat(), "payload": dict(payload or {})}
        with self.path.open("a", encoding="utf-8") as output:
            output.write(json.dumps(record, sort_keys=True) + "\n")
