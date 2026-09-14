"""Outcome-blind scoring interface for ordering legal modifications."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from core.block import Candidate
from core.modifications import Modification


@dataclass
class RankingModel:
    """A trainable logistic ranker over outcome-blind structural features.

    This intentionally modest model is a research instrument, not evidence of
    a SHA-256d weakness.  The trainer updates it only from committed records.
    """

    weights: list[float] = field(default_factory=list)
    bias: float = 0.0

    def probability(self, state_features: tuple[float, ...]) -> float:
        if not self.weights:
            self.weights = [0.0] * len(state_features)
        if len(self.weights) != len(state_features):
            raise ValueError("model feature dimension changed")
        logit = self.bias + sum(weight * value for weight, value in zip(self.weights, state_features))
        return 1.0 / (1.0 + math.exp(-max(-60.0, min(60.0, logit))))

    def score(self, candidate: Candidate, modification: Modification, mechanism_embedding: tuple[float, ...], state_features: tuple[float, ...], historical_signal: float = 0.0) -> float:
        if modification.before != candidate.mutable.as_dict()[modification.field]:
            raise ValueError("modification does not describe the supplied candidate")
        # The score intentionally excludes digest, target, and outcome data.
        return self.probability(state_features)

    def train_one(self, state_features: tuple[float, ...], outcome: bool, learning_rate: float) -> float:
        prediction = self.probability(state_features)
        label = float(outcome)
        error = prediction - label
        self.weights = [weight - learning_rate * error * value for weight, value in zip(self.weights, state_features)]
        self.bias -= learning_rate * error
        return -(label * math.log(max(prediction, 1e-12)) + (1.0 - label) * math.log(max(1.0 - prediction, 1e-12)))

    def state_dict(self) -> dict[str, object]:
        return {"weights": list(self.weights), "bias": self.bias}

    @classmethod
    def from_state_dict(cls, state: dict[str, object]) -> "RankingModel":
        return cls([float(value) for value in state.get("weights", [])], float(state.get("bias", 0.0)))
