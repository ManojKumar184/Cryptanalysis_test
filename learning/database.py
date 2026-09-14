"""Transactional SQLite archive; committed attempts are never partial."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .experience import Experience


class DuplicateExperienceError(ValueError):
    pass


class ExperienceDatabase:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.execute("PRAGMA journal_mode = WAL")
        self._create_schema()

    def close(self) -> None:
        self.connection.close()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        try:
            self.connection.execute("BEGIN IMMEDIATE")
            yield self.connection
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def _create_schema(self) -> None:
        self.connection.executescript("""
            CREATE TABLE IF NOT EXISTS candidates (
                candidate_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS attempts (
                id INTEGER PRIMARY KEY,
                candidate_id TEXT NOT NULL,
                modified_candidate_id TEXT NOT NULL UNIQUE,
                attempt_index INTEGER NOT NULL,
                modification_json TEXT NOT NULL,
                model_version TEXT,
                score REAL,
                digest_hex TEXT NOT NULL,
                target_hex TEXT NOT NULL,
                success INTEGER NOT NULL CHECK (success IN (0, 1)),
                trace_reference TEXT,
                difference_reference TEXT,
                feature_json TEXT,
                timings_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(candidate_id, attempt_index)
            );
            CREATE TABLE IF NOT EXISTS successes (
                attempt_id INTEGER PRIMARY KEY REFERENCES attempts(id),
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS models (
                version TEXT PRIMARY KEY,
                parent_version TEXT,
                path TEXT NOT NULL UNIQUE,
                experience_count INTEGER NOT NULL,
                metrics_json TEXT NOT NULL,
                promoted INTEGER NOT NULL CHECK (promoted IN (0, 1)),
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS training_runs (
                id INTEGER PRIMARY KEY,
                model_version TEXT,
                experience_count INTEGER NOT NULL,
                metrics_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS checkpoints (
                checkpoint_id TEXT PRIMARY KEY,
                path TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY,
                event_type TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                value REAL NOT NULL,
                created_at TEXT NOT NULL
            );
        """)
        columns = {row[1] for row in self.connection.execute("PRAGMA table_info(attempts)")}
        if "feature_json" not in columns:
            self.connection.execute("ALTER TABLE attempts ADD COLUMN feature_json TEXT")
        self.connection.commit()

    def commit_experience(self, experience: Experience) -> int:
        row = experience.to_row()
        try:
            with self.transaction() as connection:
                connection.execute("INSERT OR IGNORE INTO candidates(candidate_id, created_at) VALUES (?, ?)", (experience.candidate_id, experience.timestamp))
                cursor = connection.execute(
                    """INSERT INTO attempts(candidate_id, modified_candidate_id, attempt_index, modification_json, model_version, score, digest_hex, target_hex, success, trace_reference, difference_reference, feature_json, timings_json, created_at)
                    VALUES (:candidate_id, :modified_candidate_id, :attempt_index, :modification_json, :model_version, :score, :digest_hex, :target_hex, :success, :trace_reference, :difference_reference, :feature_json, :timings_json, :created_at)""",
                    {
                        "candidate_id": row["candidate_id"], "modified_candidate_id": row["modified_candidate_id"], "attempt_index": row["attempt_index"],
                        "modification_json": json.dumps(row["modification"], sort_keys=True), "model_version": row["model_version"], "score": row["score"],
                        "digest_hex": row["digest"], "target_hex": row["target_hex"], "success": int(row["success"]), "trace_reference": row["trace_reference"],
                        "difference_reference": row["difference_reference"], "timings_json": json.dumps(row["timings_ns"], sort_keys=True), "created_at": row["timestamp"],
                        "feature_json": json.dumps(row["feature_vector"]) if row["feature_vector"] is not None else None,
                    },
                )
                attempt_id = int(cursor.lastrowid)
                if experience.success:
                    connection.execute("INSERT INTO successes(attempt_id, created_at) VALUES (?, ?)", (attempt_id, experience.timestamp))
                return attempt_id
        except sqlite3.IntegrityError as error:
            raise DuplicateExperienceError("attempt is already durably committed") from error

    def experiences(self) -> list[sqlite3.Row]:
        return list(self.connection.execute("SELECT * FROM attempts ORDER BY id"))

    def count_experiences(self) -> int:
        return int(self.connection.execute("SELECT COUNT(*) FROM attempts").fetchone()[0])

    def record_model(self, *, version: str, parent_version: str | None, path: str, experience_count: int, metrics: dict[str, float], promoted: bool, created_at: str) -> None:
        with self.transaction() as connection:
            connection.execute("INSERT INTO models VALUES (?, ?, ?, ?, ?, ?, ?)", (version, parent_version, path, experience_count, json.dumps(metrics, sort_keys=True), int(promoted), created_at))

    def latest_model_version(self) -> str | None:
        row = self.connection.execute("SELECT version FROM models ORDER BY version DESC LIMIT 1").fetchone()
        return row[0] if row else None

    def model_path(self, version: str) -> str:
        row = self.connection.execute("SELECT path FROM models WHERE version = ?", (version,)).fetchone()
        if row is None:
            raise KeyError(f"unknown model version {version}")
        return str(row[0])

    def modified_candidate_ids(self, candidate_id: str) -> list[str]:
        return [str(row[0]) for row in self.connection.execute("SELECT modified_candidate_id FROM attempts WHERE candidate_id = ?", (candidate_id,))]
