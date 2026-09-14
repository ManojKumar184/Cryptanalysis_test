from core.sha256d import sha256d_with_trace
from models.difference_model import DifferenceModel
from models.generator import ModificationGenerator
from models.gnn import SHA256dGNN
from models.ranking_model import RankingModel
from representations.difference import xor_difference
from representations.sha_graph import SHAGraph
from tests.test_block import make_candidate


def test_static_graph_and_gnn_embedding_shape() -> None:
    graph = SHAGraph.sha256d()
    assert len(graph.nodes) == 128
    assert len(SHA256dGNN().forward(graph)) == 8


def test_difference_model_consumes_candidate_specific_traces() -> None:
    base = sha256d_with_trace(b"base")
    modified = sha256d_with_trace(b"modified")
    graph_embedding = SHA256dGNN().forward(SHAGraph.sha256d())
    features = DifferenceModel().forward(base.trace, modified.trace, xor_difference(base.trace, modified.trace), graph_embedding)
    assert len(features) == 10
    assert features[0] > 0


def test_difference_preserves_each_compression_block_axis() -> None:
    base = sha256d_with_trace(b"a" * 128)
    modified = sha256d_with_trace(b"b" * 128)
    delta = xor_difference(base.trace, modified.trace)
    assert len(delta.xor_words[0]) == len(base.trace.first_pass.compression_traces)
    assert all(len(block) == 64 for block in delta.xor_words[0])


def test_generator_and_ranking_only_produce_legal_outcome_blind_proposals() -> None:
    candidate = make_candidate()
    modification = ModificationGenerator().propose(candidate, 0)
    score = RankingModel().score(candidate, modification, SHA256dGNN().forward(SHAGraph.sha256d()), (0.2, 0.3))
    assert modification.field in candidate.rules.enabled_mutable_fields
    assert modification.after != modification.before
    assert isinstance(score, float)
