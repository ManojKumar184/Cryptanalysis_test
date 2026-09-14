"""Explicit recoverable controller transitions; autonomous scheduling comes later."""

from __future__ import annotations

from enum import Enum

from core.block import Candidate, FixedFields, MutableFields
from core.target import Target
from learning.database import ExperienceDatabase
from learning.experience import Experience
from learning.model_manager import ModelManager
from learning.trainer import ContinualTrainer
from persistence.checkpoint import CheckpointManager

from .improvement import ImprovementTracker
from .search import SearchEngine


class ControllerState(str, Enum):
    INITIALIZING = "INITIALIZING"
    RECOVERING = "RECOVERING"
    CREATING_CANDIDATE = "CREATING_CANDIDATE"
    ANALYZING = "ANALYZING"
    GENERATING_MODIFICATION = "GENERATING_MODIFICATION"
    VALIDATING_MODIFICATION = "VALIDATING_MODIFICATION"
    EVALUATING = "EVALUATING"
    RECORDING = "RECORDING"
    LEARNING = "LEARNING"
    CHECKPOINTING = "CHECKPOINTING"
    SUCCESS = "SUCCESS"
    NEXT_CANDIDATE = "NEXT_CANDIDATE"
    PAUSED = "PAUSED"
    ERROR = "ERROR"


class ExperimentController:
    def __init__(self, database: ExperienceDatabase, checkpoints: CheckpointManager, target: Target) -> None:
        self.database, self.checkpoints, self.target = database, checkpoints, target
        self.state = ControllerState.INITIALIZING
        self.current_candidate: Candidate | None = None
        self.attempt_index = 0
        self.improvement = ImprovementTracker()
        self.search = SearchEngine()
        self.models = ModelManager(checkpoints.root.parent / "models", database)
        self.trainer = ContinualTrainer()

    def set_candidate(self, candidate: Candidate) -> None:
        self.current_candidate = candidate
        self.attempt_index = 0
        self.search.validator.register(candidate)
        self.state = ControllerState.ANALYZING

    def restore(self, state: dict[str, object]) -> None:
        """Restore only an integrity-checked checkpoint and reconcile the DB."""
        if int(state["experience_count"]) > self.database.count_experiences():
            raise RuntimeError("checkpoint references experience not present in database")
        raw = state.get("candidate")
        if raw is None:
            self.current_candidate = None
        else:
            fixed = raw["fixed"]
            mutable = raw["mutable"]
            self.current_candidate = Candidate(FixedFields(bytes.fromhex(fixed["previous_block_hash"]), bytes.fromhex(fixed["merkle_root"]), int(fixed["bits"])), MutableFields(int(mutable["version"]), int(mutable["timestamp"]), int(mutable["nonce"])), dict(raw.get("metadata", {})))
            self.search.validator.register(self.current_candidate)
            self.search.register_committed_candidates(self.database.modified_candidate_ids(self.current_candidate.candidate_id))
        self.attempt_index = int(state["attempt_index"])
        self.state = ControllerState(str(state["controller_state"]))
        version = state.get("model_version")
        if version:
            self.search.restore_ranking(self.models.load_state(str(version)))

    def run_one_attempt(self) -> bool:
        if self.current_candidate is None:
            raise RuntimeError("a current candidate is required")
        self.state = ControllerState.GENERATING_MODIFICATION
        result = self.search.attempt(self.current_candidate, self.target, self.attempt_index)
        self.state = ControllerState.RECORDING
        experience = Experience.create(candidate_id=self.current_candidate.candidate_id, modified_candidate_id=result.candidate.candidate_id, attempt_index=self.attempt_index, modification=result.modification, digest=result.evaluation.digest, target_hex=self.target.to_hex(), success=result.evaluation.success, score=result.score, feature_vector=result.state_features, timings_ns={"sha256d": result.evaluation.sha256d_ns, "trace": result.trace_ns, "inference": result.inference_ns})
        self.database.commit_experience(experience)
        self.improvement.record_attempt(trace_ns=result.trace_ns, inference_ns=result.inference_ns)
        self.attempt_index += 1
        self.state = ControllerState.LEARNING
        training_started = __import__("time").perf_counter_ns()
        trained = self.trainer.update(self.database, self.models, self.search.ranking, batch_size=32)
        self.improvement.total_training_ns += __import__("time").perf_counter_ns() - training_started
        self.state = ControllerState.SUCCESS if result.evaluation.success else ControllerState.CHECKPOINTING
        if result.evaluation.success:
            self.improvement.record_success(self.attempt_index)
        self.checkpoint()
        return result.evaluation.success

    def checkpoint(self) -> None:
        candidate = self.current_candidate
        payload = {
            "controller_state": self.state.value,
            "candidate": {
                "fixed": {
                    "previous_block_hash": candidate.fixed.previous_block_hash.hex(),
                    "merkle_root": candidate.fixed.merkle_root.hex(),
                    "bits": candidate.fixed.bits,
                },
                "mutable": candidate.mutable.as_dict(),
                "metadata": dict(candidate.metadata),
            } if candidate else None,
            "attempt_index": self.attempt_index,
            "model_version": self.database.latest_model_version(),
            "experience_count": self.database.count_experiences(),
            "configuration_version": "v3",
        }
        self.checkpoints.create(payload)
