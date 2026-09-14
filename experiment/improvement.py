"""Success-to-first-hit statistics, distinct from training loss."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ImprovementTracker:
    attempts_to_success: list[int] = field(default_factory=list)
    total_sha_evaluations: int = 0
    total_trace_ns: int = 0
    total_inference_ns: int = 0
    total_training_ns: int = 0

    def record_attempt(self, *, trace_ns: int = 0, inference_ns: int = 0, training_ns: int = 0) -> None:
        self.total_sha_evaluations += 1
        self.total_trace_ns += trace_ns
        self.total_inference_ns += inference_ns
        self.total_training_ns += training_ns

    def record_success(self, attempts: int) -> None:
        if attempts <= 0:
            raise ValueError("successful candidate must have at least one attempt")
        self.attempts_to_success.append(attempts)

    def success_at(self, attempts: int) -> float:
        if attempts <= 0:
            raise ValueError("K must be positive")
        if not self.attempts_to_success:
            return 0.0
        return sum(value <= attempts for value in self.attempts_to_success) / len(self.attempts_to_success)
