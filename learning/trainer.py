"""Continual-update bookkeeping; outcomes become available only after commit."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .database import ExperienceDatabase
from .model_manager import ModelManager, ModelVersion
from .replay import ReplaySampler


@dataclass(frozen=True)
class TrainingResult:
    model: ModelVersion
    replay_count: int
    success_rate: float


class ContinualTrainer:
    def update(self, database: ExperienceDatabase, manager: ModelManager, batch_size: int) -> TrainingResult:
        replay = ReplaySampler().sample(database, batch_size)
        if not replay:
            raise ValueError("cannot update a model without committed experience")
        success_rate = sum(row["success"] for row in replay) / len(replay)
        model = manager.create_version({"replay_count": len(replay), "observed_success_rate": success_rate}, experience_count=database.count_experiences(), metrics={"replay_success_rate": success_rate}, promote=True)
        database.connection.execute("INSERT INTO training_runs(model_version, experience_count, metrics_json, created_at) VALUES (?, ?, ?, ?)", (model.version, database.count_experiences(), '{"replay_success_rate": ' + str(success_rate) + '}', datetime.now(timezone.utc).isoformat()))
        database.connection.commit()
        return TrainingResult(model, len(replay), success_rate)
