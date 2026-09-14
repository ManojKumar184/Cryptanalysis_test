"""One leak-resistant proposal/evaluation cycle, not a sequential search."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter_ns

from core.block import Candidate
from core.evaluator import Evaluator
from core.modifications import ModificationValidator
from core.sha256d import sha256d_with_trace
from core.target import Target
from models.generator import ModificationGenerator
from models.gnn import SHA256dGNN
from models.difference_model import DifferenceModel
from models.ranking_model import RankingModel
from representations.difference import xor_difference
from representations.sha_graph import SHAGraph


@dataclass(frozen=True)
class SearchAttempt:
    candidate: Candidate
    modification: object
    score: float
    evaluation: object
    trace_ns: int
    inference_ns: int


class SearchEngine:
    def __init__(self) -> None:
        self.generator = ModificationGenerator()
        self.validator = ModificationValidator()
        self.graph_embedding = SHA256dGNN().forward(SHAGraph.sha256d())
        self.difference_model = DifferenceModel()
        self.ranking = RankingModel()
        self.evaluator = Evaluator()

    def attempt(self, candidate: Candidate, target: Target, proposal_index: int) -> SearchAttempt:
        # Trace data is computed before scoring; trace digests are deliberately discarded.
        trace_started = perf_counter_ns()
        base_trace = sha256d_with_trace(candidate.serialize()).trace
        modification = self.generator.propose(candidate, proposal_index)
        modified_candidate = self.validator.apply(candidate, modification)
        modified_trace = sha256d_with_trace(modified_candidate.serialize()).trace
        trace_ns = perf_counter_ns() - trace_started
        inference_started = perf_counter_ns()
        features = self.difference_model.forward(base_trace, modified_trace, xor_difference(base_trace, modified_trace), self.graph_embedding)
        score = self.ranking.score(candidate, modification, self.graph_embedding, features)
        inference_ns = perf_counter_ns() - inference_started
        # Only this isolated evaluator compares the exact digest to the target.
        evaluation = self.evaluator.evaluate(modified_candidate, target)
        return SearchAttempt(modified_candidate, modification, score, evaluation, trace_ns, inference_ns)
