"""Deterministic mixed replay over the complete, unbounded experience archive."""

from __future__ import annotations

from sqlite3 import Row

from .database import ExperienceDatabase


class ReplaySampler:
    def sample(self, database: ExperienceDatabase, batch_size: int) -> list[Row]:
        if batch_size <= 0:
            raise ValueError("batch size is a positive computational parameter")
        rows = database.experiences()
        if len(rows) <= batch_size:
            return rows
        successes = [row for row in rows if row["success"]]
        failures = [row for row in rows if not row["success"]]
        selected: list[Row] = []
        for group in (successes[-1:], failures[-1:], rows[-max(1, batch_size // 3):]):
            for row in group:
                if row not in selected and len(selected) < batch_size:
                    selected.append(row)
        for row in rows:
            if len(selected) >= batch_size:
                break
            if row not in selected:
                selected.append(row)
        return selected
