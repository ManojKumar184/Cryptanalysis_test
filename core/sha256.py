"""Small auditable SHA-256 implementation with optional compression traces."""

from __future__ import annotations

from .sha_trace import CompressionTrace, SHA256Trace, WordState

_MASK32 = 0xFFFFFFFF
_INITIAL: WordState = (
    0x6A09E667, 0xBB67AE85, 0x3C6EF372, 0xA54FF53A,
    0x510E527F, 0x9B05688C, 0x1F83D9AB, 0x5BE0CD19,
)
_K = (
    0x428A2F98, 0x71374491, 0xB5C0FBCF, 0xE9B5DBA5, 0x3956C25B, 0x59F111F1, 0x923F82A4, 0xAB1C5ED5,
    0xD807AA98, 0x12835B01, 0x243185BE, 0x550C7DC3, 0x72BE5D74, 0x80DEB1FE, 0x9BDC06A7, 0xC19BF174,
    0xE49B69C1, 0xEFBE4786, 0x0FC19DC6, 0x240CA1CC, 0x2DE92C6F, 0x4A7484AA, 0x5CB0A9DC, 0x76F988DA,
    0x983E5152, 0xA831C66D, 0xB00327C8, 0xBF597FC7, 0xC6E00BF3, 0xD5A79147, 0x06CA6351, 0x14292967,
    0x27B70A85, 0x2E1B2138, 0x4D2C6DFC, 0x53380D13, 0x650A7354, 0x766A0ABB, 0x81C2C92E, 0x92722C85,
    0xA2BFE8A1, 0xA81A664B, 0xC24B8B70, 0xC76C51A3, 0xD192E819, 0xD6990624, 0xF40E3585, 0x106AA070,
    0x19A4C116, 0x1E376C08, 0x2748774C, 0x34B0BCB5, 0x391C0CB3, 0x4ED8AA4A, 0x5B9CCA4F, 0x682E6FF3,
    0x748F82EE, 0x78A5636F, 0x84C87814, 0x8CC70208, 0x90BEFFFA, 0xA4506CEB, 0xBEF9A3F7, 0xC67178F2,
)


def _rotr(value: int, shift: int) -> int:
    return ((value >> shift) | (value << (32 - shift))) & _MASK32


def _pad(message: bytes) -> bytes:
    bit_length = len(message) * 8
    padded = message + b"\x80"
    padded += b"\x00" * ((56 - len(padded) % 64) % 64)
    return padded + bit_length.to_bytes(8, "big")


class SHA256:
    """Exact one-shot SHA-256, deliberately exposing no mutable state API."""

    @staticmethod
    def digest(message: bytes) -> bytes:
        return SHA256.digest_with_trace(message)[0]

    @staticmethod
    def digest_with_trace(message: bytes) -> tuple[bytes, SHA256Trace]:
        if not isinstance(message, bytes):
            raise TypeError("SHA-256 input must be bytes")
        state = _INITIAL
        traces: list[CompressionTrace] = []
        padded = _pad(message)
        for index in range(0, len(padded), 64):
            state, trace = _compress(state, padded[index:index + 64], index // 64)
            traces.append(trace)
        digest = b"".join(word.to_bytes(4, "big") for word in state)
        return digest, SHA256Trace(tuple(traces))


def _compress(state: WordState, block: bytes, block_index: int) -> tuple[WordState, CompressionTrace]:
    schedule = [int.from_bytes(block[i:i + 4], "big") for i in range(0, 64, 4)]
    for index in range(16, 64):
        s0 = _rotr(schedule[index - 15], 7) ^ _rotr(schedule[index - 15], 18) ^ (schedule[index - 15] >> 3)
        s1 = _rotr(schedule[index - 2], 17) ^ _rotr(schedule[index - 2], 19) ^ (schedule[index - 2] >> 10)
        schedule.append((schedule[index - 16] + s0 + schedule[index - 7] + s1) & _MASK32)
    a, b, c, d, e, f, g, h = state
    rounds: list[WordState] = []
    for index in range(64):
        sigma1 = _rotr(e, 6) ^ _rotr(e, 11) ^ _rotr(e, 25)
        choose = (e & f) ^ ((~e) & g)
        temp1 = (h + sigma1 + choose + _K[index] + schedule[index]) & _MASK32
        sigma0 = _rotr(a, 2) ^ _rotr(a, 13) ^ _rotr(a, 22)
        majority = (a & b) ^ (a & c) ^ (b & c)
        temp2 = (sigma0 + majority) & _MASK32
        h, g, f, e, d, c, b, a = g, f, e, (d + temp1) & _MASK32, c, b, a, (temp1 + temp2) & _MASK32
        rounds.append((a, b, c, d, e, f, g, h))
    output = tuple((left + right) & _MASK32 for left, right in zip(state, (a, b, c, d, e, f, g, h)))
    return output, CompressionTrace(block_index, state, tuple(rounds), output)


def sha256(message: bytes) -> bytes:
    return SHA256.digest(message)
