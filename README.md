# Cryptoanalysis V3

Experimental continual-learning research infrastructure for examining whether legal Bitcoin-style candidate modifications can be ranked more efficiently. It does **not** claim SHA-256d is predictably exploitable.

Current implementation: Phase 1 cryptographic foundation. SHA-256 and SHA-256d are independently verifiable against `hashlib`; trace mode records the actual candidate-specific 64-round state trajectory for every compression block in both SHA-256d passes.

Run the verification suite with `python -m pytest`.
