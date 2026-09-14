"""Read-only dashboard snapshot builder."""

from __future__ import annotations

from learning.database import ExperienceDatabase


def snapshot(database: ExperienceDatabase) -> dict[str, object]:
    attempts = database.count_experiences()
    successes = int(database.connection.execute("SELECT COUNT(*) FROM successes").fetchone()[0])
    return {"attempt_count": attempts, "success_count": successes, "experience_count": attempts, "model_version": database.latest_model_version(), "status": "OBSERVATIONAL"}


def html(snapshot_data: dict[str, object]) -> str:
    rows = "".join(f"<tr><th>{key}</th><td>{value}</td></tr>" for key, value in snapshot_data.items())
    return f"<!doctype html><title>Cryptoanalysis V3</title><h1>Cryptoanalysis V3</h1><p>Dashboard is observational; cryptographic truth remains in the evaluator.</p><table>{rows}</table>"
