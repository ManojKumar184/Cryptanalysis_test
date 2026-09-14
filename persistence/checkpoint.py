"""Atomic, versioned checkpoints that never overwrite the only valid copy."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


class CheckpointManager:
    REQUIRED_KEYS = frozenset({"controller_state", "candidate", "attempt_index", "model_version", "experience_count", "configuration_version"})

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def create(self, state: dict[str, object]) -> Path:
        missing = self.REQUIRED_KEYS - state.keys()
        if missing:
            raise ValueError(f"checkpoint missing required fields: {sorted(missing)}")
        checkpoint_id = f"checkpoint_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')}_{uuid4().hex[:8]}"
        payload = dict(state)
        payload["checkpoint_id"] = checkpoint_id
        payload["created_at"] = datetime.now(timezone.utc).isoformat()
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        payload["integrity_sha256"] = hashlib.sha256(canonical).hexdigest()
        temporary = self.root / f".{checkpoint_id}.tmp"
        destination = self.root / f"{checkpoint_id}.json"
        temporary.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        os.replace(temporary, destination)
        return destination

    def read_valid(self, path: str | Path) -> dict[str, object] | None:
        try:
            payload = json.loads(Path(path).read_text(encoding="utf-8"))
            checksum = payload.pop("integrity_sha256")
            canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
            if hashlib.sha256(canonical).hexdigest() != checksum or not self.REQUIRED_KEYS.issubset(payload):
                return None
            payload["integrity_sha256"] = checksum
            return payload
        except (OSError, ValueError, KeyError, json.JSONDecodeError):
            return None

    def valid_checkpoints_newest_first(self) -> list[tuple[Path, dict[str, object]]]:
        valid: list[tuple[Path, dict[str, object]]] = []
        for path in sorted(self.root.glob("checkpoint_*.json"), reverse=True):
            payload = self.read_valid(path)
            if payload is not None:
                valid.append((path, payload))
        return valid
