# Cryptoanalysis V3

Experimental continual-learning research infrastructure for examining whether legal Bitcoin-style candidate modifications can be ranked more efficiently. It does **not** claim SHA-256d is predictably exploitable.

Current implementation: Phases 1–4. SHA-256 and SHA-256d are independently verifiable against `hashlib`; trace mode records the actual candidate-specific 64-round state trajectory for every compression block in both SHA-256d passes. Bitcoin-style candidates are explicit `C(F,M)` values with an 80-byte deterministic header serialization. The central rules layer permits only version, timestamp, and nonce mutations, rejects no-ops and illegal values, and the modification validator rejects duplicate result candidates. The fixed SHA-256d graph, trace-difference encoding, outcome-blind model interfaces, transactional SQLite experience archive, deterministic mixed replay, and immutable model-version artifacts are also in place.

Run the verification suite with `python -m pytest`.

Runtime data must be placed on persistent storage (the Docker/Hugging Face default is `/data/cryptoanalysis`). The dashboard is read-only. `worker.py` refuses autonomous mode unless `CRYPTOANALYSIS_INTEGRITY_VERIFIED=1`; autonomous scheduling is not enabled by default.
