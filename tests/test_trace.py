from core.sha256d import sha256d_with_trace
from representations.state_encoder import encode_trace


def test_encoder_preserves_pass_round_and_word_axes() -> None:
    encoded = encode_trace(sha256d_with_trace(b"candidate").trace)
    assert len(encoded) == 2
    assert all(len(block) == 64 for pass_blocks in encoded for block in pass_blocks)
    assert all(len(state) == 8 for pass_blocks in encoded for block in pass_blocks for state in block)
    assert all(0.0 <= word <= 1.0 for pass_blocks in encoded for block in pass_blocks for state in block for word in state)
