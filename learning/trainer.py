"""Continual-update bookkeeping; outcomes become available only after commit."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .database import ExperienceDatabase
from .model_manager import ModelManager, ModelVersion
from .replay import ReplaySampler
from models.ranking_model import RankingModel


@dataclass(frozen=True)
class TrainingResult:
    model: ModelVersion
    replay_count: int
    success_rate: float
    loss: float


class ContinualTrainer:
    def update(self, database: ExperienceDatabase, manager: ModelManager, ranking: RankingModel, batch_size: int, learning_rate: float = 0.05) -> TrainingResult:
        replay = ReplaySampler().sample(database, batch_size)
        if not replay:
            raise ValueError("cannot update a model without committed experience")
        usable = [row for row in replay if row["feature_json"]]
        if not usable:
            raise ValueError("committed experience has no outcome-blind feature vectors")
        import json
        losses = [ranking.train_one(tuple(json.loads(row["feature_json"])), bool(row["success"]), learning_rate) for row in usable]
        success_rate = sum(row["success"] for row in usable) / len(usable)
        loss = sum(losses) / len(losses)
        model = manager.create_version({"ranking": ranking.state_dict(), "replay_count": len(usable)}, experience_count=database.count_experiences(), metrics={"replay_success_rate": success_rate, "training_loss": loss}, promote=True)
        database.connection.execute("INSERT INTO training_runs(model_version, experience_count, metrics_json, created_at) VALUES (?, ?, ?, ?)", (model.version, database.count_experiences(), json.dumps({"replay_success_rate": success_rate, "training_loss": loss}), datetime.now(timezone.utc).isoformat()))
        database.connection.commit()
        return TrainingResult(model, len(usable), success_rate, loss)
