"""Durable operational accounting; no metric changes cryptographic truth."""

from __future__ import annotations

from datetime import datetime, timezone

from learning.database import ExperienceDatabase


class MetricsStore:
    def __init__(self, database: ExperienceDatabase) -> None:
        self.database = database

    def record(self, name: str, value: float) -> None:
        self.database.connection.execute("INSERT INTO metrics(name, value, created_at) VALUES (?, ?, ?)", (name, value, datetime.now(timezone.utc).isoformat()))
        self.database.connection.commit()

    def latest(self) -> dict[str, float]:
        rows = self.database.connection.execute("""SELECT name, value FROM metrics WHERE id IN (SELECT MAX(id) FROM metrics GROUP BY name)""")
        return {row["name"]: row["value"] for row in rows}
