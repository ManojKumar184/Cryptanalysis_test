# Cryptoanalysis V3

Experimental continual-learning research infrastructure for examining whether legal Bitcoin-style candidate modifications can be ranked more efficiently. It does **not** claim SHA-256d is predictably exploitable.

Current implementation: Phases 1–3. SHA-256 and SHA-256d are independently verifiable against `hashlib`; trace mode records the actual candidate-specific 64-round state trajectory for every compression block in both SHA-256d passes. Bitcoin-style candidates are explicit `C(F,M)` values with an 80-byte deterministic header serialization. The central rules layer permits only version, timestamp, and nonce mutations, rejects no-ops and illegal values, and the modification validator rejects duplicate result candidates. The fixed SHA-256d graph, trace-difference encoding, and outcome-blind model interfaces are also in place.

Run the verification suite with `python -m pytest`.
