"""Immutable, atomically written model artifacts and audit records."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .database import ExperienceDatabase


@dataclass(frozen=True)
class ModelVersion:
    version: str
    parent_version: str | None
    path: Path
    experience_count: int
    metrics: dict[str, float]
    promoted: bool
    created_at: str


class ModelManager:
    def __init__(self, model_root: str | Path, database: ExperienceDatabase) -> None:
        self.model_root = Path(model_root)
        self.model_root.mkdir(parents=True, exist_ok=True)
        self.database = database

    def create_version(self, state: dict[str, object], *, experience_count: int, metrics: dict[str, float], promote: bool) -> ModelVersion:
        parent = self.database.latest_model_version()
        next_number = int(parent.split("_")[-1]) + 1 if parent else 1
        version = f"model_{next_number:06d}"
        path = self.model_root / f"{version}.json"
        temporary = path.with_suffix(".tmp")
        payload = {"version": version, "parent_version": parent, "state": state, "experience_count": experience_count, "metrics": metrics}
        temporary.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        os.replace(temporary, path)
        created_at = datetime.now(timezone.utc).isoformat()
        self.database.record_model(version=version, parent_version=parent, path=str(path), experience_count=experience_count, metrics=metrics, promoted=promote, created_at=created_at)
        return ModelVersion(version, parent, path, experience_count, metrics, promote, created_at)

    def load_state(self, version: str) -> dict[str, object]:
        payload = json.loads(Path(self.database.model_path(version)).read_text(encoding="utf-8"))
        if payload.get("version") != version:
            raise ValueError("model artifact version mismatch")
        return dict(payload["state"])
