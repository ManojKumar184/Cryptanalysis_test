from pathlib import Path

from experiment.candidate_stream import CandidateStream


def test_candidate_stream_persists_without_silent_reset(tmp_path: Path) -> None:
    path = tmp_path / "stream.json"
    first = CandidateStream(path).next()
    second = CandidateStream(path).next()
    assert first.candidate_id != second.candidate_id
    assert CandidateStream(path).sequence == 2
